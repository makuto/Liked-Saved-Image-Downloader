# -*- coding: utf-8 -*-

import time
import os

import LikedSavedDatabase
import logger
import imageSaver
import redditScraper
import tumblrScraper
import pixivScraper
import imgurDownloader
import settings
import submission
import utilities
import LikedSavedDatabase

scriptFinishedSentinel = '>>> runLikedSavedDownloader() Process Finished <<<'

def initialize():
    settings.getSettings()
        
    if not settings.settings['Database']:
        logger.log('Please provide a location for the Database')
        return

    # Do this early so we can use it anywhere
    LikedSavedDatabase.initializeFromSettings(settings.settings)


def runLikedSavedDownloader(pipeConnection):
    if pipeConnection:
        logger.setPipe(pipeConnection)
        
    initialize()

    if (not settings.settings['Use_cached_submissions'] 
        and not settings.hasTumblrSettings() and not settings.hasRedditSettings()):
        logger.log('Please provide Tumblr or Reddit account details in settings.txt'
                   ' or via the Settings page provided by  LikedSavedDownloader server')
        return
            
    if not settings.settings['Gfycat_Client_id']:
        logger.log('No Gfycat Client ID and/or Gfycat Client Secret was provided. '
                   'This is required to download Gfycat media reliably.')

    logger.log('Output: ' + settings.settings['Output_dir'])
    utilities.makeDirIfNonexistant(settings.settings['Output_dir'])
    utilities.makeDirIfNonexistant(settings.settings['Metadata_output_dir'])
        
    submissions = getSubmissionsToSave()

    logger.log('Saving images. This will take several minutes...')
    unsupportedSubmissions = imageSaver.saveAllImages(settings.settings['Output_dir'], submissions, 
                                                      imgur_auth = imgurDownloader.getImgurAuth(),
                                                      only_download_albums = settings.settings['Only_download_albums'],
                                                      skip_n_percent_submissions = settings.settings['Skip_n_percent_submissions'],
                                                      soft_retrieve_imgs = settings.settings['Should_soft_retrieve'],
                                                      only_important_messages = settings.settings['Only_important_messages'])

    # Write out a .json file listing all of the submissions the script failed to download
    if unsupportedSubmissions:
        submission.saveSubmissionsAsJson(unsupportedSubmissions, settings.settings['Metadata_output_dir'] + u'/' 
                                         + 'UnsupportedSubmissions_' + time.strftime("%Y%m%d-%H%M%S") + '.json') 

    if settings.settings['Should_soft_retrieve']:
        logger.log('\nYou have run the script in Soft Retrieve mode - if you actually\n'
                   'want to download images now, you should change SHOULD_SOFT_RETRIEVE\n'
                   'to False in settings.txt')

    if pipeConnection:
        logger.log(scriptFinishedSentinel)
        pipeConnection.close()

def getSubmissionsToSave():
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

    pixivRequestOnlyNewCache = None
    pixivRequestOnlyNewPrivateCache = None
    if settings.settings['Pixiv_Try_Request_Only_New']:
        pixivRequestOnlyNewCache = submission.readCacheSubmissions(
            settings.settings['Pixiv_Try_Request_Only_New_Cache_File'])
        pixivRequestOnlyNewPrivateCache = submission.readCacheSubmissions(
            settings.settings['Pixiv_Try_Request_Only_New_Private_Cache_File'])

    submissions = []

    if settings.settings['Use_cached_submissions']:
        logger.log('Using cached submissions')
        submissions += submission.readCacheSubmissions(settings.settings['Reddit_cache_file'])
        submissions += submission.readCacheSubmissions(settings.settings['Tumblr_cache_file'])
        submissions += submission.readCacheSubmissions(settings.settings['Pixiv_cache_file'])
    else:
        if settings.hasRedditSettings():
            redditSubmissions, redditComments, earlyOutPoints = redditScraper.getRedditUserLikedSavedSubmissions(
                settings.settings['Username'], settings.settings['Password'], 
                settings.settings['Client_id'], settings.settings['Client_secret'],
                request_limit = settings.settings['Reddit_Total_requests'], 
                saveLiked = settings.settings['Reddit_Save_Liked'], 
                saveSaved = settings.settings['Reddit_Save_Saved'],
                earlyOutPointSaved = redditRequestOnlyNewSavedCache, 
                earlyOutPointLiked = redditRequestOnlyNewLikedCache,
                unlikeLiked = settings.settings['Reddit_Unlike_Liked'],
                unsaveSaved = settings.settings['Reddit_Unsave_Saved'])
            
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
                submission.saveSubmissionsAsJson(redditComments, settings.settings['Metadata_output_dir'] + u'/' 
                                                 + 'Reddit_SavedComment_Submissions_' + time.strftime("%Y%m%d-%H%M%S") + '.json')
                # Output to HTML so the user can look at them easily
                submission.saveSubmissionsAsHtml(redditComments, settings.settings['Output_dir'] + u'/' 
                                                 + 'Reddit_SavedComment_Submissions_' + time.strftime("%Y%m%d-%H%M%S") + '.html')
                logger.log('Saved ' + str(len(redditComments)) + ' reddit comments')

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

        if settings.hasPixivSettings():
            pixivSubmissions, nextEarlyOutPair = pixivScraper.getPixivUserBookmarkedSubmissions(settings.settings['Pixiv_username'],
                                                                                                settings.settings['Pixiv_password'],
                                                                                                requestOnlyNewCache = pixivRequestOnlyNewCache,
                                                                                                requestOnlyNewPrivateCache = pixivRequestOnlyNewPrivateCache)
            # Cache them in case it's needed later
            submission.writeCacheSubmissions(pixivSubmissions, settings.settings['Pixiv_cache_file'])

            # Set new early out point
            if nextEarlyOutPair[0]:
                submission.writeCacheSubmissions([nextEarlyOutPair[0]],
                                                 settings.settings['Pixiv_Try_Request_Only_New_Cache_File'])
            if nextEarlyOutPair[1]:
                submission.writeCacheSubmissions([nextEarlyOutPair[1]],
                                                 settings.settings['Pixiv_Try_Request_Only_New_Private_Cache_File'])
            submissions += pixivSubmissions

        # Write out a .json file with all of the submissions in case the user wants the data
        submission.saveSubmissionsAsJson(submissions, settings.settings['Metadata_output_dir'] + u'/' 
                                         + 'AllSubmissions_' + time.strftime("%Y%m%d-%H%M%S") + '.json')

        LikedSavedDatabase.db.addSubmissions(submissions)

    return submissions

def saveRequestedSubmissions(pipeConnection, submissionIds):
    if pipeConnection:
        logger.setPipe(pipeConnection)

    initialize()

    logger.log('Attempting to save {} requested submissions. This will take several minutes...'
               .format(len(submissionIds)))

    dbSubmissions = LikedSavedDatabase.db.getSubmissionsByIds(submissionIds)

    submissions = []
    # Convert from database submissions to Submission
    for dbSubmission in dbSubmissions:
        convertedSubmission = submission.Submission()
        convertedSubmission.initFromDict(dbSubmission)
        submissions.append(convertedSubmission)

    if len(submissions) != len(submissionIds):
        logger.log('Could not find {} submissions in database!'.format(len(submissionIds) - len(submissions)))

    unsupportedSubmissions = imageSaver.saveAllImages(settings.settings['Output_dir'], submissions, 
                                                      imgur_auth = imgurDownloader.getImgurAuth(),
                                                      only_download_albums = settings.settings['Only_download_albums'],
                                                      skip_n_percent_submissions = settings.settings['Skip_n_percent_submissions'],
                                                      soft_retrieve_imgs = settings.settings['Should_soft_retrieve'],
                                                      only_important_messages = settings.settings['Only_important_messages'])

    logger.log('Download finished. Please refresh the page to see updated entries')
    
    if pipeConnection:
        logger.log(scriptFinishedSentinel)
        pipeConnection.close()

def saveRequestedUrls(pipeConnection, urls):
    if pipeConnection:
        logger.setPipe(pipeConnection)

    initialize()

    logger.log('Attempting to save {} requested urls. This may take several minutes...'
               .format(len(urls)))

    submissions = []
    # Create Submission for each URL
    for url in urls:
        convertedSubmission = submission.Submission()
        convertedSubmission.source = "UserRequested"
        convertedSubmission.title = "UserRequested"
        convertedSubmission.author = "(Requested by user)"
        convertedSubmission.subreddit = "Requested_Downloads"
        convertedSubmission.subredditTitle = "Requested Downloads"
        convertedSubmission.body = "(Requested by user)"
        convertedSubmission.bodyUrl= url
        convertedSubmission.postUrl= url
        submissions.append(convertedSubmission)

    if len(submissions) != len(urls):
        logger.log('Could not parse {} URLs!'.format(len(urls) - len(submissions)))

    unsupportedSubmissions = imageSaver.saveAllImages(settings.settings['Output_dir'], submissions, 
                                                      imgur_auth = imgurDownloader.getImgurAuth(),
                                                      only_download_albums = settings.settings['Only_download_albums'],
                                                      skip_n_percent_submissions = settings.settings['Skip_n_percent_submissions'],
                                                      soft_retrieve_imgs = settings.settings['Should_soft_retrieve'],
                                                      only_important_messages = settings.settings['Only_important_messages'])

    logger.log('Download finished. Output to \'Requested Downloads\' directory')
    
    if pipeConnection:
        logger.log(scriptFinishedSentinel)
        pipeConnection.close()

if __name__ == '__main__':
    runLikedSavedDownloader(None)
