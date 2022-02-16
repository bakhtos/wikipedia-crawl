import argparse
import wikipedia as wiki
import pickle


def wiki_crawler(start_page=None, max_links=None, limit=False):
    ''' Crawl wikipedia pages' links and categories.
    Parameters:
    str start_page: name of the page to crawl
    int max_links: threshold of pages to crawl (note: it is NOT an absolute
        maximum amount of pages to crawl, see comments in the end of the while loop)
    bool limit: whether or not to use the rate limiter provided by wiki package
    Returns: None
    Side effects: saves crawled links and categories to pickled dictionaries
        in the current working directory
    '''
    
    # Deal with default parameters
    if start_page is None: start_page = wiki.random()
    else:
        try: wiki.page(start_page)
        except (wiki.exceptions.PageError, wiki.exceptions.DisambiguationError):
            raise ValueError("The provided page could not be found")
    if max_links is None: max_links = 5

    # Set limiting on/off
    wiki.set_rate_limiting(limit)

    # Initialize the crawling queue with given page
    crawl_queue = set()
    crawl_queue.add(start_page)

    # Initialize the set of all found pages
    all_links = set()
    all_links.add(start_page)

    # Initialize structures for pages' caterogies, links, failed searches
    categories = dict()
    links = dict()
    failed_pages = set()

    # Flag for the limit of crawled pages
    limit_reached = False

    # Crawl the queue
    while len(crawl_queue) != 0:
        # Pages found after crawling  the current queue
        current_crawl = set()

        # Crawl pages that are currently in the queue
        for current_page in crawl_queue:
            print("Crawling:",current_page+"...")

            # Get the page with wikipedia package, sometimes it fails even
            # though we are using the names of pages the package itself return,
            # such pages are skipped
            try:
                wiki_page = wiki.page(current_page)
            except (wiki.exceptions.PageError, wiki.exceptions.DisambiguationError):
                # Save page that failed to crawl for later, skip to next page
                failed_pages.add(current_page)
                print("\t", current_page, "failed!")
                continue

            # Get all pages linked from crawled page, remove links to 
            # failed pages
            get_links = set(wiki_page.links) - failed_pages

            # Get the categories of the page
            get_categories = set(wiki_page.categories)
            categories[current_page] = get_categories
            if not limit_reached:
                # Save all found pages to current page's outgoing links,
                # add all the found pages to be crawled, 
                # add all the found links to sat of all links
                links[current_page] = get_links
                current_crawl.update(get_links)
                all_links.update(get_links)
            else:
                # If limit of pages is reached, save only links to 
                # pages that already been found, do not add new pages
                # to crawl
                links[current_page] = all_links.intersection(get_links)
            # Check if limit has been reached
            # NOTE: since we first get all the links from the page, add them
            # to data, and only then check the limit, if there were already 95
            # crawled pages with the limit of 100, and the current crawled page
            # has 50 links, the total amount of pages could be 145 (maximum),
            # if all of the 50 links are new (ie 100 is not an absolute limit)
            limit_reached = len(all_links) > max_links

        # Update the queue to the newly found pages
        crawl_queue = current_crawl

    # Serialize the links dictionary
    with open("links.pickle", 'wb') as f:
        pickle.dump(links, f)
    # Serialize the categories dictionary
    with open("categories.pickle", 'wb') as f:
        pickle.dump(categories, f)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="crawl Wikipedia page links")
    parser.add_argument("--page", "-p", help="starting page for the crawling"
                        " (defaults to random)")
    parser.add_argument("--links", "-l", help="maximum amount of pages to crawl"
                        " (defaults to 5)", type=int)
    parser.add_argument("--limit", help="turn on rate-limiting of requests",
                        action="store_true")
    args = parser.parse_args()
    wiki_crawler(args.page, args.links, args.limit)

