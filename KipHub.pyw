#!/usr/bin/python3

# KipHub Traffic
# v2.1 2024-1-2
# Fred Rique (Farique) (c) 2021 - 2024
# www.github.com/farique1/kiphub-traffic

# Known Bugs:
# Plots not always update if not visible so they are always reconstructed.
# Popups appear at the top left of the screen when first called.
# Adding a tooltip to describe an entry on a table messes with the table sort routine.
#    tooltips.append(dpg.add_tooltip(dpg.last_item()))
#    dpg.add_text(parent=dpg.last_item(), default_value='Average of all repos average')


# Imports
import re
import os
import time
import json
import shutil
import pickle
import argparse
import requests
import webbrowser
import configparser
from itertools import zip_longest
from dataclasses import dataclass
from datetime import datetime, timedelta, date

try:
    import dearpygui.dearpygui as dpg
    dpg_module = True
except ModuleNotFoundError:
    dpg_module = False

# Command line variables
# Credentials
username = 'farique1'
token = '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'
# User
use_cache = False  # If True get API data from disk
keep_cache = False  # Keep local API response copies
view_only = True  # If True uses data from the aggregated JSON
cache = ''  # Cache behavior. u=use k=keep v=view only
sort = 'c'  # Sort order: default=names,uniques v=views c=clones o=count r=reverse
toggle = 'rp'  # toggle view items: a=days without data, r=referrers, e=expand referrers, p=report, l=labels, d=daily, s=sum, v=views, c=clones, o=count, u=unique
mono = False  # Show terminal output without colors
# Terminal colors
CYAN = '\033[38;2;00;255;255m'
YELLOW = '\033[38;2;255;255;00m'
GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
GRAY = '\033[90m'
MAGENTA = '\033[38;2;255;00;255m'
RESET = '\033[39m'

# Shared Variables
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
config_path = 'JSONs\\default.config'
users_file = 'JSONs\\users.ini'
local_path = os.path.split(os.path.abspath(__file__))[0]
users_path = os.path.join(local_path, users_file)
users_ini = configparser.ConfigParser()
config_path = os.path.join(local_path, config_path)
config_ini = configparser.ConfigParser()
# Accepted date format
match_date = r'^((\d{1,4}-)?\d{1,2}-)?\d{1,2}$'
# Sort
sort_view_clone = 0
sort_count_unique = 0
sort_reverse = False
# Misc
repo_count = 0
repo_max = 0
min_cust = None  # Start date on the format 'y-m-d', 'm-d' or 'd'
max_cust = None  # End date on the format 'y-m-d', 'm-d' or 'd'
period = 30  # number of days before last day to be shown (overrides min_cust) 0=all
gui = True  # Show GUI instead of terminal output

# GUI Variables
# Settings
vp_width = 850
vp_height = 900
small_separator = 1
large_separator = 10
default_days = 30
sort_reverse = False
repo_filter = ''
plot_alpha = 64
plot_height = 0
show_dates = True
disable_days = False
tooltips_show = True
tooltips_delay = 0.5
show_views_a = True
show_views_u = True
show_clones_a = True
show_clones_u = True
gui_loaded = False
# Colors
WHITE = (255, 255, 255)
LIGHT = (112, 112, 112)
MEDIUM = (86, 86, 86)
B_YELLOW = (180, 164, 12)
B_RED = (184, 64, 77)
DARK = (60, 60, 60)
VIEW_A = (76, 114, 176)
VIEW_U = (221, 132, 82)
CLONE_A = (85, 168, 104)
CLONE_U = (196, 78, 82)
BG = (20, 142, 142)
WB_IDLE = (18, 109, 102)
WB_ACTIVE = (39, 226, 207)
WB_HOVERED = (31, 178, 163)
WB_DEEP = (13, 76, 70)
PLOT_BG = (246, 246, 246)
# Accent
ACC_ACTIVE = 40
ACC_HOVER = 20
# Lists
BUTTON_COLOR = [('button_med', MEDIUM),
                ('button_dark', DARK),
                ('button_yellow', B_YELLOW),
                ('button_red', B_RED)]

GRAPH_COLOR = [('button_view_a', VIEW_A),
               ('button_view_u', VIEW_U),
               ('button_clone_a', CLONE_A),
               ('button_clone_u', CLONE_U)]

BLANK_REFS = [('', '', '')]
bt_dark = []
bt_med = []
bt_work = []

# Info
credentials = ['', '']

sort_items = ('Name', 'Views A', 'Views U', 'Clones A', 'Clones U', 'Referrers', 'Reverse')
sort_item = 'Name'

board_types = ('Basic', 'Graph', 'Under', 'Compact', 'Referrer', 'Full')
board_type = 'Compact'

HELP_TEXT = [('KipHub Traffic\n'
              'v2.0\n\n', WHITE),
             ('Getting started\n', WB_DEEP),
             ('When running for the first time, KipHub Traffic will ask for a GitHub username.\n'
              'After that you must enter a valid, current GitHub API token with access to repository info.\n'
              'Get the token on the GitHub page at Settings > Developer settings > Personal access tokens (classic) ticking the repo checkmark.\n'
              'You can now download the GitHub data on Menu > Settings > Fetch from GitHub.\n'
              'This is where you download updated GitHub data whenever you need.\n'
              'Remember, the whole purpose of this program is to keep track of the data past the 14 days maximum on the GitHub page, so always fetch the data on intervals shorter than this period.\n\n', WHITE),
             ('The interface\n', WB_DEEP),
             ('The interface is composed of a menu bar, a header, a repository body and footer.\n\n', WHITE),
             ('The Menu\n', WB_DEEP),
             ('The menu offers complimentary actions to help the use of KipHub Traffic.\n'
              'The File menu deals mostly with configuration. Most of the configuration done on KipHub Can be saved and restored later. You can create several custom configurations according to your taste or to better view certain aspects of the information in a way or another.\n'
              'You can revert the configuration to the default one. Open a specific configuration file, quick open previously saved configurations, save a default configuration and save the current configuration to a different configuration file. Here you can also Exit the program.\n'
              'The Settings menu is where you can enter a new token for the user (creating expiring tokens is a good practice), fetch new data from GitHib, amd show the API usage ratios. Here you can also configure some more obscure settings like small and large gaps show between the boards (Basic and Graph boards use the small separator, the rest use the large one), the delay of the tooltips (all in Deep Config), restore the width of the interface to the default size and enable or disable the tooltips.\n'
              'In the Info menu you have information about KeepHub Traffic, a help window and you can display statistics about the repositories regarding the current period.\n'
              'The statistic window show the most hits on a day and the average daily hits for each category (View All, View Uniques, Clones All, Clones Uniques) in the current period. It also show compiled information regarding all repositories. Average average show the average for all days averages and Sum average shows the sum of all hits averaged for the period. You can call several statistic windows for different periods for comparison.\n\n', WHITE),
             ('The Header\n', WB_DEEP),
             ('The header shows the username, the amount of repositories under that user, the last date the data was updated, how many days ago was the update (remember, after 14 days you start to lose data. the program will highlight this number in yellow and then in red to warn about the deadline), the first day of the shown data, the last day of the period and how many days are being shown.\n'
              'You can change the initial and final dates by clicking on their icons (they cannot go earlier or later than the available data). Enter the date by clicking on the date widget or by entering a date below. The date format is y-m-d, m-d, or only d. The current period will be taken for the omitted ones. Years can have 2 or 4 digits.\n'
              'Clicking in the days period will bring some options:\n'
              'Disabled will turn on or of the enforcing of how many days are shown. If the period is enabled (unchecked) the current period of days entered will almost always be enforced (some actions might disable or enable this without notification).\n'
              'Last day will take the ending date to the last date available.\n'
              'The slider under Last day will set the desired period to show (this will only take effect when the period is enabled). Control/Command clicking this allows for manual entry.\n'
              'All days takes the initial and final date to the earliest and latest available dates on the data, showing all available days at once.\n\n', WHITE),
             ('The Body\n', WB_DEEP),
             ('The body show boards with information about each repository. They can be Basic, Graph, Under, Compact, Referrer, Full.\n'
              'The position of the information is different on each board ans not all of them show all information available.\n'
              'The boards have a header with the name of the repository, a button <> to send the date period of this board (when zoomed) to all boards, and a combo box to change the type of this board.\n'
              'GitHub provides information about the views and clones of each repository. This information is further detailed in "al" and "uniques". All is the total amount of views or clones on the repository. Uniques are the how many unique persons viewed or cloned the repository. All and Uniques are represented by ALL and UNQ.\n'
              'GitHub provides information in two ways, a daily report detailing numbers for each day and a reported sum of the last 14 days (these numbers not always match). KipHub Traffic show all this information for comparison. GitHub also report the referrers (where visitors came from) from the last 14 days, all and unique, this information is also shown.\n'
              'The daily collect data is color coded, View All is blue, View Uniques is orange, Clones All is green and Clones Uniques is red. You can click on each color to toggle each graphic view on the plot.\n'
              'The plot can be manipulated in a number of ways. It can be dragged in all directions, can be zoomed in or out with the mouse wheel (placing the mouse on the X or Y labels while zooming will affect only this axis), double click will reset the view and the right mouse button can be used to drag a region to zoom or to call a menu with several options.\n\n', WHITE),
             ('The Footer\n', WB_DEEP),
             ('The footer is mostly about configuring the viewing of the information. There are combo boxes to change all boards to a certain type, a combo box with several options to sort the repositories (there is an entry to Revert the sorts), toggles for all four graphics that affects all repositories, button to configure the plots where you can change the intensity of the graphics fill, the height of the plots and if you want to see the dates on the X axis. There is also a filter box where you can enter text to filter which repositories are shown. A box next to it have all repository names as a shortcut for the filter and there is a button to clear the filter box.\n\n', WHITE),
             ('Resetting the User\n', WB_DEEP),
             ('If you want reset the user on KipHub Traffic, you must delete (or backup) all files inside \\JSONs and run KipHub Traffic Again.\n'
              'A multi user version might come in the future.', WHITE)]


# Early functions (used by the initialization)
def dateEntry(date_entry, date_type, sender=None):
    '''Check the date entry format and convert to a valid datetime
       date_entry = the entry to check
       date_type = the type of date (begin or end) to report on errors'''
    if date_entry:
        if not re.match(match_date, date_entry):
            if sender:
                dpg.focus_item(sender)
                return
            else:
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
            date_entry = datetime.strptime(date_entry, r'%Y-%m-%d')
        except ValueError:
            if sender:
                dpg.focus_item(sender)
                return
            else:
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
ap.add_argument('-m', '--mono', action='store_true', default=mono,
                help='Show terminal output without colors')
ap.add_argument('-g', '--gui', action='store_false', default=gui,
                help='Show GUI instead of terminal output')

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

# Apply to variables
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
if args.mono:
    # Reset colors
    CYAN = ''
    YELLOW = ''
    GREEN = ''
    RED = ''
    BLUE = ''
    GRAY = ''
    MAGENTA = ''
    RESET = ''


# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------
@dataclass
class Users:
    '''Username and token.'''
    users: list
    default_user: str


@dataclass
class Credentials:
    '''Username and token.'''
    username: str
    token: str


@dataclass
class Config:
    '''Configuration.'''
    date_days: int
    disable_days: bool
    plot_alpha: int
    plot_height: int
    show_dates: bool
    board_type: str
    sort_item: str
    sort_reverse: bool
    repo_filter: str
    tooltips_show: bool
    tooltips_delay: float
    show_views_a: bool
    show_views_u: bool
    show_clones_a: bool
    show_clones_u: bool
    small_separator: int
    large_separator: int


@dataclass
class DataHead:
    '''Header items.'''
    repositories: int
    repo_names: list
    last_updated: datetime
    earliest_day: datetime
    latest_day: datetime
    days_ago: int
    date_from: datetime
    date_to: datetime
    date_days: int
    time_period: list
    day_peak: list


@dataclass
class DataBody:
    '''Board items.'''
    repository: str
    referrers: list
    rep_view_a: int
    rep_view_u: int
    rep_clone_a: int
    rep_clone_u: int
    views_a: list
    views_u: list
    clones_a: list
    clones_u: list
    col_view_a: int
    col_view_u: int
    col_clone_a: int
    col_clone_u: int


class Boards:
    '''Repository boards'''
    def __init__(self, data_board, output_head, config, repo_filter_tag):
        self.data_board = data_board
        self.output_head = output_head

        self.board_tooltip = []
        self.board_type = config.board_type
        self.repo_filter_tag = repo_filter_tag

        self.plot_height = config.plot_height
        self.show_dates = config.show_dates
        self.show_views_a = config.show_views_a
        self.show_views_u = config.show_views_u
        self.show_clones_a = config.show_clones_a
        self.show_clones_u = config.show_clones_u
        self.small_separator = config.small_separator
        self.large_separator = config.large_separator

        self.create_board_groups()

    # -----------------------------------------------------------------------------
    # Board Functions
    # -----------------------------------------------------------------------------
    def create_board_groups(self):
        self._group = dpg.add_group(filter_key=self.data_board.repository, parent=self.repo_filter_tag)

    def populate_boards(self, board_type):
        self.separator = self.small_separator
        self.board_tooltip = []

        if board_type:
            self.board_type = board_type

        self.button_theme_view_a = 'button_view_a' if self.show_views_a else 'button_working'
        self.button_theme_view_u = 'button_view_u' if self.show_views_u else 'button_working'
        self.button_theme_clone_a = 'button_clone_a' if self.show_clones_a else 'button_working'
        self.button_theme_clone_u = 'button_clone_u' if self.show_clones_u else 'button_working'

        if self.board_type == 'Basic' or self.board_type == 'Graph':

            width = -260 if self.board_type == 'Graph' else -260
            visibility = self.board_type == 'Graph'

            with dpg.group(horizontal=True, parent=self._group):
                self.insert_header(width=width, buttons=True)

            with dpg.group(parent=self._group, show=visibility):
                with dpg.child_window(width=-1, height=80 + self.plot_height * 28):
                    self.insert_plot(height=80)

        elif self.board_type == 'Compact':
            self.separator = self.large_separator

            with dpg.group(horizontal=True, parent=self._group):
                self.insert_header(width=-76)

            with dpg.group(horizontal=True, parent=self._group):
                with dpg.child_window(width=-154, height=170 + self.plot_height * 28):
                    self.insert_plot(height=167)

                with dpg.child_window(no_scrollbar=True, no_scroll_with_mouse=True, height=168 + self.plot_height * 28):
                    self.insert_label(label=f'Collected {self.output_head.date_days} days', width=153, theme='button_dark', au=False, tooltip='collect')
                    self.insert_btn_view_col(61)
                    self.insert_btn_clone_col(61)
                    self.insert_label(label='Reported 14 days', width=153, theme='button_dark', au=False, tooltip='report')
                    self.insert_btn_view_ref(61)
                    self.insert_btn_clone_ref(61)
                    dpg.add_button(width=153, height=-1)
                    dpg.bind_item_theme(dpg.last_item(), 'button_med')

        elif self.board_type == 'Under':
            self.separator = self.large_separator

            with dpg.group(horizontal=True, parent=self._group):
                self.insert_header(width=-76)

            with dpg.group(parent=self._group):
                with dpg.child_window(width=-1, height=251 + self.plot_height * 28, border=False):
                    self.insert_plot(height=167)

                    with dpg.group(horizontal=True):
                        with dpg.group():
                            with dpg.group(horizontal=True):
                                self.insert_label(label=f'Collected in {self.output_head.date_days} days', width=180, theme='button_dark', au=True, tooltip='collect')
                                self.insert_label(label='Reported last 14 days', width=180, theme='button_dark', au=True, tooltip='report')
                                self.insert_label(label='Referrers', width=100, theme='button_med', au=True, grow_x=True)

                            with dpg.group(horizontal=True):
                                with dpg.group():
                                    with dpg.group(horizontal=True):
                                        self.insert_btn_view_col(180)
                                        self.insert_btn_view_ref(180)

                                    with dpg.group(horizontal=True):
                                        self.insert_btn_clone_col(180)
                                        self.insert_btn_clone_ref(180)

                                self.insert_referrers(amount=2, y_span=55, grow_y=False, grow_x=True)

        elif self.board_type == 'Referrer':
            self.separator = self.large_separator

            with dpg.group(horizontal=True, parent=self._group):
                self.insert_header(width=-76)

            with dpg.group(horizontal=True, parent=self._group):
                with dpg.group():
                    with dpg.child_window(width=-199, height=251 + self.plot_height * 28, border=False):
                        self.insert_plot(height=167)

                        with dpg.group(horizontal=True):
                            with dpg.group():
                                with dpg.group(horizontal=True):
                                    self.insert_label(label=f'Collected in {self.output_head.date_days} days', width=190, theme='button_dark', au=True, tooltip='collect')
                                    self.insert_label(label='Reported last 14 days', width=190, theme='button_dark', au=True, tooltip='report')

                                with dpg.group(horizontal=True):
                                    self.insert_btn_view_col(190)
                                    self.insert_btn_view_ref(190)

                                with dpg.group(horizontal=True):
                                    self.insert_btn_clone_col(190)
                                    self.insert_btn_clone_ref(190)

                            dpg.add_button(width=-1, height=83)
                            dpg.bind_item_theme(dpg.last_item(), 'button_med')

                with dpg.group():
                    self.insert_label(label='Referrers', width=106, theme='button_med', au=True)
                    self.insert_referrers(amount=8, y_span=224, grow_y=True, grow_x=True)

        elif self.board_type == 'Full':

            self.separator = self.large_separator
            with dpg.group(horizontal=True, parent=self._group):
                self.insert_header(width=-76)

            with dpg.group(horizontal=True, parent=self._group):
                with dpg.child_window(width=-199, height=251 + self.plot_height * 28, border=False):
                    self.insert_plot(height=251)

                with dpg.group():
                    self.insert_label(label=f'Collected in {self.output_head.date_days} days', width=198, theme='button_dark', au=False, tooltip='collect')
                    self.insert_btn_view_col(106)
                    self.insert_btn_clone_col(106)
                    self.insert_label(label='Reported last 14 days', width=198, theme='button_dark', au=False, tooltip='report')
                    self.insert_label(label='Referrers', width=106, theme='button_med', au=True)
                    self.insert_referrers(amount=2, y_span=55, grow_y=True)
                    self.insert_btn_view_ref(106)
                    self.insert_btn_clone_ref(106)

        self.board_separator = dpg.add_child_window(height=self.separator, parent=self._group)

        self.board_tooltip.append(dpg.add_tooltip(self.data_board.repository))
        dpg.add_text(parent=dpg.last_item(), default_value='Send this date range to all repos')
        self.board_tooltip.append(dpg.add_tooltip(f'type_{self.data_board.repository}'))
        dpg.add_text(parent=dpg.last_item(), default_value='Change information layout for this repository')
        self.board_tooltip.append(dpg.add_tooltip(f'view_a_{self.data_board.repository}'))
        dpg.add_text(parent=dpg.last_item(), default_value='Toggle the View All graph on this repository')
        self.board_tooltip.append(dpg.add_tooltip(f'view_u_{self.data_board.repository}'))
        dpg.add_text(parent=dpg.last_item(), default_value='Toggle the View Unique graph on this repository')
        self.board_tooltip.append(dpg.add_tooltip(f'clone_a_{self.data_board.repository}'))
        dpg.add_text(parent=dpg.last_item(), default_value='Toggle the Clone All graph on this repository')
        self.board_tooltip.append(dpg.add_tooltip(f'clone_u_{self.data_board.repository}'))
        dpg.add_text(parent=dpg.last_item(), default_value='Toggle the Clone Unique graph on this repository')
        if dpg.does_alias_exist(f'collect_{self.data_board.repository}'):
            self.board_tooltip.append(dpg.add_tooltip(f'collect_{self.data_board.repository}'))
            dpg.add_text(parent=dpg.last_item(), default_value='Data collected daily for those last days')
        if dpg.does_alias_exist(f'report_{self.data_board.repository}'):
            self.board_tooltip.append(dpg.add_tooltip(f'report_{self.data_board.repository}'))
            dpg.add_text(parent=dpg.last_item(), default_value='Data bundle reported for the last 14 days')

        for tt in self.board_tooltip:
            dpg.configure_item(tt, hide_on_activity=True, delay=config.tooltips_delay, show=config.tooltips_show)
            dpg.bind_item_theme(tt, 'check_and_tooltips')

    def change_board(self, sender, app_data):
        dpg.delete_item(self._group, children_only=True)
        self.populate_boards(app_data)

    def sort_boards(self):
        dpg.move_item(self._group, parent=self.repo_filter_tag)

    # -----------------------------------------------------------------------------
    # Create Functions
    # -----------------------------------------------------------------------------
    def insert_plot(self, height):
        with dpg.plot(anti_aliased=True, height=height + (self.plot_height * 28), width=-1):
            dpg.bind_item_theme(dpg.last_item(), 'plot')

            # dpg.add_plot_legend()
            self.x_axis = dpg.add_plot_axis(dpg.mvXAxis, time=True, no_tick_labels=not self.show_dates)
            self.y_axis = dpg.add_plot_axis(dpg.mvYAxis)

            self.grp_view_a = dpg.add_line_series(self.output_head.time_period, self.data_board.views_a, label="Views All", parent=self.y_axis, show=self.show_views_a)
            dpg.bind_item_theme(dpg.last_item(), 'button_view_a')
            self.grp_view_u = dpg.add_line_series(self.output_head.time_period, self.data_board.views_u, label="Views Unique", parent=self.y_axis, show=self.show_views_u)
            dpg.bind_item_theme(dpg.last_item(), 'button_view_u')
            self.grp_clone_a = dpg.add_line_series(self.output_head.time_period, self.data_board.clones_a, label="Clones All", parent=self.y_axis, show=self.show_clones_a)
            dpg.bind_item_theme(dpg.last_item(), 'button_clone_a')
            self.grp_clone_u = dpg.add_line_series(self.output_head.time_period, self.data_board.clones_u, label="Clones Unique", parent=self.y_axis, show=self.show_clones_u)
            dpg.bind_item_theme(dpg.last_item(), 'button_clone_u')

            self.grp_view_a_f = dpg.add_shade_series(self.output_head.time_period, self.data_board.views_a, label="Views All", parent=self.y_axis, show=self.show_views_a)
            dpg.bind_item_theme(dpg.last_item(), 'button_view_a')
            self.grp_view_u_f = dpg.add_shade_series(self.output_head.time_period, self.data_board.views_u, label="Views Unique", parent=self.y_axis, show=self.show_views_u)
            dpg.bind_item_theme(dpg.last_item(), 'button_view_u')
            self.grp_clone_a_f = dpg.add_shade_series(self.output_head.time_period, self.data_board.clones_a, label="Clones All", parent=self.y_axis, show=self.show_clones_a)
            dpg.bind_item_theme(dpg.last_item(), 'button_clone_a')
            self.grp_clone_u_f = dpg.add_shade_series(self.output_head.time_period, self.data_board.clones_u, label="Clones Unique", parent=self.y_axis, show=self.show_clones_u)
            dpg.bind_item_theme(dpg.last_item(), 'button_clone_u')

            # Y axis becomes crowded when y is very high. It do not occlude intermediary labels.
            # dpg.set_axis_ticks(self.y_axis, tuple(self.output_head.day_peak))

    def insert_header(self, width, buttons=False):
        with dpg.child_window(height=28, width=width, border=False):
            with dpg.group(horizontal=True):
                # width = 483 if buttons else 667
                dpg.add_button(label='Repo', width=60)
                dpg.bind_item_theme(dpg.last_item(), 'button_dark')
                dpg.add_input_text(default_value=self.data_board.repository, width=-1, readonly=True)
                dpg.bind_item_theme(dpg.last_item(), 'pad_text')

        with dpg.child_window(height=28, border=False):
            with dpg.group(horizontal=True):
                if buttons:
                    self.insert_btn_view_col(0)
                    self.insert_btn_clone_col(0)

                dpg.add_button(label='<>', width=30, tag=self.data_board.repository)
                dpg.bind_item_handler_registry(dpg.last_item(), 'date_handler')
                dpg.bind_item_theme(dpg.last_item(), 'button_working')

                dpg.add_combo(board_types, default_value=self.board_type, width=45, callback=self.change_board, tag=f'type_{self.data_board.repository}')
                dpg.bind_item_theme(dpg.last_item(), 'button_working')

    def insert_referrers(self, amount, y_span, grow_y, grow_x=False):
        child_w = -1 if grow_x else 198
        grow_height = self.plot_height if grow_y else 0

        with dpg.child_window(width=child_w, height=y_span + (grow_height * 28)):

            referrer_list = self.data_board.referrers.copy()
            if len(referrer_list) > 1:
                t_all = 0
                t_unq = 0
                for item in referrer_list:
                    t_all += int(item[1])
                    t_unq += int(item[2])
                referrer_list.append(('TOTAL', t_all, t_unq))

            for referrer, blank in zip_longest(referrer_list, BLANK_REFS * (amount + grow_height)):
                with dpg.group(horizontal=True):
                    if referrer:
                        ref_ref = referrer[0]
                        ref_all = referrer[1]
                        ref_unq = referrer[2]
                    else:
                        ref_ref = blank[0]
                        ref_all = blank[1]
                        ref_unq = blank[2]
                    dpg.add_input_text(default_value=ref_ref, width=-92, readonly=True)
                    dpg.add_button(label=ref_all, width=45)
                    dpg.add_button(label=ref_unq, width=45)

    def insert_label(self, label, width, theme, au, grow_x=False, tooltip=None):
        ref_r_w = -93 if grow_x else width
        ref_a_w = -47 if grow_x else 45
        ref_u_w = -1 if grow_x else 45
        with dpg.group(horizontal=True):
            if tooltip:
                dpg.add_button(label=label, width=ref_r_w, tag=f'{tooltip}_{self.data_board.repository}')
                # print(f'{tooltip}_{self.data_board.repository}')
            else:
                dpg.add_button(label=label, width=ref_r_w)
            dpg.bind_item_theme(dpg.last_item(), theme)
            if au:
                dpg.add_button(label='ALL', width=ref_a_w)
                dpg.add_button(label='UNQ', width=ref_u_w)
                dpg.bind_item_theme(dpg.last_container(), 'button_med')

    def insert_btn_view_ref(self, size):
        with dpg.group(horizontal=True):
            if size:
                dpg.add_button(label='Views', width=size)
                dpg.bind_item_theme(dpg.last_item(), 'button_med')
            dpg.add_button(label=self.data_board.rep_view_a, width=45)
            dpg.add_button(label=self.data_board.rep_view_u, width=45)

    def insert_btn_clone_ref(self, size):
        with dpg.group(horizontal=True):
            if size:
                dpg.add_button(label='Clones', width=size)
                dpg.bind_item_theme(dpg.last_item(), 'button_med')
            dpg.add_button(label=self.data_board.rep_clone_a, width=45)
            dpg.add_button(label=self.data_board.rep_clone_u, width=45)

    def insert_btn_view_col(self, size):
        with dpg.group(horizontal=True):
            if size:
                dpg.add_button(label='Views', width=size)
                dpg.bind_item_theme(dpg.last_item(), 'button_med')
            self.btn_view_a = dpg.add_button(label=self.data_board.col_view_a, width=45, callback=self.toggle_graph_view_a, tag=f'view_a_{self.data_board.repository}')
            dpg.bind_item_theme(dpg.last_item(), self.button_theme_view_a)
            self.btn_view_u = dpg.add_button(label=self.data_board.col_view_u, width=45, callback=self.toggle_graph_view_u, tag=f'view_u_{self.data_board.repository}')
            dpg.bind_item_theme(dpg.last_item(), self.button_theme_view_u)

    def insert_btn_clone_col(self, size):
        with dpg.group(horizontal=True):
            if size:
                dpg.add_button(label='Clones', width=size)
                dpg.bind_item_theme(dpg.last_item(), 'button_med')
            self.btn_clone_a = dpg.add_button(label=self.data_board.col_clone_a, width=45, callback=self.toggle_graph_clone_a, tag=f'clone_a_{self.data_board.repository}')
            dpg.bind_item_theme(dpg.last_item(), self.button_theme_clone_a)
            self.btn_clone_u = dpg.add_button(label=self.data_board.col_clone_u, width=45, callback=self.toggle_graph_clone_u, tag=f'clone_u_{self.data_board.repository}')
            dpg.bind_item_theme(dpg.last_item(), self.button_theme_clone_u)

    # -----------------------------------------------------------------------------
    # Plot Functions
    # -----------------------------------------------------------------------------
    def change_plot_height(self, sender, app_data, user_data):
        self.plot_height = app_data
        self.change_board(None, None)

    def toggle_graph_view_a(self):
        self.show_views_a = not self.show_views_a
        self.change_board(None, None)

    def toggle_graph_view_u(self):
        self.show_views_u = not self.show_views_u
        self.change_board(None, None)

    def toggle_graph_clone_a(self):
        self.show_clones_a = not self.show_clones_a
        self.change_board(None, None)

    def toggle_graph_clone_u(self):
        self.show_clones_u = not self.show_clones_u
        self.change_board(None, None)

    def toggle_x_label(self, hide_x_labels):
        self.show_dates = hide_x_labels
        dpg.configure_item(self.x_axis, no_tick_labels=not self.show_dates)


# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------
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


def saveData(data_file, data, credentials=None):
    '''Save the consolidated JSON
    data_file = the JSON to save'''

    if credentials:
        username = credentials[0]

    if os.path.exists(data_file):
        shutil.copy(f'JSONs/{username}.json', f'JSONs/{username}_bkp.json')
    with open(data_file, 'w') as f:
        json.dump(data, f, indent=4)


def getAPIdata(url, file=None, use_cache=use_cache, credentials=None, rate=False):
    '''Get API JSON data from the web or a cached file
       url = API point location
       file = JSON file to load or save
       use_cache = if True will load the file from disk'''

    global repo_count
    global repo_max
    global username
    global token

    if credentials:
        username = credentials[0]
        token = credentials[1]

    # create a re-usable session object with the user creds in-built
    gh_session = requests.Session()
    gh_session.auth = (username, token)

    if not use_cache:
        if not rate:
            if credentials:
                if not dpg.get_item_configuration('error')['show']:
                    return None, 'Fetching interrupted'
                dpg.configure_item('error_text', default_value=f'Fetching {url}')
                repo_count += 1
                if repo_max > 0:
                    dpg.set_value('progress_repos', 1 / repo_max * repo_count)
                    dpg.configure_item('progress_repos', overlay=f"{repo_count}/{repo_max}")
            else:
                print(f'Fetching {url}')

        response = json.loads(gh_session.get(url).text)

        # Response error
        if type(response) is dict:
            message = response.get('message', None)
            if message:
                if credentials:
                    error = 'API error\n'
                    for key in response:
                        print(key)
                        error += f'\n{key}: {response[key]}'
                    error += f'\n\n{response}'
                    return error, True
                else:
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

    return response, None


def gatherData(traffic_data, credentials=None):
    '''Consolidate all the API responses into a single JSON
       merging with a previous consolidated JSON
       traffic_data = the previous JSON'''

    def gatherViewClone(data_type):
        '''Read and format the repository information from views or clones
           data_type = if 'views' or 'clones' '''

        data, error = getAPIdata(f'{base_url}/{username}/{repo_name}/traffic/{data_type}',
                                 f'JSONs/{repo_name}_{data_type}.json',
                                 credentials=credentials)

        if error:
            return error, True

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

    global repo_count
    global repo_max
    global username

    repo_max = 0
    repo_count = 0

    if credentials:
        username = credentials[0]

    # Finds previous repo names and indexes them
    repos_dict = {}
    for count, repo in enumerate(traffic_data):
        repos_dict[repo['name']] = count

    repos, error = getAPIdata(repos_url, 'JSONs/repos.json', credentials=credentials)
    if error:
        return repos, True

    repo_names = [(repo['name']) for repo in repos if repo['owner']['login'] == username]

    repo_max = len(repo_names) * 3

    for repo_name in repo_names:
        repo_index = None
        if repo_name in repos_dict:
            repo_index = repos_dict[repo_name]

        referrers, error = getAPIdata(f'{base_url}/{username}/{repo_name}/{referrers_url}',
                                      f'JSONs/{repo_name}_referrers.json',
                                      credentials=credentials)

        if error:
            return error, True

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

    return traffic_data, None


# -----------------------------------------------------------------------------
# Terminal Section
# -----------------------------------------------------------------------------
def buildConsoleOutput(traffic_data):
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
                min_tmp = datetime.strptime(days_list[0][0], r'%Y-%m-%d')
                max_tmp = datetime.strptime(days_list[-1][0], r'%Y-%m-%d')
                min_day = min(min_day, min_tmp)
                max_day = max(max_day, max_tmp)
        return min_day, max_day

    def buildViewClone(data_type):
        '''Assemble and shows the data for the views and the clones
           data_type = if 'views' or 'clones' '''

        repo_parc = []
        l_title = f'{BLUE}{data_type.capitalize()}:'
        tot_c = 0
        tot_u = 0
        l_days = ''
        l_count = f' {BLUE}Cnt: '
        l_uniqu = f' {BLUE}Unq: '
        p_days = ''
        p_count = ''
        p_uniqu = ''

        report = (f' {CYAN}Count: {GREEN}{repo[data_type]["count"]}'
                  f' {CYAN}Uniques: {GREEN}{repo[data_type]["uniques"]}'
                  f' {GRAY}(last 14 days){RESET}')

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
                p_days += f'{BLUE}{separator}{CYAN}{str(c_day).zfill(2)}'
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
                report = f' {BLUE}Total'
        l_title += report

        if show_daily:
            if Show_labels:
                l_days = f' {BLUE}Day:{p_days}'
            l_count += GREEN + p_count
            l_uniqu += GREEN + p_uniqu

        if show_sum:
            if show_daily:
                l_days += f'  {BLUE}Sum'
            if show_report and not show_daily:
                l_days = f'       {BLUE}Total'
            l_count += f' {MAGENTA}{str(tot_c)}'
            l_uniqu += f' {MAGENTA}{str(tot_u)}'

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
    repo_head.append(f'{GREEN}{username} {BLUE}has {GREEN}{len(traffic_data)} {BLUE}GitHub repositories')
    repo_head.append(f'Last updated in {GREEN}{last_date_str} {BLUE}- {GREEN}{date_diff_str} {BLUE}days ago')
    repo_head.append(f'{GREEN}{interval.days + 1} {BLUE}days, from {GREEN}{min_day.date()} {BLUE}to {GREEN}{max_day.date()}')

    repo_list = []
    for repo in traffic_data:
        l_repo = (f'{BLUE}Repo: {RED}{repo["name"]}')

        # Assemble referrers
        l_referers = None
        if len(repo['referrers']) > 0 and show_referers:
            l_ref_expand = ''
            refs_start = ''
            refs_middle = ''
            refs_end = f'{GRAY}(last 14 days)'
            if not expand_referers:
                refs_start = f' {GRAY}(last 14 days)'
                refs_middle = '\n'
                refs_end = ''

            for referrer in repo['referrers']:
                l_ref_expand += (f'{refs_middle}'
                                 f' {GREEN}{referrer["name"]}:'
                                 f' {CYAN}Count: {GREEN}{referrer["count"]}'
                                 f' {CYAN}Uniques: {GREEN}{referrer["uniques"]}')

            l_referers = f'{BLUE}Referrers:{CYAN}{refs_start}{l_ref_expand} {refs_end}'

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


def showConsoleOutput(repo_list, repo_head):
    for output in repo_list:
        for item in output[:10]:
            if item:
                print(item)
        print()

    for item in repo_head:
        print(item)
    print(RESET)


# -----------------------------------------------------------------------------
# GUI Section
# -----------------------------------------------------------------------------
def no_traffic():
    output_head = DataHead(repositories=0,
                           repo_names=[],
                           last_updated=datetime.today(),
                           earliest_day=datetime.today(),
                           latest_day=datetime.today(),
                           days_ago=0,
                           date_from=datetime.today(),
                           date_to=datetime.today(),
                           date_days=14,
                           time_period=[],
                           day_peak=[])

    output_boards = None

    return output_head, output_boards


def buildGUIOutput(traffic_data):

    def getMinMaxdate(data_type, min_day, max_day):
        '''Get the earlier and later days in the views and clones data
           data_type = if 'views' or 'clones'
           min_day = the earlier day in the data
           max_day = the later day in the data'''
        max_hit = []
        for repo in traffic_data:
            if repo[data_type]['count'] > 0 or repo[data_type]['uniques'] > 0:
                # Convert the dictionary into a list to be able to sort it
                days_list = list(repo[data_type]['days'].items())
                days_list = sorted(days_list)
                min_tmp = datetime.strptime(days_list[0][0], r'%Y-%m-%d')
                max_tmp = datetime.strptime(days_list[-1][0], r'%Y-%m-%d')
                min_day = min(min_day, min_tmp)
                max_day = max(max_day, max_tmp)
                max_hit.append(max_tmp)
        max_day = max(max_hit)
        return min_day, max_day

    def buildGraphData(data_type):
        tot_a = 0
        tot_u = 0
        day_a = []
        day_u = []
        time_period = []
        day_peak = 0
        for d in range(interval.days + 1):
            day = min_day + timedelta(days=d)
            day_str = day.strftime(r'%Y-%m-%d')
            unix_time = int(datetime.timestamp(day))
            time_period.append(unix_time)
            if day_str in repo[data_type]['days']:
                day_total = repo[data_type]['days'][day_str][0]
                [day_str][0]
                tot_a += day_total
                day_a.append(day_total)

                day_peak = max(day_peak, day_total)

                day_total = repo[data_type]['days'][day_str][1]
                tot_u += day_total
                day_u.append(day_total)

                day_peak = max(day_peak, day_total)

            else:
                day_a.append(0)
                day_u.append(0)

        return (day_a, day_u, tot_a, tot_u, time_period, day_peak)

    last_date_str = traffic_data[0]['updated']
    min_day = max_day = last_date = datetime.strptime(last_date_str, '%Y-%m-%d')

    min_day_v, max_day_v = getMinMaxdate('views', min_day, max_day)
    min_day_c, max_day_c = getMinMaxdate('clones', min_day, max_day)

    min_day = min(min_day_c, min_day_v)
    max_day = max(max_day_c, max_day_v)

    earliest_day = min_day
    latest_day = max_day

    min_day = max_day - timedelta(config.date_days - 1)

    if min_cust and config.disable_days:
        min_day = min_cust if min_cust > earliest_day else earliest_day
    if max_cust:
        max_day = max_cust if max_cust < latest_day else latest_day
    if not config.disable_days:
        min_day = max(max_day - timedelta(config.date_days - 1), earliest_day)

    interval = max_day - min_day

    date_diff = date.today() - last_date.date()
    date_diff_str = date_diff.days

    output_head = DataHead(repositories=len(traffic_data),
                           repo_names=[],
                           last_updated=last_date,
                           earliest_day=earliest_day,
                           latest_day=latest_day,
                           days_ago=int(date_diff_str),
                           date_from=min_day,
                           date_to=max_day,
                           date_days=interval.days + 1,
                           time_period=[],
                           day_peak=[])

    day_peak = 0
    repo_names = []
    output_boards = []
    for repo in traffic_data:
        referrers = []

        repo_names.append(repo['name'])

        for refs in repo['referrers']:
            if refs:
                referrers.append((refs['name'], refs['count'], refs['uniques']))

        views_rep = repo['views']
        clones_rep = repo['clones']

        views_graph = buildGraphData('views')
        clones_graph = buildGraphData('clones')

        repo_peak = max(views_graph[5], clones_graph[5])
        day_peak = max(repo_peak, day_peak)

        output_boards.append(DataBody(repository=repo['name'],
                                      referrers=referrers,
                                      rep_view_a=views_rep['count'],
                                      rep_view_u=views_rep['uniques'],
                                      rep_clone_a=clones_rep['count'],
                                      rep_clone_u=clones_rep['uniques'],
                                      views_a=views_graph[0],
                                      views_u=views_graph[1],
                                      clones_a=clones_graph[0],
                                      clones_u=clones_graph[1],
                                      col_view_a=views_graph[2],
                                      col_view_u=views_graph[3],
                                      col_clone_a=clones_graph[2],
                                      col_clone_u=clones_graph[3]))

    tick_labels = []
    for tick in range(day_peak):
        tick_labels.append((str(tick), float(tick)))

    repo_names.sort(key=lambda x: x.lower())

    output_head.repo_names = repo_names
    output_head.time_period = clones_graph[4]
    output_head.day_peak = tick_labels

    return output_head, output_boards


def showGUIOutput():

    dpg.create_context()

    global gui_loaded
    global min_cust
    global max_cust
    global cred_file
    global data_file
    global config_path
    global tooltips
    global config_files
    global traffic
    global config
    global users
    global output_head
    global output_boards
    global body_group

    # -----------------------------------------------------------------------------
    # Date functions
    # -----------------------------------------------------------------------------

    def pick_date_from():

        max_c = max_cust

        if (convert_from_date_picker(dpg.get_value('picker_from')) >= max_cust) and config.disable_days:
            min_c = max_cust - timedelta(1)

        elif convert_from_date_picker(dpg.get_value('picker_from')) < output_head.earliest_day:
            min_c = output_head.earliest_day

        elif convert_from_date_picker(dpg.get_value('picker_from')) >= output_head.latest_day:
            min_c = output_head.latest_day - timedelta(1)
        else:
            min_c = convert_from_date_picker(dpg.get_value('picker_from'))

        if not config.disable_days:
            max_c = min_c + timedelta(period - 1)

        apply_dates(min_c, max_c)

    def pick_date_to():

        if (convert_from_date_picker(dpg.get_value('picker_to')) <= min_cust) and config.disable_days:
            max_c = min_cust + timedelta(1)

        elif convert_from_date_picker(dpg.get_value('picker_to')) <= output_head.earliest_day:
            max_c = output_head.earliest_day + timedelta(1)

        elif convert_from_date_picker(dpg.get_value('picker_to')) > output_head.latest_day:
            max_c = output_head.latest_day

        else:
            max_c = convert_from_date_picker(dpg.get_value('picker_to'))

        apply_dates(min_cust, max_c)

    def input_date_from(sender, app_data, user_data):
        date = dateEntry(app_data, 'From', sender)
        if date:
            dpg.configure_item('picker_from', default_value=convert_to_date_picker(date))
            pick_date_from()

    def input_date_to(sender, app_data, user_data):
        date = dateEntry(app_data, 'To', sender)
        if date:
            dpg.configure_item('picker_to', default_value=convert_to_date_picker(date))
            pick_date_to()

    def apply_dates(min_c, max_c):

        global min_cust
        global max_cust
        global output_head
        global output_boards

        min_cust = min_c
        max_cust = max_c

        output_head, output_boards = buildGUIOutput(traffic)

        min_cust = output_head.date_from
        max_cust = output_head.date_to

        dpg.configure_item('picker_from', default_value=convert_to_date_picker(output_head.date_from))
        dpg.configure_item('date_from', label=output_head.date_from.date())

        dpg.configure_item('picker_to', default_value=convert_to_date_picker(output_head.date_to))
        dpg.configure_item('date_to', label=output_head.date_to.date())

        dpg.configure_item('date_days', label=output_head.date_days)

        for board in body_group:
            board_data = next(item for item in output_boards if item.repository == board.data_board.repository)
            board.output_head = output_head
            board.data_board = board_data
            board.change_board(None, None)

        sum_boards()

    def toggle_days():
        global config

        config.disable_days = not config.disable_days
        dpg.configure_item('toggle_days', default_value=config.disable_days)

        if not config.disable_days:
            config.date_days = dpg.get_value('set_days')
            dpg.configure_item('toggle_days', default_value=config.disable_days)

            apply_dates(output_head.earliest_day, output_head.date_to)

    def last_day():
        apply_dates(output_head.date_from, output_head.latest_day)

    def spread_date(sender, app_data, user_data):
        # This is terrible. The only way I managed to get the repo from the clicked button on the
        # object was to assign the button a handler to access it outside the class, also assign
        # it a tag with the name of the repo, recover it here and look into the board list for
        # the correct object instance to get the dates.
        global config
        for board in body_group:
            if board.data_board.repository == dpg.get_item_alias(app_data[1]):
                day_from = datetime.fromtimestamp(dpg.get_axis_limits(board.x_axis)[0]).date() + timedelta(1)
                day_to = datetime.fromtimestamp(dpg.get_axis_limits(board.x_axis)[1]).date() + timedelta(1)

                day_from = datetime.combine(day_from, datetime.min.time())
                day_to = datetime.combine(day_to, datetime.min.time())

                config.disable_days = True
                dpg.configure_item('toggle_days', default_value=config.disable_days)

                apply_dates(day_from, day_to)

                break

    def change_days(sender, app_data):
        if config.disable_days:
            return

        config.date_days = dpg.get_value('set_days')

        apply_dates(output_head.earliest_day, output_head.date_to)

    def set_days(sender, app_data, user_data):
        config.disable_days = False
        dpg.configure_item('toggle_days', default_value=config.disable_days)

        config.date_days = user_data

        apply_dates(output_head.earliest_day, output_head.date_to)

    def all_days():
        global config

        config.disable_days = True
        dpg.configure_item('toggle_days', default_value=config.disable_days)

        apply_dates(output_head.earliest_day, output_head.latest_day)

    def convert_to_date_picker(date):
        date_day = date.day
        date_month = date.month - 1
        date_year = date.year - 1900
        return {'month_day': date_day, 'month': date_month, 'year': date_year}

    def convert_from_date_picker(date):
        date_day = date['month_day']
        date_month = date['month'] + 1
        date_year = date['year'] + 1900
        return datetime(date_year, date_month, date_day)

    # -----------------------------------------------------------------------------
    # Plot functions
    # -----------------------------------------------------------------------------

    def toggle_graph_all(sender, app_data, user_data):
        global config

        sender_alias = dpg.get_item_alias(dpg.get_item_theme(sender))
        for board in body_group:
            visibility = sender_alias != 'button_working'

            if sender == 'view_a':
                board.show_views_a = visibility
                board.toggle_graph_view_a()

            elif sender == 'view_u':
                board.show_views_u = visibility
                board.toggle_graph_view_u()

            elif sender == 'clone_a':
                board.show_clones_a = visibility
                board.toggle_graph_clone_a()

            elif sender == 'clone_u':
                board.show_clones_u = visibility
                board.toggle_graph_clone_u()

        config.show_views_a = sender_alias == 'button_working' if sender == 'view_a' else config.show_views_a
        config.show_views_u = sender_alias == 'button_working' if sender == 'view_u' else config.show_views_u
        config.show_clones_a = sender_alias == 'button_working' if sender == 'clone_a' else config.show_clones_a
        config.show_clones_u = sender_alias == 'button_working' if sender == 'clone_u' else config.show_clones_u

        button_theme = user_data if sender_alias == 'button_working' else 'button_working'
        dpg.bind_item_theme(sender, button_theme)

    def change_plot_height(sender, app_data, user_data):
        global config
        for board in body_group:
            board.change_plot_height(sender, app_data, user_data)
        config.plot_height = app_data

    def change_plot_alpha(sender, app_data):
        global config
        config.plot_alpha = app_data
        for graph in GRAPH_COLOR:
            plot_fill = (graph[1][0], graph[1][1], graph[1][2], app_data)
            with dpg.theme_component(dpg.mvAll, parent=graph[0]):
                dpg.add_theme_color(dpg.mvPlotCol_Fill, plot_fill, category=dpg.mvThemeCat_Plots)

    def toggle_x_labels(sender):
        global config
        config.show_dates = dpg.get_value(sender)
        for board in body_group:
            board.toggle_x_label(config.show_dates)

    # -----------------------------------------------------------------------------
    # Board functions
    # -----------------------------------------------------------------------------

    def filter_repos(sender, app_data):
        global config
        dpg.set_value('filter_box', app_data)
        dpg.set_value(sender, 'Repos')
        dpg.set_value("filter", app_data)
        config.repo_filter = app_data

    def filter_set(sender, app_data):
        global config
        dpg.set_value("filter", app_data)
        config.repo_filter = app_data

    def filter_clear():
        global config
        dpg.set_value('filter_box', '')
        dpg.set_value("filter", '')
        config.repo_filter = ''

    def create_boards():
        body_group = []
        for repo in output_boards:
            body_group.append(Boards(repo, output_head, config, repo_filter_tag))
        return body_group

    def populate_boards():
        for board in body_group:
            board.populate_boards(config.board_type)

    def sort_boards(sender, app_data):
        global config

        if app_data == 'Reverse':
            config.sort_reverse = not config.sort_reverse
            app_data = config.sort_item
            dpg.configure_item(sender, default_value=config.sort_item)
        else:
            config.sort_item = app_data

        if app_data == 'Name':
            body_group.sort(key=lambda x: x.data_board.repository.lower(), reverse=config.sort_reverse)
        elif app_data == 'Views A':
            body_group.sort(key=lambda x: x.data_board.col_view_a, reverse=config.sort_reverse)
        elif app_data == 'Views U':
            body_group.sort(key=lambda x: x.data_board.col_view_u, reverse=config.sort_reverse)
        elif app_data == 'Clones A':
            body_group.sort(key=lambda x: x.data_board.col_clone_a, reverse=config.sort_reverse)
        elif app_data == 'Clones U':
            body_group.sort(key=lambda x: x.data_board.col_clone_u, reverse=config.sort_reverse)
        elif app_data == 'Referrers':
            body_group.sort(key=lambda x: len(x.data_board.referrers), reverse=config.sort_reverse)

        for board in body_group:
            board.sort_boards()

    def sum_boards():
        tot_col_view_a = 0
        tot_col_view_u = 0
        tot_col_clone_a = 0
        tot_col_clone_u = 0
        for board in body_group:
            tot_col_view_a += board.data_board.col_view_a
            tot_col_view_u += board.data_board.col_view_u
            tot_col_clone_a += board.data_board.col_clone_a
            tot_col_clone_u += board.data_board.col_clone_u
        dpg.configure_item('view_a', label=tot_col_view_a)
        dpg.configure_item('view_u', label=tot_col_view_u)
        dpg.configure_item('clone_a', label=tot_col_clone_a)
        dpg.configure_item('clone_u', label=tot_col_clone_u)

    def change_boards(sender, app_data):
        global config
        config.board_type = app_data
        for board in body_group:
            board.change_board(sender, app_data)

    # -----------------------------------------------------------------------------
    # Config functions
    # -----------------------------------------------------------------------------

    def file_dialog(sender, app_data, user_data):
        dpg.bind_theme('file_theme')
        dpg.configure_item("file_dialog_id", show=True, callback=user_data)

    def file_cancel(sender, app_data, user_data):
        dpg.bind_theme(global_theme)

    def create_user():
        dpg.show_item('new_user')

    def save_users():
        users_ini.add_section('USERS')
        users_ini.add_section('DEF')
        for n, user in enumerate(users.users):
            users_ini.set('USERS', f'user{n}', user[1])
        users_ini.set('DEF', 'user', users.default_user)

        with open(users_path, 'w') as f:
            users_ini.write(f)

    def load_users():
        users_error = 'no_users'

        users = Users(users=[],
                      default_user='')

        if os.path.isfile(users_path):
            try:
                users_ini.read(users_path)
                users.users = users_ini.items('USERS')
                users.default_user = users_ini.items('DEF')[0][1]
                users_error = None
            except (ValueError, TypeError, configparser.NoOptionError, configparser.DuplicateOptionError) as e:
                users_error = f'Error loading users:\n{e}.\nCreate a new user.'

        return users, users_error

    def load_config(config_path):

        def bool2(state):
            return True if state.lower() == 'true' else False

        config_error = 'Config file not found.\nEnter your credentials and save a config file.'

        config = Config(date_days=period,
                        disable_days=disable_days,
                        plot_alpha=plot_alpha,
                        plot_height=plot_height,
                        show_dates=show_dates,
                        board_type=board_type,
                        sort_item=sort_item,
                        sort_reverse=sort_reverse,
                        repo_filter=repo_filter,
                        tooltips_show=tooltips_show,
                        tooltips_delay=tooltips_delay,
                        show_views_a=show_views_a,
                        show_views_u=show_views_u,
                        show_clones_a=show_clones_a,
                        show_clones_u=show_clones_u,
                        small_separator=small_separator,
                        large_separator=large_separator)

        if os.path.isfile(config_path):
            try:
                config_ini.read(config_path)
                config_sec = config_ini['CONFIGS']
                config.date_days = int(config_sec.get('date_days'))
                config.disable_days = bool2(config_sec.get('disable_days'))
                config.plot_alpha = int(config_sec.get('plot_alpha'))
                config.plot_height = int(config_sec.get('plot_height'))
                config.show_dates = bool2(config_sec.get('show_dates'))
                config.board_type = config_sec.get('board_type')
                config.sort_item = config_sec.get('sort_item')
                config.sort_reverse = bool2(config_sec.get('sort_reverse'))
                config.repo_filter = config_sec.get('repo_filter')
                config.tooltips_show = bool2(config_sec.get('tooltips_show'))
                config.tooltips_delay = float(config_sec.get('tooltips_delay'))
                config.show_views_a = bool2(config_sec.get('show_views_a'))
                config.show_views_u = bool2(config_sec.get('show_views_u'))
                config.show_clones_a = bool2(config_sec.get('show_clones_a'))
                config.show_clones_u = bool2(config_sec.get('show_clones_u'))
                config.small_separator = int(config_sec.get('small_separator'))
                config.large_separator = int(config_sec.get('large_separator'))
                config_error = None

            except (ValueError, TypeError, configparser.NoOptionError, configparser.DuplicateOptionError) as e:
                config_error = f'Error loading config file:\n{e}.\nFix it or enter your credentials and save a new one.'

        return config, config_error

    def save_config(sender, app_data, override=False):
        if not override and not gui_loaded:
            return

        dpg.bind_theme(global_theme)

        global config_files

        if sender == 'save_config':
            file = config_path
        else:
            file = app_data['file_path_name']

        if not config_ini.has_section('CONFIGS'):
            config_ini.add_section('CONFIGS')
        config_ini.set('CONFIGS', 'date_days', str(output_head.date_days))
        config_ini.set('CONFIGS', 'disable_days', str(config.disable_days))
        config_ini.set('CONFIGS', 'plot_alpha', str(config.plot_alpha))
        config_ini.set('CONFIGS', 'plot_height', str(config.plot_height))
        config_ini.set('CONFIGS', 'show_dates', str(config.show_dates))
        config_ini.set('CONFIGS', 'board_type', config.board_type)
        config_ini.set('CONFIGS', 'sort_item', config.sort_item)
        config_ini.set('CONFIGS', 'sort_reverse', str(config.sort_reverse))
        config_ini.set('CONFIGS', 'repo_filter', config.repo_filter)
        config_ini.set('CONFIGS', 'tooltips_show', str(config.tooltips_show))
        config_ini.set('CONFIGS', 'tooltips_delay', str(config.tooltips_delay))
        config_ini.set('CONFIGS', 'show_views_a', str(config.show_views_a))
        config_ini.set('CONFIGS', 'show_views_u', str(config.show_views_u))
        config_ini.set('CONFIGS', 'show_clones_a', str(config.show_clones_a))
        config_ini.set('CONFIGS', 'show_clones_u', str(config.show_clones_u))
        config_ini.set('CONFIGS', 'small_separator', str(config.small_separator))
        config_ini.set('CONFIGS', 'large_separator', str(config.large_separator))

        with open(file, 'w') as configfile:
            config_ini.write(configfile)

        config_files = list_saved_files()

    def list_saved_files():
        config_files = []
        dpg.delete_item('saved_config', children_only=True)
        for file in os.listdir("JSONs"):
            if file.endswith(".config"):
                file = f'JSONs/{file}'
                config_files.append(file)
                dpg.add_menu_item(label=os.path.basename(file), parent='saved_config', callback=load_saved_files, user_data={'file_path_name': file})
        return config_files

    def load_saved_files(sender, app_data, user_data):
        open_config(None, user_data)

    def open_config(sender, app_data):
        if not gui_loaded:
            return None, 'Error'

        dpg.bind_theme(global_theme)

        if sender == 'revert_config':
            file = config_path
        else:
            file = app_data['file_path_name']

        config_temp, config_error = load_config(file)

        if config_error:
            show_info(text=config_error)
            return

        global config
        global body_group

        config = config_temp
        output_head.date_days = config.date_days

        refresh_gui_config()
        for board in body_group:
            dpg.delete_item(board._group)
        body_group = create_boards()
        populate_boards()
        change_plot_alpha(None, config.plot_alpha)
        if not config.disable_days:
            min_day = output_head.date_to - timedelta(output_head.date_days - 1)
            apply_dates(min_day, output_head.date_to)
        sort_boards('sort_boards', config.sort_item)
        sum_boards()
        set_tooltips()

    # -----------------------------------------------------------------------------
    # Misc menu functions
    # -----------------------------------------------------------------------------

    def set_tooltips():
        for tt in tooltips:
            dpg.configure_item(tt, delay=config.tooltips_delay, show=config.tooltips_show)
            dpg.bind_item_theme(tt, 'check_and_tooltips')
        for board in body_group:
            for tt in board.board_tooltip:
                dpg.configure_item(tt, delay=config.tooltips_delay, show=config.tooltips_show)
                dpg.bind_item_theme(tt, 'check_and_tooltips')

    def toggle_tooltips():
        global config
        config.tooltips_show = dpg.get_value('toggle_tooltips')
        set_tooltips()

    def save_credentials(sender, app_data, user_data):
        global credentials
        credentials = [dpg.get_value('cred_username'), dpg.get_value('cred_token')]
        with open(cred_file, 'wb') as f:
            pickle.dump(credentials, f)
        dpg.hide_item('credentials')

    def enter_credentials():
        global credentials
        credentials = load_credentials(cred_file)

        dpg.configure_item('cred_username', default_value=users.default_user)
        dpg.configure_item('cred_token', default_value=credentials[1])
        show_centered_window('credentials')

    def load_credentials(cred_file):
        try:
            with open(cred_file, 'rb') as f:
                credentials = pickle.load(f)
        except FileNotFoundError:
            return ['', '']
        return credentials

    def fetch_data(sender, app_data):
        global traffic
        global output_head
        global output_boards
        global body_group
        global max_cust
        global gui_loaded

        credentials = load_credentials(cred_file)
        if credentials[0] == '' or credentials[1] == '':
            show_info(text='No credentials found.\nEnter the GitHub API token for this user.')
        else:
            width = dpg.get_viewport_client_width()
            dpg.add_progress_bar(default_value=0, overlay='', width=-1, tag='progress_repos', parent='error')
            dpg.configure_item('error_text', default_value='')
            dpg.configure_item('error', width=width - 100)
            show_info(label='Downloading data from GitHub')

            traffic, error = gatherData(traffic, credentials=credentials)

            dpg.configure_item('error', show=False)
            dpg.delete_item('progress_repos')

            if error:
                show_info(text=traffic, label='Cancelled')
                traffic = []
            else:
                max_cust = None
                saveData(data_file, traffic, credentials)
                output_head, output_boards = buildGUIOutput(traffic)
                for board in body_group:
                    dpg.delete_item(board._group)
                body_group = create_boards()
                sort_boards('sort_boards', config.sort_item)
                populate_boards()
                sum_boards()
                filter_repos('repo_names', config.repo_filter)
                refresh_gui_fetch()
                dpg.configure_item('frame', show=True)
                gui_loaded = True

    def show_api_rate():
        if dpg.does_alias_exist('api_rate_window'):
            dpg.delete_item('api_rate_window')

        req, _ = getAPIdata(rate_url, credentials=credentials, rate=True)

        with dpg.window(label=f'GitHub API rates', pos=(50, 30), tag='api_rate_window'):
            dpg.bind_item_theme(dpg.last_item(), 'button_working')

            with dpg.table(borders_innerH=True, borders_innerV=True, borders_outerV=True, borders_outerH=True,
                           sortable=True, sort_multi=True, callback=sort_stats_callback):
                dpg.bind_item_theme(dpg.last_item(), 'table')

                dpg.add_table_column(label="Name")
                dpg.add_table_column(label="Limit", width_fixed=True)
                dpg.add_table_column(label="Used", width_fixed=True)
                dpg.add_table_column(label="Remaining", width_fixed=True)
                dpg.add_table_column(label="Reset", width_fixed=True, no_sort=True)

                for rate in req['resources']:
                    with dpg.table_row():
                        dpg.add_text(rate)
                        dpg.add_text(req['resources'][rate]['limit'])
                        dpg.add_text(req['resources'][rate]['used'])
                        dpg.add_text(req['resources'][rate]['remaining'])
                        dpg.add_text(datetime.fromtimestamp(req['resources'][rate]['reset']))
                with dpg.table_row():
                    dpg.add_text('rate')
                    dpg.add_text(req['rate']['limit'])
                    dpg.add_text(req['rate']['used'])
                    dpg.add_text(req['rate']['remaining'])
                    dpg.add_text(datetime.fromtimestamp(req['resources'][rate]['reset']))

    def accept_deep_config():
        global config

        config.small_separator = int(dpg.get_value('small_separator'))
        config.large_separator = int(dpg.get_value('large_separator'))
        config.tooltips_delay = float(dpg.get_value('tooltips_delay'))

        config.small_separator = max(min(config.small_separator, 20), 1)
        config.large_separator = max(min(config.large_separator, 30), 1)

        dpg.set_value('small_separator', config.small_separator)
        dpg.set_value('large_separator', config.large_separator)

        for board in body_group:
            board.small_separator = config.small_separator
            board.large_separator = config.large_separator
            if board.board_type == 'Basic' or board.board_type == 'Graph':
                dpg.configure_item(board.board_separator, height=config.small_separator)
            else:
                dpg.configure_item(board.board_separator, height=config.large_separator)

        set_tooltips()

        dpg.hide_item('deep_config')

    def reject_deep_config():
        dpg.set_value('small_separator', config.small_separator)
        dpg.set_value('large_separator', config.large_separator)
        dpg.set_value('tooltips_delay', config.tooltips_delay)
        dpg.hide_item('deep_config')

    def show_help():
        dpg.configure_item('help_window', show=True, height=dpg.get_viewport_client_height() - 65)

    def about():
        pos_x = dpg.get_viewport_client_width() / 2 - 128
        pos_y = dpg.get_viewport_client_height() / 2 - 50
        show = not dpg.is_item_visible('about')
        dpg.configure_item('about', pos=(pos_x, pos_y), show=show)

    def statistics():
        if not gui_loaded:
            return

        span = len(output_head.time_period)
        sum_avg_va = 0
        sum_all_va = 0
        sum_avg_vu = 0
        sum_all_vu = 0
        sum_avg_ca = 0
        sum_all_ca = 0
        sum_avg_cu = 0
        sum_all_cu = 0
        date_from = output_head.date_from.date()
        date_to = output_head.date_to.date()
        days = date_to - date_from
        with dpg.window(label=f'Statistics from {date_from} to {date_to} - {days.days + 1} days', pos=(50, 30)):
            dpg.bind_item_theme(dpg.last_item(), 'button_working')
            dpg.add_text('P**: Most hits in a day / M**: Average hits per day.')
            dpg.add_text('P=Peak  M=Average  V=View  C=Clone  A=All  U=Unique', color=WB_DEEP)

            with dpg.table(borders_innerH=True, borders_innerV=True, borders_outerV=True, borders_outerH=True,
                           sortable=True, sort_multi=True, callback=sort_stats_callback) as stat_table:
                dpg.bind_item_theme(dpg.last_item(), 'table')

                dpg.add_table_column(label="Repository")
                dpg.add_table_column(label="PVA", width=40, width_fixed=True)
                dpg.add_table_column(label="PVU", width=40, width_fixed=True)
                dpg.add_table_column(label="PCA", width=40, width_fixed=True)
                dpg.add_table_column(label="PCU", width=40, width_fixed=True)
                dpg.add_table_column(label="MVA", width=40, width_fixed=True)
                dpg.add_table_column(label="MVU", width=40, width_fixed=True)
                dpg.add_table_column(label="MCA", width=40, width_fixed=True)
                dpg.add_table_column(label="MCU", width=40, width_fixed=True)

                for board in body_group:
                    sum_avg_va += board.data_board.col_view_a / span
                    sum_all_va += sum(board.data_board.views_a)
                    sum_avg_vu += board.data_board.col_view_u / span
                    sum_all_vu += sum(board.data_board.views_u)
                    sum_avg_ca += board.data_board.col_clone_a / span
                    sum_all_ca += sum(board.data_board.clones_a)
                    sum_avg_cu += board.data_board.col_clone_u / span
                    sum_all_cu += sum(board.data_board.clones_u)

                    with dpg.table_row():
                        dpg.add_text(board.data_board.repository)
                        dpg.add_text(max(board.data_board.views_a))
                        dpg.add_text(max(board.data_board.views_u))
                        dpg.add_text(max(board.data_board.clones_a))
                        dpg.add_text(max(board.data_board.clones_u))
                        dpg.add_text(round(board.data_board.col_view_a / span, 2))
                        dpg.add_text(round(board.data_board.col_view_u / span, 2))
                        dpg.add_text(round(board.data_board.col_clone_a / span, 2))
                        dpg.add_text(round(board.data_board.col_clone_u / span, 2))

                with dpg.table_row():
                    dpg.add_text('Average average', color=WB_DEEP)
                    # Adding a tooltip here to describe the entry messes with the table sort routine
                    dpg.add_text(0, color=WB_HOVERED)
                    dpg.add_text(0, color=WB_HOVERED)
                    dpg.add_text(0, color=WB_HOVERED)
                    dpg.add_text(0, color=WB_HOVERED)
                    dpg.add_text(round(sum_avg_va / output_head.repositories, 2), color=WB_DEEP)
                    dpg.add_text(round(sum_avg_vu / output_head.repositories, 2), color=WB_DEEP)
                    dpg.add_text(round(sum_avg_ca / output_head.repositories, 2), color=WB_DEEP)
                    dpg.add_text(round(sum_avg_cu / output_head.repositories, 2), color=WB_DEEP)

                with dpg.table_row():
                    dpg.add_text('Sum average', color=WB_DEEP)
                    # Adding a tooltip here to describe the entry messes with the table sort routine
                    dpg.add_text(0, color=WB_HOVERED)
                    dpg.add_text(0, color=WB_HOVERED)
                    dpg.add_text(0, color=WB_HOVERED)
                    dpg.add_text(0, color=WB_HOVERED)
                    dpg.add_text(round(sum_all_va / span, 2), color=WB_DEEP)
                    dpg.add_text(round(sum_all_vu / span, 2), color=WB_DEEP)
                    dpg.add_text(round(sum_all_ca / span, 2), color=WB_DEEP)
                    dpg.add_text(round(sum_all_cu / span, 2), color=WB_DEEP)

            dpg.set_table_row_color(stat_table, output_head.repositories, WB_HOVERED)
            dpg.set_table_row_color(stat_table, output_head.repositories + 1, WB_HOVERED)

    # -----------------------------------------------------------------------------
    # Helper functions
    # -----------------------------------------------------------------------------
    def create_first_user():
        new_user = dpg.get_value('enter_new_user')
        if not new_user:
            return

        dpg.hide_item('new_user')
        dpg.configure_item('accept_new_user', width=199, callback=create_user)
        dpg.set_value('enter_new_user', '')
        dpg.show_item('cancel_new_user')

        global users
        global cred_file
        global data_file
        global config_path

        users.users = [('user1', new_user)]
        users.default_user = new_user

        cred_file = f'JSONs/{users.default_user}.pickle'
        data_file = f'JSONs/{users.default_user}.json'
        config_path = f'JSONs/{users.default_user}.config'

        save_users()

        file = f'JSONs/{users.default_user}.config'
        save_config(None, {'file_path_name': file}, override=True)

        time.sleep(0.1)
        enter_credentials()

    def sort_stats_callback(sender, sort_specs):
        if sort_specs is None:
            return

        rows = dpg.get_item_children(sender, 1)
        cols = dpg.get_item_children(sender, 0)
        col_index = cols.index(sort_specs[0][0])

        sortable_list = []
        for row in rows:
            sort_cell = dpg.get_item_children(row, 1)[col_index]
            sortable_list.append([row, dpg.get_value(sort_cell)])

        if col_index == 0:
            sortable_list.sort(key=lambda x: x[1].lower(), reverse=sort_specs[0][1] < 0)
        elif col_index < 5:
            sortable_list.sort(key=lambda x: int(x[1]), reverse=sort_specs[0][1] < 0)
        else:
            sortable_list.sort(key=lambda x: float(x[1]), reverse=sort_specs[0][1] < 0)

        new_order = []
        for pair in sortable_list:
            new_order.append(pair[0])

        dpg.reorder_items(sender, 1, new_order)

    def show_info(text='', label='Error'):
        window_size = dpg.get_text_size(text)
        if window_size:
            if window_size[0] > 0.0 and window_size[1] > 0.0:
                window_size[0] = min(window_size[0], dpg.get_viewport_client_width() - 100)
                dpg.configure_item('error', width=window_size[0] + 20, height=window_size[1] * 2)
        dpg.configure_item('error_text', default_value=text, color=color)
        dpg.configure_item('error', label=label)
        show_centered_window('error')

    def show_centered_window(window_id):
        if dpg.is_viewport_ok():
            with dpg.mutex():
                vp_width = dpg.get_viewport_width()
                vp_height = dpg.get_viewport_height()
                dpg.show_item(window_id)
            dpg.split_frame()
            wd_width = dpg.get_item_width(window_id)
            wh_height = dpg.get_item_height(window_id)
            dpg.set_item_pos(window_id, [int((vp_width / 2 - wd_width / 2)), int((vp_height / 2 - wh_height / 2))])
        else:
            dpg.show_item(window_id)

    def refresh_gui_fetch():
        dpg.configure_item('username', default_value=users.default_user)
        dpg.configure_item('date_days', label=output_head.date_days)
        dpg.configure_item('repositories', label=output_head.repositories)
        dpg.configure_item('last_updated', label=output_head.last_updated.date())
        dpg.configure_item('days_ago', label=output_head.days_ago)
        if output_head.days_ago > 9:
            dpg.bind_item_theme('days_ago', 'button_yellow')
        if output_head.days_ago > 12:
            dpg.bind_item_theme('days_ago', 'button_red')
        dpg.configure_item('date_from', label=output_head.date_from.date())
        dpg.configure_item('date_to', label=output_head.date_to.date())
        dpg.configure_item('repo_names', items=output_head.repo_names)
        dpg.configure_item('picker_from', default_value=convert_to_date_picker(output_head.date_from.date()))
        dpg.configure_item('picker_to', default_value=convert_to_date_picker(output_head.date_to.date()))

    def refresh_gui_config():
        dpg.configure_item('username', default_value=users.default_user)
        dpg.configure_item('date_days', label=output_head.date_days)
        dpg.configure_item('set_days', default_value=output_head.date_days)
        dpg.configure_item('toggle_days', default_value=config.disable_days)
        dpg.configure_item('plot_alpha', default_value=config.plot_alpha)
        dpg.configure_item('plot_height', default_value=config.plot_height)
        dpg.configure_item('plot_show_dates', default_value=config.show_dates)
        dpg.configure_item('board_type', default_value=config.board_type)
        dpg.configure_item('sort_item', default_value=config.sort_item)
        dpg.configure_item('filter_box', default_value=config.repo_filter)
        dpg.configure_item('toggle_tooltips', default_value=config.tooltips_show)
        dpg.configure_item('tooltips_delay', default_value=config.tooltips_delay)
        dpg.configure_item('small_separator', default_value=config.small_separator)
        dpg.configure_item('large_separator', default_value=config.large_separator)
        dpg.bind_item_theme('view_a', 'button_view_a' if config.show_views_a else 'button_working')
        dpg.bind_item_theme('view_u', 'button_view_u' if config.show_views_u else 'button_working')
        dpg.bind_item_theme('clone_a', 'button_clone_a' if config.show_clones_a else 'button_working')
        dpg.bind_item_theme('clone_u', 'button_clone_u' if config.show_clones_u else 'button_working')
        change_plot_alpha(None, config.plot_alpha)

    # -----------------------------------------------------------------------------
    # region Theme definitions
    # -----------------------------------------------------------------------------
    with dpg.theme() as global_theme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, BG, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_TitleBg, WB_HOVERED, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, WB_IDLE, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_TitleBgCollapsed, WB_DEEP, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, BG, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_PopupBg, BG, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_Border, WB_IDLE, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarBg, BG, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrab, WB_IDLE, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabHovered, WB_HOVERED, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabActive, WB_ACTIVE, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_Button, LIGHT, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, LIGHT, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, LIGHT, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_CheckMark, WB_DEEP, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, WB_DEEP, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, WB_HOVERED, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, LIGHT, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, LIGHT, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, LIGHT, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_TextSelectedBg, MEDIUM, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_TextDisabled, WB_IDLE, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_MenuBarBg, WB_IDLE, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_Header, WB_ACTIVE, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, WB_HOVERED, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, WB_ACTIVE, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_Separator, WB_IDLE, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ResizeGrip, WB_IDLE, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ResizeGripHovered, WB_HOVERED, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ResizeGripActive, WB_ACTIVE, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_TableHeaderBg, WB_IDLE, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_TableBorderLight, WB_IDLE, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_TableBorderStrong, WB_IDLE, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_PlotHistogram, WB_DEEP, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 1, 1, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 0, 7, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_ChildBorderSize, 0, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_PopupBorderSize, 1, category=dpg.mvThemeCat_Core)

    with dpg.theme(tag='file_theme'):
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, BG, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_TitleBg, WB_HOVERED, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, WB_IDLE, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_TitleBgCollapsed, WB_DEEP, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, BG, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_PopupBg, BG, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_Border, WB_IDLE, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarBg, BG, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrab, WB_IDLE, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabHovered, WB_HOVERED, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabActive, WB_ACTIVE, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_Button, WB_IDLE, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, WB_ACTIVE, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, WB_HOVERED, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_CheckMark, WB_DEEP, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, WB_DEEP, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, WB_HOVERED, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, WB_IDLE, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, WB_ACTIVE, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, WB_HOVERED, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_TextSelectedBg, MEDIUM, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_TextDisabled, WB_IDLE, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_MenuBarBg, WB_IDLE, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_Header, WB_ACTIVE, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, WB_HOVERED, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, WB_ACTIVE, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_Separator, WB_IDLE, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ResizeGrip, WB_IDLE, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ResizeGripHovered, WB_HOVERED, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ResizeGripActive, WB_ACTIVE, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_TableHeaderBg, WB_IDLE, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_TableBorderLight, WB_IDLE, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_TableBorderStrong, WB_IDLE, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_TextSelectedBg, WB_HOVERED, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 1, 1, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 5, 7, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_ChildBorderSize, 0, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_PopupBorderSize, 1, category=dpg.mvThemeCat_Core)

    with dpg.theme(tag='button_working'):
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_Button, WB_IDLE, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, WB_ACTIVE, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, WB_HOVERED, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, WB_IDLE, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, WB_ACTIVE, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, WB_HOVERED, category=dpg.mvThemeCat_Core)
            # dpg.add_theme_color(dpg.mvThemeCol_PopupBg, WB_IDLE, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_Header, WB_IDLE, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, WB_HOVERED, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, WB_ACTIVE, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_TextSelectedBg, WB_HOVERED, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_PopupBorderSize, 1, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 10, 7, category=dpg.mvThemeCat_Core)

    with dpg.theme(tag='plot'):
        with dpg.theme_component(dpg.mvPlot):
            dpg.add_theme_color(dpg.mvPlotCol_PlotBg, PLOT_BG, category=dpg.mvThemeCat_Plots)
            dpg.add_theme_color(dpg.mvPlotCol_FrameBg, PLOT_BG, category=dpg.mvThemeCat_Plots)
            dpg.add_theme_color(dpg.mvPlotCol_PlotBorder, (220, 220, 220), category=dpg.mvThemeCat_Plots)
            dpg.add_theme_color(dpg.mvThemeCol_Text, LIGHT, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvPlotStyleVar_PlotPadding, 10, 6, category=dpg.mvThemeCat_Plots)
            dpg.add_theme_style(dpg.mvPlotStyleVar_LabelPadding, 4, 4, category=dpg.mvThemeCat_Plots)
            dpg.add_theme_color(dpg.mvPlotCol_LegendBg, PLOT_BG, category=dpg.mvThemeCat_Plots)
            dpg.add_theme_style(dpg.mvPlotStyleVar_Marker, dpg.mvPlotMarker_Circle, category=dpg.mvThemeCat_Plots)
            dpg.add_theme_style(dpg.mvPlotStyleVar_MarkerSize, 1, category=dpg.mvThemeCat_Plots)
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_PopupBg, BG, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_Text, WB_DEEP, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, WB_IDLE, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, WB_ACTIVE, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, WB_HOVERED, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_Button, WB_IDLE, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, WB_ACTIVE, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, WB_HOVERED, category=dpg.mvThemeCat_Core)

    with dpg.theme(tag='table'):
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 0, 4, category=dpg.mvThemeCat_Core)

    for button in BUTTON_COLOR:
        with dpg.theme(tag=button[0]):
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_Button, button[1], category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, button[1], category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, button[1], category=dpg.mvThemeCat_Core)

    for graph in GRAPH_COLOR:
        plot_fill = (graph[1][0], graph[1][1], graph[1][2], plot_alpha)
        graph_idle = (graph[1][0], graph[1][1], graph[1][2])
        graph_active = (graph[1][0] + ACC_ACTIVE, graph[1][1] + ACC_ACTIVE, graph[1][2] + ACC_ACTIVE)
        graph_hovered = (graph[1][0] + ACC_HOVER, graph[1][1] + ACC_HOVER, graph[1][2] + ACC_HOVER)
        with dpg.theme(tag=graph[0]):
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_Button, graph_idle, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, graph_active, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, graph_hovered, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvPlotCol_Line, graph_idle, category=dpg.mvThemeCat_Plots)
                dpg.add_theme_color(dpg.mvPlotCol_Fill, plot_fill, category=dpg.mvThemeCat_Plots)

    with dpg.theme(tag='check_and_tooltips'):
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 1, 1, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, WB_IDLE, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, WB_ACTIVE, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, WB_HOVERED, category=dpg.mvThemeCat_Core)

    with dpg.theme(tag='pad_text'):
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, LIGHT, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, LIGHT, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, LIGHT, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 10, 7, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_TextSelectedBg, MEDIUM, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_TextDisabled, WB_IDLE, category=dpg.mvThemeCat_Core)

    with dpg.theme(tag='menu'):
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 10, 10, category=dpg.mvThemeCat_Core)
    # endregion

    # -----------------------------------------------------------------------------
    # Handlers
    # -----------------------------------------------------------------------------
    with dpg.item_handler_registry(tag='release_handler'):
        dpg.add_item_deactivated_after_edit_handler(callback=change_days)

    with dpg.item_handler_registry(tag="date_handler"):
        dpg.add_item_clicked_handler(callback=spread_date)

    # -----------------------------------------------------------------------------
    # region Main interface
    # -----------------------------------------------------------------------------
    viewport = dpg.create_viewport(title='KipHub Traffic', width=vp_width, height=vp_height, min_height=500, min_width=500, x_pos=800, small_icon='kiphub.ico', large_icon='kiphub.ico')
    with dpg.window(label='main_window', tag='main_window'):
        # -----------------------------------------------------------------------------
        # Menus
        # -----------------------------------------------------------------------------
        with dpg.menu_bar():
            with dpg.menu(label='File'):
                dpg.bind_item_theme(dpg.last_item(), 'menu')
                dpg.add_menu_item(label='Revert Default Config', callback=open_config, tag='revert_config')
                dpg.add_menu_item(label='Open Config', callback=file_dialog, user_data=open_config)
                dpg.add_menu(label="Open Saved Configs", tag='saved_config')
                dpg.add_menu_item(label='Save Default Config', callback=save_config, tag='save_config')
                dpg.add_menu_item(label='Save Config As', callback=file_dialog, user_data=save_config)
                dpg.add_separator()
                dpg.add_menu_item(label='Exit', callback=lambda: dpg.stop_dearpygui())
            with dpg.menu(label='Settings'):
                dpg.bind_item_theme(dpg.last_item(), 'menu')
                # dpg.add_menu_item(label='Users')
                dpg.add_menu_item(label='Credentials', callback=enter_credentials)
                dpg.add_menu_item(label='Fetch from GitHub', callback=fetch_data)
                dpg.add_menu_item(label='Show API Rate', callback=show_api_rate)
                dpg.add_separator()
                dpg.add_menu_item(label='Deep Config', callback=lambda: dpg.configure_item('deep_config', show=True))
                dpg.add_separator()
                dpg.add_menu_item(label="Restore Width", callback=lambda: dpg.configure_viewport(viewport, width=850))
                dpg.add_checkbox(label="Show Tooltips", default_value=tooltips_show, callback=toggle_tooltips, tag='toggle_tooltips')
                dpg.bind_item_theme(dpg.last_item(), 'check_and_tooltips')

            with dpg.menu(label='Info'):
                dpg.bind_item_theme(dpg.last_item(), 'menu')
                dpg.add_menu_item(label='About', callback=about)
                dpg.add_menu_item(label='Help', callback=show_help)
                dpg.add_menu_item(label='Statistics', callback=statistics)

        # -----------------------------------------------------------------------------
        # Frame window
        # -----------------------------------------------------------------------------
        with dpg.child_window(pos=(28, 40), tag='frame', show=False):
            # -----------------------------------------------------------------------------
            # Header window
            # -----------------------------------------------------------------------------
            with dpg.child_window(width=-20, height=55, no_scrollbar=True, no_scroll_with_mouse=True, tag='header'):
                with dpg.group(horizontal=True):
                    with dpg.group():
                        with dpg.group(horizontal=True):
                            bt_dark.append(dpg.add_button(label="KipHub Traffic", width=134))
                            bt_med.append(dpg.add_button(label="User", width=60))
                            dpg.add_input_text(width=400, tag='username', readonly=True)
                            dpg.bind_item_theme(dpg.last_item(), 'pad_text')
                            bt_med.append(dpg.add_button(label="Repositories", width=120))
                            dpg.add_button(width=60, tag='repositories')

                        with dpg.group(horizontal=True):
                            bt_med.append(dpg.add_button(label="Last updated", width=134))
                            dpg.add_button(width=95, tag='last_updated')
                            bt_med.append(dpg.add_button(label="Days ago", width=85))
                            dpg.add_button(width=60, tag='days_ago')
                            bt_med.append(dpg.add_button(label="From", width=60))
                            bt_work.append(dpg.add_button(width=95, tag='date_from'))
                            with dpg.popup(dpg.last_item(), mousebutton=dpg.mvMouseButton_Left):
                                dpg.add_text('From date', color=WB_DEEP)
                                bt_work.append(dpg.add_date_picker(callback=pick_date_from, tag='picker_from'))
                                bt_work.append(dpg.add_input_text(label='Enter date', on_enter=True, width=150, tag='input_from', callback=input_date_from))

                            bt_med.append(dpg.add_button(label="to", width=35))
                            bt_work.append(dpg.add_button(width=95, tag='date_to'))
                            with dpg.popup(dpg.last_item(), mousebutton=dpg.mvMouseButton_Left):
                                dpg.add_text('To date', color=WB_DEEP)
                                bt_work.append(dpg.add_date_picker(callback=pick_date_to, tag='picker_to'))
                                bt_work.append(dpg.add_input_text(label='Enter date', on_enter=True, width=150, tag='input_to', callback=input_date_to))

                            bt_med.append(dpg.add_button(label="Days", width=50))
                            bt_work.append(dpg.add_button(width=60, tag='date_days'))
                            with dpg.popup(dpg.last_item(), mousebutton=dpg.mvMouseButton_Left, tag="popup_days"):
                                bt_work.append(dpg.add_checkbox(label='Disabled', default_value=disable_days, tag='toggle_days', callback=toggle_days))
                                bt_work.append(dpg.add_button(label='Last day', width=100, callback=last_day, tag='last_day'))
                                bt_work.append(dpg.add_drag_int(width=100, min_value=2, max_value=365, format='%d (drag)', tag='set_days'))
                                dpg.bind_item_handler_registry(dpg.last_item(), 'release_handler')
                                bt_work.append(dpg.add_button(label='14 days', width=100, user_data=14, callback=set_days, tag='14_days'))
                                bt_work.append(dpg.add_button(label='30 days', width=100, user_data=30, callback=set_days, tag='30_days'))
                                bt_work.append(dpg.add_button(label='90 days', width=100, user_data=90, callback=set_days, tag='90_days'))
                                bt_work.append(dpg.add_button(label='All days', width=100, callback=all_days, tag='all_days'))
                    dpg.add_button(width=-1, height=56)

            dpg.add_child_window(height=10)

            # -----------------------------------------------------------------------------
            # Body window
            # -----------------------------------------------------------------------------
            with dpg.child_window(width=-20, height=-80, delay_search=True, tag='body'):
                with dpg.filter_set(id='filter') as repo_filter_tag:
                    pass

            dpg.add_child_window(height=10)

            # -----------------------------------------------------------------------------
            # Footer window
            # -----------------------------------------------------------------------------
            with dpg.child_window(width=-20, height=55, no_scrollbar=True, no_scroll_with_mouse=True, tag='footer'):
                with dpg.group(horizontal=True):
                    with dpg.group():
                        with dpg.group(horizontal=True):
                            bt_dark.append(dpg.add_button(label="Configuration", width=134))
                            bt_med.append(dpg.add_button(label="Info", width=73,))
                            bt_work.append(dpg.add_combo(board_types, width=118, callback=change_boards, tag='board_type'))
                            bt_med.append(dpg.add_button(label="Sort", width=73, tag='sort_boards'))
                            bt_work.append(dpg.add_combo(sort_items, width=118, callback=sort_boards, tag='sort_item'))

                            bt_med.append(dpg.add_button(label="Graph", width=73))
                            dpg.add_button(label="", width=45, tag='view_a', callback=toggle_graph_all, user_data='button_view_a')
                            dpg.add_button(label="", width=45, tag='view_u', callback=toggle_graph_all, user_data='button_view_u')
                            dpg.add_button(label="", width=45, tag='clone_a', callback=toggle_graph_all, user_data='button_clone_a')
                            dpg.add_button(label="", width=45, tag='clone_u', callback=toggle_graph_all, user_data='button_clone_u')

                        with dpg.group(horizontal=True):
                            bt_work.append(dpg.add_button(label="Plot", width=134, tag='plot_config'))
                            with dpg.popup(dpg.last_item(), mousebutton=dpg.mvMouseButton_Left, tag="popup_height"):
                                bt_work.append(dpg.add_slider_int(label='Alpha', width=100, min_value=0, max_value=255, callback=change_plot_alpha, tag='plot_alpha'))
                                bt_work.append(dpg.add_slider_int(label='Height', width=100, min_value=0, max_value=10, callback=change_plot_height, tag='plot_height'))
                                bt_work.append(dpg.add_checkbox(label='Show dates', callback=toggle_x_labels, tag='plot_show_dates'))
                            bt_med.append(dpg.add_button(label="Filter", width=73))
                            bt_work.append(dpg.add_input_text(width=431, callback=filter_set, tag='filter_box'))
                            bt_work.append(dpg.add_combo([], default_value='Repos', width=78, height_mode=5, callback=filter_repos, tag='repo_names'))
                            bt_work.append(dpg.add_button(label="Clear", width=60, callback=filter_clear, tag='clear_filter'))

                    dpg.add_button(width=-1, height=56,
                                   label='Thank you for using KipHub Traffic\n'
                                         'Fred Rique 2024\n'
                                         'Click to open on GitHub', callback=lambda: webbrowser.open('https://github.com/farique1/KipHub-Traffic'))
                    dpg.bind_item_theme(dpg.last_item(), 'button_working')

        dpg.set_primary_window('main_window', True)
    # endregion

    # -----------------------------------------------------------------------------
    # region Support windows
    # -----------------------------------------------------------------------------
    with dpg.file_dialog(directory_selector=False, default_path='JSONs', default_filename='', modal=True, show=False, id="file_dialog_id", width=700, height=400, cancel_callback=file_cancel):
        dpg.add_file_extension("", color=WB_DEEP)
        dpg.add_file_extension(".config", custom_text="[Config]")

    with dpg.window(label='New User', no_close=True, show=False, modal=True, no_resize=True, tag='new_user'):
        dpg.bind_item_theme(dpg.last_item(), 'button_working')
        dpg.add_text('Enter a new GitHub user.')
        dpg.add_input_text(label='Username', default_value='', width=300, tag='enter_new_user')
        with dpg.group(horizontal=True):
            dpg.add_button(label='OK', width=199, callback=create_user, tag='accept_new_user')
            dpg.add_button(label='Cancel', width=100, callback=lambda: dpg.hide_item('new_user'), tag='cancel_new_user')

    with dpg.window(label='Credentials', no_resize=True, width=500, modal=True, show=False, tag='credentials'):
        dpg.bind_item_theme(dpg.last_item(), 'button_working')
        dpg.add_text('Enter the GitHub API Token for this user.')
        dpg.add_input_text(label='Username', default_value='', width=400, readonly=True, tag='cred_username')
        dpg.bind_item_theme(dpg.last_item(), 'pad_text')
        dpg.add_input_text(label='API Token', default_value='', width=400, tag='cred_token')
        dpg.add_child_window(height=10)
        with dpg.group(horizontal=True):
            dpg.add_button(label='Save', width=299, callback=save_credentials)
            dpg.add_button(label='Cancel', width=100, callback=lambda: dpg.hide_item('credentials'))

    with dpg.window(label='Deep Config', pos=(vp_width / 2 - 100, vp_height / 2 - 100), no_close=True, show=False, modal=True, no_resize=True, tag='deep_config'):
        dpg.bind_item_theme(dpg.last_item(), 'button_working')
        dpg.add_input_text(label='Small separator', default_value=small_separator, decimal=True, width=60, tag='small_separator')
        dpg.add_input_text(label='Large separator', default_value=large_separator, decimal=True, width=60, tag='large_separator')
        dpg.add_input_text(label='Tooltips delay', default_value=tooltips_delay, decimal=True, width=60, tag='tooltips_delay')
        dpg.add_child_window(height=10)
        with dpg.group(horizontal=True):
            dpg.add_button(label='OK', width=60, callback=accept_deep_config)
            dpg.add_button(label='Cancel', width=60, callback=reject_deep_config)

    with dpg.window(label='Help', width=600, pos=(125, 30), show=False, tag='help_window'):
        dpg.bind_item_theme(dpg.last_item(), 'button_working')
        for text, color in HELP_TEXT:
            dpg.add_text(text, color=color, wrap=0)
            dpg.bind_item_theme(dpg.last_item(), 'check_and_tooltips')

    with dpg.window(label='About', no_resize=True, modal=True, show=False, tag='about'):
        dpg.bind_item_theme(dpg.last_item(), 'button_working')
        dpg.add_text('KipHub Traffic v2.0\n'
                     'github.com/farique1/KipHub-Traffic\n'
                     'Fred Rique (c) 2021-2024')

    with dpg.window(label='', modal=True, show=False, tag='error', horizontal_scrollbar=True):
        dpg.bind_item_theme(dpg.last_item(), 'button_working')
        dpg.add_text('', tag='error_text')
    # endregion

    # -----------------------------------------------------------------------------
    # region Tooltips
    # -----------------------------------------------------------------------------
    tooltips = []
    tooltips.append(dpg.add_tooltip('date_from'))
    dpg.add_text(parent=dpg.last_item(), default_value='Show data from this date')
    tooltips.append(dpg.add_tooltip('date_to'))
    dpg.add_text(parent=dpg.last_item(), default_value='Show data until this date')
    tooltips.append(dpg.add_tooltip('input_from'))
    dpg.add_text(parent=dpg.last_item(), default_value='Enter a date manually\nFormat: y-m-d / m-d / d')
    tooltips.append(dpg.add_tooltip('input_to'))
    dpg.add_text(parent=dpg.last_item(), default_value='Enter a date manually\nFormat: y-m-d / m-d / d')
    tooltips.append(dpg.add_tooltip('date_days'))
    dpg.add_text(parent=dpg.last_item(), default_value='Amount of days showing')
    tooltips.append(dpg.add_tooltip('toggle_days'))
    dpg.add_text(parent=dpg.last_item(), default_value='Disable the fixed amount of days')
    tooltips.append(dpg.add_tooltip('last_day'))
    dpg.add_text(parent=dpg.last_item(), default_value='Go to the last day on the data')
    tooltips.append(dpg.add_tooltip('set_days'))
    dpg.add_text(parent=dpg.last_item(), default_value='Amount of days to show\nClick-drag to change\nCTRL+click or double click for manual entry\nHold SHIFT/ALT to go faster/slower')
    tooltips.append(dpg.add_tooltip('14_days'))
    dpg.add_text(parent=dpg.last_item(), default_value='Show the last 14 days')
    tooltips.append(dpg.add_tooltip('30_days'))
    dpg.add_text(parent=dpg.last_item(), default_value='Show the last 30 days')
    tooltips.append(dpg.add_tooltip('90_days'))
    dpg.add_text(parent=dpg.last_item(), default_value='Show the last 90 days')
    tooltips.append(dpg.add_tooltip('all_days'))
    dpg.add_text(parent=dpg.last_item(), default_value='Show all days available on the data')
    tooltips.append(dpg.add_tooltip('board_type'))
    dpg.add_text(parent=dpg.last_item(), default_value='Choose how repository information is shown')
    tooltips.append(dpg.add_tooltip('sort_item'))
    dpg.add_text(parent=dpg.last_item(), default_value='Sort the repositories\n"Reverse" reverses the order')
    tooltips.append(dpg.add_tooltip('view_a'))
    dpg.add_text(parent=dpg.last_item(), default_value='Toggle the View All graphs on all repositories')
    tooltips.append(dpg.add_tooltip('view_u'))
    dpg.add_text(parent=dpg.last_item(), default_value='Toggle the View Unique graphs on all repositories')
    tooltips.append(dpg.add_tooltip('clone_a'))
    dpg.add_text(parent=dpg.last_item(), default_value='Toggle the Clone All graphs on all repositories')
    tooltips.append(dpg.add_tooltip('clone_u'))
    dpg.add_text(parent=dpg.last_item(), default_value='Toggle the Clone Unique graphs on all repositories')
    tooltips.append(dpg.add_tooltip('plot_config'))
    dpg.add_text(parent=dpg.last_item(), default_value='Configure the plots appearance')
    tooltips.append(dpg.add_tooltip('plot_alpha'))
    dpg.add_text(parent=dpg.last_item(), default_value='Set the graphs opacity')
    tooltips.append(dpg.add_tooltip('plot_height'))
    dpg.add_text(parent=dpg.last_item(), default_value='Set the plots height')
    tooltips.append(dpg.add_tooltip('plot_show_dates'))
    dpg.add_text(parent=dpg.last_item(), default_value='Toggle the display of the dates')
    tooltips.append(dpg.add_tooltip('filter_box'))
    dpg.add_text(parent=dpg.last_item(), default_value='Filter the repositories shown')
    tooltips.append(dpg.add_tooltip('repo_names'))
    dpg.add_text(parent=dpg.last_item(), default_value='Repository names filter shortcut')
    tooltips.append(dpg.add_tooltip('clear_filter'))
    dpg.add_text(parent=dpg.last_item(), default_value='Clear the repository filter')
    # endregion

    # -----------------------------------------------------------------------------
    # region Apply themes
    # -----------------------------------------------------------------------------
    dpg.bind_theme(global_theme)
    for t in bt_dark:
        dpg.bind_item_theme(t, 'button_dark')
    for t in bt_med:
        dpg.bind_item_theme(t, 'button_med')
    for t in bt_work:
        dpg.bind_item_theme(t, 'button_working')
    # endregion

    # -----------------------------------------------------------------------------
    # region Initialization
    # -----------------------------------------------------------------------------
    start_error = None

    users, users_error = load_users()

    config_path = f'JSONs/{users.default_user}.config'
    config, config_error = load_config(config_path)

    if not users_error:

        cred_file = f'JSONs/{users.default_user}.pickle'
        data_file = f'JSONs/{users.default_user}.json'
        config_path = f'JSONs/{users.default_user}.config'

        if not config_error:

            traffic = loadData(data_file)

            if traffic:
                output_head, output_boards = buildGUIOutput(traffic)
            else:
                start_error = 'No data available for this user.\nFetch GitHub data from the menu or enter new credentials.'
        else:
            start_error = config_error
    else:
        start_error = users_error

    if start_error:
        output_head, output_boards = no_traffic()
        traffic = []
        body_group = []

    min_cust = output_head.date_from
    max_cust = output_head.date_to

    if start_error is None:
        dpg.configure_item('frame', show=True)
        gui_loaded = True
        body_group = create_boards()
        sort_boards('sort_boards', config.sort_item)
        populate_boards()
        sum_boards()
        filter_repos('repo_names', config.repo_filter)
        config_files = list_saved_files()
    else:
        if users_error == 'no_users':
            dpg.configure_item('accept_new_user', width=300, callback=create_first_user)
            dpg.hide_item('cancel_new_user')
            dpg.show_item('new_user')
        else:
            show_info(text=start_error)

    set_tooltips()
    refresh_gui_fetch()
    refresh_gui_config()
    # endregion

    # -----------------------------------------------------------------------------
    # region Initialize DPG
    # -----------------------------------------------------------------------------
    dpg.setup_dearpygui()
    dpg.show_viewport()

    while dpg.is_dearpygui_running():
        dpg.render_dearpygui_frame()

    dpg.destroy_context()
    # endregion


# -----------------------------------------------------------------------------
# Main function
# -----------------------------------------------------------------------------
def main():
    if not os.path.isdir('JSONs'):
        os.mkdir('JSONs')

    if args.gui:
        if not dpg_module:
            print(f'{RED}Dear PyGui module not installed.')
            print(f'{YELLOW}Instal the Dear PyGui module or run KipHub Traffic with {GREEN}-g{RESET}')
            raise SystemExit(0)
        else:
            showGUIOutput()
    else:
        traffic = loadData(data_file)

        if view_only and not traffic:
            print(f'{RED}No data available. Use -d to download data from GitHub.{RESET}\n')
            raise SystemExit(0)

        if not view_only:
            traffic, _ = gatherData(traffic)
            saveData(data_file, traffic)

        output_head, output_list = buildConsoleOutput(traffic)
        showConsoleOutput(output_list, output_head)


if __name__ == '__main__':
    main()
