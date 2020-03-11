import re
import grequests
import requests
from bs4 import BeautifulSoup

from base import PybLevel, PybLink, PybActivity
from exceptions import InvalidParentLevelException, InvalidTargetException, DuplicateLevelException, InvalidLinkEntryException, NoLinksInScanLevel, greq_excep_handler


class GatherLink(PybLink):
    def __init__(self, text, link):
        super(GatherLink, self).__init__(text, link)


class GatherLevel(PybLevel):
    def __init__(self, html_tag: str, html_attrib: str, html_attrib_val: str):
        super(GatherLevel, self).__init__(html_tag, html_attrib, html_attrib_val)


class Gatherer(PybActivity):
    """
        pyblix.Gatherer is the initialization phase for pyblix.Scanner.

        Create a GatherLevel object that represents the HTML Parent of your link collection.
        This is usually an Index page that contains a list of all your blog posts.

        This GatherLevel can then be passed to the Gatherer that will scan for all your articles/posts.
    """
    _user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:73.0) Gecko/20100101 Firefox/73.0"
    _accept_header = "text/html,application/xhtml+xml,application/xml"
    request_headers = {'User-Agent': _user_agent, 'Accept': _accept_header}

    def __init__(self, domain: str, verify_ssl: bool, article_root_page: str,
                 parent_level: GatherLevel, verbose: bool = False):
        super(Gatherer, self).__init__(verbose, domain, verify_ssl)
        self.article_root_page = article_root_page
        self.identifiable_parent_level = parent_level

        # Add Host field to header, some pages give 500's or other vhosts without Host
        host_header = {'Host': self.domain}
        self.request_headers.update(host_header)

        self.gather_links = []
        if self.verbose:
            print(f"Validating URL: {self.article_root_page}")
        self._validate_url()

        if self.verbose:
            print(f"Validating parent level: {self.identifiable_parent_level}")
        self._validate_parent_level()

    def _validate_url(self):
        with requests.Session() as _sess:
            root_response = _sess.get(url=self.article_root_page,
                                      verify=self.verify_ssl,
                                      headers=self.request_headers)

            if root_response.status_code == 200:
                self.article_root_html = root_response.text
                self.article_root_soup = BeautifulSoup(self.article_root_html, 'html.parser')
            else:
                raise InvalidTargetException

    def _validate_parent_level(self):
        self.parent_level_soup = self.article_root_soup.find(self.identifiable_parent_level.html_tag,
                                                             {
                                                                 self.identifiable_parent_level.html_attrib:
                                                                 self.identifiable_parent_level.html_attrib_val
                                                             })

        try:
            all_links = self.parent_level_soup.find_all("a")
            for link in all_links:
                glink = GatherLink(link.text, link['href'])
                self.gather_links.append(glink)
        except AttributeError:
            raise InvalidParentLevelException

    @property
    def number_of_gather_links(self):
        return len(self.gather_links)


class ScanLevel(PybLevel):
    def __init__(self, html_tag, html_attrib, html_attrib_val):
        super(ScanLevel, self).__init__(html_tag, html_attrib, html_attrib_val)


class Scanner(PybActivity):
    tmp_total_links = 0

    def __init__(self, gatherer: Gatherer, timeout: int = 3):
        self._for_gatherer = gatherer
        v, d, v_s = self._for_gatherer.verbose, self._for_gatherer.domain, self._for_gatherer.verify_ssl
        super(Scanner, self).__init__(v, d, v_s)

        self.all_articles = self._for_gatherer.gather_links

        self.timeout = timeout

        self.scan_levels = []
        self.article_link_dict = {}

    def add_level(self, scan_level: ScanLevel):
        if scan_level not in self.scan_levels:
            self.scan_levels.append(scan_level)
        else:
            raise DuplicateLevelException

    def _create_normalized_link_list(self):
        if self.verbose:
            print("Normalizing the obtained link dictionary")
        self._normalized_link_list = []

        for k in self.article_link_dict.keys():
            # What if the link is still a string and not a list?
            v = self.article_link_dict.get(k)
            if isinstance(v, str) and v not in self._normalized_link_list:
                self._normalized_link_list.append(v)
            elif isinstance(v, list):
                [self._normalized_link_list.append(x) for x in v if x not in self._normalized_link_list]
            else:
                raise InvalidLinkEntryException

        if self.verbose:
            print(f"All Done, we normalized {self.tmp_total_links} links to {len(self._normalized_link_list)} !")

    def collect_links(self):
        if len(self.scan_levels) > 0:
            for article in self.all_articles:
                if self.verbose:
                    print(f"Getting links for article: {article}")
                counter = 0
                with requests.Session() as _sess:
                    article_resp = _sess.get(url=article.link, headers=self._for_gatherer.request_headers,
                                             verify=self.verify_ssl)
                article_body = article_resp.text
                soup = BeautifulSoup(article_body, 'html.parser')
                for scan_level in self.scan_levels:
                    if self.verbose:
                        print(f"Scanning level: {scan_level}")

                    search_frame = soup.find(scan_level.html_tag, {scan_level.html_attrib: scan_level.html_attrib_val})
                    all_links_in_article = search_frame.find_all("a")
                    self.tmp_total_links += len(all_links_in_article)
                    if self.verbose:
                        print(f"We found {len(all_links_in_article)} links.")
                    for link in all_links_in_article:
                        try:
                            link_href = link['href']
                        except KeyError:
                            # no href... ignore it
                            continue

                        if article.text in self.article_link_dict.keys():
                            if isinstance(self.article_link_dict[article.text], str):
                                self.article_link_dict[article.text] = [self.article_link_dict[article.text], link_href]
                            else:
                                self.article_link_dict[article.text].append(link_href)
                        else:
                            self.article_link_dict[article.text] = link_href
            self._create_normalized_link_list()

        else:
            raise NoLinksInScanLevel

    def scan_links(self):
        if self.verbose:
            print("Generating request set")
        request_set = (grequests.get(url=u,
                                     headers=self._for_gatherer.request_headers,
                                     verify=self.verify_ssl,
                                     timeout=self.timeout)
                       for u in self._normalized_link_list)

        if self.verbose:
            print("Firing requests and waiting for them to come back.")
        all_results = grequests.map(request_set, exception_handler=greq_excep_handler)

        print(all_results)