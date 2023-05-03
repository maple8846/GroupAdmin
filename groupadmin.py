import logging
import pymysql.cursors
import schedule
import requests
import json


import gspread
from oauth2client.service_account import ServiceAccountCredentials
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]


# 设置 API Key




import time
import telegram
import asyncio
from datetime import datetime, timedelta



from telegram import __version__ as TG_VER
from typing import Optional, Tuple

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 5):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )
from telegram import  ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, Chat, ChatMember, ChatMemberUpdated, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
    ChatMemberHandler,
    CallbackContext,
    InlineQueryHandler,
    CallbackQueryHandler,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Connect to MySQL database
connection = None

bottoken = None
chat_id = None
nowpaymentsapi = None
price = None




CHECK_STARTED = False


PAYMENT_URL = 'https://api.nowpayments.io/v1/payment'



async def join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global CHECK_STARTED
    global chat_id

    if False == checkStatus():
        await update.message.reply_text('当前机器人已经欠费，请联系群主续费使用')
        return


    if context.chat_data.get('payment_started'):
        await update.message.reply_text('有支付正在处理，请勿重复创建支付')
        return

    if False == CHECK_STARTED:
        CHECK_STARTED = True
        daily_time = datetime.now().time()
        context.job_queue.run_daily(kick_invalid_users, time=daily_time, chat_id=chat_id)
    else:
        await update.message.reply_text('已经有一笔支付在处理，请勿重复输输入')
        await asyncio.sleep(0)
        return

     # 回复一个带有付款链接的按钮
    keyboard = [[InlineKeyboardButton("Pay with TRC20 USDT", callback_data='pay')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Please click the button below to proceed with the payment:', reply_markup=reply_markup)




async def button(update: Update, context: CallbackContext) -> None:
    global nowpaymentsapi
    global price



    query = update.callback_query
    if query.data == 'pay':
        if context.chat_data.get('payment_started'):
            await query.message.reply_text('有支付正在处理，请勿重复创建支付')
            return

        payload = json.dumps({
            "price_amount": price,
            "price_currency": "usd",
            "pay_currency": "usdttrc20",
            "ipn_callback_url": "https://api.nowpayments.io",
            "order_id": str(query.from_user.id) + '_' + datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "order_description": "Apple Macbook Pro 2019 x 1",
            "case": "success"
        })
        headers = {
            'x-api-key': nowpaymentsapi,
            'Content-Type': 'application/json'
        }

        response = requests.request("POST", PAYMENT_URL, headers=headers, data=payload)
        # Define payment address and amount

        if response.status_code != 201:
            context.chat_data['payment_started'] = False
            await query.message.reply_text('处理出错，请重新输入命令\join')
            return

        payment_address = response.json()['pay_address']
        payment_amount = response.json()['pay_amount']
        payment_id = response.json()["payment_id"]
        order_id = response.json()["order_id"]

        # 存储 payment_id 到 chat_data 字典中
        context.chat_data["payment_id"] = payment_id

        context.chat_data["order_id"] = order_id



        message = await query.message.reply_text(f"收款地址{payment_address}，收款金额：{payment_amount}，请使用trc20网络支付")
        context.chat_data['message_id'] = message.message_id
        keyboard = [[InlineKeyboardButton("已经付款", callback_data='paid')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await message.reply_text("请点击以下按钮表示已完成付款：", reply_markup=reply_markup)
        context.chat_data['payment_started'] = True

    if query.data == 'paid':
        wait_time = 3 * 60
        payment_id = context.chat_data.get("payment_id")
        payment_url = f'https://api.nowpayments.io/v1/payment/{payment_id}'

        headers = {'x-api-key': nowpaymentsapi}

        while True:
            response = requests.get(payment_url, headers=headers)

            if response.status_code != 200:
                context.chat_data['payment_started'] = False
                await query.message.reply_text('处理出错，请重新输入命令\join')
                return

            payment_status = response.json()['payment_status']


                # Check payment status and handle accordingly
            if payment_status == 'finished':

                context.chat_data['payment_started'] = False

                user_id = query.from_user.id
                await unban_user(context.bot, user_id, chat_id)

                invite_link = await context.bot.create_chat_invite_link(chat_id=chat_id, expire_date=0)

                order_id = context.chat_data["order_id"]

                await query.message.reply_text(f"您已经成功支付，点击链接加入群组：{invite_link}。您的订单id是:{order_id} ,有疑问请使用订单id联系群主")
                break
            elif payment_status == 'partially_paid':
                    # Handle unpaid status
                await query.message.reply_text("您支付了部分金额，请完成支付")
                time.sleep(wait_time)  # Wait for 3 minutes before querying status again
                continue
            elif payment_status == 'expired' or payment_status == 'failed':
                context.chat_data['payment_started'] = False
                await query.message.reply_text("支付超时或支付失败，请输入/join重新完成支付")
                break
            else:
                await query.message.reply_text("支付正在处理，请耐心等待")
                time.sleep(wait_time)  # Wait for 3 minutes before querying status again
                continue


def record_chat_members(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # 记录用户信息
    id = update.chat_member.from_user.id
    expiration_date = datetime.now() + timedelta(days=365)

    with connection.cursor() as cursor:
        # 查询是否已存在该用户记录
        sql = "SELECT * FROM USERTBL WHERE usr_id=%s"
        cursor.execute(sql, (id,))
        result = cursor.fetchone()

        if result:
            # 如果存在，则检查expiration_date是否需要更新
            if result['expiration_date'] > datetime.now():
                expiration_date = result['expiration_date'] + timedelta(days=365)

            # 更新记录
            sql = "UPDATE USERTBL SET expiration_date=%s WHERE usr_id=%s"
            cursor.execute(sql, (expiration_date, id))
        else:
            # 如果不存在，则插入新记录
            sql = "INSERT INTO USERTBL (usr_id, expiration_date) VALUES (%s, %s)"
            cursor.execute(sql, (id, expiration_date))

        connection.commit()
    return












async def unban_user(bot, user_id, chat_id):
    try:
        member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
    except telegram.error.BadRequest as e:
        # 如果用户从未加入该群组，将会发生 BadRequest 异常
        if e.message == 'Bad Request: user not found':
            return
        else:
            raise e
    if member.status == 'kicked':
        await bot.unban_chat_member(chat_id=chat_id, user_id=user_id)
    await asyncio.sleep(0)


def read_config_file(file_path):

    with open(file_path, "r") as file:
        for line in file:
            key_value_pair = line.strip().split(":")
            if key_value_pair[0] == "bottoken":
                bottoken = ":".join(key_value_pair[1:])
            elif key_value_pair[0] == "chat_id":
                chat_id = key_value_pair[1]
            elif key_value_pair[0] == "nowpaymentsapi":
                nowpaymentsapi = key_value_pair[1]
            elif key_value_pair[0] == "user":
                user = key_value_pair[1]
            elif key_value_pair[0] == "password":
                password = key_value_pair[1]
            elif key_value_pair[0] == "price":
                price = key_value_pair[1]


    return bottoken, chat_id, nowpaymentsapi,price,user, password



async def kick_invalid_users(context):
    chat_id = context.job.chat_id

    if False == checkStatus():
        await update.message.reply_text('当前机器人已经欠费，请联系群主续费使用')
        return
    with connection.cursor() as cursor:
        # 查询用户的使用期限
        sql = "SELECT usr_id, expiration_date FROM USERTBL"
        cursor.execute(sql)
        results = cursor.fetchall()

        for result in results:

            print(result)
            usr_id = result['usr_id']
            expiration_date = result['expiration_date']
            # 将 expiration_date 转换为日期对象
            # Convert expiration_date string to datetime object


            # 比较当前日期和过期日期
            if datetime.now() >= expiration_date:
                try:
                    await context.bot.ban_chat_member(chat_id=chat_id, user_id=usr_id)
                except telegram.error.BadRequest:
                    print(f"User {usr_id} is not a member of the chat")
        await asyncio.sleep(0)

def checkStatus():
    # 创建客户端对象并授权
    # 通过 API 密钥创建凭据
    global bottoken
    creds =ServiceAccountCredentials.from_json_keyfile_name('deft-province-315910-3b247578727f.json')

    # 访问您的Google Sheet
    client = gspread.authorize(creds)

    # 选择您要打开的工作表
    sheet = client.open("GroupManager").sheet1


    # 读取所有单元格的值并打印出来
    records  = sheet.get_all_records()
    current_date = datetime.now().strftime("%Y-%m-%d")

    for record in records:
        if record['bottoken'] == bottoken:
            dt_obj = datetime.strptime(record['Expired Date'], "%m/%d/%Y %H:%M:%S")
            formatted_date = dt_obj.strftime("%Y/%m/%d")
            if formatted_date < current_date:
                return False
            else:
                return True


def main() -> None:
    global bottoken
    global chat_id
    global nowpaymentsapi
    global price
    global connection
    bottoken,  chat_id, nowpaymentsapi, price, user , password= read_config_file("config.txt")

    connection = pymysql.connect(
        host="localhost",
        user=user,
        password=password,
        database="usertable",
        cursorclass=pymysql.cursors.DictCursor,
    )

    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(bottoken).build()

    application.add_handler(CommandHandler("join", join))

    application.add_handler(CallbackQueryHandler(button))

    application.add_handler(ChatMemberHandler(record_chat_members, ChatMemberHandler.CHAT_MEMBER))


    # Run the bot until the user presses Ctrl-C


    # Run the bot until the user presses Ctrl-C
    application.run_polling()




    # 每天固定时间执行kick_invalid_users函数





if __name__ == "__main__":
    main()
