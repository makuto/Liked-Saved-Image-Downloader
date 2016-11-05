# -*- coding: utf-8 -*-

import scraper
import imageSaver

# Open this file to change the script settings. DO NOT change the settings below
DEFAULT_SETTINGS_FILENAME = 'settings.txt'

"""
Default settings. Note that these are overridden by the default settings file
"""
USERNAME = ''
PASSWORD = ''

# If True, don't actually download the images - just pretend to
SHOULD_SOFT_RETRIEVE = True

# If True, reddit scraper won't print URLs to console
SILENT_GET = False

# Total requests to reddit (actual results may vary)
TOTAL_REQUESTS = 500

# May result in shitty URLs (regex is tough)
URLS_FROM_COMMENTS = False

# Use the fancy new version, which organizes images by subreddit
USE_NEW_VERSION = False

# Don't get new stuff, just use the .xml files from last run
USE_CACHED_SUBMISSIONS = False
DEFAULT_CACHE_FILE = 'SubmissionCache.bin'

OUTPUT_DIR = u'output'

def readSettings(settingsFileName):
	global USERNAME
	global PASSWORD
	global SHOULD_SOFT_RETRIEVE
	global SILENT_GET
	global TOTAL_REQUESTS
	global URLS_FROM_COMMENTS
	global USE_NEW_VERSION
	global USE_CACHED_SUBMISSIONS
	global OUTPUT_DIR

	settingsFile = open(settingsFileName, 'r')
	lines = settingsFile.readlines()
	settingsFile.close()

	# This isn't robust at all, especially if people have any keywords in the username etc.
	for line in lines:
		if 'username='.lower() in line.lower():
			USERNAME = line[line.rfind('=') + 1:].strip(' \t\n')

		elif 'password='.lower() in line.lower():
			PASSWORD = line[line.rfind('=') + 1:].strip(' \t\n')

		elif 'SHOULD_SOFT_RETRIEVE='.lower() in line.lower():
			SHOULD_SOFT_RETRIEVE = True if 'True'.lower() in line.lower() else False

		elif 'SILENT_GET='.lower() in line.lower():
			SILENT_GET = True if 'True'.lower() in line.lower() else False

		elif 'TOTAL_REQUESTS='.lower() in line.lower():
			TOTAL_REQUESTS = int(line[line.rfind('=') + 1:].strip(' \t\n'))

		elif 'URLS_FROM_COMMENTS='.lower() in line.lower():
			URLS_FROM_COMMENTS = True if 'True'.lower() in line.lower() else False

		elif 'USE_NEW_VERSION='.lower() in line.lower():
			USE_NEW_VERSION = True if 'True'.lower() in line.lower() else False

		elif 'USE_CACHED_SUBMISSIONS='.lower() in line.lower():
			USE_CACHED_SUBMISSIONS = True if 'True'.lower() in line.lower() else False

		elif 'OUTPUT_DIR='.lower() in line.lower():
			OUTPUT_DIR = line[line.rfind('=') + 1:].strip(' \t\n')

def main():
	readSettings(DEFAULT_SETTINGS_FILENAME)

	if not USERNAME or not PASSWORD:
		print('Please provide a username and password in settings.txt')
		return

	print('Username: ' + USERNAME)

	if USE_NEW_VERSION:
		if USE_CACHED_SUBMISSIONS:
			submissions = scraper.readCacheRedditSubmissions(DEFAULT_CACHE_FILE)
		else:
			submissions = scraper.getRedditUserLikedSavedSubmissions(USERNAME, PASSWORD, 
				request_limit = TOTAL_REQUESTS, silentGet = SILENT_GET, extractURLsFromComments = URLS_FROM_COMMENTS)

			# Cache them in case it's needed later
			scraper.writeCacheRedditSubmissions(submissions, DEFAULT_CACHE_FILE)

		print 'Saving images. This will take several minutes...'
		unsupportedSubmissions = imageSaver.saveAllImages_Advanced(OUTPUT_DIR, submissions, 
			soft_retrieve_imgs = SHOULD_SOFT_RETRIEVE)

		# Unicode errors make this borked for now
		#scraper.saveSubmissionsAsXML(unsupportedSubmissions, OUTPUT_DIR + u'/' + 'UnsupportedSubmissions.xml') 

	else:
	    #Talk to reddit and fill .txt files with liked and saved URLS
	    scraper.getRedditUserLikedSavedImages(USERNAME, PASSWORD, 
	    	request_limit = TOTAL_REQUESTS, silentGet = SILENT_GET, extractURLsFromComments = URLS_FROM_COMMENTS)

	    #Parse those .txt files for image URLS and download them (if !SHOULD_SOFT_RETRIEVE)
	    imageSaver.saveAllImages(soft_retrieve_imgs = SHOULD_SOFT_RETRIEVE)

	if SHOULD_SOFT_RETRIEVE:
		print('\nYou have run the script in Soft Retrieve mode - if you actually\n'
			  'want to download images now, you should change SHOULD_SOFT_RETRIEVE\n'
			  'to False in settings.txt')

if __name__ == '__main__':
	main()
