import logging
from dotenv import load_dotenv
import asyncpg
import os

load_dotenv()
logging.basicConfig(filename="bot_log.txt", filemode='a', level=logging.INFO, format="%(asctime)s - %(levelname)s - "
                                                                                    "%(message)s")

USER = os.getenv('DB_USER')
PASSWORD = os.getenv('DB_PASSWORD')
HOST = os.getenv('DB_HOST')
PORT = os.getenv('DB_PORT')
DATABASE = os.getenv('DB_DATABASE')


async def fetch_from_db(query, *params):
    logging.info(f"Подключение к БД")
    conn = await asyncpg.connect(user=USER, password=PASSWORD, database=DATABASE, host=HOST, port=PORT)
    try:
        if params:
            result = await conn.fetch(query, *params)
        else:
            result = await conn.fetch(query)
        return result
    finally:
        await conn.close()


async def get_emails():
    logging.info(f"Запросы данных о email")
    try:
        return await fetch_from_db("SELECT email FROM email_table")
    except Exception as e:
        logging.log(f"Произошла ошибка в запросе к phone {e}")


async def get_phone_numbers():
    logging.info(f"Запросы данных о phone")
    try:
        return await fetch_from_db("SELECT phone_number FROM phone_table")
    except Exception as e:
        logging.log(f"Произошла ошибка в запросе к phone {e}")


async def insert_email(email):
    logging.info(f"Добавление данных в email_table")
    try:
        await fetch_from_db("INSERT INTO email_table (email) VALUES ($1) ON CONFLICT DO NOTHING", email)
    except Exception as e:
        logging.log(f"Произошла ошибка при добавлении данных в email_table {e}")


async def insert_phone_number(phone_number):
    logging.info(f"Добавление данных в phone_number")
    try:
        await fetch_from_db("INSERT INTO phone_table (phone_number) VALUES ($1) ON CONFLICT DO NOTHING", phone_number)
    except Exception as e:
        logging.log(f"Произошла ошибка при добавлении данных в phone_number {e}")
