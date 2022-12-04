from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

import sqlite3 as sq

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
bot = Bot(token='5634919470:AAHVMnHME0ZpzDcqZwfcKBX3glIZ7tW9xDQ')
dp = Dispatcher(bot, storage=MemoryStorage())


class FSMtest(StatesGroup):
    parent_id = State()
    title = State()
    message_text = State()

    start_edit = State()
    edit_choose = State()
    edit_content = State()
    edit_commit = State()

    show_message = State()


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer('В боковом меню все нужные команды')


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
    await message.answer('В разработке')


# ##########################################################################################################################

@dp.message_handler(state=FSMtest.show_message)
async def show(message: types.Message, state: FSMContext):
    message_to_show = cursor.execute(f'SELECT * FROM answers WHERE id = {message.text}').fetchall()
    # await message.answer(f'id: {message_to_show[0]}\n'
    #                      f'id родителя: {message_to_show[1]}\n'
    #                      f'Кнопка: {message_to_show[2]}\n'
    #                      f'Текст: {message_to_show[3]}')
    print(message_to_show)
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
        await message.answer(data['message_text'])
        cursor.execute(f'INSERT INTO answers(parent_id, title, message_text, file) VALUES (?, ?, ?, NULL)',
                       tuple(data.values()))
        base.commit()

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


executor.start_polling(dp, skip_updates=True)
