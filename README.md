  
# KipHub Traffic  
*v1.1*  
  
My take on the "GitHub doesn't save more than 14 days of traffic data" problem.  
There are a lot of similar tools out there but all of them seemed a bit overworked for my taste so I took the usual approach and made a simpler one with chicken wire and bubble gum. It uses no external dependencies and no servers, you just have to run it once every fourteen days and you are done. It even manages to produce a passable visual representation of the data with lots of options.  
  
Each repository will be listed with information about `referrers`, `views` and `clones` each with `count` and `uniques` . If the information is not available its section will be omitted:  
```  
Repo: msx-basic-dignified  
Referrers: (last 14 days)  
 github.com C10 U2  
 msx.org C4 U2  
 Google C2 U1  
Views: C26 U8 (last 14 days)  
 Day: 20 21 22 23 24 25 26 27 28 29 30 31|01 02 03 04 05 06 07 08  Sum  
 Cnt:          3     13                   1  5  15 4     1         42  
 Unq:          2     1                    1  1  4  1     1         11  
Clones: C2 U2 (last 14 days)  
 Day: 20 21 22 23 24 25 26 27 28 29 30 31|01 02 03 04 05 06 07 08  Sum  
 Cnt:          1     1     1  1                                    4  
 Unq:          1     1     1  1                                    4  
```  
The values show in `Referrers`, `Views` and `Clones` are given as is by GitHub and are only for the past 14 days. `C` stands for `count` and `U` for `uniques`.  `|` marks a new month and `Sum` shows the total amount for the period.  
  
The information shown can be customised in a number of ways with toggles to hide any information not needed, these include hiding days without data, referrers (which can be show on a single line or expanded), the views and clones 14 days reports, the days and sum labels, the daily data, the sum and the whole views, clones, count or unique sections.  
Showing for instance:  
```  
Repo: msx-basic-dignified  
Clones:  
 Cnt:  54  
 Unq:  40  
```  
You can customize the repository sort order (ascending or descending) based on its `name` (*default*), `views`, `clones` and then by `count` and `uniques`.  
  
The dates shown can also be customized. By default it will display the last 30 available days but you can choose a starting date, an ending date or a period ranging back from the ending date.  
  
The API data is consolidated and saved on a JSON file with the GitHub login name. When downloading data and updating the JSON database a backup of the previous one will be created.  All created files are saved on the `JSONs` folder.  
  
You can also specify if you want to keep the API response (each on its own JSON file) and even if you want to reuse these data instead of the main JSON database or the AIP's.  
  
There is no built in option to save the output to a text file but you can pipe the output to a text file by using `> output.txt` after the commands.  
  
There are some predefined `.bat` files for Windows users to call KipHub Traffic with custom settings.  
```  
KipHub_DOWN.bat  
KipHub_VIEW.bat  
KipHub_VIEW_AllDays.bat  
KipHub_VIEW_AllInfo.bat  
KipHub_VIEW_ClonesUnique.bat  
KipHub_VIEW_Referres.bat  
```  
### How to use  
  
**KipHub Traffic** uses the personal access token from the GitHub API.  
  
> Get the token at `Settings > Developer settings > Personal access tokens` ticking the `repo` checkmark.  
  
Assign your `token` and `username` to the appropriated variables in the code:  
  
``` python  
username = '<YOUR_USERNAME>'  
token = '<YOUR_TOKEN>'  
```  
  
And run it with:  
`KipHub.py [args] [> output.txt]`  
  
The program will call the GitHub API, get your repository list and go through each one of them collecting their traffic data and consolidating them on a single JSON. This JSON is your long term traffic storage, if there is one present, **KipHub** will load it and merge the new data.  
  
> There must be a folder called `JSONs` at the level of `KipHub.py`.  
  
**There are several arguments you can use to customize the output:**  
  
`-d`  
By default KipHib Traffic only display the available data.  
Use this to download new data from GitHub.  
  
`-c [k,u]`  
*Cache behavior.*  
KipHub Traffic can keep the API response JSONs as local files. This changes the way it is used and kept.  
`k`: keep a local copy of the API response JSONs.  
`u`: do not go online, use the local copy of the API JSONs to update the database and show the data.  
Default: do not save the API JSONs nor use it.  
  
`-b <date>`  
*Custom **start** date.*  
The format must be `y-m-d`, `m-d` or just `d`.  
Default: the first date available across all repos.  
  
`-e <date>`  
*Custom **end** date.*  
The format must be `y-m-d`, `m-d` or just `d`.  
Default: the date last updated.  
  
`-p <days>`  
*Period.*  
Number of days to show before the **end** date (overrides `-b`).  
Default: none  
  
`-s [v,c,o,r]`  
*Sorting order.*  
Changes the sort order.  
You can use more than one letter to refine the sort.  
`v`: sort by `views`.  
`c`: sort by `clones`  
The default secondary sort is by `uniques`  
`o`: sort secondary by `count`.  
`r`: reverse the sort order.  
Default: alphabetically by repo name.  
  
`-t [a,r,e,p,l,d,s,v,c,o,u]`  
*Toggle view elements.*  
Configures the way the data is show.  
You can use more than one letter to refine the output.  
`a`: hide all days without data.  
`r`: hide the `referrers`  
`e`: `referrers` are show all on the same line, this expands them to one line each.  
`p`: hide the reported 14 days `count` and  `unique` for `views` and `clones`.  
`l`: hide the label for the days and sums.  
`d`: hide the daily information.  
`s`: hide the sum.  
`v`: hide the `views`.  
`c`: hide the `clones`.  
`o`: hide the `count`  
`u`: hide the `unique`.  
Default: show everiything.  
Obs. these are toggles so you can set a default in the variable `toggle = ''` on the code and toggle back the information when needed.  
  
`> output.txt`  
*Save output.*  
Use at the end of the command.  
Saves a copy of the output to a text file.  
  
  
## Acknowledgements  
  
Enjoy and send feedback.  
***KipHub Traffic** is offered as is, with no guarantees whatsoever.*  
