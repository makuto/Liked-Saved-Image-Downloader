# -*- coding: utf-8 -*-
from crcUtils import signedCrc32
import LikedSavedDatabase
import imageSaver
import imgurpython as imgur
import logger
import os
import sys
import utilities

import urllib
if sys.version_info[0] >= 3:
	from urllib.request import urlretrieve, urlopen
        #from urllib.request import urlopen
else:
	from urllib import urlretrieve, urlopen

def isImgurIndirectUrl(url):
    # If it is imgur domain, has no file type, and isn't an imgur album
    return ('imgur' in url.lower() 
        and not imageSaver.getFileTypeFromUrl(url) 
        and not '/a/' in url)

def convertImgurIndirectUrlToImg(url):
    IMGUR_INDIRECT_SOURCE_KEY = '<link rel="image_src"'
    IMGUR_INDIRECT_SOURCE_KEY_ATTRIBUTE = 'href='
    
    return imageSaver.findSourceFromHTML(url, IMGUR_INDIRECT_SOURCE_KEY, 
                              sourceKeyAttribute = IMGUR_INDIRECT_SOURCE_KEY_ATTRIBUTE)

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
                albumStartId = albumUrl.find('/a/') + 3
                albumEndId = albumUrl[albumStartId:].find('/')
                if albumEndId != -1:
                    albumId = albumUrl[albumStartId:albumStartId + albumEndId]
                else:
                    albumId = albumUrl[albumStartId:]

                try:
                    albumImages = imgurClient.get_album_images(albumId)
                except:
                    logger.log('Imgur album url ' + albumURL + ' could not be retrieved!')

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
                    LikedSavedDatabase.db.associateFileToSubmission(
                            utilities.outputPathToDatabasePath(saveFilePath), albumSubmission)

                logger.log('\t\t[' + imageSaver.percentageComplete(imageIndex, numImages) + '] ' 
                    + ' [save] ' + imageUrl + ' saved to "' + saveAlbumPath + '"')

            numSavedAlbumsTotal += 1

    return numSavedAlbumsTotal
