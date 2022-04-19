import time
import sys
import os
import random

#WhoSampled
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait

#Soundcloud
import math
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options

# Spotify
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials , SpotifyOAuth

import pprint



# userID = ''
# https://open.spotify.com/user/{USER-ID}

# SPOTIFY API CREDENTIALS
_client_secret = ""
_client_id = ""
_redirect_uri = ""





def delay_print(s):
	for c in s:
		sys.stdout.write(c)
		sys.stdout.flush()
		time.sleep(0.05)

def main():
    delay_print('Oyama Productions\n')
    time.sleep(2.5)

    delay_print('\nPlease choose a streaming service...\n')
    print('1 - SoundCloud')
    print('2 - Spotify')
    option = input('??? : ')

    if option == '1':
        SoundCloud()
    elif option == '2':
        spotify()
    else:
        print('ERROR: INVALID OPTION! ')

def SoundCloud():
    try:
        #PLAYLIST EXTRACTION
        username = input('\nEnter Soundcloud Username: ')
        howmany = input('Enter how many songs User liked: ')
        time.sleep(1)

        delay_print('\nVibing with '+ str(username)+'\n')

        options = Options()
        options.headless = True
        driver = webdriver.Firefox(options = options)

        driver.get("https://soundcloud.com/"+str(username)+"/likes")
        time.sleep(1)

        elem = driver.find_element_by_tag_name("body")

        no_of_pagedowns = int(howmany)*.7
        while no_of_pagedowns>0:
            elem.send_keys(Keys.PAGE_DOWN)
            time.sleep(1)
            no_of_pagedowns-=1
            print(no_of_pagedowns, 'pages left...')

        song_div = driver.find_elements_by_class_name("soundTitle__usernameTitleContainer")
        song_count = 0
        with open('likes.txt', 'a', encoding='utf-8') as f:
            for x in song_div:
                song_count += 1
                print(song_count)
                print (x.text , "\n")
                f.write(x.text)
                f.write('\n')
                f.write('\n')

        whosampled(driver, 'likes.txt', 1 , 3)

    except Exception as e:
        print(e)
        driver.quit()
    driver.quit()

def spotify():
    userID = input("Please enter spotify user ID: ")
    delay_print('\n 1 : Select playlist')
    delay_print('\n 2 : All Playlist Songs (doesnt look for dupes)')
    delay_print('\n 3 : All saved / liked songs\n')
    time.sleep(1)
    option = input("Please choose an option: ")

    print('\n')

    if option == '1':
        playlistDict = get_Playlists(userID)
        counter = 0
        keyIndex = []
        for x , y in playlistDict.items():
            keyIndex.append(x)
            print( '  ' + str(counter) + '--' +   str(x)  )
            counter += 1
        option = int(input("Please enter album index number: "))


        songOnly = []
        for i in playlistDict[ keyIndex[option] ]:
            print(i)
            songOnly.append(i[1])
        delay_print("\nTotal songs : {}\n".format(len(songOnly)) )

        while True:
            proceed = input("Please type 'YES' to begin assesment... ")
            if proceed.lower() == "yes":
                SPOTIFYwhosampled(songOnly)
                break
            else:
                delay_print("\nok ill wait.... \n")
                time.sleep()

    elif option == '2':
        songOnly = []
        playlistDict = get_Playlists(userID)

        for key , value in playlistDict.items():
            pprint.pprint(value)
            songOnly.append(value[1])

        while True:
            proceed = input("Please type 'YES' to begin assesment... ")
            if proceed.lower() == "yes":
                SPOTIFYwhosampled(songOnly)
                break
            else:
                delay_print("\nok ill wait.... \n")
                time.sleep(2)

    elif option == '3':
        songs = []
        songMeta = get_savedSongs()
        for x in songMeta:
            songs.append(x[1])
        SPOTIFYwhosampled(songs)
def get_Playlists(userID):
    # spotify login
    global _client_secret , _client_id
    
    client_credentials_manager = SpotifyClientCredentials(client_id=_client_id, client_secret=_client_secret)
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)


    playlists = sp.user_playlists(userID)
    cleanData_Albums = {}
    while playlists:

        # playlist item
        soung_count = 0
        for i in range(0 , len(playlists['items']) , 1) :
            playlist_songs = []
            albumDictionary = playlists['items'][i]
            ALLsongsDictionary = sp.user_playlist_tracks(user=userID, playlist_id=albumDictionary['id'])
            # print(albumDictionary['name'])

            # All songs in playlist item
            for x in ALLsongsDictionary['items']:
                track = x['track']
                # print(track)
                playlist_songs.append( ( track['artists'][0]['name'] , track['name']  )  )
            
            # add all songs from album into a value for cleanData_Albums
            cleanData_Albums.update({albumDictionary['name'] : playlist_songs })


        # albumDictionary KEYS!!!
        # -collaborative
        # -description
        # -external_urls
        # -href
        # -id
        # -images
        # -name
        # -owner
        # -primary_color
        # -public
        # -snapshot_id
        # -tracks
        # -type
        # -uri


        # ALL SONGS IN ALBUM DICTIONARY KEYS!!!
        # -added_at
        # -added_by
        # -is_local
        # -primary_color
        # -track
        # -video_thumbnail


        # INDIVISUAL SONG DICTIONARY!!!
        # -album
        # -artists
        # -available_markets
        # -disc_number
        # -duration_ms
        # -episode
        # -explicit
        # -external_ids
        # -external_urls
        # -href
        # -id
        # -is_local
        # -name
        # -popularity
        # -preview_url
        # -track
        # -track_number
        # -type
        # -uri




        if playlists['next']: #next page check
            playlists = sp.next(playlists)
        else:
            playlists = None
    return cleanData_Albums 
def get_savedSongs():
    global _client_secret , _client_id , _redirect_uri

    # spotify login
    scope = "user-library-read"
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope  , client_id= _client_id, client_secret= _client_secret , redirect_uri =  _redirect_uri  ) )

    all_songs = []
    results = sp.current_user_saved_tracks()
    totalLikedSongs = int(results['total'])
    while results:   # LOOKUP SONGS
        for idx, item in enumerate(results['items']):
            track = item['track']
            all_songs.append( (track['artists'][0]['name'], track['name']) )
            

            # TRACK DICTIONARY KEYS
            # album
            # artists
            # available_markets
            # disc_number
            # duration_ms
            # explicit
            # external_ids
            # external_urls
            # href
            # id
            # is_local
            # name
            # popularity
            # preview_url
            # track_number
            # type
            # uri


        if results['next']: #next page check
            results = sp.next(results)
        else:
            results = None

    return all_songs

def whosampled(driver , fileName , start , iteration):
    try:
        delay_print('\nFINDING SAMPLES...')
        driver.get("https://www.whosampled.com/")
        time.sleep(1)

        likes_file = open( fileName, "r", encoding="utf8")

        list_of_song_meta = []
        data = likes_file.readlines()
        for song_meta in data:
            data_word = song_meta.strip("\n")
            list_of_song_meta.append(data_word)


        for x in range(start, len(list_of_song_meta), iteration):
            time.sleep(2)
            song = list_of_song_meta[x]
            search = driver.find_element_by_xpath('//*[@id="searchInput"]')
            search.send_keys(song)
            search.send_keys(Keys.RETURN)

            delay_print('Searching...')
            time.sleep(2)

            try:
                top_connection = driver.find_element_by_class_name('connectionTitle').text
                print("\nSAMPLE FOUND")
                print(song)
                print(top_connection)

                with open('AcceptedConnections.txt', 'a', encoding='utf-8') as accept_file:
                    accept_file.write(str(top_connection))
                    accept_file.write('\n')
                    accept_file.write('\n')
                    accept_file.close()

                driver.get("https://www.whosampled.com/")

            except NoSuchElementException:
                print('\nDID NOT FIND\nNO CONNECTION----->', song)
                driver.get("https://www.whosampled.com/")

        likes_file.close()
        driver.quit()

    except Exception as e:
        print(e)
        driver.quit()

def SPOTIFYwhosampled(list_of_song_meta):
    try:
        options = Options()
        options.headless = True
        driver = webdriver.Firefox(options = options)

        delay_print('\nFINDING SAMPLES...')
        driver.get("https://www.whosampled.com/")
        time.sleep(1)

        for x in range( len(list_of_song_meta) ):
            time.sleep(2)
            song = list_of_song_meta[x]
            search = driver.find_element_by_xpath('//*[@id="searchInput"]')
            search.send_keys(song)
            search.send_keys(Keys.RETURN)

            delay_print('\nSearching...')
            time.sleep(2)

            try:
                top_connection = driver.find_element_by_class_name('connectionTitle').text
                print("\nSAMPLE FOUND")
                print(song)
                print(top_connection)

                with open('AcceptedConnections.txt', 'a', encoding='utf-8') as accept_file:
                    accept_file.write(str(top_connection))
                    accept_file.write('\n')
                    accept_file.write('\n')
                    accept_file.close()

                driver.get("https://www.whosampled.com/")

            except NoSuchElementException:
                print('\nDID NOT FIND\nNO CONNECTION----->', song)
                driver.get("https://www.whosampled.com/")

        likes_file.close()
        driver.quit()

    except Exception as e:
        print(e)
        driver.quit()



main()


