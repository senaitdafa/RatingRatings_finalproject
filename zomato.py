import requests
from bs4 import BeautifulSoup
import json
import os
import sqlite3

HEADER = {"User-agent": "curl/7.43.0", "Accept": "application/json", "user_key": "1e91fb3c6392d47f99cc42d3e9144e32"}
ANN_ARBOR_KEY = "118000"

def getURL(search, count):
    url = "https://developers.zomato.com/api/v2.1/search?entity_id=285&entity_type=city&q=" + search + "&count=" + str(count)
    return url

def search(url):
    req = requests.get(url, headers = HEADER)
    r = json.loads(req.text)
    return r

def searchIndiv(resId):
    url = "https://developers.zomato.com/api/v2.1/restaurant?res_id=" + str(resId)
    req = requests.get(url, headers = HEADER)
    r = json.loads(req.text)
    return r

def getIds(cur, conn, term, count):
    cur.execute("SELECT * FROM ids")
    prev = cur.fetchall()
    isUnique = True
    url = getURL(term, count)
    r = search(url)
    dict = {}
    for rest in r['restaurants']:
        # Get ids and names
        id = rest['restaurant']['R']['res_id']
        name = rest['restaurant']['name'].replace("'", "")
        dict[name] = id
    for rest in dict:
        if rest in prev:
            isUnique = False
        if isUnique:
            do = "INSERT INTO ids VALUES ('%s', '%s')"%(rest, dict[rest])
            cur.execute(do)
            conn.commit()
        isUnique = True
    return id

def getData(cur, conn, data):
    dict = {}
    for id in data:
        rest = searchIndiv(data[id])
        # Get name, rating, open, delivery, takeout, type, price
        name = rest['name'].replace("'", "")
        rating = rest['user_rating']['aggregate_rating']
        if rating == 0:
            rating = "N/A"
        # Only returns open restaurants
        open = True
        deliveryNum = rest['has_online_delivery']
        # Get delivery / takeout
        delivery = False
        takeout = False
        if deliveryNum == 0:
            delivery = True
        if 'Takeaway Available' in rest['highlights']:
            takeout = True
        # Get type - DOUBLE CHECK WHERE BARS SHOWS UP
        if 'Bars' in rest['highlights']:
            type = 'Bar'
        else:
            type = 'Dine in'
        # Get price
        priceNum = rest['price_range']
        if priceNum == 1:
            price = '$'
        elif priceNum == 2:
            price = '$$'
        elif priceNum == 3:
            price = '$$$'
        elif priceNum == 4:
            price = '$$$$'
        else:
            price = "N/A"
        query = "INSERT INTO restoInfo VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s')"%(name, rating, open, delivery, takeout, type, price)
        cur.execute(query)
        conn.commit()

def setUpDatabase(db_name):
    path = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(path+'/'+db_name)
    cur = conn.cursor()
    return cur, conn

def main():
    cur, conn = setUpDatabase('zomato.db')
    cur.execute("CREATE TABLE if NOT EXISTS ids (name VARCHARS, id VARCHARS)")
    cur.execute("DELETE FROM ids")
    cur.execute("CREATE TABLE if NOT EXISTS restoInfo (name VARCHARS, rating VARCHARS, open BOOLEAN, delivery BOOLEAN, takeout BOOLEAN, type LIST, price VARCHARS)")
    cur.execute("DELETE FROM restoInfo")
    
    # Set of restaurants used across platforms to compare
    restos = ['Sava’s', 'Jolly Pumpkin', 'Slurping Turtle', 'Miss Kim’s', 'Zingerman’s Roadhouse', 'Chop House', 'Weber’s Restaurant', 'Mani Osteria', 'Isalita', 'Aventura', 'Blue Nile']
    idsList ={}
    for name in restos:
        idsList[name] = getIds(cur, conn, name, 1)
    getData(cur, conn, idsList)
    # Get more data:

    getIds(cur, conn, "dinner", 25)
    getIds(cur, conn, "bar", 25)
    getIds(cur, conn, "breakfast", 25)
    getIds(cur, conn, "fast food", 25)
    getIds(cur, conn, "coffee", 25)
    cur.execute("SELECT * FROM ids")
    ids = cur.fetchall()
    idDict = {}
    for item in ids:
        idDict[item[0]] = item[1]
    getData(cur, conn, idDict)

main()

