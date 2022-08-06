import requests
from bs4 import BeautifulSoup as bs
from datetime import datetime, timedelta
from urllib import parse


class newsUpdater:
    def __init__(self, query: str, sort: int):
        """
        query : should be encoded
        sort : 0 - related, 1 - recent
        qdt : 0 - general search, 1 - detail search enabled
        pd : 4 - within a day
        """
        self.query = parse.quote(query)
        self.sort = int(sort)

        self.url = f"https://m.search.naver.com/search.naver?where=m_news&query={self.query}&sm=mtb_opt&sort={self.sort}&qdt=1&pd=4"

    def _get_news(self):
        result = requests.get(self.url)
        result_html = result.text
        soup = bs(result_html, "html.parser")

        search_result = soup.select_one("#news_result_list")
        search_desc = soup.select_one(
            "#ct > div.sp_nkeyword.sp_nkeyword_etc > div > div"
        )

        # Search description
        if search_desc:
            search_desc.a.decompose()
            search_desc = search_desc.text
        else:
            search_desc = "일반검색"

        try:
            news_links = search_result.select(".bx > .news_wrap > a")
            return news_links, search_desc

        except AttributeError:
            return [], search_desc

    def remove_outdated_news(self, links: list, keeptime: int) -> None:
        now = datetime.now()
        outdated = timedelta(days=keeptime)
        only_up_to_date = [
            link
            for link in links
            if (now - datetime.strptime(link["added"], "%Y-%m-%d %H:%M:%S") < outdated)
        ]

        # # Logging the oldest articles in each keyword
        # time_passed = [
        #     now - datetime.strptime(link["added"], "%Y-%m-%d %H:%M:%S")
        #     for link in links
        # ]

        # try:
        #     print(f"the oldest news: {max(time_passed)}")
        # except ValueError:
        #     print(f"Nothing remained: {len(time_passed)} should be equal to zero.")

        return only_up_to_date

    def get_updated_news(self, old_links: list):
        new_links = []
        links, search_desc = self._get_news()

        # print(search_desc)
        #  '습도 더운'을 하나이상 포함한 검색결과 중 '오늘' '내일'을 포함한 상세검색 결과입니다.

        # Handling the database based on the time newslinks were added
        # now = datetime.now()
        # old_urls = [old_link['link'] for old_link in old_links]

        for link in links:
            title = str(link.get_text()).strip()
            # Not appending the duplicated links: check based on the link
            if link["href"] not in old_links:
                new_links.append({"title": title, "link": link["href"]})
                #  "added": now.strftime(format="%Y-%m-%d %H:%M:%S")})
                # new_links.extend((title, link["href"]))

        return new_links, search_desc


if __name__ == "__main__":
    import time

    a = newsUpdater(query="+오늘 +내일 습도 | 더운", sort=1)
    b = newsUpdater(query='+오늘 +내일 습도 | 더운 | "일기 예보" ** 아니', sort=1)
    c = newsUpdater(query='+오늘 +내일 습도 | 더운 | "일기 예보" ** 아니', sort=1)

    news_ = a.get_updated_news([])
    print("num_news", len(news_))
    print(news_[0:2], "\n")
