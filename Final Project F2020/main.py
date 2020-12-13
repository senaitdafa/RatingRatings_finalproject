from db_manager import *
from google_code import get_restaurant_by_name
# from yelp import *
# from facebook import *

def main():
    '''docstring'''
    cur, conn = create_database(DATABASE)
    create_restaurant_table(cur, conn)
    create_customer_table(cur, conn)
    #"sava's"
    restaurants = ("Seva Restaurant", ) #we need 20 to get 100 customers
    rests = [("Seva Restaurant",),("Shake Shack",),("Slows Bar BQ"),("Stella's Lounge",),
("Sundance Grill & Bar",),("Supino Pizzeria",),("Taco King",),("Taqueria Mi Pueblo",),("Terra",),
("Texas de Brazil",),("The Apparatus Room",),("The Chop House",),
("The Earle Restaurant",),("The Green Well",),("The Kitchen By Wolfgang Puck",),("The Lunch Room",),
("The Old Goat",),("The Pit Stop",),("The West End Grill",),("The Winchester",),("Tomukun Korean Barbeque",),
("Vicente's Cuban Cuisine",),("Vinology Restaurant & Event Space",),("Weber's Restaurant",)]

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
    
    