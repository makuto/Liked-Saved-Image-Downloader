# -*- coding: utf-8 -*-

import pickle
import jsonpickle
import os

class Submission:
    def __init__(self):
        # Source is either Tumblr or Reddit
        self.source = u''

        self.title = u''
        self.author = u''

        self.subreddit = u''
        self.subredditTitle = u''

        self.body = u''
        self.bodyUrl = u''
        self.postUrl = u''

    def getXML(self):
        baseString = (u'\t<source>' + self.source + u'</source>\n'
            + u'\t<title>' + self.title + u'</title>\n'
            + u'\t<author>' + self.author + u'</author>\n'
            + u'\t<subreddit>' + self.subreddit + u'</subreddit>\n'
            + u'\t<subredditTitle>' + self.subredditTitle + u'</subredditTitle>\n'
            + u'\t<body>' + self.body + u'</body>\n'
            + u'\t<bodyUrl>' + self.bodyUrl + u'</bodyUrl>\n'
            + u'\t<postUrl>' + self.postUrl + u'</postUrl>\n')

        return unicode(baseString)

    def getJson(self):
        jsonpickle.set_preferred_backend('json')
        jsonpickle.set_encoder_options('json', ensure_ascii=False, indent=4, separators=(',', ': '))
        return jsonpickle.encode(self)

def writeOutSubmissionsAsJson(redditList, file):
    file.write('{\n'.encode('utf8'))
    for submission in redditList:
        outputString = submission.getJson() + u',\n'
        file.write(outputString.encode('utf8'))
    file.write('}'.encode('utf8'))

def saveSubmissionsAsJson(submissions, fileName):
    outputFile = open(fileName, 'wb')
    writeOutSubmissionsAsJson(submissions, outputFile)
    outputFile.close()

def writeOutSubmissionsAsXML(redditList, file):
    for submission in redditList:
        outputString = u'<submission>\n' + submission.getXML() + u'</submission>\n'
        file.write(outputString.encode('utf8'))

def saveSubmissionsAsXML(submissions, fileName):
    outputFile = open(fileName, 'wb')
    writeOutSubmissionsAsXML(submissions, outputFile)
    outputFile.close()

def writeCacheSubmissions(submissions, cacheFileName):
    cacheFile = open(cacheFileName, 'wb')
    pickle.dump(submissions, cacheFile)

def readCacheSubmissions(cacheFileName):
    if os.path.exists(cacheFileName):
        cacheFile = open(cacheFileName, 'rb')
        submissions = pickle.load(cacheFile)
        return submissions
    else:
        return []
