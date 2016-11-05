# -*- coding: utf-8 -*-

import urllib
import datetime
import os
import random
from operator import attrgetter
from zlib import crc32
import sys

def getFileTypeFromUrl(url):
    if url and url.find('.') != -1:
        return url[url.rfind('.') + 1:]
    else:
        return ''

# Helper function. Print percentage complete
def percentageComplete(currentItem, numItems):
    if numItems:
        return str(int(((float(currentItem) / float(numItems)) * 100))) + '%'

    return 'Invalid'

def isUrlSupportedType(url):
    supportedTypes = ['jpg', 'gif', 'png', 'webm', 'mp4']
    urlFileType = getFileTypeFromUrl(url)
    return urlFileType in supportedTypes

# Find the source of an image by reading the url's HTML, looking for sourceKey
def findSourceFromHTML(url, sourceKey):
    SANE_NUM_LINES = 30

    # Open the page to search for a saveable .gif or .webm
    pageSource = urllib.urlopen(url)
    pageSourceLines = pageSource.readlines()
    pageSource.close()

    # If a page has fewer than this number of lines, there is something wrong.
    # This is a somewhat arbitrary heuristic
    if len(pageSourceLines) <= SANE_NUM_LINES:
        print 'Url "' + url + '" has a suspicious number of lines (' + str(len(pageSourceLines)) + ')'

    for line in pageSourceLines:
        foundSourcePosition = line.lower().find(sourceKey.lower())
        
        if foundSourcePosition > -1:
            # Find the first character of the URL (add 1 for the ")
            urlStartPosition = foundSourcePosition + len(sourceKey) + 1

            # From the start of the url, search for the next '"' which is the end of the src link
            urlEndPosition = line[urlStartPosition:].find('"')

            if urlEndPosition > -1:
                sourceUrl = line[urlStartPosition:urlStartPosition + urlEndPosition]

                return sourceUrl

    return ''

def isGfycatUrl(url):
    return 'gfycat' in url.lower()

# Special handling for Gfycat links
# Returns a URL to a webm which can be downloaded by urllib
def convertGfycatUrlToWebM(url):
    # Change this:
    #   https://gfycat.com/IndolentScalyIncatern
    # Into this:
    #   https://zippy.gfycat.com/IndolentScalyIncatern.webm
    # Or maybe this:
    #   https://giant.gfycat.com/IndolentScalyIncatern.webm

    # Look for this key in the HTML document and get whatever src is
    GFYCAT_SOURCE_KEY = '<source id="webmSource" src='

    return findSourceFromHTML(url, GFYCAT_SOURCE_KEY)

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

def getURLSFromFile(filename):
    f = open(filename, 'r')
    urls = []
    nonRelevantURLs = 0
    
    for line in f:
        if isUrlSupportedType(line):
            urls.append(line[:-1]) #trim off the newline
        else:
            nonRelevantURLs += 1

    print 'Filtered ' + str(nonRelevantURLs) + ' URLs that didn\'t contain images'
    return urls

def saveAllImagesToDir(urls, directory, soft_retrieve = True):
    count = 0
    imagesToSave = len(urls)
    for url in urls:
        if not soft_retrieve:
            urllib.urlretrieve(url, directory + '/img' + str(count) + url[-4:])

        count += 1
        print ('[' + str(int((float(count) / float(imagesToSave)) * 100)) + '%] ' 
            + url + ' saved to "' + directory + '/img' + str(count) + url[-4:] + '"')

def makeDirIfNonexistant(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
        
#note that you must explicitly set soft_retrieve to False to actually get the images
def saveAllImages(soft_retrieve_imgs=True):
    saved_urls = getURLSFromFile('savedURLS.txt')
    liked_urls = getURLSFromFile('likedURLS.txt')
    timestamp = datetime.datetime.now().strftime('%m-%d_%H-%-M-%S')
    count = 0
    savedDirectory = 'ImagesSaved__' + timestamp
    likedDirectory = 'ImagesLiked__' + timestamp

    makeDirIfNonexistant(savedDirectory)
    makeDirIfNonexistant(likedDirectory)

    saveAllImagesToDir(saved_urls, savedDirectory, soft_retrieve = soft_retrieve_imgs)
    saveAllImagesToDir(liked_urls, likedDirectory, soft_retrieve = soft_retrieve_imgs)

# Make sure the filename is alphanumeric or has supported symbols, and is shorter than 45 characters
def safeFileName(filename):
    acceptableChars = ['_', ' ']
    safeName = ''
    for char in filename:
        if char.isalnum() or char in acceptableChars:
            safeName += char

    # If there were no valid characters, give it a random number for a unique title
    if not safeName:
        safeName = 'badName_' + str(random.randint(1, 1000000))

    MAX_NAME_LENGTH = 45
    if len(safeName) > MAX_NAME_LENGTH:
        safeName = safeName[:MAX_NAME_LENGTH]

    return safeName

# Save the images in directories based on subreddits
# Name the images based on their submission titles
# Returns a list of submissions which didn't have supported image formats
def saveAllImages_Advanced(outputDir, submissions, soft_retrieve_imgs = True):
    if not soft_retrieve_imgs:
        makeDirIfNonexistant(outputDir)
    
    sortedSubmissions = sorted(submissions, key=attrgetter('subreddit'))

    unsupportedSubmissions = []

    submissionsToSave = len(sortedSubmissions)
    for currentSubmissionIndex, submission in enumerate(sortedSubmissions):
        url = submission.bodyUrl

        # Massage Gfycat links so that they can be downloaded
        if isGfycatUrl(url):
            url = convertGfycatUrlToWebM(url)

        if isGifVUrl(url):
            url = convertGifVUrlToWebM(url)

        if isUrlSupportedType(url):
            subredditDir = submission.subreddit[3:-1]
            fileType = getFileTypeFromUrl(url)

            # Example path:
            # output/aww/My Cute Kitten_802984323.png
            # output/subreddit/Submission Title_urlCRC.fileType
            # The CRC is used so that if we are saving two images with the same
            #  post title (e.g. 'me_irl') we get unique filenames because the URL is different
            saveFilePath = (outputDir + u'/' + subredditDir + u'/' 
                + safeFileName(submission.title) + u'_' + unicode(crc32(url)) + u'.' + fileType)

            # If we already saved the image, skip it
            if os.path.isfile(saveFilePath):
                print ('[' + percentageComplete(currentSubmissionIndex, submissionsToSave) + '] ' 
                    + ' [already saved] ' + 'Skipping ' + saveFilePath)
                continue

            if not soft_retrieve_imgs:
                # Make directory for subreddit
                makeDirIfNonexistant(outputDir + '/' + subredditDir)

                # Retrieve the image and save it
                urllib.urlretrieve(url, saveFilePath)

            # Output our progress
            print ('[' + percentageComplete(currentSubmissionIndex, submissionsToSave) + '] ' 
                    + ' [save] ' + url + ' saved to "' + subredditDir + '"')

        else:
            print ('[' + percentageComplete(currentSubmissionIndex, submissionsToSave) + '] '
                + ' [unsupported] ' + 'Skipped "' + url + '"')
            unsupportedSubmissions.append(submission)

    return unsupportedSubmissions