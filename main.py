from sqlite3 import dbapi2
from urllib import parse
import telegram
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
import re


# Logger
logging.basicConfig(
    level=logging.ERROR, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Parsing arguments
parser = argparse.ArgumentParser(description="Process some integers.")
parser.add_argument(
    "--DB_FILE", required=True, help="Database filename"
)
parser.add_argument(
    "--TOKEN_FILE",
    required=False,
    default="auth/access_token.txt",
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
    user_db = handler.get_user(chat_id)

    user = update.message.from_user

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
            # InlineKeyboardButton(text="키워드 삭제", callback_data="1"),
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


def current_keyword(update: Update, context: CallbackContext) -> list:
    chat_id = get_chat_id(update, context)
    nl = "\n"

    keywords = handler.get_keyword(chat_id)
    # [('나나나', 1, '2021-08-10 16:36:38.117548'), ('삼성물산', 0, '2021-08-10 16:29:58.278979'), ('삼성전자', '2021-08-10 16:29:26.077459'), ('옹', '2021-08-10 16:36:36.157206'), ('자반고등어', '2021-08-10 16:36:40.397227'), ('카카오', '2021-08-10 16:29:45.387042')]

    if len(keywords) == 0:
        text = f"{siren} 등록된 키워드가 없습니다.\n키워드를 추가하세요!"
    else:
        # for i in keywords:
        #     print(i)
        listup = [f'[{idx+1:^5d}] {kw[1]} **{kw[2]}' if kw[3]==1 else f'[{idx+1:^5d}] {kw[1]}' for idx, kw in enumerate(keywords)]
        text = f"{bookmark} 현재 키워드 목록 {bookmark}\n\n{nl.join(listup)}"

    return text, keywords


def add_keyword(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    chat_id = get_chat_id(update, context)

    input_keyword = update.message.text.strip()
    # print(f"user {user.first_name}'s new keyword is {input_keyword}")

    if input_keyword == "초기화!":
        unset(update, context)
        del_account = handler.del_account(chat_id)
        text = (
            f"{good} {user.first_name}의 계정 정보가 초기화 되었습니다."
            if del_account
            else f"다음에 다시 시도해주세요."
        )
        update.message.reply_text(text)

    elif "**" in input_keyword:
        search_keyword, title_filter = input_keyword.split("**")
        search_keyword = search_keyword.strip()
        title_filter = title_filter.strip()

        handler.add_keyword(id=chat_id, keyword=search_keyword, title_filter=title_filter, mode=1)
        update.message.reply_text(f'[제목필터]"{search_keyword}" 추가 완료!')

        kw_text, _ = current_keyword(update, context)
        context.bot.send_message(chat_id, kw_text)


    elif input_keyword is not None:
        # If there is no keyword in the list, then add keyword and its new list to store old links
        result = handler.add_keyword(id=chat_id, keyword=input_keyword, mode=0)
        
        if result:
            update.message.reply_text(f'[전체알림]"{input_keyword}" 추가 완료!')
        else:
            # Deleted message doesn't work. should get current status from the query.
            update.message.reply_text(f"{minus} [{input_keyword}] 삭제 완료!")
        # current_keyword(update, context)
        kw_text, _ = current_keyword(update, context)
        context.bot.send_message(chat_id, kw_text)

    # else:
    #     del old_links_dict[input_keyword]
    #     update.message.reply_text(f"{minus} [{input_keyword}] 삭제 완료!")

    # update_user_db(user_db)

def delete_keyword(update: Update, context: CallbackContext) -> int:
    chat_id = update.message.chat_id
    try:
        # args[0] should contain the time for the timer in seconds.
        keyword_num = int(context.args[0]) - 1
        kw_text, kw_data = current_keyword(update, context)

        handler.del_keyword(id=chat_id, delete_id=kw_data[keyword_num][0])
        update.message.reply_text(f"{minus} [{kw_data[keyword_num][1]}] 삭제 완료!")


    except (IndexError, ValueError):
        update.message.reply_text("/del 삭제할 키워드 번호")

    kw_text, _ = current_keyword(update, context)
    context.bot.send_message(chat_id, kw_text)



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
        context.bot.send_message(chat_id=chat_id, text=f"삭제할 키워드의 ID를 입력하세요.")

    elif choice == "2":
        kw_text, _ = current_keyword(update, context)
        context.bot.send_message(chat_id, kw_text)

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
    # print(keywords)
    # keywords = [kw[0] for kw in keywords]
    current_jobs = context.job_queue.get_jobs_by_name(chat_id)

    for keyword in keywords:
        kw_id, kw, title_filter, mode, _ = keyword
        updater = newsUpdater(query=kw, sort=1)
        old_links = handler.get_links(chat_id, kw)
        old_links = [link[2] for link in old_links]
        new_links, search_desc = updater.get_updated_news(old_links=old_links)

        # Title filter for given words
        if mode == 1:
            # If the keyword has a title filter. -> check if the title is containing any of the keyword(s).
            # only_words = re.sub(r"\W+", " ", kw).split()
            title_filter = title_filter.strip().split(';')
            check_ = lambda title: all(word.strip() in title for word in title_filter)
            # check_ = lambda title: any(word in title for word in only_words)
            new_links = [link for link in new_links if check_(link["title"])]
            search_desc += f" + [{', '.join(title_filter)}] 제목에 포함"

        else:
            pass

        if new_links:

            context.bot.send_message(
                chat_id=chat_id,
                text=f"{siren} [{kw}] 새로운 뉴스 {len(new_links)}건 {siren}\n- {search_desc}",
            )
            for link in new_links[::-1]:
                context.bot.send_message(
                    chat_id=chat_id,
                    text=f"[{kw}]\n{link['title']}\n{link['link']}",
                )
            handler.add_links(chat_id, kw, new_links)

            # context.bot.send_message(
            #     chat_id=chat_id,
            #     text=f"{lightning} Quick /start {lightning}",
            # )
        elif len(current_jobs) == 0:
            # No news notification only for no job exist case.
            context.bot.send_message(
                chat_id=chat_id,
                text=f"[{kw}] 새로운 뉴스 없음!",
            )
            pass

        # As soon as the new links were sent, check outdated articles and deactivate them
        handler.remove_outdated_news(id=chat_id, keyword=kw, keeptime=1)


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
    bot = telegram.Bot(token=TOKEN)
    all_active_users = [user[0] for user in handler.get_user()]
    # for user_id in all_active_users:
    #     bot.sendMessage(
    #         chat_id=user_id, text=f"{siren} 봇이 재시작되어 알림이 해제되었습니다. 다시 설정해 주세요!"
    #     )

    updater = Updater(TOKEN)

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("set", set_timer))
    dp.add_handler(CommandHandler("unset", unset))
    dp.add_handler(CommandHandler("del", delete_keyword))

    dp.add_handler(CallbackQueryHandler(button))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, add_keyword))
    dp.add_handler(CommandHandler("help", help_command))

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
