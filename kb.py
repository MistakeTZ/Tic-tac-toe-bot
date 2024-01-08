from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

marks = [" ", "❌", "🔵"]

menu_buttons = [
    [InlineKeyboardButton(text="📝 Профиль", callback_data="profile")],
    [InlineKeyboardButton(text="🔎 Игра против рандомов", callback_data="game"),
    InlineKeyboardButton(text="🔎 Приватная игра", callback_data="private_game")]
]
menu = InlineKeyboardMarkup(inline_keyboard=menu_buttons)

profile_buttons = [
    [InlineKeyboardButton(text="🖋️ Изменить имя", callback_data="change_name"),
    InlineKeyboardButton(text="📜 Посмотреть историю", callback_data="history")],
    [InlineKeyboardButton(text="🔙 Вернуться", callback_data="menu")]
]
profile = InlineKeyboardMarkup(inline_keyboard=profile_buttons)

game = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Вернуться", callback_data="menu")]])

again_buttons = [
    [InlineKeyboardButton(text="🔄️ Сыграть снова", callback_data="game"),
    InlineKeyboardButton(text="⚔️ Реванш", callback_data="replay")],
    [InlineKeyboardButton(text="🔙 Вернуться", callback_data="menu")]
]
again = InlineKeyboardMarkup(inline_keyboard=again_buttons)


def create_matrx(arr: list) -> InlineKeyboardMarkup:
    buttons = []
    for y in range(3):
        buttons.append([void_but(), void_but()])
        for x in range(3):
            buttons[y].append(InlineKeyboardButton(text=marks[arr[y][x]], callback_data=f"b{x}{y}"))
        buttons[y].append(void_but())
        buttons[y].append(void_but())

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def void_but() -> InlineKeyboardButton:
    return InlineKeyboardButton(text="🟩", callback_data="none")