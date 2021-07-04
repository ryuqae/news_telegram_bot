import requests
from bs4 import BeautifulSoup as bs


class newsUpdater:
    def __init__(self, query):
        self.query = query
        self.timesleep = 3600
        self.url = f"https://m.search.naver.com/search.naver?where=m_news&sm=mtb_jum&query={query}"

    def _get_news(self):
        result = requests.get(self.url)
        result_html = result.text
        soup = bs(result_html, "html.parser")

        search_result = soup.select_one("#news_result_list")
        news_links = search_result.select(".bx > .news_wrap > a")
        return news_links

    def get_updated_news(self, old_links):
        # new_links = []
        # links = self._get_news()
        new_links = [link["href"] for link in self._get_news() if link not in old_links]
        return new_links


if __name__ == "__main__":
    a = newsUpdater(query="카카오")
    news_ = a.get_updated_news()
    newer = a.get_updated_news(news_[:-5])

    for line in newer:
        print(line.get_text(), line["href"])
