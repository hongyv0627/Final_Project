#################################
##### Name: Hongyu Dai
##### Uniqname: hongyud
#################################

from bs4 import BeautifulSoup
import requests
import json
import secrets # file that contains your API key
import time
import sqlite3 


def open_cache(CACHE_FILENAME):
    ''' opens the cache file if it exists and loads the JSON into
    a dictionary, which it then returns.
    if the cache file doesn't exist, creates a new cache dictionary
    Parameters
    ----------
    None
    Returns
    -------
    The opened cache
    '''
    try:
        cache_file = open(CACHE_FILENAME, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict


def save_cache(cache_dict):
    ''' saves the current state of the cache to disk
    Parameters
    ----------
    cache_dict: dict
        The dictionary to save
    Returns
    -------
    None
    '''
    dumped_json_cache = json.dumps(cache_dict)
    fw = open(CACHE_FILENAME,"w")
    fw.write(dumped_json_cache)
    fw.close() 


def make_url_request_using_cache(url, cache, headers=None, yelp=False):
    if (url in cache.keys()): # the url is our unique key
        print("Using cache")
        return cache[url]
    else:
        print("Fetching")
        time.sleep(1)
        if yelp is True:
            response = requests.get(url, headers=headers)
        else:
            response = requests.get(url)
        cache[url] = response.text
        save_cache(cache)
        return cache[url]

CACHE_FILENAME = 'cache_Final.json'
CACHE_DICT = open_cache(CACHE_FILENAME)


#'User-Agent': 'UMSI 507 Course Final Project','From': 'hongyud@umich.edu','Course-Info': 'https://www.si.umich.edu/programs/courses/507',

class Restaurant:
    """
    a national site

    Instance Attributes
    -------------------
    category: string
        the category of a national site (e.g. 'National Park', '')
        some sites have blank category.

    name: string
        the name of a national site (e.g. 'Isle Royale')

    address: string
        the city and state of a national site (e.g. 'Houghton, MI')

    zipcode: string
        the zip-code of a national site (e.g. '49931', '82190-0168')

    phone: string
        the phone of a national site (e.g. '(616) 319-7906', '307-344-7381')
    """

    def __init__(self, name, street, city, state, zipcode, rating, review_count):
        self.name = name
        self.street = street
        self.city = city
        self.state = state
        self.zipcode = zipcode
        self.rating = rating
        self.review_count = review_count

    def full_address(self):
        return f"{self.street}, {self.city}, {self.state} {self.zipcode}"
    
    def info(self):
        return f"{self.street}, {self.city}, {self.state} {self.zipcode}: {self.rating} with {self.review_count}"

    def __eq__(self, other):
        if self.full_address() ==other.full_address() and self.name==other.name:
            return True
        else:
            return False



def build_fast_food_brand_list():
    """
    Make a list that contains the 50 biggest fast food brands from "https://www.qsrmagazine.com/reports/2020-qsr-50"

    Parameters
    ----------
    None

    Returns
    -------
    list
    """

    fast_food_brand_list = []
    main_page_url = 'https://www.qsrmagazine.com/reports/2020-qsr-50'
    url_text = make_url_request_using_cache(main_page_url,CACHE_DICT)

    soup = BeautifulSoup(url_text, 'html.parser')

    brand_list = soup.find_all('p',class_='chainame')
    for brand in brand_list:
        fast_food_brand_list.append(brand.text.strip().lower())
    
    return fast_food_brand_list


def get_restaurant_list_from_google(brand_name, location):
    
    key = secrets.GOOGLE_API_KEY
    converted_brand_name = brand_name.replace(" ","+")
    converted_location = location.replace(" ","+")
    google_api_url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={converted_brand_name}+in+{converted_location}&region=us&type=restaurant&key={key}"

    google_api_url_text = make_url_request_using_cache(google_api_url,CACHE_DICT)
    google_api_url_json = json.loads(google_api_url_text)

    google_instance_list = []
    while len(google_instance_list) <100: #maximum number of restaurants that we grab is 100
        if google_api_url_json['status'] =='ZERO_RESULTS':
            print(f"we cannot find any {brand_name} restaurants in {location}.") 
            break
        elif google_api_url_json['status'] =='OK':
            for restaurant in google_api_url_json['results']:
                name = restaurant.get('name',None)
                formatted_address = restaurant.get("formatted_address", None)
                rating = restaurant.get("rating", 0)
                review_count = restaurant.get("user_ratings_total", 0)
                try:
                    address = formatted_address.split(",")
                    street = address[0].strip()
                    city = address[1].strip()
                    state = address[2].strip().split(" ")[0]
                    zipcode = address[2].strip().split(" ")[1]
                    restaurant_class = Restaurant(name=name, street=street, city=city, state=state, zipcode=zipcode, rating=rating, review_count=review_count)
                    google_instance_list.append(restaurant_class)
                except IndexError: #in case if our instance of restaurants don't have formatted address
                    continue
            
            try: #If your search will return more than 20, then the search response will include an additional value — next_page_token.
                next_page_token = google_api_url_json['next_page_token']
            except KeyError or google_api_url_json['next_page_token']=="": #If the next_page_token is null, or is not returned, then there are no further results.
                break
            else: #Pass the value of the next_page_token to the pagetoken parameter of a new search to see the next set of results. 
                google_api_url_next_page = f'{google_api_url}&pagetoken={next_page_token}'
                google_api_url_text = make_url_request_using_cache(google_api_url_next_page,CACHE_DICT)
                google_api_url_json = json.loads(google_api_url_text)

    return google_instance_list
                


def get_corresponding_yelp_information(google_instance_list):

    

    yelp_instance_list = []
    yelp_key = secrets.YELP_API_KEY
    yelp_headers = {'User-Agent': 'UMSI 507 Course Final Project',
        'From': 'hongyud@umich.edu',
        'Course-Info': 'https://www.si.umich.edu/programs/courses/507',
        'Authorization': f'Bearer {yelp_key}'}
    
    for restaurant in google_instance_list: #for each restaurant in google, we search its yelp details
        if restaurant not in yelp_instance_list: #check if restaurant instance from google is in our list of instance from yelp, if not we search
            location = restaurant.full_address()
            term = restaurant.name
            yelp_api_url = f'https://api.yelp.com/v3/businesses/search?location={location}&term={term}'
            yelp_api_url_text = make_url_request_using_cache(yelp_api_url,CACHE_DICT,headers=yelp_headers,yelp=True)
            yelp_api_url_json = json.loads(yelp_api_url_text)
            
            for business in yelp_api_url_json['businesses']: #we will get more than 1 result of restaurants even though our input has only 1 restaurant
                name = business.get("name",None)
                street = business['location'].get("address1", None)
                city = business['location'].get("city", None)
                state = business['location'].get("state", None)
                zipcode = business['location'].get("zip_code", None)
                rating = business.get("rating", 0)
                review_count = business.get("review_count", 0)
                restaurant_class = Restaurant(name=name, street=street, city=city, state=state, zipcode=zipcode, rating=rating, review_count=review_count)
                if restaurant_class not in yelp_instance_list: #we may get repeated restaurant result each search, so we only append new restaurant result that is not in our list.
                    yelp_instance_list.append(restaurant_class)
                elif restaurant_class in yelp_instance_list:
                    continue
        elif restaurant in yelp_instance_list:#if restaurant instance from google is in our list of instance from yelp, we don't need to search its yelp details 
            continue

    return yelp_instance_list


def create_new_table(data_source,table_name,database_name):
    connection = sqlite3.connect(f"{database_name}.sqlite")
    cursor = connection.cursor()
    drop_table = f"""DROP TABLE IF EXISTS {table_name}"""
    
    create_table= f"""CREATE TABLE IF NOT EXISTS {table_name} (
        'ID' INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
        'Name' TEXT NOT NULL,
        'Street' TEXT NOT NULL,
        'City' TEXT NOT NULL,
        'State' TEXT NOT NULL,
        'Zipcode' TEXT NOT NULL,
        '{data_source}_rating' TEXT NOT NULL,
        '{data_source}_review_count' TEXT NOT NULL
        );
    """
    cursor.execute(drop_table)
    cursor.execute(create_table)
    connection.commit()
    connection.close()


def insert_new_value(object_list,table_name,database_name):
    connection = sqlite3.connect(f"{database_name}.sqlite")
    cursor = connection.cursor()
    insert_value = f"""INSERT INTO {table_name}
       VALUES(NULL,?,?,?,?,?,?,?)"""
    for restaurant in object_list:
        insert_list = [restaurant.name,restaurant.street,restaurant.city,restaurant.state,restaurant.zipcode,restaurant.rating,restaurant.review_count]
        cursor.execute(insert_value,insert_list)
    
    connection.commit()
    connection.close()
    
    
    
    
    
    

if __name__ == "__main__":

    
    x = get_restaurant_list_from_google("McDonald's", "Los Angeles")
    y = get_corresponding_yelp_information(x)
    create_new_table("Google", "Google_list", "Final_Project_database")
    insert_new_value(x, "Google_list", "Final_Project_database")
    create_new_table("Yelp", "Yelp_list", "Final_Project_database")
    insert_new_value(y, "Yelp_list", "Final_Project_database")
    
    '''
    for i in y:
        print(i.info())
    print("----------------")
    for j in x:
        print(j.info())
        '''