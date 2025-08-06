from asyncio import timeout
import pytz

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, JobQueue

from cloudflare_workers_ai import CloudflareWorkersAi
from model import Task
from typing import Dict, List
from save_json import SaveJsonDB
from datetime import datetime
from random import randint

from сonfig import Config
import asyncio

config = Config()
db = SaveJsonDB(config.get_url_DB(),timeout=10)

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я Task Tracker Bot 📝\n\nКоманды:\n/add <задача>\n/list\n/done <номер>\n/clear"
    )

# /add <задача>
async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    id = randint(0,10000)
    task_text = " ".join(context.args)

    if not task_text:
        await update.message.reply_text("❗ Пожалуйста, укажи задачу после команды /add")
        return

    task = Task(id= id,title=task_text,status='Open')
    cloudflare_ai = CloudflareWorkersAi(task=task,ai_agent=config.get_ai_agent(),timeout=10)
    task = cloudflare_ai.send_task_ai()
    task = db.create_task(task)
    await update.message.reply_text(f"✅ Задача добавлена: {task.title}")

# /list
async def list_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tasks = db.load_tasks()

    if not tasks:
        await update.message.reply_text("📭 У тебя пока нет задач.")
    else:
        msg = "\n".join(
            [f"{task.id}. Задача:{task.title} Статус:{task.status})"
             for task in tasks]
        )
        await update.message.reply_text(f"📝Задачи:\n{msg}")

# /done <номер>
async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not context.args or not context.args[0].isdigit():
            await update.message.reply_text("❗ Укажи номер задачи, например: /done 2")
            return
        task = db.get_task(id=context.args[0])
        task.status = 'Closed'
        task = db.update_task_id(id=context.args[0],task=task)
        await update.message.reply_text(f"✅ Задача выполнена: {task.title}")
    except:
        await update.message.reply_text("❗ Некорректный id задачи.")

# /clear
async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not context.args or not context.args[0].isdigit():
            await update.message.reply_text("❗ Укажи номер задачи, например: /clear 2")
            return
        task = db.delete_task_id(context.args[0])
        await update.message.reply_text(f"✅ Задача №{task.id} удалена: {task.title}")
    except:
        await update.message.reply_text("❗ Некорректный id задачи.")

# Основной запуск
async def main():
    app = ApplicationBuilder().token("8243876048:AAF4xx2RoR-Wxx0j4u7gvIob3qvxonylthI").build()
    app.job_queue.scheduler.configure(timezone=pytz.UTC)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("list", list_tasks))
    app.add_handler(CommandHandler("done", done))
    app.add_handler(CommandHandler("clear", clear))

    print("Бот запущен...")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    import nest_asyncio

    nest_asyncio.apply()  # 💡 позволяет повторно использовать текущий event loop
    asyncio.run(main())
