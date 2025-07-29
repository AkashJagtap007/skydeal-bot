import asyncio
import re
import threading
import os
from telethon.sync import TelegramClient, events, Button
from ping_server import app
import aiohttp

# === Telegram API Credentials ===
api_id = 26429542
api_hash = '6caf396bf1f8898478ce1d8bdb1b5a88'
session_name = 'skydeal'

# === Telegram Channels ===
source_channels = ['skydeal_frostfibre', 'dealdost', 'realearnkaro']
destination_channel = 'SkyDeal247'
converter_bot = 'ekconverter20bot'

# === Telegram Client ===
client = TelegramClient(session_name, api_id, api_hash)

def extract_links(text):
    return re.findall(r'(https?://[^\s<>]+)', text)

def is_only_link(text):
    return bool(re.fullmatch(r'https?://\S+', text.strip()))

async def resolve_link(link):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(link, allow_redirects=True) as resp:
                return str(resp.url)
    except:
        return link

@client.on(events.NewMessage(chats=source_channels))
async def handle_message(event):
    text = event.raw_text or ""
    if '🛒 Buy now ✅' in text:
        return

    links = extract_links(text)
    if not links:
        return

    converted_links = {}
    for link in links:
        resolved = await resolve_link(link)
        if "amazon." not in resolved:
            continue

        try:
            async with client.conversation(converter_bot, timeout=30) as conv:
                await conv.send_message(resolved)
                reply = await conv.get_response()
                converted = reply.text.strip()

                if "We could not locate an affiliate URL" in converted:
                    continue

                converted_links[link] = converted
        except:
            continue

    if not converted_links:
        return

    for original, new_link in converted_links.items():
        text = text.replace(original, new_link)

    text += "\n\n🛒 Buy now ✅"
    button = [[Button.url("🔗 Buy Now", list(converted_links.values())[0])]]

    # ✅ Safe: always use send_message instead of send_file to avoid media errors
    await client.send_message(destination_channel, text, buttons=button, link_preview=True)

@client.on(events.NewMessage(chats=destination_channel))
async def delete_unwanted(event):
    if is_only_link(event.raw_text) or "We could not locate an affiliate URL" in event.raw_text:
        try:
            await event.delete()
        except:
            pass

async def start():
    await client.start()
    print("🚀 Amazon bot is live.")
    await client.run_until_disconnected()

if __name__ == "__main__":
    threading.Thread(target=app.run, kwargs={'host': '0.0.0.0', 'port': 8080}).start()
    asyncio.run(start())
