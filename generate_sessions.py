import asyncio
from pyrogram import Client
from config import API_ID, API_HASH

async def main():
    print("--- Creating Portal Session ---")
    async with Client("portals", api_id=API_ID, api_hash=API_HASH, workdir="markets"):
        print("Portal session created successfully.")

    print("\n--- Creating MRKT Session ---")
    async with Client("mrkt", api_id=API_ID, api_hash=API_HASH, workdir="markets"):
        print("MRKT session created successfully.")

if __name__ == "__main__":
    asyncio.run(main())