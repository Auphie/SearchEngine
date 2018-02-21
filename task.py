# -*- coding: UTF-8 -*-
import re
import json
import datetime
import pytz
import requests
from celery import Celery
from bs4 import BeautifulSoup
import rethinkdb as r
from pymongo import MongoClient
from bson.objectid import ObjectId

profile = {}

app = Celery('tasks', broker='pyamqp://celery:celery@localhost//')
custom_headers = json.loads(r'''{
"Cookie":"trctestcookie=ok; bb_sessionhash=b94e3be6625814799942c9b1b1531485; bb_lastvisit=1517315818; bb_lastactivity=0; __utma=35414334.739693991.1517315820.1517315820.1517315820.1; __utmc=35414334; __utmz=35414334.1517315820.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); __utmt=1; __gads=ID=25c408c519cdba54:T=1517315820:S=ALNI_MY0NqJY1t862NnxeIexu648Tu-jhQ; bb_forum_view=723e91efa9356f6ee94f01eba06127c2ac4c9a19a-1-%7Bi-3_i-1517315862_%7D; trc_cookie_storage=taboola%2520global%253Auser-id%3D9fb09c65-d038-47cc-aca3-9186c0df7852-tuct1686a87; __utmb=35414334.80.4.1517316250219",
"Host":"www.dogforums.com",
"Pragma":"no-cache",
"Referer":"http://www.dogforums.com/",
"Upgrade-Insecure-Requests":"1",
"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.119 Safari/537.36"
}''')

@app.task
def get_tt_pages():
    url = 'http://www.dogforums.com/members/list/'
    resp = requests.get(url, headers=custom_headers)
    resp.encoding = 'utf-8'
    last_page = re.findall("Page 1 of (\d*)", resp.text)[0]
    return int(last_page)

@app.task
def get_member_list(num):
    url = 'http://www.dogforums.com/members/list/index{}.html'
    resp = requests.get(url.format(num), headers=custom_headers)
    resp.encoding = 'utf-8'

    hrefs = [href for href in re.findall("""<a href="(.*)" class="username">""", resp.text)]
    return hrefs

@app.task
def get_member_detl(url):
    resp = requests.get(url, headers=custom_headers)
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
            print(profile)
            to_rethinkdb.delay(profile)
  #          to_mongoDB.delay(profile)
        except AttributeError:
            continue

@app.task
def to_rethinkdb(profile):
    conn = r.connect()
    res = r.db('forums').table('dogforums').insert(profile).run(conn)
    conn.close()
    return res

"""
@app.task
def to_mongoDB(profile):
    conn = MongoClient('localhost', 27017)
    db = conn.dog
    collection = db.dogforums
    results = collection.insert_many(profile)
    connection.close()
    return results
"""