import psycopg2
import asyncio
import logging
import re
import subprocess
import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackContext,
    ContextTypes,
    MessageHandler,
    filters
)
import paramiko
from dotenv import load_dotenv

# .env
load_dotenv()
TOKEN = os.getenv("TOKEN")
RM_HOST = os.getenv("RM_HOST")
RM_PORT = int(os.getenv("RM_PORT", 22))
RM_USER = os.getenv("RM_USER")
SSH_KEY_PATH = os.getenv("SSH_KEY_PATH", None)
RM_PASSWORD = os.getenv("RM_PASSWORD", None)
DB_DATABASE = os.getenv("DB_DATABASE")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

# логгирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='bot.log'
)

# Регулярные выражения
email_pattern = re.compile(
                r'\b[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~-]+(?:\.[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~-]+)*' \
                r'@(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b')
#phone_pattern = re.compile(r'(8|\+7)[\s-]?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}')
password_pattern = re.compile(
    r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()])[A-Za-z\d!@#$%^&*()]{8,}$')


# SSH-соединениe
def get_ssh_connection():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    if SSH_KEY_PATH:
        ssh.connect(RM_HOST, port=RM_PORT, username=RM_USER, key_filename=SSH_KEY_PATH)
    else:
        ssh.connect(RM_HOST, port=RM_PORT, username=RM_USER, password=RM_PASSWORD)
    return ssh

# Функция для подключения к PostgreSQL
def get_db_connection():
    return psycopg2.connect(
        dbname=DB_DATABASE,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
    )

# Функция для нормализации номера телефона
def normalize_phone_number(phone_num):
    if phone_num.startswith('+'):
        return '+' + re.sub(r'\D', '', phone_num[1:])
    else:
        return re.sub(r'\D', '', phone_num)
        
# Обработчик команды /get_repl_logs
async def get_repl_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        result = subprocess.run(
            "cat /var/log/postgresql/postgresql.log | grep repl",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        output = result.stdout.decode().strip()

        if result.returncode != 0 or not output:
            error_message = result.stderr.decode().strip()
            response = f"No replication logs found or an error occurred: {error_message}"
            await update.message.reply_text(response)
        else:
            chunk_size = 4096 
            for i in range(0, len(output), chunk_size):
                await update.message.reply_text(output[i:i+chunk_size])
    except Exception as e:
        await update.message.reply_text(f"An error occurred while fetching replication logs: {str(e)}")



# Обработчики команд
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Используйте /find_email для поиска email, /find_phone_number для номеров телефонов, /verify_password для проверки сложности пароля. Для работы с бд используйте /get_repl_logs. Если вас интересуют команды для взаимодействия с kali и БД, то используйте команду /help.")

async def get_emails(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT email FROM emails;")
    emails = cur.fetchall()
    cur.close()
    conn.close()

    if emails:
        email_list = ', '.join([e[0] for e in emails])
        await update.message.reply_text(f"Список email-адресов:\n{email_list}")
    else:
        await update.message.reply_text("Нет email-адресов в базе данных.")

async def get_phone_numbers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT phone FROM phones;")
    phone_numbers = cur.fetchall()
    cur.close()
    conn.close()

    if phone_numbers:
        phone_list = ', '.join([p[0] for p in phone_numbers])
        await update.message.reply_text(f"Список номеров телефонов:\n{phone_list}")
    else:
        await update.message.reply_text("Нет номеров телефонов в базе данных.")

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Используйте /get_release, /get_uname, /get_uptime для получения информации о системе.""\n"
        "Используйте /get_df для сбора информации о состоянии файловой системы.""\n"
        "Используйте /get_free для сбора информации о состоянии оперативной памяти.""\n"
        "Используйте /get_mpstat для сбора информации о производительности системы.""\n"
        "Используйте /get_w для для сбора информации о работающих в данной системе пользователях.""\n"
        "Используйте /get_auths, /get_critical для сбора логов.""\n"
        "Используйте /get_ps для сбора информации о запущенных процессах.""\n"
        "Используйте /get_ss для сбора информации об используемых портах.""\n"
        "Используйте /get_apt_list для сбора информации об установленных пакетах.""\n"
        "Используйте /get_repl_logs для вывода логов о репликации.""\n"
        "Используйте /get_emails для вывода информации из базы emails.""\n"
        "Используйте /get_phone_numbers для вывода информации из базы phones.""\n"
        "Используйте /get_services для сбора информации о запущенных сервисах.")
async def find_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["state"] = "FIND_EMAIL"
    await update.message.reply_text("Пожалуйста, отправьте текст, чтобы найти email-адреса.")


async def find_phone_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["state"] = "FIND_PHONE"
    await update.message.reply_text("Пожалуйста, отправьте текст, чтобы найти номера телефонов.")

async def verify_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["state"] = "VERIFY_PASSWORD"
    await update.message.reply_text("Пожалуйста, отправьте пароль, чтобы проверить его сложность.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get("state")

    if state == "FIND_EMAIL":
        text = update.message.text
        emails = email_pattern.findall(text)
        unique_emails = {email.lower() for email in emails} 

        if unique_emails:
            email_list = ', '.join(unique_emails)
            context.user_data["emails"] = list(unique_emails)
            await update.message.reply_text(f"Найденные email адреса:\n{email_list}. Хотите сохранить их в базе данных? (да/нет)")
            context.user_data["state"] = "SAVE_EMAILS"
        else:
            await update.message.reply_text("Email адреса не найдены.")
            context.user_data.pop("state", None)  

    elif state == "FIND_PHONE":
        user_input = update.message.text

        # Модифицированные регулярные выражения
        phoneNumRegex1 = re.compile(r'(?<!\d)(?:\+?7|8)[\s(]?(?!\d{19})\d{1,3}[\s)]?\d{1,3}[\s-]?\d{2}[\s-]?\d{2}\b')
        phoneNumRegex2 = re.compile(r'\b(?:\+?7|8)[\s-]?(?!\d{19})\d{1,3}[\s-]?\d{1,3}[\s-]?\d{2}[\s-]?\d{2}\b')

        phoneNumberSet = set()  
        phoneNumbers = []       

        for phone_num in phoneNumRegex1.findall(user_input) + phoneNumRegex2.findall(user_input):
            normalized = normalize_phone_number(phone_num)
            if len(normalized) == 12 or (len(normalized) == 11 and normalized.startswith('8')):  
                if normalized not in phoneNumberSet:
                    phoneNumberSet.add(normalized)
                    phoneNumbers.append(phone_num)  

        if not phoneNumbers:  
            await update.message.reply_text('Телефонные номера не найдены.')
            context.user_data.pop("state", None)  
            return

        phoneNumbersStr = '\n'.join(phoneNumbers)  

        context.user_data["phones"] = phoneNumbers  
        await update.message.reply_text(f"Найденные номера телефонов:\n{phoneNumbersStr}")
        await update.message.reply_text("Хотите сохранить их в базе данных? (да/нет)")
        context.user_data["state"] = "SAVE_PHONES"

    elif state == "SAVE_EMAILS":
        response = update.message.text.strip().lower()
        if response in ("да", "yes"):
            try:
                conn = get_db_connection()
                cur = conn.cursor()
                emails = context.user_data["emails"]
                cur.executemany("INSERT INTO emails (email) VALUES (%s)", [(e,) for e in emails])
                conn.commit()
                await update.message.reply_text("Email-адреса успешно сохранены.")
                cur.close()
                conn.close()
            except Exception as e:
                await update.message.reply_text(f"Ошибка при сохранении email-адресов: {e}")
        else:
            await update.message.reply_text("Email-адреса не были сохранены.")

        context.user_data.pop("state", None)  

    elif state == "SAVE_PHONES":
        response = update.message.text.strip().lower()
        if response in ("да", "yes"):
            try:
                conn = get_db_connection()
                cur = conn.cursor()
                phones = context.user_data["phones"]
                cur.executemany("INSERT INTO phones (phone) VALUES (%s)", [(p,) for p in phones])
                conn.commit()
                await update.message.reply_text("Номера телефонов успешно сохранены.")
                cur.close()
                conn.close()
            except Exception as e:
                await update.message.reply_text(f"Ошибка при сохранении номеров телефонов: {e}")
        else:
            await update.message.reply_text("Номера телефонов не были сохранены.")

        context.user_data.pop("state", None)  

    elif state == "VERIFY_PASSWORD":
        password = update.message.text
        if password_pattern.match(password):
            await update.message.reply_text("Пароль сложный.")
        else:
            await update.message.reply_text("Пароль простой.")
        context.user_data.pop("state", None)  

    elif state == "APT_LIST":
        ssh = get_ssh_connection()
        package_name = update.message.text.strip().lower()

        if package_name == "все":
            command = "dpkg -l | head -n 20"
        else:
            command = f"dpkg --list | grep {package_name}"

        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read().decode("utf-8")

        if not output.strip():
            await update.message.reply_text(f"Пакет '{package_name}' не найден.")
        else:
            await update.message.reply_text(f"Информация о пакете '{package_name}':\n{output}")

        context.user_data.pop("state", None)  
        ssh.close()

# Обработчики SSH
async def get_release(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ssh = get_ssh_connection()
    stdin, stdout, stderr = ssh.exec_command("cat /etc/os-release")
    output = stdout.read().decode("utf-8")
    await update.message.reply_text(f"Информация о релизе:\n{output}")
    ssh.close()

async def get_uname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ssh = get_ssh_connection()
    stdin, stdout, stderr = ssh.exec_command("uname -a")
    output = stdout.read().decode("utf-8")
    await update.message.reply_text(f"Информация о системе:\n{output}")
    ssh.close()


async def get_uptime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ssh = get_ssh_connection()
    stdin, stdout, stderr = ssh.exec_command("uptime")
    output = stdout.read().decode("utf-8")
    await update.message.reply_text(f"Система работает:\n{output}")
    ssh.close()


async def get_df(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ssh = get_ssh_connection()
    stdin, stdout, stderr = ssh.exec_command("df -h")
    output = stdout.read().decode("utf-8")
    await update.message.reply_text(f"Информация о состоянии файловой системы:\n{output}")
    ssh.close()

async def get_free(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ssh = get_ssh_connection()
    stdin, stdout, stderr = ssh.exec_command("free -m")
    output = stdout.read().decode("utf-8")
    await update.message.reply_text(f"Информация о состоянии оперативной памяти:\n{output}")
    ssh.close()


async def get_mpstat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ssh = get_ssh_connection()
    stdin, stdout, stderr = ssh.exec_command("vmstat")
    output = stdout.read().decode("utf-8")
    await update.message.reply_text(f"Информация о производительности системы:\n{output}")
    ssh.close()


async def get_w(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ssh = get_ssh_connection()
    stdin, stdout, stderr = ssh.exec_command("w")
    output = stdout.read().decode("utf-8")
    await update.message.reply_text(f"Информация о работающих в системе пользователях:\n{output}")
    ssh.close()


async def get_auths(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ssh = get_ssh_connection()
    stdin, stdout, stderr = ssh.exec_command("last -n 10")
    output = stdout.read().decode("utf-8")
    await update.message.reply_text(f"Последние 10 входов в систему:\n{output}")
    ssh.close()


async def get_critical(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ssh = get_ssh_connection()
    stdin, stdout, stderr = ssh.exec_command("journalctl -p 2 -n 5")
    output = stdout.read().decode("utf-8")

    if not output.strip():  
        await update.message.reply_text("Критических ошибок нет.")
    else:
        await update.message.reply_text(f"Последние 5 критических ошибок:\n{output}")

    ssh.close()


async def get_ps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ssh = get_ssh_connection()
    stdin, stdout, stderr = ssh.exec_command("ps aux")
    output = stdout.read().decode("utf-8")

    if len(output) > 4000:  # Telegram ограничивает длину сообщений
        output = output[:3997] + "..."  

    await update.message.reply_text(f"Информация о запущенных процессах:\n{output}")
    ssh.close()


async def get_ss(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ssh = get_ssh_connection()
    stdin, stdout, stderr = ssh.exec_command("ss -tuln")
    output = stdout.read().decode("utf-8")

    if not output.strip():  # Проверка, что есть данные
        await update.message.reply_text("Нет активных портов.")
    else:
        await update.message.reply_text(f"Информация об используемых портах:\n{output}")

    ssh.close()


async def get_apt_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Ставим состояние для ожидания ввода названия пакета
    context.user_data["state"] = "APT_LIST"
    await update.message.reply_text(
        "Пожалуйста, введите название пакета, который нужно найти, или напишите 'все' для списка всех установленных пакетов.")



async def get_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ssh = get_ssh_connection()
    stdin, stdout, stderr = ssh.exec_command("systemctl list-units --type=service --state=running")
    output = stdout.read().decode("utf-8")

    if not output.strip():
        await update.message.reply_text("Нет запущенных сервисов.")
    else:
        await update.message.reply_text(f"Запущенные сервисы:\n{output}")

    ssh.close()



application = ApplicationBuilder().token(TOKEN).build()


application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help))
application.add_handler(CommandHandler("find_email", find_email))
application.add_handler(CommandHandler("find_phone_number", find_phone_number))
application.add_handler(CommandHandler("verify_password", verify_password))
application.add_handler(CommandHandler("get_release", get_release))
application.add_handler(CommandHandler("get_uname", get_uname))
application.add_handler(CommandHandler("get_uptime", get_uptime))
application.add_handler(CommandHandler("get_df", get_df))
application.add_handler(CommandHandler("get_free", get_free))
application.add_handler(CommandHandler("get_mpstat", get_mpstat))
application.add_handler(CommandHandler("get_w", get_w))
application.add_handler(CommandHandler("get_auths", get_auths))
application.add_handler(CommandHandler("get_critical", get_critical))
application.add_handler(CommandHandler("get_ps", get_ps))
application.add_handler(CommandHandler("get_ss", get_ss))
application.add_handler(CommandHandler("get_apt_list", get_apt_list))
application.add_handler(CommandHandler("get_services", get_services))
application.add_handler(CommandHandler("get_repl_logs", get_repl_logs))
application.add_handler(CommandHandler("get_emails", get_emails))
application.add_handler(CommandHandler("get_phone_numbers", get_phone_numbers))
#application.add_handler(MessageHandler(filters.TEXT, handle_apt_list_response))
application.add_handler(MessageHandler(filters.TEXT, handle_message))


if __name__ == "__main__":
    application.run_polling()
