from aiogram import F, Router
from aiogram.types import CallbackQuery
from aiogram.utils.deep_linking import create_start_link

from createbot import bot


inline_kb_router = Router()


@inline_kb_router.callback_query(F.data == "make_link")
async def make_link(callback: CallbackQuery) -> None:
    link = await create_start_link(bot, callback.from_user.username, encode=True)
    await bot.send_message(
        chat_id=callback.message.chat.id,
        text=(
            "<b>Разместите эту ссылку⬇️</b> в описании своего профиля Telegram, "
            "TikTok, Instagram или в канале Telegram.\n\n"
            f"{link}\n\n"
            "<a href='https://t.me/questions_anonbot'>Анонимные вопросы</a>"
        ),
    )
