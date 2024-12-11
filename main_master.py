from main import main
from helpers import GREEN, BLUE, RESET
import signal
import sys
# Define a signal handler for keyboard interruption
def signal_handler(sig, frame):
    print('Exiting gracefully...')
    sys.exit(0)

# Attach the signal handler to the SIGINT signal (Ctrl + C)
signal.signal(signal.SIGINT, signal_handler)

# List of animes
animes_raw = """
# Yashahime: Princess Half-Demon
# Baki
# Soul Eater
"""

animes = animes_raw.strip().splitlines()
animes = [x.strip() for x in animes]
animes = [x.replace(":", "") for x in animes]
animes = [x.replace("'", "") for x in animes]
animes = [x.replace(" ", "-") for x in animes]  # replaces spaces with "-" as expected for the function input
animes = [x for x in animes if x != ""]  # Remove empty strings from the list
animes = [x for x in animes if not x.startswith("#")]  # Remove lines starting with "#"
animes = [x for x in animes if not x.startswith("//")]  # Remove lines starting with "//"
animes = [x.split("=")[0] for x in animes]  # if you paste something like chaos-dragon=12  CAUTION: in this case you will have all small letter names

animes = [x.replace("-", " ") for x in animes]
animes = [x.title() for x in animes]
animes = [x.replace(" ", "-") for x in animes]

seasons = "all"  # you can comma "," separate values, use ":" for ranges and "all" for everything
episode = "7"  # does not take any effect, not implemented
thread_amount = 3
path = "output"
proxy = None
mode = ("download")
streamer = "VOE"
# streamer = "Vidoza"

loops = 3
for _ in range(loops):
    """
    re-run the process. 
    This is helpful in case any error occured on the way and will retry every failed download, keeping everything else
    intact. Usually you will experience at least a few connection errors, so it is a good idea to loop it over night.
    """
    for anime in animes:
        """
        Download anime each after another
        """
        main(f'{anime}', seasons, episode, thread_amount, path, proxy, mode, streamer)

# print(f'#####################')
# print(f'{GREEN}Downloads processes done, start inspection to check status{RESET}')
# print(f'#####################')
#
# mode = "inspect"  # run inspect for a pretty summary :)
# for anime in animes:
#     main(f'{anime}', seasons, episode, thread_amount, path, proxy, mode, streamer)

print(f'#####################')
print(f'All animes processed!')
for anime in animes:
    print(f'{BLUE}Processed anime{RESET}: {anime.replace("-", " ")}')
print(f'{GREEN}Have a nice day! :-){RESET}')
print(f'#####################')
