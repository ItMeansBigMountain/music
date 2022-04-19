
# requesting data and converting api info to base64
import requests
import json
import base64

# display popup to auth
import webbrowser

# detect url from pop up window
from pywinauto import Application
from pywinauto.findwindows import find_windows

# debugging
import time
import pprint

# webcrawl lyrics
import bs4

# WATSON AI
import watson

import statistics

# TODO turn into secrets
spotify_clientId = ''
spotify_clientSecret = ''
genius_clientId = ''
genius_clientsECRET = ''
callbackURL = 'https://example.com/callback/'
API_COOLDOWN_RATE = 3





'''
PROCEDURE

auth user to login (permission/consistincy differences)
after pop up auth we check all the songs in each playlist
make arrays for each playlist filled with the song's meta-data


ENDPOINTS
https://developer.spotify.com/documentation/web-api/reference/


GENIUS auth
    https://api.genius.com/oauth/authorize


-----------------------------------------------------------------------------

NOTE ctrl + f "//phase" to see speggetti code

build dictionaries filled with 
    each album and the bpm of each song
    each playlist and the bpm of each song
    all user likes and the bpms of each song


Run samples through watson sentiment
    append sentiment to each song's dictionary
        get avg and frequency of each verse and then find average of all verses / frequency counter


Draw out data on white board.... youll need it lol


# USER MUSIC GROUPS
type(likes) = <class 'list'>
type(albums) = <class 'dict'>
type(playlists) = <class 'dict'>


'''







# auth SPOTFITY scopes
scopes = [
 'ugc-image-upload',
 'user-read-recently-played',
 'user-top-read',
 'user-read-playback-position',
 'user-read-playback-state',
 'user-modify-playback-state',
 'user-read-currently-playing',
 'app-remote-control',
 'streaming',
 'playlist-modify-public',
 'playlist-modify-private',
 'playlist-read-private',
 'playlist-read-collaborative',
 'user-follow-modify',
 'user-follow-read',
 'user-library-modify',
 'user-library-read',
 'user-read-email',
 'user-read-private'
]
spotty_full_permission = ''
for i in scopes:
    spotty_full_permission += i + ' '


# genius scopes
genius_scopes = [
    'me',
    'create_annotation',
    'manage_annotation',
    'vote',
]
genius_full_permission = ''
for i in genius_scopes:
    genius_full_permission += i + ' '







#  Authorization by getting token
def authorize_spotify_NO_USER():
    url = "https://accounts.spotify.com/api/token"
    headers = {}
    data = {}

    # Encode as Base64
    message = f"{spotify_clientId}:{spotify_clientSecret}"
    messageBytes = message.encode('ascii')
    base64Bytes = base64.b64encode(messageBytes)
    base64Message = base64Bytes.decode('ascii')

    headers['Authorization'] = f"Basic {base64Message}"
    data['grant_type'] = "client_credentials"


    r = requests.post(url, headers=headers, data=data).json()

    token = r['access_token']
    return token
def authorize_spotify_IMPLICIT(): # sleeps for 3 seconds and detects open chrome window

    headers = {
        'client_id' : spotify_clientId,
        'response_type' : 'token',
        'redirect_uri' : callbackURL,
        'scope' : spotty_full_permission,
    }

    # open url on browser
    url = f"https://accounts.spotify.com/authorize?client_id={headers['client_id']}&response_type={headers['response_type']}&redirect_uri={headers['redirect_uri']}&scope={headers['scope']}"
    browser = webbrowser.open(url, new=1)


    time.sleep(API_COOLDOWN_RATE)


    # detect url from open apps
    # find_windows(best_match='chrome')
    app = Application(backend='uia')
    app.connect(title_re=".*Chrome.*")
    dlg = app.top_window()
    url = dlg.child_window(title="Address and search bar", control_type="Edit").get_value()

    # get auth code after user accepts
    auth_code_token =  url.split("=")[1].split("&")[0] 
    return auth_code_token
def authorize_spotify_REFRESHABLE(): # sleeps for 3 seconds and detects open chrome window

    headers = {
        'client_id' : spotify_clientId,
        'response_type' : 'code',
        'redirect_uri' : callbackURL,
        'scope' : spotty_full_permission,
    }

    # open url on browser
    url = f"https://accounts.spotify.com/authorize?client_id={headers['client_id']}&response_type={headers['response_type']}&redirect_uri={headers['redirect_uri']}&scope={headers['scope']}"
    browser = webbrowser.open(url, new=1)


    time.sleep(API_COOLDOWN_RATE)



    # detect url from open apps
    app = Application(backend='uia')
    app.connect(title_re=".*Chrome.*")
    dlg = app.top_window()
    url = dlg.child_window(title="Address and search bar", control_type="Edit").get_value()



    # get auth code after user accepts
    auth_code  =  url.split("?")[1].split("=")[1] 



    url = "https://accounts.spotify.com/api/token"
    headers = {}
    data = {}

    # Encode as Base64
    message = f"{spotify_clientId}:{spotify_clientSecret}"
    messageBytes = message.encode('ascii')
    base64Bytes = base64.b64encode(messageBytes)
    base64Message = base64Bytes.decode('ascii')

    headers['Authorization'] = f"Basic {base64Message}"
    data['grant_type'] = "authorization_code"
    data['code'] = auth_code
    data['redirect_uri'] = callbackURL



    r = requests.post(url, headers=headers, data=data).json()
    token = r['access_token']
    return token

def Oauth_function( base_url , CLIENT_ID , callback , scope ,  clientsECRET , res_type):
    url = f'{base_url}?client_id={CLIENT_ID}&redirect_uri={callback}&scope={scope}&response_type={res_type}&client_secret={clientsECRET}'

    browser = webbrowser.open(url, new = 1)
    time.sleep(API_COOLDOWN_RATE)

    # detect url from open apps
    # find_windows(best_match='chrome')
    app = Application(backend='uia')
    app.connect(title_re=".*Chrome.*")
    dlg = app.top_window()
    url = dlg.child_window(title="Address and search bar", control_type="Edit").get_value()

    # get auth code after user accepts
    auth_code_token =  url.split("=")[1].split("&")[0] 
    return auth_code_token






# user info
def user_profile(token):
    user_info_url = f"https://api.spotify.com/v1/me"
    headers = {"Authorization": "Bearer " + token}
    res = requests.get(url= user_info_url ,  headers=headers ).json()
    return res



# user music
def user_likes(token):
    playlistUrl = f"https://api.spotify.com/v1/me/tracks"
    headers = {"Authorization": "Bearer " + token}
    
    # LOOKUP SONGS
    results = requests.get(url=playlistUrl, headers=headers).json()
    all_songs = []
    totalLikedSongs = int(results['total'])
    while results:   
        for idx, item in enumerate(results['items']):
            track = item['track']
            song_info = {
                "artists"  : [  track['artists'][i]['name']  for i in range(len(track['artists']))  ],
                "name"  :  track['name'] ,
                "id"  :  track['id'],
                "popularity"  :  track['popularity']
            }
            all_songs.append( song_info )
       
        #next page check
        if results['next']:
            results = requests.get(url=results['next'], headers=headers).json()
        else:
            results = None

    return all_songs
def user_albums(token):
    playlistUrl = f"https://api.spotify.com/v1/me/albums"
    headers = {"Authorization": "Bearer " + token}
    results = requests.get(url=playlistUrl, headers=headers).json()

    # GRAB ALBUMS
    all_albums = {}
    count = 0
    while results:  
        for item in results['items']:
            album = item['album']
            all_albums[count] =  {
                'name' : item['album']['name'],
                "genres" : album['genres'],
                "id" : album['id'],
                "popularity" : album['popularity'],
                "songs" : [],
            }
            # ADD SONGS
            for track in item['album']['tracks']['items']:
                all_albums[count]['songs'].append(   (track['id'] , track['name']    ,  [i['name'] for i in track['artists']  ]  )   )
            count += 1

        if results['next']: #next page check
            results = requests.get(url=results['next'], headers=headers).json()
        else:
            results = None
    
    
    
    return all_albums
def user_playlists(token):
    playlistUrl = f"https://api.spotify.com/v1/me/playlists"
    headers = {"Authorization": "Bearer " + token}
    results = requests.get(url=playlistUrl, headers=headers).json()

    all_playlists = {}
    count = 0
    # EVERY PLAYLIST
    while results:   
        for item in results['items']:
            all_playlists[count] =  {
                'owner' : item['owner']['display_name'],
                'name' : item['name'],
                "description" : item['description'],
                "id" : item['id'],
                "songs" : [],
            }

            # LOOKUP SONGS
            pl_tracks_call = requests.get(url=item['tracks']['href'] , headers = headers).json()
            while pl_tracks_call:
                for track in pl_tracks_call['items']:
                    all_playlists[count]['songs'].append(   (track['track']['id'] , track['track']['name']  ,[ i['name'] for i in track['track']['artists']  ] )   )
            
                # PAGINATION [TRACKS]
                if pl_tracks_call['next']:
                    pl_tracks_call = requests.get(url=pl_tracks_call['next'] , headers = headers).json()
                else:
                    pl_tracks_call = None
            
            count += 1

         # PAGINATION [PLAYLISTS]
        if results['next']:
            results = requests.get(url=item['next'] , headers = headers).json()
        else:
            results = None
    return all_playlists






# analysis //phase 1
def _song_analysis_details(token , song_id , details : bool , song_title , artist_name): 
    info = f"https://api.spotify.com/v1/audio-features/{song_id}"
    headers = {"Authorization": "Bearer " + token}
    
    # fetch data
    res = requests.get(url=info, headers=headers).json()

    # SONG DETAIL DOUBLE FEATURE of the function
    if details:
        analysis = requests.get( url = res['analysis_url'], headers = headers ).json()
        pprint.pprint( analysis.keys()  );print("\n")
        pprint.pprint( analysis['track']   )
        return analysis


    # API COOL DOWN ERROR HANDLING
    while 'error' in res.keys():
        print(f'< {song_id} > got an error\n waiting for api cooldown')
        time.sleep(API_COOLDOWN_RATE)
        res = _song_analysis_details(token, song_id , details  )
    
    # append WATSON AI to SOTIFY results  (master dictionary of clean watson frequencies)
    res['ai'] = _watson_lyric_analysis( song_title, artist_name)
    return res





# This function will automatically clean nlu data from watson //phase 2
def _watson_lyric_analysis(  song_title, artist_name):
    print(f"Analyzing {artist_name} : {song_title}")
    lyrics = _request_song_info(genius_token , song_title , artist_name )

    # NLU
    song_ai = []
    nlu = None
    if lyrics:
        for bar in lyrics:
            try:
                nlu = watson.ai_to_Text( bar )
                song_ai.append(nlu)
            except Exception as e:
                pass
        nlu =  watson.averages_calc(song_ai)
    else:
        print("No lyrics found\n")

    context = {
        'lyrics' : lyrics,
        'nlu' : nlu,
        # 'tone' : tone
    }
    return context





# AVERAGING FUNCTIONS
def group_avg_atrributes(token , group : dict()  ): #lol get it?
    print(f'there are {len(group)} groups found')

    song_stats = {}
    for x in group.keys():
        
        # populate song arr
        amount = len(group[x]['songs'])
        song_stats[group[x]['name']] = []
        for name in group[x]['songs']:
            song = _song_analysis_details(token, name[0] , False )
            song_stats[group[x]['name']].append(song)
        

        # populate group attribs
        group_avg = {
            'acousticness' : [],
            'danceability' : [],
            'duration_ms' : [],
            'energy' : [],
            'instrumentalness' : [],
            'liveness' : [],
            'loudness' : [],
            'speechiness' : [],
            'tempo' : [],
            'valence' : [],
        }
        for song in song_stats[group[x]['name']]:
            for key in group_avg.keys():
                group_avg[key].append( song[key] )
        song_stats[group[x]['name']] = group_avg
        
        
        # average of group attribs
        for stat in song_stats[group[x]['name']].keys():
            song_stats[group[x]['name']][stat] = "{:.4f}".format(sum(song_stats[group[x]['name']][stat]) / len(song_stats[group[x]['name']][stat]))

        # slap amount of songs in that dic
        song_stats[group[x]['name']]['amount'] = amount

    pprint.pprint( song_stats )
    return song_stats







def likes_avg_atrributes(token , group : list()  ): 
    # populate song arr
    song_stats  = {
        'acousticness' : [],
        'danceability' : [],
        'duration_ms' : [],
        'energy' : [],
        'instrumentalness' : [],
        'liveness' : [],
        'loudness' : [],
        'speechiness' : [],
        'tempo' : [],
        'valence' : [],
        'ai' : []
    }
    
    
    # populating song_stats arrays with song stats.
    for song in group :
        # Song == a specific song's clean data //phase 0
        song = _song_analysis_details(token, song['id'] , False ,  song['name'] , song['artists'][0] )
        for x in song_stats.keys():
            song_stats[x].append(song[x])


    # ****************
    # AT THIS POINT song_stats is a dictionary that holds arrays populated with all the user's liked music
    # ****************



    # averaging spotify (turning each key into it's average)
    spotty_keys = list(song_stats.keys())[:-1]
    for x in spotty_keys:
        song_stats[x] =  statistics.mean(song_stats[x])



    # averaging watson (watson averages are )
    # NOTE: every item in ['ai'] has sorted dictionary of the song's frequencies
    # BUG THIS BLOCK NEEDS TO RETURN song_stats['ai']'S ARR INTO ONE
    for x in song_stats['ai']:
        if x['nlu'] :
            mood = watson.mood(x['nlu'])





    # pprint.pprint(  song_stats  )
    return song_stats




# get song lyrics html using rapGenius   //phase 3
def _request_song_info(token , song_title, artist_name):
    base_url = 'https://api.genius.com'
    headers = {'Authorization': 'Bearer ' + token  }
    search_url = base_url + '/search'
    data = {'q': song_title + ' ' + artist_name}
    response = requests.get(search_url, data=data, headers=headers).json()
    
    # Search for matches in the request response
    remote_song_info = None
    for hit in response['response']['hits']:
        if artist_name.lower() in hit['result']['primary_artist']['name'].lower():
            remote_song_info = hit
            break

    # Extract lyrics from URL if the song was found
    if remote_song_info:
        song_url = remote_song_info['result']['url']
        return _webcrawl_lyrics(song_url)
    else:
        return None

#BS4 WEBCRAWLING for lyrics //phase 4
def _webcrawl_lyrics(url):
    # EXTRACT HTML
    page = requests.get(url)
    html = bs4.BeautifulSoup(page.text, 'html.parser')

    try:
        lyrics = html.find("div", {"id": "lyrics-root-pin-spacer"}).get_text()
        # lyrics = html.find("div", {"class": "lyrics"}).get_text()
    except Exception as e:
        print(  '\ndef _webcrawl_lyrics(url):\nERROR FINDING LYRICS: ' , str(e))
        return None


    
    # CREATE ARRAY THAT FINDS A LOWER CASE AND AN UPPERCASE RIGHT NEXT TO EACHOTHER AND SPLITS STRING
    lyrics_text = str(lyrics)
    all_bars = []
    br_point = 0
    previous = 0
    for x in range(0, len(lyrics_text)  - 1 , 1)  :
        if  lyrics_text[x].islower() and lyrics_text[x+1].isupper():
            br_point = x+1
            bar = lyrics_text[previous:br_point]
            all_bars.append(bar)
            previous = br_point
        

    # removing "[ SONG EVENT ]" from each bar
    event_start = None
    event_end = None
    for x in all_bars:
        found = False
        for y in range(len(x)):
            if x[y] == '['  : event_start = y  
            if x[y] == ']'  :
                found = True
                event_end = y
                no_event_bar = x[:event_start] + ' ' + x[event_end+1:]
        if found:
            x = no_event_bar


    return all_bars










# handmade api requests




# SPOTIFY
# token = authorize_spotify_NO_USER()
# token = authorize_spotify_IMPLICIT()
spotty_token = authorize_spotify_REFRESHABLE()


# GENIUS
genius_token =  Oauth_function( 'https://api.genius.com/oauth/authorize' , genius_clientId , callbackURL , genius_full_permission , genius_clientsECRET , 'token' )


# ENDPOINTS
# user_info = user_profile(spotty_token)

likes = user_likes(spotty_token)
# albums = user_albums(spotty_token)
# playlists = user_playlists(spotty_token)

# pprint.pprint(likes)
# pprint.pprint(albums)
# pprint.pprint(playlists)


# Music  Group analysis
likes_avg_atrributes(spotty_token , likes)
# group_avg_atrributes(spotty_token , albums ) 
# group_avg_atrributes(spotty_token , playlists ) 


# song analysis
# song = _song_analysis_details(spotty_token, '2kkWbvrQpSiH7TScbI9H0S' , False , 'Weatherman' , 'Xavier Wulf' )

