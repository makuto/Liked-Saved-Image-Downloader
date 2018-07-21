import pytumblr
import logger
from submission import Submission
from crcUtils import signedCrc32
from builtins import str

def getTumblrUserLikedSubmissions(clientId, clientSecret, tokenId, tokenSecret,
	likeRequestLimit = 100, requestOnlyNewCache = None):
	tumblrClient = pytumblr.TumblrRestClient(
		clientId, clientSecret, tokenId, tokenSecret)

	# This is an annoying limit the api seems to impose
	POSTS_PER_PAGE = 50

	oldestPageTimestamp = 0
	totalRequests = 0
	submissions = []

	foundOldSubmission = False

	while totalRequests < likeRequestLimit:
		if oldestPageTimestamp:
			tumblrLikes = tumblrClient.likes(**{'limit':POSTS_PER_PAGE, 
			                                    'offset':totalRequests})
		else:
			tumblrLikes = tumblrClient.likes(**{'limit':POSTS_PER_PAGE})

		numPostsThisPage = len(tumblrLikes['liked_posts'])

		if not numPostsThisPage:
			break;

		logger.log(str(numPostsThisPage) 
			+ ' Tumblr likes requested. Total likes: '
			+ str(tumblrLikes['liked_count']))

		for postIndex, post in reversed(list(enumerate(tumblrLikes['liked_posts']))):
			if 'photos' in post:
				for photoIndex, photo in enumerate(post['photos']):
					newSubmission = Submission()

					newSubmission.source = u'Tumblr'

					# Tumblr submissions don't have titles, so make one
					# This'll look ugly in the file browser, unfortunately
					if len(post['photos']) > 1:
						newSubmission.title = str(signedCrc32(post['short_url'].encode()))
						newSubmission.title += u'_'
						newSubmission.title += str(photoIndex)
					else:
						newSubmission.title = str(signedCrc32(post['short_url'].encode()))

					"""logger.log(post)
					return"""
					newSubmission.author = post['blog_name']

					newSubmission.subreddit = post['short_url']
					newSubmission.subredditTitle = post['blog_name'] + '_Tumblr'

					newSubmission.body = post['caption']
					newSubmission.bodyUrl = photo['original_size']['url']

					newSubmission.postUrl = post['short_url']

					submissions.append(newSubmission)

					if (requestOnlyNewCache 
						and requestOnlyNewCache[0] 
						and newSubmission.postUrl == requestOnlyNewCache[0].postUrl):
						logger.log('Found early out point after ' + str(len(submissions)) + ' new submissions.'
		                      ' If you e.g. changed your total requests value and want to go deeper, set'
		                      ' Tumblr_Try_Request_Only_New to False in your settings.txt')
						foundOldSubmission = True
						break

			else:
				logger.log('Skipped ' + post['short_url'] + ' (does not have images)')

			if foundOldSubmission:
				break

		if foundOldSubmission:
			break

		oldestPageTimestamp = tumblrLikes['liked_posts'][-1]['liked_timestamp']

		# If we didn't get a full page's worth of posts, we're on the last page
		# Sometimes pages don't have POSTS_PER_PAGE, they're a little under
		RANDOM_PAGE_TOLERANCE = 10
		if numPostsThisPage < POSTS_PER_PAGE - RANDOM_PAGE_TOLERANCE:
			break

		totalRequests += numPostsThisPage

	newEarlyOut = submissions[0] if len(submissions) else None
	return submissions, newEarlyOut
