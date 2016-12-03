# -*- coding: utf-8 -*-

import scraper
import imageSaver

# Open this file to change the script settings. DO NOT change the settings below
DEFAULT_SETTINGS_FILENAME = 'settings.txt'

"""
Default settings. Note that these are overridden by the default settings file
"""
settings = {
'Username' : '',
'Password' : '',
'Client_id' : '',
'Client_secret': '',

# If True, don't actually download the images - just pretend to
'Should_soft_retrieve' : True,

# If True, reddit scraper won't print URLs to console
'Silent_get' : False,

# Total requests to reddit (actual results may vary)
'Total_requests' : 500,

# May result in shitty URLs (regex is tough)
'Urls_from_comments' : False,

# Use the fancy new version, which organizes images by subreddit
'Use_new_version' : False,

# Don't get new stuff, just use the .xml files from last run
'Use_cached_submissions' : False,
'Default_cache_file' : 'SubmissionCache.bin',

'Output_dir' : u'output'
}

def valueAfterTag(line, optionTag):
	return line[len(optionTag) + 1:].strip(' \t\n')

def lineHasOption(line, optionTag):
	return (optionTag.lower() in line.lower() 
		and line[:len(optionTag) + 1].lower() == optionTag.lower() + '=')

def getBooleanOption(line, optionTag):
	if lineHasOption(line, optionTag):
		return True if valueAfterTag(line, optionTag).lower() == 'true' else False
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

def main():
	readSettings(DEFAULT_SETTINGS_FILENAME)

	if not settings['Username'] or not settings['Password']:
		print('Please provide a Username and password in settings.txt')
		return

	print('Username: ' + settings['Username'])

	if settings['Use_new_version']:
		if settings['Use_cached_submissions']:
			submissions = scraper.readCacheRedditSubmissions(settings['Default_cache_file'])
		else:
			submissions = scraper.getRedditUserLikedSavedSubmissions(settings['Username'], settings['Password'], 
				settings['Client_id'], settings['Client_secret'],
				request_limit = settings['Total_requests'], silentGet = settings['Silent_get'], 
				extractURLsFromComments = settings['Urls_from_comments'])

			# Cache them in case it's needed later
			scraper.writeCacheRedditSubmissions(submissions, settings['Default_cache_file'])

		print 'Saving images. This will take several minutes...'
		unsupportedSubmissions = imageSaver.saveAllImages_Advanced(settings['Output_dir'], submissions, 
			soft_retrieve_imgs = settings['Should_soft_retrieve'])

		# Unicode errors make this borked for now
		#scraper.saveSubmissionsAsXML(unsupportedSubmissions, OUTPUT_DIR + u'/' + 'UnsupportedSubmissions.xml') 

	else:
	    #Talk to reddit and fill .txt files with liked and saved URLS
	    scraper.getRedditUserLikedSavedImages(settings['Username'], settings['Password'], 
	    	settings['Client_id'], settings['Client_secret'],
	    	request_limit = settings['Total_requests'], silentGet = settings['Silent_get'], 
	    	extractURLsFromComments = settings['Urls_from_comments'])

	    #Parse those .txt files for image URLS and download them (if !SHOULD_SOFT_RETRIEVE)
	    imageSaver.saveAllImages(soft_retrieve_imgs = settings['Should_soft_retrieve'])

	if settings['Should_soft_retrieve']:
		print('\nYou have run the script in Soft Retrieve mode - if you actually\n'
			  'want to download images now, you should change SHOULD_SOFT_RETRIEVE\n'
			  'to False in settings.txt')

if __name__ == '__main__':
	main()
