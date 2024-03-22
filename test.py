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