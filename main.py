import threading
import argparse
import queue
import time
import sys
import requests
import signal
import os

from helpers import print_header, get_time_formated, parameter_checks, get_episodes_links, download_episode, set_stop_indicator
from helpers import get_stop_indicator
from helpers import GREEN, RED, BLUE, RESET
from helpers import progress
from helpers import event_log, save_list_of_titles, inspect_episodes_to_do, remove_ansi_sequences

from requests.exceptions import ConnectionError, Timeout, RequestException
import socket
from urllib3.exceptions import NameResolutionError


threads = []
threads_semaphore = None
tasks_to_do = 0


# Function to gracefully stop the program on CTRL + C
def stop_program(signum, frame, q):
    global threads, threads_semaphore
    if not get_stop_indicator(): #In case the program already handles a stop signal, do not run this function again
        set_stop_indicator()
    else:
        return

    if signum != None:
        print(f'\n[{get_time_formated(timeformat="%H:%M")}] Ctrl + C detected.')
    else:
        print("Internal Call for program termination.")

    print(f'[{get_time_formated(timeformat="%H:%M")}] Clearing queue ', end="") #Empty the queue to avoid new threads get started
    q.mutex
    while not q.empty():
        q.get()
        q.task_done()
    print(f"[{GREEN}Done{RESET}]")

    print(f'[{get_time_formated(timeformat="%H:%M")}] Clearing threads ', end="") #Join every thread for cleanup
    for thread in threads:
            thread.join()
            threads.remove(thread)
            threads_semaphore.release()
    print(f"[{GREEN}Done{RESET}]")

    print(f'[{get_time_formated(timeformat="%H:%M")}] Bye') #Say good bye ^^

def download_controller(anime:str, q:queue, path:str, proxy:dict, preferred_streamer:str):
    global threads_semaphore, tasks_to_do
    the_only_one_streamer_name = ""      # streamer name for testing. Normally set here ""
    # print(f'Set preferred streamer : {preferred_streamer}')

    if get_stop_indicator():
        return


    try:
        episode = q.get(timeout=1)
        stamp = episode.stamp
        filename = episode.filename
        anime_folder_path = episode.anime_path
        season_folder_path = episode.season_folder_path

        try:
            with open(f'{anime_folder_path}/completed_episodes.txt', 'r') as file:
                if episode.filename in file.read():
                    msg = f'--- You are lucky! "{GREEN}{episode.filename}{RESET}" was already done ---'
                    print(msg)
                    q.task_done()
                    tasks_to_do = tasks_to_do - 1
                    threads_semaphore.release()
                    return True
        except:
            pass

        if not preferred_streamer == "":  # make preferred streamer the first on the list
            # old_list = episode.streaming_services.copy()
            new_list = [streamer for streamer in episode.streaming_services if streamer.name == preferred_streamer]
            new_list.extend(episode.streaming_services)
            episode.streaming_services = new_list
        # for streamer in episode.streaming_services:
        #     print(streamer.name)
        # for streamer in episode.streaming_services:
        #     print(f'{streamer.}')
        if not the_only_one_streamer_name == "":  # get only selected streamer and drop other streamers
            episode.streaming_services = [streamer for streamer in episode.streaming_services if streamer.name == the_only_one_streamer_name]

        if len(episode.streaming_services) == 0:
            msg = f'{RED}{filename}{RESET} does not have an active or valid GERMAN-DUB streaming service, skipp it. See url for manual options: {episode.url}'
            print(f'{msg}')
            msg = remove_ansi_sequences(msg)
            event_log(msg, "failed_episodes", anime_folder_path)
            q.task_done()
            tasks_to_do = tasks_to_do - 1
            threads_semaphore.release()
            return True

        for streamer in episode.streaming_services: #While episodes_classes download isn't successful, try other streaming services
            try:
                req = requests.get(streamer.url, proxies=proxy)
                if req.status_code != 200:  # Check if the episode of streamer is up
                    continue
            except (ConnectionError, Timeout, RequestException) as e:
                print(f'Error in {stamp} {streamer}: {e}')
            except socket.gaierror as e:
                print(f'Error in {stamp} {streamer}: {e}')
            except NameResolutionError as e:
                print(f'Error in {stamp} {streamer}: {e}')

            else:
                if download_episode(episode, streamer, path, proxy) == True: #If download fails, continue the loop and try another streamer
                    print(f'[{get_time_formated(timeformat="%H:%M")}] Episode: [{BLUE}{stamp}{RESET}] [{GREEN}Done{RESET}]')
                    try:
                        del progress[stamp]    # del if still exist
                    except:
                        pass
                    msg = f'{GREEN}{filename}{RESET} completed from streamer {streamer.name}'
                    # print(msg)
                    msg = remove_ansi_sequences(msg)
                    event_log(msg, "completed_episodes", anime_folder_path)
                    q.task_done()
                    tasks_to_do = tasks_to_do - 1
                    threads_semaphore.release()
                    return True
                else:
                    try:
                        del progress[stamp]
                    except:
                        pass
                    try:
                        os.remove(f'{episode.season_folder_path}/{episode.filename}.mp4')
                    except Exception as e:
                        pass
                    msg = f'Episode {RED}{filename}{RESET} failed from streamer {streamer.name}. See url for manual options: {episode.url}'
                    # print(msg)
                    msg = remove_ansi_sequences(msg)
                    event_log(msg, "failed_episodes", anime_folder_path)
                    continue
        print(f"{RED}ERROR{RESET}: Episode {BLUE}{episode.stamp}{RESET} could not be downloaded by any streaming service.")
        threads_semaphore.release()
        print(f"{BLUE}INFO{RESET}: Episode {BLUE}{episode.stamp}{RESET} Putted back into queue.")
        q.put(episode)      #put failed episode back into queue
        return False #Return False in case episode could not be downloaded
    except queue.Empty: #Return True in case the queue is empty
        return True

def thread_operator(anime:str, q:queue, threads_amount:int, path:str, proxy:dict, preferred_streamer:str = ""):
    global threads, threads_semaphore, tasks_to_do

    while tasks_to_do > 0: #For every queue element, create a thread. passivly wait while max num of threads is reached
        threads_semaphore.acquire()
        thread = threading.Thread(target=download_controller, args=(anime, q, path, proxy, preferred_streamer))
        threads.append(thread)
        thread.start()
        
        for thread in threads: #For every active thread, check if he is still alive, otherwise join it.
            if not thread.is_alive():
                thread.join()
                threads.remove(thread)

        if get_stop_indicator(): #In case CTRL + C was detected, terminate the program
            stop_program(None, None, q)
            return

def thread_master(anime, q, threads_amount, path, proxy, preferred_streamer):
    threads_semaphore.acquire()
    threading_thread = threading.Thread(target=thread_operator, args = (anime, q, threads_amount, path, proxy, preferred_streamer))
    threading_thread.start()
    # while not get_stop_indicator():
    while not (tasks_to_do <= 0 or get_stop_indicator()):
        sorted_by_keys = dict(sorted(progress.items()))
        print(f'[{get_time_formated(timeformat="%H:%M:%S")}] {sorted_by_keys}, Tasks_to_do: {tasks_to_do}', end="\r")
        # print(f'{sorted_by_keys}', end='\r')
        time.sleep(1)
    threads_semaphore.release()
    threading_thread.join()
    return

def startup(anime=None, seasons=None, episode=None, threads_amount=None, path=None, proxy=None, mode=None, streamer=None):
    #Get episode Links with for all Hosters of an episode
    if mode in ["download", "collect"]:
        global tasks_to_do
        print(f'[{get_time_formated(timeformat="%H:%M")}] Episodes queued ', end='\n', flush=True)
        episodes = get_episodes_links(anime=anime, seasons_requested_raw=seasons, episode=episode, output_path=path, proxy=proxy)
        save_list_of_titles(episodes)

    # print(f'mode in startup is: {mode}')

    if mode == "download":
        #Put Episodes into a queue
        # print(f'Making queue!')
        q = queue.Queue()
        for episode in episodes:
            q.put(episode)
            tasks_to_do = tasks_to_do + 1
        print(f'[{GREEN}Done{RESET}]')
        print(f'Videos scheduled to download: {tasks_to_do}')
        # Register signal handler for Ctrl + C
        signal.signal(signal.SIGINT, lambda sig, frame: stop_program(sig, frame, q))

        #Start threads with downloading tasks
        # thread_operator(anime, q, threads_amount, path, proxy)
        thread_master(anime, q, threads_amount, path, proxy, streamer)

    if mode in ["inspect", "download"]:
        try:
            inspect_episodes_to_do(anime, path, episodes)
        except:
            inspect_episodes_to_do(anime, path)


def main(anime:str, seasons:str, episode:str, threads:int, path:str, proxy:dict, mode:str, streamer:str):
    # print(f'mode in main is: {mode}')
    threads = threads + 1  # add a thread for the thread_master which manages other threads
    global threads_semaphore
    # print_header()
    print(f'[{get_time_formated(timeformat="%H:%M")}] AniDL started')

    threads_semaphore = threading.Semaphore(threads) #create a semaphore with the maximum amount of threads 

    parameter_checks(anime, seasons, episode, threads, path, proxy, mode, streamer)
    startup(anime=anime, seasons=seasons, episode=episode, threads_amount=threads, path=path, proxy=proxy, mode=mode, streamer=streamer)


if __name__ == '__main__':

    if len(sys.argv) == 1:    #sys.argv[0] is function name, i guess... hence there is 1 argument passed if no arguments are passed
        anime = "DGray-Man"       #remember not to use spaces, use "-" instead. If not sure, check the link in the website
        seasons = "all"       # "all"               # you can comma "," separate values, use ":" for ranges and "all" for everything
        episode = "7"               #does not take any effect, not implemented
        thread_amount = 3
        path = "output"
        proxy = None
        mode = "collect"
        streamer = "VOE"
        # streamer = "Vidoza"

        main(anime, seasons, episode, thread_amount, path, proxy, mode, streamer)
    else:
        # param1 = sys.argv[1] ...
        parser = argparse.ArgumentParser(description='A simple program with argparse')
        parser.add_argument('-a', '--anime', required=True, help='Specify the anime name')
        parser.add_argument('-s', '--seasons', required=False, default="all", help='Season to download')
        parser.add_argument('-e', '--episode', help='Episode to download - currently not supported!')
        parser.add_argument('-p', '--path', required=False, type=str,
                            help='Location where the downloaded episodes_classes get stored')
        parser.add_argument('-t', '--threads', type=int, default=2, help='Amount of threads')
        parser.add_argument('-x', '--proxy', type=str, default=None,
                            help='enter an https proxys IP address (e.x 182.152.157.1:8080)')
        parser.add_argument('-m', '--mode', type=str, default="collect", help='modes: download, collect, inspect')
        parser.add_argument('-ss', '--streaming_service', type=str, default="any", help='name of preferred streaming service, type "all" if not care')

        args = parser.parse_args()
        anime = args.anime
        seasons = args.seasons
        episode = args.episode
        thread_amount = args.threads
        path = args.path
        proxy_ip = args.proxy
        mode = args.mode
        streamer = args.streaming_service

        if proxy_ip != None:  # Configure proxy dict
            proxy = {'https': 'https://' + proxy_ip}
        else:
            proxy = None

        main(anime, seasons, episode, thread_amount, path, proxy, mode, streamer)

        # main.py -a Fairy-Tail -s 7 -p S01 -t 1