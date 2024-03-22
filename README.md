.data_loader.py:
```python
import pandas as pd
from db import Sqlite

excel_data = pd.read_excel('Расписание_обучающихся_с_кабинетами_5.xlsx', sheet_name="data")

db = Sqlite("db.sqlite")
print(excel_data)
for id in range(len(excel_data)):
    print(db.find_grade_by_name(excel_data["Класс"][id]), excel_data["Класс"][id])
    db.add_schedule(db.find_grade_by_name(excel_data["Класс"][id]), int(excel_data["№-урока"][id]), 1, excel_data["Понедельник"][id], excel_data["Каб."][id])
    db.add_schedule(db.find_grade_by_name(excel_data["Класс"][id]), int(excel_data["№-урока"][id]), 2, excel_data["Вторник"][id], excel_data["Каб.2"][id])
    db.add_schedule(db.find_grade_by_name(excel_data["Класс"][id]), int(excel_data["№-урока"][id]), 3, excel_data["Среда"][id], excel_data["Каб.3"][id])
    db.add_schedule(db.find_grade_by_name(excel_data["Класс"][id]), int(excel_data["№-урока"][id]), 4, excel_data["Четверг"][id], excel_data["Каб.4"][id])
    db.add_schedule(db.find_grade_by_name(excel_data["Класс"][id]), int(excel_data["№-урока"][id]), 5, excel_data["Пятница"][id], excel_data["Каб.5"][id])

```
cnf.py:
```python
from db import Sqlite
from envparse import env

env.read_envfile(".env")
token = env("TELEGRAM")

sql = Sqlite("db.sqlite")
```
db.py:
```python
import datetime
import sqlite3

class Sqlite:
    def __init__(self, db_name: str):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        
        self.do("CREATE TABLE IF NOT EXISTS user(id INTEGER PRIMARY KEY, name TEXT, grade INTEGER)")
        self.do("CREATE TABLE IF NOT EXISTS grade(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)")
        self.do("CREATE TABLE IF NOT EXISTS schedule(id INTEGER PRIMARY KEY AUTOINCREMENT, grade_id INTEGER, lesson_number INTEGER, week_day INTEGER, lesson_name TEXT, classroom TEXT)")
        
    def do(self, sql: str, options=()):
        self.cursor.execute(sql, options)
        self.conn.commit()
        
    def read(self, sql: str, options=(), fetchone=False):
        self.cursor.execute(sql, options)
        if fetchone:
            return self.cursor.fetchone()
        else:
            return self.cursor.fetchall()
        
    def add_grade(self, name: str) -> None:
        self.do("INSERT INTO grade(name) VALUES(?)", (name,))
        
    def all_grades(self):
        return [i[0] for i in self.read("SELECT name FROM grade")]
    
    def all_grades_id(self):
        return [i[0] for i in self.read("SELECT id FROM grade")]
    
    def all_users(self):
        return [i[0] for i in self.read("SELECT id FROM user")]
    
    def find_grade_by_name(self, name: str) -> int:
        return self.read("SELECT id FROM grade WHERE name = ?", (name,))[0][0]
    
    def find_grade_from_user_id(self, user_id: int) -> int:
        return self.read("SELECT grade FROM user WHERE id = ?", (user_id,))[0][0]
    
    def find_schedule(self, user_id: int, lesson: int) -> list:
        return (self.read("SELECT lesson_name, classroom FROM schedule WHERE grade_id = ? and week_day = ? and lesson_number = ?", (self.find_grade_from_user_id(user_id), datetime.datetime.today().weekday(), lesson)))
        
    def add_schedule(self, grade_id: int, lesson_number: int, week_day: int, lesson_name: str, classroom: str) -> None:
        self.do("INSERT INTO schedule(grade_id, lesson_number, week_day, lesson_name, classroom) VALUES(?, ?, ?, ?, ?)", (grade_id, lesson_number, week_day, lesson_name, classroom))
        
    def user_exists(self, user_id: int) -> bool:
        return bool(self.read("SELECT * FROM user WHERE id = ?", (user_id,), fetchone=True))
    
    def add_user(self, user_id: int, name: str) -> None:
        self.do("INSERT INTO user(id, name) VALUES(?, ?)", (user_id, name))
        
    def update_grade(self, user_id: int, grade_id: int) -> None:
        self.do("UPDATE user SET grade = ? WHERE id = ?", (grade_id, user_id))
        
```
main.py:
```python
import asyncio
import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData
from aiogram.filters import Command
from cnf import token, sql

bot = Bot(token)
dp = Dispatcher()

bells = {
    1: (7, 55),
    2: (8, 50),
    3: (9, 45),
    4: (10, 45),
    5: (11, 45),
    6: (12, 50),
    7: (13, 55),
    8: (14, 55)
}

# region Functions

class Callback(CallbackData, prefix="cb"):
    data: str

def get_command(text):
    return text.split(' ')[0].replace("/", "")

def get_args(text):
    return " ".join(text.split(' ')[1:])

def format_md(text):
    text = str(text)
    for i in "+-*/^()<>`'\".:!_":
        text = text.replace(i, f"\\{i}")
    return text

def build_kb(item, reply):
    builder = InlineKeyboardBuilder()
    for i, j in zip(item, reply):
        builder.button(text=i, callback_data=Callback(data="grade_"+str(j)).pack())
    return builder.as_markup()

async def run_daily_task(hour, minute, function):
    while True:
        now = datetime.datetime.now()
        # Проверяем, что сегодня будний день (понедельник=0, воскресенье=6)
        if now.weekday() < 5:
            target_time = datetime.datetime(now.year, now.month, now.day, hour, minute)
            if now > target_time:
                target_time += datetime.timedelta(days=1)
            delta = target_time - now
            await asyncio.sleep(delta.total_seconds())
            await function()
        else:
            # Если сегодня выходной, ждем до следующего буднего дня
            next_weekday = (now + datetime.timedelta(days=1)).replace(hour=hour, minute=minute)
            delta = next_weekday - now
            await asyncio.sleep(delta.total_seconds())
            
async def synt_schedule(user_id, lesson):
    lesson_name, class_room = sql.find_schedule(user_id, lesson)[0]
    return f"{lesson_name} {class_room}" if lesson_name != "-" else None
        
async def send_schedule(lesson):
    for user_id in sql.all_users():
        schedule = await synt_schedule(user_id, lesson)
        await bot.send_message(user_id, schedule) if schedule is not None else None
    
# endregion
# region Handlers
@dp.message(Command(commands=['help', 'start']))
async def help(message: types.Message):
    if not sql.user_exists(message.from_user.id):
        sql.add_user(message.from_user.id, message.from_user.full_name)
    grades = sql.all_grades(), sql.all_grades_id()
    await message.answer("Приветствую тебя, путник. Выбери свой отряд:\nИ если по пути позникнут проблемы отправь мне голубя @lixelv", reply_markup=build_kb(grades[0], grades[1]))
    
@dp.callback_query(Callback.filter(F.data.split("_")[0] == "grade"))
async def answer(query: types.CallbackQuery, callback_data: Callback):
    sql.update_grade(query.from_user.id, callback_data.data.split("_")[1])
    await query.message.answer("Вы выбрали правильный отряд!", show_alert=True)
# endregion


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    for i, j in bells.items():
        loop.create_task(run_daily_task(j[0], j[1], lambda: send_schedule(i)))
    loop.run_until_complete(dp.start_polling(bot))

```
readme.py:
```python
import os
def readme(dirpath):
    with open('README.md', 'r+', encoding='utf-8') as f_:
        for i in os.listdir(dirpath):
            if os.path.isdir(i):
                readme(os.path.join(dirpath, i))
            if os.path.join(dirpath, i) != __file__ and os.path.splitext(i)[1] == '.py':
                with open(os.path.join(dirpath, i), 'r', encoding='utf-8') as f:
                    content = f.read()
                    f_.write(f'{i}:\n```python\n{content}\n```\n')
readme(os.getcwd())

```
test.py:
```python
import datetime
import asyncio


async def run_daily_task(hour, minute, function):
    while True:
        now = datetime.datetime.now()
        # Проверяем, что сегодня будний день (понедельник=0, воскресенье=6)
        if now.weekday() < 5:
            target_time = datetime.datetime(now.year, now.month, now.day, hour, minute)
            if now > target_time:
                target_time += datetime.timedelta(days=1)
            delta = target_time - now
            await asyncio.sleep(delta.total_seconds())
            await function()
        else:
            # Если сегодня выходной, ждем до следующего буднего дня
            next_weekday = (now + datetime.timedelta(days=1)).replace(hour=hour, minute=minute)
            delta = next_weekday - now
            await asyncio.sleep(delta.total_seconds())
```
