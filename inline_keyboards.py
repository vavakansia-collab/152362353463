from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton


kb_start = InlineKeyboardBuilder()
kb_start.add(
    InlineKeyboardButton(
        text="🔗 Ссылка для анонимных вопросов",
        callback_data="make_link",
    )
)

kb_ask_more = InlineKeyboardBuilder()
kb_ask_more.add(
    InlineKeyboardButton(
        text="🔁 Написать еще",
        callback_data="ask_more",
    )
)

kb_share = InlineKeyboardBuilder()
kb_share.add(
    InlineKeyboardButton(
        text="🔗 Поделиться",
        callback_data="share_link",
    )
)
