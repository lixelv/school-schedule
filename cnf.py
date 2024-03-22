from db import Sqlite
from envparse import env

env.read_envfile(".env")
token = env("TELEGRAM")

sql = Sqlite("db.sqlite")