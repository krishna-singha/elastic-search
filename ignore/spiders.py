from urllib.request import urlopen
from link_finder import LinkFinder
from general import *

class Spider:
    def __init__(self, project_name, base_url, domain_name):
        self.project_name = project_name
        self.base_url = base_url
        self.domain_name = domain_name
        self.queue_file = f"{project_name}/queue.txt"
        self.crawled_file = f"{project_name}/crawled.txt"
        self.queue = set()
        self.crawled = set()
        self.boot()

    def boot(self):
        create_project_dir(self.project_name)
        create_data_files(self.project_name, self.base_url)
        self.queue = file_to_set(self.queue_file)
        self.crawled = file_to_set(self.crawled_file)

    def crawl_page(self, thread_name, page_url):
        if page_url not in self.crawled:
            print(f"{thread_name} now crawling {page_url}")
            print(f"Queue {len(self.queue)} | Crawled {len(self.crawled)}")
            self.add_links_to_queue(self.gather_links(page_url))
            self.queue.discard(page_url)
            self.crawled.add(page_url)
            self.update_files()

    def gather_links(self, page_url):
        try:
            response = urlopen(page_url)
            if 'text/html' in response.getheader('Content-Type'):
                html_bytes = response.read()
                html_string = html_bytes.decode("utf-8")
                finder = LinkFinder(self.base_url, page_url)
                finder.feed(html_string)
                return finder.page_links()
        except Exception as e:
            print(f"Error crawling {page_url}: {e}")
        return set()

    def add_links_to_queue(self, links):
        for url in links:
            if url in self.queue or url in self.crawled:
                continue
            if self.domain_name not in url:
                continue
            self.queue.add(url)

    def update_files(self):
        set_to_file(self.queue, self.queue_file)
        set_to_file(self.crawled, self.crawled_file)
