#import scrapy

import urllib
import datetime
import os

def getURLSFromFile(filename):
    f = open(filename, 'r')
    urls = []
    nonRelevantURLs = 0
    #no .gifv support yet (four symbols...)
    filters = ['.jpg', '.gif', '.png']
    blacklist = ['.gifv'] 
    
    for line in f:
        isRelevant = False
        for currentFilter in filters:
            if currentFilter in line:
                isRelevant = True
                break
                
        #Filter out blacklisted URLs (unsupported formats etc.)
        for currentFilter in blacklist:
            if currentFilter in line:
                isRelevant = False
                break

        if isRelevant:
            urls.append(line[:-1]) #trim off the newline

        else:
            nonRelevantURLs += 1
    print 'Filtered ' + str(nonRelevantURLs) + ' URLs that didn\'t contain images'
    return urls

def _saveAllImagesToDir(urls, directory, soft_retrieve = True):
    count = 0
    imagesToSave = len(urls)
    for url in urls:
        if not soft_retrieve:
            urllib.urlretrieve(url, directory + '/img' + str(count) + url[-4:])

        count += 1
        print '[' + str(int((float(count) / float(imagesToSave)) * 100)) + '%] ' + url + ' saved to "' + directory + '/img' + str(count) + url[-4:] + '"'

def _makeDirIfNonexistant(directory):
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

    _makeDirIfNonexistant(savedDirectory)
    _makeDirIfNonexistant(likedDirectory)

    _saveAllImagesToDir(saved_urls, savedDirectory, soft_retrieve = soft_retrieve_imgs)
    _saveAllImagesToDir(liked_urls, likedDirectory, soft_retrieve = soft_retrieve_imgs)
