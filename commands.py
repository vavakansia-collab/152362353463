import html
from dataclasses import dataclass

from aiogram import types, Router, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.payload import decode_payload

from sqlite_db import sql_add_id, sql_select_id, sql_add_message
from inline_keyboards import kb_start, kb_ask_more
from createbot import *
from config import LOG_CHAT_ID
from loggers import handlers_logger


commands_router = Router()


@dataclass
class TargetContext:
    recipient_id: int
    recipient_label: str


@dataclass
class RouteContext:
    owner_id: int
    owner_label: str
    peer_id: int
    peer_label: str


route_registry: dict[int, RouteContext] = {}
user_targets: dict[int, TargetContext] = {}


class Form(StatesGroup):
    question = State()


def _quote(text: str) -> str:
    escaped = html.escape(text or "")
    return f"<blockquote>{escaped}</blockquote>"


def _format_message_body(body: str) -> str:
    return f"👁️‍🗨️Новое сообщение:\n\n{_quote(body)}\n\n↪️ Свайпни для ответа"


def _user_label(user: types.User) -> str:
    if user.username:
        return f"@{user.username}"
    if user.full_name:
        return user.full_name
    return f"id{user.id}"


def _username_label(username: str | None, user_id: int | None) -> str:
    if username:
        return f"@{username}"
    if user_id:
        return f"id{user_id}"
    return "неизвестно"


async def _report_route(text: str | None, sender_label: str | None, recipient_label: str | None) -> None:
    if not LOG_CHAT_ID:
        return
    safe_text = html.escape(text or "", quote=False)
    sender = sender_label or "неизвестно"
    recipient = recipient_label or "неизвестно"
    log_text = f'Сообщение "{safe_text}" от пользователя {sender} к пользователю {recipient}'
    await bot.send_message(chat_id=LOG_CHAT_ID, text=log_text)


@commands_router.message(CommandStart(deep_link=True))
async def command_handler_start_referral(message: types.Message, command: CommandObject, state: FSMContext):
    args = command.args
    recipient = decode_payload(args)
    username = message.from_user.username
    if not recipient == username:
        await sql_add_id(message)
        recipient_record = await sql_select_id(recipient)
        if not recipient_record:
            await message.answer("❌ Пользователь ещё не зарегистрировался в боте.")
            return
        recipient_id = recipient_record[0]
        recipient_label = _username_label(recipient, recipient_id)
        user_targets[message.from_user.id] = TargetContext(recipient_id, recipient_label)
        await state.set_state(Form.question)
        recipient_display = recipient or "пользователю"
        await message.answer(f"Задайте любой вопрос пользователю")
    else:
        handlers_logger.warning(f"Пользователь {message.from_user.id}-{username} написал самому себе по ссылке")
        await message.answer("❌ Вы не можете писать самому себе")


@commands_router.message(Form.question)
async def process_question(message: types.Message, state: FSMContext):
    target = user_targets.get(message.from_user.id)
    if not target:
        await message.answer("❌ Ссылка устарела. Получите новую персональную ссылку для отправки вопроса.")
        await state.clear()
        return

    question_text = message.text
    sender_label = _user_label(message.from_user)

    await sql_add_message(message, question_text, target.recipient_id)
    await message.reply("⚡️Сообщение отправлено!", reply_markup=kb_ask_more.as_markup())

    forwarded = await bot.send_message(chat_id=target.recipient_id, text=_format_message_body(question_text))
    route_registry[forwarded.message_id] = RouteContext(
        owner_id=target.recipient_id,
        owner_label=target.recipient_label,
        peer_id=message.from_user.id,
        peer_label=sender_label,
    )
    await _report_route(question_text, sender_label, target.recipient_label)
    await state.clear()


@commands_router.message(F.reply_to_message)
async def handle_reply(message: types.Message):
    replied_msg = message.reply_to_message
    if replied_msg.from_user.id != (await message.bot.me()).id:
        return

    route = route_registry.get(replied_msg.message_id)
    if not route:
        return

    if message.chat.id != route.owner_id:
        return

    sender_label = _user_label(message.from_user)
    recipient_label = route.peer_label or _username_label(None, route.peer_id)

    await sql_add_message(message, message.text, route.peer_id)
    forwarded = await bot.send_message(text=_format_message_body(message.text), chat_id=route.peer_id)
    route_registry[forwarded.message_id] = RouteContext(
        owner_id=route.peer_id,
        owner_label=route.peer_label,
        peer_id=route.owner_id,
        peer_label=sender_label,
    )
    await message.reply("⚡️Ответ отправлен!")
    await _report_route(
        message.text,
        sender_label,
        recipient_label,
    )


@commands_router.message(CommandStart())
async def command_handler_start(message: types.Message):
    await sql_add_id(message)
    await message.answer(f'🙋 Добро пожаловать в бота для анонимных вопросов - <a href="https://t.me/questions_anonbot">Анонимные вопросы</a>.\n\n<b>Начните получать анонимные вопросы прямо сейчас!!!</b>\n\nДля этого создайте ссылку нажав на кнопку ниже ⬇️', reply_markup=kb_start.as_markup())


@commands_router.callback_query(F.data == "ask_more")
async def callback_ask_more(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    if callback.from_user.id not in user_targets:
        await callback.message.answer("❌ Для начала откройте персональную ссылку получателя и задайте первый вопрос.")
        return
    await state.set_state(Form.question)
    await callback.message.answer("Введите ещё один вопрос")
