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
# Ron Kamonohashi's Forbidden Deductions
# Ikki Tousen
# Shin Ikki Tousen
# Last Hope
# Edens Zero
# Tenjho Tenge
# Katsugeki Touken Ranbu
# Garo Vanishing Line
# Made in Abyss
# The Great Cleric
# God Eater
# Gantz
# Katsugeki: Touken Ranbu
# Cagaster of an Insect Cage
# Our Last Crusade or the Rise of a New World
# The World's Finest Assassin Gets Reincarnated in Another World as an Aristocrat
# Sengoku Basara Samurai Kings
# XxxHOLiC
# The God of High School
# Date a Bullet
# Terminator Zero
# Juni Taisen: Zodiac War
# Accel World
# Chaos Dragon
# Hunter x Hunter
Jeanne die Kamikaze Diebin

# pokmon=1249
# one-piece=1104                        //done
# detektiv-conan=512                    //done
# naruto-shippuden=509
# dragonball-z=308                      //done
# fairy-tail=294                        //done
# yu-gi-oh=237                          //done
# bleach=235                            //done
# boruto-naruto-next-generations=233
# naruto=223
# sailor-moon=203
# inuyasha=197                          //done
# bakugan-battle-brawlers=189           //done
# yu-gi-oh-gx=180                       //done
# my-hero-academia=171                  //done
# black-clover=170                      //done
# beyblade-metal-fusion=167
# dragonball-z-kai=158
# dragonball=157                        //done
# jojos-bizarre-adventure=155           //done
# beyblade=154
# hunter-x-hunter=150                   //done
# yu-gi-oh-arc-v=148                    //done
# dragonball-super=133                  //done
# captain-tsubasa-1983=128
# the-seven-deadly-sins=124             //done
# yu-gi-oh-5ds=116                      //done
# city-hunter=114                       
# sword-art-online=113                  //done
# digimon-digital-monsters=110
# adventures-of-maya-the-honeybee=104
# bakugan-battle-planet=101
# mila-superstar=101
# dragon-quest-the-adventure-of-dai=100
# attack-on-titan=100                   //done
# haikyu=95
# that-time-i-got-reincarnated-as-a-slime=86
# food-wars-shokugeki-no-sma=86
# slayers=84
# kurokos-basketball=82
# ranma=81                              //done
# baki=79
# vicky-the-little-viking=78
# dr-slump=74
# monster=74
# monster-rancher=73                    //done
# fullmetal-alchemist-brotherhood=68    //done
# demon-slayer-kimetsu-no-yaiba=65
# dragonball-gt=64                      //done without titles
# shaman-king=64
# to-love-ru=64
# danmachi-is-it-wrong-to-try-to-pick-up-girls-in-a-dungeon=62
# highschool-dxd=61
# black-butler=60
# cardcaptors=59
# dr-stone=58
# code-geass-lelouch-of-the-rebellion=58
# fatekaleid-liner-prisma-illya=58
# blue-exorcist=56
# tsubasa-chronicle=55
# rezero-starting-life-in-another-world=55
# when-they-cry=55
# wedding-peach=55
# star-blazers-2199-space-battleship-yamato=54
# overlord=54
# ghost-in-the-shell-stand-alone-complex=54
# the-ancient-magus-bride=54
# ikki-tousen=53
# alle-meine-freunde=52
# fullmetal-alchemist=52
# the-great-adventures-of-robin-hood=52
# the-jungle-book=52
# the-legend-of-snow-white=52
# the-legend-of-zorro=52                //done
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
