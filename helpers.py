import os
import re
import time
from datetime import datetime
from typing import Dict, Any

import platform
import subprocess
from bs4 import BeautifulSoup
from Episode import Episode
import threading
import sys
import os
import glob
import re
import requests
import json
import wget
from bs4 import BeautifulSoup
from yt_dlp import YoutubeDL
# from youtube_dl import YoutubeDL
import base64
import threading
import urllib
from requests.exceptions import ConnectionError, Timeout, ReadTimeout
import io


progress = {}


#Color Codes - ANSI escape codes
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
PURPLE = '\033[95m'
CYAN = '\033[96m'
WHITE = '\033[97m'
RESET = '\033[0m'

STOP_THREADS = False  #Indicator showing if the program should get terminated
THREAD_DATA = {}  #Dictionary to collect data about the downloading progress

data_update_mutex = threading.Lock()  #Mutex to lock writing in THREAD_DATA

# Global progress dictionary
progress = {}

def ensure_folder(folder_path, printit=False):
    """
    import os
    check if a folder exist, create it if not exist
    """
    # Check if the folder exists
    try:
        if not os.path.exists(folder_path):
            # If not, create the folder
            os.makedirs(folder_path)
            if printit:
                print(f"Folder '{folder_path}' created.")
        else:
            if printit:
                print(f"Folder '{folder_path}' already exists.")
    except FileExistsError:
        pass


def write_unique_line(file_path, line):
    """
    # Example usage
    file_path = 'example.txt'
    line_to_add = 'This is a unique line.'
    write_unique_line(file_path, line_to_add)
    """
    # Read the file to check for the line
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
            # Strip newlines for comparison
            lines = [l.strip() for l in lines]

            if line in lines:
                # print(f'The line "{line}" is already in the file.')
                return
    except FileNotFoundError:
        # If the file doesn't exist, we will create it
        pass

    # Write the line to the file if not present
    with open(file_path, 'a') as file:
        file.write(line + '\n')
    # print(f'Added the line "{line}" to the file.')


def remove_ansi_sequences(text):
    """
    Removes ANSI escape sequences from the given string.

    Args:
        text (str): The input string containing ANSI escape sequences.

    Returns:
        str: The string with ANSI escape sequences removed.
    """
    ansi_escape_pattern = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape_pattern.sub('', text)


def event_log(dataline: str, filename: str = "log", folderpath: str = "") -> None:
    """
    import os
    from datetime import datetime
    # Example usage:
    event_log("logs", "event_log", "This is a test log entry.")

    Logs an event with a timestamp to a specified file within a folder.
    Args:
        dataline (str): The data line to be logged.
        filename (str): The name of the log file (without extension).
        folderpath (str): The path to the folder where the log file will be stored.
    Creates the folder and/or file if they do not exist and appends
    the log entry in the format 'timestamp dataline' to the file.
    """
    # Ensure the folder exists
    os.makedirs(folderpath, exist_ok=True)
    # Create a full path to the file
    filepath = os.path.join(folderpath, f"{filename}.txt")
    # Create a timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Append the line to the file
    with open(filepath, "a") as file:
        file.write(f"{timestamp} {dataline}\n")
    print(f"{PURPLE}Logged to {filename}{RESET}: {timestamp} {dataline}")


def get_season(anime):
    url = "https://aniworld.to/anime/stream/" + anime
    counter_seasons = 1
    html_page = urllib.request.urlopen(url, timeout=50)
    soup = BeautifulSoup(html_page, features="html.parser")
    for link in soup.findAll('a'):
        seasons = str(link.get("href"))
        if "/staffel-{}".format(counter_seasons) in seasons:
            counter_seasons = counter_seasons + 1
    return counter_seasons - 1


def encoded_numbers_string_to_list(input_string: str = None) -> list[int]:
    """
    Function designed to decode input numbers passed as one string into a list of those numbers.
    Numbers are separated with ",", but using "a:b" can also a range from "a" to "b" be passed
    Output is sorted. A "-" excludes an element or range of elements from the result.
    # Example usage
    input_strings = ["3", "3,6", "3:6", "10,1:3,0,22:25", "10,1:3,0,22:25,-23", "0:30,-1,-10:15,20"]
    for string in input_strings:
        result = encoded_numbers_string_to_list(string)
        print(result)
    [3]
    [3, 6]
    [3, 4, 5, 6]
    [0, 1, 2, 3, 10, 22, 23, 24, 25]
    [0, 1, 2, 3, 10, 22, 24, 25]
    [0, 2, 3, 4, 5, 6, 7, 8, 9, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30]
    """
    if input_string is None:
        raise ValueError("No input string provided.")

    def switch_set(set1, set2, item, action):
        if action == "set1":
            set1.add(item)
        elif action == "set2":
            set2.add(item)
        else:
            raise ValueError(f'{action} not implemented')
        return set1, set2

    set1 = set()
    set2 = set()
    # Split input string by commas
    input_strings = input_string.split(",") if "," in input_string else [input_string]
    for input_str in input_strings:
        action = "set1"
        input_str = input_str.strip()

        if input_str.startswith("-"):
            action = "set2"
            input_str = input_str[1:].strip()

        if ":" in input_str:
            a, b = map(int, input_str.split(":"))
            items = range(a, b + 1)
        else:
            items = [int(input_str)]

        for item in items:
            set1, set2 = switch_set(set1, set2, item, action)
            # Convert sets to integers and compute the result
    result_set = set1 - set2
    result_list = sorted(result_set)
    return result_list


def decode_season_string(anime: str, season: str = "all") -> list:
    """
    Example input: "1", "1,8", "0:5", "10,1:3,0", "ALL"   # ":" indicates a range from - to
    Output is list of string
    """
    season_list = []
    if season.lower() == "all":
        no_of_seasons = get_season(anime)
        if no_of_seasons == 1:
            season = "0,1"
        elif no_of_seasons > 1:
            season = f'0,1:{no_of_seasons}'
        else:
            raise ValueError(f'No episodes_classes found for anime {anime}. Is the spelling correct?')
    season_list = encoded_numbers_string_to_list(season)
    season_list = list(map(str, season_list))
    return (season_list)

def get_timestamp():
    """
    from datetime import datetime
    # Example filename with timestamp
    filename = f'{timestamp}_file.txt'
    """
    # Create a timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return timestamp
def get_time_formated(timeformat=None):
    if timeformat == None:
        return time.time()
    return time.strftime(timeformat)


def print_header():
    with open("header", "r") as header:
        for line in header.readlines():
            print(line, end="")
        print("")
    return


def parameter_checks(anime: str, season: str, episode: str, threads: int, path: str, proxy: dict, mode: str, streamer: str):
    if proxy != None:
        req = requests.get("https://inflacsan.de", proxies=proxy)
        if req.status_code != 200:
            print(
                f"{RED}ERROR{RESET}: The given proxy returend status code: {BLUE}{req.status_code}{RESET} insted of {BLUE}200{RESET}.")
            exit(1)
        pass

    req = requests.get("https://aniworld.to/anime/stream/" + anime, proxies=proxy)
    if "messageAlert danger" in str(req.content):
        print(
            f"{RED}ERROR{RESET}: The name of the anime \"{anime}\" you provided is wrong. Please regard the anime naming schemea for this downloader.")
        exit(1)

    if threads > 5:
        print(f"{BLUE}INFO{RESET}: You are using a lot of threads.")

    ensure_folder(path)
    if not os.path.isdir(path):
        print(f"{RED}ERROR{RESET}: The path you provided do not exist or is not a path to a folder.")
        exit(1)

    modes = {"collect", "download", "inspect"}
    modes_desc = """Modes description:
    "collect" - collects list of episodes_classes and stores them to a file
    "download" - runs "collect" first and then downloads the episodes_classes in German. Afterwards, it runs "inspect"
    "inspect" - inspects the download status based on log files, listing the episodes_classes remaining to download
    """
    if mode not in modes:
        print(f"{RED}ERROR{RESET}: The mode {mode} you provided is not implemented. Available modes: {modes}.")
        print(modes)
        exit(1)

    implemented_streamers = {"VOE", "Vidoza", "Streamtape"}
    if not streamer in implemented_streamers:
        print(f"{RED}ERROR{RESET}: The streamer {streamer} you provided is not implemented. Available streamers: {implemented_streamers}.")
        exit(1)

    print(f'[{get_time_formated(timeformat="%H:%M")}] Parameter checks [{GREEN}Done{RESET}]')


def set_stop_indicator():
    global STOP_THREADS
    STOP_THREADS = True

def get_stop_indicator():
    global STOP_THREADS
    return STOP_THREADS

def get_episodes_links(anime=None, seasons_requested_raw="", episode="", output_path="", proxy=None):
    episodes_elem = []

    seasons = decode_season_string(anime, seasons_requested_raw)

    for season in seasons:
        if (int(season) == 0):
            url = "https://aniworld.to/anime/stream/" + anime + "/filme"
        else:
            url = "https://aniworld.to/anime/stream/" + anime + "/staffel-" + str(season)

        req = requests.get(url, proxies=proxy)

        soup = BeautifulSoup(req.content, 'html.parser')
        if (int(season) == 0):
            episodes = soup.find_all('tr', {'itemprop': 'episode'})
        else:
            episodes = soup.find_all('tr', {'itemprop': 'episode'})

        # print(f'Episodes length: {len(episodes_classes)}')

        for episode in episodes:
            episode_id = episode['data-episode-id']
            episode_name = episode.find('strong').text.strip()
            episode_num = episode.find('a').text.strip()
            if (int(season) == 0):
                episode_url = "https://aniworld.to/" + str(episode.find('a')['href'])
            else:
                episode_url = "https://aniworld.to/" + str(episode.find('a', itemprop='url')['href'])
            # print(f'episode id is: {episode_id}')
            # print(f'episode name is: {episode_name}')
            # print(f'episode num is: {episode_num}')
            # print(f'episode url is: {episode_url}')
            #         # >>>
            #         episode id is: 65
            #         episode name is: Wir dringen in Everlues Villa ein!
            #         episode num is: Folge 3
            #         episode url is: https://aniworld.to//anime/stream/fairy-tail/staffel-1/episode-3
            episodes_elem.append(
                Episode(episode_id, episode_name, episode_num, episode_url, season, anime, output_path))
    return episodes_elem


def download_from_url(url: str, stamp: str, title: str, season_folder_path: str, proxy: dict):
    progress[stamp] = "0%"
    extension = ".mp4"
    if url[-4:] != extension:
        extension = ".unkn"

    req = requests.get(url, stream=True, proxies=proxy)
    if req.status_code == 200:
        total_data_size = int(req.headers.get('content-length', 0))
        filepath = f'{season_folder_path}/{title}{extension}'
        ensure_folder(season_folder_path)
        with open(filepath, 'wb') as file:
            downloaded_data = 0
            for i, chunk in enumerate(req.iter_content(chunk_size=1024)):
                if get_stop_indicator():
                    file.close()
                    return False
                file.write(chunk)
                downloaded_data += len(chunk)
                data_update_mutex.acquire()
                # THREAD_DATA[stamp]=[total_data_size,downloaded_data] #Dict, containing information (not threadsafe!)
                percent = f"{round(downloaded_data / total_data_size * 100, 1)}%"
                progress[stamp] = percent
                data_update_mutex.release()
                # update_download_data()
            file.close()
            # THREAD_DATA.pop(stamp)
    return True

def download_from_m3u8(links: dict, progress_key: str, out_filename: str = "", folder_path: str = ""):
    """
    Return download finished status. WARNING: this does not necessarily mean that the file was downloaded successfully!
    Verify "progress" global variable for details.

    :param links: list of m3u8 links
    :param progress_key: episode stamp (e.g., "S01E14")
    :param out_filename: filename of the file to download (without extension)
    :param folder_path: path to the output folder
    :return: download finished status
    """
    progress[progress_key] = f'0%'
    if len(links) < 1:
        return False

    filepath = os.path.join(folder_path, out_filename + '.mp4')

    try:
        link = links.get('hls')
        if link:
            def progress_hook(d):
                if d['status'] == 'downloading':
                    percent_str = remove_ansi_sequences(d['_percent_str'])
                    number = round(float(percent_str.strip().replace('%', '')), 1)
                    progress[progress_key] = f"{number}%"
                    try:
                        number = round(float(percent_str), 1)
                        progress[progress_key] = f"{number}%"
                    except ValueError:
                        pass
                elif d['status'] == 'finished':
                    #                 when "finished", '_percent_str' jumps to 100%, even if an download error occured. Thet's not helpful...
                    try:  # so far, that part never happen
                        number = round(float(d['fragment_index']) / float(d['fragment_count']) * 100, 1)
                        progress[progress_key] = f"{number}%"
                    except:
                        pass

            class QuietLogger:
                def debug(self, msg): pass
                def warning(self, msg): pass
                def error(self, msg): print(msg)

            ydl_opts = {
                'outtmpl': filepath,
                'quiet': True,
                'no_warnings': True,
                'logger': QuietLogger(),
                'progress_hooks': [progress_hook],
                'format': 'best'
            }
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([link])
            return True
    except (ConnectionError, Timeout, ReadTimeout, Exception) as e:
        print(f"Error during HLS download {progress_key}: {e}")
        return False

    try:
        link = links.get('mp4')
        if link:
            # Capture wget output and suppress it
            original_stdout = sys.stdout
            sys.stdout = io.StringIO()  # Redirect stdout to capture output

            def parse_progress_output(output):
                """Parse wget output to extract progress percentage.
                TODO: This part was not tested and may not work as expected. Test this part
                """
                lines = output.getvalue().splitlines()
                for line in lines:
                    # Look for progress updates in wget output
                    if "%" in line:
                        try:
                            percent = float(line.split('%')[0].split()[-1])
                            progress[progress_key] = f"{percent:.1f}%"
                        except (ValueError, IndexError):
                            pass

            try:
                wget.download(link, out=filepath)
            finally:
                # Parse progress and restore stdout
                parse_progress_output(sys.stdout)
                sys.stdout = original_stdout

            return True
    except (ConnectionError, Timeout, ReadTimeout, Exception) as e:
        print(f"Error during MP4 download {progress_key}: {e}")
        return False

    return False

def download_episode(episode, streamer, path: str, proxy: dict):
    stamp = episode.stamp
    filename = episode.filename
    anime_folder_path = episode.anime_path
    season_folder_path = episode.season_folder_path
    print(
        f'[{get_time_formated(timeformat="%H:%M")}] Downloading episode: [{BLUE}{episode.stamp}{RESET}] from streamer: [{BLUE}{streamer.name}{RESET}]')

    req = requests.get(streamer.url, proxies=proxy)
    if req.status_code != 200:
        print(
            f'[{RED}ERROR{RESET}] Requesting the episodes_classes stream url returend a status code: {BLUE}{req.status_code}{RESET}')
        return False
    soup = BeautifulSoup(req.content, 'html.parser')

    def get_video_src(streamer):
        if streamer.name == "Vidoza":
            video_element = soup.find('source', {'type': 'video/mp4'})
            if video_element:
                video_src = video_element['src']
                return video_src
            else:
                print(f'[{RED}ERROR{RESET}] Video URL could not be found')
            return None
        elif streamer.name == "Streamtape":
            STREAMTAPE_PATTERN = re.compile(r'get_video\?id=[^&\'\s]+&expires=[^&\'\s]+&ip=[^&\'\s]+&token=[^&\'\s]+\'')
            video_src = STREAMTAPE_PATTERN.search(req.content.decode('utf-8'))
            if video_src != None:
                video_src = "https://" + streamer.name + ".com/" + video_src.group()[:-1]
                return video_src
            else:
                print(f'[{RED}ERROR{RESET}] Video URL could not be found')
            return None
        else:
            print(f'[{RED}ERROR{RESET}] The Streamer: {BLUE}{streamer.name}{RESET} is not supported')
            return None

    if streamer.name == "VOE":
        m3u8_url = episode.set_m3u8_url("VOE")
        # print(f"-----------")
        # print(m3u8_url)
        # print(f"-----------")
        if download_from_m3u8(m3u8_url, stamp, filename, season_folder_path):
            if float(progress[stamp].replace("%", "")) >= 97.5:   # no better idea so far :/ yt_dlp doesn't really return a finisched successfully status
                # print(f'[{get_time_formated(timeformat="%H:%M")}] Episode: [{BLUE}{stamp}{RESET}] [{GREEN}Done{RESET}]')
                del progress[stamp]
                return True
        del progress[stamp]
        return False
    #     elif streamer.name == "Doodstream":
    #         pass # TODO implement a downloading logic
    elif streamer.name in {"Vidoza", "Streamtape"}:
        video_src = get_video_src(streamer)
        if download_from_url(video_src, stamp, filename, season_folder_path, proxy):
            if progress[stamp] == "100.0%":
                # print(f'[{get_time_formated(timeformat="%H:%M")}] Episode: [{BLUE}{stamp}{RESET}] [{GREEN}Done{RESET}]')
                del progress[stamp]
                return True
        del progress[stamp]
        return False
    else:
        print(f'[{RED}ERROR{RESET}] The Streamer: {BLUE}{streamer.name}{RESET} is not implemented')
        return False
    return True


def save_list_of_titles(episodes_elements: list[Episode]):
    pathes = set()
    for episode in episodes_elements:
        anime_folder_path = episode.anime_path
        anime = episode.anime
        ensure_folder(anime_folder_path)
        path = f'{anime_folder_path}/{anime}_list_of_titles.txt'
        pathes.add(path)
        write_unique_line(path, episode.filename)

    no_of_episodes = len(episodes_elements)

    print(f'List of titles written to: {pathes}')
    print(f'No of episodes_classes : {no_of_episodes}')

def inspect_episodes_to_do(anime, output_path, episodes_classes = []):
    def get_stamp(text):
        pattern = r'S\d{2}E\d{3}'  # Find all matches in the text
        matches = re.findall(pattern, text)
        return matches[0]
    def search_episode_url_from_episodes(episode_filename, episodes_classes):
        if len(episodes_classes) == 0:
            return ""
        stamp = get_stamp(episode_filename)
        for episode_class in episodes_classes:
            if stamp == episode_class.stamp:
                return episode_class.url

    print(f'####################################   Inspection of download log files started   ####################################')
    aname = anime.replace("-", " ")
    episodes_all = []
    episodes_done = []
    episodes_to_do = []
    anime_folder_path = f'{output_path}/{aname}' if not output_path == "" else f'{aname}'
    path = f'{anime_folder_path}/completed_episodes.txt'
    if not os.path.isfile(path):
        print(f'Missing required log files, nothing to inspect.')
        return
    with open(path, 'r') as file:
        episodes_done = file.read()
    path = f'{anime_folder_path}/{anime}_list_of_titles.txt'
    if not os.path.isfile(path):
        print(f'Missing required log files, nothing to inspect.')
        return
    with open(path, 'r') as file:
        episodes_all = file.read().splitlines()

    # path = f'{anime_folder_path}/{get_timestamp()}_to_do_inspection_results.txt'
    path = f'{anime_folder_path}/to_do_inspection_results.txt'
    with open(path, 'a') as file:
        for episode in episodes_all:
            if not episode in episodes_done:
                episodes_to_do.append(episode)
                msg = f'{get_timestamp()} Episode not done: {episode} {search_episode_url_from_episodes(episode, episodes_classes)}'
                print(msg)
                file.write(f'{msg}\n')
        if len(episodes_to_do) == 0:
            file.write(f'{get_timestamp()} Everything DONE, YAY!\n')

    print(f'{BLUE}Inspection finished.{RESET} Titles not found in "{anime_folder_path}/completed_episodes.txt": {len(episodes_to_do)}')
    print(f'{BLUE}Please check output.{RESET} Episodes without titles may not be available in your selected language, so that\'s normal')
    print(f'{PURPLE}Result logged to:{RESET} {path}')