#!/bin/python3

import requests
from bs4 import BeautifulSoup
import re 
import sys
import os
import json
import datetime
from elasticsearch import Elasticsearch
import hashlib


def only_numerics(seq):
    seq_type= type(seq)
    return seq_type().join(filter(seq_type.isdigit, seq))

HEADERS = ({'User-Agent':
            'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36',
            'Accept-Language': 'en-US, en;q=0.5'})
page = requests.get("https://dreamcargiveaways.co.uk/current-competitions",headers=HEADERS)
soup = BeautifulSoup(page.content, 'html.parser')

t1=soup.find_all('li', {"class" : re.compile('product type-product post.*')} )

es = Elasticsearch([{'host': 'localhost', 'port': 9200}])

tt=datetime.datetime.now().isoformat()

for num in t1:
    link = [a['href'] for a in  num.find_all('a',    {"class" : re.compile('woocommerce-LoopProduct-link woocommerce-loop-product__link')}  )  ][0]
    #print(link)
    subpage = requests.get(link,headers=HEADERS)
    subsoup = BeautifulSoup(subpage.content, 'html.parser')
    t1=subsoup.find_all('div', {"class" : re.compile('competition-meta')} )[0]

    #print(t1)

    try:
        timed=only_numerics( t1.find_all('span', {"class" : re.compile('countdown-timer-d')} )[0].get_text() )
        timeh=only_numerics( t1.find_all('span', {"class" : re.compile('countdown-timer-h')} )[0].get_text() )
        timem=only_numerics( t1.find_all('span', {"class" : re.compile('countdown-timer-i')} )[0].get_text() )
        times=only_numerics( t1.find_all('span', {"class" : re.compile('countdown-timer-s')} )[0].get_text() )
        try:
            tickets= t1.find_all('span', {"class" : re.compile('ticket-counter-label wc-comps-tickets-sold')} )[0].get_text() 
            #print(tickets)
            x = re.search('(\d+)\/(\d+)', tickets )
            ticketssold=x.group(1)
            ticketstotal=x.group(2)
        except:
            ticketssold=-1
            ticketstotal=-1

        price=  t1.find_all('span', {"class" : re.compile('woocommerce-Price-amount amount')} )[0].get_text()[1:]
        label=  t1.find_all('label', {"class" : re.compile('sr-only')} )[0].get_text() 
        label = os.linesep.join([s for s in label.splitlines() if s]).lstrip()
        x = {
        "label": label,
        "timeleft":    int(timed)*60*60*24  +    int(timeh)*60*60 +     int(timem)*60 + int(times)  ,
        "ticketstotal": int(ticketstotal),
        "ticketssold": int(ticketssold),
        "tickerprice": float(price),
        "link": link,
        "@timestamp": tt
        }
        y = json.dumps(x)
        print(y) 
        mdx=hashlib.md5(y.encode('utf-8')).hexdigest()
#        print(mdx)
        res = es.index(index="dreamcargiveaways", id=mdx, body=x)
        print(res['result'])
    except:
        xxx=0
#        print('-')

