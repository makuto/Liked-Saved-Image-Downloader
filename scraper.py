# -*- coding: utf-8 -*-

import praw
from submission import Submission 

user_agent = 'Python Script: v2.0: Reddit Liked Saved Image Downloader (by /u/makuto9)'

# Helper function. Print percentage complete
def percentageComplete(currentItem, numItems):
    if numItems:
        return str(int(((float(currentItem + 1) / float(numItems)) * 100))) + '%'

    return 'Invalid'

def getSubmissionsFromRedditList(redditList):
    submissions = []

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
    savedSubmissions = getSubmissionsFromRedditList(savedLinks)
    print '\n\nRetrieving your liked submissions. This can take several minutes...\n'
    likedSubmissions = getSubmissionsFromRedditList(likedLinks)    

    return savedSubmissions + likedSubmissions