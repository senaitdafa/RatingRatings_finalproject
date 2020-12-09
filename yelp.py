# Gets data from yelp: Creates database with one table of restaurant id's and
# one table of the restaurant information collected over all three resources

import json
import requests
import urllib
import sqlite3
import os
from urllib.parse import quote
# FOR PYTHON 2: from urllib import quote

API_KEY= "VkEEqfy2J6ZQswh9VscCaOEjgPh0PZfSmn0WGf3IHI9UeCpEINpO_BRKXW0tbUhQ6dt76E1LysXiYOmcrrTbNubn77fzWhkJL0M9r3aIPwMD2_wD8MgIz_xLwlPMX3Yx"

# API constants
API_HOST = 'https://api.yelp.com'
SEARCH_PATH = '/v3/businesses/search'
BUSINESS_PATH = '/v3/businesses/'  # Business ID will come after slash.

# Hard codes
DEFAULT_LOCATION = 'Ann Arbor, MI'
SEARCH_LIMIT = 1

def request(host, path, api_key, url_params=None):
    url_params = url_params or {}
    url = '{0}{1}'.format(host, quote(path.encode('utf8')))
    headers = {
        'Authorization': 'Bearer %s' % api_key,
    }
    
    response = requests.request('GET', url, headers=headers, params=url_params)

    return response.json()


def search(api_key, term, searchLim):
    url_params = {
        'term': term.replace(' ', '+'),
        'location': DEFAULT_LOCATION,
        'limit': searchLim
    }
    return request(API_HOST, SEARCH_PATH, api_key, url_params=url_params)

def get_business(api_key, business_id):
    business_path = BUSINESS_PATH + business_id
    return request(API_HOST, business_path, api_key)

def setUpDatabase(db_name):
    path = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(path+'/'+db_name)
    cur = conn.cursor()
    return cur, conn

def makeIdTable(cur, conn, dict):
    cur.execute("SELECT * FROM ids")
    prev = cur.fetchall()
    isUnique = True
    for resto in dict:
        for place in prev:
            if place[1] == dict[resto]:
                isUnique = False
        if isUnique:
            name = resto.replace("'", "")
            do = "INSERT INTO ids VALUES ('%s', '%s')"%(name, dict[resto])
            cur.execute(do)
            conn.commit()
        isUnique = True

def getRestoInfo(cur, conn, ids):
    cur.execute("CREATE TABLE if NOT EXISTS restoInfo (name VARCHARS, rating VARCHARS, open BOOLEAN, delivery BOOLEAN, takeout BOOLEAN, type LIST, price VARCHARS)")
    cur.execute("DELETE FROM restoInfo")
    #Get name, rating, open, delivery, takeout, type, price
    for item in ids:
        name = item[0]
        data = get_business(API_KEY, item[1])
        #Get rating
        if 'rating' in data:
            rating = data['rating']
        else:
            rating = ''
        #Get open
        if data['is_closed'] == 'True':
            open = True
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
        query = "INSERT INTO restoInfo VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s')"%(name, rating, open, delivery, takeout, restoType, price)
        cur.execute(query)
        conn.commit()

def getNameId(toSearch, amount):
    data = {}
    dataSet = search(API_KEY, toSearch, amount)
    for item in dataSet['businesses']:
        data[item['name']] = item['id']
    return data


def main():
    # Set of restaurants used across 3 platforms to compare
    ids = {'Sava’s': 'Fv2VLzVj9ATLcTbFehTDjg', 'Jolly Pumpkin': 'ZJVhCAjBeRlzLhgRVVJD5Q', 'Slurping Turtle': '6yjTZfR3dxb77XoFKT8U1w', 'Miss Kim’s': '6nLwTxr6P5vIU_lZBAzeOw', 'Zingerman’s Roadhouse': 'fQ8c9S6jitKS5RT6S-ziGA', 'Chop House': 'YW8P3qfoLuGGZmHhTG1sgg', 'Weber’s Restaurant': 'tE_oCseh9BIe39AcZzOUEg', 'Mani Osteria': '4REtzXpQYy8dVev8RjWbSQ', 'Isalita': 'GPzt1fncpK_Foi_DBYlYBg', 'Aventura': 'yNIYH9041m1JEyRS-N_LNw', 'Blue Nile': 'yLx8vO015iMCbxsI045Vkw'}
    # Get results of different sources
    dataDinn = getNameId("dinner", 25)
    dataBar = getNameId("bar", 25)
    dataBreak = getNameId("breakfast", 25)
    dataFast = getNameId("fast food", 25)
    dataCof= getNameId("coffee", 25)
    
    cur, conn = setUpDatabase('yelp.db')
    cur.execute("CREATE TABLE if NOT EXISTS ids (name VARCHARS, id VARCHARS)")
    cur.execute("DELETE FROM ids")
    makeIdTable(cur, conn, ids)
    makeIdTable(cur, conn, dataDinn)
    makeIdTable(cur, conn, dataBar)
    makeIdTable(cur, conn, dataBreak)
    makeIdTable(cur, conn, dataFast)
    makeIdTable(cur, conn, dataCof)
    cur.execute("SELECT * FROM ids")
    ids = cur.fetchall()
    getRestoInfo(cur, conn, ids)


if __name__ == '__main__':
    main()
