import praw
import re

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
    
def getRedditUserLikedSavedImages(user_name, user_password, request_limit = 100, silentGet = False, extractURLsFromComments = False):
    user_agent = "PythonStuff: Likes grabber 1.0 by /u/makuto9"
    
    fSaved = open("savedURLS.txt", 'w')
    fLiked = open("likedURLS.txt", 'w')
    
    r = praw.Reddit(user_agent=user_agent)

    r.login(user_name, user_password)

    savedLinks = r.user.get_saved(limit=request_limit)
    savedLinks = list(savedLinks)

    likedLinks = r.user.get_upvoted(limit=request_limit)
    likedLinks = list(likedLinks)

    writeOutAllLinksFromRedditList(savedLinks, fSaved, silent = silentGet, extractLinksFromComments = extractURLsFromComments)
    writeOutAllLinksFromRedditList(likedLinks, fLiked, silent = silentGet, extractLinksFromComments = extractURLsFromComments)
    
    fSaved.close()
    fLiked.close()
    return
