import asyncio
import os

from utils.config import API_ID, API_HASH

async def create_session(session_name: str, telethon_client_class):
    """
    Creates and authorizes a Telethon session.
    """
    print(f"--- Creating {session_name} Session ---")

    if not API_ID or not API_HASH:
        print("API_ID or API_HASH not found in config. Please check your .env file.")
        return

    session_path = os.path.join("markets", session_name)
    
    try:
        client = telethon_client_class(session_path, API_ID, API_HASH)
        await client.start()
        
        me = await client.get_me()
        print(f"{session_name} session created/verified successfully. Logged in as: {me.first_name} (ID: {me.id})")
        
        await client.disconnect()
        
    except Exception as e:
        print(f"An error occurred during {session_name} session creation: {e}")

async def main():
    from telethon import TelegramClient

    if not os.path.exists("markets"):
        try:
            os.makedirs("markets")
            print("Created 'markets' directory.")
        except OSError as e:
            print(f"Failed to create 'markets' directory: {e}")
            return

    await create_session("portals", TelegramClient)
    print()
    await create_session("mrkt", TelegramClient)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nSession generation cancelled by user.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")