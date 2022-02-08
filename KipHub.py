#!/usr/bin/python3

# KipHub Traffic
# v1.1 2022-02-08
# Fred Rique (Farique) (c) 2021 - 2022
# www.github.com/farique1/kiphub-traffic

import re
import os
# import sys
import json
import shutil
import argparse
import requests
from datetime import datetime, timedelta, date

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
data_file = f'JSONs/{username}.json'

# Accepted date format
match_date = r'^((\d{1,4}-)?\d{1,2}-)?\d{1,2}$'

# Sort
sort_view_clone = 0
sort_count_unique = 0
sort_reverse = False

# User
use_cache = False  # If True get API data from disk
keep_cache = False  # Keep local API response copies
view_only = True  # If True uses data from the aggregated JSON
min_cust = None  # Start date on the format 'y-m-d', 'm-d' or 'd'
max_cust = None  # End date on the format 'y-m-d', 'm-d' or 'd'
period = 30  # number of days before last day to be shown (overrides min_cust) 0=all
cache = ''  # Cache behavior. u=use k=keep v=view only
sort = ''  # Sort order: default=names,uniques v=views c=clones o=count r=reverse
toggle = ''  # toggle view items: a=days without data, r=referrers, e=expand referrers, p=report, l=labels, d=daily, s=sum, v=views, c=clones, o=count, u=unique


def dateEntry(date_entry, date_type):
    '''Check the date entry format and convert to a valid datetime
       date_entry = the entry to check
       date_type = the type of date (begin or end) to report on errors'''
    if date_entry:
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
            date_entry = '2000'[0:(4 - len(year))] + date_entry

        try:
            date_entry = datetime.strptime(date_entry, '%Y-%m-%d')
        except ValueError:
            print(f'\n Invalid {date_type} date format: {date_entry}\n')
            raise SystemExit(0)
    return date_entry


def notStrings(str1, str2):
    '''Toggle characters on a string based on a second string'''
    for c in str2:
        if c in str1:
            str1 = str1.replace(c, '')
        else:
            str1 += c
    return str1


# Command line arguments
ap = argparse.ArgumentParser(description='KipHub Traffic: download and save GitHub traffic data',
                             epilog='Fred Rique (farique) (c) 2021 - '
                                    'github.com/farique/kiphub-traffic \n')
ap.add_argument('-d', '--down', action='store_false', default=view_only,
                help='Download data from Github')
ap.add_argument('-c', '--cache', metavar='uk', default=cache,
                help='Cache behavior: u=use k=keep (default="%(default)s")')
ap.add_argument('-b', '--begin', metavar='y-m-d', default=min_cust,
                help='Custom start date (defaul=fisrt reported date)', )
ap.add_argument('-e', '--end', metavar='y-m-d', default=max_cust,
                help='Custom end date (defaul=last updated date)')
ap.add_argument('-p', '--period', metavar='days', default=period, type=int,
                help='Days before end date: 0=all (default=%(default)s)')
ap.add_argument('-s', '--sort', metavar='vcor', default=sort,
                help='Sort order: v=views c=clones o=count r=reverse (default=names,uniques)')
ap.add_argument('-t', '--toggle', metavar='arepldsvcou',
                help=('toggle view items: a=days without data, r=referers, e=expand referers, '
                      'p=report, l=labels, d=daily, s=sum, v=views, c=clones, o=count, u=unique'
                      ' (default="%(default)s")'))
args = ap.parse_args()

# Apply arguments
min_cust = dateEntry(args.begin, 'begin')
max_cust = dateEntry(args.end, 'end')
period = args.period
view_only = args.down

cache = args.cache.lower()
use_cache = True if 'u' in cache else use_cache
keep_cache = True if 'k' in cache else keep_cache

# Set values to add to the sort index amount
sort = args.sort.lower()
if 'v' in sort:
    sort_view_clone = 1
    sort_count_unique = 1
if 'c' in sort:
    sort_view_clone = 3
    sort_count_unique = 1
if 'o' in sort:
    sort_count_unique = 0
if 'r' in sort:
    sort_reverse = not sort_reverse

if args.toggle is not None:
    toggle = notStrings(toggle.lower(), args.toggle.lower())
show_all_days = 'a' not in toggle
show_referers = 'r' not in toggle
expand_referers = 'e' not in toggle
show_report = 'p' not in toggle
Show_labels = 'l' not in toggle
show_daily = 'd' not in toggle
show_sum = 's' not in toggle
show_views = 'v' not in toggle
show_clones = 'c' not in toggle
show_count = 'o' not in toggle
show_uniqu = 'u' not in toggle


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
    if os.path.exists(data_file):
        shutil.copy(f'JSONs/{username}.json', f'JSONs/{username}_bkp.json')
    with open(data_file, 'w') as f:
        json.dump(data, f, indent=4)


def getAPIdata(url, file=None, use_cache=use_cache):
    '''Get API JSON data from the web or a cached file
       url = API point location
       file = JSON file to load or save
       use_cache = if True will load the file from disk'''

    # create a re-usable session object with the user creds in-built
    gh_session = requests.Session()
    gh_session.auth = (username, token)

    if not use_cache:
        print(f'Fetching {url}')
        response = json.loads(gh_session.get(url).text)

        # Response error
        if type(response) is dict:
            message = response.get('message', None)
            if message:
                print('\nAPI error\n')
                for key in response:
                    print(f'{key}: {response[key]}')
                print(f'\n{response}\n')
                raise SystemExit(0)
        if file and keep_cache:
            print(f'Saving {file}')
            with open(file, 'w') as f:
                json.dump(response, f, indent=4)

    # Read from disk
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

    # Finds previous repo names and indexes them
    repos_dict = {}
    for count, repo in enumerate(traffic_data):
        repos_dict[repo['name']] = count

    repos = getAPIdata(repos_url, 'JSONs/repos.json')
    repo_names = [(repo['name']) for repo in repos if repo['owner']['login'] == username]
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


def buildOutput(traffic_data):
    '''Build the output lists
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

    def buildViewClone(data_type):
        '''Assemble and shows the data for the views and the clones
           data_type = if 'views' or 'clones' '''

        repo_parc = []
        l_title = f'{data_type.capitalize()}:'
        tot_c = 0
        tot_u = 0
        l_days = ''
        l_count = ' Cnt: '
        l_uniqu = ' Unq: '
        p_days = ''
        p_count = ''
        p_uniqu = ''

        report = (f' C{repo[data_type]["count"]}'
                  f' U{repo[data_type]["uniques"]}'
                  f' (last 14 days)')

        # Build display strings
        o_day = 0
        for d in range(interval.days + 1):
            day = min_day + timedelta(days=d)
            day_str = day.strftime('%Y-%m-%d')
            c_day = day.day
            if day_str in repo[data_type]['days'] or show_all_days:

                # Separate months (only if show all days to avoid inconsistencies)
                separator = ' '
                if c_day < o_day and show_all_days:
                    separator = '|'
                p_days += f'{separator}{str(c_day).zfill(2)}'
                o_day = c_day

                if day_str in repo[data_type]['days']:
                    day_view = repo[data_type]['days'][day_str][0]
                    tot_c += day_view
                    p_count += str(day_view).ljust(3)

                    day_view = repo[data_type]['days'][day_str][1]
                    tot_u += day_view
                    p_uniqu += str(day_view).ljust(3)
                else:
                    p_count += '   '
                    p_uniqu += '   '

        if not show_report:
            report = ''
            if not show_daily and show_sum and Show_labels:
                report = ' Total'
        l_title += report

        if show_daily:
            if Show_labels:
                l_days = f' Day:{p_days}'
            l_count += p_count
            l_uniqu += p_uniqu

        if show_sum:
            if show_daily:
                l_days += '  Sum'
            if show_report and not show_daily:
                l_days = '       Total'
            l_count += f' {str(tot_c)}'
            l_uniqu += f' {str(tot_u)}'

        if not Show_labels:
            l_days = None
        if not show_count or (not show_daily and not show_sum):
            l_count = None
        if not show_uniqu or (not show_daily and not show_sum):
            l_uniqu = None

        repo_parc = [l_title, l_days, l_count, l_uniqu]
        if ((tot_c == 0 and tot_u == 0)
                or (not show_views and data_type == 'views')
                or (not show_clones and data_type == 'clones')
                or l_count is None and l_uniqu is None):
            repo_parc = [None, None, None, None]

        return repo_parc, tot_c, tot_u

    # Set Starting and ending days as the last day updated
    last_date_str = traffic_data[0]['updated']
    min_day = max_day = last_date = datetime.strptime(last_date_str, '%Y-%m-%d')

    min_day, max_day = getMinMaxdate('views', min_day, max_day)
    min_day, max_day = getMinMaxdate('clones', min_day, max_day)
    if min_cust:
        min_day = min_cust if min_cust > min_day else min_day
    if max_cust:
        max_day = max_cust if max_cust < max_day else max_day
    if period:
        min_day = max(max_day - timedelta(period - 1), min_day)
    interval = max_day - min_day

    # Create the list
    repo_head = []
    date_diff = date.today() - last_date.date()
    date_diff_str = date_diff.days
    repo_head.append(f'{username} has {len(traffic_data)} GitHub repositories')
    repo_head.append(f'Last updated in {last_date_str} - {date_diff_str} days ago')
    repo_head.append(f'{interval.days + 1} days, from {min_day.date()} to {max_day.date()}')

    repo_list = []
    for repo in traffic_data:
        l_repo = (f'Repo: {repo["name"]}')

        # Assemble referrers
        l_referers = None
        if len(repo['referrers']) > 0 and show_referers:
            l_ref_expand = ''
            refs_start = ''
            refs_middle = ''
            refs_end = '(last 14 days)'
            if not expand_referers:
                refs_start = ' (last 14 days)'
                refs_middle = '\n'
                refs_end = ''

            for referrer in repo['referrers']:
                l_ref_expand += (f'{refs_middle}'
                                 f' {referrer["name"]}'
                                 f' C{referrer["count"]}'
                                 f' U{referrer["uniques"]}')

            l_referers = f'Referrers:{refs_start}{l_ref_expand} {refs_end}'

        repo_views, v_tot_c, v_tot_u = buildViewClone('views')
        repo_count, c_tot_c, c_tot_u = buildViewClone('clones')

        repo_parc = [l_repo, l_referers]
        repo_parc.extend(repo_views)
        repo_parc.extend(repo_count)
        repo_parc.extend([v_tot_c, v_tot_u, c_tot_c, c_tot_u])  # Indexes for sorting only

        repo_list.append(repo_parc)

    repo_list = sorted(repo_list, key=lambda x: x[0].upper(), reverse=sort_reverse)

    sort_index = 9
    if (sort_view_clone + sort_count_unique) > 0:
        sort_index += sort_view_clone + sort_count_unique  # Add to match sort index
        repo_list = sorted(repo_list, key=lambda x: x[sort_index], reverse=sort_reverse)

    return repo_head, repo_list


# def getUserInput(output_head):
#     print('KipHub Traffic: download and save GitHub traffic data\n'
#           'Fred Rique (farique) (c) 2021 - github.com/farique/kiphub-traffic\n')

#     command = ''
#     while command.lower() != 'q':
#         for item in output_head:
#             print(item)
#         print()

#         print('Get data (d)            : no')
#         print('Cache  (c + uk)         : do not use, do not keep local')
#         print('Date   (b|e + date)     : from 2022-01-03 to 2022-02-07')
#         print('Period (p + # of days)  : all ')
#         print('Sort   (s + cvor)       : names reverse')
#         print('Toggle (t + arepldsvcou): all days, referers expand, report, labels, daily, sum, views clones, count, unique')
#         print()

#         command = input('Type option: ')

#     raise SystemExit(0)


def showOutput(repo_list, repo_head):
    for item in repo_head:
        print(item)
    print()

    for output in repo_list:
        for item in output[:10]:
            if item:
                print(item)
        print()


def main():
    # # Show remaining rate (use_cache must be False)
    # req = getAPIdata(rate_url)
    # print(req)
    # raise SystemExit(0)

    traffic = loadData(data_file)

    if view_only and not traffic:
        print('No data available. Use -d to download data from GitHub.\n')
        raise SystemExit(0)

    if not view_only:
        traffic = gatherData(traffic)
        saveData(data_file, traffic)

    output_head, output_list = buildOutput(traffic)

    # Future implemantation (maybe)
    # if (len(sys.argv)) == 1:
    #     getUserInput(output_head)

    showOutput(output_list, output_head)


if __name__ == '__main__':
    main()
