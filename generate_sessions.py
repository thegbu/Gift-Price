import asyncio
import os

from utils.config import API_ID, API_HASH

async def create_session(session_name: str, pyrogram_client_class, pyrogram_errors_module):
    """
    Creates and authorizes a Pyrogram session.
    Pyrogram classes are passed as arguments to delay the import.
    """
    print(f"--- Creating {session_name} Session ---")

    if not API_ID or not API_HASH:
        print("API_ID or API_HASH not found in config. Please check your .env file.")
        return

    try:
        async with pyrogram_client_class(
            session_name,
            api_id=API_ID,
            api_hash=API_HASH,
            workdir="markets"
        ) as app:
            me = await app.get_me()
            print(f"{session_name} session created/verified successfully. Logged in as: {me.first_name} (ID: {me.id})")

    except pyrogram_errors_module.RPCError as e:
        print(f"Telegram RPC Error during {session_name} session creation: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during {session_name} session creation: {e}")

async def main():
    from pyrogram import Client, errors

    if not os.path.exists("markets"):
        try:
            os.makedirs("markets")
            print("Created 'markets' directory.")
        except OSError as e:
            print(f"Failed to create 'markets' directory: {e}")
            return

    await create_session("portals", Client, errors)
    print()
    await create_session("mrkt", Client, errors)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Session generation cancelled by user.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")