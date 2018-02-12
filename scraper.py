# -*- coding: utf-8 -*-

import praw
import submission
from submission import Submission 

#import pprint

user_agent = 'Python Script: v2.0: Reddit Liked Saved Image Downloader (by /u/makuto9)'

# Helper function. Print percentage complete
def percentageComplete(currentItem, numItems):
    if numItems:
        return str(int(((float(currentItem + 1) / float(numItems)) * 100))) + '%'

    return 'Invalid'

def getSubmissionsFromRedditList(redditList, earlyOutPoint = None):
    submissions = []
    comments = []

    numTotalSubmissions = len(redditList)
    for currentSubmissionIndex, singleSubmission in enumerate(redditList):

        if type(singleSubmission) is praw.models.Submission:
            newSubmission = Submission()

            newSubmission.source = u'reddit'

            newSubmission.title = singleSubmission.title
            newSubmission.author = singleSubmission.author.name if singleSubmission.author else u'no_author'

            newSubmission.subreddit = singleSubmission.subreddit.url
            newSubmission.subredditTitle = singleSubmission.subreddit.title

            newSubmission.body = singleSubmission.selftext
            newSubmission.bodyUrl = singleSubmission.url

            newSubmission.postUrl = singleSubmission.permalink

            submissions.append(newSubmission)

            print(percentageComplete(currentSubmissionIndex, numTotalSubmissions))

            # Check to see if we've already downloaded this submission; if so, early out
            if (earlyOutPoint 
                and earlyOutPoint[0] 
                and newSubmission.postUrl == earlyOutPoint[0].postUrl):
                print('Found early out point after ' + str(len(submissions)) + ' new submissions.'
                      ' If you e.g. changed your total requests value and want to go deeper, set'
                      ' Reddit_Try_Request_Only_New to False in your settings.txt')
                break
        else:
            # I looked at https://praw.readthedocs.io/en/latest/getting_started/quick_start.html
            #  very bottom to learn how to enumerate what information a submission can provide
            # print(singleSubmission.body)
            # pprint.pprint(vars(singleSubmission))
            newSubmission = Submission()

            newSubmission.source = u'reddit'

            newSubmission.title = u'Comment on ' + singleSubmission.link_title
            newSubmission.author = singleSubmission.author.name if singleSubmission.author else u'no_author'

            newSubmission.subreddit = singleSubmission.subreddit.url
            newSubmission.subredditTitle = singleSubmission.subreddit.title

            newSubmission.body = singleSubmission.body
            newSubmission.bodyUrl = singleSubmission.permalink

            newSubmission.postUrl = singleSubmission.link_permalink

            comments.append(newSubmission)

    return submissions, comments

def getRedditUserLikedSavedSubmissions(user_name, user_password, client_id, client_secret,
                                       request_limit = 10, saveLiked = True, saveSaved = True,
                                       earlyOutPointSaved = None, earlyOutPointLiked = None):
    r = praw.Reddit(client_id = client_id,
        client_secret=client_secret,
        username=user_name,
        password=user_password,
        user_agent=user_agent)

    print('\n\nCommunicating with reddit. This should only take a minute...\n')

    savedLinks = None 
    if saveSaved: 
        print('\tGetting saved links...') 
        savedLinks = r.user.me().saved(limit=request_limit) 
        savedLinks = list(savedLinks) 
 
    likedLinks = None 
    if saveLiked: 
        print('\tGetting liked links...') 
        likedLinks = r.user.me().upvoted(limit=request_limit) 
        likedLinks = list(likedLinks)

    savedSubmissions = []
    savedComments = []
    if saveSaved: 
        print('\n\nRetrieving your saved submissions. This can take several minutes...\n') 
        savedSubmissions, savedComments = getSubmissionsFromRedditList(savedLinks, earlyOutPointSaved) 
 
    likedSubmissions = []
    likedComments = []
    if saveLiked: 
        print('\n\nRetrieving your liked submissions. This can take several minutes...\n') 
        likedSubmissions, likedComments = getSubmissionsFromRedditList(likedLinks, earlyOutPointLiked)     
 
    submissions = savedSubmissions + likedSubmissions
    # I don't think you can ever have liked comments, but I'm including it anyways
    comments = savedComments + likedComments

    newEarlyOutSaved = savedSubmissions[0] if len(savedSubmissions) else None
    newEarlyOutLiked = likedSubmissions[0] if len(likedSubmissions) else None
    return submissions, comments, (newEarlyOutSaved, newEarlyOutLiked)