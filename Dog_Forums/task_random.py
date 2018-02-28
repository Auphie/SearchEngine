# -*- coding: UTF-8 -*-
import re
import json
import pytz
import time
import requests
import random
from fake_useragent import UserAgent
from celery import Celery
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import rethinkdb as r
from pymongo import MongoClient
from bson.objectid import ObjectId

profile = {}

app = Celery('tasks', broker='pyamqp://celery:celery@localhost//')

@app.task
def random_header():
    ua = UserAgent()
    random_header = json.loads(r'''{
    "Host":"www.dogforums.com",
    "Pragma":"no-cache",
    "Referer":"http://www.dogforums.com/",
    "Upgrade-Insecure-Requests":"1",
    "User-Agent":"%s"
    }'''%ua.random)
    return random_header

@app.task
def get_random_proxy():
    proxy_list = [
     '208.95.62.80:3128','61.219.36.120:80','203.177.78.62:8080','89.236.17.108:3128',
     '35.189.86.114:3128','185.93.3.123:8080','208.95.62.81:3128','35.198.12.92:80',
     '151.80.140.233:54566','185.82.212.95:8080','147.135.210.114:54566','196.22.51.90:80',
     '61.220.26.97:80','159.203.181.50:3128','','','','','','',]
    
    proxy = random.choice(proxy_list)
    return proxy

@app.task
def get_tt_pages():
    url = 'http://www.dogforums.com/members/list/'
    resp = requests.get(url, headers=random_header())
    resp.encoding = 'utf-8'
    last_page = re.findall("Page 1 of (\d*)", resp.text)[0]
    return int(last_page)

@app.task
def get_member_list(num):
    url = 'http://www.dogforums.com/members/list/index{}.html'
    resp = requests.get(url.format(num), headers=random_header())
    resp.encoding = 'utf-8'

    hrefs = [href for href in re.findall("""<a href="(.*)" class="username">""", resp.text)]
    return hrefs

@app.task
def get_member_detl(url):
   # time.sleep(1)
    resp = requests.get(url, headers=random_header())
    resp.encoding = 'utf-8'
    soup = BeautifulSoup(resp.text, 'lxml')

    def get_signiture():
        if 'Signature' in soup.text.split():
            signature = soup.select('div.subsection')[1].text.strip()
        else:
            signature = ""
        return signature
    
    data = {}
    data['member_name'] = soup.select_one('span.subsectiontitle').text.replace('About ','')
    data['url'] = url
    data['signiture'] = get_signiture()
    for i in range(0,20):
        try:
            key = soup.select('dl.stats')[i].select_one('dt').text
            value = soup.select('dl.stats')[i].select_one('dd').text
            data[key] = value
        except IndexError:
            break
            
    return data

@app.task
def collect_profile(page):
    for url in get_member_list(page):
        try:
            profile = get_member_detl(url)
    #        print(profile)
            to_rethinkdb.delay(profile)
            to_mongoDB(profile)
        except AttributeError:
            continue

@app.task
def to_rethinkdb(profile):
    conn = r.connect()
    res = r.db('Dogforums').table('Member').insert(profile).run(conn)
    conn.close()
    return res

@app.task
def to_mongoDB(profile):
    conn = MongoClient('localhost', 27017)
    db = conn.Dogforums
    collection = db.Member
    results = collection.insert(profile)
    conn.close()
    return results
