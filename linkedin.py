import asyncio
import json
from bs4 import BeautifulSoup

from playwright.async_api import async_playwright, Browser, BrowserContext, Page

URL_BASE = (
    "https://www.linkedin.com/jobs/search-results/"
    "?keywords=python&f_TPR=r86400&f_WT=2&start="
)



def clean_description(text: str) -> str:
    # Remove HTML, caso ainda exista
    text = BeautifulSoup(text, "html.parser").get_text("\n")

    # Normaliza \r\n
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Remove espaços no começo/fim de cada linha
    lines = [line.strip() for line in text.split("\n")]

    # Remove linhas vazias duplicadas
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

    return "\n".join(cleaned).strip()


async def inject_session(browser: Browser) -> BrowserContext:
    with open("cookies.json", "r", encoding="utf-8") as f:
        cookies = json.load(f)

    context = await browser.new_context()
    await context.add_cookies(cookies)

    return context


async def get_jobs_ids(page: Page) -> list[str]:
    jobs = await page.query_selector_all(
        "div[componentkey^='job-card-component-ref-']"
    )

    return [
        (await job.get_attribute("componentkey")).split("-")[-1]
        for job in jobs
    ]


async def process_job(
    context: BrowserContext,
    job_id: str,
    semaphore: asyncio.Semaphore,
):
    async with semaphore:
        page = await context.new_page()

        try:
            url = (
                "https://www.linkedin.com/jobs/search-results/"
                f"?keywords=python&f_TPR=r86400&f_WT=2"
                f"&currentJobId={job_id}"
            )

            await page.goto(url)
            await page.wait_for_selector("button[data-testid='expandable-text-button']", timeout=5000)
            await page.click("button[data-testid='expandable-text-button']")
            description = await page.locator(
                "span[data-testid='expandable-text-box']"
            ).first.inner_text()

            description = clean_description(description)
            print(description)
            breakpoint()

            print(f"Processando: {job_id}")

            # fazer scraping / aplicação aqui

        finally:
            await page.close()


async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await inject_session(browser)


        step = 0

        while True:
            page = await context.new_page()

            await page.goto(f"{URL_BASE}{step}")

            no_results = await page.locator(
                "h2:has-text('Nenhum resultado encontrado')"
            ).count()

            if no_results:
                await page.close()
                print("Fim das vagas.")
                break

            jobs_ids = await get_jobs_ids(page)
            await page.close()

            if not jobs_ids:
                print("Nenhum job encontrado. Encerrando.")
                break

            semaphore = asyncio.Semaphore(5)

            tasks = [
                process_job(context, job_id, semaphore)
                for job_id in jobs_ids
            ]

            await asyncio.gather(*tasks)

            step += 25



            await browser.close()


asyncio.run(run())

        