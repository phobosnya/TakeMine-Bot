import requests
import asyncio

from aiogram import Bot
from aiogram.types import ParseMode

import config
import db


async def start():
    bot = Bot(token=config.BOT_TOKEN)

    while True:
        await asyncio.sleep(2)
        headers = {
            'accept': 'application/json',
            'Rocket-Pay-Key': f'{config.API_TOKEN}'
        }
        resp = requests.get(f'https://pay.ton-rocket.com/tg-invoices?limit=100&offset=0', headers= headers).json()
        if not resp['success']:
            continue

        for tx in resp['data']['results']:
            if tx['status'] == 'expired':
                requests.delete(f"https://pay.ton-rocket.com/tg-invoices/{tx['id']}", headers=headers,)
                continue
            elif tx['status'] == "paid":
                requests.delete(f"https://pay.ton-rocket.com/tg-invoices/{tx['id']}", headers=headers,)
                value = float(tx['amount'])
                uid = tx["hiddenMessage"]
                if not uid.isdigit():
                    continue
                uid = int(uid)
                if not db.check_user(uid):
                    continue
                db.add_balance(uid, value)
                await bot.send_message(uid, 'Платеж принят!\n'
                                      f'*+{value} TAKE*',
                                      parse_mode=ParseMode.MARKDOWN)