import pytumblr
from submission import Submission 
from zlib import crc32

def getTumblrUserLikedSubmissions(clientId, clientSecret, tokenId, tokenSecret,
	likeRequestLimit = 100):
	tumblrClient = pytumblr.TumblrRestClient(
		clientId, clientSecret, tokenId, tokenSecret)

	# This is an annoying limit the api seems to impose
	POSTS_PER_PAGE = 50

	oldestPageTimestamp = 0
	totalRequests = 0
	submissions = []

	while totalRequests < likeRequestLimit:
		if oldestPageTimestamp:
			tumblrLikes = tumblrClient.likes(**{'limit':POSTS_PER_PAGE, 
			                                    'offset':totalRequests})
		else:
			tumblrLikes = tumblrClient.likes(**{'limit':POSTS_PER_PAGE})

		numPostsThisPage = len(tumblrLikes['liked_posts'])

		if not numPostsThisPage:
			break;

		print(str(numPostsThisPage) 
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
						newSubmission.title = unicode(crc32(post['short_url'])) + u'_' + unicode(photoIndex)
					else:
						newSubmission.title = unicode(crc32(post['short_url']))

					newSubmission.author = post['blog']['name']

					newSubmission.subreddit = post['blog']['url']
					newSubmission.subredditTitle = post['blog']['title'] + '_Tumblr'

					newSubmission.body = post['caption']
					newSubmission.bodyUrl = photo['original_size']['url']

					newSubmission.postUrl = post['short_url']

					submissions.append(newSubmission)

			else:
				print('Skipped ' + post['short_url'] + ' (does not have images)')

		oldestPageTimestamp = tumblrLikes['liked_posts'][-1]['liked_timestamp']

		# If we didn't get a full page's worth of posts, we're on the last page
		# Sometimes pages don't have POSTS_PER_PAGE, they're a little under
		RANDOM_PAGE_TOLERANCE = 10
		if numPostsThisPage < POSTS_PER_PAGE - RANDOM_PAGE_TOLERANCE:
			break

		totalRequests += numPostsThisPage

	return submissions
