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
import rethinkdb as r
from pymongo import MongoClient
from bson.objectid import ObjectId

profile = {}

app = Celery('tasks', broker='pyamqp://celery:celery@localhost//')

@app.task
def random_header():
    ua = UserAgent()
    random_header = json.loads(r'''{
    "Cache-Control": "max-age=0",
    "Connection": "keep-alive",
    "Host": "www.dogforum.com",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent":"%s"
    }'''%ua.random)
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
def get_dog_list():
    url = 'http://www.dogforum.com/dogs/'
    resp = requests.get(url, headers=random_header())
    hrefs = [href for href in re.findall("""<a href="(http://www.dogforum.com/dogs/\S*/)">""", resp.text)]
    return hrefs

@app.task
def get_dog_detl(url):
    resp = requests.get(url, headers=random_header())
    soup = BeautifulSoup(resp.text, 'lxml')
    data = {}
    pack = {} 
    try:
        data['pet_name'] = soup.select_one('#name').text
    except (IndexError):
        data['pet_name'] = ""
    try:
        data['owner_url'] = soup.select('table')[13].select('td > a')[0]['href']
    except (IndexError):
        data['owner_url'] = ""
    try:
        data['owner_name'] = soup.select('table')[13].select('td > a')[0].text
    except (IndexError):
        data['owner_name'] = ""
    try:
        data['pet_name'] = soup.select('table')[13].select('#name')[0].text
    except (IndexError):
        data['pet_name'] = ""
    try:
        data['breed'] = re.findall("Breed</h3></td><td>(.{2,30})</td></tr>",str(soup.select('table')[13]))[0]
    except (IndexError):
        data['breed'] = ""
    try:
        data['gender'] = soup.select('table')[13].select('#gender')[0].text
    except (IndexError, KeyError):
        data['gender'] = ""
    try:
        data['age'] = re.findall(">Age</h3></td><td>(.{2,30})</td></tr>",str(soup.select('table')[13]))[0]
    except (IndexError, KeyError):
        data['age'] = ""
    try:
        data['food'] = soup.select('table')[13].select('#food')[0].text
    except (IndexError, KeyError):
        data['food'] = ""
    try:
        data['snacks'] = soup.select('table')[13].select('#snakes')[0].text
    except (IndexError, KeyError):
        data['snacks'] = ""
    try:
        data['toys'] = soup.select('table')[13].select('#toys')[0].text
    except (IndexError, KeyError):
        data['toys'] = ""
    try:
        data['activities'] = soup.select('table')[13].select('#activities')[0].text
    except (IndexError, KeyError):
        data['activities'] = ""
    for num in range(0,20):
        try:
            key = soup.select('table')[14].select('a')[num].text
            value = soup.select('table')[14].select('a')[num]['href']
            pack[key] = value
        except (AttributeError, IndexError, KeyError):
            continue
    try:
        pack.pop('')
        data['pack'] = pack
    except (IndexError, KeyError):
        data['pack'] = ""
    return data

@app.task
def collect_profile(url):
    try:
        profile = get_dog_detl(url)
        to_mongoDB.delay(profile)
    except AttributeError:
        continue

@app.task
def to_rethinkdb(profile):
    conn = r.connect()
    res = r.db('Dogforum').table('DogDetail').insert(profile).run(conn)
    conn.close()
    return res

@app.task
def to_mongoDB(profile):
    conn = MongoClient('localhost', 27017)
    db = conn.Dog
    collection = db.dogDetail
    results = collection.insert(profile)
    conn.close()
    return results

