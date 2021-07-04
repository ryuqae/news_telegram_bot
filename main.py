import telegram
from telegram.ext import CommandHandler

import logging
from apscheduler.schedulers.blocking import BlockingScheduler

# import json
from news_search import newsUpdater

# logging.basicConfig(
#     level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
# )


with open("./access_token.txt") as f:
    lines = f.readlines()
    TOKEN = lines[0].strip()

bot = telegram.Bot(token=TOKEN)
sched = BlockingScheduler()


# 기존에 보냈던 링크를 담아둘 리스트
old_links = []

updates = bot.get_updates()

# for u in updates:
#     print(u.message["chat"]["username"], u.message["chat"])


# chat_id = bot.getUpdates()[-1].message.chat.id  # 가장 최근에 온 메세지의 chat id를 가져옵니다
# print(chat_id)

# bot.sendMessage(chat_id=chat_id, text="안녕하세요")


def send_links():
    global old_links
    updater = newsUpdater("카카오")
    print(f"saved links : {sorted(old_links)}")
    new_links = updater.get_updated_news(old_links)
    print(f"new links : {sorted(new_links)}\n===============\n")

    if new_links:
        bot.sendMessage(chat_id=62786931, text=f"새로운 뉴스 {len(new_links)}건")
        for link in new_links:
            bot.sendMessage(chat_id=62786931, text=link)
    else:
        bot.sendMessage(chat_id=62786931, text="새로운 뉴스 없음")
    old_links += new_links.copy()
    old_links = list(set(old_links))


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


if __name__ == "__main__":
    send_links()
    # 스케쥴러 세팅 및 작동
    sched.add_job(send_links, "interval", minutes=10)
    sched.start()
