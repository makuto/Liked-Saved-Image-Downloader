# -*- coding: utf-8 -*-

import urllib
import datetime
import os
import random
from operator import attrgetter
from zlib import crc32

def getFileTypeFromUrl(url):
    if url.find('.'):
        return url[url.rfind('.') + 1:]
    else:
        return ''

def isUrlSupportedType(url):
    # no .gifv support yet (four symbols...)
    filters = ['.jpg', '.gif', '.png']
    blacklist = ['.gifv'] 
    
    isSupported = False

    # Make sure URL has file of supported type
    for currentFilter in filters:
        if currentFilter in url:
            isSupported = True
            break
            
    # Filter out unsupported types
    for currentFilter in blacklist:
        if currentFilter in url:
            isSupported = False
            break

    # Ensure that the file type doesn't have any shit besides the type (e.g. '.png?1')
    # (for now, just reject the URL rather than removing odd characters)
    fileType = getFileTypeFromUrl(url)
    for character in fileType:
        if not character.isalpha():
            isSupported = False

    return isSupported

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
    for count, submission in enumerate(sortedSubmissions):
        if isUrlSupportedType(submission.bodyUrl):
            subredditDir = submission.subreddit[3:-1]
            url = submission.bodyUrl
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
                print 'Skipping ' + saveFilePath + ' (already saved)'
                continue

            if not soft_retrieve_imgs:
                # Make directory for subreddit
                makeDirIfNonexistant(outputDir + '/' + subredditDir)

                # Retrieve the image and save it
                urllib.urlretrieve(url, saveFilePath)

            # Output our progress
            print ('[' + str(int((float(count) / float(submissionsToSave)) * 100)) + '%] ' 
                    + url + ' saved to "' + subredditDir + '"')

        else:
            print 'Skipped "' + submission.bodyUrl + '" (image not recognized/supported)'
            unsupportedSubmissions.append(submission)

    return unsupportedSubmissions