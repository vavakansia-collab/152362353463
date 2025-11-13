from aiogram import F, Router
from aiogram.types import CallbackQuery, FSInputFile
from aiogram.utils.deep_linking import create_start_link

from createbot import bot


inline_kb_router = Router()


@inline_kb_router.callback_query(F.data == "make_link")
async def make_link(callback: CallbackQuery) -> None:
    link = await create_start_link(bot, callback.from_user.username, encode=True)
    await bot.send_photo(
        chat_id=callback.message.chat.id,
        photo=FSInputFile("question.png"),
        caption=(
            "🔗 Начни получать анонимные сообщения прямо сейчас!\n\n"
            "Твоя личная ссылка:\n"
            f"👉 {link}\n\n"
            "Размести эту ссылку в своём профиле Telegram ● Instagram ● TikTok "
            "или других соц. сетях, чтобы начать получать сообщения 💬"
        ),
    )
