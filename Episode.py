from bs4 import BeautifulSoup
import requests
import re

from Streamer import Streamer


class Episode:
    def __init__(self, episode_id, name, episode_num, url, episode_season, anime, output_path=""):
        self.output_path = output_path
        self.anime = anime
        self.anime_path = f'{output_path}/{anime.replace("-"," ")}' if len(output_path) > 0 else f'{anime.replace("-"," ")}'
        self.episode_id = episode_id
        self.name = name
        self.season = episode_season  # 2
        self.episode_num = episode_num  # Folge 31
        self.number = self.extract_episode_number(self.episode_num)  # 31
        self.url = url
        self.languages = ["GER-DUB"]   # ["GER-DUB", "GER-SUB", "ENG-SUB"]
        self.streaming_services = self.get_streamers()
        self.m3u8_url = None
        self.stamp = self.get_episode_stamp()  # S02E007
        self.filename = self.construct_episode_filename()  # ani-me-name S02E007 episode title
        self.season_folder_path = self.construct_season_folder_path()
        self.total_data_size = 0
        self.downloaded_data = 0
        self.progress = 0
        self.status = "Unknown"

    def get_streamers(self):
        """
        This will select streamers for the first valid language from the list
        """
        for language in self.languages:
            lang_code = {'GER-DUB': "1", "GER-SUB": "3", "ENG-SUB": "2"}
            try:
                content = requests.get(self.url).content
                soup = BeautifulSoup(content, 'html.parser')
                streamers = soup.find_all('li', class_='col-md-3')

                streamers_elem = []
                for streamer in streamers:
                    if streamer['data-lang-key'] == lang_code[language]:
                        """
                        "1" == GERMAN DUB
                        "3" == JAP - GER SUB
                        "2" == JAP - ENG SUB
                        """
                        link_id = streamer['data-link-id']
                        streaming_service = streamer.find('h4').text.strip()
                        link_target = streamer['data-link-target']
                        streamers_elem.append(Streamer(streaming_service, link_target, link_id))
                # i = 0
                # for _ in streamers_elem:
                #     if streamers_elem[i].name in {"VOE", "Doodstream"}:  # Not implemented
                #         del streamers_elem[i]
                # for streamer in streamers_elem:
                #     print(streamer.name)
                return streamers_elem
            except requests.RequestException as e:
                print(f"In Episode.get_streamers: Request failed: {e}")
                return []
            except Exception as e:
                print(f"In Episode.get_streamers: an error occured: {e}")
                return []

    def get_streamers_backup(self):
        try:
            content = requests.get(self.url).content
            soup = BeautifulSoup(content, 'html.parser')
            streamers = soup.find_all('li', class_='col-md-3')

            streamers_elem = []
            for streamer in streamers:
                if streamer['data-lang-key'] == "1":
                    """
                    "1" == GERMAN DUB
                    "3" == JAP - GER SUB
                    "2" == JAP - ENG SUB
                    """
                    link_id = streamer['data-link-id']
                    streaming_service = streamer.find('h4').text.strip()
                    link_target = streamer['data-link-target']
                    streamers_elem.append(Streamer(streaming_service, link_target, link_id))
            # i = 0
            # for _ in streamers_elem:
            #     if streamers_elem[i].name in {"VOE", "Doodstream"}:  # Not implemented
            #         del streamers_elem[i]
            # for streamer in streamers_elem:
            #     print(streamer.name)
            return streamers_elem
        except requests.RequestException as e:
            print(f"In Episode.get_streamers: Request failed: {e}")
            return []
        except Exception as e:
            print(f"In Episode.get_streamers: an error occured: {e}")
            return []

    def set_m3u8_url(self, streamer_name):
        for streamer in self.streaming_services:
            if streamer.name == streamer_name:
                self.m3u8_url = streamer.m3u8_url
                return streamer.m3u8_url
        self.m3u8_url = dict()
        return dict()

    def extract_episode_number(self, episode_num):
        try:
            return episode_num.split(" ")[1]
        except IndexError:
            return "Unknown"

    def check_status(self, total_data_size=None, downloaded_data=None):
        if total_data_size is not None:
            self.total_data_size = total_data_size
        if downloaded_data is not None:
            self.downloaded_data = downloaded_data

        if self.total_data_size == 0:
            self.status = "Not_started"
        elif self.total_data_size - self.downloaded_data == 0:
            self.status = "Done"
        else:
            self.status = "In progress or Failed"
        return self.status

    def get_episode_stamp(self):
        return f'S{pad_with_zeros(self.season, 2)}E{pad_with_zeros(self.number, 3)}'

    def construct_episode_filename(self):
        episode_filename = f'{self.anime} {self.stamp} {self.name}'
        episode_filename = sanitize_filename(episode_filename, 128)
        print(f'created filename: {episode_filename}')
        return episode_filename

    def construct_season_folder_path(self):
        main_folder = self.anime_path
        season_folder = f'S{pad_with_zeros(self.season, 2)}'
        folder_path = f'{main_folder}/{season_folder}'
        return folder_path

def pad_with_zeros(value, no_of_digits):
    """ Example usage:
    print(pad_with_zeros("2",3))    # Output: "002"
    print(pad_with_zeros("72",3))   # Output: "072"
    print(pad_with_zeros("172",3))  # Output: "172"
    print(pad_with_zeros("5172",3)) # Output: "5172"
    """
    # Convert the input to a string
    value_str = str(value)
    # Pad the string with leading zeros to ensure it has at least 3 characters
    padded_value = value_str.zfill(no_of_digits)
    return padded_value

def sanitize_filename(filename,length_limit=255):
    """  import re
    # Example usage:
    print(sanitize_filename("my<in:valid>file|name?.txt"))  # Output: "my_in_valid_file_name_.txt"
    print(sanitize_filename("valid_filename.txt"))          # Output: "valid_filename.txt"
    """
    # Define the set of invalid characters for these filesystems
    invalid_chars = r'[<>:"/\\|?*\x00-\x1F]'
    # Replace invalid characters with an underscore
    sanitized_filename = re.sub(invalid_chars, '_', filename)
    # Truncate the filename to 255 characters to ensure compatibility with most filesystems
    sanitized_filename = sanitized_filename[:length_limit]
    sanitized_filename = sanitized_filename.strip()
    return sanitized_filename