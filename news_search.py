import requests
from bs4 import BeautifulSoup as bs
from datetime import datetime, timedelta


class newsUpdater:
    def __init__(self, query: str, sort: int):
        self.query = query
        self.sort = int(sort)
        # self.url = f"https://m.search.naver.com/search.naver?where=m_news&sm=mtb_jum&query={query}"
        # self.url = f"https://m.search.naver.com/search.naver?where=m_news&ie=utf8&sm=mns_hty&query{query}"
        self.url = f"https://m.search.naver.com/search.naver?where=m_news&query={query}&sm=mtb_opt&sort={sort}"
        """
        https://m.search.naver.com/search.naver?where=m_news&query=삼성전자 +카카오&sm=mtb_opt&sort=1
        """

    def _get_news(self):
        result = requests.get(self.url)
        result_html = result.text
        soup = bs(result_html, "html.parser")

        search_result = soup.select_one("#news_result_list")
        news_links = search_result.select(".bx > .news_wrap > a")
        return news_links

    def remove_outdated_news(self, links: list, keeptime:int) -> None:
        now = datetime.now()
        outdated = timedelta(days=keeptime)
        only_up_to_date = [link for link in links if (now - datetime.strptime(link["added"], "%Y-%m-%d %H:%M:%S") < outdated)]
        time_passed = [now - datetime.strptime(link["added"], "%Y-%m-%d %H:%M:%S") for link in links]
        print(f"the oldest news: {max(time_passed)}")


        # print(f"only_up_to_date: {len(only_up_to_date)}")
        # print("outdated news were removed.")

        return only_up_to_date

    def get_updated_news(self, old_links: list):
        new_links = []
        links = self._get_news()

        # Handling the database based on the time newslinks were added
        now = datetime.now()
        old_urls = [old_link['link'] for old_link in old_links]

        for link in links:
            title = str(link.get_text()).strip()
            # Not appending the duplicated links: check based on the link
            if link["href"] not in old_urls:
                new_links.append({"title": title, "link": link["href"], "added": now.strftime(format="%Y-%m-%d %H:%M:%S")})

        # new_links = self._remove_outdated_news(new_links, now)

        return new_links




if __name__ == "__main__":
    import time
    a = newsUpdater(query="카카오 삼성전자", sort=1)
    news_ = a.get_updated_news([])
    # print(news_)

    
    for line in news_:
        print(line)

    time.sleep(10)
    newer = a.get_updated_news(news_)

    for line in newer:
        print(line)
