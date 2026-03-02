from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import InlineKeyboardBuilder

from createbot import bot
from config import ADMIN_IDS
from sqlite_db import sql_get_all_users, sql_get_user_info, sql_set_block_status
import asyncio

admin_router = Router()

class AdminStates(StatesGroup):
    waiting_for_broadcast_text = State()
    waiting_for_search_id = State()
    waiting_for_block_id = State()

def get_admin_kb():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔍 Поиск юзера", callback_data="admin_search"))
    builder.row(types.InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast"))
    builder.row(types.InlineKeyboardButton(text="🚫 Блокировка/Разблокировка", callback_data="admin_block_panel"))
    return builder.as_markup()

@admin_router.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    await message.answer("🛠 Админ-панель:", reply_markup=get_admin_kb())

@admin_router.callback_query(F.data == "admin_search")
async def start_search(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("Введите Telegram ID пользователя для поиска:")
    await state.set_state(AdminStates.waiting_for_search_id)

@admin_router.message(AdminStates.waiting_for_search_id)
async def process_search(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text)
        user_info = await sql_get_user_info(user_id)
        if user_info:
            uid, username, reg_date, blocked = user_info
            status = "🚫 Заблокирован" if blocked else "✅ Активен"
            await message.answer(f"👤 Информация о пользователе:\n"
                                 f"ID: <code>{uid}</code>\n"
                                 f"Username: @{username if username else 'Нет'}\n"
                                 f"Дата регистрации: {reg_date}\n"
                                 f"Статус: {status}")
        else:
            await message.answer("❌ Пользователь не найден в базе.")
    except ValueError:
        await message.answer("❌ Введите корректный числовой ID.")
    await state.clear()

@admin_router.callback_query(F.data == "admin_broadcast")
async def start_broadcast(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("Введите текст для рассылки всем пользователям:")
    await state.set_state(AdminStates.waiting_for_broadcast_text)

@admin_router.message(AdminStates.waiting_for_broadcast_text)
async def process_broadcast(message: types.Message, state: FSMContext):
    broadcast_text = message.text
    users = await sql_get_all_users()
    count = 0
    await message.answer(f"🚀 Начинаю рассылку на {len(users)} пользователей...")
    
    for user in users:
        try:
            await bot.send_message(user[0], broadcast_text)
            count += 1
            await asyncio.sleep(0.05) # Small delay to avoid flood
        except Exception:
            pass
            
    await message.answer(f"✅ Рассылка завершена. Успешно отправлено: {count}")
    await state.clear()

@admin_router.callback_query(F.data == "admin_block_panel")
async def start_block(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("Введите Telegram ID пользователя для блокировки/разблокировки:")
    await state.set_state(AdminStates.waiting_for_block_id)

@admin_router.message(AdminStates.waiting_for_block_id)
async def process_block(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text)
        user_info = await sql_get_user_info(user_id)
        if user_info:
            new_status = 1 if not user_info[3] else 0
            await sql_set_block_status(user_id, new_status)
            status_text = "заблокирован" if new_status else "разблокирован"
            await message.answer(f"✅ Пользователь <code>{user_id}</code> успешно {status_text}.")
        else:
            await message.answer("❌ Пользователь не найден в базе.")
    except ValueError:
        await message.answer("❌ Введите корректный числовой ID.")
    await state.clear()
