import asyncio

from database import create_database
from linkedin import run


asyncio.run(create_database())
asyncio.run(run())


# page.locator("button[aria-label='Usar a candidatura simplificada para esta vaga']").click()
# page.wait_for_selector("div[componentkey^='job-card-component-ref-']")
# page.get_by_role("button", name="Avançar").click()
# page.get_by_role("button", name="Avançar").click()