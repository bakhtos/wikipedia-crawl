import argparse
import wikipedia as wiki
import pickle

STOP_CATEGORIES = set([
'All articles with dead external links', 'All pages needing factual verification', 'Articles with BIBSYS identifiers', 'Articles with BNE identifiers', 'Articles with BNF identifiers', 'Articles with CINII identifiers', 'Articles with Curlie links', 'Articles with GND identifiers', 'Articles with ISNI identifiers', 'Articles with LCCN identifiers', 'Articles with MusicBrainz identifiers', 'Articles with NDL identifiers', 'Articles with NKC identifiers', 'Articles with NLA identifiers', 'Articles with NLI identifiers', 'Articles with NSK identifiers', 'Articles with PWN identifiers', 'Articles with SUDOC identifiers', 'Articles with Trove identifiers', 'Articles with VIAF identifiers', 'Articles with WORLDCATID identifiers'
])

def wiki_crawler(start_page=None, max_links=None, limit=False):
    
    if start_page is None: start_page = wiki.random()
    if max_links is None: max_links = 500

    wiki.set_rate_limiting(limit)

    crawl_queue = set()
    crawl_queue.add(start_page)
    all_links = set()
    all_links.add(start_page)
    categories = dict()
    links = dict()
    failed_pages = set()
    limit_reached = False
    while len(crawl_queue) != 0:
        print(crawl_queue)
        current_crawl = set()
        for current_page in crawl_queue:
            print(current_page)
            try:
                wiki_page = wiki.page(current_page)
            except (wiki.exceptions.PageError, wiki.exceptions.DisambiguationError):
                failed_pages.add(current_page)
                continue
            get_links = set(wiki_page.links) - failed_pages
            get_categories = set(wiki_page.categories)
            get_categories -= STOP_CATEGORIES
            categories[current_page] = get_categories
            if not limit_reached:
                links[current_page] = get_links
                current_crawl.update(get_links)
                all_links.update(get_links)
            else:
                links[current_page] = all_links.intersection(get_links)
            limit_reached = len(all_links) > max_links
        crawl_queue = current_crawl

    with open("links.pickle", 'wb') as f:
        pickle.dump(links, f)
    with open("categories.pickle", 'wb') as f:
        pickle.dump(categories, f)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="crawl Wikipedia page links")
    parser.add_argument("--page", "-p", help="starting page for the crawling"
                        " (defaults to random)")
    parser.add_argument("--links", "-l", help="maximum amount of pages to crawl"
                        " (defaults to 500)", type=int)
    parser.add_argument("--limit", help="turn on rate-limiting of requests",
                        action="store_true")
    args = parser.parse_args()
    print(args)
    wiki_crawler(args.page, args.links, args.limit)

