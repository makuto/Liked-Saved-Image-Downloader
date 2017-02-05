# -*- coding: utf-8 -*-

import praw
import pickle
import jsonpickle

user_agent = 'Python Script: v2.0: Reddit Liked Saved Image Downloader (by /u/makuto9)'

# Helper function. Print percentage complete
def percentageComplete(currentItem, numItems):
    if numItems:
        return str(int(((float(currentItem + 1) / float(numItems)) * 100))) + '%'

    return 'Invalid'
    
class RedditSubmission:
    def __init__(self):
        self.title = u''
        self.author = u''
        self.subreddit = u''
        self.subredditTitle = u''
        self.body = u''
        self.bodyUrl = u''
        self.postUrl = u''

    def getXML(self):
        baseString = (u'\t<title>' + self.title + u'</title>\n'
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

def writeOutRedditSubmissionsAsJson(redditList, file):
    file.write('{\n')
    for submission in redditList:
        outputString = submission.getJson() + u',\n'
        file.write(outputString.encode('utf8'))
    file.write('}')

def saveSubmissionsAsJson(submissions, fileName):
    outputFile = open(fileName, 'w')
    writeOutRedditSubmissionsAsJson(submissions, outputFile)
    outputFile.close()

def writeOutRedditSubmissionsAsXML(redditList, file):
    for submission in redditList:
        outputString = u'<submission>\n' + submission.getXML() + u'</submission>\n'
        file.write(outputString.encode('utf8'))

def saveSubmissionsAsXML(submissions, fileName):
    outputFile = open(fileName, 'w')
    writeOutRedditSubmissionsAsXML(submissions, outputFile)
    outputFile.close()

def writeCacheRedditSubmissions(submissions, cacheFileName):
    cacheFile = open(cacheFileName, 'wb')
    pickle.dump(submissions, cacheFile)

def readCacheRedditSubmissions(cacheFileName):
    cacheFile = open(cacheFileName, 'rb')
    submissions = pickle.load(cacheFile)
    return submissions

def getRedditSubmissionsFromRedditList(redditList):
    submissions = []

    numTotalSubmissions = len(redditList)
    for currentSubmissionIndex, singleSubmission in enumerate(redditList):
        if type(singleSubmission) is praw.models.Submission:
            newSubmission = RedditSubmission()

            newSubmission.title = singleSubmission.title
            newSubmission.author = singleSubmission.author.name if singleSubmission.author else u'no_author'

            newSubmission.subreddit = singleSubmission.subreddit.url
            newSubmission.subredditTitle = singleSubmission.subreddit.title

            newSubmission.body = singleSubmission.selftext
            newSubmission.bodyUrl = singleSubmission.url

            newSubmission.postUrl = singleSubmission.permalink

            submissions.append(newSubmission)

            print percentageComplete(currentSubmissionIndex, numTotalSubmissions)
        else:
            # TODO: Macoy: Look at https://praw.readthedocs.io/en/latest/getting_started/quick_start.html
            #  very bottom to learn how to enumerate what information a submission can provide
            print('Comment (unsupported): ' + singleSubmission.body[:40] + '...')

    return submissions

def getRedditUserLikedSavedSubmissions(user_name, user_password, client_id, client_secret,
                                       request_limit = 10):
    r = praw.Reddit(client_id = client_id,
        client_secret=client_secret,
        username=user_name,
        password=user_password,
        user_agent=user_agent)

    #r.login(user_name, user_password)

    print '\n\nCommunicating with reddit. This should only take a minute...\n'
    savedLinks = r.user.me().saved(limit=request_limit)
    savedLinks = list(savedLinks)

    likedLinks = r.user.me().upvoted(limit=request_limit)
    likedLinks = list(likedLinks)

    print '\n\nRetrieving your saved submissions. This can take several minutes...\n'
    savedSubmissions = getRedditSubmissionsFromRedditList(savedLinks)
    print '\n\nRetrieving your liked submissions. This can take several minutes...\n'
    likedSubmissions = getRedditSubmissionsFromRedditList(likedLinks)    

    return savedSubmissions + likedSubmissions