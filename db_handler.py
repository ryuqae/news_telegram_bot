import sqlite3
from datetime import datetime, timedelta
from sqlite3.dbapi2 import IntegrityError


class Handler:
    def __init__(self, db_file: str) -> None:
        self.db_file = db_file

        self.user_table = "user"
        self.keyword_table = "keyword"
        self.article_table = "article"

        (
            self.user_id,
            self.username,
            self.keyword,
            self.url,
            self.title,
            self.added_timestamp,
            self.active,
        ) = "uid name query url title added_timestamp active".split()

        user_init = f"""CREATE TABLE IF NOT EXISTS {self.user_table} ({self.user_id} INTEGER NOT NULL, {self.username} TEXT, {self.added_timestamp} TEXT, {self.active} INTEGER, PRIMARY KEY({self.user_id}))"""
        keyword_init = f"""CREATE TABLE IF NOT EXISTS {self.keyword_table} ({self.user_id} INTEGER NOT NULL, {self.keyword} TEXT, {self.added_timestamp} TEXT, {self.active} INTEGER, UNIQUE({self.user_id}, {self.keyword}))"""
        article_init = f"""CREATE TABLE IF NOT EXISTS {self.article_table} ({self.user_id} INTEGER NOT NULL, {self.keyword} TEXT, {self.url} TEXT NOT NULL, {self.title} TEXT, {self.added_timestamp} TEXT, {self.active} INTEGER, UNIQUE({self.user_id}, {self.keyword}, {self.url}))"""

        with sqlite3.connect(db_file) as conn:
            cur = conn.cursor()
            cur.execute(user_init)
            cur.execute(keyword_init)
            cur.execute(article_init)
            conn.commit()

    def _get(self, query: str) -> list:
        with sqlite3.connect(self.db_file) as conn:
            cur = conn.cursor()
            cur.execute(query)
            result = cur.fetchall()
            return result

    def _update(self, query: str, data: list = None) -> bool:
        with sqlite3.connect(self.db_file) as conn:
            cur = conn.cursor()
            if not data:
                cur.execute(query)
                return True
            else:
                try:
                    cur.executemany(query, data)
                    conn.commit()
                    return True
                except IntegrityError:
                    return False

    def check_connection(self, conn: sqlite3.Connection) -> None:
        try:
            conn.cursor()
            return True
        except Exception as e:
            return False

    def get_user(self, id: int = None) -> bool:
        if id is None:
            sql = f"""
            SELECT {self.user_id} from {self.user_table} WHERE {self.active}=1
            """
        else:
            sql = f"""
                SELECT * from {self.user_table} WHERE {self.user_id}=={id} AND {self.active}=1
                """
        return self._get(sql)

    def add_user(self, id: int, name: str) -> bool:
        sql = f"""
            INSERT INTO {self.user_table}({self.user_id}, {self.username}, {self.added_timestamp}, {self.active}) VALUES(?,?,?,?)
            ON CONFLICT({self.user_id}) DO UPDATE SET {self.active} = {self.active} * -1
            """

        row = [(id, name, datetime.now(), 1)]

        return self._update(sql, row)

    def add_keyword(self, id: int, keyword: str):
        sql = f"""
        INSERT INTO {self.keyword_table}({self.user_id}, {self.keyword}, {self.added_timestamp}, {self.active}) VALUES(?,?,?,?)
        ON CONFLICT({self.user_id}, {self.keyword}) DO UPDATE SET {self.active} = {self.active} * -1
        """
        row = [(id, keyword, datetime.now(), True)]

        return self._update(sql, row)

    def del_account(self, id: int):
        kw_sql = f"""
        UPDATE {self.keyword_table} SET {self.active}=-1 WHERE {self.user_id}={id}
        """
        user_sql = f"""
        UPDATE {self.user_table} SET {self.active}=-1 WHERE {self.user_id}={id} 
        """

        return self._update(user_sql) & self._update(kw_sql)

    def get_keyword(self, id: int):
        sql = f"""
        SELECT {self.keyword}, {self.added_timestamp} FROM {self.keyword_table} WHERE {self.user_id}={id} AND {self.active}=1
        """
        return self._get(sql)

    def get_links(self, id: int, keyword: str) -> bool:
        sql = f"""
        SELECT * FROM {self.article_table} WHERE {self.user_id} = {id} AND {self.keyword} = '{keyword}' AND {self.active} = 1
        """
        return self._get(sql)

    def add_links(self, id: int, keyword: str, articles: list) -> bool:
        sql = f"""
        INSERT INTO {self.article_table}({self.user_id}, {self.keyword}, {self.url}, {self.title}, {self.added_timestamp}, {self.active}) VALUES(?,?,?,?,?,?)
        ON CONFLICT({self.user_id}, {self.keyword}, {self.url}) DO UPDATE SET {self.active} = 1
        """
        data = [
            (id, keyword, article["link"], article["title"], datetime.now(), 1)
            for article in articles
        ]
        # print("ADD LINK DATA", data)

        return self._update(sql, data)

    def remove_outdated_news(self, id: int, keyword: str, keeptime: int) -> None:
        outdated = datetime.now() - timedelta(days=keeptime)

        sql = f"""
        UPDATE {self.article_table} SET {self.active} = -1 WHERE {self.user_id} = {id} AND {self.keyword} = '{keyword}' AND {self.added_timestamp} < '{outdated}'
        """
        return self._update(sql)


if __name__ == "__main__":
    handler = Handler("new6.db")
    # handler.add_user(id=3239233, name="jeongwoo")
    # added = handler.add_keyword(id=3239233, keyword="삼성전자")
    # print(f"키워드 추가 완료 {added}")
    # handler.add_keyword(id=3239, keyword="카카오")
    # handler.add_keyword(id=3239, keyword="신라호텔")

    # keywords = handler.get_keyword(id=3239233)
    # urls = ["http://naver.com/mai", "http://ddanzi.com/freee", "http://google.com/home"]
    # add_link = handler.add_links(id=3239, keyword="삼성전자", articles=urls)
    handler.remove_outdated_news(62786931, "삼성전자", 60)

    # print(handler.get_links(3239, "삼성전자"))

    # print(add_link)
    # print(f"키워드 목록 {keywords}")
