import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Filters,
    CommandHandler,
    MessageHandler,
    Updater,
    CallbackQueryHandler,
    CallbackContext,
    ConversationHandler,
)

import logging

# from apscheduler.schedulers.blocking import BlockingScheduler

from news_search import newsUpdater

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Authentication
with open("./access_token.txt") as f:
    lines = f.readlines()
    TOKEN = lines[0].strip()

bot = telegram.Bot(token=TOKEN)


# chat_id = bot.getUpdates()[-1].message.chat.id  # 봇에 메시지를 보내기 위한 chat id 구하기

# sched = BlockingScheduler()


# 기존에 보냈던 링크를 담아둘 리스트
old_links = dict()
keywords = set()

# update = bot.get_updates()

# for u in updates:
#     print(u.message["chat"]["username"], u.message["chat"])

# chat_id = bot.getUpdates()[-1].message.chat.id  # 가장 최근에 온 메세지의 chat id를 가져옵니다
# print(chat_id)


def get_chat_id(update, context):
    chat_id = -1

    if update.message is not None:
        # text message
        chat_id = update.message.chat.id
    elif update.callback_query is not None:
        # callback message
        chat_id = update.callback_query.message.chat.id
    elif update.poll is not None:
        # answer in Poll
        chat_id = context.bot_data[update.poll.id]

    return chat_id


def start(update: Update, context: CallbackContext) -> None:
    options = [
        [
            InlineKeyboardButton(text="키워드 추가", callback_data="1"),
            InlineKeyboardButton(text="키워드 삭제", callback_data="2"),
        ],
        [
            InlineKeyboardButton(text="현재 키워드 목록", callback_data="3"),
            InlineKeyboardButton(text="검색주기 설정", callback_data="4"),
        ],
        [
            InlineKeyboardButton(text="지금 검색", callback_data="5"),
        ],
    ]

    # Buttons' layout markup
    reply_markup = InlineKeyboardMarkup(options)

    # Message with the buttons
    context.bot.send_message(
        chat_id=get_chat_id(update, context),
        text="원하는 작업이 무엇인가?",
        reply_markup=reply_markup,
    )

    # selection from callback
    # choice = update.callback_query.data
    # if choice == "1":
    #     # Choice 1: Text
    #     update.callback_query.message.edit_text("You have chosen Text")


def current_keyword(update: Update, context: CallbackContext):
    print(update.message)
    if len(keywords) == 0:
        context.bot.send_message(get_chat_id(update, context), "키워드를 추가하세요 /start")

    else:
        context.bot.send_message(
            get_chat_id(update, context), f"현재 키워드 [{' | '.join(list(keywords))}]"
        )


def add_keyword(update: Update, context: CallbackContext) -> None:
    global keywords
    user = update.message.from_user
    input_keyword = update.message.text.strip()
    print(input_keyword, keywords)

    if "초기화" in input_keyword.split():
        keywords = set()
    elif input_keyword not in keywords:
        update.message.reply_text(f"{user.first_name}(이)가 추가할 키워드는 [{input_keyword}]")
        keywords.add(input_keyword)
        # Add new keyword into old_links
        if input_keyword not in old_links.keys():
            old_links[input_keyword] = []
    else:
        update.message.reply_text(f"{user.first_name}(이)가 제거할 키워드는 [{input_keyword}]")
        keywords.remove(input_keyword)
    current_keyword(update, context)


# def remove_keyword(update: Update, context: CallbackContext) -> None:
#     user = update.message.from_user
#     update.message.reply_text(f"{user.name}(이)가 삭제할 키워드는 [{update.message.text}]")


def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    choice = query.data
    # print(query)

    query.edit_message_text(text=f"네, 알겠습니다!")

    if choice == "1":
        # Add a keyword to the list
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"추가할 키워드는 무엇?")
    elif choice == "2":
        # Remove a selected keyword from the list
        pass
    elif choice == "3":
        current_keyword(update, context)

    elif choice == "4":
        pass

    else:
        send_links(update, context)


def send_links(update: Update, context: CallbackContext) -> None:
    global old_links, keywords

    for keyword in keywords:
        updater = newsUpdater(keyword)
        # print(f"saved links : {sorted(old_links[keyword])}")
        new_links = updater.get_updated_news(old_links[keyword])
        # print(f"new links : {sorted(new_links)}\n===============\n")

        if new_links:
            context.bot.sendMessage(
                chat_id=get_chat_id(update, context),
                text=f"=====\n{keyword} 관련 새로운 뉴스 {len(new_links)}건\n=====",
            )
            for link in new_links:
                context.bot.sendMessage(chat_id=get_chat_id(update, context), text=link)
                # bot.sendMessage(chat_id=62786931, text=link)
        else:
            context.bot.sendMessage(
                chat_id=get_chat_id(update, context),
                text=f"=====\n{keyword} 관련 새로운 뉴스 없음!\n=====",
            )

        old_links[keyword] += new_links.copy()
        # old_links = list(set(old_links))


def help_command(update: Update, context: CallbackContext) -> None:
    """Displays info on how to use the bot."""
    update.message.reply_text("/hey 입력하면 시작할 수 있음")
    print(old_links)


# def handler(msg):
#     content_type, chat_type, chat_id, msg_date, msg_id = telepot.glance(msg, long=True)

#     print(msg)

#     if content_type == "text":
#         str_message = msg["text"]
#         if str_message[0:1] == "/":
#             args = str_message.split(" ")
#             command = args[0]
#             del args[0]

#             #'/뉴스 <원하는 기업>'으로 텔레그램 봇에 입력하면 get_news 함수가 실행된다.
#             # 추후에 한 코드 안에 다른 기능도 넣을 예정이라 이렇게 구분 지었다.
#             if command == "/뉴스":
#                 n = " ".join(args)
#                 new_links = get_news(n)
#                 for link in new_links:
#                     bot.sendMessage(chat_id, text=link)


def main() -> None:
    """
    Run the bot
    """
    updater = Updater(TOKEN)

    updater.dispatcher.add_handler(CommandHandler("hey", start))
    updater.dispatcher.add_handler(CallbackQueryHandler(button))
    updater.dispatcher.add_handler(
        MessageHandler(Filters.text & ~Filters.command, add_keyword)
    )
    updater.dispatcher.add_handler(CommandHandler("help", help_command))

    updater.start_polling()

    updater.idle()


if __name__ == "__main__":
    main()

    # send_links()
    # 스케쥴러 세팅 및 작동
    # sched.add_job(send_links, "interval", minutes=10)
    # sched.start()
