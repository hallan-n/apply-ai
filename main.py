import asyncio

from database import create_database
from linkedin import run


asyncio.run(create_database())
asyncio.run(run())
