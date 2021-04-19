#################################
##### Name: Hongyu Dai
##### Uniqname: hongyud
#################################

from bs4 import BeautifulSoup
import requests
import json
import secrets # file that contains your API key
import time



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


def make_url_request_using_cache(url, cache):
    if (url in cache.keys()): # the url is our unique key
        print("Using cache")
        return cache[url]
    else:
        print("Fetching")
        time.sleep(1)
        response = requests.get(url, headers=headers)
        cache[url] = response.text
        save_cache(cache)
        return cache[url]

CACHE_FILENAME = 'cache_Final.json'
CACHE_DICT = open_cache(CACHE_FILENAME)
headers = {'User-Agent': 'UMSI 507 Course Final Project','From': 'hongyud@umich.edu','Course-Info': 'https://www.si.umich.edu/programs/courses/507'}


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


if __name__ == "__main__":
    x = build_fast_food_brand_list()
    print(x)