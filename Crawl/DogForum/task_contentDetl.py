# -*- coding: UTF-8 -*-
import re
import json
import requests
import random
from datetime import datetime
from dateutil import parser
from fake_useragent import UserAgent
from celery import Celery
from bs4 import BeautifulSoup
import rethinkdb as r
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Celery('tasks', broker='pyamqp://celery:celery@localhost//')
set_url = []

@app.task
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

@app.task
def get_random_proxy():
    proxy_list = [
    '208.95.62.80:3128','61.219.36.120:80','203.177.78.62:8080','89.236.17.108:3128',
     '35.189.86.114:3128','185.93.3.123:8080','208.95.62.81:3128','35.198.12.92:80',
  '151.80.140.233:54566','185.82.212.95:8080','147.135.210.114:54566','196.22.51.90:80','61.220.26.97:80','159.203.181.50:3128','','','','','','',]
    
    proxy = random.choice(proxy_list)
    return proxy

@app.task
def url_filter(board_name, title_url, title):
    if title_url not in set_url:
        content_page_url(board_name, title_url, title)
        set_url.append(title_url)

@app.task
def content_page_url(board_name, title_url, title):
    resp = requests.get(title_url, headers = random_header(title_url))
    if not re.findall("Page 1 of (\d*)", resp.text):
        get_content(board_name, title_url, 1, title)
    else:
        get_content(board_name, title_url, 1, title)
        last_page = int(re.findall("Page 1 of (\d*)", resp.text)[0])
        for page in range(2, last_page+1):
            url2 = title_url+'page%s/'%page
            get_content(board_name, url2, page, title)

@app.task
def get_content(board_name, title_url, page, title):
    resp = requests.get(title_url, headers=random_header(title_url))
    resp.encoding = 'utf-8'
    soup = BeautifulSoup(resp.text, 'lxml')

    post = []
    
    for num in range(0,len(soup.select('.tborder.vbseo_like_postbit'))):
        block = {}
        block['board'] = board_name
        block['url'] = title_url
        block['page'] = int(page)
        block['title'] = title
        floor = soup.select('.tborder.vbseo_like_postbit')[num].findAll(id=re.compile("^postcount"))[0].get('name')
        block['floor'] = int(floor)
        block['author_url'] = soup.select('.tborder.vbseo_like_postbit')[num].select('a.bigusername')[0]['href']
        block['author_name'] = soup.select('.tborder.vbseo_like_postbit')[num].select('a.bigusername')[0].text

        dt = parser.parse(soup.select('.tborder.vbseo_like_postbit')[num].find('td').text.strip())
        block['post_date'] = dt.strftime("%Y-%m-%d %H:%M")
        block['post_stamp'] = int(dt.strftime("%Y%m%d%H%M"))
        
        author = {}
        try:
            author['member_type'] = soup.select('.tborder.vbseo_like_postbit')[num].select('div.smallfont')[0].text
        except IndexError:
            pass
        try:
            author['location'] = re.findall('Location: (.*).', soup.select('.tborder.vbseo_like_postbit')[num].text)[0].strip()
        except IndexError:
            pass
        try:
            author['join_date'] = re.findall('Join Date:(.*) Location', soup.select('.tborder.vbseo_like_postbit')[num].text)[0].strip()
        except IndexError:
            pass
        try:
            author['posts'] = int(re.findall('Posts: (.*)', soup.select('.tborder.vbseo_like_postbit')[num].text)[0].strip())
        except IndexError:
            pass
        try:
            author['mentioned'] = re.findall('Mentioned: (.*)Tag', soup.select('.tborder.vbseo_like_postbit')[num].text)[0].strip()
        except IndexError:
            pass
        try:
            author['tagged'] = re.findall('Tagged: (\d*)', soup.select('.tborder.vbseo_like_postbit')[num].text)[0].strip() + ' thread(s)'
        except IndexError:
            pass
        block['author_info'] = author
        block['_id'] = re.findall('http://www.dogforum.com/(.*)', title_url)[0].replace('/','.') + 'F%s'%floor
        block['id'] = re.findall('http://www.dogforum.com/(.*)', title_url)[0].replace('/','.') + 'F%s'%floor

        quotation = [y.text.strip() for y in soup.select('.tborder.vbseo_like_postbit')[num].findAll(id=re.compile("^post_message_"))[0].select('td.alt2')]
        block['quotation'] = quotation

        [div.extract() for div in soup.select('.tborder.vbseo_like_postbit')[num].find("div", id=re.compile("^post_message_")).select('div')]
        [quo.extract() for quo in soup.select('.tborder.vbseo_like_postbit')[num].findAll(id=re.compile("^post_message_"))[0].select('td.alt2')]
        a = soup.select('.tborder.vbseo_like_postbit')[num].find("div", id=re.compile("^post_message_")).text
        a.replace('Sent from my iPad using Tapatalk','').replace('Quote: ','[...quotation...]').replace("\r","").replace('\t','').replace("\n","").strip()
        block['content'] = a
        post.append(block)
        
    to_mongoDB(board_name.replace('-','_'), post)

@app.task
def to_rethinkdb(board_name, post):
    conn = r.connect()
    res = r.db('Dogforum').table(board_name).insert(post).run(conn)
    conn.close()

@app.task
def to_mongoDB(board_name, post):
    conn = MongoClient('localhost', 27017)
    db = conn.Dogforum
    collection = db[board_name]
    results = collection.insert_many(post)
    conn.close()
