import requests

API = 'https://maps.googleapis.com/maps/api/place/'
KEY = 'AIzaSyBc7m7A4hy1sASJFnQj8_vWoTaLhI3bx8U'
LOC = '42.2780,-83.7382' #umich coordinates 
RADIUS = '1500'


def get_restaurant_by_name(name):
    try:
        r = requests.get(
            f"{API}nearbysearch/json?key={KEY}&location={LOC}&radius={RADIUS}&name={name}"
        )
        #Place ID Details
        place_id = r.json()['results'][0]['place_id']
        r = requests.get(f"{API}details/json?key={KEY}&place_id={place_id}")
        info = r.json()['result']
    except:
        print("API request failed.")
        return{}
    else:
        return info

# #Place search
# name = 'savas'
# r1 = requests.get(f"{API}findplacefromtext/json?key={KEY}&location={LOC}&radius={RADIUS}name={name}")

# for result in r1.json()['result']:
#     print(result['name'])

# # soup = BeautifulSoup(r.json)

# #Place ID Details
# place_id = ''
# r2 = requests.get(f"{API}details/json?key={KEY}&place_id={place_id}")
# r2.json()['result']['reviews']

# Enable billing to get the API working
# Test API by getting a request
# In the Json look for place ID
# Then make a place details search, with a place ID thats obtained from the precious one 
