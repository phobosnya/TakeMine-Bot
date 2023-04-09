import logging

from aiogram.dispatcher import FSMContext
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters import Text
from aiogram.types import ParseMode, ReplyKeyboardMarkup, KeyboardButton, \
                          InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.dispatcher.filters.state import State, StatesGroup
import json
import config
import db
import requests
import take
import random
import string

logging.basicConfig(level=logging.INFO)
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

class Form(StatesGroup):
    amount = State()
    withamount = State()
    withservamount = State()
    minenickvip = State()
    minenickprim = State()
    minenickpir = State()
    screensum = State()
    uid = State()
    sumstate = State()

@dp.message_handler(commands=['start', 'help'])
async def welcome_handler(message: types.Message):
    uid = message.from_user.id
    if not db.check_user(uid):
        db.add_user(uid)
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row(KeyboardButton('Пополнить'))
    keyboard.row(KeyboardButton('Вывод'))
    keyboard.row(KeyboardButton('Баланс'), KeyboardButton('Киты'))
    await message.answer('''***Приветствую!***
Я - телеграм бот, созданный для покупки доната на сервере ***TonTake*** и для вывода заработанной криптовалюты на нем.
Нажмите __*Киты*__, чтобы открыть наборы, доступные для покупки.
Нажмите __*Пополнить*__, чтобы положить TAKE на свой счет.
Нажмите __Вывод__, чтобы вывести TAKE на ton-rocket кошелек.
Для отмены любого действия напишите /cancel.
Удачной игры!''',
                         reply_markup=keyboard,
                         parse_mode=ParseMode.MARKDOWN)

@dp.message_handler(commands='balance',state='*')
@dp.message_handler(Text(equals='Баланс', ignore_case=True),state='*')
async def balance_handler(message: types.Message, state: FSMContext):
    await state.finish()
    uid = message.from_user.id
    user_balance = db.get_balance(uid)
    await message.answer(f'Ваш баланс: *{user_balance} TAKE*',
                         parse_mode=ParseMode.MARKDOWN)

@dp.message_handler(commands='withdraw', state='*')
@dp.message_handler(Text(equals='Вывод', ignore_case=True),state='*')
async def withdraw_handler(message: types.Message, state: FSMContext):
    await state.finish()
    kb = InlineKeyboardMarkup(row_width=2).add(InlineKeyboardButton(text = "Баланс бота", callback_data="withbot"), InlineKeyboardButton(text = "Баланс сервера", callback_data="withserv"))
    await message.answer("Выберите, откуда хотите вывести TAKE:", reply_markup=kb, parse_mode=ParseMode.MARKDOWN)

@dp.callback_query_handler(text = "withserv")
async def process_withdraw(callback: types.CallbackQuery):
    await bot.delete_message(callback.from_user.id, callback.message.message_id)
    global code
    code = ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for _ in range(8))
    await bot.send_photo(callback.from_user.id, "https://imageup.ru/img268/4284910/screenshot_1.png", f"Пришлите скриншот подобного формата, введя в чат сумму и следующий код через запятую: {code} \nТакже не забудьте зажать таб!\nУчтите, что 100 внутриигровых TAKE = 1 TAKE в боте.")
    await Form.withservamount.set()

@dp.message_handler(state = Form.withservamount, content_types=['photo', 'text'])
async def process_sum(message: types.Message, state: FSMContext):
    if message.text == "/cancel":
        await message.answer("Вывод отменен...")
        await state.finish()
    elif not message.text:
        global code
        await message.forward(5602124939)
        kb = InlineKeyboardMarkup(row_width=1).add(InlineKeyboardButton(text = "Подтвердить", callback_data="proceed"), InlineKeyboardButton(text = "Отклонить", callback_data="decline"))
        await bot.send_message(5602124939, f'''Запрос на вывод средств
Данные о юзере:
Код: {code}
Баланс: {db.get_balance(message.from_user.id)} TAKE
id: `{message.from_user.id}`
{f"Тег: @{message.from_user.username}" if message.from_user.username else ""}''', reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
        await message.answer("Запрос на вывод успешно отправлен, ждите обработки втечение 12 часов.")
        await state.finish()
    else:
        await message.answer("Пришлите фото. Или напишите /cancel для отмены.")

@dp.callback_query_handler(text = "proceed")
async def process_proceedure(callback: types.CallbackQuery, state: FSMContext):
    lines = callback.message.text.split('\n')
    uid = lines[4].split(': ')[1]
    await callback.message.edit_text(f'''***ПОДТВЕРЖДЕНО***
{callback.message.text}''', parse_mode=ParseMode.MARKDOWN)
    await bot.send_message(callback.from_user.id, "Введите сумму вывода на скрине")
    await Form.uid.set()
    await state.set_data(uid)

@dp.message_handler(state = Form.uid)
async def process_withserv(message:types.Message, state:FSMContext):
    valid = False
    try:
        float(message.text)
        valid = True
    except:
        pass
    if valid and float(message.text)>0 and float(message.text):
        uid = await state.get_data()
        db.add_balance(uid, float(message.text))
        await bot.send_message(uid, 'Вывод принят!\n'
                                      f'*+{message.text} TAKE*',
                                      parse_mode=ParseMode.MARKDOWN)
        await message.answer(f'''Вы успешно вывели ***{message.text} TAKE*** на счет пользователя!''', parse_mode=ParseMode.MARKDOWN)
        await state.finish()
    else:
        await message.answer('***Некорректные данные.*** Попробуйте еще раз...', parse_mode=ParseMode.MARKDOWN)

@dp.callback_query_handler(text = "decline")
async def process_decline(callback: types.CallbackQuery):
    lines = callback.message.text.split('\n')
    uid = lines[4].split(': ')[1]
    await bot.send_message(int(uid), "Ваш запрос на вывод средств был отклонен, попробуйте еще раз.\nВы также можете связаться с поддержкой: @TonTakeHelp")
    await callback.message.edit_text(f'''***ОТКЛОНЕНО***
{callback.message.text}''', parse_mode=ParseMode.MARKDOWN)

@dp.callback_query_handler(text = "withbot")
async def process_withdraw(callback: types.CallbackQuery):
    await bot.delete_message(callback.from_user.id, callback.message.message_id)
    await bot.send_message(callback.from_user.id, "Введите сумму вывода...")
    await Form.withamount.set()

@dp.message_handler(state=Form.withamount)
async def process_sum(message: types.Message, state: FSMContext):
    valid = False
    try:
        float(message.text)
        valid = True
    except:
        pass
    if message.text == "/cancel":
        await message.reply("***Вывод отменен***", parse_mode=ParseMode.MARKDOWN)
        await state.finish()
    elif valid and float(message.text)>0 and float(message.text) <= db.get_balance(message.from_user.id):
        url = 'https://pay.ton-rocket.com/app/transfer'
        headers = {
            "accept": "application/json",
            "Rocket-Pay-Key": f"{config.API_TOKEN}",
            "Content-Type": "application/json"
        }
        data = f'''{"{"}
            "tgUserId": {message.from_user.id},
            "currency": "TAKE",
            "amount": {float(message.text)},
            "transferId": "{str(message.from_user.id)+str(random.randint(0,1000000000))}",
            "description": "Withdraw for {message.text} TAKE"
        {"}"}'''
        print(data)
        #data = f"{data}".encode()
        rept = requests.post(url, data=data, headers = headers)
        db.decrease_balance(message.from_user.id, float(message.text))
        req = rept.json()
        print(req)
        if req['success'] == False:
            await message.answer("Возникли неполадки при выводе, попробуйте позже...")
        else:
            await message.answer(f'''Вы успешно вывели ***{message.text} TAKE*** с вашего счета!''', parse_mode=ParseMode.MARKDOWN)
        await state.finish()
    elif float(message.text) > db.get_balance(message.from_user.id):
        await message.answer('***Недостаточно средств...***', parse_mode=ParseMode.MARKDOWN)
        await state.finish()
    else:
        await message.answer('***Некорректные данные.*** Попробуйте еще раз...', parse_mode=ParseMode.MARKDOWN)

@dp.message_handler(commands="kits", state = "*")
@dp.message_handler(Text(equals='Киты', ignore_case=True), state = '*')
async def kit_packs(message: types.Message, state:FSMContext):
    await state.finish()
    kb = InlineKeyboardMarkup(row_width = 2).add(InlineKeyboardButton(text = "VIP", callback_data="VIP"), InlineKeyboardButton(text = "PRIMAL", callback_data="PRIMAL"), InlineKeyboardButton(text = "PIRATE", callback_data="PIRATE"))
    await message.answer("Выберите один из доступных наборов:", reply_markup=kb)

@dp.callback_query_handler(text = "VIP")
async def vip_hand(callback: types.CallbackQuery):
    kb = InlineKeyboardMarkup(row_width=1).add(InlineKeyboardButton(text = "Купить", callback_data="buyvip"))
    await bot.send_photo(callback.from_user.id, "https://imageup.ru/img96/4284166/photo_2023-04-08_18-26-39.jpg", '''**VIP**
Перезарядка набора: ***7 дней***
Стоимость привелегии: ***2 TAKE***
Дополнительные возможности:
***Префикс***''', reply_markup=kb, parse_mode=ParseMode.MARKDOWN)

@dp.callback_query_handler(text = "buyvip")
async def confirmation(callback: types.CallbackQuery):
    kb = InlineKeyboardMarkup(row_width=1).add(InlineKeyboardButton(text = "Подтверждаю", callback_data="confvip"))
    await bot.send_message(callback.from_user.id, "Вы точно хотите купить набор ***VIP*** за ***2 TAKE***?", reply_markup=kb, parse_mode=ParseMode.MARKDOWN)

@dp.callback_query_handler(text = "confvip")
async def payment(callback: types.CallbackQuery):
    if db.get_balance(callback.from_user.id) >= 2:
        await bot.send_message(callback.from_user.id, '''Отлично!
Прежде чем отправить запрос на получение привилегии, введите свой никнейм в майнкрафте
Предупреждение:
Проверьте введенный ник внимательно. В случае ненахождения вашего ника в базе данных, вам напишет поддержка.''')
        await Form.minenickvip.set()
    else:
        await bot.send_message(callback.from_user.id, "Недостаточно средств.")

@dp.message_handler(state = Form.minenickvip)
async def proccess_nick(message: types.Message, state: FSMContext):
    if message.text == "/cancel":
        await message.reply("***Операция отменена***", parse_mode=ParseMode.MARKDOWN)
        await state.finish()
    elif len(message.text) > 3:
        await bot.send_message(5602124939, f'''Запрос на покупку набора VIP
Данные о юзере:
Баланс: {db.get_balance(message.from_user.id)} TAKE
MC Nickname: {message.text}
id: `{message.from_user.id}`
{f"Тег: @{message.from_user.username}" if message.from_user.username else ""}''', parse_mode=ParseMode.MARKDOWN)
        db.decrease_balance(message.from_user.id, 2)
        await message.answer("Запрос на получение привилегии успешно отправлен.\nПривилегия активируется в течении 12 часов.\nСпасибо за покупку!")
        await state.finish()
    else:
        await message.answer("Некорректные данные... Никнейм должен быть длиннее.")

@dp.callback_query_handler(text = "PRIMAL")
async def pri_hand(callback: types.CallbackQuery):
    kb = InlineKeyboardMarkup(row_width=1).add(InlineKeyboardButton(text = "Купить", callback_data="buyprim"))
    await bot.send_photo(callback.from_user.id, "https://imageup.ru/img291/4284180/photo_2023-04-08_17-00-23.jpg", '''**PRIMAL**
Перезарядка: ***21 день***
Стоимость: ***5 TAKE***
***Шлем - Защита 1; Подводное дыхание 1
Нагрудник, поножи, ботинки - Защита 2
Лук: Бесконечность***
Возможности:
***Префикс***
Команды: ***/rtp***''', reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
    
@dp.callback_query_handler(text = "buyprim")
async def confirmation(callback: types.CallbackQuery):
    kb = InlineKeyboardMarkup(row_width=1).add(InlineKeyboardButton(text = "Подтверждаю", callback_data="confprim"))
    await bot.send_message(callback.from_user.id, "Вы точно хотите купить набор ***PRIMAL*** за ***5 TAKE***?", reply_markup=kb, parse_mode=ParseMode.MARKDOWN)

@dp.callback_query_handler(text = "confprim")
async def payment(callback: types.CallbackQuery):
    if db.get_balance(callback.from_user.id) >= 5:
        await bot.send_message(callback.from_user.id, '''Отлично!
Прежде чем отправить запрос на получение привилегии, введите свой никнейм в майнкрафте
Предупреждение:
Проверьте введенный ник внимательно. В случае ненахождения вашего ника в базе данных, вам напишет поддержка.''')
        await Form.minenickprim.set()
    else:
        await bot.send_message(callback.from_user.id, "Недостаточно средств.")

@dp.message_handler(state = Form.minenickprim)
async def proccess_nick(message: types.Message, state: FSMContext):
    if message.text == "/cancel":
        await message.reply("***Операция отменена***", parse_mode=ParseMode.MARKDOWN)
        await state.finish()
    elif len(message.text) > 3:
        await bot.send_message(5602124939, f'''Запрос на покупку набора PRIMAL
Данные о юзере:
Баланс: {db.get_balance(message.from_user.id)} TAKE
MC Nickname: {message.text}
id: `{message.from_user.id}`
{f"Тег: @{message.from_user.username}" if message.from_user.username else ""}''', parse_mode=ParseMode.MARKDOWN)
        db.decrease_balance(message.from_user.id, 5)
        await message.answer("Запрос на получение привилегии успешно отправлен.\nПривилегия активируется в течении 12 часов.\nСпасибо за покупку!")
        await state.finish()
    else:
        await message.answer("Некорректные данные... Никнейм должен быть длиннее.")

@dp.callback_query_handler(text = "PIRATE")
async def pir_hand(callback: types.CallbackQuery):
    kb = InlineKeyboardMarkup(row_width=1).add(InlineKeyboardButton(text = "Купить", callback_data="buypirate"))
    await bot.send_photo(callback.from_user.id, "https://imageup.ru/img211/4284186/photo_2023-04-08_17-18-49.jpg", '''**PIRATE**
Стоимость: ***13 TAKE***
Перезарядка набора: ***14 дней***
Зачарования: ***лучшие!***
Привелегии:
***/rtp; /rg claim(300блоков); Награды за квесты пирата удваиваются (добавляется финальный квест на 1 TAKE)***''', reply_markup=kb, parse_mode=ParseMode.MARKDOWN)

@dp.callback_query_handler(text = "buypirate")
async def confirmation(callback: types.CallbackQuery):
    kb = InlineKeyboardMarkup(row_width=1).add(InlineKeyboardButton(text = "Подтверждаю", callback_data="confpirate"))
    await bot.send_message(callback.from_user.id, "Вы точно хотите купить набор ***PIRATE*** за ***13 TAKE***?", reply_markup=kb, parse_mode=ParseMode.MARKDOWN)

@dp.callback_query_handler(text = "confpirate")
async def payment(callback: types.CallbackQuery):
    if db.get_balance(callback.from_user.id) >= 13:
        await bot.send_message(callback.from_user.id, '''Отлично!
Прежде чем отправить запрос на получение привилегии, введите свой никнейм в майнкрафте
Предупреждение:
Проверьте введенный ник внимательно. В случае ненахождения вашего ника в базе данных, вам напишет поддержка.''')
        await Form.minenickpir.set()
    else:
        await bot.send_message(callback.from_user.id, "Недостаточно средств.")

@dp.message_handler(state = Form.minenickpir)
async def proccess_nick(message: types.Message, state: FSMContext):
    if message.text == "/cancel":
        await message.reply("***Операция отменена***", parse_mode=ParseMode.MARKDOWN)
        await state.finish()
    elif len(message.text) > 3:
        await bot.send_message(5602124939, f'''Запрос на покупку набора PIRATE
Данные о юзере:
Баланс: {db.get_balance(message.from_user.id)} TAKE
MC Nickname: {message.text}
id: `{message.from_user.id}`
{f"Тег: @{message.from_user.username}" if message.from_user.username else ""}''', parse_mode=ParseMode.MARKDOWN)
        db.decrease_balance(message.from_user.id, 13)
        await message.answer("Запрос на получение привилегии успешно отправлен.\nПривилегия активируется в течении 12 часов.\nСпасибо за покупку!")
        await state.finish()
    else:
        await message.answer("Некорректные данные... Никнейм должен быть длиннее.")

@dp.message_handler(commands='deposit', state='*')
@dp.message_handler(Text(equals='Пополнить', ignore_case=True),state='*')
async def deposit_handler(message: types.Message, state: FSMContext):
    await state.finish()
    kb = InlineKeyboardMarkup(row_width=2).add(InlineKeyboardButton(text = "Баланс бота", callback_data="botpoc"), InlineKeyboardButton(text = "Баланс сервера", callback_data="servpoc"))
    await message.answer("Выберите баланс", reply_markup=kb)

@dp.callback_query_handler(text = "servpoc")
async def proc(callback: types.CallbackQuery):
    await callback.message.delete()
    await bot.send_message(callback.from_user.id, "***Введите сумму пополнения и точный ник в майнкрафте через запятую, по порядку 0.5, TMPhobos***\nУчтите, что минимальная сумма пополнения 0.5 TAKE", parse_mode=ParseMode.MARKDOWN)
    await Form.sumstate.set()

@dp.message_handler(state = Form.sumstate)
async def procstate(message: types.Message, state: FSMContext):
    if message.text == "/cancel":
        await message.answer("***Пополнение отменено.***", parse_mode=ParseMode.MARKDOWN)
        await state.finish()
    else:
        try:
            if message.text.find(","):
                data = message.text.split(",")
                if float(data[0])>=0.5:
                    if float(data[0])<=db.get_balance(message.from_user.id):
                        if len(data[1].replace(" ", '', 1)) >= 3:
                            kb = InlineKeyboardMarkup(row_width=1).add(InlineKeyboardButton(text = "Подтвердить выполнение", callback_data="procproced"))
                            await bot.send_message(5602124939, f'''Запрос на пополнение средств на сервере
Данные о юзере:
Сумма пополнения: {data[0]}
Баланс: {db.get_balance(message.from_user.id)} TAKE
MC Nickname: {data[1]}
id: `{message.from_user.id}`
{f"Тег: @{message.from_user.username}" if message.from_user.username else ""}''', reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
                            db.decrease_balance(message.from_user.id, float(data[0]))
                            await message.answer(f"Запрос на пополнение счета отправлен, ждите пополнения втечение 12 часов.\nВ противном случае обратитесь в поддержку: @TonTakeHelp, указав ваш айди: `{message.from_user.id}` и описав проблему.\nУдачи!", parse_mode=ParseMode.MARKDOWN)
                        else:
                            await message.answer("***Слишком короткий ник, попробуйте еще раз***", parse_mode=ParseMode.MARKDOWN)
                    else:
                        await message.answer("***Недостаточно средств.***", parse_mode=ParseMode.MARKDOWN)
                        await state.finish()
                else:
                    await message.answer("***Минимальная сумма пополнения - 0.5 TAKE. Попробуйте еще раз.***", parse_mode=ParseMode.MARKDOWN)
        except:
            await message.answer("***Некорректные данные, введите ник и сумму по порядку 0.5, TMPhobos***", parse_mode=ParseMode.MARKDOWN)

@dp.callback_query_handler(text = "procproced")
async def proc(callback: types.CallbackQuery):
    await callback.message.edit_text(f"ВЫПОЛНЕНО\n{callback.message.text}")
    lines = callback.message.text.split('\n')
    uid = lines[5].split(': ')[1]
    balance = lines[2].split(': ')[1]
    nick = lines[4].split(': ')[1]
    await bot.send_message(uid, f"Ваш баланс на сервере(Ник: ***{nick}***) был пополнен на сумму ***{balance} TAKE***.\nПотратьте с умом!", parse_mode=ParseMode.MARKDOWN)

@dp.callback_query_handler(text = "botpoc")
async def proc(callback: types.CallbackQuery):
    await callback.message.delete()
    await bot.send_message(callback.from_user.id, "***Введите сумму пополнения...***", parse_mode=ParseMode.MARKDOWN)
    await Form.amount.set()

@dp.message_handler(state=Form.amount)
async def process_sum(message: types.Message, state: FSMContext):
    valid = False
    try:
        float(message.text)
        valid = True
    except:
        pass
    if message.text == "/cancel":
        await message.reply("***Пополнение отменено***", parse_mode=ParseMode.MARKDOWN)
        await state.finish()
    elif valid and float(message.text)>0:
        url = 'https://pay.ton-rocket.com/tg-invoices'
        headers = {
            "accept": "application/json",
            "Rocket-Pay-Key": f"{config.API_TOKEN}",
            "Content-Type": "application/json"
        }
        data = f'''{"{"}
            "amount": {float(message.text)},
            "numPayments": 1,
            "currency": "TAKE",
            "description": "Pay check for {float(message.text)} TAKE",
            "hiddenMessage": "{message.from_user.id}",
            "callbackUrl": "https://t.me/ton_rocket",
            "payload": "some custom payload I want to see in webhook or when I request invoice",
            "expiredIn": 900
        {"}"}'''
        print(data)
        #data = f"{data}".encode()
        rept = requests.post(url, data=data, headers = headers)
        req = rept.json()
        print(req)
        await message.answer(f'''Вы оформили счет на ***{message.text} TAKE***
Перейти к оплате можно по [ссылке.]({req['data']['link']})
Через 15 минут счет станет *невалидным*.''', parse_mode=ParseMode.MARKDOWN)
        await state.finish()
    else:
        await message.answer('***Некорректные данные.*** Попробуйте еще раз...', parse_mode=ParseMode.MARKDOWN)


if __name__ == '__main__':
    ex = executor.Executor(dp)

    ex.loop.create_task(take.start())

    ex.start_polling()
