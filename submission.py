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

        return str(baseString)

    def getHtml(self):
        baseString = (u'\t<p>' + self.source + u'</p>\n'
            + u'\t<h2>' + self.title + u'</h2>\n'
            + u'\t<h3>' + self.author + u'</h3>\n'
            + u'\t<h4>' + self.subreddit + u'</h4>\n'
            + u'\t<h4>' + self.subredditTitle + u'</h4>\n'
            + u'\t<p>' + self.body + u'</p>\n'
            # + u'\t<p>' + self.bodyUrl + u'</p>\n'
            + u'\t<a href=' + self.postUrl + u'/>Link</a><br /><br />\n')

        return baseString

    def getJson(self):
        jsonpickle.set_preferred_backend('json')
        jsonpickle.set_encoder_options('json', ensure_ascii=False, indent=4, separators=(',', ': '))
        return jsonpickle.encode(self)
    
    def getAsList(self):
        return [self.source, self.title, self.author,
                self.subreddit, self.subredditTitle,
                self.body, self.bodyUrl, self.postUrl]
    
    def initFromDict(self, dictEntry):
        self.source = dictEntry['source']

        self.title = dictEntry['title']
        self.author = dictEntry['author']

        self.subreddit = dictEntry['subreddit']
        self.subredditTitle = dictEntry['subredditTitle']

        self.body = dictEntry['body']
        self.bodyUrl = dictEntry['bodyUrl']
        self.postUrl = dictEntry['postUrl']

def getAsList_generator(submissions):
    for submission in submissions:
        yield submission.getAsList()

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

def writeOutSubmissionsAsHtml(redditList, file):
    submissionsStr = ""
    for submission in redditList:
        submissionsStr += submission.getHtml() + u'\n'
        
    htmlStructure = u"""<!doctype html>

<html lang="en">
<head>
  <meta charset="utf-8">

  <title>Reddit Saved Comments</title>
</head>

<body>
{0}
</body>
</html>
    """.format(submissionsStr)
        
    file.write(htmlStructure.encode('utf8'))

def saveSubmissionsAsHtml(submissions, fileName):
    outputFile = open(fileName, 'wb')
    writeOutSubmissionsAsHtml(submissions, outputFile)
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
