# -*- coding: utf-8 -*-

import praw
import re
import pickle

user_agent = 'Python Script: v2.0: Reddit Liked Saved Image Downloader (by /u/makuto9)'

# Helper function. Print percentage complete
def percentageComplete(currentItem, numItems):
    if numItems:
        return str(int(((float(currentItem + 1) / float(numItems)) * 100))) + '%'

    return 'Invalid'

def writeOutAllLinksFromRedditList(redditList, f, silent=False, extractLinksFromComments = False):
    for singleSubmission in redditList:
        if type(singleSubmission) is praw.objects.Submission:
            f.write(singleSubmission.url + '\n')
            if not silent:
                print singleSubmission.url
        else:
            if extractLinksFromComments:
                #use regex copied from internet to extract urls from comments (use r' so Python doesn't escape sequences)
                http_regex = r'_^(?:(?:https?|ftp)://)(?:\S+(?::\S*)?@)?(?:(?!10(?:\.\d{1,3}){3})(?!127(?:\.\d{1,3}){3})(?!169\.254(?:\.\d{1,3}){2})(?!192\.168(?:\.\d{1,3}){2})(?!172\.(?:1[6-9]|2\d|3[0-1])(?:\.\d{1,3}){2})(?:[1-9]\d?|1\d\d|2[01]\d|22[0-3])(?:\.(?:1?\d{1,2}|2[0-4]\d|25[0-5])){2}(?:\.(?:[1-9]\d?|1\d\d|2[0-4]\d|25[0-4]))|(?:(?:[a-z\x{00a1}-\x{ffff}0-9]+-?)*[a-z\x{00a1}-\x{ffff}0-9]+)(?:\.(?:[a-z\x{00a1}-\x{ffff}0-9]+-?)*[a-z\x{00a1}-\x{ffff}0-9]+)*(?:\.(?:[a-z\x{00a1}-\x{ffff}]{2,})))(?::\d{2,5})?(?:/[^\s]*)?$_iuS'
                old_http_regex = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
                commentURL = re.findall(http_regex, singleSubmission.body)
                for commentLink in commentURL:
                    f.write(commentLink + '\n')
                    if not silent:
                        print 'Comment link (extracted via regex): ' + commentLink
    
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

def writeOutRedditSubmissionsAsXML(redditList, file, silent = False, extractLinksFromComments = False):
    for submission in redditList:
        file.write(u'<submission>\n' + submission.getXML() + u'</submission>\n')
        #file.write(u'<submission>\n' + submission.getXML().encode('utf-8', 'replace') + u'</submission>\n')

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
            # Macoy: Look at https://praw.readthedocs.io/en/latest/getting_started/quick_start.html
            #  very bottom to learn how to enumerate what information a submission can provide
            print('Comment (unsupported): ' + singleSubmission.body[:40] + '...')

    return submissions

def getRedditUserLikedSavedImages(user_name, user_password, client_id, client_secret,
                                  request_limit = 100, silentGet = False, 
                                  extractURLsFromComments = False):
    fSaved = open('savedURLS.txt', 'w')
    fLiked = open('likedURLS.txt', 'w')
    
    r = praw.Reddit(user_agent=user_agent)

    #r.login(user_name, user_password)

    savedLinks = r.user.me().saved(limit=request_limit)
    savedLinks = list(savedLinks)

    likedLinks = r.user.me().upvoted(limit=request_limit)
    likedLinks = list(likedLinks)

    writeOutAllLinksFromRedditList(savedLinks, fSaved, 
        silent = silentGet, extractLinksFromComments = extractURLsFromComments)
    writeOutAllLinksFromRedditList(likedLinks, fLiked, 
        silent = silentGet, extractLinksFromComments = extractURLsFromComments)
    
    fSaved.close()
    fLiked.close()
    return

def getRedditUserLikedSavedSubmissions(user_name, user_password, client_id, client_secret,
                                       request_limit = 10, silentGet = False, 
                                       extractURLsFromComments = False):
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