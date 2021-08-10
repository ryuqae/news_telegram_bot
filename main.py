from sqlite3 import dbapi2
from urllib import parse
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import (
    Filters,
    CommandHandler,
    MessageHandler,
    Updater,
    CallbackQueryHandler,
    CallbackContext,
)
from emoji import emojize
import logging
import json
import argparse
from news_search import newsUpdater

from db_handler import Handler
import sqlite3


# Logger
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Parsing arguments
parser = argparse.ArgumentParser(description="Process some integers.")
parser.add_argument(
    "--DB_FILE", required=False, default="new_user_db.json", help="Database filename"
)
parser.add_argument(
    "--TOKEN_FILE",
    required=False,
    default="access_token_test.txt",
    help="Access token filename",
)
parser.add_argument("--MIN_DUR", required=True, help="Minimum duration for alert")
args = parser.parse_args()


DB_FILE = args.DB_FILE
TOKEN_FILE = args.TOKEN_FILE

# # Minimum duration for notification
MIN_DUR = int(args.MIN_DUR)

print(f"Minimum Duration: {MIN_DUR}sec.")


# Predefined emojis
bookmark = emojize(":bookmark:", use_aliases=True)
bell = emojize(":bell:", use_aliases=True)
lightning = emojize(":high_voltage:", use_aliases=True)
good = emojize(":smiling_face_with_sunglasses:", use_aliases=True)
siren = emojize(":police_car_light:", use_aliases=True)
plus = emojize(":plus:", use_aliases=True)
minus = emojize(":minus:", use_aliases=True)
party = emojize(":party_popper:", use_aliases=True)


# Authentication
with open(TOKEN_FILE) as f:
    lines = f.readlines()
    TOKEN = lines[0].strip()


with open("search_help.txt", "r") as f:
    search_help = f.readlines()


# Connect to the given db file
handler = Handler(DB_FILE)


# def read_user_db() -> dict:
#     try:
#         with open(DB_FILE, "r") as f:
#             user_db = json.load(f)
#     except FileNotFoundError:
#         with open(DB_FILE, "w") as f:
#             f.write("{}")
#         return read_user_db()
#     print(f"{DB_FILE} is loaded successfully")
#     return user_db


def update_user_db(user_db: dict) -> bool:
    with open(DB_FILE, "w+") as f:
        temp = json.dumps(user_db, ensure_ascii=False, sort_keys=True, indent=4)
        f.write(temp)
    print("user_db.json is written successfully!")


# Get chat_id to send message under each context
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
    return str(chat_id)


def start(update: Update, context: CallbackContext) -> None:
    chat_id = get_chat_id(update, context)
    # print(chat_id)
    user_db = handler.get_user(chat_id)

    user = update.message.from_user
    # user_db = read_user_db()

    if len(user_db) == 0:
        result = handler.add_user(chat_id, user.first_name)
        if result:
            context.bot.send_message(
                chat_id,
                f"{party} {user.first_name}님, 새로 오신 것을 환영합니다!\n사용법이 궁금하시면 /help 를 입력하세요.",
            )
    else:
        context.bot.send_message(chat_id, f"{good} {user.first_name}님, 안녕하세요!")

    options = [
        [
            # InlineKeyboardButton(text="키워드 편집", callback_data="1"),
            InlineKeyboardButton(
                text=f"{bookmark} 현재 키워드 목록 {bookmark}", callback_data="2"
            ),
        ],
        [
            InlineKeyboardButton(text=f"{bell} 설정된 뉴스 알림 {bell}", callback_data="3"),
        ],
        [
            InlineKeyboardButton(
                text=f"{lightning} 지금 검색 {lightning}", callback_data="4"
            ),
        ],
    ]

    # Buttons' layout markup
    reply_markup = InlineKeyboardMarkup(options)

    # Message with the buttons
    context.bot.send_message(
        chat_id=chat_id,
        text="원하는 작업을 선택하세요.",
        reply_markup=reply_markup,
    )


def current_keyword(update: Update, context: CallbackContext) -> None:
    # user_db = read_user_db()
    chat_id = get_chat_id(update, context)
    nl = "\n"

    print(DB_FILE)

    # with sqlite3.connect(DB_FILE) as conn:
    #     cursor = conn.cursor()
    #     cursor.execute("SELECT * FROM keywords")
    #     print(cursor.fetchall())

    keywords = handler.get_keyword(chat_id)
    # [('나나나', '2021-08-10 16:36:38.117548'), ('삼성물산', '2021-08-10 16:29:58.278979'), ('삼성전자', '2021-08-10 16:29:26.077459'), ('옹', '2021-08-10 16:36:36.157206'), ('자반고등어', '2021-08-10 16:36:40.397227'), ('카카오', '2021-08-10 16:29:45.387042')]

    print(keywords)

    text = (
        f"{siren} 등록된 키워드가 없습니다.\n키워드를 추가하세요!"
        if len(keywords) == 0
        else f"{bookmark} 현재 키워드 목록 {bookmark}\n\n{nl.join([kw[0] for kw in keywords])}"
    )
    context.bot.send_message(chat_id, text)

    # try:

    # except KeyError:
    #     start(update, context)
    #     # context.bot.send_message(chat_id, f"{siren} 등록된 키워드가 없습니다.\n키워드를 추가하세요!")


def add_keyword(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    chat_id = get_chat_id(update, context)

    input_keyword = update.message.text.strip()
    print(f"user {user.first_name}'s new keyword is {input_keyword}")

    if input_keyword == "초기화!":
        unset(update, context)
        del_account = handler.del_account(chat_id)
        text = (
            f"{good} {user.first_name}의 계정 정보가 초기화 되었습니다."
            if del_account
            else f"다음에 다시 시도해주세요."
        )
        update.message.reply_text(text)

    elif input_keyword is not None:
        # If there is no keyword in the list, then add keyword and its new list to store old links
        # old_links_dict[input_keyword] = []
        result = handler.add_keyword(chat_id, input_keyword)
        if result:
            update.message.reply_text(f"{plus} [{input_keyword}] 추가 완료!")
        else:
            update.message.reply_text(f"{minus} [{input_keyword}] 삭제 완료!")
        current_keyword(update, context)

    # else:
    #     del old_links_dict[input_keyword]
    #     update.message.reply_text(f"{minus} [{input_keyword}] 삭제 완료!")

    # update_user_db(user_db)


def check_alert_interval(chat_id: str, update: Update, context: CallbackContext):
    current_jobs = context.job_queue.get_jobs_by_name(chat_id)
    try:
        interval = current_jobs[0].job.trigger.interval
        return interval

    except (NameError, IndexError):
        return None


def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    choice = query.data

    chat_id = get_chat_id(update, context)

    query.edit_message_text(text=f"네, 알겠습니다! {good}")

    if choice == "1":
        # Add a keyword to the list
        current_keyword(update, context)
        context.bot.send_message(chat_id=chat_id, text=f"추가 혹은 삭제할 키워드를 입력하세요.")

    elif choice == "2":
        current_keyword(update, context)

    elif choice == "3":
        interval = check_alert_interval(chat_id, update, context)

        text = (
            f"{siren} 아직 설정된 알림이 없습니다.\n``` /set 설정할 알림주기(단위: 초)```"
            if interval is None
            else f"{bell} 현재 설정된 알림주기 {bell}\n``` {interval} ```"
        )

        context.bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")

    elif choice == "4":
        # Get news immediately
        context.job_queue.run_once(send_links, 0, context=chat_id, name=str(chat_id))


def send_links(context: CallbackContext) -> None:
    job = context.job
    chat_id = str(job.context)

    keywords = handler.get_keyword(chat_id)
    keywords = [kw[0] for kw in keywords]
    current_jobs = context.job_queue.get_jobs_by_name(chat_id)

    for keyword in keywords:
        updater = newsUpdater(query=keyword, sort=1)
        new_links = updater.get_updated_news(handler.get_links(chat_id, keyword))

        if new_links:
            context.bot.send_message(
                chat_id=chat_id,
                text=f"{siren} [{keyword}] 새로운 뉴스 {len(new_links)}건 {siren}",
            )
            for link in new_links[::-1]:
                context.bot.send_message(
                    chat_id=chat_id,
                    text=f"[{keyword}]\n{link['title']}\n{link['link']}",
                )
            # context.bot.send_message(
            #     chat_id=chat_id,
            #     text=f"{lightning} Quick /start {lightning}",
            # )
        elif len(current_jobs) == 0:
            # No news notification only for no job exist case.
            context.bot.send_message(
                chat_id=chat_id,
                text=f"[{keyword}] 새로운 뉴스 없음!",
            )
            pass

        handler.add_links(chat_id, keyword, new_links)

        # old_links_dict[keyword] += new_links.copy()
        # # keep links only 1 day(keeptime=1)
        # old_links_dict[keyword] = updater.remove_outdated_news(
        #     old_links_dict[keyword], keeptime=1
        # ).copy()

    # update_user_db(user_db)


def help_command(update: Update, context: CallbackContext) -> None:
    """Displays info on how to use the bot."""
    update.message.reply_text(" ".join(search_help), parse_mode="Markdown")


def remove_job_if_exists(name: str, context: CallbackContext) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


def set_timer(update: Update, context: CallbackContext):
    global due
    chat_id = update.message.chat_id
    try:
        # args[0] should contain the time for the timer in seconds.
        due = int(context.args[0])
        if due < MIN_DUR:
            update.message.reply_text(
                f"{siren} 최소 {MIN_DUR}초 이상으로 지정해주세요.\n현재 입력값: {due}초"
            )
            return
        job_removed = remove_job_if_exists(str(chat_id), context)

        context.job_queue.run_repeating(
            send_links, due, context=chat_id, name=str(chat_id)
        )
        text = f"{good} 뉴스 알림주기 설정 완료!\n지금부터 {due}초마다 알려드릴게요."
        if job_removed:
            text += f"\n\n{siren} 기존에 설정된 값은 삭제됩니다."
        update.message.reply_text(text)

    except (IndexError, ValueError):
        update.message.reply_text("/set 설정할 알림주기(단위: 초)")


def unset(update: Update, context: CallbackContext) -> None:
    """Remove the job if the user changed their mind."""
    chat_id = update.message.chat_id
    job_removed = remove_job_if_exists(str(chat_id), context)
    text = f"{good} 더이상 뉴스알림이 울리지 않습니다." if job_removed else f"{siren} 설정된 뉴스알림이 없습니다."
    update.message.reply_text(text)


def main() -> None:
    """
    Run the bot
    """
    # Reboot Message for the next version
    # bot = telegram.Bot(token=TOKEN)
    # bot.sendMessage(chat_id="62786931", text=f'{siren} 봇이 재시작되어 알림이 해제되었습니다. 다시 설정해 주세요!')

    updater = Updater(TOKEN)

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("set", set_timer))
    dp.add_handler(CommandHandler("unset", unset))

    dp.add_handler(CallbackQueryHandler(button))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, add_keyword))
    dp.add_handler(CommandHandler("help", help_command))

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
