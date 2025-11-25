import asyncio
import logging
import os
from pyrogram import Client, errors
from utils.config import API_ID, API_HASH
from utils.logger_setup import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

async def create_session(session_name: str):
    """Creates and authorizes a Pyrogram session."""
    logger.info(f"--- Creating {session_name} Session ---")
    
    if not API_ID or not API_HASH:
        logger.error("API_ID or API_HASH not found in config. Please check your .env file.")
        return

    try:
        async with Client(session_name, api_id=API_ID, api_hash=API_HASH, workdir="markets") as app:
            me = await app.get_me()
            logger.info(f"{session_name} session created/verified successfully. Logged in as: {me.first_name} (ID: {me.id})")
    except errors.RPCError as e:
        logger.error(f"Telegram RPC Error during {session_name} session creation: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred during {session_name} session creation: {e}")

async def main():
    if not os.path.exists("markets"):
        try:
            os.makedirs("markets")
            logger.info("Created 'markets' directory.")
        except OSError as e:
            logger.error(f"Failed to create 'markets' directory: {e}")
            return

    await create_session("portals")
    print()
    await create_session("mrkt")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Session generation cancelled by user.")