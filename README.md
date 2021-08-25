# KipHub Traffic  
  
My take on the "GitHub doesn't save more than 14 days of traffic data" problem.  
There are a lot of similar tools out there but all of them seemed a bit overworked for my taste so I took my usual approach and made a simpler one with chicken wire and bubble gum. It uses no external dependencies and no servers, you just have to run it once every fourteen days and you are done. It even manages to produce a nice visual representation of the data with lots of options.  
  
Each repository will be listed with information about `referrers`, `views` and `clones`, if the information is not available its section will be omitted:  
```  
msx-basic-dignified  
Referrers: github.com 15 1  
Views: 36 4  
 Day: 08 09 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24  Sum  
 Cnt:    6  3  1  2  8  1  1  2     3  14 2     1     1   45  
 Unq:    2  1  1  1  1  1  1  2     1  1  1     1     1   15  
Clones: 2 2  
 Day: 08 09 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24  Sum  
 Cnt:          1                                      1   2  
 Unq:          1                                      1   2  
```  
You can customize the repository sort order (ascending or descending) based on its name (*default*), `views`, `clones` and then by `count` and `uniques`.  
`Sum` shows the total amount for the period but cannot be sorted by and the `uniques` figure is misleading.  
  
The dates shown can also be customized. By default it will display all days from the first available day with data across all repos to the last update but you can choose a starting date, an ending date or a period ranging back from the ending date to show.  
The numbers after `Referrers:`, `Views:` and `Clones:` are the `count` and `uniques` numbers respectively and they always refer to the 14 days before the last update, same with the `referrers`.  
  
You can also specify if you want to keep the API response (each on its own JSON file) or if you want to just view the data (as opposed to downloading it) from the response or the consolidated JSON database.  
  
There is no built in option to save the output to a text file but come on, just put `> output.txt` after the command and you are done.  
  
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
Only the last 14 days are taken into account.  
`v`: sort by `views`.  
`c`: sort by `clones`  
The default secondary sort is by `uniques`  
`o`: sort secondary by `count`.  
`r`: reverse the sort order.  
Default: alphabetically by repo name.  
  
`-c [k,u,v]`  
*Cache behavior.*  
Changes the way the cache is used and kept.  
`k`: keep a local copy of the API response JSONs.  
`u`: do not go online, use the local copy of the API JSONs to update the database and show the data.  
`v`: do not go online, view the database without accessing the API.  
Default: get the data from GitHub and do not save the JSONs cache.  
  
`> output.txt`  
*Save output.*  
Use at the end of the command.  
Saves a copy of the output to a text file.  
  
  
## Acknowledgements  
  
Enjoy and send feedback.  
***KipHub Traffic** is offered as is, with no guarantees whatsoever.*  
