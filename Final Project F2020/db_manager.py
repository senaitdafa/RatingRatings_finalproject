import os
import sqlite3

DATABASE = 'reviews.db'


def update_restaurant_table(cur, conn, info, index):
    """docstring"""

    # parse info
    name = info['name']
    avg_rating = float(info['rating']) # testing
    is_open = 'T' if info['business_status'] == 'OPERATIONAL' else 'F'
    delivery = 'T' if 'meal_delivery' in info['types'] else 'F'
    takeout = 'T' if 'meal_takeaway' in info['types'] else 'F'
    restaurant_type = 'unknown'
    avg_price = int(info['price_level'])

    # write to table
    cur.execute("INSERT INTO Restaurant (\
                    restautant_id, name, avg_rating, open,\
                    delivery, takeout, type, avg_price)\
                    VALUES (?,?,?,?,?,?,?,?)",
        (index, name, avg_rating, is_open, delivery, takeout, restaurant_type,
         avg_price))
    conn.commit()


def create_restaurant_table(cur, conn):
    """docstring"""
    cur.execute("DROP TABLE Restautant")
    cur.execute("CREATE TABLE Restaurant (\
                    restaurant_id INTEGER PRIMARY KEY,\
                    name TEXT,\
                    avg_rating REAL,\
                    open TEXT,\
                    delivery TEXT,\
                    takeout TEXT,\
                    type TEXT,\
                    avg_price INTEGER)")
    conn.commit()

def update_customer_table(cur, conn, review, index, restaurant_index):
    """docstring"""

   
    # parse info 
    name = review['author_name']
    time = review['time']
    text = review['text']
    rating = review['rating']

    # write to table
    cur.execute(
        "INSERT INTO Customer (\
            customer_id, name, restaurant_id, review_time, review, rating)\
            VALUES (?,?,?,?,?,?)",
        (index, name, restaurant_index, time, text, rating))
    conn.commit()
  

def create_customer_table(cur, conn):
    """docstring"""
    cur.execute("DROP TABLE IF EXISTS Customer")
    cur.execute("CREATE TABLE Customer (\
                    customer_id INTEGER PRIMARY KEY,\
                    name TEXT,\
                    restaurant_id INTEGER,\
                    review_time TEXT,\
                    review TEXT,\
                    rating TEXT\
                    )")
    conn.commit()

def create_database(db_name):
    """docstring"""
    path = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(path + '/' + db_name)
    cur = conn.cursor()
    return cur, conn 
