# -*- coding: utf-8 -*-

import praw
from submission import Submission 

#import pprint

user_agent = 'Python Script: v2.0: Reddit Liked Saved Image Downloader (by /u/makuto9)'

# Helper function. Print percentage complete
def percentageComplete(currentItem, numItems):
    if numItems:
        return str(int(((float(currentItem + 1) / float(numItems)) * 100))) + '%'

    return 'Invalid'

def getSubmissionsFromRedditList(redditList):
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
                                       request_limit = 10, saveLiked = True, saveSaved = True):
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
        savedSubmissions, savedComments = getSubmissionsFromRedditList(savedLinks) 
 
    likedSubmissions = []
    likedComments = []
    if saveLiked: 
        print('\n\nRetrieving your liked submissions. This can take several minutes...\n') 
        likedSubmissions, likedComments = getSubmissionsFromRedditList(likedLinks)     
 
    submissions = savedSubmissions + likedSubmissions
    # I don't think you can ever have liked comments, but I'm including it anyways
    comments = savedComments + likedComments

    return submissions, comments