import requests
from bs4 import BeautifulSoup
from queue import Queue
from concurrent.futures import ThreadPoolExecutor
import threading
import time

from helpers import get_episodes_links, write_unique_line


# Constants
URL = "https://aniworld.to/animes"  # Replace with your target website URL
URL_BEGINNING = "/anime/stream/"
OUTPUT_PATH = "output_list_no_of_german_dubbed.txt"
OUTPUT_SORTED_PATH = OUTPUT_PATH.replace("txt", "") + "_sorted.txt"
NUM_THREADS = 100


def fetch_html(url):
    """Fetch the HTML content from a given URL."""
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to fetch the webpage. Status code: {response.status_code}")
        exit(1)
    return response.text

def parse_html(html_content):
    """Parse the HTML content using BeautifulSoup."""
    soup = BeautifulSoup(html_content, "html.parser")
    return [(a['title'], a['href']) for a in soup.find_all('a', title=True, href=True)]

def save_data(data):
    """Save extracted data to text files."""
    with open("extracted_titles_and_links.txt", "w", encoding="utf-8") as file:
        for title, href in data:
            file.write(f"Title: {title}\nLink: {href}\n\n")

    with open("extracted_valid_titles.txt", "w", encoding="utf-8") as file:
        for title, href in data:
            if URL_BEGINNING in href:
                title = href.replace(URL_BEGINNING, "")
                file.write(f'{title}\n')

def load_animes(filepath):
    """Load anime titles from a file."""
    with open(filepath, "r", encoding="utf-8") as file:
        return file.read().splitlines()

def get_number_of_german_episodes(anime, q_outputs):
    """Get the number of German-dubbed episodes for an anime."""
    seasons = "all"
    output_path = "output_list_german_animes"
    episode = ""
    proxy = None
    episodes_elem = get_episodes_links(anime, seasons, episode, output_path, proxy)
    num_german_titles = sum(1 for ep in episodes_elem if ep.name.strip())
    result = f'{anime}={num_german_titles}'
    q_outputs.put(result)
    return num_german_titles

def process_queue(animes, num_threads, completion_event, q_outputs, animes_processed):
    """Process items from a queue using a specified number of threads."""
    q = Queue()
    for anime in animes:
        if anime not in animes_processed:
            q.put(anime)

    def thread_task():
        while not q.empty():
            try:
                anime = q.get_nowait()
                get_number_of_german_episodes(anime, q_outputs)
            except Exception as e:
                print(f"Error occurred for {anime}: {e}")
            finally:
                q.task_done()

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        for _ in range(num_threads):
            executor.submit(thread_task)

    q.join()
    completion_event.set()

def monitor_processing(completion_event, q_outputs, output_filepath):
    """Monitor the processing status and save results."""
    while not (completion_event.is_set() and q_outputs.empty()):
        try:
            anime_num = q_outputs.get()
            write_unique_line(output_filepath, anime_num)
        except Exception as e:
            print(f"Error writing output: {e}")
        time.sleep(0.5)

def sort_and_save_ranking(filepath, output_sorted_filepath):
    """Sort the anime ranking by number of German-dubbed episodes and save it."""
    anime_ranking = {}
    with open(filepath, 'r') as file:
        for line in file.read().splitlines():
            title, num = line.split("=")
            anime_ranking[title] = int(num)

    sorted_ranking = dict(sorted(anime_ranking.items(), key=lambda item: item[1], reverse=True))
    with open(output_sorted_filepath, 'w') as file:
        for key, value in sorted_ranking.items():
            file.write(f'{key}={value}\n')

def remove_duplicate_lines(filepath):
    """Remove duplicate lines from a file."""
    with open(filepath, 'r') as file:
        lines = file.read().splitlines()
    with open(filepath, 'w') as file:
        file.write("")
    for line in lines:
        write_unique_line(filepath, line)

if __name__ == "__main__":

    html_content = fetch_html(URL)
    data = parse_html(html_content)
    save_data(data)
    print("Data extraction complete.")

    animes = load_animes("extracted_valid_titles.txt")
    q_outputs = Queue()

    try:
        with open(OUTPUT_PATH, 'r') as file:
            animes_processed = [line.split("=")[0] for line in file.read().splitlines()]
    except FileNotFoundError:
        animes_processed = []

    completion_event = threading.Event()
    process_thread = threading.Thread(target=process_queue, args=(animes, NUM_THREADS, completion_event, q_outputs, animes_processed))
    process_thread.start()

    monitor_processing(completion_event, q_outputs, OUTPUT_PATH)
    process_thread.join()

    sort_and_save_ranking(OUTPUT_PATH, OUTPUT_SORTED_PATH)
    remove_duplicate_lines(OUTPUT_PATH)
    remove_duplicate_lines(OUTPUT_SORTED_PATH)

    print("Processing complete.")
    print(f"Please inspect: {OUTPUT_SORTED_PATH}")
