# -*- coding: UTF-8 -*-
import re
import json
import requests
import random
from fake_useragent import UserAgent
from celery import Celery
from bs4 import BeautifulSoup
from pymongo import MongoClient
from bson.objectid import ObjectId

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
def get_dog_detl(url):
    resp = requests.get(url, headers=random_header())
    soup = BeautifulSoup(resp.text, 'lxml')
    data = {}
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
    to_mongoDB(data)

@app.task
def to_mongoDB(data):
    conn = MongoClient('localhost', 27017)
    db = conn.dogs
    collection = db.dogDetail
    results = collection.insert(data)
    conn.close()