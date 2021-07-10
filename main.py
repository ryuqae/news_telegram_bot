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


# Logger
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Parsing arguments
parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument("--DB_FILE", required=False, default="new_user_db.json", help="Database filename")
parser.add_argument("--TOKEN_FILE", required=False, default="access_token_test.txt", help="Access token filename")
parser.add_argument("--MIN_DUR", required=True, help="Minimum duration for alert")
args=parser.parse_args()


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


def read_user_db() -> dict:
    try:
        with open(DB_FILE, "r") as f:
            user_db = json.load(f)
    except FileNotFoundError:
        with open(DB_FILE, "w") as f:
            f.write("{}")
        return read_user_db()
    print(f"{DB_FILE} is loaded successfully")
    return user_db


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
    user = update.message.from_user
    user_db = read_user_db()

    if chat_id not in user_db.keys():
        user_db[chat_id] = {}
        update_user_db(user_db)
        context.bot.send_message(
            chat_id,
            f"{party} {user.first_name}님, 새로 오신 것을 환영합니다!\n사용법이 궁금하시면 /help 를 입력하세요.",
        )
    else:
        context.bot.send_message(chat_id, f"{user.first_name}님, 안녕하세요!")

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
    user_db = read_user_db()
    chat_id = get_chat_id(update, context)
    nl = '\n'

    try:
        old_links_dict = user_db[chat_id]
        keywords = old_links_dict.keys()
        text = (
            f"{siren} 등록된 키워드가 없습니다.\n키워드를 추가하세요!"
            if len(keywords) == 0
            else f"{bookmark} 현재 키워드 목록 {bookmark}\n\n{nl.join(list(keywords))}"
        )
        context.bot.send_message(chat_id, text)

    except KeyError:
        start(update, context)
        # context.bot.send_message(chat_id, f"{siren} 등록된 키워드가 없습니다.\n키워드를 추가하세요!")


def add_keyword(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    chat_id = get_chat_id(update, context)
    user_db = read_user_db()

    old_links_dict = user_db[chat_id]

    keywords = old_links_dict.keys()
    input_keyword = update.message.text.strip()
    print(f"user {user.first_name}'s new keyword is {input_keyword}")

    if input_keyword == "초기화!":
        del user_db[chat_id]
        unset(update, context)
        print("ID DELETED SUCCESS") if chat_id not in user_db.keys() else print(
            "ID DELETED FAIL"
        )
    elif input_keyword not in keywords:
        # If there is no keyword in the list, then add keyword and its new list to store old links
        old_links_dict[input_keyword] = []
        update.message.reply_text(f"{plus} [{input_keyword}] 추가 완료!")

    else:
        del old_links_dict[input_keyword]
        update.message.reply_text(f"{minus} [{input_keyword}] 삭제 완료!")

    update_user_db(user_db)
    current_keyword(update, context)


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
    user_db = read_user_db()

    old_links_dict = user_db[chat_id]

    keywords = user_db[chat_id].keys()
    current_jobs = context.job_queue.get_jobs_by_name(chat_id)

    for keyword in keywords:
        updater = newsUpdater(query=keyword, sort=1)
        new_links = updater.get_updated_news(old_links_dict[keyword])

        if new_links:
            context.bot.send_message(
                chat_id=chat_id,
                text=f"{siren} [{keyword}] 새로운 뉴스 {len(new_links)}건 {siren}",
            )
            for link in new_links[::-1]:
                context.bot.send_message(chat_id=chat_id, text=f"[{keyword}]\n{link['title']}\n{link['link']}")
            # context.bot.send_message(
            #     chat_id=chat_id,
            #     text=f"{lightning} Quick /start {lightning}",
            # )
        elif len(current_jobs)==0:
            # No news notification only for no job exist case.
            context.bot.send_message(
                chat_id=chat_id,
                text=f"[{keyword}] 새로운 뉴스 없음!",
            )
            pass

        old_links_dict[keyword] += new_links.copy()
        # keep links only 1 day(keeptime=1)
        old_links_dict[keyword] = updater.remove_outdated_news(old_links_dict[keyword], keeptime=1).copy()

    update_user_db(user_db)


def help_command(update: Update, context: CallbackContext) -> None:
    """Displays info on how to use the bot."""
    update.message.reply_text(
        "/start : 현재 상태 확인\n\n1. 키워드 편집\n현재 목록에 없는 키워드를 입력하면 추가되고, 이미 추가된 키워드를 다시 한 번 입력하면 삭제됩니다.\n\n2. 키워드 초기화\n[초기화!]를 입력하면 저장된 키워드가 모두 삭제됩니다.\n\n3. 뉴스 알림주기 설정\n/set 설정할 알림주기(단위: 초)\n/unset 알림해제"
    )


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
