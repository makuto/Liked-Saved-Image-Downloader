# -*- coding: utf-8 -*-

import time
import os

import scraper
import tumblrScraper
import submission
import imageSaver
import settings

def main():
	settings.getSettings()

	if (not settings.settings['Use_cached_submissions'] 
	    and not settings.hasTumblrSettings() and not settings.hasRedditSettings()):
		print('Please provide Tumblr or Reddit account details settings.txt')
		return

	imgurAuth = None
	if (settings.settings['Should_download_albums'] 
		and settings.hasImgurSettings()):
		imgurAuth = imageSaver.ImgurAuth(settings.settings['Imgur_client_id'], 
						 settings.settings['Imgur_client_secret'])
	else:
		print('No Imgur Client ID and/or Imgur Client Secret was provided, or album download is not'
			' enabled. This is required to download imgur albums. They will be ignored. Check'
			' settings.txt for how to fill in these values.')

	print('Output: ' + settings.settings['Output_dir'])

	# TODO: Only save one post for early out. Only save once all downloading is done
	redditRequestOnlyNewSavedCache = None
	redditRequestOnlyNewLikedCache = None
	if settings.settings['Reddit_Try_Request_Only_New']:
		redditRequestOnlyNewSavedCache = submission.readCacheSubmissions(
                        settings.settings['Reddit_Try_Request_Only_New_Saved_Cache_File'])
		redditRequestOnlyNewLikedCache = submission.readCacheSubmissions(
                        settings.settings['Reddit_Try_Request_Only_New_Liked_Cache_File'])

	tumblrRequestOnlyNewCache = None
	if settings.settings['Tumblr_Try_Request_Only_New']:
		tumblrRequestOnlyNewCache = submission.readCacheSubmissions(
                        settings.settings['Tumblr_Try_Request_Only_New_Cache_File'])

	submissions = []

	if settings.settings['Use_cached_submissions']:
		print('Using cached submissions')
		submissions += submission.readCacheSubmissions(settings.settings['Reddit_cache_file'])
		submissions += submission.readCacheSubmissions(settings.settings['Tumblr_cache_file'])
	else:
		if settings.hasRedditSettings():
			redditSubmissions, redditComments, earlyOutPoints = scraper.getRedditUserLikedSavedSubmissions(
				settings.settings['Username'], settings.settings['Password'], 
				settings.settings['Client_id'], settings.settings['Client_secret'],
				request_limit = settings.settings['Reddit_Total_requests'], 
				saveLiked = settings.settings['Reddit_Save_Liked'], 
				saveSaved = settings.settings['Reddit_Save_Saved'],
				earlyOutPointSaved = redditRequestOnlyNewSavedCache, 
				earlyOutPointLiked = redditRequestOnlyNewLikedCache)
			
			# Cache them in case it's needed later
			submission.writeCacheSubmissions(redditSubmissions, settings.settings['Reddit_cache_file'])

			# Set new early out points
			submission.writeCacheSubmissions([earlyOutPoints[0]],
				settings.settings['Reddit_Try_Request_Only_New_Saved_Cache_File'])
			submission.writeCacheSubmissions([earlyOutPoints[1]],
				settings.settings['Reddit_Try_Request_Only_New_Liked_Cache_File'])

			submissions += redditSubmissions

			# For reddit only: write out comments to separate json file
			if settings.settings['Reddit_Save_Comments']:
				submission.saveSubmissionsAsJson(redditComments, settings.settings['Output_dir'] + u'/' 
					+ 'Reddit_SavedComment_Submissions_' + time.strftime("%Y%m%d-%H%M%S") + '.json')
				submission.saveSubmissionsAsHtml(redditComments, settings.settings['Output_dir'] + u'/' 
					+ 'Reddit_SavedComment_Submissions_' + time.strftime("%Y%m%d-%H%M%S") + '.html')
				print('Saved ' + str(len(redditComments)) + ' reddit comments')

		if settings.hasTumblrSettings():
			tumblrSubmissions, earlyOutPoint = tumblrScraper.getTumblrUserLikedSubmissions(
				settings.settings['Tumblr_Client_id'], settings.settings['Tumblr_Client_secret'], 
				settings.settings['Tumblr_Client_token'], settings.settings['Tumblr_Client_token_secret'],
				likeRequestLimit = settings.settings['Tumblr_Total_requests'],
				requestOnlyNewCache = tumblrRequestOnlyNewCache)
			
			# Cache them in case it's needed later
			submission.writeCacheSubmissions(tumblrSubmissions, settings.settings['Tumblr_cache_file'])

			# Set new early out point
			submission.writeCacheSubmissions([earlyOutPoint], 
				settings.settings['Tumblr_Try_Request_Only_New_Cache_File'])

			submissions += tumblrSubmissions

		# Write out a .json file with all of the submissions in case the user wants the data
		submission.saveSubmissionsAsJson(submissions, settings.settings['Output_dir'] + u'/' 
			+ 'AllSubmissions_' + time.strftime("%Y%m%d-%H%M%S") + '.json') 

	print('Saving images. This will take several minutes...')
	unsupportedSubmissions = imageSaver.saveAllImages(settings.settings['Output_dir'], submissions, 
		imgur_auth = imgurAuth, only_download_albums = settings.settings['Only_download_albums'],
		skip_n_percent_submissions = settings.settings['Skip_n_percent_submissions'],
		soft_retrieve_imgs = settings.settings['Should_soft_retrieve'],
		only_important_messages = settings.settings['Only_important_messages'])

	# Write out a .json file listing all of the submissions the script failed to download
	submission.saveSubmissionsAsJson(unsupportedSubmissions, settings.settings['Output_dir'] + u'/' 
		+ 'UnsupportedSubmissions_' + time.strftime("%Y%m%d-%H%M%S") + '.json') 

	if settings.settings['Should_soft_retrieve']:
		print('\nYou have run the script in Soft Retrieve mode - if you actually\n'
			  'want to download images now, you should change SHOULD_SOFT_RETRIEVE\n'
			  'to False in settings.txt')

if __name__ == '__main__':
	main()
