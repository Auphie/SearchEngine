# -*- coding: UTF-8 -*-
import re
import json
import requests
import random
import time
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
    time.sleep(0.2)
    resp = requests.get(title_url, headers=random_header(title_url))
    resp.encoding = 'utf-8'
    soup = BeautifulSoup(resp.text, 'lxml')

    post = []
    
    for num in range(0,len(soup.select('.tborder.vbseo_like_postbit'))):
        floor = soup.select('.tborder.vbseo_like_postbit')[num].findAll(id=re.compile("^postcount"))[0].get('name')
        article = {}
        article['_id'] = re.findall('http://www.dogforum.com/(.*)', title_url)[0].replace('/','.') + 'F%s'%floor
        article['id'] = re.findall('http://www.dogforum.com/(.*)', title_url)[0].replace('/','.') + 'F%s'%floor
        article['board'] = board_name
        article['title'] = title
        article['url'] = title_url.replace(''.join(c for c in re.findall("/(page.*)", title_url)),'')
        article['title_id'] = re.findall('http.*-(\d{1,7})/',title_url)[0]
        block = {}
        block['content_url'] = title_url
        block['page'] = int(page)
        block['floor'] = int(floor)
        block['author_url'] = soup.select('.tborder.vbseo_like_postbit')[num].select('a.bigusername')[0]['href']
        block['author_name'] = soup.select('.tborder.vbseo_like_postbit')[num].select('a.bigusername')[0].text
        try:
            dt = parser.parse(soup.select('.tborder.vbseo_like_postbit')[num].find('td').text.strip())
            block['post_date'] = dt.strftime("%Y-%m-%d %H:%M")
            block['post_stamp'] = int(dt.strftime("%Y%m%d%H%M"))
        except (ValueError):
            block['post_date'] = "2018-4-3 0:0"
            block['post_stamp'] = "201804030000"
        try:
            block['member_type'] = soup.select('.tborder.vbseo_like_postbit')[num].select('div.smallfont')[0].text
        except IndexError:
            pass
        try:
            block['location'] = re.findall('Location: (.*).', soup.select('.tborder.vbseo_like_postbit')[num].text)[0].strip()
        except IndexError:
            pass
        try:
            block['join_date'] = re.findall('Join Date:(.*) Location', soup.select('.tborder.vbseo_like_postbit')[num].text)[0].strip()
        except IndexError:
            pass
        try:
            block['posts'] = re.findall('Posts: (.*)', soup.select('.tborder.vbseo_like_postbit')[num].text)[0].strip()
        except IndexError:
            pass
        try:
            block['mentioned'] = re.findall('Mentioned: (.*)Tag', soup.select('.tborder.vbseo_like_postbit')[num].text)[0].strip()
        except IndexError:
            pass
        try:
            block['tagged'] = re.findall('Tagged: (\d*)', soup.select('.tborder.vbseo_like_postbit')[num].text)[0].strip() + ' thread(s)'
        except IndexError:
            pass

        quotation = [y.text.strip() for y in soup.select('.tborder.vbseo_like_postbit')[num].findAll(id=re.compile("^post_message_"))[0].select('td.alt2')]
        block['quotation'] = quotation

        [div.extract() for div in soup.select('.tborder.vbseo_like_postbit')[num].find("div", id=re.compile("^post_message_")).select('div')]
        [quo.extract() for quo in soup.select('.tborder.vbseo_like_postbit')[num].findAll(id=re.compile("^post_message_"))[0].select('td.alt2')]
        a = soup.select('.tborder.vbseo_like_postbit')[num].find("div", id=re.compile("^post_message_")).text
        a.replace('Sent from my iPad using Tapatalk','').replace('Quote: ','[...quotation...]').replace("\r","").replace('\t','').replace("\n","").strip()
        block['content'] = a
        
        article['threads'] = block
        post.append(article.copy())

    to_mongoDB(post)
    to_rethinkdb(post)

@app.task
def to_rethinkdb(post):
    conn = r.connect()
    res = r.db('forum').table('thread').insert(post).run(conn)
    conn.close()

@app.task
def to_mongoDB(post):
    conn = MongoClient('localhost', 27017)
    db = conn.forum
    collection = db.thread
    results = collection.insert_many(post)
    conn.close()
