import asyncio
import json
import re
from llm import ask_llm, prompt
from logger import logging
from bs4 import BeautifulSoup
from database import create_job, get_job, update_job_status

from playwright.async_api import async_playwright, Browser, BrowserContext, Page

URL_BASE = (
    "https://www.linkedin.com/jobs/search-results/"
    # "?keywords=FastAPI&f_TPR=r86400&f_AL=true" 24h
    "?keywords=Python&f_TPR=r604800&f_AL=true" # 1semana
    "&f_SAL=f_SA_id_225001%3A272001&start="
)


def clean_description(text: str) -> str:
    logging.info("Limpando descrição da vaga")

    text = BeautifulSoup(text, "html.parser").get_text("\n")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.strip() for line in text.split("\n")]
    cleaned = []
    previous_empty = False

    for line in lines:
        if not line:
            if not previous_empty:
                cleaned.append("")
            previous_empty = True
        else:
            cleaned.append(line)
            previous_empty = False

    logging.info("Descrição limpa com sucesso")

    return "\n".join(cleaned).strip()


async def inject_session(browser: Browser) -> BrowserContext:
    logging.info("Carregando cookies da sessão")

    with open("cookies.json", "r", encoding="utf-8") as f:
        cookies = json.load(f)

    logging.info(f"{len(cookies)} cookies carregados")

    context = await browser.new_context()
    await context.add_cookies(cookies)

    logging.info("Sessão injetada com sucesso")

    return context


async def get_jobs_ids(page: Page) -> list[str]:
    logging.info("Buscando IDs das vagas")

    jobs = await page.query_selector_all("div[componentkey^='job-card-component-ref-']")

    logging.info(f"{len(jobs)} vagas encontradas na página")

    return [(await job.get_attribute("componentkey")).split("-")[-1] for job in jobs]


async def skip_modal(page: Page):
    dialog = page.locator("dialog")

    while True:
        inputs = dialog.locator("input")

        for i in range(await inputs.count()):
            input = inputs.nth(i)
            aria_label = await input.get_attribute("aria-label")

            if not aria_label:
                continue

            aria_label = aria_label.lower()

            if "current location" in aria_label:
                await input.fill("Vitória, ES, Brazil")

            elif "pretensão salarial" in aria_label:
                await input.fill("9000" if "pj" in aria_label else "7000")

            elif "expected salary" in aria_label:
                await input.fill("9000" if "pj" in aria_label else "7000")

        next_step = dialog.get_by_role("button", name="Avançar")

        if await next_step.count() > 0:
            await next_step.click()

        await page.wait_for_timeout(500)

        rate = dialog.get_by_role("button", name="Avaliar")

        if await rate.count() > 0:
            await rate.click()

        await page.wait_for_timeout(500)

        if await dialog.get_by_text("Este campo é obrigatório", exact=True).count():
            logging.info("Campo obrigatório não preenchido. Ignorando")
            return False
        
        if await dialog.get_by_text("Valor inválido", exact=True).count():
            logging.info("Campo obrigatório não preenchido. Ignorando")
            return False
        
        send = dialog.get_by_role("button", name="Enviar candidatura")

        if await send.count() > 0:
            return True

async def process_job(
    context: BrowserContext,
    job_id: str,
    semaphore: asyncio.Semaphore,
):
    async with semaphore:
        logging.info(f"[{job_id}] Iniciando processamento")

        page = await context.new_page()

        try:
            url = (
                "https://www.linkedin.com/jobs/search-results/"
                f"?keywords=python&f_TPR=r86400&f_WT=2"
                f"&currentJobId={job_id}"
            )

            logging.info(f"[{job_id}] Acessando página da vaga")

            await page.goto(url)

            logging.info(f"[{job_id}] Página carregada")

            await page.wait_for_selector(
                "button[data-testid='expandable-text-button']", timeout=20000
            )

            logging.info(f"[{job_id}] Botão de expandir encontrado")

            await page.click("button[data-testid='expandable-text-button']")

            logging.info(f"[{job_id}] Descrição expandida")

            description = await page.locator(
                "span[data-testid='expandable-text-box']"
            ).first.inner_text()

            logging.info(f"[{job_id}] Descrição capturada")

            description = clean_description(description)

            title = await page.locator("title").first.inner_text()

            logging.info(f"[{job_id}] Título capturado: {title}")

            job = await get_job(job_id)

            if job:
                logging.info(f"[{job_id}] Vaga já existe no banco. Ignorando")
                return

            logging.info(f"[{job_id}] Salvando vaga no banco")


            await create_job(
                job_id=job_id,
                company=title.split(" | ")[1],
                job_title=title.split(" | ")[0],
                description=description,
                location="Brazil",
                status="pending",
                is_remote=True,
            )

            candidacy = page.locator(
                "button[aria-label='Usar a candidatura simplificada para esta vaga']"
            )

            if await candidacy.count():
                await candidacy.first.click()
                await page.wait_for_timeout(1000)
            else:
                logging.info(f"[{job_id}] Botão de candidatura simplificada não encontrado. Ignorando")
                return





            can_continue = await skip_modal(page)

            if not can_continue:
                logging.info(f"[{job_id}] Modal de candidatura não pode ser continuado. Ignorando")
                return







 

            response = ask_llm("gpt-5-mini",
                    prompt.format(
                        title=title.split(" | ")[0],
                        description=description
                    )
                )

            if response == "NÃO APLICAR":
                logging.info(f"[{job_id}] Candidato não atende aos requisitos. Ignorando")
                return

            if response == "AVALIAR":
                logging.info(f"[{job_id}] Candidato atende parcialmente aos requisitos. Avaliando manualmente")
                await update_job_status(job_id, "evaluate")
                return

            
            dialog = page.locator("dialog")

            await dialog.get_by_role("button", name="Enviar candidatura").click()

            await update_job_status(job_id, "submitted")

            logging.info(f"[{job_id}] Vaga salva com sucesso")

        finally:
            await page.close()

            logging.info(f"[{job_id}] Página fechada")


async def run():
    logging.info("Iniciando scraper do LinkedIn")

    async with async_playwright() as p:
        logging.info("Iniciando navegador")

        browser = await p.chromium.launch(headless=False)

        logging.info("Navegador iniciado")

        context = await inject_session(browser)

        step = 0

        while True:
            logging.info(f"Iniciando página de busca: start={step}")

            page = await context.new_page()

            await page.goto(f"{URL_BASE}{step}")

            logging.info(f"Página de busca carregada: start={step}")

            no_results = await page.locator(
                "h2:has-text('Nenhum resultado encontrado')"
            ).count()

            if no_results:
                logging.info("Nenhum resultado encontrado. Finalizando scraper")

                await page.close()

                print("Fim das vagas.")
                break

            jobs_ids = await get_jobs_ids(page)

            await page.close()

            if not jobs_ids:
                logging.warning("Nenhum job encontrado. Encerrando")

                print("Nenhum job encontrado. Encerrando.")
                break

            logging.info(
                f"Processando {len(jobs_ids)} vagas com limite de 5 simultâneas"
            )

            semaphore = asyncio.Semaphore(1)

            tasks = [process_job(context, job_id, semaphore) for job_id in jobs_ids]

            await asyncio.gather(*tasks)

            logging.info(f"Página start={step} processada com sucesso")

            step += 25

            logging.info(f"Avançando para start={step}")

        await browser.close()

    logging.info("Scraper finalizado")
