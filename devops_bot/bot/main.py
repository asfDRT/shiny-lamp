import os
import re
import sys

from dotenv import load_dotenv
import logging
import asyncio
import paramiko

import aiogram
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram import types
from aiogram.types import CallbackQuery

from datetime import datetime

from sql import get_emails, get_phone_numbers, insert_email, insert_phone_number

load_dotenv()
logging.basicConfig(filename="bot_log.txt", filemode='a', level=logging.INFO, format="%(asctime)s - %(levelname)s - "
                                                                                     "%(message)s")

TOKEN = os.getenv('TOKEN')

dp = Dispatcher()


class FindMode(StatesGroup):
    EMAIL = State()
    PHONE = State()
    PASSWORD = State()
    SAVE_EMAILS = State()
    SAVE_PHONES = State()


@dp.message(Command("find_email"))
async def find_email(message: Message, state: FSMContext) -> None:
    await state.set_state(FindMode.EMAIL)
    logging.info(f"Пользователь {message.from_user.id} запросил поиск email-адресов")
    await message.answer("Пожалуйста, введите текст, в котором нужно найти email-адреса:")


@dp.message(FindMode.EMAIL)
async def handle_text_email(message: Message, state: FSMContext) -> None:
    email_pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
    text = message.text
    emails = re.findall(email_pattern, text)

    if emails:
        await message.answer("Найденные email-адреса:\n" + "\n".join(emails) + "\n\nХотите сохранить их в базу данных? Напишите 'да' или 'нет'.")
        await state.update_data(emails=emails)
        await state.set_state(FindMode.SAVE_EMAILS)
    else:
        await message.answer("Email-адреса не найдены в тексте.")
        await state.clear()


@dp.message(FindMode.SAVE_EMAILS)
async def save_emails(message: Message, state: FSMContext):
    try:
        if message.text.lower() == 'да':
            data = await state.get_data()
            emails = data.get('emails', [])
            for email in emails:
                await insert_email(email)
            await message.answer("Email-адреса сохранены в базу данных.")
            logging.info(f"Пользователь {message.from_user.id} записал данные в таблицу email_table")
        else:
            await message.answer("Сохранение отменено.")
        await state.clear()
    except Exception as e:
        logging.CRITICAL(f"Ошибка добавления email адреса в таблицу email_table {e}")
        await message.answer("Ошибка добавления")
        await state.clear()



@dp.message(Command("find_phone_number"))
async def find_phone_number(message: Message, state: FSMContext) -> None:
    await state.set_state(FindMode.PHONE)
    logging.info(f"Пользователь {message.from_user.id} запросил поиск номеров телефонов")
    await message.answer("Пожалуйста, введите текст, в котором нужно найти номера телефонов:")


@dp.message(FindMode.PHONE)
async def handle_text_phone(message: Message, state: FSMContext) -> None:
    phone_pattern = r"(?<!\d)(\+7|8)[\s(-]*(\d{3})[\s)-]*(\d{3})[\s-]*(\d{2})[\s-]*(\d{2})(?!\d)"
    text = message.text

    phones = [match.group(0) for match in re.finditer(phone_pattern, text)]

    if phones:
        await message.answer("Найденные номера телефонов:\n" + "\n".join(
            phones) + "\n\nХотите сохранить их в базу данных? Напишите 'да' или 'нет'.")
        await state.update_data(phones=phones)
        await state.set_state(FindMode.SAVE_PHONES)
    else:
        await message.answer("Номера телефонов не найдены в тексте.")
        await state.clear()


@dp.message(FindMode.SAVE_PHONES)
async def save_phones(message: Message, state: FSMContext):
    try:
        if message.text.lower() == 'да':
            data = await state.get_data()
            phones = data.get('phones', [])
            for phone in phones:
                await insert_phone_number(phone)
            await message.answer("Номера телефонов сохранены в базу данных.")
        else:
            await message.answer("Сохранение отменено.")
        await state.clear()
    except Exception as e:
        logging.CRITICAL(f"Ошибка добавления email адреса в таблицу phone_table {e}")
        await message.answer("Ошибка добавления")
        await state.clear()


@dp.message(Command("verify_password"))
async def verify_password(message: Message, state: FSMContext) -> None:
    await state.set_state(FindMode.PASSWORD)
    logging.info(f"Пользователь {message.from_user.id} запросил проверку пароля")
    await message.answer("Пароль должен соответствовать правилам:\n"
                         "- Пароль должен содержать не менее восьми символов\n"
                         "- Пароль должен включать как минимум одну заглавную букву (A–Z)\n"
                         "- Пароль должен включать хотя бы одну строчную букву (a–z)\n"
                         "- Пароль должен включать хотя бы одну цифру (0–9)\n"
                         "- Пароль должен включать хотя бы один специальный символ, такой как !@#$%^&*()\n\n"
                         "Пожалуйста, введите пароль для проверки:")


@dp.message(FindMode.PASSWORD)
async def handle_password(message: Message, state: FSMContext) -> None:
    await state.set_state(FindMode.PASSWORD)
    password_pattern = r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[!@#$%^&*()]).{8,}$"
    password = message.text
    if re.match(password_pattern, password):
        await message.answer("Пароль сложный")
    else:
        await message.answer("Пароль простой")

    await state.clear()


@dp.message(Command("help"))
async def find_email(message: Message):
    logging.info(f"Пользователь {message.from_user.id} ввел команду help")
    await message.answer("Список команд:\n"
                         "- /find_email - поиск email-адреса в тексте\n"
                         "- /find_phone_number - поиск номера телефона в тексте\n"
                         "- /verify_password - проверка пароля на сложность\n"
                         "- /get_release - SSH информация о релизе\n"
                         "- /get_uname - SSH информацию об имени хоста и тд\n"
                         "- /get_uptime - SSH информация о времени работы\n"
                         "- /get_df - SSH информация о состоянии файловой системы\n"
                         "- /get_free - SSH информация о состоянии оперативной памяти\n"
                         "- /get_mpstat - SSH информация о производительности системы\n"
                         "- /get_w - SSH информация об работающих в данной системе пользователях\n"
                         "- /get_auths - SSH информация об последних 10 входов в систему\n"
                         "- /get_critical - SSH информация об последних 5 критических событиях\n"
                         "- /get_ps - SSH информация о запущенных процессах\n"
                         "- /get_ss - SSH информация об используемых портах\n"
                         "- /get_apt_list - SSH информация об установленных пакетах\n"
                         "- /get_services - SSH информация о запущенных сервисах\n"
                         "- /get_repl_logs - Запроси логов реплекации\n"
                         "- /get_emails - получение email из БД\n"
                         "- /get_phone_numbers - получение phone из БД\n"
                         "!!!!!!!!!!!!!!!!!!!!\n"
                         "/get_repl_logs_ansible - Получение логов репликации при использовании ansible\n")


async def ssh_command(command: str) -> str:
    host = os.getenv('RM_HOST')
    port = os.getenv('RM_PORT')
    username = os.getenv('RM_USER')
    password = os.getenv('RM_PASSWORD')

    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    ssh_client.connect(hostname=host, username=username, password=password, port=port)

    stdin, stdout, stderr = ssh_client.exec_command(command)
    output = stdout.read().decode("utf-8").strip()
    error = stderr.read().decode("utf-8").strip()

    ssh_client.close()

    if error:
        logging.critical(f"Ошибка выполнения команды: {error}")
        raise Exception(f"Ошибка выполнения команды: {error}")

    return output


async def ssh_command_for_bd(command: str) -> str:
    host = os.getenv('DB_HOST')
    port = os.getenv('RM_PORT')
    username = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')

    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    ssh_client.connect(hostname=host, username=username, password=password, port=port)

    stdin, stdout, stderr = ssh_client.exec_command(command)
    output = stdout.read().decode("utf-8").strip()
    error = stderr.read().decode("utf-8").strip()

    ssh_client.close()

    if error:
        logging.critical(f"Ошибка выполнения команды: {error}")
        raise Exception(f"Ошибка выполнения команды: {error}")

    return output


@dp.message(Command("get_release"))
async def get_release(message: Message):
    """
    Получение информации о релизе
    """
    logging.info(f"Пользователь {message.from_user.id} запросил информацию о релизе")
    try:
        output = await ssh_command("hostnamectl | grep 'Operating System'")
        await message.answer(f"```\n{output}\n```", parse_mode=ParseMode.MARKDOWN_V2)
    except Exception as e:
        logging.critical(f"Ошибка выполнения команды: {e}")


@dp.message(Command("get_uname"))
async def get_uname(message: Message):
    """
    Получение информации uname
    """
    logging.info(f"Пользователь {message.from_user.id} запросил uname")
    try:
        output = await ssh_command("uname -a")
        await message.answer(f"```\n{output}\n```", parse_mode=ParseMode.MARKDOWN_V2)
    except Exception as e:
        logging.critical(f"Ошибка выполнения команды: {e}")


@dp.message(Command("get_uptime"))
async def get_uptime(message: Message):
    """
    Получение информации об времени работы ОС
    """
    logging.info(f"Пользователь {message.from_user.id} запросил uptime")
    try:
        output = await ssh_command("uptime")
        await message.answer(f"```\n{output}\n```", parse_mode=ParseMode.MARKDOWN_V2)
    except Exception as e:
        logging.critical(f"Ошибка выполнения команды: {e}")


@dp.message(Command("get_df"))
async def get_df(message: Message):
    """
    Получение информации о файловой системе
    """
    logging.info(f"Пользователь {message.from_user.id} запросил информацию о файловой системе")
    try:
        output = await ssh_command("df -h")
        await message.answer(f"```\n{output}\n```", parse_mode=ParseMode.MARKDOWN_V2)
    except Exception as e:
        logging.critical(f"Ошибка выполнения команды: {e}")


@dp.message(Command("get_free"))
async def get_free(message: Message):
    """
    Получение информации о ОЗУ
    """
    logging.info(f"Пользователь {message.from_user.id} запросил информацию о ОЗУ")
    try:
        output = await ssh_command("free -h")
        await message.answer(f"```\n{output}\n```", parse_mode=ParseMode.MARKDOWN_V2)
    except Exception as e:
        logging.critical(f"Ошибка выполнения команды: {e}")


@dp.message(Command("get_mpstat"))
async def get_mpstat(message: Message):
    """
    Получение информации о производительности системы с помощью mpstat
    """
    logging.info(f"Пользователь {message.from_user.id} запросил mpstat")
    try:
        output = await ssh_command("mpstat")
        await message.answer(f"```\n{output}\n```", parse_mode=ParseMode.MARKDOWN_V2)
    except Exception as e:
        logging.critical(f"Ошибка выполнения команды: {e}")


@dp.message(Command("get_w"))
async def get_w(message: Message):
    """
    Получение информации о пользователях
    """
    logging.info(f"Пользователь {message.from_user.id} запросил информацию о пользвоателях работающих в системе")
    try:
        output = await ssh_command("w")
        await message.answer(f"```\n{output}\n```", parse_mode=ParseMode.MARKDOWN_V2)
    except Exception as e:
        logging.critical(f"Ошибка выполнения команды: {e}")


@dp.message(Command("get_auths"))
async def get_auths(message: Message):
    """
    Получение о последних 10 логинах
    """
    logging.info(f"Пользователь {message.from_user.id} запросил информацию о 10 последних логинах")
    try:
        output = await ssh_command("last -n 10")
        await message.answer(f"```\n{output}\n```", parse_mode=ParseMode.MARKDOWN_V2)
    except Exception as e:
        logging.critical(f"Ошибка выполнения команды: {e}")


@dp.message(Command("get_critical"))
async def get_critical(message: Message):
    """
    Получение информации о 5 последних критических событиях
    """
    logging.info(f"Пользователь {message.from_user.id} запросил информацию о критических событиях")
    try:
        output = await ssh_command("journalctl -p err -n 5")
        await message.answer(f"```\n{output}\n```", parse_mode=ParseMode.MARKDOWN_V2)
    except Exception as e:
        logging.critical(f"Ошибка выполнения команды: {e}")


@dp.message(Command("get_ps"))
async def get_ps(message: Message):
    """
    Получение информации о запущенных процессах
    """
    logging.info(f"Пользователь {message.from_user.id} запросил информацию о процессах")
    try:
        output = await ssh_command("ps")
        await message.answer(f"```\n{output}\n```", parse_mode=ParseMode.MARKDOWN_V2)
    except Exception as e:
        logging.critical(f"Ошибка выполнения команды: {e}")


@dp.message(Command("get_ss"))
async def get_ss(message: Message):
    """
    Получение информации о используемых портах
    """
    logging.info(f"Пользователь {message.from_user.id} запросил информацию о портах")
    try:
        output = await ssh_command("ss -tuln")
        await message.answer(f"```\n{output}\n```", parse_mode=ParseMode.MARKDOWN_V2)
    except Exception as e:
        logging.critical(f"Ошибка выполнения команды: {e}")


@dp.message(Command("get_apt_list"))
async def get_apt_list(message: Message):
    """
    Получение информации о пакетах
    """
    logging.info(f"Пользователь {message.from_user.id} запросил информацию об установленных пакетах")
    await message.answer("Введите имя пакета для поиска или отправьте 'все' для вывода всех пакетов:")

    @dp.message()
    async def handle_apt_query(message: Message):
        package_query = message.text.strip()
        if package_query.lower() == 'все':
            command = "dpkg -l | head -n 30"
            description = "Все установленные пакеты:"
        else:
            command = f"dpkg -l | grep {package_query} | head -n 20"
            description = f"Информация о пакете '{package_query}':"

        try:
            output = await ssh_command(command)
            if output:
                await message.answer(f"```\n{description}\n{output}\n```", parse_mode=ParseMode.MARKDOWN_V2)
            else:
                await message.answer(f"Пакет '{package_query}' не найден.")
        except Exception as e:
            logging.critical(f"Ошибка выполнения команды: {e}")
            await message.answer("Произошла ошибка при выполнении команды.")


@dp.message(Command("get_services"))
async def get_services(message: Message):
    """
    Получение информации о запущенных сервисах
    """
    logging.info(f"Пользователь {message.from_user.id} запросил информацию о запущенных сервисах")
    command = "systemctl list-units --type=service --state=running"

    try:
        output = await ssh_command(command)
        if output:
            await message.answer(f"```\nАктивные сервисы:\n{output}\n```", parse_mode=ParseMode.MARKDOWN_V2)
        else:
            await message.answer("Не найдено запущенных сервисов.")
    except Exception as e:
        logging.critical(f"Ошибка выполнения команды: {e}")
        await message.answer("Произошла ошибка при выполнении команды.")


@dp.message(Command("get_emails"))
async def handle_get_emails(message: Message):
    """
    Получаем данные из таблицы email
    """
    logging.info(f"Пользователь {message.from_user.id} запросил данные о email")
    emails = await get_emails()
    try:
        if emails:
            response = "Email-адреса из БД:\n" + "\n".join(email['email'] for email in emails)
        else:
            response = "Email-адреса не найдены"
        await message.answer(response)
    except Exception as e:
        logging.critical(f"Ошибка выполнения команды: {e}")
        await message.answer("Произошла ошибка при выполнении команды.")


@dp.message(Command("get_phone_numbers"))
async def handle_get_phone_numbers(message: Message):
    """
    Получение номеров телефона из БД
    """
    logging.info(f"Пользователь {message.from_user.id} запросил данные о phone")
    phone_numbers = await get_phone_numbers()
    try:
        if phone_numbers:
            response = "Номера телефонов из БД:\n" + "\n".join(phone['phone_number'] for phone in phone_numbers)
        else:
            response = "Номера телефонов не найдены"
        await message.answer(response)
    except Exception as e:
        logging.critical(f"Ошибка выполнения команды: {e}")
        await message.answer("Произошла ошибка при выполнении команды.")



@dp.message(Command("get_repl_logs"))
async def get_latest_db_log(message: Message):
    """
    Получение и вывод последнего лога PostgreSQL из общего тома, фильтрация по ключевому слову "replication".
    """
    logging.info(f"Пользователь {message.from_user.id} запросил последний логи")
    try:
        logs_dir = '/db-logs'
        log_files = sorted(os.listdir(logs_dir), reverse=True)  # Сортировка файлов по дате создания
        if log_files:
            latest_log_file = log_files[0]
            log_path = os.path.join(logs_dir, latest_log_file)
            with open(log_path, 'r') as file:
                log_contents = file.readlines()
                matched_lines = [line for line in log_contents if "replication" in line]

            if matched_lines:
                filtered_logs_content = f"**{escape_markdown(latest_log_file)}**\n{''.join([escape_markdown(line) for line in matched_lines])}\n\n"
                await message.answer(filtered_logs_content, parse_mode=ParseMode.MARKDOWN_V2)
            else:
                await message.answer("Логи с упоминаниями 'replication' не найдены в последнем файле.")
        else:
            await message.answer("Лог-файлы не найдены в директории.")
    except Exception as e:
        logging.critical(f"Ошибка при получении логов: {e}")
        await message.answer("Произошла ошибка при выполнении команды.")

def escape_markdown(text):
    """
    Вспомогательная функция для удаления символовм, так как тг ругается
    """
    escape_chars = '_*[]()~`>#+-=|{}.!'
    return ''.join('\\' + char if char in escape_chars else char for char in text)


@dp.message(Command("get_repl_logs_ansible"))
async def get_repl_logs_ansible(message: Message):
    """
    Получение самого свежего лога репликации
    """
    logging.info(f"Пользователь {message.from_user.id} запросил логи репликации")
    command = "ls -t /var/lib/postgresql/14/main/log/*.log | head -1 | xargs grep 'replication'"

    try:
        output = await ssh_command_for_bd(command)
        if output:
            limited_output = output[:4095]
            await message.answer(f"```\nПоследние логи репликации:\n{limited_output}\n```", parse_mode=ParseMode.MARKDOWN_V2)
        else:
            await message.answer("Логи репликации не найдены.")
    except Exception as e:
        logging.critical(f"Ошибка выполнения команды: {e}")
        await message.answer("Произошла ошибка при выполнении команды."



async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.debug(f"Бот запущен")
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
