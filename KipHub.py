# KipHub Traffic
# Fred Rique (Farique) (c) 2021
# www.github.com/farique1/kiphub-traffic

import re
import json
import argparse
import requests
from datetime import datetime, timedelta

# Credentials
username = '<YOUR_USERNAME>'
token = '<YOUR_TOKEN>'

# Paths
base_url = 'https://api.github.com/repos'
user_url = username
repo_url = ''
referrers_url = 'traffic/popular/referrers'
views_url = 'traffic/views'
clones_url = 'traffic/clones'
repos_url = 'https://api.github.com/user/repos'
rate_url = 'https://api.github.com/rate_limit'
data_file = 'JSONs/traffic.json'

# Accepted date format
match_date = r'^((\d{1,4}-)?\d{1,2}-)?\d{1,2}$'

# Sort
sort_1st = 'views'
sort_2nd = 'clones'
sort_3rd = 'uniques'
sort_4th = 'count'
sort_name = 'name'  # 'updated' ignores the name sort (as all have the same date)
sort_reverse = False

# User
use_cache = False  # If True get API data from disk
keep_cache = False  # Keep local API response copies
view_only = False  # If True uses data from the aggregated JSON
min_cust = None  # Start date on the format 'y-m-d', 'm-d' or 'd'
max_cust = None  # End date on the format 'y-m-d', 'm-d' or 'd'
period = None  # number of days before last day to be shown (overrides min_cust)
sort = ''  # Sort order. none=names v=views c=clones o=count (uniques=def) r=reverse
cache = ''  # Cache behavior. u=use k=keep v=view only


def dateEntry(date_entry, date_type):
    '''Check the date entry format and convert to a valid datetime
       date_entry = the entry to check
       date_type = the type of date (begin or end) to report on errors'''
    if date_entry:
        # # Use something like this.
        # # Smaller but is defaulting to 1900-01-01 on missing values
        # for fmt in ('%y-%m-%d', '%Y-%m-%d', '%m-%d', '%d'):
        #     try:
        #         date_entry = datetime.strptime(str(date_entry), fmt)
        #     except ValueError:
        #         print('error')
        if not re.match(match_date, date_entry):
            print(f'\n Invalid {date_type} date entry format: {date_entry}\n')
            raise SystemExit(0)

        # Deal with partial date entry
        data_format = date_entry.count('-')
        if data_format == 0:
            date_entry = f'{datetime.now().strftime("%Y-%m")}-{date_entry}'
        if data_format == 1:
            date_entry = f'{datetime.now().strftime("%Y")}-{date_entry}'
        year = date_entry.split('-')[0]
        if data_format == 2 and len(year) < 4:
            date_entry = '2000'[0:(4-len(year))] + date_entry

        try:
            date_entry = datetime.strptime(date_entry, '%Y-%m-%d')
        except ValueError:
            print(f'\n Invalid {date_type} date format: {date_entry}\n')
            raise SystemExit(0)
    return date_entry


# Command line arguments
ap = argparse.ArgumentParser(description='Collect and save GitHub traffic data '
                                         '(-c and -s can take more than one letter)',
                             epilog='Fred Rique (farique) (c) 2021 - '
                                    'github.com/farique/kiphub-traffic')
ap.add_argument('-b', '--begin', metavar='', default=min_cust,
                help='Custom start date (defaul = fisrt reported date)', )
ap.add_argument('-e', '--end', metavar='', default=max_cust,
                help='Custom end date (defaul = last updated date)')
ap.add_argument('-p', '--period', metavar='', default=period, type=int,
                help='Days before end date')
ap.add_argument('-c', '--cache', metavar='', default=cache,
                help='Cache behavior: u=use k=keep v=view only')
ap.add_argument('-s', '--sort', default=sort,
                help='Sort order. none=names v=views c=clones o=count (uniques=def) r=reverse')
args = ap.parse_args()

# Apply arguments
min_cust = dateEntry(args.begin, 'begin')
max_cust = dateEntry(args.end, 'end')
period = args.period

cache = args.cache.lower()
use_cache = True if 'u' in cache else use_cache
keep_cache = True if 'k' in cache else keep_cache
view_only = True if 'v' in cache else view_only

sort = args.sort.lower()
if 'v' in sort:
    sort_name = 'updated'
    sort_reverse = True
if 'c' in sort:
    sort_1st, sort_2nd = sort_2nd, sort_1st
    sort_name = 'updated'
    sort_reverse = True
if 'o' in sort:
    sort_3rd, sort_4th = sort_4th, sort_3rd
if 'r' in sort:
    sort_reverse = not sort_reverse


def loadData(data_file):
    '''Load the consolidated JSON
       If not found, generate a blank array
       data_file = the JSON to load'''
    try:
        with open(data_file, 'r') as f:
            traffic_in = json.load(f)
    except FileNotFoundError:
        traffic_in = []
    return traffic_in


def saveData(data_file, data):
    '''Save the consolidated JSON
       data_file = the JSON to save'''
    with open(data_file, 'w') as f:
        json.dump(data, f, indent=4)


def getAPIdata(url, file=None, use_cache=use_cache):
    '''Get API JSON data from the web or a cached file
       url = API point location
       file = JSON file to load or save
       use_cache = if True will load the file from disk'''
    if not use_cache:
        print(f'Fetching {url}')
        response = json.loads(gh_session.get(url).text)
        if file and keep_cache:
            print(f'Saving {file}')            
            with open(file, 'w') as f:
                json.dump(response, f, indent=4)
    else:
        try:
            with open(file, 'r') as f:
                response = json.load(f)
        except FileNotFoundError:
            print(f'\n Cache file not found: {file}\n')
            print()
            raise SystemExit(0)
    return response


def gatherData(traffic_data):
    '''Consolidate all the API responses into a single JSON
       merging with a previous consolidated JSON
       traffic_data = the previous JSON'''
    def gatherViewClone(data_type):
        '''Read and format the repository information from views or clones
           data_type = if 'views' or 'clones' '''
        data = getAPIdata(f'{base_url}/{user_url}/{repo_name}/traffic/{data_type}',
                           f'JSONs/{repo_name}_{data_type}.json')
        data_dict = {}
        data_dict['count'] = data['count']
        data_dict['uniques'] = data['uniques']

        # Make a dictionary with the days names as keys for easy merging
        # If the key (day) already exists the value will be replaced with the new one
        days_dict = {}
        if repo_index is not None:
            days_dict = traffic_data[repo_index][data_type]['days']
        if data['count'] > 0 or data['uniques'] > 0:
            for day in data[data_type]:
                short_date = day['timestamp'][:10]
                days_dict[short_date] = [day['count'],
                                         day['uniques']]
        data_dict['days'] = days_dict
        return data_dict

    # Previous repos name and index dictionary
    # finds their existence and place on the list
    repos_dict = {}
    for count, repo in enumerate(traffic_data):
        repos_dict[repo['name']] = count

    repos = getAPIdata(repos_url, 'JSONs/repos.json')
    repo_names = [(repo['name']) for repo in repos]
    for repo_name in repo_names:
        repo_index = None
        if repo_name in repos_dict:
            repo_index = repos_dict[repo_name]

        referrers = getAPIdata(f'{base_url}/{user_url}/{repo_name}/{referrers_url}',
                               f'JSONs/{repo_name}_referrers.json')
        referrers_list = []
        if len(referrers) > 0:
            for referrer in referrers:
                referrers_dict = {}
                referrers_dict['name'] = referrer['referrer']
                referrers_dict['count'] = referrer['count']
                referrers_dict['uniques'] = referrer['uniques']
                referrers_list.append(referrers_dict)

        views_dict = gatherViewClone('views')
        clones_dict = gatherViewClone('clones')

        repo_dict = {}
        repo_dict['name'] = repo_name
        repo_dict['updated'] = datetime.now().strftime('%Y-%m-%d')
        repo_dict['referrers'] = referrers_list
        repo_dict['views'] = views_dict
        repo_dict['clones'] = clones_dict

        # If the repo already exists replace with merged, if not, create
        if repo_index is not None:
            traffic_data[repo_index] = repo_dict
        else:
            traffic_data.append(repo_dict)

    return traffic_data


def showData(traffic_data, min_cust, max_cust):
    '''Show the traffic data
       traffic_data = the consolidated JSON with all the info
       min_cust = the user defined start day date
       max_cust = the user defined end day date'''
    def getMinMaxdate(data_type, min_day, max_day):
        '''Get the earlier and later days in the views and clones data
           data_type = if 'views' or 'clones'
           min_day = the earlier day in the data
           max_day = the later day in the data'''
        for repo in traffic_data:
            if repo[data_type]['count'] > 0 or repo[data_type]['uniques'] > 0:
                # Convert the dictionary into a list to be able to sort it
                days_list = list(repo[data_type]['days'].items())
                days_list = sorted(days_list)
                min_tmp = datetime.strptime(days_list[0][0], '%Y-%m-%d')
                max_tmp = datetime.strptime(days_list[-1][0], '%Y-%m-%d')
                min_day = min(min_day, min_tmp)
                max_day = max(max_day, max_tmp)
        return min_day, max_day


    def showViewClone(data_type):
        '''Assemble and shows the data for the views and the clones
           data_type = if 'views' or 'clones' ''' 
        def showContUnique(data_pos, title):
            '''Assemble and shows the data for count and uniques
               data_pos = the position of count and uniques on the list
               title = the name of the data being shown'''
            print(title, end='')
            # Call the days in the correct order (dictionaries have no sort)
            total = 0
            for d in range(interval.days + 1):
                day = min_day + timedelta(days=d)
                day = day.strftime('%Y-%m-%d')
                # Print the data if the day exists, if not, leave a blank space
                if day in repo[data_type]['days']:
                    day_view = repo[data_type]["days"][day][data_pos]
                    total = total + day_view
                    print(f'{str(day_view).ljust(2)} ', end='')
                else:
                    print('   ', end='')
            print(f' {total}')


        if repo[data_type]['count'] > 0 or repo[data_type]['uniques'] > 0:
            print(f'{data_type.capitalize()}: '
                  f'{repo[data_type]["count"]} '
                  f'{repo[data_type]["uniques"]} ')
            print(' Day: ', end='')
            for d in range(interval.days + 1):
                day = min_day + timedelta(days=d)
                print(f'{str(day.day).zfill(2)} ', end='')
            print(' Sum')
            showContUnique(0, ' Cnt: ')
            showContUnique(1, ' Unq: ')


    # Set Starting and ending days as the last day updated
    min_day = max_day = datetime.strptime(traffic_data[0]["updated"], '%Y-%m-%d')

    min_day, max_day = getMinMaxdate('views', min_day, max_day)
    min_day, max_day = getMinMaxdate('clones', min_day, max_day)
    if min_cust:
        min_day = min_cust if min_cust > min_day else min_day
    if max_cust:
        max_day = max_cust if max_cust < max_day else max_day
    if period:
        min_day = max(max_day - timedelta(period - 1), min_day)
    interval = max_day - min_day

    # Output the data
    print(f'{username} has {len(traffic_data)} GitHub repositories')
    print(f'Updated in {traffic_data[0]["updated"]}')
    traffic_data = sorted(traffic_data,
                          key = lambda i: (i[sort_name].lower(),
                                           i[sort_1st][sort_3rd],
                                           i[sort_1st][sort_4th],
                                           i[sort_2nd][sort_3rd],
                                           i[sort_2nd][sort_4th]),
                          reverse=sort_reverse)
    for repo in traffic_data:
        print()
        print(repo['name'])
        if len(repo['referrers']) > 0:
            print('Referrers:', end=' ')
            for referrer in repo['referrers']:
                print(f'{referrer["name"]} '
                      f'{referrer["count"]} '
                      f'{referrer["uniques"]} ',
                      end='')
            print()
        showViewClone('views')
        showViewClone('clones')
    print()


# create a re-usable session object with the user creds in-built
gh_session = requests.Session()
gh_session.auth = (username, token)

# # Show ramaining rate (use_cache must be False)
# req = getAPIdata(rate_url)
# print(req)
# raise SystemExit(0)

traffic_in = loadData(data_file)

traffic_out = traffic_in
if not view_only:
    traffic_out = gatherData(traffic_in)

saveData(data_file, traffic_out)

showData(traffic_out, min_cust, max_cust)
