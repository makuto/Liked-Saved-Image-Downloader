from pixivpy3 import *
from submission import Submission
import logger

# Note that this does NOT set the download URL, and won't set title to be unique for albums
def fillPixivSubmission(illustration, submissionToFill):
    submissionToFill.source = u'Pixiv'

    submissionToFill.title = illustration.title

    submissionToFill.author = illustration.user.name

    submissionToFill.subreddit = 'https://www.pixiv.net/en/users/{}'.format(illustration.user.id)
    submissionToFill.subredditTitle = illustration.user.name + '_Pixiv'

    submissionToFill.body = illustration.caption

    submissionToFill.postUrl = 'https://www.pixiv.net/en/artworks/{}'.format(illustration.id)

def pixivSubmissionsFromJson(bookmarks):
    submissions = []
    for illustration in bookmarks.illusts:
        if illustration.type not in ['illust', 'manga']:
            # TODO: Add more format support
            logger.log("Skipping " + illustration.type)
            continue

        # Album
        if illustration.meta_pages:
            imageIndex = 0
            for imagePage in illustration.meta_pages:
                newSubmission = Submission()
                fillPixivSubmission(illustration, newSubmission)

                newSubmission.title = '{}_{}'.format(newSubmission.title, imageIndex)
                newSubmission.bodyUrl = imagePage.image_urls.original
                imageIndex += 1

                submissions.append(newSubmission)

        # Single image
        elif illustration.meta_single_page:
            newSubmission = Submission()
            fillPixivSubmission(illustration, newSubmission)

            # The image that will be downloaded
            newSubmission.bodyUrl = illustration.meta_single_page.original_image_url

            submissions.append(newSubmission)

    logger.log("Got {} Pixiv bookmarks".format(len(submissions)))
    return submissions

def getPixivUserBookmarkedSubmissions(username, password,
                                      requestOnlyNewCache = None,
                                      requestOnlyNewPrivateCache = None):
    logger.log("Communicating with Pixiv...")
    pixivApi = AppPixivAPI()
    # TODO: Use refresh token? Right now, login will have to happen once per hour, so I'll just
    # login every time instead and toss the complexity
    pixivLoginJson = pixivApi.login(username, password)
    pixivUserId = int(pixivLoginJson.response.user.id)

    firstPublicBookmark = None
    firstPrivateBookmark = None

    submissions = []
    for visibilityCachePair in [('public', requestOnlyNewCache), ('private', requestOnlyNewPrivateCache)]:
        pageNum = 1
        bookmarks = pixivApi.user_bookmarks_illust(pixivUserId, restrict=visibilityCachePair[0])
        while bookmarks:
            logger.log("Page {}".format(pageNum))
            pageNum += 1

            thisPageSubmissions = pixivSubmissionsFromJson(bookmarks)
            earlyOut = False
            for thisPageSubmission in thisPageSubmissions:
                # Set early out points for next run
                if not firstPublicBookmark and visibilityCachePair[0] == 'public':
                    firstPublicBookmark = thisPageSubmission
                elif not firstPrivateBookmark and visibilityCachePair[0] == 'private':
                    firstPrivateBookmark = thisPageSubmission

                if (visibilityCachePair[1]
                    and thisPageSubmission.postUrl == visibilityCachePair[1][0].postUrl):
                    logger.log("Found early out point for {} bookmarks after {} submissions"
                               .format(visibilityCachePair[0], len(submissions)))
                    earlyOut = True
                    break

                submissions.append(thisPageSubmission)

            if earlyOut:
                break
            if 'next_url' not in bookmarks:
                break
            nextUrlParsed = pixivApi.parse_qs(bookmarks.next_url)
            if not nextUrlParsed:
                break
            nextPageBookmarks = nextUrlParsed['max_bookmark_id']
            bookmarks = pixivApi.user_bookmarks_illust(pixivUserId,
                                                       restrict=visibilityCachePair[0],
                                                       max_bookmark_id=nextPageBookmarks)

    logger.log("Pixiv returned {} submissions".format(len(submissions)))
    return (submissions, (firstPublicBookmark, firstPrivateBookmark))

if __name__ == '__main__':
    submissions = getPixivUserBookmarkedSubmissions('your username', 'your password')
    for pixivSubmission in submissions:
        print('{}\n\t{}'.format(pixivSubmission.title, pixivSubmission.bodyUrl))
