# -*- coding: utf-8 -*-

import time
import os

import scraper
import tumblrScraper
import submission
import imageSaver

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

# Disable downloading albums by default.
'Should_download_albums' : False,

# If true, do not download single images, only submissions which are imgur albums
'Only_download_albums' : False,

# If True, don't actually download the images - just pretend to
'Should_soft_retrieve' : True,

'Reddit_Save_Liked' : True,
'Reddit_Save_Saved' : True,
'Reddit_Save_Comments' : True,

'Only_important_messages' : False,

# Total requests to reddit (actual results may vary)
'Reddit_Total_requests' : 500,

# Total requests to Tumblr
'Tumblr_Total_requests' : 500,

# Don't get new stuff, just use the .xml files from last run
'Use_cached_submissions' : False,
'Reddit_cache_file' : 'Reddit_SubmissionCache.bin',
'Tumblr_cache_file' : 'Tumblr_SubmissionCache.bin',

# If the script failed at say 70%, you could use toggle Use_cached_submissions and set this value to
#  69. The script would then restart 69% of the way into the cached submissions nearer to where you
#  left off. 
# The reason why this isn't default is because there might have been changes to the script which 
#  made previous submissions successfully download, so we always re-check submissions 
'Skip_n_percent_submissions': 0,

'Output_dir' : 'output'
}

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

def main():
	# To make sure I don't accidentally commit my settings.txt, it's marked LOCAL_, 
	# which is in .gitignore
	hiddenSettingsFilename = "LOCAL_settings.txt"
	if os.path.isfile(hiddenSettingsFilename):
		print('Reading settings from ' + hiddenSettingsFilename)
		readSettings(hiddenSettingsFilename)
	else:
		print('Reading settings from ' + DEFAULT_SETTINGS_FILENAME)
		readSettings(DEFAULT_SETTINGS_FILENAME)

	if (not settings['Use_cached_submissions'] 
	    and not hasTumblrSettings() and not hasRedditSettings()):
		print('Please provide Tumblr or Reddit account details settings.txt')
		return

	imgurAuth = None
	if (settings['Should_download_albums'] 
		and hasImgurSettings()):
		imgurAuth = imageSaver.ImgurAuth(settings['Imgur_client_id'], 
										 settings['Imgur_client_secret'])
	else:
		print('No Imgur Client ID and/or Imgur Client Secret was provided, or album download is not'
			' enabled. This is required to download imgur albums. They will be ignored. Check'
			' settings.txt for how to fill in these values.')

	print('Output: ' + settings['Output_dir'])

	submissions = []

	if settings['Use_cached_submissions']:
		print('Using cached submissions')
		submissions += submission.readCacheSubmissions(settings['Reddit_cache_file'])
		submissions += submission.readCacheSubmissions(settings['Tumblr_cache_file'])
	else:
		if hasRedditSettings():
			redditSubmissions, redditComments = scraper.getRedditUserLikedSavedSubmissions(
				settings['Username'], settings['Password'], 
				settings['Client_id'], settings['Client_secret'],
				request_limit = settings['Reddit_Total_requests'], 
				saveLiked = settings['Reddit_Save_Liked'], 
				saveSaved = settings['Reddit_Save_Saved'])
			
			# Cache them in case it's needed later
			submission.writeCacheSubmissions(redditSubmissions, settings['Reddit_cache_file'])

			submissions += redditSubmissions

			# For reddit only: write out comments to separate json file
			if settings['Reddit_Save_Comments']:
				submission.saveSubmissionsAsJson(redditComments, settings['Output_dir'] + u'/' 
					+ 'Reddit_SavedComment_Submissions_' + time.strftime("%Y%m%d-%H%M%S") + '.json')
				print('Saved ' + str(len(redditComments)) + ' reddit comments')

		if hasTumblrSettings():
			tumblrSubmissions = tumblrScraper.getTumblrUserLikedSubmissions(
				settings['Tumblr_Client_id'], settings['Tumblr_Client_secret'], 
				settings['Tumblr_Client_token'], settings['Tumblr_Client_token_secret'],
				likeRequestLimit = settings['Tumblr_Total_requests'])
			
			# Cache them in case it's needed later
			submission.writeCacheSubmissions(tumblrSubmissions, settings['Tumblr_cache_file'])

			submissions += tumblrSubmissions

		# Write out a .json file with all of the submissions in case the user wants the data
		submission.saveSubmissionsAsJson(submissions, settings['Output_dir'] + u'/' 
			+ 'AllSubmissions_' + time.strftime("%Y%m%d-%H%M%S") + '.json') 

	print('Saving images. This will take several minutes...')
	unsupportedSubmissions = imageSaver.saveAllImages(settings['Output_dir'], submissions, 
		imgur_auth = imgurAuth, only_download_albums = settings['Only_download_albums'],
		skip_n_percent_submissions = settings['Skip_n_percent_submissions'],
		soft_retrieve_imgs = settings['Should_soft_retrieve'],
		only_important_messages = settings['Only_important_messages'])

	# Write out a .json file listing all of the submissions the script failed to download
	submission.saveSubmissionsAsJson(unsupportedSubmissions, settings['Output_dir'] + u'/' 
		+ 'UnsupportedSubmissions_' + time.strftime("%Y%m%d-%H%M%S") + '.json') 

	if settings['Should_soft_retrieve']:
		print('\nYou have run the script in Soft Retrieve mode - if you actually\n'
			  'want to download images now, you should change SHOULD_SOFT_RETRIEVE\n'
			  'to False in settings.txt')

if __name__ == '__main__':
	main()
