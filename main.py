import asyncio
from dotenv import load_dotenv
from database import create_database
from linkedin import run


load_dotenv(override=True)


asyncio.run(create_database())
asyncio.run(run())
