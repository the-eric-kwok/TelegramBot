# -*- coding: utf8 -*-

from telegram.ext import Updater, Handler, CommandHandler, CallbackQueryHandler
import telegram as tg
import datetime as dt
import logging
import json
from threading import Timer


TOKEN = ""
PROXY = ""
CONFIGFILE = 'config.json'
SAVEFILE = 'save.json'
LOGFILE = 'tgbot.log'

logging.basicConfig(
    # filename=LOGFILE,
    format='%(asctime)s [%(name)s] [%(levelname)s]: %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)
userList = []


class UserNotFoundError(Exception):
    pass


class User:
    __sign_flag = False
    __chat_id = 0
    msg_fail_times = 0
    lastMessage = None

    def __init__(self, sign_flag=False, chat_id=0):
        self.__sign_flag = sign_flag
        self.__chat_id = chat_id

    def sign(self):
        self.__sign_flag = True

    def reset(self):
        self.__sign_flag = False
        self.msg_fail_times = 0

    def getSignFlag(self):
        return self.__sign_flag

    def getChatId(self):
        return self.__chat_id


def reseter(updater):
    # Run at 0:00 every day
    for user in userList:
        if user.msg_fail_times > 20:
            logger.error("Msg send to " + str(user.getChatId()) +
                         " failed over 20 times. Removing from user list.")
            userList.remove(user)
            break
        if user.getSignFlag() == False:
            logger.info(
                "User %s not sign in, removing from user list.", str(user.getChatId()))
            updater.bot.send_message(user.getChatId(),
                                     text="由于您昨日未签到，失去了活动返现资格，已将您移出消息列表。未来将不会再向您发送提醒。再见👋")
            userList.remove(user)
            break
        user.reset()


def notify(updater):
    keyboard = [[tg.InlineKeyboardButton(
        "打开咪咕阅读", url="https://wap.cmread.com/r/p/clientdlwap.jsp")]]
    reply_markup = tg.InlineKeyboardMarkup(keyboard)
    for user in userList:
        if user.getSignFlag() == False:
            try:    # Delete button under the last message
                user.lastMessage.edit_reply_markup(reply_markup=None)
            except:
                pass
            try:
                user.lastMessage = updater.bot.send_message(
                    user.getChatId(), text="Kindle 签到啦", reply_markup=reply_markup)
            except:
                logger.error("Msg sending to " +
                             str(user.getChatId()) + " failed!")
                user.msg_fail_times += 1


def redAlert(updater):
    keyboard = [[tg.InlineKeyboardButton(
        "打开咪咕阅读", url="https://wap.cmread.com/r/p/clientdlwap.jsp")]]
    reply_markup = tg.InlineKeyboardMarkup(keyboard)
    for user in userList:
        if user.getSignFlag() == False:
            try:    # Delete button under the last message
                user.lastMessage.edit_reply_markup(reply_markup=None)
            except:
                pass
            try:
                user.lastMessage = updater.bot.send_message(
                    user.getChatId(), text="快签到！！", reply_markup=reply_markup)
            except:
                logger.error("Msg sending to " +
                             str(user.getChatId()) + " failed!")
                user.msg_fail_times += 1


def scheduler(updater):
    # Runs every minutes
    # If now time match in timeList
    # travell through UserList, notify user whos sign_flag is false
    logger.debug("Tick Tok!")
    now = dt.datetime.now()
    timeList = [8, 12, 19, 22]
    if now.hour in timeList and now.minute == 0:
        logger.debug("Alarm at: " + now.strftime("%H:%M"))
        notify(updater)
    if now.hour == 23:
        logger.debug("Alarm at: " + now.strftime("%H:%M"))
        redAlert(updater)
    if now.hour == 0 and now.minute == 0:
        reseter(updater)


class Repeat (Timer):
    def run(self):
        while not self.finished.is_set():
            self.function(*self.args, **self.kwargs)
            self.finished.wait(self.interval)


def findUser(chat_id):
    for user in userList:
        if chat_id == user.getChatId():
            return user
    raise UserNotFoundError


def help(update, context):
    update.message.reply_text('''
    使用帮助：
    /sign 将当天签到状态设为已签到
    /ami 查询当天签到状态
    ''')


def stop(update, context):
    chatId = update.message.chat_id
    try:
        user = findUser(chatId)
        userList.remove(user)
        update.message.reply_text("您已成功登出，今后将不会再给您发送提醒！")
        logger.info("User %s logged out", chatId)
        save()
    except UserNotFoundError:
        update.message.reply_text("您还没有登录，无需登出")


def start(update, context):
    chatId = update.message.chat_id
    try:
        findUser(chatId)
        update.message.reply_text("您已登录，无需重复登录了！")
    except UserNotFoundError:
        user = User(chat_id=chatId)
        userList.append(user)
        update.message.reply_text("登录成功！")
        help(update, context)
        logger.info("User %s logged in", chatId)
        save()


def sign_in(update, context):
    chat_id = update.message.chat_id
    try:
        user = findUser(chat_id)
        user.sign()
        logger.info(str(chat_id) + " signed in")
        update.message.reply_text("今日已签到！")
        save()
    except UserNotFoundError:
        logger.error("User not found: " + str(chat_id))
        update.message.reply_text("看起来你还没有登录，请使用 /start 登录")


def get_status(update, context):
    chat_id = update.message.chat_id
    try:
        user = findUser(chat_id)
        sign_flag = user.getSignFlag()
        if sign_flag == True:
            update.message.reply_text("今日已签到")
        else:
            update.message.reply_text("今日未签到")
    except UserNotFoundError:
        logger.error("User not found: " + str(chat_id))
        update.message.reply_text("看起来你还没有登录，请使用 /start 登录")


def error(update, context):
    logger.error('Update "%s" caused error "%s"', update, context.error)
    logger.error('context.chat_data: "%s"', context.chat_data)


def button(update, context):
    query = update.callback_query
    query.answer()


def load_config():
    global TOKEN, PROXY
    with open(CONFIGFILE, 'r') as f:
        config = json.load(f)
    TOKEN = config["TOKEN"]
    PROXY = config["PROXY"]


def load():
    global userList
    with open(SAVEFILE, 'r') as f:
        ulist = json.load(f)
    logger.debug("ulist: " + str(ulist))
    for u in ulist:
        user = User(u["sign_flag"], u["chat_id"])
        userList.append(user)


def save():
    ulist = []
    for user in userList:
        udict = {}
        udict["chat_id"] = user.getChatId()
        udict["sign_flag"] = user.getSignFlag()
        ulist.append(udict)
    logger.debug("ulist: " + str(ulist))
    with open(SAVEFILE, 'w') as f:
        json.dump(ulist, f)


def main():
    try:
        load_config()
        load()
    except Exception as e:
        logger.error(e)
    updater = Updater(token=TOKEN, use_context=True,
                      request_kwargs={
                          'proxy_url': PROXY
                      })
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("stop", stop))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("sign", sign_in))
    dp.add_handler(CommandHandler("ami", get_status))

    dp.add_handler(CallbackQueryHandler(button))

    dp.add_error_handler(error)

    t = Repeat(60.0, scheduler, [updater, ])
    t.start()

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
