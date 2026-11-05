import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
load_dotenv()

url= URL.create(
    "postgresql+psycopg",
    username=os.environ["POSTGRES_USER"],
    password=os.environ["POSTGRES_PASSWORD"],
    host="localhost",
    port=int(os.environ["POSTGRES_PORT"]),
    database=os.environ["POSTGRES_DB"],   
)
engine = create_engine(url)
with engine.connect() as conn:
    print(conn.execute(text("select current_database(),current_user")).one())
