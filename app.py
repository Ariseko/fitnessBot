from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

import sqlite3 as sq

files_list = (1, 6, 13, 71, 80)

base = sq.connect('quest.db')
cursor = base.cursor()
base.execute('CREATE TABLE IF NOT EXISTS answers (id INTEGER PRIMARY KEY AUTOINCREMENT,'
             'parent_id INTEGER,'
             'title TEXT,'
             'message_text TEXT,'
             'file TEXT)')
base.execute('CREATE TABLE IF NOT EXISTS states (id INTEGER, node_id INTEGER)')
base.commit()

storage = MemoryStorage()
bot = Bot(token='5780779424:AAHqlAMKzVkYM7fYek89Mxnx7HyPD3GJXzc')
dp = Dispatcher(bot, storage=MemoryStorage())


class FSMtest(StatesGroup):
    zero_consult = State()
    consult_first = State()
    consult_second = State()

    parent_id = State()
    title = State()
    message_text = State()

    start_edit = State()
    edit_choose = State()
    edit_content = State()
    edit_commit = State()

    show_message = State()

    delete_start = State()
    delete_get_id = State


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    photo = open('files/zero.jpg', 'rb')
    existion = bool(
        cursor.execute(f'SELECT EXISTS(SELECT id FROM states WHERE id = {message.from_user.id})').fetchone()[0])

    start_message = cursor.execute(f'SELECT message_text FROM answers WHERE id = 0').fetchone()[0]

    start_button = 'Абонемент в зал'
    start_dialog = ReplyKeyboardMarkup(resize_keyboard=True)
    start_dialog.add(start_button)

    if existion is True:
        await message.answer('🔹 _Подпишись_ на канал в телеге - https://t.me/+EAi2GUBEB7JlY2Qy \n'
                             '🔹В нем много полезной инфы🔝')
        await bot.send_photo(message.chat.id, photo=photo)
        await message.answer(start_message, reply_markup=start_dialog)
        cursor.execute(f'UPDATE states SET node_id = 0 WHERE id = {message.from_user.id}')
        base.commit()
    else:
        cursor.execute(f'INSERT INTO states (id, node_id) VALUES ({message.from_user.id}, 0)')
        base.commit()
        await bot.send_photo(message.chat.id, photo=photo)
        await message.answer(start_message, reply_markup=start_dialog)


@dp.message_handler(state=FSMtest.consult_first)
async def first_consult(messsage: types.Message, state: FSMContext):
    if messsage.text == 'Получить бесплатную консультацию':
        await messsage.answer('Отлично! Тогда напишите мне пожалуйста Ваше '
                              'Имя, возраст, главную фитнес цель и номер телефона'
                              '\n\nПример:'
                              '\n\nИванов Иван Иванович'
                              '\nХочу сбросить вес'
                              '\n28 лет')
        await FSMtest.consult_second.set()
    else:
        restart_kb = ReplyKeyboardMarkup(resize_keyboard=True)
        restart_btn = KeyboardButton('/start')
        restart_kb.add(restart_btn)
        await messsage.answer('Чтобы начать заново, пожалуйста, нажмите на кнопку', reply_markup=restart_kb)
        await state.finish()


@dp.message_handler(state=FSMtest.consult_second)
async def second_consult(message: types.Message, state: FSMContext):
    zayavka = f'@{message.from_user.username}\n' \
              f'{message.text}'

    restart_kb = ReplyKeyboardMarkup(resize_keyboard=True)
    restart_btn = KeyboardButton('/start')
    restart_kb.add(restart_btn)

    await bot.send_message(337652760, zayavka)
    await message.answer('Отлично! Ваш тренер в скором времени с вами свяжется.'
                         'А пока можете пройти игру заново', reply_markup=restart_kb)

    await state.finish()


@dp.message_handler(commands=['new'])
async def start_insert(message: types.Message):
    await FSMtest.parent_id.set()
    await message.answer(f'id родителя')


@dp.message_handler(commands=['edit'])
async def edit(message: types.Message):
    await FSMtest.start_edit.set()
    await message.answer('Введи id сообщения, которое хочешь поправить')


@dp.message_handler(commands=['show'])
async def start_show(message: types.Message):
    await FSMtest.show_message.set()
    await message.answer('Введи id сообщения, которое хочешь посмотреть')


@dp.message_handler(commands=['delete'])
async def delete(message: types.Message):
    delete_kb = ReplyKeyboardMarkup(resize_keyboard=True)
    delete_yes_btn = KeyboardButton('Да')
    delete_no_btn = KeyboardButton('Нет')

    delete_kb.add(delete_yes_btn).add(delete_no_btn)
    await message.answer('При удалении, все сообщения, которые идут после него'
                         ' будут идти после родителя удаленного сообщения, ты точно хочешь удалить?',
                         reply_markup=delete_kb)
    await FSMtest.delete_start.set()


@dp.message_handler(state=FSMtest.delete_start)
async def delete_start(message: types.Message, state: FSMContext):
    if message.text == 'Да':
        await message.answer('Введи номер сообщения для удаления')
        await FSMtest.next()
    else:
        await message.answer('Отмена операции')
        await state.finish()


@dp.message_handler(state=FSMtest.delete_get_id)
async def delete_procceed(message: types.Message, state: FSMContext):
    await message.answer('Сообщение удаляется...')
    list_of_deleted_childs = cursor.execute(f'select id from answers where parent_id = {message.text}').fetchall()


# ##########################################################################################################################

@dp.message_handler(state=FSMtest.show_message)
async def show(message: types.Message, state: FSMContext):
    message_to_show = cursor.execute(f'SELECT * FROM answers WHERE id = {message.text}').fetchone()
    await message.answer(f'id: {message_to_show[0]}\n'
                         f'id родителя: {message_to_show[1]}\n'
                         f'Кнопка: {message_to_show[2]}\n'
                         f'Текст: {message_to_show[3]}')
    # print(message_to_show)
    await state.finish()


# ##########################################################################################################################


@dp.message_handler(state=FSMtest.parent_id)
async def get_parents_id(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        try:
            data['parent_id'] = int(message.text)
            await message.answer('Текст кнопки')
        except():
            await message.answer('Error')

    await FSMtest.title.set()


@dp.message_handler(state=FSMtest.title)
async def get_title(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        try:
            data["title"] = message.text
            await message.answer("Введи сообщение")
        except():
            await message.answer('Error')

    await FSMtest.message_text.set()


@dp.message_handler(state=FSMtest.message_text)
async def get_message(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['message_text'] = message.text
        await message.answer(f"кнопка{data['title']}")
        cursor.execute(f'INSERT INTO answers(parent_id, title, message_text, file) VALUES (?, ?, ?, NULL)',
                       tuple(data.values()))
        base.commit()
        addedMessageId = cursor.execute(
            f'SELECT id from answers where parent_id = {data["parent_id"]} and title = "{data["title"]}"').fetchone()
        await message.answer(f'id добавленного сообщения {addedMessageId}')

    await state.finish()


# ##########################################################################################################################

@dp.message_handler(state=FSMtest.start_edit)
async def fork(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['id'] = int(message.text)

    edit_kb = ReplyKeyboardMarkup(resize_keyboard=True)
    edit_parent_id_btn = KeyboardButton('Изменить родителя')
    edit_title_btn = KeyboardButton('Изменить кнпоку')
    edit_text_btn = KeyboardButton('Изменить текст')
    edit_kb.add(edit_parent_id_btn).add(edit_title_btn).add(edit_text_btn)

    await message.answer('Выбери что хочешь отредачить', reply_markup=edit_kb)
    await FSMtest.edit_choose.set()


@dp.message_handler(state=FSMtest.edit_choose)
async def edit_choose(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['change_object'] = message.text
    await FSMtest.edit_content.set()
    await message.answer('На что поменять?')


@dp.message_handler(state=FSMtest.edit_content)
async def edit_content(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        try:
            if data['change_object'] == 'Изменить родителя':
                cursor.execute(f'UPDATE answers SET parent_id = {int(message.text)} WHERE id = {data["id"]}')
                base.commit()
            elif data['change_object'] == 'Изменить кнпоку':
                cursor.execute(f'UPDATE answers SET title = "{message.text}" WHERE id = {data["id"]}')
                base.commit()
            elif data['change_object'] == 'Изменить текст':
                cursor.execute(f'UPDATE answers SET message_text = "{message.text}" WHERE id = {data["id"]}')
                base.commit()

            await state.finish()

        except:
            await message.answer('Что то пошло не так, напиши Басе')
            await state.finish()


@dp.message_handler()
async def handler(message: types.Message):
    dialog = ReplyKeyboardMarkup(resize_keyboard=True)
    previous_node_id = cursor.execute(f'SELECT node_id FROM states WHERE id = {message.from_user.id}').fetchone()[0]
    current_node = cursor.execute(
        f"SELECT * FROM answers WHERE parent_id = {previous_node_id} and title = '{message.text}'").fetchall()[0]
    message_text = current_node[3]
    next = current_node[0]
    next_nodes = cursor.execute(f'SELECT * FROM answers WHERE parent_id = {next}').fetchall()

    for item in next_nodes:
        dialog.add(item[2])

    if current_node[0] == 1:
        photo = open('files/first.jpg', 'rb')
        await bot.send_photo(message.chat.id, photo=photo)
    elif current_node[0] == 2:
        photo = open('files/second.jpg', 'rb')
        await bot.send_photo(message.chat.id, photo=photo)

    if len(next_nodes) != 0:
        await message.answer(message_text, reply_markup=dialog)
        next_node_id = current_node[0]
        cursor.execute(f'UPDATE states SET node_id = {next_node_id} WHERE id = {message.from_user.id}')
        base.commit()
    elif len(next_nodes) == 0:
        consult_kb = ReplyKeyboardMarkup(resize_keyboard=True)
        consult_btn_0 = KeyboardButton('Начать заново')
        consult_btn_1 = KeyboardButton('Получить бесплатную консультацию')
        consult_kb.add(consult_btn_0).add(consult_btn_1)
        await message.answer(message_text, reply_markup=consult_kb)
        next_node_id = current_node[0]
        cursor.execute(f'UPDATE states SET node_id = {next_node_id} WHERE id = {message.from_user.id}')
        base.commit()
        await FSMtest.consult_first.set()

    if current_node[0] in files_list:
        await message.reply_document(open(f'files/{current_node[0]}.pdf', 'rb'),
                                     caption='Сохрани себе в избранное, чтоб не потерять😉')


executor.start_polling(dp, skip_updates=True)
