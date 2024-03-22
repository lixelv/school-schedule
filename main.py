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
    await message.answer("Приветствую тебя, путник. Выбери свой отряд:\nИ если по пути позникнут проблемы отправь мне голубя @lixelv\nСуть бота в том, чтобы получать сообщения о следующем уроке, и том, где он находится. После выбора класса все происходит автоматически.", reply_markup=build_kb(grades[0], grades[1]))

@dp.callback_query(Callback.filter(F.data.split("_")[0] == "grade"))
async def answer(query: types.CallbackQuery, callback_data: Callback):
    sql.update_grade(query.from_user.id, callback_data.data.split("_")[1])
    await query.message.answer("Хороший выбор!", show_alert=True)
# endregion


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    for i, j in bells.items():
        loop.create_task(run_daily_task(j[0], j[1], lambda: send_schedule(i)))
    loop.run_until_complete(dp.start_polling(bot))
