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
import os
from news_search import newsUpdater


# Logger
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Predefined emojis
bookmark = emojize(":bookmark:", use_aliases=True)
bell = emojize(":bell:", use_aliases=True)
lightning = emojize(":high_voltage:", use_aliases=True)
good = emojize(":smiling_face_with_sunglasses:", use_aliases=True)
siren = emojize(":police_car_light:", use_aliases=True)
plus = emojize(":plus:", use_aliases=True)
minus = emojize(":minus:", use_aliases=True)

# Authentication
with open("./access_token.txt") as f:
    lines = f.readlines()
    TOKEN = lines[0].strip()


# 기존에 보냈던 링크를 담아둘 리스트
# archieved_txt = [file for file in os.listdir("old_news_link") if file.endswith(".txt")]

with open("user_db.json", "r") as f:
    user_db = json.load(f)

# user_db = {
#     "62786931": {"삼성전자": ["a", "b", "c"]},
#     "1852535116": {"오오": ["d", "e"], "카카오": ["f", "g"]},
# }


# Minimum duration for notification
MIN_DUR = 10


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
    return chat_id


def start(update: Update, context: CallbackContext) -> None:
    chat_id = get_chat_id(update, context)
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
    chat_id = get_chat_id(update, context)
    try:
        old_links_dict = user_db[str(chat_id)]
    except KeyError:
        user_db[str(chat_id)] = {}
        print("new user added!")

    try:
        keywords = old_links_dict.keys()
        # keywords = user_db[str(chat_id)].keys()
        text = (
            f"{siren} 등록된 키워드가 없습니다.\n키워드를 추가하세요!"
            if len(keywords) == 0
            else f"{bookmark} 현재 키워드 목록: [{' | '.join(list(keywords))}]"
        )
        context.bot.send_message(chat_id, text)

    except KeyError:
        old_links_dict = {}
        context.bot.send_message(chat_id, f"{siren} 등록된 키워드가 없습니다.\n키워드를 추가하세요!")


def add_keyword(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    chat_id = get_chat_id(update, context)
    try:
        old_links_dict = user_db[str(chat_id)]
    except KeyError:
        user_db[str(chat_id)] = {}
        print("new user added!")

    keywords = old_links_dict.keys()
    # print(old_links_dict, keywords)

    print(f"user is {user.first_name}")

    input_keyword = update.message.text.strip()
    print(f"new keyword is {input_keyword}")

    if input_keyword == "초기화!":
        user_db[str(chat_id)] = dict()
    elif input_keyword not in keywords:
        # If there is no keyword in the list, then add keyword and its new list to store old links
        old_links_dict[input_keyword] = []
        update.message.reply_text(f"{plus} [{input_keyword}] 추가 완료!")

        # # Add new keyword into old_links
        # if input_keyword not in old_links.keys():
        #     old_links[input_keyword] = []
    else:
        del old_links_dict[input_keyword]
        update.message.reply_text(f"{minus} [{input_keyword}] 삭제 완료!")

    # Save personal keywords as a json at user_db.json
    with open("user_db.json", "w+") as f:
        temp = json.dumps(user_db, ensure_ascii=False, sort_keys=True, indent=4)
        f.write(temp)
        print("user_db.json is written successfully!")

    current_keyword(update, context)


def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    choice = query.data
    # print(query)

    chat_id = get_chat_id(update, context)
    # chat_id = update.effective_chat.id

    query.edit_message_text(text=f"네, 알겠습니다! {good}")

    if choice == "1":
        # Add a keyword to the list
        current_keyword(update, context)
        context.bot.send_message(chat_id=chat_id, text=f"추가 혹은 삭제할 키워드를 입력하세요.")

    elif choice == "2":
        current_keyword(update, context)

    elif choice == "3":
        try:
            context.bot.send_message(
                chat_id=chat_id, text=f"{bell} 현재 설정된 알림주기: {due}분"
            )
        except NameError:
            context.bot.send_message(
                chat_id=chat_id,
                text=f"{siren} 아직 설정된 알림이 없습니다.\n/set [설정할 알림주기(단위: 분)]",
            )
    elif choice == "4":
        # Get news immediately
        context.job_queue.run_once(send_links, 0, context=chat_id, name=str(chat_id))


def send_links(context: CallbackContext) -> None:
    job = context.job
    chat_id = job.context
    try:
        old_links_dict = user_db[str(chat_id)]
    except KeyError:
        user_db[str(chat_id)] = {}
        print("new user added!")

    keywords = user_db[str(chat_id)].keys()

    for keyword in keywords:
        updater = newsUpdater(keyword)
        new_links = updater.get_updated_news(old_links_dict[keyword])

        if new_links:
            context.bot.send_message(
                chat_id=chat_id,
                text=f"=====\n{siren} {keyword} 관련 새로운 뉴스 {len(new_links)}건 {siren}\n=====",
            )
            for link in new_links:
                context.bot.send_message(chat_id=chat_id, text=link)
        else:
            context.bot.send_message(
                chat_id=chat_id,
                text=f"=====\n{keyword} 관련 새로운 뉴스 없음!\n=====",
            )

        old_links_dict[keyword] += new_links.copy()

        # with open(f"old_news_link/{keyword}.txt", "a+") as file:
        #     for link in new_links:
        #         file.write(f"{link}\n")

    with open("user_db.json", "w+") as f:
        temp = json.dumps(user_db, ensure_ascii=False, sort_keys=True, indent=4)
        f.write(temp)
        print("user_db.json is written successfully!")


def help_command(update: Update, context: CallbackContext) -> None:
    """Displays info on how to use the bot."""
    update.message.reply_text(
        "/start : 현재 상태 확인\n\n1. 키워드 편집\n현재 목록에 없는 키워드를 입력하면 추가되고, 이미 추가된 키워드를 다시 한 번 입력하면 삭제됩니다.\n\n2. 키워드 초기화\n[초기화!]를 입력하면 저장된 키워드가 모두 삭제됩니다.\n\n3. 뉴스 알림주기 설정\n/set [설정할 알림주기(단위: 분)]\n알림 해제 : /unset"
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
                f"{siren} 최소 {MIN_DUR}분 이상으로 지정해주세요.\n현재 입력값: {due}분"
            )
            return
        job_removed = remove_job_if_exists(str(chat_id), context)

        context.job_queue.run_repeating(
            send_links, due * 60, context=chat_id, name=str(chat_id)
        )
        text = f"{good} 뉴스 알림주기 설정 완료!\n지금부터 {due}분마다 알려드릴게요."
        if job_removed:
            text += "\n(기존에 설정된 값은 삭제됩니다.)"
        update.message.reply_text(text)

    except (IndexError, ValueError):
        update.message.reply_text("/set [설정할 알림주기(단위: 분)]")


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

    # Read the archieved old links from the text files in old_news_link directory
    # for file in archieved_txt:
    #     with open(os.path.join("old_news_link", file), "r") as f:
    #         old_links[file.split(".")[0]] = f.read().splitlines()[-30:]

    # with open("user_db.json", "r") as f:
    #     user_db = json.load(f)

    print(user_db.keys())

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
