# AniDL

This is a python written video downloader for aniworld, running from command line or your IDE.

Currently focused only on GERMAN-DUBBED episodes.

# Usage

python main.py -options 

python main_master.py

python get_all_episodes_counted.py

# Options

  -h, --help            show this help message and exit
  
  -a ANIME, --anime ANIME
                        Specify the anime name in format "Ani-Me-Na-Me"
                        
  -s SEASONS, --seasons SEASONS
                        Season to download; seasons can be comma separated; a range of seasons can be passed using ":"; for movies, use "0"; for all seasons including movies, use "all"; to exclude a season (such as from "all" or a
                        range), start the number from "-"
                        
  -e EPISODE, --episode EPISODE
                        Episode to download - currently not supported!
                        
  -p PATH, --path PATH  Location where the downloaded episodes get stored
  
  -t THREADS, --threads THREADS
                        Amount of threads of downloads
                        
  -x PROXY, --proxy PROXY
                        enter an https proxys IP address (e.x 182.152.157.1:8080)
                        
  -m MODE, --mode MODE  modes: download, collect - collect list of titles, inspect - inspect the download status
  
  -ss STREAMING_SERVICE, --streaming_service STREAMING_SERVICE
                        name of preferred streaming service, type "all" if not care

# Examples

python main.py -a "Sword-Art-Online" -s "0,1:4,-3" -p "output" -m "collect"

python main.py -a "Sword-Art-Online" -s "all" -p "output" -m "download" -t 3 -ss "Vidoza"

python main.py -a "Sword-Art-Online" -p output -m "inspect"

# Features and limitations

Implemented streaming services:
* VOE
* Vidoza
* Streamtape

Modes:
* collect - collects only the list of German titles
* download - collect + download + inspect
* inspect - inspects the download logs for missing episodes

Episode title included in the file name.

Auto-retry from the same or another streamer in case of an error.

List all, list completed and list failed log files.

Auto skip successfully processed episodes in case of a retry (no dummy overwrites, but overwrites titles which are not logged to successfully completed).

Create convenient status summary for manual actions.

Only GERMAN-DUBBED episodes are scheduled to download (to be more precise: episodes having a German title), although it can be easily extended to GER-SUB and ENG-SUB cause the language codes are already known and only need to be parsed.

Proxy is not tested.

# Extras

Use get_all_episodes_counted.py in order to get a list of the most numerous available GER-DUB animes

Use main_master.py to automate the process over multiple animes

# Credits

This repo is an extension of the project available at https://github.com/inflac/AniworlDL
