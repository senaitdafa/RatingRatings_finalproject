import sqlite3
import unittest
import os
from bs4 import BeautifulSoup, Comment
import requests
import re


def setUpDatabase(db_name):
    path = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(path+'/'+db_name)
    cur = conn.cursor()
    return cur, conn

def create_tables(cur,conn):
    cur.execute("CREATE TABLE if NOT EXISTS restaurant_data(name VARCHARS PRIMARY KEY, rating VARCHARS, isOpen BOOLEAN, type VARCHARS, price VARCHARS)")
    conn.commit()

def mine_data(cur, conn, links):
    #Fetching name data
    count = 0
    for link in links:
        if count > 25:
            break
        resp = requests.get(link)
        soup = BeautifulSoup(resp.content, 'lxml')
                
        #retreive Restaurant name
        name = soup.find('h1', class_="_3a1XQ88S").text.strip()

        #retrieve Price Range:
        price = soup.find('a', class_="_2mn01bsa").string  

        # detrieve isOpen, defaults to Closed if no information is provided
        try:
            o_str = soup.find('span', class_= "_2ttkbuua" ).text.strip()
            if (o_str[0] == 'O'): #meaning Open Now
                is_open = True
            else: 
                is_open = False
        except:
            is_open = False

        #retrieve rating
        rating = soup.find('span', class_= "r2Cf69qf").text.strip()

        #retrieve type, sometimes empty
        try:
            type_list = soup.find_all('a', class_ = "_2mn01bsa")
            r_type = type_list[1].text.strip()
        except:
            r_type = ""
        
        #it will only execute if the primary key(name) is not in data base
        try:
            cur.execute("INSERT INTO Restaurant_data (name, rating, isOpen, type, price) VALUES (?,?,?,?,?)",(name,rating,is_open,r_type,price))
            conn.commit()
            count += 1
        except:   
            continue

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
    # Mid-Range(Ann Arbor), Detroit, Grand Rapids
    search_pages= ["https://www.tripadvisor.com/Restaurants-g29556-zft10613-Ann_Arbor_Michigan.html",
    "https://www.tripadvisor.com/Restaurants-g29556-c10646-Ann_Arbor_Michigan.html",
    "https://www.tripadvisor.com/Restaurants-g29556-Ann_Arbor_Michigan.html",
    "https://www.tripadvisor.com/Restaurants-g42139-Detroit_Michigan.html",
    "https://www.tripadvisor.com/Restaurants-g42256-Grand_Rapids_Kent_County_Michigan.html"]

    for page in search_pages:
        mine_data(cur, conn, create_links(page))

def main():
    cur,conn = setUpDatabase('TripAdvisor.db')
    update_db(conn,cur)



if __name__ == '__main__':
    main()