from db_manager import *
from google_code import get_restaurant_by_name
import urllib
# from yelp import *
# from facebook import *

def main():
    
    cur, conn = create_database(DATABASE)
    create_restaurant_table(cur, conn)
    create_customer_table(cur, conn)

    restaurants = ["sava's","The Chop House","The West End Grill", "Vinology", "Tomukun Korean Barbeque", 
    "The Lunch Room", "Palio's", "Taco King", "Weber's", "Slurping Turtle", 
     "Chela's", "Mani Osteria and Bar", "Isalita","Ashley's", "Jolly Pumpkin Cafe & Brewery", 
     "Krazy Jim's Blimpy Burger","El Harissa Market Cafe", "Gratzi Ann Arbor","Panchero's", "Blue Nile Restaurant" ]
   
    for restaurant in restaurants:
        print(restaurant)
        customer_count = 0
        for i, restaurant in enumerate(restaurants, 1):
            # from places API
            # TODO: what if API requests fails? 
            restaurant_info = get_restaurant_by_name(restaurant)
            update_restaurant_table(cur, conn, restaurant_info, i)

            reviews = restaurant_info.get('reviews', [])
            for review in reviews:
                customer_count += 1
                update_customer_table(cur, conn, review, customer_count, i)

        # get info from Yelp API
        # get info from Facebook API
        # calculate avg_price
        # update avg_price in info dictionary 

        conn.close()

    

if __name__ == '__main__':
    main()
    
    