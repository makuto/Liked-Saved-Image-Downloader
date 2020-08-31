# -*- coding: utf-8 -*-
import os
import re
import sys

import urllib
if sys.version_info[0] >= 3:
	from urllib.request import urlretrieve, urlopen
        #from urllib.request import urlopen
else:
	from urllib import urlretrieve, urlopen

# local imports
from utils.crcUtils import signedCrc32
import LikedSavedDatabase
import imageSaver
import imgurpython as imgur
from utils import logger
import settings
from utils import utilities

def isImgurIndirectUrl(url):
    # If it is imgur domain, has no file type, and isn't an imgur album
    return ('imgur' in url.lower() 
        and not imageSaver.getFileTypeFromUrl(url) 
        and not '/a/' in url)

def imgurIdFromUrl(url):
    idMatch = re.search(r"imgur.com.*/(.*)", url)
    if not idMatch:
        return None
    return idMatch.group(1)

def convertImgurIndirectUrlToImg(submission, imgurAuth, url):
    # Login to imgur
    # This is required since they made NSFW images require login
    imgurClient = imgur.ImgurClient(imgurAuth.clientId, imgurAuth.clientSecret)

    if not checkImgurAPICredits(imgurClient):
        return None

    imageId = imgurIdFromUrl(url)
    if not imageId:
        logger.log("Failed to convert {} to image id".format(url))
        
    try:
        return imgurClient.get_image(imageId).link
    except Exception as e:
        errorMessage = ('Failed to convert imgur to image link: '
                        '[ERROR] Exception: Url {} raised exception:\n\t {}'.format(url, e))
        logger.log(errorMessage)
        LikedSavedDatabase.db.addUnsupportedSubmission(submission, errorMessage)
        return None

def isImgurAlbumUrl(url):
    # If it is imgur domain, has no file type, and is an imgur album
    return ('imgur' in url.lower()
            and not imageSaver.getFileTypeFromUrl(url)
            and '/a/' in url)


# Obnoxious special case: imgur album urls with anchors (eg /a/erere#0)
def cleanImgurAlbumUrl(url):
    anchor = url.rfind('#')
    if anchor > -1:
        return url[:anchor]
    return url

# Returns whether or not there are credits remaining
def checkImgurAPICredits(imgurClient):
    logger.log('Imgur API Credit Report:\n'
        + '\tUserRemaining: ' + str(imgurClient.credits['UserRemaining'])
        + '\n\tClientRemaining: ' + str(imgurClient.credits['ClientRemaining']))

    if not imgurClient.credits['UserRemaining']:
        logger.log('You have used up all of your Imgur API credits! Please wait an hour')
        return False

    # Ensure that this user doesn't suck up all the credits (remove this if you're an asshole)
    if imgurClient.credits['ClientRemaining'] < 1000:
        logger.log('RedditLikedSavedImageDownloader Imgur Client is running low on Imgur API credits!\n'
            'Unfortunately, this means no one can download any Imgur albums until the end of the month.\n'
            'If you are really jonesing for access, authorize your own Imgur Client and fill in'
            ' its details in settings.txt.')
        return False

    return True

class ImgurAuth:
    def __init__(self, clientId, clientSecret):
        self.clientId = clientId
        self.clientSecret = clientSecret

def getImgurAuth():
    imgurAuth = None
    if settings.hasImgurSettings():
        return ImgurAuth(settings.settings['Imgur_client_id'], 
                                         settings.settings['Imgur_client_secret'])
    else:
        logger.log('No Imgur Client ID and/or Imgur Client Secret was provided, or album download is not'
                   ' enabled. This is required to download imgur albums. They will be ignored. Check'
                   ' settings.txt for how to fill in these values.')
        return None

def saveAllImgurAlbums(outputDir, imgurAuth, subredditAlbums, soft_retrieve_imgs = True):
    numSavedAlbumsTotal = 0

    # Login to imgur
    imgurClient = imgur.ImgurClient(imgurAuth.clientId, imgurAuth.clientSecret)

    if not checkImgurAPICredits(imgurClient):
        return 0

    if not soft_retrieve_imgs:
        utilities.makeDirIfNonexistant(outputDir)

    subredditIndex = -1
    numSubreddits = len(subredditAlbums)
    for subredditDir, albums in subredditAlbums.items():
        subredditIndex += 1
        logger.log('[' + imageSaver.percentageComplete(subredditIndex, numSubreddits) + '] ' 
            + subredditDir)

        if not soft_retrieve_imgs:
            # Make directory for subreddit
            utilities.makeDirIfNonexistant(outputDir + '/' + subredditDir)

        numAlbums = len(albums)
        for albumIndex, album in enumerate(albums):
            albumSubmission = album[0]
            albumTitle = album[1]
            albumUrl = cleanImgurAlbumUrl(album[2])
            logger.log('\t[' + imageSaver.percentageComplete(albumIndex, numAlbums) + '] ' 
                + '\t' + albumTitle + ' (' + albumUrl + ')')

            # Example path:
            # output/aww/Cute Kittens_802984323
            # output/subreddit/Submission Title_urlCRC
            # The CRC is used so that if we are saving two albums with the same
            #  post title (e.g. 'me_irl') we get unique folder names because the URL is different
            saveAlbumPath = (outputDir + u'/' + subredditDir + u'/' 
                + imageSaver.safeFileName(albumTitle) + u'_' + str(signedCrc32(albumUrl.encode())))

            #saveAlbumPath = safeFileName(saveAlbumPath, file_path = True)

            # If we already saved the album, skip it
            # Note that this means updating albums will not be updated
            if os.path.isdir(saveAlbumPath):
                # In case this is a legacy album (before database file associations), add the folder's contents
                # This should only really happen if the user is purposefully downloading legacy stuff (because
                # e.g. the script got updated)
                filesFound = False
                for root, dirs, files in os.walk(saveAlbumPath):
                    for file in files:
                        print("Success {} on {}"
                              .format(utilities.outputPathToDatabasePath(os.path.join(root, file)), albumSubmission))
                        LikedSavedDatabase.db.onSuccessfulSubmissionDownload(
                            albumSubmission, utilities.outputPathToDatabasePath(os.path.join(root, file)))
                        filesFound = True
                if filesFound:
                    logger.log('\t\t[already saved] ' + 'Skipping album ' + albumTitle 
                               + ' (note that this script will NOT update albums)')                
                    continue

            if not soft_retrieve_imgs:
                # Make directory for album
                utilities.makeDirIfNonexistant(saveAlbumPath)            

            albumImages = []
            # Don't talk to the API for soft retrieval (we don't want to waste our credits)
            if not soft_retrieve_imgs:
                # Request the list of images from Imgur
                albumId = imgurIdFromUrl(albumUrl)
                if not albumId:
                    LikedSavedDatabase.db.addUnsupportedSubmission(albumSubmission,
                                                                   "Imgur album ID could not be found")
                else:
                    try:
                        if '/a/' in albumUrl:
                            albumImages = imgurClient.get_album_images(albumId)
                        else:
                            albumImages = [imgurClient.get_image(albumId)]
                    except:
                        logger.log('Imgur album url ' + albumUrl + ' could not be retrieved!')
                        LikedSavedDatabase.db.addUnsupportedSubmission(albumSubmission,
                                                                       "Imgur album hit exception")

            if not albumImages:
                continue

            numImages = len(albumImages)
            for imageIndex, image in enumerate(albumImages):
                imageUrl = image.link
                fileType = imageSaver.getFileTypeFromUrl(imageUrl)
                saveFilePath = saveAlbumPath + u'/' + str(imageIndex) + '.' + fileType

                if not soft_retrieve_imgs:
                    # Retrieve the image and save it
                    urlretrieve(imageUrl, saveFilePath)
                    LikedSavedDatabase.db.onSuccessfulSubmissionDownload(
                        albumSubmission, utilities.outputPathToDatabasePath(saveFilePath))

                logger.log('\t\t[' + imageSaver.percentageComplete(imageIndex, numImages) + '] ' 
                    + ' [save] ' + imageUrl + ' saved to "' + saveAlbumPath + '"')

            numSavedAlbumsTotal += 1

    return numSavedAlbumsTotal
