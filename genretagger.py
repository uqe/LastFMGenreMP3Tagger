import time
import pylast
import argparse
import os
from termcolor import colored

from mutagen import MutagenError
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.id3 import TCON

network = pylast.LastFMNetwork(
    api_key="0699f06d9be5baad7c56c389e9a9ee33", api_secret="599de309aabe91113b0da6782aa5555c")

parser = argparse.ArgumentParser(
    description='Update genre tag of mp3s in folder using Last.FM')
parser.add_argument('-p', '--path', nargs=1, required=True, dest='path')
args = parser.parse_args()
folder = args.path[0]

genre_map = {}
artists_to_skip = []

# list of preferred genres in order of preference (i.e. favour 'post-rock' over 'post-metal' when both are present)
preferred_genres = ['blackgaze', 'dungeon synth', 'shoegaze', 'indietronica',
                    'post-rock', 'post-metal', 'screamo', 'emo', 'slowcore', 'idm', 'jazz hop', 'chiptune']

correct_genre_names = {'Idm': 'IDM', 'Jazz Hop': 'Jazz-Hop'}


def get_top_tag(tags_list):
    if not tags_list:
        return None

    ignore_tags = ['seen live', 'favorites']
    tag_names = []
    for tag in tags_list:
        tag_name = tag.item.name
        if tag_name not in ignore_tags:
            tag_names.append(tag_name)

    if not tag_names:
        return None

    # if the most popular tag is a priority genre, just return it as it's likely exactly what we want
    if tag_names[0] in preferred_genres:
        return tag_names[0].title()

    # otherwise, we try to return the highest ranked preferred genre
    # first, create a list of preferred genres in the tag list retaining the order
    present_preferred_genres = [x for x in preferred_genres if x in tag_names]

    # if no preferred genre exists, return the most popular tag
    if not present_preferred_genres:
        return tag_names[0].title()

    return present_preferred_genres[0].title()


def update_music_file_genre(mp3_file, file_name):
    artist = ""

    if file_name.endswith('.flac'):
        artist = mp3_file["artist"][0]

    if file_name.endswith('.mp3'):
        artist = mp3_file.tags.getall("TPE1")[0].text[0]

    # as long as the artist tag is not empty...
    if artist and artist not in artists_to_skip:
        if artist not in genre_map:
            last_artist = network.get_artist(artist)
            if last_artist:
                try:
                    tags = last_artist.get_top_tags(8)
                    # print(tags)
                except pylast.WSError:
                    # artist can't be found - skip and prevent it from being tried again
                    print(colored((
                        '      Не могу найти артиста \'%s\' на ластике, поэтому пропускаю \n' % artist), 'red', 'on_grey', attrs=['bold']))
                    artists_to_skip.append(artist)
                    return

                top_tag = get_top_tag(tags)

                if not top_tag:
                    print(colored((
                        '      У артиста \'%s\' нет тегов на ластике, поэтому пропускаю \n' % artist), 'red', 'on_grey', attrs=['bold']))
                    artists_to_skip.append(artist)
                    return

                # Correct genre name (e.g. 'Idm' -> 'IDM') if necessary
                if top_tag in correct_genre_names:
                    top_tag = correct_genre_names[top_tag]

                genre_map[artist] = top_tag

        if file_name.endswith('.flac'):
            mp3_file["GENRE"] = genre_map[artist]

        if file_name.endswith('.mp3'):
            mp3_file.tags.add(TCON(text=[genre_map[artist]]))

        mp3_file.save()
        print('      Установил жанр: %s' % genre_map[artist], "\n")


for dir_name, subdirList, file_list in os.walk(folder):

    print(colored(('Обрабатываю папку: %s' %
          dir_name), 'green', attrs=['bold', 'dark'],))

    for file_name in file_list:
        if file_name.endswith('.flac') or file_name.endswith('.mp3'):
            file_path = os.path.join(dir_name, file_name)
            print(colored(('    Обрабатываю файл: %s' %
                  file_name), 'cyan', attrs=['bold']))

            try:
                if file_name.endswith('.flac'):
                    audio_file = FLAC(file_path)

                if file_name.endswith('.mp3'):
                    audio_file = MP3(file_path)

                if not audio_file:
                    print('БИТЫЙ ФАЙЛ?', file_path)
                else:
                    update_music_file_genre(audio_file, file_name)
                    time.sleep(0.3)
            except MutagenError:
                print("Loading failed :(")
