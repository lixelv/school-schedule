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
        