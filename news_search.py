import requests
from bs4 import BeautifulSoup as bs
from datetime import datetime, timedelta
from urllib import parse


class newsUpdater:
    def __init__(self, query: str, sort: int):
        """
        query : should be encoded
        sort : 0 - related, 1 - recent
        qdt : 0- general search, 1 - detail search enabled
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
        try:
            news_links = search_result.select(".bx > .news_wrap > a")
            return news_links

        except AttributeError:
            return []

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
        links = self._get_news()

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

        return new_links


if __name__ == "__main__":
    import time

    a = newsUpdater(query="오뚜기 +진라면", sort=1)
    news_ = a.get_updated_news([])
    # print(news_)

    for line in news_:
        print(line)

    time.sleep(1)
    newer = a.get_updated_news(news_)

    for line in newer:
        print(line)
