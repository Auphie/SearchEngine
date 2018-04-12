import task_contentDetl
import re
import json
import requests
import random
from fake_useragent import UserAgent
from bs4 import BeautifulSoup

def random_header(url):
    ua = UserAgent()
    random_header = json.loads(r'''{
    "Cache-Control": "max-age=0",
    "Connection": "keep-alive",
    "Host": "www.dogforum.com",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent":"%s"
    }'''%ua.random)
    random_header["Referer"] = url
    return random_header

board_name = 'dog-performance-sports'
total_page = 3

for page in range(1, total_page + 1):
    url = "http://www.dogforum.com/{}/{}/".format(board_name, page)
    resp = requests.get(url, headers=random_header(url))
    soup = BeautifulSoup(resp.text, 'lxml')
    for num in range(0,len(soup.findAll("a", id=re.compile("^thread_title_")))):
        try:
            title_url = soup.findAll("a", id=re.compile("^thread_title_"))[num]['href']
            title = soup.findAll("a", id=re.compile("^thread_title_"))[num].text
        except IndexError:
            break
        task_contentDetl.url_filter.delay(board_name, title_url, title)
