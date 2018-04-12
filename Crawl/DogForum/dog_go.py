import task_dog
import json
import re
import requests
from bs4 import BeautifulSoup

header = json.loads(r'''{
    "Cache-Control": "max-age=0",
    "Connection": "keep-alive",
    "Host": "www.dogforum.com",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36"
    }''')

url = 'http://www.dogforum.com/dogs/'
resp = requests.get(url, headers=header)
hrefs = [href for href in re.findall("""<a href="(http://www.dogforum.com/dogs/\S*/)">""", resp.text)]
for url in hrefs:
    task_dog.get_dog_detl.delay(url)