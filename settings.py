# -*- coding: utf-8 -*-

import os
import time
import operator

# Open this file to change the script settings. DO NOT change the settings below
DEFAULT_SETTINGS_FILENAME = 'settings.txt'

"""
Default settings. Note that these are overridden by the default settings file
"""
settings = {
    # Reddit authentication information
    'Username' : '',
    'Password' : '',
    'Client_id' : '',
    'Client_secret' : '',

    # Imgur authentication information
    'Imgur_client_id' : '',
    'Imgur_client_secret' : '',

    # Tumblr authentication information
    'Tumblr_Client_id' : '',
    'Tumblr_Client_secret' : '',
    'Tumblr_Client_token' : '',
    'Tumblr_Client_token_secret' : '',
    
    # Gfycat authentication information
    # https://developers.gfycat.com/signup/#/apiform
    # Requires https://github.com/ankeshanand/py-gfycat
    'Gfycat_Client_id' : '',
    'Gfycat_Client_secret' : '',

    # Disable downloading albums by default.
    'Should_download_albums' : False,

    # If true, do not download single images, only submissions which are imgur albums
    'Only_download_albums' : False,

    # If True, don't actually download the images - just pretend to
    'Should_soft_retrieve' : True,

    'Reddit_Save_Liked' : True,
    'Reddit_Save_Saved' : True,
    'Reddit_Save_Comments' : True,
    'Reddit_Unlike_Liked': False,
    'Reddit_Unsave_Saved': False,

    'Only_important_messages' : False,

    # Total requests to reddit (actual results may vary)
    'Reddit_Total_requests' : 500,

    # Total requests to Tumblr
    'Tumblr_Total_requests' : 500,

    # Don't get new stuff, just use the .xml files from last run
    'Use_cached_submissions' : False,
    'Reddit_cache_file' : 'Reddit_SubmissionCache.bin',
    'Tumblr_cache_file' : 'Tumblr_SubmissionCache.bin',

    # Attempt to only request and download new submissions (those which haven't been downloaded)
    # This uses the Reddit and Tumblr cache files to know what's already been downloaded,
    #  so it will only work if you've successfully run the script before
    'Reddit_Try_Request_Only_New' : True,
    'Tumblr_Try_Request_Only_New' : True,
    'Reddit_Try_Request_Only_New_Saved_Cache_File' : 'Reddit_RequestOnlyNewSaved.bin',
    'Reddit_Try_Request_Only_New_Liked_Cache_File' : 'Reddit_RequestOnlyNewLiked.bin',
    'Tumblr_Try_Request_Only_New_Cache_File' : 'Tumblr_RequestOnlyNew.bin',

    # If the script failed at say 70%, you could use toggle Use_cached_submissions and set this value to
    #  69. The script would then restart 69% of the way into the cached submissions nearer to where you
    #  left off. 
    # The reason why this isn't default is because there might have been changes to the script which 
    #  made previous submissions successfully download, so we always re-check submissions 
    'Skip_n_percent_submissions': 0,

    'Output_dir' : 'output',
    'Database' : 'LikedSaved.db'
}

redditClientSecretInstructions = '''You need OAuth tokens to run the script. To get them follow these steps:</p>
    <ol>
        <li>Go to <a href="https://www.reddit.com/prefs/apps/">Reddit app preferences</a> (while signed in to reddit)</li>
        <li>Scroll down to the bottom and click "create app" (something like that)</li>
        <li>Fill in the fields as such:</li>
            <ul>
                <li><b>name:</b> Reddit Liked-Saved Image Downloader</li>
                <li>Choose <b>"script"</b> as the type</li>
                <li><b>about url:</b> https://github.com/makuto/redditLikedSavedImageDownloader</li>
                <li><b>redirect uri:</b> http://localhost:8080</li>
            </ul>
        <li>Click create app</li>
        <li>Copy the text which is right below "personal use script" for Client ID</li>
        <li>Copy the secret for Client Secret as well</li>
    </ol>
    <p class="optionComment">Yes, this is painful, but it's for your own security</p>
'''

tumblrClientSecretInstructions = '''
Follow the same procedure as reddit for Tumblr:</p>
    <ol>
        <li><a href="https://www.tumblr.com/oauth/apps">Register the app</a></li>
        <li>Then go <a href="https://api.tumblr.com/console">here</a> to get your tokens</li>
    </ol>
<p class="optionComment">Refer to the <a href="https://github.com/tumblr/pytumblr">PyTumblr page</a> for more details).
'''

requestsInstructions = 'Increase this value to get more submissions'

# This is provides metadata to create nice sections for the web interface
# [('header', ['option_to_include', ('another_option', 'this one has a comment')])]
settingsStructure = [
    ('Output',
     [('Output_dir', 'All images, videos, and comments will be saved to this directory. You will have to restart the server whenever you change this value when using the Random Image Browser')]),
    
    ('Reddit Auth',
     ['Username',
      'Password',
      'Client_id',
      ('Client_secret', redditClientSecretInstructions)]),
    
    ('Reddit Settings',
     [('Reddit_Total_requests', requestsInstructions),
      'Reddit_Save_Liked',
      'Reddit_Save_Saved',
      'Reddit_Save_Comments',
      ('Reddit_Unlike_Liked', 'Unlike/remove upvote after the submission has been recorded'),
      ('Reddit_Unsave_Saved', 'Unsave submission after it has been recorded'),
      ('Reddit_Try_Request_Only_New',
       "Attempt to only request and download new submissions (those which haven't been downloaded) "
       "This uses the Reddit cache files to know what's already been downloaded, so it will only"
       "work if you've successfully run the script before"),
      'Reddit_Try_Request_Only_New_Saved_Cache_File',
      'Reddit_Try_Request_Only_New_Liked_Cache_File']),
    
    ('Imgur Auth',
     ['Imgur_client_id',
      ('Imgur_client_secret',"These need to be filled in so that the script can download Imgur "
       "albums. If not filled in, imgur albums will be ignored. Single images will still be "
       "downloaded. I've filled in a public imgur user's information. This isn't safe giving you"
       " hooligans the secret, but fuck it. If you want to use your own Imgur Client, sign in to"
       " Imgur, then go <a href=\"https://api.imgur.com/oauth2/addclient\">here</a> and create"
       " your new client.")]),

    ('Gfycat Auth',
     ['Gfycat_Client_id',
      ('Gfycat_Client_secret', "These need to be filled in so that the script can download Gfycat"
       " media. If not filled in, many Gfycat links will fail to download."
       " Go <a href=\"https://developers.gfycat.com/signup/#/apiform\">here</a> to get your API keys.")]),
    
    ('Tumblr Auth',
     ['Tumblr_Client_id',
      'Tumblr_Client_secret',
      'Tumblr_Client_token',
      ('Tumblr_Client_token_secret', tumblrClientSecretInstructions)]),

    ('Tumblr Settings',
     [('Tumblr_Total_requests', requestsInstructions),
      ('Tumblr_Try_Request_Only_New',
       "Attempt to only request and download new submissions (those which haven't been downloaded) "
       "This uses the Reddit cache files to know what's already been downloaded, so it will only "
       "work if you've successfully run the script before"),
      'Tumblr_Try_Request_Only_New_Cache_File']),
    
    ('Download Settings',
     [
         'Should_download_albums',
         
         ('Only_download_albums',
          'If true, do not download single images, only submissions which are imgur albums')
     ]),

    ('Debugging and Development',
    [
        ('Only_important_messages', 'Output minimal information to the console'),
        ('Use_cached_submissions', 'Do not get new stuff, just use the cache files from last run'),
        'Reddit_cache_file',
        'Tumblr_cache_file',
        ('Skip_n_percent_submissions', "If the script failed at say 70%, you could use toggle Use_cached_submissions and set this value to 69. The script would then restart 69% of the way into the cached submissions nearer to where you left off. The reason why this isn't default is because there might have been changes to the script which made previous submissions successfully download, so we always re-check submissions"),
        
        ('Should_soft_retrieve', "If True, don't actually download the images - just pretend to"),
        
        ('Database')
    ]),
]

def valueAfterTag(line, optionTag):
    return line[len(optionTag) + 1:].strip(' \t\n')

def lineHasOption(line, optionTag):
    return (optionTag.lower() in line.lower() 
            and line[:len(optionTag) + 1].lower() == optionTag.lower() + '=')

def getBooleanOption(line, optionTag):
    if lineHasOption(line, optionTag):
        value = valueAfterTag(line, optionTag).lower()
        return True if (value == 'true' or value == '1') else False
    return False

def getStringOption(line, optionTag):
    if lineHasOption(line, optionTag):
        return valueAfterTag(line, optionTag)
    return ''

def getIntegerOption(line, optionTag):
    if lineHasOption(line, optionTag):
        return int(valueAfterTag(line, optionTag))
    return -1

def readSettings(settingsFileName):
    global settings

    settingsFile = open(settingsFileName, 'r')
    lines = settingsFile.readlines()
    settingsFile.close()

    for line in lines:
        # Ignore blank or commented lines
        if not len(line.strip(' \t\n')) or line[0] == '#':
            continue

        for option in settings:
            if lineHasOption(line, option):
                if type(settings[option]) == bool:
                    settings[option] = getBooleanOption(line, option)
                    break
                
                elif type(settings[option]) == int:
                    settings[option] = getIntegerOption(line, option)
                    break
                
                elif type(settings[option]) == str:
                    settings[option] = getStringOption(line, option)
                    break

def hasRedditSettings():
    return (settings['Username'] and settings['Password'] and 
            settings['Client_id'] and settings['Client_secret'])

def hasTumblrSettings():
    return (settings['Tumblr_Client_id'] and settings['Tumblr_Client_secret'] and 
            settings['Tumblr_Client_token'] and settings['Tumblr_Client_token_secret'])

def hasImgurSettings():
    return (settings['Imgur_client_id'] and settings['Imgur_client_secret'])

# To make sure I don't accidentally commit my settings.txt, it's marked LOCAL_, 
# which is in .gitignore
hiddenSettingsFilename = "LOCAL_settings.txt"

# Not intended to be edited by a human, definitely shouldn't be checked in
serverSettingsFilename = 'LOCAL_settings_from_server.txt'

# Returns which settings file should be used
def getSettingsFilename():
    candidates = []
    if os.path.isfile(hiddenSettingsFilename):
        candidates.append(hiddenSettingsFilename)
        
    if os.path.isfile(serverSettingsFilename):
        candidates.append(serverSettingsFilename)
        
    if os.path.isfile(DEFAULT_SETTINGS_FILENAME):
        candidates.append(DEFAULT_SETTINGS_FILENAME)

    # Choose the most recently edited file
    # From http://code.activestate.com/recipes/576804-find-the-oldest-or-yougest-of-a-list-of-files/
    timeNow = time.time()
    newestFile = candidates[0], timeNow - os.path.getctime(candidates[0])
    
    for fileName in candidates:
        age = timeNow - os.path.getctime(fileName)
        if operator.lt(age, newestFile[1]):
            newestFile = fileName, age

    return newestFile[0]

def writeServerSettings():
    settingsOutput = []
    for option in settings:
        optionValue = settings[option]

        if type(settings[option]) == bool:
            optionValue = 'True' if optionValue else 'False'
            
        settingsOutput.append('{}={}\n'.format(option, optionValue))
        
    serverSettings = open(serverSettingsFilename, 'w')
    serverSettings.writelines(settingsOutput)
    serverSettings.close()

    print('Wrote settings to ' + serverSettingsFilename)

def getSettings():
    settingsFilename = getSettingsFilename()
    print('Reading settings from settings file with most recent timestamp, which was:\n'
          + settingsFilename
          + "\nIf you want to read from a different settings file, make it more recent")
    readSettings(settingsFilename)
