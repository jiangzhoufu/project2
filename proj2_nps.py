#################################
###### Name: Jiangzhou Fu
##### Uniqname: jiangzhf
#################################

from bs4 import BeautifulSoup
import requests
import json
import secrets as secrets # file that contains your API key

CACHE_FILENAME = 'proj2_cache.json'
CACHE_DICT = {}


def open_cache():
    ''' Opens the cache file if it exists and loads the JSON into
    the CACHE_DICT dictionary.
    if the cache file doesn't exist, creates a new cache dictionary
    
    Parameters
    ----------
    None
    
    Returns
    -------
    The opened cache: dict
    '''
    try:
        cache_file = open(CACHE_FILENAME, 'r')
        cache_content = cache_file.read()
        cache_dict = json.load(cache_content)
        cache_file.close()
    except:
        cache_dict = {}
        
    return cache_dict


def save_cache(cache_dict):    
    ''' Saves the current state of the cache to disk
    
    Parameters
    ----------
    cache_dict: dict
        The dictionary to save
    
    Returns
    -------
    None
    '''
    
    dumped_json = json.dumps(cache_dict)
    fw = open(CACHE_FILENAME, 'w')
    fw.write(dumped_json)
    fw.close()
    

class NationalSite:
    '''a national site

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
    '''
    def __init__(self, category, name, address, zipcode, phone):
        
        self.category = category
        self.name = name 
        self.address = address
        self.zipcode = zipcode
        self.phone = phone
        
    
    def info(self):
        '''
        Shows the national site info, including: name, category, 
        address and zipcode
        
        Parameters
        ----------
        None

        Returns
        -------
        string
             national site information.
        '''
        info = f"{self.name} ({self.category}): {self.address} {self.zipcode}"
        
        return info
    

def build_state_url_dict():
    ''' Make a dictionary that maps state name to state page url from "https://www.nps.gov"

    Parameters
    ----------
    None

    Returns
    -------
    dict
        key is a state name and value is the url
        e.g. {'michigan':'https://www.nps.gov/state/mi/index.htm', ...}
    '''
    url = 'https://www.nps.gov/index.htm'
    state_dict = {}
    
    if url in CACHE_DICT.keys():
        print('Using Cashe')
        response = CACHE_DICT[url]
        soup = BeautifulSoup(response, 'html.parser')
    
    else:
        print('Fetching')
        response = requests.get(url)
        CACHE_DICT[url] = response.text
        save_cache(CACHE_DICT)
        soup = BeautifulSoup(response.text, 'html.parser')
    
    res = soup.find('ul', class_='dropdown-menu SearchBar-keywordSearch').find_all('li')
    
    for i in res:
        state = i.find('a').string.strip().lower()
        url = 'https://www.nps.gov' + i.find('a')['href']
        state_dict[state] = url
        
    return state_dict
        
        
        
def get_site_instance(site_url):
    '''Make an instances from a national site URL.
    
    Parameters
    ----------
    site_url: string
        The URL for a national site page in nps.gov
    
    Returns
    -------
    instance
        a national site instance
    '''
    
    response = requests.get(site_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    if soup.find('span', class_='Hero-designation').string:
        category = soup.find('span', class_='Hero-designation').string.strip()
    else: category = 'no category'
    
    if soup.find('a', class_='Hero-title').string:
        name = soup.find('a', class_='Hero-title').string.strip()
    else: name = 'no name'
    
    if  soup.find('span', itemprop='addressLocality').string:
        locality = soup.find('span', itemprop='addressLocality').string.strip()
    else: locality = 'no address'
    
    if soup.find('span', itemprop='addressRegion').string:
        region = soup.find('span', itemprop='addressRegion').string.strip()
    else: region = 'no adress'
    
    if (locality == 'no address') and (region == 'no adress'):
        address = 'no adress'
    else: address = locality + ', ' + region
    
    zipcode = soup.find('span', itemprop='postalCode').string.strip()
    phone = soup.find('span', itemprop='telephone').string.strip()
    
    return NationalSite(category, name, address, zipcode, phone)


def get_sites_for_state(state_url):
    '''Make a list of national site instances from a state URL.
    
    Parameters
    ----------
    state_url: string
        The URL for a state page in nps.gov
    
    Returns
    -------
    list
        a list of national site instances
    '''

    if state_url in CACHE_DICT.keys():
        print('Using Cache')
        response = CACHE_DICT[state_url]
        save_cache(CACHE_DICT)
        soup = BeautifulSoup(response, 'html.parser')
    
    else:
        print('Fetching')
        response = requests.get(state_url)
        CACHE_DICT[state_url] = response.text
        save_cache(CACHE_DICT)
        soup = BeautifulSoup(response.text, 'html.parser')
        
    parks = soup.find('ul', id='list_parks').find_all('h3')
    
    sites_for_state = []
    for park in parks:
        park_url = 'https://www.nps.gov' + park.find('a')['href'] + 'index.htm'
        sites = get_site_instance(park_url)
        sites_for_state.append(sites)
    
    return sites_for_state
        


def get_nearby_places(site_object):
    '''Obtain API data from MapQuest API.
    
    Parameters
    ----------
    site_object: object
        an instance of a national site
    
    Returns
    -------
    dict
        a converted API return from MapQuest API
    '''
    if site_object.zipcode in CACHE_DICT.keys():
        print('Using Cache')
        response = CACHE_DICT[site_object.zipcode]
        
    else:
        print('Fetching')
        MapQuest = 'http://www.mapquestapi.com/search/v2/radius'
        params_dict = {'key': secrets.API_KEY,
                       'origin': site_object.zipcode,
                       'radius': 10,
                       'maxMatches': 10,
                       'ambiguities': 'ignore',
                       'outFormat': 'json'}
        response = requests.get(MapQuest, params = params_dict).json()
        CACHE_DICT[site_object.zipcode] = response
        
    return response
    

if __name__ == "__main__":
    
    state_url_dict = build_state_url_dict()
    
    flag = True
    while flag:
        state = input('Enter a state name (e.g. Michigan, michigan) or exit: ')
        
        if state == 'exit':
            print('you exit')
            flag=False
            
        elif state.lower() in state_url_dict.keys():
            state_url = state_url_dict[state.lower()]
            sites = get_sites_for_state(state_url)
            print('---------------------------------')
            print(f'List of national sites in {state}')
            print('---------------------------------')
            for site in sites:
                print(f'[{sites.index(site)+1}] {site.info()}')
            print('\n')
            
            while flag:
                number = input("Choose the number of detail search or 'exit' or 'back': ")
                if number == 'back':
                    break
                elif number == 'exit':
                    print('you exit')
                    flag = False
                    
                elif number.isnumeric():
                    if 0 < int(number) <= len(sites):
                        index = int(number) - 1 
                    
                        nearby_places = get_nearby_places(sites[index])["searchResults"]
                        print("--------------------------------")
                        print(f"Places near {sites[index].name}")
                        print("--------------------------------")

                        for nearby_place in nearby_places:
                            name = nearby_place["name"]
                            if nearby_place["fields"]["address"]:
                                address = nearby_place["fields"]["address"]
                            else:
                                address = "no address"
                            if nearby_place["fields"]["city"]:
                                city = nearby_place["fields"]["city"]
                            else:
                                city = "no city"
                            if nearby_place["fields"]["group_sic_code_name"]:
                                category = nearby_place["fields"]["group_sic_code_name"]
                            else:
                                category = "no category"
                            print(f"- {name} ({category}): {address}, {city}")
                        print('\n')
                else:
                    print("[Error] Invalid input")
                    print("-------------------------------\n")
        else:
            print("[Error] Enter proper state name \n")
                    