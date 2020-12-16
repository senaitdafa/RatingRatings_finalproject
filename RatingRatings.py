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


# Get the important data from each restaurant using the id
def getRestoInfoYelp(cur, conn, data):
    count = 0
    #Get name, rating, open, delivery, takeout, type, price
    name = data['name']
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
            
    cur.execute("SELECT EXISTS (SELECT 1 FROM Yelp WHERE name = ?)",(name,))
    x = cur.fetchone()  
    if x[0] == 0:
        cur.execute("INSERT OR IGNORE INTO Yelp VALUES (?, ?, ?, ?, ?, ?, ?)",(name, rating, open, delivery, takeout, restoType, price))
        conn.commit()
        return True
    else:   
        return False    

def yelp(cur, conn):
    types = ["dinner", "bar", "breakfast", "fast food", "coffee"]
    count = 0
    for type in types:
        data = searchYelp(YELP_API_KEY, type, 25)
        for resto in data['businesses']:
            success = getRestoInfoYelp(cur, conn, resto)
            if success == True:
                count += 1
                if count >=25:
                    quit()
            else:
                continue
                

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
    cur.execute("SELECT EXISTS (SELECT 1 FROM TripAdvisor WHERE name = ?)",(name,))
    x = cur.fetchone()
    if x[0] == 0:
        cur.execute("INSERT OR IGNORE INTO TripAdvisor (name, rating, isOpen, type, price) VALUES (?,?,?,?,?)", (name,rating,is_open,r_type,price))
        populate_customer_reviews(cur, conn, soup)   
        conn.commit()
        return True
    else:
        return False

def populate_customer_reviews(cur, conn, soup):
    try:
        name = soup.find('h1', class_="_3a1XQ88S").text.strip()
    except:
        name = "retreieve error"
    
    reviews = soup.find_all('p', class_="partial_entry")
    for r in reviews:
        try:
            review = r.text.strip()
            cur.execute("INSERT OR IGNORE INTO CustReviews (name, review) VALUES (?,?)", (name,review))
            conn.commit()
        except:
            review = "This review contained no text or error"
            cur.execute("INSERT OR IGNORE INTO CustReviews (name, review) VALUES (?,?)", (name,review))
            conn.commit()
                

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
    "https://www.tripadvisor.com/Restaurants-g29556-c10646-Ann_Arbor_Michigan.html"]
    links = []
    for page in search_pages:
        for x in create_links(page):
            links.append(x)
    
    twenty_count = 0
    hundred_count = 0
    for link in links:
        worked = mine_data(cur, conn, link)
        if worked == True:
            twenty_count += 1
            hundred_count +=10
            if twenty_count >=2 and hundred_count < 100:
                quit()
        else:
            continue
    
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
def searchZomato(search, count):
    url = getURLZomato(search, count)
    req = requests.get(url, headers = HEADER)
    r = json.loads(req.text)
    return r

# Get the important data for each restaurant
def getDataZomato(cur, conn, jsonData):
    rest = jsonData['restaurant']
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
    
    
    cur.execute("SELECT EXISTS (SELECT 1 FROM Zomato WHERE name = ?)",(name,))
    x = cur.fetchone()  
    if x[0] == 0:
        cur.execute("INSERT OR IGNORE INTO Zomato VALUES (?, ?, ?, ?, ?,?, ?)",(name, rating, open, delivery, takeout, type, price))
        conn.commit()
        return True
    else:   
        return False

def zomato(cur, conn):
    types = ["dinner", "bar", "breakfast", "fast food", "coffee"]
    count = 0
    for type in types:
        data = searchZomato(type, 25)
        for resto in data['restaurants']:
            success = getDataZomato(cur, conn, resto)
            if success == True:
                count += 1
                if count >=25:
                    quit()
            else:
                continue
                

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
    f.write("Calculating the percent of restaurants in the Yelp and Zomato tables at each price level \n Yelp: \n")
    
    f.write("Level $" + str(aYelp[0] / totalYelp[0])+"%\n")
    f.write("Level $$" +str(bYelp[0] / totalYelp[0])+"%\n")
    f.write("Level $$$" +str(cYelp[0] / totalYelp[0])+"%\n")
    f.write("Level $$$$" +str(dYelp[0] / totalYelp[0])+"%\n")

    f.write("Level $" +str(aZom[0] / totalZom[0])+"%\n")
    f.write("Level $$" +str(bZom[0] / totalZom[0])+"%\n")
    f.write("Level $$$" +str(cZom[0] / totalZom[0])+"%\n")
    f.write("Level $$$$" +str(dZom[0] / totalZom[0])+"%\n")
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

def visualizations(cur, conn):
    yelpPercent = get_Yelp_pie(cur, conn)
    taPercent = get_TA_pie(cur, conn)
    zomPercent = get_Zomato_pie(cur, conn)
    totPercentages(yelpPercent, taPercent, zomPercent)
    calculations(cur, conn)
    get_rating_numerical(cur,conn)

def main():
    cur, conn = setUpDatabase("ratings.db")
    
    # Create tables for each resource
    
    cur.execute("CREATE TABLE if NOT EXISTS Yelp (name VARCHARS PRIMARY KEY UNIQUE, rating VARCHARS, open BOOLEAN, delivery BOOLEAN, takeout BOOLEAN, type LIST, price VARCHARS)")
    cur.execute("CREATE TABLE if NOT EXISTS TripAdvisor (name VARCHARS PRIMARY KEY UNIQUE, rating VARCHARS, isOpen BOOLEAN, type VARCHARS, price VARCHARS)")
    cur.execute("CREATE TABLE if NOT EXISTS Zomato (name VARCHARS PRIMARY KEY UNIQUE, rating VARCHARS, open BOOLEAN, delivery BOOLEAN, takeout BOOLEAN, type LIST, price VARCHARS)")
    cur.execute("CREATE TABLE if NOT EXISTS CustReviews(id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE, name VARCHAR, review VARCHAR, FOREIGN KEY(name) REFERENCES TripAdvisor(name))")

    conn.commit()
    
    # Call each resource
    yelp(cur, conn)
    tripadvisor(cur,conn)
    zomato(cur, conn)
 
    #Calculations
    visualizations(cur, conn)


main()

