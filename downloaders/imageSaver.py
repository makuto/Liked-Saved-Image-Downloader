# -*- coding: utf-8 -*-

import json
import os
import random
import re
import sys
import time

from builtins import str
from operator import attrgetter

import urllib
if sys.version_info[0] >= 3:
	from urllib.request import urlretrieve, urlopen
        #from urllib.request import urlopen
else:
	from urllib import urlretrieve, urlopen

# third-party imports
# Must use API to access images
from pixivpy3 import *
from gfycat.client import GfycatClient

# local imports
import settings
import LikedSavedDatabase
import submission as Submissions
from downloaders import imgurDownloader, videoDownloader
from downloaders.redditScraper import redditClient, isRedditGallery, downloadRedditGallery
from utils import logger, utilities
from utils.crcUtils import signedCrc32

SupportedTypes = ['jpg', 'jpeg', 'gif', 'png', 'webm', 'mp4']

def getFileTypeFromUrl(url):
    if url and url.find('.') != -1 and url.rfind('.') > url.rfind('/'):
        return url[url.rfind('.') + 1:]
    else:
        return ''

# Helper function. Print percentage complete
def percentageComplete(currentItem, numItems):
    if numItems:
        return str(int(((float(currentItem + 1) / float(numItems)) * 100))) + '%'

    return 'Invalid'

def isUrlSupportedType(url):
    urlFileType = getFileTypeFromUrl(url)
    return urlFileType in SupportedTypes

def getUrlContentType(url):
    if url:
        openedUrl = None
        try:
            openedUrl = urlopen(url)
        except IOError as e:
            logger.log('[ERROR] getUrlContentType(): IOError: Url {0} raised exception:\n\t{1} {2}'
                .format(url, e.errno, e.strerror))
        except Exception as e:
            logger.log('[ERROR] Exception: Url {0} raised exception:\n\t {1}'
                        .format(url, e))
            logger.log('[ERROR] Url ' + url + 
                ' raised an exception I did not handle. Open an issue at '
                '\n\thttps://github.com/makuto/redditLikedSavedImageDownloader/issues'
                '\n and I will try to fix it')
        else:
            if sys.version_info[0] >= 3:
                return openedUrl.info().get_content_subtype()
            else:
                return openedUrl.info().subtype
    return ''

def isContentTypeSupported(contentType):
    # JPGs are JPEG
    supportedTypes = SupportedTypes + ['jpeg']
    return contentType.lower() in supportedTypes

def convertContentTypeToFileType(contentType):
    # Special case: we want all our JPEGs to be .jpg :(
    if contentType.lower() == 'jpeg':
        return 'jpg'

    return contentType

def getUrlLines(url):
    # Open the page to search for a saveable .gif or .webm
    try:
        pageSource = urlopen(url)
    except urllib.error.HTTPError as e:
        logger.log("URL {} had HTTP error:\n{}".format(url, str(e.reason)))
        return None, None

    # This code doesn't quite work yet; if things are breaking near here you're not reading a .html
    # Leaving this here for future work
    pageEncoding = None
    if sys.version_info[0] >= 3:
        pageEncoding = pageSource.headers.get_content_charset()
        #logger.log(pageSource.headers.get_content_subtype())
        #logger.log(url)

    pageSourceLines = pageSource.readlines()
    pageSource.close()

    return pageSourceLines, pageEncoding

# Find the source of an image by reading the url's HTML, looking for sourceKey
# An example key would be '<img src='. Note that the '"' will automatically be 
#  recognized as part of the key, so do not specify it
# If sourceKeyAttribute is specified, sourceKey will first be found, then 
#  the line will be searched for sourceKeyAttribute (e.g. sourceKey = '<img' and 
#  sourceKeyAttribute = 'src=').
def findSourceFromHTML(url, sourceKey, sourceKeyAttribute=''):
    SANE_NUM_LINES = 30

    pageSourceLines, pageEncoding = getUrlLines(url)

    if not pageSourceLines:
        return None

    # If a page has fewer than this number of lines, there is something wrong.
    # This is a somewhat arbitrary heuristic
    if len(pageSourceLines) <= SANE_NUM_LINES:
        logger.log('Url "' + url + '" has a suspicious number of lines (' + str(len(pageSourceLines)) + ')')

    for line in pageSourceLines:
        lineStr = line
        if sys.version_info[0] >= 3 and pageEncoding:
            # If things are breaking near here you're not reading a .html
            lineStr = line.decode(pageEncoding)

        try:
            foundSourcePosition = lineStr.lower().find(sourceKey.lower())
        # Probably not reading a text file; we won't be able to determine the type
        except TypeError:
            logger.log('Unable to guess type for Url "' + url)
            return ''

        if foundSourcePosition > -1:
            urlStartPosition = -1
            if sourceKeyAttribute:
                attributePosition = lineStr[foundSourcePosition:].lower().find(sourceKeyAttribute.lower())
                # Find the first character of the URL specified by the attribute (add 1 for the ")
                urlStartPosition = foundSourcePosition + attributePosition + len(sourceKeyAttribute) + 1
            else:
                # Find the first character of the URL (add 1 for the ")
                urlStartPosition = foundSourcePosition + len(sourceKey) + 1

            # From the start of the url, search for the next '"' which is the end of the src link
            urlEndPosition = lineStr[urlStartPosition:].find('"')

            if urlEndPosition > -1:
                sourceUrl = lineStr[urlStartPosition:urlStartPosition + urlEndPosition]

                return sourceUrl

    return ''

def isGfycatUrl(url):
    return ('gfycat' in url.lower()
            and '.webm' not in url.lower()
            and '.gif' not in url.lower()[-4:])

def gfycatToRedGifsWorkaround(gfyUrl):
    logger.log("Using Gfycat->RedGifs workaround")
    return findSourceFromHTML(gfyUrl, '<source id="mp4source" src=')

# Lazy initialize in case it's not needed
gfycatClient = None
# Special handling for Gfycat links
# Returns a URL to a webm which can be downloaded by urllib
def convertGfycatUrlToWebM(submission, url):
    global gfycatClient
    # Change this:
    #   https://gfycat.com/IndolentScalyIncatern
    #   https://gfycat.com/IndolentScalyIncatern/
    # Into this:
    #   https://zippy.gfycat.com/IndolentScalyIncatern.webm
    # Or maybe this:
    #   https://giant.gfycat.com/IndolentScalyIncatern.webm

    # Lazy initialize client
    if not gfycatClient and settings.settings['Gfycat_Client_id']:
        gfycatClient = GfycatClient(settings.settings['Gfycat_Client_id'], settings.settings['Gfycat_Client_secret'])

    # Still don't have a client?
    if not gfycatClient:
        logger.log("Warning: no Gfycat client; gifs will likely fail to download")
        newUrl = gfycatToRedGifsWorkaround(url)
        if newUrl:
            return newUrl
        # Hacky solution while Gfycat API isn't set up. This breaks if case is wrong
        return "https://giant.gfycat.com/{}.webm".format(url[url.rfind("/") + 1:])
    else:
        # Get the gfyname from the url
        matches = re.findall(r'gfycat\.com.*/([a-zA-Z]+)', url)
        if not matches:
            errorMessage = "Gfycat URL {} doesn't seem to match expected URL format".format(url)
            logger.log(errorMessage)
            LikedSavedDatabase.db.addUnsupportedSubmission(submission, errorMessage)
        else:
            try:
                gfycatUrlInfo = gfycatClient.query_gfy(matches[0])
            except Exception as e:
                errorMessage = '[ERROR] Exception: Url {0} raised exception:\n\t {1}'.format(url, e)
                logger.log(errorMessage)
                logger.log("Gfycat client was used to make this query")
                # Gfycat sucks. They created RedGifs, but broke Gfycat API by making it not actually
                # support that transition, and you can't get a RedGifs API token unless you email
                # them for one. Great engineering, folks
                newUrl = gfycatToRedGifsWorkaround(url)
                if newUrl:
                    return newUrl
                LikedSavedDatabase.db.addUnsupportedSubmission(submission, errorMessage)
                return None
            return gfycatUrlInfo['gfyItem']['mp4Url']

def isGifVUrl(url):
    return getFileTypeFromUrl(url) == 'gifv'

# Special handling for Imgur's .gifv
def convertGifVUrlToWebM(url):
    # Find the source link
    GIFV_SOURCE_KEY = '<source src='
    gifvSource = findSourceFromHTML(url, GIFV_SOURCE_KEY)

    # Didn't work? Try the alternate key
    if not gifvSource:
        ALTERNATE_GIFV_SOURCE_KEY = '<meta itemprop="contentURL" content='
        gifvSource = findSourceFromHTML(url, ALTERNATE_GIFV_SOURCE_KEY)

    # Still nothing? Try text hacking .mp4 onto the link and hope it's valid
    if not gifvSource:
        gifvSource = url[:-5] + '.mp4'

    # For whatever reason, Imgur has this screwy no http(s) on their source links sometimes
    if gifvSource and gifvSource[:2] == '//':
        gifvSource = 'http:' + gifvSource

    return gifvSource

def findSourceForRedGif(url):
    pageSourceLines, pageEncoding = getUrlLines(url)
    videoElement = "<video id=\"video-{}".format(url[url.rfind("/") + 1:])
    logger.log("RedGifs: looking for {}".format(videoElement))

    foundSourcePosition = None
    for line in pageSourceLines:
        lineStr = line
        if sys.version_info[0] >= 3 and pageEncoding:
            # If things are breaking near here you're not reading a .html
            lineStr = line.decode(pageEncoding)

        # State machine; only look for source once we've hit the video we care about
        if foundSourcePosition:
            try:
                sourcePosition = lineStr.lower().find('<source src="'.lower())
                if sourcePosition:
                    # Ignore low quality mobile and webm formats
                    if 'mobile'.lower() not in lineStr.lower() and '.mp4' in lineStr:
                        matches = re.findall(r'src="([^"]*)"', url)
                        return matches[0]
                # Probably not reading a text file; we won't be able to determine the type
            except TypeError:
                logger.log('Unable to guess type for Url "' + url)
                return None
        else:
            try:
                foundSourcePosition = lineStr.lower().find(videoElement.lower())
                # Probably not reading a text file; we won't be able to determine the type
            except TypeError:
                logger.log('Unable to guess type for Url "' + url)
                return None


    return None

# Make sure the filename is alphanumeric or has supported symbols, and is shorter than 45 characters
def safeFileName(filename, file_path = False):
    acceptableChars = ['_', ' ']
    safeName = ''

    # If we are making a file path safe, allow / and \
    if file_path:
        acceptableChars += ['/', '\\']

    for char in filename:
        if char.isalnum() or char in acceptableChars:
            safeName += char

    # If there were no valid characters, give it a random number for a unique title
    if not safeName:
        safeName = 'badName_' + str(random.randint(1, 1000000))

    if not file_path:
        MAX_NAME_LENGTH = 250
        if len(safeName) > MAX_NAME_LENGTH:
            safeName = safeName[:MAX_NAME_LENGTH]

    return safeName

# Save the images in directories based on subreddits
# Name the images based on their submission titles
# Returns a list of submissions which didn't have supported image formats
def saveAllImages(outputDir, submissions, imgur_auth = None, only_download_albums = False,
                  skip_n_percent_submissions = 0, 
                  soft_retrieve_imgs = False, only_important_messages = False):
    numSavedImages = 0
    numAlreadySavedImages = 0
    numSavedAlbums = 0
    numAlreadySavedVideos = 0
    numSavedVideos = 0
    numUnsupportedImages = 0
    numUnsupportedAlbums = 0
    numUnsupportedVideos = 0

    unsupportedSubmissions = []

    # Dictionary where key = subreddit and value = list of (submissionTitle, imgur album urls)
    imgurAlbumsToSave = {}

    if not soft_retrieve_imgs:
        utilities.makeDirIfNonexistant(outputDir)
    
    # Sort by subreddit, alphabetically
    sortedSubmissions = sorted(submissions, key=attrgetter('subreddit'))

    # Start further into the list (in case the script failed early or something and you don't want 
    #  to redownload everything)
    if skip_n_percent_submissions:
        newFirstSubmissionIndex = int((len(sortedSubmissions) / 100) * skip_n_percent_submissions)
        sortedSubmissions = sortedSubmissions[newFirstSubmissionIndex:]

        logger.log('Starting at ' + str(skip_n_percent_submissions) + '%; skipped ' +
            str(newFirstSubmissionIndex) + ' submissions')

    # Lazy-initialized
    pixivApi = None

    submissionsToSave = len(sortedSubmissions)

    # lazy
    reddit_client = redditClient()

    for currentSubmissionIndex, submission in enumerate(sortedSubmissions):
        url = submission.bodyUrl
        subredditDir = submission.subreddit[3:-1] if submission.source == u'reddit' else safeFileName(submission.subredditTitle)
        submissionTitle = submission.title
        # Always trust tumblr submissions because we know 100% they're images
        shouldTrustUrl = (submission.source == u'Tumblr')
        # Always use tumblr Submission titles because we generate them in tumblrScraper
        shouldTrustTitle = (submission.source == u'Tumblr')

        if not url:
            continue

        # All pixiv downloads need to go through the pixiv API
        if submission.source == u'Pixiv':
            # Always re-login because it'll timeout otherwise
            if not pixivApi:
                pixivApi = AppPixivAPI()
                pixivLoginJson = pixivApi.login(settings.settings['Pixiv_username'],
                                                settings.settings['Pixiv_password'])

            submissionOutputDir = outputDir + u'/' + subredditDir
            utilities.makeDirIfNonexistant(submissionOutputDir)
            # Weird webp format...
            pixivFilename = "{}_{}.riff".format(str(signedCrc32(submission.postUrl.encode())),
                                                safeFileName(submissionTitle))
            saveFilePath = "{}/{}".format(submissionOutputDir, pixivFilename)
            if os.path.isfile(saveFilePath):
                if not only_important_messages:
                    logger.log('[' + percentageComplete(currentSubmissionIndex, submissionsToSave) + '] '
                               + ' [already saved] ' + 'Skipping ' + saveFilePath)
                numAlreadySavedImages += 1
                continue

            # Go easy on the Pixiv server
            # I should do this for the other sites too, but oh well
            time.sleep(random.random() * 2.0)
            downloaded = pixivApi.download(url,
                                           path=submissionOutputDir,
                                           name=pixivFilename)
            if downloaded:
                logger.log('[' + percentageComplete(currentSubmissionIndex, submissionsToSave) + '] '
                           + ' [save] ' + 'Saved "' + url + '" to ' + saveFilePath)
                LikedSavedDatabase.db.onSuccessfulSubmissionDownload(submission,
                                                                     utilities.outputPathToDatabasePath(saveFilePath))
                numSavedImages += 1
            else:
                LikedSavedDatabase.db.addUnsupportedSubmission(submission,
                                                               "Failed to download from Pixiv")
                numUnsupportedImages += 1
            continue

        urlContentType = getUrlContentType(url)

        if videoDownloader.shouldUseYoutubeDl(url):
            if "gfycat" in url:
                possibleRedGifUrl = gfycatToRedGifsWorkaround(url)
                if possibleRedGifUrl and 'redgifs' in possibleRedGifUrl:
                    logger.log("Using RedGifs redirect for YoutubeDL")
                    url = url.replace("gfycat.com/", "redgifs.com/watch/")
            result = videoDownloader.downloadVideo(outputDir + u'/' + subredditDir, url)
            if not result[0]:
                if result[1] == videoDownloader.alreadyDownloadedSentinel:
                    LikedSavedDatabase.db.removeFromUnsupportedSubmissions(submission)
                    numAlreadySavedVideos += 1
                else:
                    logger.log('[' + percentageComplete(currentSubmissionIndex, submissionsToSave) + '] '
                               + ' [unsupported] ' + 'Failed to retrieve "' + url + '" (video). Reason: ' + result[1])
                    LikedSavedDatabase.db.addUnsupportedSubmission(submission, result[1])
                    numUnsupportedVideos += 1
            else:
                logger.log('[' + percentageComplete(currentSubmissionIndex, submissionsToSave) + '] '
                           + ' [save] ' + 'Saved "' + url + '" (video) to ' + result[1])
                LikedSavedDatabase.db.onSuccessfulSubmissionDownload(
                    submission, utilities.outputPathToDatabasePath(result[1]))
                numSavedVideos += 1
            continue
        elif settings.settings['Only_download_videos'] and not 'gfycat' in url:
            logger.log("Skipped {} due to 'Only download videos' setting".format(url))
            continue

        if isRedditGallery(reddit_client, submission, urlContentType):
            if not soft_retrieve_imgs:
                downloadedMedia = downloadRedditGallery(reddit_client, submission, outputDir)

                for saveFilePath in downloadedMedia:
                    LikedSavedDatabase.db.onSuccessfulSubmissionDownload(
                        submission, utilities.outputPathToDatabasePath(saveFilePath))

                if downloadedMedia:
                    # Output our progress
                    logger.log('[' + percentageComplete(currentSubmissionIndex, submissionsToSave) + '] ' 
                            + ' [save] ' + url + ' saved to "' + subredditDir + '"')
                    numSavedAlbums += 1

                continue

        if not shouldTrustUrl:
            # Imgur Albums have special handling
            if imgurDownloader.isImgurAlbumUrl(url):
                if not imgur_auth:
                    logger.log('[' + percentageComplete(currentSubmissionIndex, submissionsToSave) + '] '
                        + ' [unsupported] ' + 'Skipped "' + url + '" (imgur album)')
                    LikedSavedDatabase.db.addUnsupportedSubmission(submission,
                                                                   "Imgur albums not supported without Imgur Authentication")
                    numUnsupportedAlbums += 1
                    continue
                elif not settings.settings['Should_download_albums']:
                    logger.log("Skipped {} due to 'Should download albums' set to false".format(url))
                    continue
                else:
                    # We're going to save Imgur Albums at a separate stage
                    if subredditDir in imgurAlbumsToSave:
                        imgurAlbumsToSave[subredditDir].append((submission, submissionTitle, url))
                    else:
                        imgurAlbumsToSave[subredditDir] = [(submission, submissionTitle, url)]
                    continue
            elif only_download_albums:
                continue

            # Massage special-case links so that they can be downloaded
            if isGfycatUrl(url):
                url = convertGfycatUrlToWebM(submission, url)
            elif isGifVUrl(url):
                url = convertGifVUrlToWebM(url)
            elif 'redgifs.com' in url:
                url = findSourceForRedGif(url)
                if not url:
                    LikedSavedDatabase.db.addUnsupportedSubmission(submission,
                                                                   "Failed to find source from RedGifs HTML")
                    numUnsupportedImages += 1
                    continue
            elif imgurDownloader.isImgurIndirectUrl(url):
                if not imgur_auth:
                    logger.log('[' + percentageComplete(currentSubmissionIndex, submissionsToSave) + '] '
                        + ' [unsupported] ' + 'Skipped "' + url + '" (imgur indirect link)')
                    LikedSavedDatabase.db.addUnsupportedSubmission(submission,
                                                                   "Imgur indirect links not supported without Imgur Authentication")
                    numUnsupportedImages += 1
                    continue
                url = imgurDownloader.convertImgurIndirectUrlToImg(submission, imgur_auth, url)

            if url:
                # Trust these because they are always parsed successfully
                if 'redgifs' in url:
                    logger.log("WARNING: RedGifs will likely block this request. Please enable YoutubeDL"
                               " to work around this")
                    urlContentType = getFileTypeFromUrl(url)
                    shouldTrustUrl = True
                else:
                    # keep urlContentType the same
                    pass
            else:
                logger.log('[' + percentageComplete(currentSubmissionIndex, submissionsToSave) + '] '
                        + ' [unsupported] ' + 'Failed to resolve trusted URL')
                LikedSavedDatabase.db.addUnsupportedSubmission(submission,
                                                               "No trusted URL found")
                numUnsupportedImages += 1
                continue

        if shouldTrustUrl or isUrlSupportedType(url) or isContentTypeSupported(urlContentType):
            fileType = getFileTypeFromUrl(url)
            if not fileType:
                fileType = convertContentTypeToFileType(urlContentType)

            if not shouldTrustUrl:
                # If the file path doesn't match the content type, it's possible it's incorrect 
                #  (e.g. a .png labeled as a .jpg)
                contentFileType = convertContentTypeToFileType(urlContentType)
                if contentFileType != fileType and (contentFileType != 'jpg' and fileType != 'jpeg'):
                    logger.log('WARNING: Content type "' + contentFileType 
                        + '" was going to be saved as "' + fileType + '"! Correcting.')
                    if contentFileType == 'html':
                        logger.log('[' + percentageComplete(currentSubmissionIndex, submissionsToSave) + '] '
                            + ' [unsupported] ' + 'Skipped "' + url 
                            + '" (file is html, not image; this might mean Access was Denied)')
                        numUnsupportedImages += 1
                        continue

                    fileType = contentFileType

            if shouldTrustTitle:
                saveFilePath = (outputDir + u'/' + subredditDir + u'/' 
                    + safeFileName(submissionTitle) + u'.' + fileType)
            else:
                # Example path:
                # output/aww/My Cute Kitten_802984323.png
                # output/subreddit/Submission Title_urlCRC.fileType
                # The CRC is used so that if we are saving two images with the same
                #  post title (e.g. 'me_irl') we get unique filenames because the URL is different
                saveFilePath = (outputDir + u'/' + subredditDir + u'/' + safeFileName(submissionTitle)
                                + u'_' + str(signedCrc32(url.encode())) + u'.' + fileType)

                # Maybe not do this? Ubuntu at least can do Unicode folders etc. just fine
                #saveFilePath = safeFileName(saveFilePath, file_path = True)

            # If we already saved the image, skip it
            # TODO: Try not to make make any HTTP requests on skips...
            if os.path.isfile(saveFilePath):
                if not only_important_messages:
                    logger.log('[' + percentageComplete(currentSubmissionIndex, submissionsToSave) + '] ' 
                        + ' [already saved] ' + 'Skipping ' + saveFilePath)
                # In case of legacy unsupported submissions, update with the new submission
                LikedSavedDatabase.db.onSuccessfulSubmissionDownload(submission,
                                                                     utilities.outputPathToDatabasePath(saveFilePath))
                numAlreadySavedImages += 1
                continue

            if not soft_retrieve_imgs:
                # Make directory for subreddit
                utilities.makeDirIfNonexistant(outputDir + '/' + subredditDir)

                # Retrieve the image and save it
                try:
                    urlretrieve(url, saveFilePath)

                    LikedSavedDatabase.db.onSuccessfulSubmissionDownload(
                        submission, utilities.outputPathToDatabasePath(saveFilePath))
                except IOError as e:
                    errorMessage = '[ERROR] retrieval: IOError: Url {0} raised exception:\n\t{1} {2}'.format(url, e.errno, e.strerror)
                    logger.log(errorMessage)
                    LikedSavedDatabase.db.addUnsupportedSubmission(submission, errorMessage)
                    numUnsupportedImages += 1
                    continue
                except KeyboardInterrupt:
                    exit()
                except Exception as e:
                    errorMessage = '[ERROR] Exception: Url {0} raised exception:\n\t {1}'.format(url, e)
                    logger.log(errorMessage)
                    logger.log('[ERROR] Url ' + url + 
                        ' raised an exception I did not handle. Open an issue at '
                        '\n\thttps://github.com/makuto/redditLikedSavedImageDownloader/issues'
                        '\n and I will try to fix it')
                    LikedSavedDatabase.db.addUnsupportedSubmission(submission, errorMessage)
                    numUnsupportedImages += 1
                    continue

            # Output our progress
            logger.log('[' + percentageComplete(currentSubmissionIndex, submissionsToSave) + '] ' 
                    + ' [save] ' + url + ' saved to "' + subredditDir + '"')
            numSavedImages += 1

        else:
            logger.log('[' + percentageComplete(currentSubmissionIndex, submissionsToSave) + '] '
                + ' [unsupported] ' + 'Skipped "' + url + '" (content type "' + urlContentType + '")')
            unsupportedSubmissions.append(submission)
            LikedSavedDatabase.db.addUnsupportedSubmission(submission,
                                                           "URL or content type {} not supported".format(urlContentType))
            numUnsupportedImages += 1

    if imgur_auth and imgurAlbumsToSave:
        numSavedAlbums = imgurDownloader.saveAllImgurAlbums(outputDir, imgur_auth, imgurAlbumsToSave, 
                                                            soft_retrieve_imgs = soft_retrieve_imgs)

    logger.log('Good:')
    logger.log('\t Saved Images: {}'.format(numSavedImages))
    logger.log('\t Already Saved Images: {}'.format(numAlreadySavedImages))
    logger.log('\t Saved Albums: {}'.format(numSavedAlbums))
    logger.log('\t Saved Videos: {}'.format(numSavedVideos))
    logger.log('\t Already Saved Videos: {}'.format(numAlreadySavedVideos))
    logger.log('Bad:')
    logger.log('\t Unsupported Images: {}'.format(numUnsupportedImages))
    logger.log('\t Unsupported Albums: {}'.format(numUnsupportedAlbums))
    logger.log('\t Unsupported Videos: {}'.format(numUnsupportedVideos))

    return unsupportedSubmissions

def loadSubmissionsFromJson(filename):
    file = open(filename, 'r')
    # Ugh...
    lines = file.readlines()
    text = u''.join(lines)
    # Fix the formatting so the json module understands it
    text = "[{}]".format(text[1:-3])
        
    dictSubmissions = json.loads(text)
    submissions = []
    for dictSubmission in dictSubmissions:
        submission = Submissions.Submission()
        submission.initFromDict(dictSubmission)
        submissions.append(submission)

    return submissions

if __name__ == '__main__':
    print("Running image saver tests")

    outputDirOverride = 'LOCAL_testOutput'
    utilities.makeDirIfNonexistant(outputDirOverride)
    
    settings.getSettings()
    LikedSavedDatabase.initializeFromSettings(settings.settings)
    
    # Temporary override
    settings.settings['Output_dir'] = outputDirOverride
    
    testSubmissions = loadSubmissionsFromJson('LOCAL_imageSaver_test_submissions.json')
    if testSubmissions:        
        unsupportedSubmissions = saveAllImages(outputDirOverride, testSubmissions, 
                                               imgur_auth = imgurDownloader.getImgurAuth(),
                                               only_download_albums = settings.settings['Only_download_albums'],
                                               skip_n_percent_submissions = settings.settings['Skip_n_percent_submissions'],
                                               soft_retrieve_imgs = settings.settings['Should_soft_retrieve'],
                                               only_important_messages = settings.settings['Only_important_messages'])
    else:
        print("No submissions found")
