"""
Simple Bot to create a todo list and edit the list.

Source: https://dev.to/lordghostx/building-a-telegram-bot-with-python-and-fauna-494i
"""

import os, logging, pytz
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from faunadb import query as q
from faunadb.objects import Ref
from faunadb.client import FaunaClient
from datetime import datetime

PORT = int(os.environ.get('PORT', 5000))
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = "Telegram bot token"
fauna_secret = "Fauna db Secret"
client = FaunaClient(secret=fauna_secret)   

    

def welcome(update, context):
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
    welcome_text = 'Hello {}, my name is watari your personal telegram assistant.\nYou can call on me anytime... \nWhat will you like to do now though? Add task with /add_todo 😇'.format(first_name)
    context.bot.send_message(chat_id=chat_id, text=welcome_text)

    
def calling(update, context):
    chat_id = update.effective_chat.id
    context.bot.send_message(chat_id=chat_id, text='Yesssss??!!!, no dey shout my name boss🙄🙄😪... What will you like to do today though? Add tasks with /add_todo 😇')
    
    
def add_todo(update, context):
    chat_id = update.effective_chat.id

    user = client.query(q.get(q.match(q.index("userss"), chat_id)))
    client.query(q.update(q.ref(q.collection("users"), user["ref"].id()), {"data": {"last_command": "add_todo"}}))
    context.bot.send_message(chat_id=chat_id, text="Enter the todo task you want to add🎤")


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
    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", welcome))
    dispatcher.add_handler(CommandHandler("watariiiii", calling))
    dispatcher.add_handler(CommandHandler("add_todo", add_todo))
    dispatcher.add_handler(CommandHandler("list_todo", list_todo))
    dispatcher.add_handler(MessageHandler(Filters.regex("/update_[0-9]*"), update_todo))
    dispatcher.add_handler(MessageHandler(Filters.regex("/delete_[0-9]*"), delete_todo))
    dispatcher.add_handler(MessageHandler(Filters.text, echo))
    updater.start_webhook(listen="0.0.0.0", port=int(PORT), url_path=TOKEN)
    updater.bot.setWebhook('https://evening-citadel-87390.herokuapp.com/' + TOKEN)
    updater.idle()
    
    
if __name__ == '__main__':
    main()
