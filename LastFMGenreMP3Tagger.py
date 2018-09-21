import pylast
import config
import eyed3
import argparse
import os

API_KEY = config.last_api_key
API_SECRET = config.last_api_secret
username = config.last_u
password_hash = pylast.md5(config.last_p)

network = pylast.LastFMNetwork(api_key=API_KEY, api_secret=API_SECRET,
                               username=username, password_hash=password_hash)

parser = argparse.ArgumentParser(description='Update genre tag of mp3s in folder using Last.FM')
parser.add_argument('-p', '--path', nargs=1, required=True, dest='path')
args = parser.parse_args()
folder = args.path[0]

genre_map = {}

# list of preferred genres in order of preference (i.e. favour 'post-rock' over 'post-metal' when both are present)
preferred_genres = ['blackgaze', 'dungeon synth', 'shoegaze', 'post-rock', 'post-metal', 'screamo', 'emo', 'slowcore',
                    'idm']


def get_top_tag(tags_list):
    ignore_tags = ['seen live', 'favorites']
    tag_names = []
    for tag in tags_list:
        tag_name = tag.item.name
        if tag_name not in ignore_tags:
            tag_names.append(tag_name)

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


def update_mp3_genre(mp3_file):
        artist = mp3_file.tag.artist
        # as long as the artist tag is not empty...
        if artist:
            print(mp3_file.tag.title)
            if artist in genre_map:
                mp3_file.tag.genre = genre_map[artist]
                mp3_file.tag.save()
                print('using cached genre %s' % genre_map[artist])
                return
            else:
                last_artist = network.get_artist(artist)
                if last_artist:
                    tags = last_artist.get_top_tags(8)
                    top_tag = get_top_tag(tags)
                    # 'IDM' needs to be all caps
                    top_tag = 'IDM' if top_tag == 'Idm' else top_tag
                    genre_map[artist] = top_tag

                    print('for the artist %s' % artist)
                    print('we have the last fm artist %s' % last_artist)
                    print('and the top tag is %s' % genre_map[artist])

                    mp3_file.tag.genre = genre_map[artist]

                    mp3_file.tag.save()


for dir_name, subdirList, file_list in os.walk(folder):
    print('Found directory: %s' % dir_name)
    for file_name in file_list:
        if file_name.endswith('.mp3'):
            file_path = os.path.join(dir_name, file_name)
            print(file_path)
            audio_file = eyed3.load(file_path)

            if not audio_file:
                # if the file couldn't be read, rename it and try again
                print('eyed3 returned None for file. Temporarily renaming file and trying again')
                temp_path = os.path.join(dir_name, "temp.mp3")
                os.rename(file_path, temp_path)
                audio_file = eyed3.load(temp_path)
                # if it still doesn't work, give up
                if not audio_file:
                    print('eyed3 returned None for file again. Terminating')
                    continue
                update_mp3_genre(audio_file)
                # name it back to the original
                os.rename(temp_path, file_path)
            else:
                update_mp3_genre(audio_file)
