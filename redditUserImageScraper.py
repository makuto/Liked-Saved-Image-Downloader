import scraper
import imageSaver

# If True, don't actually download the images - just pretend to
SHOULD_SOFT_RETRIEVE = True

#If True, reddit scraper won't print URLs to console
SILENT_GET = False

#Total requests to reddit (actual results may vary)
TOTAL_REQUESTS = 500

#May result in shitty URLs (regex is tough)
URLS_FROM_COMMENTS = False

USERNAME = 'YOUR_USERNAME_HERE (NO /U/)'
PASSWORD = 'YOUR_PASSWORD_HERE'

def main():
    #Talk to reddit and fill .txt files with liked and saved URLS
    scraper.getRedditUserLikedSavedImages(USERNAME, PASSWORD, request_limit = TOTAL_REQUESTS, silentGet = SILENT_GET, extractURLsFromComments = URLS_FROM_COMMENTS)

    #Parse those .txt files for image URLS and download them (if !SHOULD_SOFT_RETRIEVE)
    imageSaver.saveAllImages(soft_retrieve_imgs = SHOULD_SOFT_RETRIEVE)
    
main()
