import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.utils.markdown import hbold
from aiogram.types.callback_query import CallbackQuery
from aiogram.types.user import User

import json
import kb
import pickle
import random


config = None
texts = None
bot: Bot = None
ready_indexes = {}
games = []

dp = Dispatcher()


class Player:
    name = "player"
    id = 0
    elo = 1500
    history = {}
    state = "none"
    game = -1

    def __init__(self, name, id) -> None:
        self.name = name
        self.id = id

users = []
try:
    with open("users.bin", "rb") as f:
        users = pickle.load(f)
except FileNotFoundError:
    with open('users.bin', "wb") as f:
        pickle.dump(users, f)


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    
    for user in users:
        if user.id == message.from_user.id:
            await message.answer(texts["start_message"].format(user=users[index_of(message.from_user)].name), reply_markup=kb.menu)
            reset(message.from_user)
            return
        
    await message.answer(texts["start_message"].format(user=message.from_user.first_name), reply_markup=kb.menu)
    users.append(Player(message.from_user.first_name, message.from_user.id))
    write_to_binary()

    reset(message.from_user)

@dp.callback_query(F.data == "history")
@dp.callback_query(F.data == "replay")
async def profile(clbck: CallbackQuery):
    await clbck.answer(texts["non_func"])

@dp.callback_query(F.data == "game")
async def profile(clbck: CallbackQuery):
    global ready_indexes
    
    await clbck.message.edit_reply_markup()
    answer = await clbck.message.answer(texts["game_search"], reply_markup=kb.game)

    index = index_of(clbck.from_user)
    users[index].state = "search"
    if not index in ready_indexes.keys():
        ready_indexes[index] = [answer, 0]
    
    for key in ready_indexes.keys():
        if key == index:
            continue
        if ready_indexes[key][1] == 0:
            await game(key, index)
            break
        

@dp.callback_query(F.data == "private_game")
async def profile(clbck: CallbackQuery):
    global ready_indexes
    
    await clbck.message.edit_reply_markup()
    code = random.randint(10000, 99999)
    answer = await clbck.message.answer(texts["find"].format(code=code), reply_markup=kb.game)

    index = index_of(clbck.from_user)
    users[index].state = "search_for"
    ready_indexes[index] = [answer, code]


@dp.callback_query(F.data == "profile")
async def profile(clbck: CallbackQuery):
    reset(clbck.from_user)

    await clbck.message.edit_reply_markup()
    await show_profile(clbck.from_user, clbck.message)
    
    
@dp.callback_query(F.data == "change_name")
async def profile(clbck: CallbackQuery):

    await clbck.message.edit_reply_markup()
    await clbck.message.answer(texts["change_name"])
    users[index_of(clbck.from_user)].state = "change_name"

@dp.callback_query(F.data == "menu")
async def profile(clbck: CallbackQuery):
    reset(clbck.from_user)
    await clbck.message.edit_reply_markup()
    await clbck.message.answer(texts["menu_message"], reply_markup=kb.menu)


@dp.message()
async def mes(message: types.Message) -> None:
    
    index = index_of(message.from_user)
    if users[index].state == "change_name":
        users[index].name = message.text
        users[index].state = "none"
        write_to_binary()

        await show_profile(message.from_user, message)

    elif users[index].state == "search_for":
        try:
            int_code = int(message.text)
        except ValueError:
            await message.answer(texts["wrong_code"])
            return
        for key in ready_indexes.keys():
            if ready_indexes[key][1] == int_code:
                if key == index_of(message.from_user):
                    await message.answer(texts["your_code"])
                    return
                await game(key, index_of(message.from_user))
                return
        await message.answer(texts["not_found"])

    elif users[index].state == "game":
        for i in range(len(games) - 1, -1, -1):
            if games[i]["player1"] == users[index]:
                await games[i]["message2"].answer(message.text)
                return
            elif games[i]["player2"] == users[index]:
                await games[i]["message1"].answer(message.text)
                return


async def game(player1: int, player2: int):
    global ready_indexes

    players = [[users[player1], ready_indexes[player1][0]], [users[player2], ready_indexes[player2][0]]]

    del ready_indexes[player1]
    del ready_indexes[player2]

    hod = random.randint(1, 2)

    for i in range(2):
        players[i][0].state = "game"
        players[i][0].game = len(games)
        await players[i][1].answer(texts["start"].format(name1=players[0][0].name, name2=players[1][0].name))

    ikm = kb.create_matrx([[0, 0, 0], [0, 0, 0], [0, 0, 0]])
    message1 = await players[(-1 * hod) + 2][1].answer(texts["move"], reply_markup=ikm, parse_mode="MarkdownV2")
    message2 = await players[hod - 1][1].answer(texts["wait"], reply_markup=ikm, parse_mode="MarkdownV2")

    games.append({
        "board": [[0,0,0], [0,0,0], [0,0,0]],
        "message1": message1,
        "message2": message2,
        "player1": players[(-1 * hod) + 2][0],
        "player2": players[hod - 1][0],
        "hod": 1
    })

    await players[0][1].delete()
    await players[1][1].delete()


async def move(data, user):
    if user.state != "game":
        return
    if user.game < 0:
        return
    if user.game + 1 > len(games):
        return
    game = games[user.game]
    player_number = 2 if game["player2"] == user else 1
    hod = game["hod"]
    if hod != player_number:
        return
    board = game["board"]
    if board[int(data[1])][int(data[0])] != 0:
        return
    
    board[int(data[1])][int(data[0])] = player_number
    games[user.game]["hod"] = 1 if hod == 2 else 2
    games[user.game]["board"] = board

    ikm = kb.create_matrx(board)
    await types.Message.edit_text(self=game["message1"], text=texts["move"] if hod == 2 else texts["wait"], reply_markup=ikm, parse_mode="MarkdownV2")
    await types.Message.edit_text(self=game["message2"], text=texts["wait"] if hod == 2 else texts["move"], reply_markup=ikm, parse_mode="MarkdownV2")

    await win(game)

async def win(game):
    board = game["board"]
    win = -1
    for i in range(3):
        if board[i][0] != 0 and board[i][0] == board[i][1] and board[i][0] == board[i][2]:
            win = board[i][0]
            break
        if board[0][i] != 0 and board[0][i] == board[1][i] and board[0][i] == board[2][i]:
            win = board[0][i]
            break
    if win == -1:
        if board[0][0] != 0 and board[0][0] == board[1][1] and board[0][0] == board[2][2]:
            win = board[0][0]
        elif board[0][2] != 0 and board[0][2] == board[1][1] and board[0][2] == board[2][0]:
            win = board[0][2]
        elif board[0][0] != 0 and board[0][1] != 0 and board[0][2] != 0 and board[1][0] != 0 and board[1][1] != 0 and board[1][2] != 0 and board[2][0] != 0 and board[2][1] != 0 and board[2][2] != 0:
            win = 0
    
    if win == -1:
        return
    
    ikm = kb.create_matrx(board)
    await types.Message.edit_text(self=game["message1"], text=texts["end"], reply_markup=ikm, parse_mode="MarkdownV2")
    await types.Message.edit_text(self=game["message2"], text=texts["end"], reply_markup=ikm, parse_mode="MarkdownV2")

    elo1 = game["player1"].elo
    elo2 = game["player2"].elo
    elo1_ = count_elo(elo1, elo2, 1.0 if win == 1 else 0.0 if win == 2 else 0.5)
    elo2_ = count_elo(elo2, elo1, 1.0 if win == 2 else 0.0 if win == 1 else 0.5)
    final_elo1 = str(elo1) + ("+" if elo1_ >= 0 else "") + str(elo1_)
    final_elo2 = str(elo2) + ("+" if elo2_ >= 0 else "") + str(elo2_)

    if win == 1:
        await game["message1"].answer(texts["win"].format(elo=final_elo1), reply_markup=kb.again)
        await game["message2"].answer(texts["lose"].format(elo=final_elo2), reply_markup=kb.again)
    elif win == 2:
        await game["message1"].answer(texts["lose"].format(elo=final_elo1), reply_markup=kb.again)
        await game["message2"].answer(texts["win"].format(elo=final_elo2), reply_markup=kb.again)
    else:
        await game["message1"].answer(texts["draw"].format(elo=final_elo1), reply_markup=kb.again)
        await game["message2"].answer(texts["draw"].format(elo=final_elo2), reply_markup=kb.again)

    game["player1"].state = "none"
    game["player2"].state = "none"
    game["player1"].elo = elo1 + elo1_
    game["player2"].elo = elo2 + elo2_

    write_to_binary()

def count_elo(elo1: int, elo2: int, win_c: float) -> int:
    ea = 1.0 / (1.0 + float(10 ^ (elo2 - elo1)))
    if win_c == 0.0:
        return -int(16 * (1 - ea))
    return int(16 * (win_c - ea))


async def show_profile(user: User, message: types.Message):
    index = index_of(user)
    await message.answer(texts["profile"].format(name=users[index].name, elo=users[index].elo, history=""),
        reply_markup=kb.profile)
    
def write_to_binary():
    with open("users.bin", "wb") as f:
        pickle.dump(users, f)

def reset(user: User):
    global ready_indexes

    index = index_of(user)
    if index in ready_indexes.keys():
        del ready_indexes[index]
        users[index].state = "none"

def index_of(user: User):
    return next(i for i in range(len(users)) if users[i].id==user.id)


async def main() -> None:
    global config, texts, bot

    with open("config.json") as f:
        config = json.load(f)
    with open("texts.json", encoding="utf8") as f:
        texts = json.load(f)

    bot = Bot(config["TOKEN"], parse_mode=ParseMode.HTML)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


@dp.callback_query(F.data == "b00")
async def profile(clbck: CallbackQuery):
    await move("00", users[index_of(clbck.from_user)])
@dp.callback_query(F.data == "b01")
async def profile(clbck: CallbackQuery):
    await move("01", users[index_of(clbck.from_user)])
@dp.callback_query(F.data == "b02")
async def profile(clbck: CallbackQuery):
    await move("02", users[index_of(clbck.from_user)])
@dp.callback_query(F.data == "b10")
async def profile(clbck: CallbackQuery):
    await move("10", users[index_of(clbck.from_user)])
@dp.callback_query(F.data == "b11")
async def profile(clbck: CallbackQuery):
    await move("11", users[index_of(clbck.from_user)])
@dp.callback_query(F.data == "b12")
async def profile(clbck: CallbackQuery):
    await move("12", users[index_of(clbck.from_user)])
@dp.callback_query(F.data == "b20")
async def profile(clbck: CallbackQuery):
    await move("20", users[index_of(clbck.from_user)])
@dp.callback_query(F.data == "b21")
async def profile(clbck: CallbackQuery):
    await move("21", users[index_of(clbck.from_user)])
@dp.callback_query(F.data == "b22")
async def profile(clbck: CallbackQuery):
    await move("22", users[index_of(clbck.from_user)])


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())