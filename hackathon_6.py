from telebot import TeleBot
from telebot.types import (
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
    )
from dotenv import load_dotenv
import os
from pathlib import Path
from time import sleep
from typing import List, Dict, Union
import db
import datetime
import os
from random import choice
import json

load_dotenv()
# константы.
TOKEN = os.getenv("TOKEN")
BASE_DIR = Path(__file__).resolve().parent
DB_DIR = BASE_DIR / "db.db"
FILE_BOOSTS = BASE_DIR / "boosts.json"
# оптмимизация в виде хранения в словаре/списке.
state = {"starting" : True, "active" : False, "make_quest" : False, "fighting" : False}
question = [
        {
            "человек паук" : "Он бросает что-то липкое, аж дрожит его рука.\nЛипка, липка, но не крепка, чтобы равной быть со мной."
            },
        {
            "тор" : "Гром несётся сквозь долину.\nУж таков, неутешим. Лишь ты хоть позли его-то, будет гром с грозой жестокой."
            }, 
        {
            "железный человек" : "Он железный, но не сломается,\nВ бою всегда впереди покажется.\nСнарядов преграды он не боится"
            }
    ]
list_this_question = list()
heroes = list()
warrior = [
    ["Разбойник", 12, 23, 11],
    ["Ведьма", 5, 34, 2],
    ["Палладин", 65, 10, 22]
    ]
# октрываем json-файл, если он существует.
if os.path.exists(FILE_BOOSTS):
    with open(FILE_BOOSTS, "r", encoding="utf-8") as file:
        data_boosts = json.load(file)
else:
    data_boosts = dict()

bot = TeleBot(token=TOKEN)
# суперкласс для квеста.
class Sprite:
    def __init__(self, name : Union[str], health : Union[int], damage : Union[int], defend : Union[int], win=0):
        self.name = name
        self.health = health
        self.damage = damage * 2 if "X2 урон" in data_boosts else damage
        self.defend = defend
        self.win = win
    # информация о герое.
    def get_info(self):
        return f"<i><b>Ифнормация о {self.name}\nЗдоровье: {self.health}\nАтака: {self.damage}\nЗащита: {self.defend}\nВсего побед: {self.win}</b></i>"
    # атака героя на врага.
    def attack(self, opponent, message):
        opponent.health -= self.damage

        bot.send_message(message.chat.id, f"<i><b>{self.name} нанёс урон {opponent.name} в размере {self.damage}!</b></i>", parse_mode="HTML")
    # защита героя.
    def defending(self, message):
        self.health + self.defend

        bot.send_message(message.chat.id, f"<i><b>{self.name} защитился!</b></i>", parse_mode="HTML")
# возвращаем список комманд.
def commands() -> List[str]:
    return [
        "Отгадать загадку Потустороннего📃", 
        "Посмотреть информацию о себе📋",
        "OutWorld магазин🛍️",
        "Квест на победу🌿",
        "Скрыть🔑"
        ]
# вовзращаем список товаров в магазине.
def get_utils() -> Dict:
    return {
        "X2 награда" : 250,
        "X2 урон" : 350
    }
# сохранения в json-файл.
def save_datab():
    with open(FILE_BOOSTS, "w", encoding="utf-8") as file:
        json.dump(data_boosts, file, ensure_ascii=False, indent=4)

list_utils = [s for s in get_utils().keys()]
# реагируем на Reply-клавиатуру.
@bot.message_handler(func=lambda m: m.text == "Да" or m.text == "Нет")
def answer(message : Message):
    text = message.text.lower()

    if text == "да":
        bot.send_message(message.chat.id, "<i><b>Хорошо, отлично, что решил присоединиться, ведь я тебя наделю частью своих сил...</b></i>"
                        "<i><b> воспользуйся ими, командой /help, и помни: используй навыки с разумом.</b></i>",
                        parse_mode="HTML", 
                        reply_markup=ReplyKeyboardRemove())
        
        hero = Sprite(message.from_user.first_name, 100, 25, 15)
        heroes.append(hero)
        
        reg_date = datetime.datetime.now().date()
        parse_date = datetime.datetime.strftime(reg_date, "%d-%m-%Y")
        
        db.insert_user(message.from_user.first_name, 
                       message.from_user.id,
                       str(parse_date)
                       )
        
        if str(message.from_user.id) not in data_boosts:
            data_boosts[str(message.from_user.id)] = list()
            save_datab()

        state["active"] = True
    else:
        bot.send_message(message.chat.id, f"<i><b>Как хочешь, {message.from_user.first_name}</b></i>\n"
                         "<i><b>думаю, потом ты поймёшь, какую ошибку ты совершил... а сейчас уходи живей, а не то иначе.....</b></i>",
                         parse_mode="HTML",
                         reply_markup=ReplyKeyboardRemove()
                         )
# правильные ответы на загадки.
@bot.message_handler(func=lambda m: m.text in list_this_question)    
def total_answer(message : Message):
    if not state["make_quest"]:
        return

    text = message.text

    if text == list_this_question[0]:
        user_boosts = data_boosts[str(message.from_user.id)]
        reward = 200 if list_utils[0] in user_boosts else 100

        bot.send_message(message.chat.id, f"<i><b>Молодец! Тебе повезло, {message.from_user.first_name}</b></i>\n"
                        f"<i><b>Твоей наградой будет {reward} OutWorld коинов.🪙</b></i>",
                        parse_mode="HTML")

        db.set_balance(message.from_user.id, reward)

        state["make_quest"] = False
# квест-борьба.
@bot.message_handler(func=lambda m: m.text == "Атаковать⚔️" or m.text == "Защищаться🛡️")
def fight(message : Message):
    if not state["fighting"]:
        return
    
    text = message.text

    player = heroes[0]
    enemy = heroes[1]

    if player.health <= 0:
        bot.send_message(message.chat.id, f"<i><b>О нет, герой {player.name} проиграл от своего оппонента - {enemy.name}!🎌\nНадеюсь, у тебя получиться в следующий раз!</b></i>", parse_mode="HTML", reply_markup=ReplyKeyboardRemove())
        new_player = Sprite(message.from_user.first_name, 100, 25, 15)

        print(heroes)

        del heroes[0:1]
        heroes.append(new_player)
        return
    
    if enemy.health <= 0:
        bot.send_message(message.chat.id, f"<i><b>{enemy.name} рухнул от удара {player.name}\nУра-а-а... {player.name} победил!🏆\nВ качество победы ему начисляется +1 очко к победам.</b></i>", parse_mode="HTML", reply_markup=ReplyKeyboardRemove())

        db.set_win(message.from_user.id, 1)
        heroes.pop(1)
        return
    
    if text == "Атаковать⚔️":
        player.attack(enemy, message)
    else:
        player.defending(message)

    sleep(2)
    enemy.attack(player, message)
# "список комманд".
@bot.message_handler(commands=["help"])
def help(message : Message):
    if state["active"]:
        markup = InlineKeyboardMarkup()

        for command in commands():
            markup.add(InlineKeyboardButton(text=command, callback_data=command))
        
        bot.send_message(message.chat.id, "<i><b>Твои возможности🦾</b></i>", parse_mode="HTML", reply_markup=markup)
# начало.
@bot.message_handler()
def start(message : Message):
    if not os.path.exists(DB_DIR):
        db.create_table()

    if state["starting"] and message.from_user.id not in db.get_all_users_id():

        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(KeyboardButton("Да"))
        keyboard.add(KeyboardButton("Нет"))

        bot.send_message(message.chat.id, f"<i><b>Приветствую тебя🙌, {message.from_user.first_name},</b></i>\n"
                         f"<i><b>Я... Потусторонний... самый могущественный из вселенной marvel.</b></i>",
                         parse_mode="HTML"
                         )
        sleep(2)

        bot.send_message(message.chat.id, "<i><b>Не спрашивай, откуда я тут! Это секретная информация,</b></i>"
                         "<i><b> Но у меня к тебе заманчивое предложение:</b></i>",
                         parse_mode="HTML"
                         )
        sleep(2)

        bot.send_message(message.chat.id, "<i><b>предлагаю перейти на мою сторону, иначе можешь уходить, ведь я не держу никого.</b></i>"
                         "<i><b> Ты согласен?</b></i>",
                         parse_mode="HTML",
                         reply_markup=keyboard)
        
        state["starting"] = False
    else:
        if state["starting"]:
            bot.send_message(message.chat.id, f"<i><b>О, это ты, {message.from_user.first_name}.\nЯ тебя ждал...(разблокирована способость: ты снова можешь использовать команду /help).</b></i>", parse_mode="HTML")
            hero = Sprite(message.from_user.first_name, 100, 25, 15)

            heroes.append(hero)
            state["starting"] = False
            state["active"] = True
# реагируем на Inline-кнопки.
@bot.callback_query_handler()
def action_keyboard(callback):
    main_command = commands()

    if callback.data == main_command[0]:
        choice_quest = choice(question)

        for key, value in choice_quest.items():
            list_this_question.append(key)
            list_this_question.append(value)

        bot.send_message(callback.message.chat.id, f"<i><b>Держи загадку, и не смей не отгадать её:\n{list_this_question[1]}</b></i>", parse_mode="HTML")

        state["make_quest"] = True

    elif callback.data == main_command[1]:
        user_info = db.get_user_info(callback.from_user.id)

        bot.send_message(callback.message.chat.id,
                         "<i><b>О тебе - герое(наверное)📑</b></i>\n"
                         f"<i><b>📛Имя: {user_info[0]}</b></i>\n"
                         f"<i><b>🪙OutWorld коинов: {user_info[1]}</b></i>\n"
                         f"<i><b>🏆Побед: {user_info[2]}</b></i>\n"
                         f"<i><b>🗓️Дата появления: {user_info[3]}</b></i>",
                         parse_mode="HTML")
    
    elif callback.data == main_command[2]:
        markup = InlineKeyboardMarkup()

        for text, price in get_utils().items():
            markup.add(InlineKeyboardButton(text=f"{text} - {price}", callback_data=text))
        markup.add(InlineKeyboardButton(text="Скрыть🔑", callback_data="Выйти"))

        bot.send_message(callback.message.chat.id, f"<i><b>🙌Приветствую тебя, {callback.from_user.first_name}\n</b></i>"
                         "<i><b>Это OutWorld магазин🛍️, тут особый ассортимент:</b></i>",
                         parse_mode="HTML",
                         reply_markup=markup)
    
    elif callback.data in get_utils().keys():
        call_price = get_utils()[callback.data]
        user_boosts = data_boosts[str(callback.from_user.id)]
        
        balance_user = db.get_user_info(callback.from_user.id)[1]

        if balance_user < call_price:
            bot.send_message(callback.message.chat.id, "<i><b>К сожалению, у тебя не хватает OutWrold коинов💸.</b></i>", parse_mode="HTML")
            return
        
        if callback.data in user_boosts:
            bot.send_message(callback.message.chat.id, f"<i><b>У тебя предмет '{callback.data}' уже есть!</b></i>", parse_mode="HTML")
            return
        
        new_balance = balance_user - call_price
        user_boosts.append(callback.data)

        bot.send_message(callback.message.chat.id, f"<i><b>Успешно приобретён {callback.data} за {call_price}!</b></i>", parse_mode="HTML")

        db.set_balance(callback.from_user.id, new_balance)
        save_datab()
    
    elif callback.data == main_command[3]:
        player = heroes[0]
        choicing = choice(warrior)
        enemy = Sprite(choicing[0], choicing[1], choicing[2], choicing[3])

        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(KeyboardButton("Атаковать⚔️"))
        keyboard.add(KeyboardButton("Защищаться🛡️"))

        bot.send_message(callback.message.chat.id, f"<i><b>Добро пожаловать на квест-борьбу!\nПоприветствуем обе стороны:\n</b></i>"
                         f"<i><b>Наш герой - {player.name}\n</b></i>"
                         f"<i><b>Против - {enemy.name}</b></i>",
                         parse_mode="HTML",
                         reply_markup=keyboard)
        
        heroes.append(enemy)
        state["fighting"] = True

    elif callback.data == "Выйти":
        bot.edit_message_reply_markup(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=None
        )
        bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id)

    elif callback.data == main_command[4]:
        bot.edit_message_reply_markup(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=None
        )
        bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id)

bot.polling(non_stop=True)