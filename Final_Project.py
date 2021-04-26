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
import plotly
import plotly.graph_objects as go

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
    '''Check the cache for a saved result for the url. If the result is 
    found, return it. Otherwise send a new request, save it, then return it.
    Parameters
    ----------
    url: string
        The URL for the API endpoint

    cache: dict
        The dictionary to save

    headers (optional): strings
        the headers string which is necessary when we request Yelp API

    yelp: bool
        boolean value deciding if we request Yelp API or not
    
    Returns
    -------
    string
        the results of the query as a Python object loaded from JSON
    '''
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
    a restaurant instance

    Instance Attributes
    -------------------
    name: string
        the name of a fast food restaurant (e.g. 'McDonald's')

    street: string
         the street of a fast food restaurant (e.g. '201 W Washington Blvd')

    city: string
        the city of a fast food restaurant (e.g. 'Los Angeles')

    state: string
        the state of a fast food restaurant (e.g. 'CA')

    zipcode: string
        the zip-code of a fast food restaurant (e.g. '90007')

    rating: string
        the rating of a fast food restaurant (e.g. '3.7')

    review_count: string
        the rating number of a fast food restaurant (e.g. '200')
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
        a list that contains the 50 biggest fast food brands
    """

    fast_food_brand_list = []
    main_page_url = 'https://www.qsrmagazine.com/reports/2020-qsr-50'
    url_text = make_url_request_using_cache(main_page_url,CACHE_DICT)

    soup = BeautifulSoup(url_text, 'html.parser')

    brand_list = soup.find_all('p',class_='chainame')
    for brand in brand_list:
        fast_food_brand_list.append(brand.text.strip().lower().replace("’","'"))
    
    return fast_food_brand_list



def get_restaurant_list_from_google(brand_name, location):
    '''Make a list of restaurant instances from Google Places API,
       with brand name and location as input value that users want
       to search for.
    
    Parameters
    ----------
    brand_name: string
        The name of the fast food restaurant that users want to search for.
    
    location: string
        The location of the fast food restaurant that users want to search for.
    
    Returns
    -------
    list
        a list of fast food restaurant instances with Google rating information
    '''
    key = secrets.GOOGLE_API_KEY
    converted_brand_name = brand_name.replace(" ","+")
    converted_location = location.replace(" ","+")
    google_api_url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={converted_brand_name}+in+{converted_location}&region=us&type=restaurant&key={key}"

    google_api_url_text = make_url_request_using_cache(google_api_url,CACHE_DICT)
    google_api_url_json = json.loads(google_api_url_text)

    google_instance_list = []
    while len(google_instance_list) <100: #maximum number of restaurants that we grab is 100
        if google_api_url_json['status'] =='ZERO_RESULTS':
            return list()
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
    '''Make a list of fast food restaurant instances from Yelp Fusion API,
       with the list of google instance that users have already got from 
       Google Places API as input value. Each instance will be passed into 
       the Yelp Fusion API to get their corresponding Yelp rating information.
    
    Parameters
    ----------
    google_instance_list: list
        The list of google instances
    
    Returns
    -------
    list
        a list of fast food restaurant instances with Yelp rating information
    '''
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
    '''create a new SQLite table 
    Parameters
    ----------
    data_source: string
        The name of data source

    table_name: string
        The name of table

    database_name: string
        The name of database
    
    Returns
    -------
    None
    '''
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
    '''Insert new value to the SQLite table
    
    Parameters
    ----------
    object: list
        The list of fast food restaurant instances, with each instances
        a new value that we want to insert to the table
    
    table_name: string
        The name of table that we want to insert new value to

    database_name: string
        The name of database that we want to insert new value to
    
    Returns
    -------
    None
    '''
    connection = sqlite3.connect(f"{database_name}.sqlite")
    cursor = connection.cursor()
    insert_value = f"""INSERT INTO {table_name}
       VALUES(NULL,?,?,?,?,?,?,?)"""
    for restaurant in object_list:
        insert_list = [restaurant.name,restaurant.street,restaurant.city,restaurant.state,restaurant.zipcode,restaurant.rating,restaurant.review_count]
        cursor.execute(insert_value,insert_list)
    
    connection.commit()
    connection.close()
    


def match_restaurant(google_table,yelp_table,database_name):
    '''From two table, match their information with foreign keys
    
    Parameters
    ----------
    google_table: string
        The name of first SQLite table, containing google ratings' information
    
    yelp_table: string
        The name of second SQLite table, containing yelp ratings' information

    database_name: string
        The name of database containg the above two tables
    
    Returns
    -------
    list
        a list of tuples that represent the query result, with each tuple containing
        an restaurant intance's detailed information including google's rating and 
        yelp's rating
    '''
    connection = sqlite3.connect(f"{database_name}.sqlite")
    cursor = connection.cursor()
    query = f"""
    SELECT {google_table}.Name, {google_table}.Street, {google_table}.City, {google_table}.Zipcode, Google_rating, Google_review_count, Yelp_rating, Yelp_review_count
    FROM {google_table}
    JOIN {yelp_table}
    ON ({google_table}.Name == {yelp_table}.Name
    AND {google_table}.Street == {yelp_table}.Street
    AND {google_table}.Zipcode == {yelp_table}.Zipcode)
    """
    result = cursor.execute(query).fetchall()
    connection.close()
    return result
    


def create_dict_of_ratings_list(matched_restaurant_list):
    '''From the list of tuples that represent the query result, build a dictionary 
    of lists that contains all data we need to generate the plots.
    
    Parameters
    ----------
    matched_restaurant: list
        The list of tuples that represent the query result, with each tuple containing
        an restaurant intance's detailed information including google's rating and 
        yelp's rating
    
    Returns
    -------
    dict
        a dictionary of lists that contains all data we need to generate the plots, including
        Google ratings and its rating numbers, Yelp ratings and its rating numbers, Weighted ratings 
        and total rating numbers.
    
    '''
    dict_of_ratings = {}
    list_of_google_ratings = []
    list_of_google_review_count = []
    list_of_yelp_ratings = []
    list_of_yelp_review_count = []
    list_of_weighted_ratings = []
    list_of_total_review_count = []

    for resuaurant in matched_restaurant_list:
        list_of_google_ratings.append(float(resuaurant[4]))
        list_of_google_review_count.append(int(resuaurant[5]))
        list_of_yelp_ratings.append(float(resuaurant[6]))
        list_of_yelp_review_count.append(int(resuaurant[7]))
        
        total_review_count = (int(resuaurant[5]) + int(resuaurant[7]))
        list_of_total_review_count.append(int(total_review_count))

        weighted_rating = (float(resuaurant[4])*int(resuaurant[5]) + float(resuaurant[6]) * int(resuaurant[7])) / total_review_count
        list_of_weighted_ratings.append(float(format(weighted_rating,'.2f')))

    dict_of_ratings["Google_ratings"] = list_of_google_ratings
    dict_of_ratings["Google_review_counts"] = list_of_google_review_count
    dict_of_ratings["Yelp_ratings"] = list_of_yelp_ratings
    dict_of_ratings["Yelp_review_counts"] = list_of_yelp_review_count
    dict_of_ratings["Weighted_ratings"] = list_of_weighted_ratings
    dict_of_ratings["Total_review_counts"] = list_of_total_review_count

    return dict_of_ratings



def make_histogram(xvals,title):
    '''Generate probability distribution of a dataset in terms of histogram.
    
    Parameters
    ----------
    xvals: list
        a list that contains dataset

    title: string
        The title of histogram
    
    Returns
    -------
    None
    '''
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=xvals, 
        histnorm='probability',
        #name = f''
        xbins=dict(start=-0, end=5, size=0.1), # bins used for histogram
        marker_color='#EB89B5',
        opacity=0.75
    ))

    fig.update_layout(
            title_text = title,  # title of plot
            xaxis_title_text = 'Rating',  # xaxis label
            yaxis_title_text = 'Probability',  # yaxis label
            bargap=0.2,  # gap between bars of adjacent location coordinates
           #bargroupgap=0.1  # gap between bars of the same location coordinates
        )
    fig.show()
    #fig.write_html("histogram.html", auto_open=True)

        

def make_scattor_plots(xvals,yvals,x_axis,y_axis,title):
    '''Generate scatter plot of a dataset versus another dataset.
    
    Parameters
    ----------
    xvals: list
        a list that contains dataset

    xvals: list
        a list that contains dataset

    x_axis: string
        The name of x axis
    
    x_axis: string
        The name of y axis
    
    title: string
        The title of scatter plot
    
    Returns
    -------
    None
    '''
    fig = go.Figure()
    # Add traces
    fig.add_trace(go.Scatter(
        x=xvals, y=yvals,
        mode='markers',
    ))
      
    fig.update_layout(
        title_text=title,  # title of plot
        xaxis_title_text=x_axis,  # xaxis label
        yaxis_title_text=y_axis)  # yaxis label
    fig.show()
    #fig.write_html("histogram.html", auto_open=True)
    


if __name__ == "__main__":
    
    while True:
        input_brand = input('Please enter a fast food restaurant name for the research or type "exit" to leave: ')
        print(" ")
        if input_brand.lower() == "exit":
            print('Bye!')
            break 

        fast_food_brand_list = build_fast_food_brand_list()
        if input_brand.lower() not in fast_food_brand_list:
            print("The restaurant you enter is not a fast food restaurant, please try again.")
            continue

        input_location = input("Please enter a location you want to search (for example, Los Angeles): ")
        google_result = get_restaurant_list_from_google(input_brand,input_location)
        if google_result is False:
            print(f"we cannot find any {input_brand} restaurants in {input_location}. Try another location.") 
            continue

        yelp_result = get_corresponding_yelp_information(google_result)

        create_new_table("Google","Google_table", "restaurant_database")
        insert_new_value(google_result,"Google_table","restaurant_database")

        create_new_table("Yelp", "Yelp_table", "restaurant_database")
        insert_new_value(yelp_result, "Yelp_table", "restaurant_database")

        matched_restaurant_list = match_restaurant("Google_table","Yelp_table","restaurant_database")

        dict_of_ratings = create_dict_of_ratings_list(matched_restaurant_list)
        
        print("-----------------------------")
        print(f"We found {len(google_result)} relevant results on Google and "
              f"{len(yelp_result)} relevant results on Yelp.")
        print(" ")
        print(f"After the matching, we found {len(matched_restaurant_list)} qualified restaurants.")
        print("We will use the data of these qualified restaurants for you to examine and plot.")
        print(" ")

        while True:
            plot_choice_text = \
            '''We have the following plots available for you to check, enter the number to see the corresponding plot:
            1. Distribution of Google Rating
            2. Distribution of Yelp Rating
            3. Distribution of Weighted Rating
            4. Scatter plot of Google Rating versus its Rating Numbers
            5. Scatter plot of Yelp Rating versus its Rating Numbers
            6. Scatter plot of Google and Yelp's Weighted Rating versus its total Rating Numbers
            7. Scatter plot of Google Rating versus its Yelp Rating
            8. Scatter plot of Google Rating number versus its Yelp Rating Numbers'''
            print(plot_choice_text)
            print(" ")
            input_plot = input("What plot do you want to examine? Enter the number 1-8.")
            if input_plot not in ["1","2","3","4","5","6","7","8"]:
                print("Please enter a valid number between 1-8.")
                continue
            elif input_plot == "1":
                xvals = dict_of_ratings["Google_ratings"]
                title = "Distribution of Google Rating"
                make_histogram(xvals,title)

            elif input_plot == "2":
                xvals = dict_of_ratings["Yelp_ratings"]
                title = "Distribution of Yelp Rating"
                make_histogram(xvals,title)

            elif input_plot == "3":
                xvals = dict_of_ratings["Weighted_ratings"]
                title = "Distribution of Weighted Rating"
                make_histogram(xvals,title)

            elif input_plot == "4":
                yvals = dict_of_ratings["Google_ratings"]
                xvals = dict_of_ratings['Google_review_counts']
                y_axis = "Google_ratings"
                x_axis = 'Google_review_counts'
                title = 'Scatter plot of Google Rating versus its Rating Numbers'
                make_scattor_plots(xvals,yvals,x_axis,y_axis,title)

            elif input_plot == "5":
                yvals = dict_of_ratings["Yelp_ratings"]
                xvals = dict_of_ratings["Yelp_review_counts"]
                y_axis = "Yelp_ratings"
                x_axis = 'Yelp_review_counts'
                title = 'Scatter plot of Yelp Rating versus its Rating Numbers'
                make_scattor_plots(xvals,yvals,x_axis,y_axis,title)

            elif input_plot == "6":
                yvals = dict_of_ratings["Weighted_ratings"]
                xvals = dict_of_ratings["Total_review_counts"]
                y_axis = "Weighted_ratings"
                x_axis = 'Total_review_counts'
                title = "Scatter plot of Google and Yelp's Weighted Rating versus its Rating Numbers"
                make_scattor_plots(xvals,yvals,x_axis,y_axis,title)
            
            elif input_plot == "7":
                yvals = dict_of_ratings["Google_ratings"]
                xvals = dict_of_ratings["Yelp_ratings"]
                y_axis = "Google_ratings"
                x_axis = 'Yelp_ratings'
                title = 'Scatter plot of Google Rating versus its Yelp Rating'
                make_scattor_plots(xvals,yvals,x_axis,y_axis,title)
            
            elif input_plot == "8":
                yvals = dict_of_ratings["Google_review_counts"]
                xvals = dict_of_ratings["Yelp_review_counts"]
                y_axis = 'Google_review_counts'
                x_axis = 'Yelp_review_counts'
                title = 'Scatter plot of Google Rating number versus its Yelp Rating Numbers'
                make_scattor_plots(xvals,yvals,x_axis,y_axis,title)



            print(" ")
            input_another_plot = input("Do you want to plot another chart? (Yes/No): ")
            if input_another_plot.lower() == "no":
                print(" ")
                break
            else:
                print(" ")
                continue

            





    '''
    x = get_restaurant_list_from_google("McDonald's", "Los Angeles")
    y = get_corresponding_yelp_information(x)
    create_new_table("Google", "Google_list", "Final_Project_database")
    insert_new_value(x, "Google_list", "Final_Project_database")
    create_new_table("Yelp", "Yelp_list", "Final_Project_database")
    insert_new_value(y, "Yelp_list", "Final_Project_database")
    z = match_restaurant("Google_list","Yelp_list","Final_Project_database")
    a = create_dict_of_ratings_list(z)
    print(a)
    
    for i in y:
        print(i.info())
    print("----------------")
    for j in x:
        print(j.info())
    '''