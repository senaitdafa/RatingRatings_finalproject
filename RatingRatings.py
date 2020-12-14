import json
import requests
import urllib
import sqlite3
import os
from urllib.parse import quote
from bs4 import BeautifulSoup
###############################################################################
# YELP
###############################################################################

YELP_API_KEY= "VkEEqfy2J6ZQswh9VscCaOEjgPh0PZfSmn0WGf3IHI9UeCpEINpO_BRKXW0tbUhQ6dt76E1LysXiYOmcrrTbNubn77fzWhkJL0M9r3aIPwMD2_wD8MgIz_xLwlPMX3Yx"
API_HOST = 'https://api.yelp.com'
SEARCH_PATH = '/v3/businesses/search'
BUSINESS_PATH = '/v3/businesses/'
DEFAULT_LOCATION = 'Ann Arbor, MI'

def request(host, path, api_key, url_params=None):
    url_params = url_params or {}
    url = '{0}{1}'.format(host, quote(path.encode('utf8')))
    headers = {
        'Authorization': 'Bearer %s' % api_key,
    }
    
    response = requests.request('GET', url, headers=headers, params=url_params)
    return response.json()

def searchYelp(api_key, term, searchLim):
    url_params = {
        'term': term.replace(' ', '+'),
        'location': DEFAULT_LOCATION,
        'limit': searchLim
    }
    return request(API_HOST, SEARCH_PATH, api_key, url_params=url_params)

def getBusinessYelp(api_key, business_id):
    business_path = BUSINESS_PATH + business_id
    return request(API_HOST, business_path, api_key)

def makeIdTableYelp(cur, conn, dict):
    cur.execute("SELECT * FROM yelpIds")
    prev = cur.fetchall()
    isUnique = True
    for resto in dict:
        for place in prev:
            if place[1] == dict[resto]:
                isUnique = False
        if isUnique:
            name = resto.replace("'", "")
            do = "INSERT INTO yelpIds VALUES ('%s', '%s')"%(name, dict[resto])
            cur.execute(do)
            conn.commit()
        isUnique = True

def getRestoInfoYelp(cur, conn, ids):
    cur.execute("CREATE TABLE if NOT EXISTS Yelp (name VARCHARS, rating VARCHARS, open BOOLEAN, delivery BOOLEAN, takeout BOOLEAN, type LIST, price VARCHARS)")
    cur.execute("DELETE FROM Yelp")
    #Get name, rating, open, delivery, takeout, type, price
    for item in ids:
        name = item[0]
        data = getBusinessYelp(YELP_API_KEY, item[1])
        #Get rating
        if 'rating' in data:
            rating = data['rating']
        else:
            rating = ''
        #Get open
        if 'is_closed' in data:
            if data['is_closed'] == 'True':
                open = True
            else:
                open = False
        else:
            open = False
        #Get delivery and Takeout
        if 'transactions' in data:
            if 'delivery' in data['transactions']:
                delivery = True
            else: delivery = False
            if 'pickup' in data['transactions']:
                takeout = True
            else: takeout = False
        else:
            delivery = False
            takeout = False
        #Get type
        types = ''
        restoType = ''
        if 'categories' in data:
            for type in data['categories']:
                types = types + " " + type['title']
            if 'Bars' in types:
                restoType = 'Bar'
            else:
                restoType = 'Dine in'
        #Get price
        if 'price' in data:
            price = data['price']
        else:
            price = ''
        query = "INSERT INTO Yelp VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s')"%(name, rating, open, delivery, takeout, restoType, price)
        cur.execute(query)
        conn.commit()

def getNameIdYelp(toSearch, amount):
    data = {}
    dataSet = searchYelp(YELP_API_KEY, toSearch, amount)
    for item in dataSet['businesses']:
        data[item['name']] = item['id']
    return data

def yelp(cur, conn):
    # Set of restaurants used across 3 platforms to compare
    ids = {'Sava’s': 'Fv2VLzVj9ATLcTbFehTDjg', 'Jolly Pumpkin': 'ZJVhCAjBeRlzLhgRVVJD5Q', 'Slurping Turtle': '6yjTZfR3dxb77XoFKT8U1w', 'Miss Kim’s': '6nLwTxr6P5vIU_lZBAzeOw', 'Zingerman’s Roadhouse': 'fQ8c9S6jitKS5RT6S-ziGA', 'Chop House': 'YW8P3qfoLuGGZmHhTG1sgg', 'Weber’s Restaurant': 'tE_oCseh9BIe39AcZzOUEg', 'Mani Osteria': '4REtzXpQYy8dVev8RjWbSQ', 'Isalita': 'GPzt1fncpK_Foi_DBYlYBg', 'Aventura': 'yNIYH9041m1JEyRS-N_LNw', 'Blue Nile': 'yLx8vO015iMCbxsI045Vkw'}
    # Get results of different sources
    dataDinn = getNameIdYelp("dinner", 25)
    dataBar = getNameIdYelp("bar", 25)
    dataBreak = getNameIdYelp("breakfast", 25)
    dataFast = getNameIdYelp("fast food", 25)
    dataCof = getNameIdYelp("coffee", 25)

    cur.execute("CREATE TABLE if NOT EXISTS yelpIds (name VARCHARS, id VARCHARS)")
    cur.execute("DELETE FROM yelpIds")
    makeIdTableYelp(cur, conn, ids)
    makeIdTableYelp(cur, conn, dataDinn)
    makeIdTableYelp(cur, conn, dataBar)
    makeIdTableYelp(cur, conn, dataBreak)
    makeIdTableYelp(cur, conn, dataFast)
    makeIdTableYelp(cur, conn, dataCof)
    cur.execute("SELECT * FROM yelpIds")
    ids = cur.fetchall()
    getRestoInfoYelp(cur, conn, ids)

###############################################################################
# GOOGLE
###############################################################################

###############################################################################
# TRIP ADVISOR
###############################################################################

###############################################################################
# ZOMATO
###############################################################################

HEADER = {"User-agent": "curl/7.43.0", "Accept": "application/json", "user_key": "1e91fb3c6392d47f99cc42d3e9144e32"}
ANN_ARBOR_KEY = "118000"

def getURLZomato(search, count):
    url = "https://developers.zomato.com/api/v2.1/search?entity_id=285&entity_type=city&q=" + search + "&count=" + str(count)
    return url

def searchZomato(url):
    req = requests.get(url, headers = HEADER)
    r = json.loads(req.text)
    return r

def searchIndivZomato(resId):
    url = "https://developers.zomato.com/api/v2.1/restaurant?res_id=" + str(resId)
    req = requests.get(url, headers = HEADER)
    r = json.loads(req.text)
    return r

def getIdsZomato(cur, conn, term, count):
    cur.execute("SELECT * FROM ZomatoIds")
    prev = cur.fetchall()
    isUnique = True
    url = getURLZomato(term, count)
    r = searchZomato(url)
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
            do = "INSERT INTO ZomatoIds VALUES ('%s', '%s')"%(rest, dict[rest])
            cur.execute(do)
            conn.commit()
        isUnique = True
    return id

def getDataZomato(cur, conn, data):
    dict = {}
    for id in data:
        rest = searchIndivZomato(data[id])
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
        query = "INSERT INTO Zomato VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s')"%(name, rating, open, delivery, takeout, type, price)
        cur.execute(query)
        conn.commit()

def zomato(cur, conn):
    cur.execute("CREATE TABLE if NOT EXISTS ZomatoIds (name VARCHARS, id VARCHARS)")
    cur.execute("DELETE FROM ZomatoIds")
    cur.execute("CREATE TABLE if NOT EXISTS Zomato (name VARCHARS, rating VARCHARS, open BOOLEAN, delivery BOOLEAN, takeout BOOLEAN, type LIST, price VARCHARS)")
    cur.execute("DELETE FROM Zomato")
    
    # Set of restaurants used across platforms to compare
    restos = ['Sava’s', 'Jolly Pumpkin', 'Slurping Turtle', 'Miss Kim’s', 'Zingerman’s Roadhouse', 'Chop House', 'Weber’s Restaurant', 'Mani Osteria', 'Isalita', 'Aventura', 'Blue Nile']
    idsList ={}
    for name in restos:
        idsList[name] = getIdsZomato(cur, conn, name, 1)
    getDataZomato(cur, conn, idsList)
    # Get more data:

    getIdsZomato(cur, conn, "dinner", 25)
    getIdsZomato(cur, conn, "bar", 25)
    getIdsZomato(cur, conn, "breakfast", 25)
    getIdsZomato(cur, conn, "fast food", 25)
    getIdsZomato(cur, conn, "coffee", 25)
    cur.execute("SELECT * FROM ZomatoIds")
    ids = cur.fetchall()
    idDict = {}
    for item in ids:
        idDict[item[0]] = item[1]
    getDataZomato(cur, conn, idDict)

###############################################################################
# MAIN
###############################################################################

def setUpDatabase(db_name):
    path = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(path+'/'+db_name)
    cur = conn.cursor()
    return cur, conn

def main():
    cur, conn = setUpDatabase("ratings.db")
    
    # Create tables for each resource
    cur.execute("CREATE TABLE if NOT EXISTS Yelp (name VARCHARS, rating VARCHARS, open BOOLEAN, delivery BOOLEAN, takeout BOOLEAN, type LIST, price VARCHARS)")
    cur.execute("DELETE FROM Yelp")
    cur.execute("CREATE TABLE if NOT EXISTS Google (name VARCHARS, rating VARCHARS, open BOOLEAN, delivery BOOLEAN, takeout BOOLEAN, type LIST, price VARCHARS)")
    cur.execute("DELETE FROM Google")
    cur.execute("CREATE TABLE if NOT EXISTS TripAdvisor (name VARCHARS, rating VARCHARS, open BOOLEAN, delivery BOOLEAN, takeout BOOLEAN, type LIST, price VARCHARS)")
    cur.execute("DELETE FROM TripAdvisor")
    cur.execute("CREATE TABLE if NOT EXISTS Zomato (name VARCHARS, rating VARCHARS, open BOOLEAN, delivery BOOLEAN, takeout BOOLEAN, type LIST, price VARCHARS)")
    # Ran out of calls for Zomato so saving data
    # cur.execute("DELETE FROM Zomato")
    conn.commit()

    # Call each resource
    yelp(cur, conn)
    # OUT OF CALLS FOR ZOMATO!
    # zomato(cur, conn)
    # google(cur, conn)
    # tripAdvisor(cur, conn)


main()
#yelp(cur, conn)

