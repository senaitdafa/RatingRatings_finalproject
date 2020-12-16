import json
import requests
import urllib
import sqlite3
import os
from urllib.parse import quote
from bs4 import BeautifulSoup
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
###############################################################################
# YELP
###############################################################################

# Yelp constants
YELP_API_KEY= "VkEEqfy2J6ZQswh9VscCaOEjgPh0PZfSmn0WGf3IHI9UeCpEINpO_BRKXW0tbUhQ6dt76E1LysXiYOmcrrTbNubn77fzWhkJL0M9r3aIPwMD2_wD8MgIz_xLwlPMX3Yx"
API_HOST = 'https://api.yelp.com'
SEARCH_PATH = '/v3/businesses/search'
BUSINESS_PATH = '/v3/businesses/'
DEFAULT_LOCATION = 'Ann Arbor, MI'

# Request in specific format for Yelp
def request(host, path, api_key, url_params=None):
    url_params = url_params or {}
    url = '{0}{1}'.format(host, quote(path.encode('utf8')))
    headers = {
        'Authorization': 'Bearer %s' % api_key,
    }
    
    response = requests.request('GET', url, headers=headers, params=url_params)
    return response.json()

# Returns search results from Yelp, general searches
def searchYelp(api_key, term, searchLim):
    url_params = {
        'term': term.replace(' ', '+'),
        'location': DEFAULT_LOCATION,
        'limit': searchLim
    }
    return request(API_HOST, SEARCH_PATH, api_key, url_params=url_params)

# Get data for specific restaurants using the id
def getBusinessYelp(api_key, business_id):
    business_path = BUSINESS_PATH + business_id
    return request(API_HOST, business_path, api_key)

# Get and store ids
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

# Get the important data from each restaurant using the id
def getRestoInfoYelp(cur, conn, ids):
    count = 0
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
        cur.execute("SELECT * FROM yelpIds")
        prev = cur.fetchall()
        isUnique = True
        query = "INSERT INTO Yelp VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s')"%(name, rating, open, delivery, takeout, restoType, price)
        cur.execute(query)
        conn.commit()
        # Make sure only 25 are called at a time using a count
        count += 1
        if count == 25:
            return count
    # If less than 25 are left, simply end
    return count

# Uses search functions to get name and id
def getNameIdYelp(toSearch, amount):
    data = {}
    dataSet = searchYelp(YELP_API_KEY, toSearch, amount)
    for item in dataSet['businesses']:
        data[item['name']] = item['id']
    return data

def yelp(cur, conn):
    # Set of restaurants used across 3 platforms to compare
    ids = {'Sava’s': 'Fv2VLzVj9ATLcTbFehTDjg', 'Jolly Pumpkin': 'ZJVhCAjBeRlzLhgRVVJD5Q', 'Slurping Turtle': '6yjTZfR3dxb77XoFKT8U1w', 'Miss Kim’s': '6nLwTxr6P5vIU_lZBAzeOw', 'Zingerman’s Roadhouse': 'fQ8c9S6jitKS5RT6S-ziGA', 'Chop House': 'YW8P3qfoLuGGZmHhTG1sgg', 'Weber’s Restaurant': 'tE_oCseh9BIe39AcZzOUEg', 'Mani Osteria': '4REtzXpQYy8dVev8RjWbSQ', 'Isalita': 'GPzt1fncpK_Foi_DBYlYBg', 'Aventura': 'yNIYH9041m1JEyRS-N_LNw', 'Blue Nile': 'yLx8vO015iMCbxsI045Vkw'}
    # Get results of different sources, cap at 25
    dataDinn = getNameIdYelp("dinner", 25)
    dataBar = getNameIdYelp("bar", 25)
    dataBreak = getNameIdYelp("breakfast", 25)
    dataFast = getNameIdYelp("fast food", 25)
    dataCof = getNameIdYelp("coffee", 25)

    # Get ids for all datapoints to use
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
    
    # Get data points and put into table
    cur.execute("CREATE TABLE if NOT EXISTS Yelp (name VARCHARS, rating VARCHARS, open BOOLEAN, delivery BOOLEAN, takeout BOOLEAN, type LIST, price VARCHARS)")
    cur.execute("DELETE FROM Yelp")
    cur.execute("SELECT * FROM yelpIds")
    # Break into groups of 25 in getRestoInfoYelp, make sure it goes through
    # all data by collecting the length of yelpIds, run until count is that length
    max = len(cur.fetchall())
    count = 0
    while count < max:
        count += getRestoInfoYelp(cur, conn, ids[count:])


###############################################################################
# GOOGLE
###############################################################################

###############################################################################
# TRIP ADVISOR
###############################################################################

def mine_data(cur, conn, link):
    #Fetching name data
    try:
        resp = requests.get(link)
        soup = BeautifulSoup(resp.content, 'lxml')
    except:
        print("timed out")
        return False

        #retreive Restaurant name
    try:
        name = soup.find('h1', class_="_3a1XQ88S").text.strip()
    except:
        name = "retreieve error"
        #retrieve Price Range:
    try:
        price = soup.find('a', class_="_2mn01bsa").string
    except:
        price = ""

        # detrieve isOpen, defaults to Closed if no information is provided
    try:
        o_str = soup.find('span', class_= "_2ttkbuua").text.strip()
        if (o_str[0] == 'O'):  # meaning Open Now
            is_open = True
        else:
            is_open = False
    except:
        is_open = False

        #retrieve rating
    try:
        rating = soup.find('span', class_="r2Cf69qf").text.strip()
    except:
        rating = "na"
        #retrieve type, sometimes empty
    try:
        type_list = soup.find_all('a', class_= "_2mn01bsa")
        r_type = type_list[1].text.strip()
    except:
        r_type = ""
        #it will only execute if the primary key(name) is not in data base
    try:
        cur.execute("INSERT OR IGNORE INTO TripAdvisor (name, rating, isOpen, type, price) VALUES (?,?,?,?,?)", (name,rating,is_open,r_type,price))
        conn.commit()
        return True
    except:
        return False
def create_links(search_link):
    base_url = "https://www.tripadvisor.com"
    resp = requests.get(search_link)
    soup = BeautifulSoup(resp.content, 'html.parser')
    tags = soup.find_all('a', class_="_15_ydu6b")
    results = []
    for tag in tags:
        s= tag.get('href', None)
        results.append(base_url+s)  
    return results
def update_db(conn, cur):
    #Search pages in order: Local(Ann Arbor), Fast Food (Ann Arbor),
    # Mid-Range(Ann Arbor)
    search_pages= ["https://www.tripadvisor.com/Restaurants-g29556-zft10613-Ann_Arbor_Michigan.html",
    "https://www.tripadvisor.com/Restaurants-g29556-c10646-Ann_Arbor_Michigan.html",
    "https://www.tripadvisor.com/Restaurants-g29556-Ann_Arbor_Michigan.html"]
    "https://www.tripadvisor.com/Restaurants-g42139-Detroit_Michigan.html"
    "https://www.tripadvisor.com/Restaurants-g42256-Grand_Rapids_Kent_County_Michigan.html"
    links = []
    for page in search_pages:
        for x in create_links(page):
            links.append(x)
    count = 0
    for link in links:
        worked = mine_data(cur, conn, link)
        if worked == True:
            count += 1
            if count >=25:
                exit()
    
def tripadvisor(cur,conn):
    update_db(conn,cur)
###############################################################################
# ZOMATO
###############################################################################

# Zomato constants to use for every call
HEADER = {"User-agent": "curl/7.43.0", "Accept": "application/json", "user_key": "1e91fb3c6392d47f99cc42d3e9144e32"}
ANN_ARBOR_KEY = "118000"

# Get url for Zomato, count to keep under 25 calls
def getURLZomato(search, count):
    url = "https://developers.zomato.com/api/v2.1/search?entity_id=285&entity_type=city&q=" + search + "&count=" + str(count)
    return url

# Uses getURLZomato to get search results. Count built into getURLZomato.
def searchZomato(url):
    req = requests.get(url, headers = HEADER)
    r = json.loads(req.text)
    return r

# Get results for a specific restaurant using the restaurant id
def searchIndivZomato(resId):
    url = "https://developers.zomato.com/api/v2.1/restaurant?res_id=" + str(resId)
    req = requests.get(url, headers = HEADER)
    r = json.loads(req.text)
    return r

# Get ids and store them in a table
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

# Get the important data for each restaurant
def getDataZomato(cur, conn, data):
    idDict = {}
    count = 0
    for resto in data:
        idDict[resto[0]] = resto[1]
    for resto in idDict:
        rest = searchIndivZomato(idDict[resto])
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
        # Make sure only 25 are called at a time using a count
        count += 1
        if count == 25:
            return count
    # If less than 25 are left, simply end
    return count
    

def zomato(cur, conn):
    cur.execute("CREATE TABLE if NOT EXISTS ZomatoIds (name VARCHARS, id VARCHARS)")
    cur.execute("DELETE FROM ZomatoIds")
    cur.execute("CREATE TABLE if NOT EXISTS Zomato (name VARCHARS, rating VARCHARS, open BOOLEAN, delivery BOOLEAN, takeout BOOLEAN, type LIST, price VARCHARS)")
    cur.execute("DELETE FROM Zomato")
    
    # Set of restaurants used across platforms to compare
    restos = ['Sava’s', 'Jolly Pumpkin', 'Slurping Turtle', 'Miss Kim’s', 'Zingerman’s Roadhouse', 'Chop House', 'Weber’s Restaurant', 'Mani Osteria', 'Isalita', 'Aventura', 'Blue Nile']
    for name in restos:
        getIdsZomato(cur, conn, name, 1)
    #getDataZomato(cur, conn, idsList)
    # Get more data:
    getIdsZomato(cur, conn, "dinner", 25)
    getIdsZomato(cur, conn, "bar", 25)
    getIdsZomato(cur, conn, "breakfast", 25)
    getIdsZomato(cur, conn, "fast food", 25)
    getIdsZomato(cur, conn, "coffee", 25)
    cur.execute("SELECT * FROM ZomatoIds")
    allIds = cur.fetchall()
    # Break into groups of 25 in getRestoInfoYelp, make sure it goes through
    # all data by collecting the length of ZomatoIds, run until count is that length

    max = len(allIds)
    count = 0
    while count < max:
        count += getDataZomato(cur, conn, allIds[count:])

###############################################################################
# Calculations Functions
###############################################################################
def calculations(cur, conn):
    # Create an execute select from Yelp 
    aYelp = cur.execute("SELECT count(*) FROM Yelp WHERE price = ?",("$",)).fetchone()
    print(aYelp[0])
    bYelp = cur.execute("SELECT count(*) FROM Yelp WHERE price = ?",("$$",)).fetchone()
    print(bYelp[0])
    cYelp = cur.execute("SELECT count(*) FROM Yelp WHERE price = ?",("$$$",)).fetchone()
    print(cYelp[0])
    dYelp = cur.execute("SELECT count(*) FROM Yelp WHERE price = ?",("$$$$",)).fetchone()
    print(dYelp[0])

    # Create an execute select from Zomato
    aZom = cur.execute("SELECT count(*) FROM Zomato WHERE price = ?",("$",)).fetchone()
    print(aZom[0])
    bZom = cur.execute("SELECT count(*) FROM Zomato WHERE price = ?",("$$",)).fetchone()
    print(bZom[0])
    cZom = cur.execute("SELECT count(*) FROM Zomato WHERE price = ?",("$$$",)).fetchone()
    print(cZom[0])
    dZom = cur.execute("SELECT count(*) FROM Zomato WHERE price = ?",("$$$$",)).fetchone()
    print(dZom[0])
    
    # (8 calculations) The number of resaurants with one dolar sign devided by the total numnber of restaruants in the table 
    totalYelp = cur.execute("SELECT count(*) FROM Yelp").fetchone()
    print(totalYelp[0])
    totalZom = cur.execute("SELECT count(*) FROM Zomato").fetchone()
    print(totalZom[0])
    #Calcultions
    

#Output into the file
    f = open("calculationsfile.txt", "w")
    f.write(str(aYelp[0] / totalYelp[0])+"\n")
    f.write(str(bYelp[0] / totalYelp[0])+"\n")
    f.write(str(cYelp[0] / totalYelp[0])+"\n")
    f.write(str(dYelp[0] / totalYelp[0])+"\n")

    f.write(str(aZom[0] / totalZom[0])+"\n")
    f.write(str(bZom[0] / totalZom[0])+"\n")
    f.write(str(cZom[0] / totalZom[0])+"\n")
    f.write(str(dZom[0] / totalZom[0])+"\n")
    f.close()
#calculate numerical average ratings from Yelp and Trip Advisor
def get_rating_numerical(cur, conn):
    cur.execute("Select TripAdvisor.name, TripAdvisor.rating, Yelp.rating FROM TripAdvisor JOIN Yelp  WHERE TripAdvisor.name = Yelp.name ")
    names = []
    TA_vals=[]
    Yelp_vals= []
    for x in cur.fetchall():
        names.append(x[0])
        TA_vals.append(float(x[1]))
        if x[2] != "":
            Yelp_vals.append(float(x[2]))
    #plot matlab
    fig, ax = plt.subplots()
    n = len(names)
    x = np.arange(n)
    width = .35

    p1 = ax.bar(x, TA_vals, width, color = 'blue')
    p2 = ax.bar(x+width, Yelp_vals, width, color = 'green')

    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation = 40)

    ax.autoscale_view()
    ax.legend((p1[0],p2[0]), ('Trip Advisor', 'Yelp'))
    ax.set_xlabel('Restaurant Name')
    ax.set_ylabel('Average Rating')
    ax.set_title('Average Rating Per Restaurant Per Webpage')
    ax.grid()
    fig.savefig("Average Rating (Numerical)")
    plt.show()

def makePieChart(labels, sizes, name):
    fig1, ax1 = plt.subplots()
    ax1.pie(sizes, labels=labels, autopct='%1.1f%%',
            shadow=True, startangle=90)
    ax1.axis('equal')
    plt.title(name)
    plt.savefig(name)
    plt.show()

#what percent are 5, 4, 3, 2, 1 

def get_TA_pie(cur, conn):
    names = ["5.0", "4.5", "4.0", "3.5", "<3.5"]
    ratings = []
    fives = 0
    fourfive = 0
    four = 0
    threefive = 0
    three = 0
    cur.execute("SELECT rating FROM TripAdvisor")
    data = cur.fetchall()
    for rate in data:
        ratings.append(rate[0])
    fives = ratings.count('5.0')
    fourfive = ratings.count('4.5')
    four = ratings.count('4.0')
    threefive = ratings.count('3.5')
    three = ratings.count('3.0')

    sizes = [fives, fourfive, four, threefive, three]
    makePieChart(names, sizes, "Average TripAdvisor Ratings")

    return sizes

def get_Yelp_pie(cur, conn):
    names = ["5.0", "4.5", "4.0", "3.5", "<3.5"]
    ratings = []
    fives = 0
    fourfive = 0
    four = 0
    threefive = 0
    three = 0
    cur.execute("SELECT rating FROM Yelp")
    data = cur.fetchall()
    for rate in data:
        ratings.append(rate[0])
    fives = ratings.count('5.0')
    fourfive = ratings.count('4.5')
    four = ratings.count('4.0')
    threefive = ratings.count('3.5')
    three = ratings.count('3.0')

    sizes = [fives, fourfive, four, threefive, three]
    makePieChart(names, sizes, "Average Yelp Ratings")

    return sizes

def get_Zomato_pie(cur, conn):
    names = ["5.0", "4.5", "4.0", "3.5", "<3.5"]
    ratings = []
    fives = 0
    fourfive = 0
    four = 0
    threefive = 0
    three = 0
    cur.execute("SELECT rating FROM Zomato")
    data = cur.fetchall()
    for rate in data:
        ratings.append(rate[0])
    fives = ratings.count('5.0')
    fourfive = ratings.count('4.5')
    four = ratings.count('4.0')
    threefive = ratings.count('3.5')
    three = ratings.count('3.0')

    sizes = [fives, fourfive, four, threefive, three]
    makePieChart(names, sizes, "Average Zomato Ratings")

    return sizes

def totPercentages(set1, set2, set3):
    names = ["5.0", "4.5", "4.0", "3.5", "<3.5"]
    if len(set1) == 5 and len(set2) == 5 and len(set3) == 5:
        data = []
        percentages = []
        total = 0
        data.append(set1[0] + set2[0] + set3[0])
        data.append(set1[1] + set2[1] + set3[1])
        data.append(set1[2] + set2[2] + set3[2])
        data.append(set1[3] + set2[3] + set3[3])
        data.append(set1[4] + set2[4] + set3[4])
        for val in data:
            total += val
        for val in data:
            fraction = int((val / total) * 100)
            percentages.append(fraction)
        
        makePieChart(names, percentages, "Average Ratings Total")
    else:
        print("Error with size of data sets in totPercentages")
     
###############################################################################
# MAIN
###############################################################################

def setUpDatabase(db_name):
    path = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(path+'/'+db_name)
    conn.execute("PRAGMA foreign_keys = 1")
    cur = conn.cursor()
    return cur, conn

def main():
    
    cur, conn = setUpDatabase("ratings.db")
    
    # Create tables for each resource
    cur.execute("CREATE TABLE if NOT EXISTS Yelp (name VARCHARS, rating VARCHARS, open BOOLEAN, delivery BOOLEAN, takeout BOOLEAN, type LIST, price VARCHARS)")
    cur.execute("DELETE FROM Yelp")
    cur.execute("CREATE TABLE if NOT EXISTS TripAdvisor (name VARCHARS PRIMARY KEY UNIQUE, rating VARCHARS, isOpen BOOLEAN, type VARCHARS, price VARCHARS)")
    cur.execute("CREATE TABLE if NOT EXISTS Zomato (name VARCHARS, rating VARCHARS, open BOOLEAN, delivery BOOLEAN, takeout BOOLEAN, type LIST, price VARCHARS)")
    cur.execute("DELETE FROM Zomato")
    conn.commit()

    # Call each resource
    yelp(cur, conn)
    tripadvisor(cur,conn)
    get_rating_numerical(cur,conn)
    # OUT OF CALLS FOR ZOMATO!
    zomato(cur, conn)
 

    #Calculations
    yelpPercent = get_Yelp_pie(cur, conn)
    taPercent = get_TA_pie(cur, conn)
    zomPercent = get_Zomato_pie(cur, conn)
    totPercentages(yelpPercent, taPercent, zomPercent)
    calculations(cur, conn)



main()

