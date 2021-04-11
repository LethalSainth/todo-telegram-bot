"""
Simple Bot to create a todo list and edit the list.

Source: https://dev.to/lordghostx/building-a-telegram-bot-with-python-and-fauna-494i
"""

import telegram
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters 
from faunadb import query as q
from faunadb.objects import Ref
from faunadb.client import FaunaClient
import pytz
from datetime import datetime
import os,logging


tgram_bot_token = "1117281529:AAHxO27N0Uwf4lN253mz95GOhyfsg8vphuc"
fauna_secret = "fnAEAQyvrUACCNjdFDrIeXot-6bwA85huqVeNo5p"
client = FaunaClient(secret=fauna_secret)
PORT = int(os.environ.get('PORT', 8443))
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)



def start(update, context):
    chat_id = update.effective_chat.id

    first_name = update["message"]["chat"]["first_name"]
    username = update["message"]["chat"]["username"]

    try:
        client.query(q.get(q.match(q.index("users"), chat_id)))
    except:
        user = client.query(q.create(q.collection("users"), {
            "data": {
                "id": chat_id,
                "first_name": first_name,
                "username": username,
                "last_command": "",
                "date": datetime.now(pytz.UTC)
            }
        }))
    welcome_text = 'Welcome L-sama, I am Watari your personal todo list compiler.'
    context.bot.send_message(chat_id=chat_id, text=welcome_text)


def add_todo(update, context):
    chat_id = update.effective_chat.id

    user = client.query(q.get(q.match(q.index("userss"), chat_id)))
    client.query(q.update(q.ref(q.collection("users"), user["ref"].id()), {"data": {"last_command": "add_todo"}}))
    context.bot.send_message(chat_id=chat_id, text="Enter the todo task you want to add 😁")


def list_todo(update, context):
    chat_id = update.effective_chat.id

    task_message = ""
    tasks = client.query(q.paginate(q.match(q.index("todo"), chat_id)))
    for i in tasks["data"]:
        task = client.query(q.get(q.ref(q.collection("todo"), i.id())))
        if task["data"]["completed"]:
            task_status = "Completed"
        else:
            task_status = "Not Completed"
        task_message += "{}\nStatus: {}\nUpdate Link: /update_{}\nDelete Link: /delete_{}\n\n".format(
            task["data"]["todo"], task_status, i.id(), i.id())
    if task_message == "":
        task_message = "You have not added any task, do that with /add_todo 😇"
    context.bot.send_message(chat_id=chat_id, text=task_message)


def update_todo(update, context):
    chat_id = update.effective_chat.id
    message = update.message.text
    todo_id = message.split("_")[1]

    task = client.query(q.get(q.ref(q.collection("todo"), todo_id)))
    if task["data"]["completed"]:
        new_status = False
    else:
        new_status = True
    client.query(q.update(q.ref(q.collection("todo"), todo_id),
                          {"data": {"completed": new_status}}))
    context.bot.send_message(
        chat_id=chat_id, text="Successfully updated todo task status 👌\n\nSee all your todo with /list_todo")


def delete_todo(update, context):
    chat_id = update.effective_chat.id
    message = update.message.text
    todo_id = message.split("_")[1]

    client.query(q.delete(q.ref(q.collection("todo"), todo_id)))
    context.bot.send_message(
        chat_id=chat_id, text="Successfully deleted todo task status 👌\n\nAdd a new todo with /add_todo")



def echo(update, context):
    chat_id = update.effective_chat.id
    message = update.message.text

    user = client.query(q.get(q.match(q.index("userss"), chat_id)))
    last_command = user["data"]["last_command"]

    if last_command == "add_todo":
        todo = client.query(q.create(q.collection("todo"), {
            "data": {
                "user_id": chat_id,
                "todo": message,
                "completed": False,
                "date": datetime.now(pytz.UTC)
            }
        }))
        client.query(q.update(q.ref(q.collection("users"), user["ref"].id()), {
                     "data": {"last_command": ""}}))
        context.bot.send_message(
            chat_id=chat_id, text="Successfully added todo task 👍\n\nSee all your todo with /list_todo")


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def main():
    updater = Updater(token=tgram_bot_token, use_context=True)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("add_todo", add_todo))
    dispatcher.add_handler(CommandHandler("list_todo", list_todo))
    dispatcher.add_handler(MessageHandler(Filters.regex("/update_[0-9]*"), update_todo))
    dispatcher.add_handler(MessageHandler(Filters.regex("/delete_[0-9]*"), delete_todo))
    dispatcher.add_handler(MessageHandler(Filters.text, echo))
    updater.start_webhook(listen="0.0.0.0", port=int(PORT), url_path= tgram_bot_token)
    updater.bot.setWebhook('https://ancient-falls-19245.herokuapp.com/' + tgram_bot_token)
    updater.idle()

if __name__ == '__main__':
    main()