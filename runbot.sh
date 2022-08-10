kill -9 `cat log/zipxa.pid`
kill -9 `cat log/zipxa1.pid`
kill -9 `cat log/zipxa2.pid`
kill -9 `cat log/zipxa3.pid`
kill -9 `cat log/zipxa4.pid`

nohup python3 main.py --MIN_DUR 10 --TOKEN_FILE auth/zipxa_token.txt --DB_FILE database/zipxa_20220807.db > log/zipxa.log 2>&1 & echo $! > log/zipxa.pid
nohup python3 main.py --MIN_DUR 10 --TOKEN_FILE auth/zipxa1_token.txt --DB_FILE database/zipxa1_20220807.db > log/zipxa1.log 2>&1 & echo $! > log/zipxa1.pid
nohup python3 main.py --MIN_DUR 10 --TOKEN_FILE auth/zipxa2_token.txt --DB_FILE database/zipxa2_20220807.db > log/zipxa2.log 2>&1 & echo $! > log/zipxa2.pid
nohup python3 main.py --MIN_DUR 10 --TOKEN_FILE auth/zipxa3_token.txt --DB_FILE database/zipxa3_20220807.db > log/zipxa3.log 2>&1 & echo $! > log/zipxa3.pid
nohup python3 main.py --MIN_DUR 10 --TOKEN_FILE auth/zipxa4_token.txt --DB_FILE database/zipxa4_20220807.db > log/zipxa4.log 2>&1 & echo $! > log/zipxa4.pid