import copy

# import re
import urllib.parse

from http_headers import FIREFOX_LINUX

from exceptions import (
    DuplicateLevelException,
    InvalidLinkEntryException,
    InvalidParentLevelException,
    InvalidTargetException,
    NoLinksInScanLevel,
    UnknownDictExceptionError,
)
from urllib.parse import urlparse

import grequests
import requests
from bs4 import BeautifulSoup

from base import PybActivity, PybLevel, PybLink


class GatherLink(PybLink):
    def __init__(self, text, link):
        super(GatherLink, self).__init__(text, link)


class GatherLevel(PybLevel):
    def __init__(self, html_tag: str, html_attrib: str, html_attrib_val: str):
        super(GatherLevel, self).__init__(html_tag, html_attrib, html_attrib_val)


class Gatherer(PybActivity):
    """
        pyblix.Gatherer is the initialization phase for pyblix.Scanner.

        Create a GatherLevel object that represents the HTML Parent of your link
        collection. This is usually an Index page that contains a list of all your
        blog posts.

        This GatherLevel can then be passed to the Gatherer that will scan for all
        your articles/posts.
    """

    _user_agent = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:73.0) Gecko/20100101 Firefox/73.0"
    )
    request_headers = FIREFOX_LINUX

    def __init__(
        self,
        domain: str,
        verify_ssl: bool,
        article_root_page: str,
        parent_level: GatherLevel,
        verbose: bool = False,
    ):
        super(Gatherer, self).__init__(verbose, domain, verify_ssl)
        self.article_root_page = article_root_page
        self.identifiable_parent_level = parent_level

        self.gather_links = []
        if self.verbose:
            print(f"Validating URL: {self.article_root_page}")
        self._validate_url()

        if self.verbose:
            print(f"Validating parent level: {self.identifiable_parent_level}")
        self._validate_parent_level()

    def _validate_url(self):
        with requests.Session() as _sess:
            root_response = _sess.get(
                url=self.article_root_page,
                verify=self.verify_ssl,
                headers=self.request_headers,
            )

            if root_response.status_code == 200:
                self.article_root_html = root_response.text
                self.article_root_soup = BeautifulSoup(
                    self.article_root_html, "html.parser"
                )
            else:
                raise InvalidTargetException

    def _validate_parent_level(self):
        html_attrib = self.identifiable_parent_level.html_attrib
        html_attrib_val = self.identifiable_parent_level.html_attrib_val
        self.parent_level_soup = self.article_root_soup.find(
            self.identifiable_parent_level.html_tag, {html_attrib: html_attrib_val},
        )

        try:
            all_links = self.parent_level_soup.find_all("a")
            for link in all_links:
                glink = GatherLink(link.text, link["href"])
                self.gather_links.append(glink)
        except AttributeError:
            raise InvalidParentLevelException

    @property
    def number_of_gather_links(self):
        return len(self.gather_links)


class ScanLevel(PybLevel):
    def __init__(self, html_tag, html_attrib, html_attrib_val):
        super(ScanLevel, self).__init__(html_tag, html_attrib, html_attrib_val)


class ScanResult(object):
    def __init__(self, parent_text, parent_link):
        self.parent_text = parent_text
        self.parent_link = parent_link

        self.scan_link = ""

        self.status_code = 0
        self.threw_exception = False
        self.result_text = ""
        self.scan_done = False

    def set_scan_link(self, link):
        self.scan_link = link

    def set_result_by_exception(self, excep):
        exception_readable_dict = {
            requests.exceptions.SSLError: "ERR: SSL Error",
            # TODO: Maybe find a way to clean these up? re?
            requests.exceptions.InvalidURL: "ERR: URL Invalid",
            requests.exceptions.ConnectionError: "ERR: Couldn't connect",
            TypeError: "ERR: Unreadable response",  # Lol wth
            requests.exceptions.ConnectTimeout: "ERR: Timed out",
            requests.exceptions.ReadTimeout: "ERR: Read timed out",
        }

        # Response object will be none so we need to add it to dict here
        try:
            self.threw_exception = True
            self.result_text = exception_readable_dict[type(excep)]
            self.scan_done = True
        except KeyError as ex:
            print(ex)
            raise UnknownDictExceptionError

    def set_result_by_status_code(self, status_code, redir_link=""):
        response_code_readable_dict = {
            200: "OK: All Good!",
            201: "OK: API Created response (?)",
            202: "OK: Accepted",
            301: "WRN: Moved permanently to {}",
            302: "WRN: Redirected to {}",
            400: "ERR: Bad Request",
            401: "ERR: Unauthorized",
            403: "ERR: Forbidden",
            404: "ERR: Not Found",
            405: "ERR: Get not allowed (?)",
            406: "ERR: Unacceptable request",
            429: "CRIT: Too many requests you filthy animal",
            500: "ERR: Internal Server Error",
            502: "ERR: Bad Gateway",
            503: "ERR: Service Unavailable",
        }

        self.status_code = status_code
        self.result_text = response_code_readable_dict[status_code].format(redir_link)
        self.scan_done = True


class Scanner(PybActivity):
    tmp_total_links = 0

    def __init__(self, gatherer: Gatherer, timeout: int = 3):
        self._for_gatherer = gatherer
        v, d, v_s = (
            self._for_gatherer.verbose,
            self._for_gatherer.domain,
            self._for_gatherer.verify_ssl,
        )
        super(Scanner, self).__init__(v, d, v_s)

        self.all_articles = self._for_gatherer.gather_links

        self.timeout = timeout

        self.scan_levels = []
        self.article_link_dict = {}
        self._all_results = []

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
                [
                    self._normalized_link_list.append(x)
                    for x in v
                    if x not in self._normalized_link_list
                ]
            else:
                raise InvalidLinkEntryException

        if self.verbose:
            print(
                f"Done normalizing, we reduced {self.tmp_total_links} links to"
                f" {len(self._normalized_link_list)} !"
            )

        if self.verbose:
            print("Cleaning up links we can't query")

        # clean copy
        clean_list = []
        # \u2026 grmblgrmbl...

        [
            clean_list.append(entry.replace("\u2026", ""))
            for entry in self._normalized_link_list
            if (entry[:4] == "http" or entry[:5] == "https")
            and "//localhost" not in entry
        ]
        self._normalized_link_list = copy.deepcopy(clean_list)

        if self.verbose:
            print(f"{len(self._normalized_link_list)} links left after cleaning!")

    def handle_frame(self, search_frame, article, scan_result: ScanResult):
        try:
            all_links_in_article = search_frame.find_all("a")
        except AttributeError:
            if self.verbose:
                print(f"Dropping {article.text} because it contains no links.")
            all_links_in_article = []
        self.tmp_total_links += len(all_links_in_article)
        if self.verbose:
            print(f"We found {len(all_links_in_article)} links.")
        for link in all_links_in_article:
            try:
                link_href = urllib.parse.unquote(link["href"])
                if link_href[-1:] in ["?", "\u2026", "#"]:
                    link_href = link_href[:-1]
            except KeyError:
                # no href... ignore it
                continue

            tmp_scan_result = copy.deepcopy(scan_result)
            tmp_scan_result.set_scan_link(link_href)
            self._all_results.append(tmp_scan_result)

            if article.text in self.article_link_dict.keys():

                if isinstance(self.article_link_dict[article.text], str):
                    self.article_link_dict[article.text] = [
                        self.article_link_dict[article.text],
                        link_href,
                    ]
                else:
                    self.article_link_dict[article.text].append(link_href)
            else:
                self.article_link_dict[article.text] = link_href

    def collect_links(self):
        if len(self.scan_levels) > 0:
            for article in self.all_articles:
                if self.verbose:
                    print(f"Getting links for article: {article}")

                s = ScanResult(article.text, article.link)
                with requests.Session() as _sess:
                    article_resp = _sess.get(
                        url=article.link,
                        headers=self._for_gatherer.request_headers,
                        verify=self.verify_ssl,
                    )
                article_body = article_resp.text
                soup = BeautifulSoup(article_body, "html.parser")
                for scan_level in self.scan_levels:

                    count_helper = soup.find_all(
                        scan_level.html_tag,
                        {scan_level.html_attrib: scan_level.html_attrib_val},
                    )

                    if len(count_helper) > 0:
                        for frame in count_helper:
                            self.handle_frame(frame, article, s)
                    else:
                        search_frame = soup.find(
                            scan_level.html_tag,
                            {scan_level.html_attrib: scan_level.html_attrib_val},
                        )
                        self.handle_frame(search_frame, article, s)

            self._create_normalized_link_list()

        else:
            raise NoLinksInScanLevel

    def link_iterator(self):
        for u in self._normalized_link_list:
            yield grequests.get(
                url=u,
                headers=self._for_gatherer.request_headers,
                verify=self.verify_ssl,
                timeout=self.timeout,
            )

    def scan_links(self):
        if self.verbose:
            print("Generating request set")

        request_set = (u for u in self.link_iterator())

        print("Firing requests and waiting for them to come back.")
        all_results = grequests.map(
            request_set, exception_handler=self.request_exception_handler
        )

        for result in all_results:
            if result is not None:
                # VERY Interesting :-)
                hist = result.history
                if len(hist) > 0:
                    # Where does this link occur in our scan results?
                    indices = [
                        i
                        for i, x in enumerate(self._all_results)
                        if x.scan_link == urllib.parse.unquote(hist[0].url)
                    ]

                    for idx in indices:
                        self._all_results[idx].set_result_by_status_code(
                            hist[0].status_code, urllib.parse.unquote(result.url)
                        )
                else:
                    indices = [
                        i
                        for i, x in enumerate(self._all_results)
                        if x.scan_link == urllib.parse.unquote(result.url)
                    ]
                    for idx in indices:
                        self._all_results[idx].set_result_by_status_code(
                            result.status_code, urllib.parse.unquote(result.url)
                        )

    def request_exception_handler(self, request, exception):
        exception_readable_dict = {
            requests.exceptions.SSLError: "ERR: SSL Error",
            # TODO: Maybe find a way to clean these up? re?
            requests.exceptions.InvalidURL: "ERR: URL Invalid",
            requests.exceptions.ConnectionError: "ERR: Couldn't connect",
            TypeError: "ERR: Unreadable response",  # Lol wth
            requests.exceptions.ConnectTimeout: "ERR: Timed out",
            requests.exceptions.ReadTimeout: "ERR: Read timed out",
        }

        indices = [
            i
            for i, x in enumerate(self._all_results)
            if x.scan_link == urllib.parse.unquote(request.url)
        ]
        # Response object will be none so we need to add it to dict here
        for idx in indices:
            self._all_results[idx].set_result_by_exception(exception)

    @property
    def get_normalized_link_list(self):
        return self._normalized_link_list

    @property
    def get_article_link_dict(self):
        return self.article_link_dict

    @property
    def all_results(self):
        return self._all_results
