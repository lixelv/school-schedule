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
