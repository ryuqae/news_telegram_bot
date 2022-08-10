kill -9 `cat test/testbot.pid`
nohup python3 main.py --MIN_DUR 10 --TOKEN_FILE auth/test_token.txt --DB_FILE database/zipxa2_20220807.db  > test/testbot.log 2>&1 & echo $! > test/testbot.pid
