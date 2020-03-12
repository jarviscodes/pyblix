import copy
# import re
import urllib.parse
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


class ScanLinkResult(PybLink):
    def __init__(self, result_string, title, link):
        super(ScanLinkResult, self).__init__(title, link)
        self.result_string = result_string


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
    _accept_header = "text/html,application/xhtml+xml,application/xml"
    request_headers = {"User-Agent": _user_agent, "Accept": _accept_header}

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

        # Add Host field to header, some pages give 500's or other vhosts without Host
        host_header = {"Host": self.domain}
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
            self.identifiable_parent_level.html_tag,
            {html_attrib: html_attrib_val},
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
        self.link_status = {}

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

    def handle_frame(self, search_frame, article):
        try:
            all_links_in_article = search_frame.find_all("a")
        except AttributeError:
            print("Oof")
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
                            self.handle_frame(frame, article)
                    else:
                        search_frame = soup.find(
                            scan_level.html_tag,
                            {scan_level.html_attrib: scan_level.html_attrib_val},
                        )
                        self.handle_frame(search_frame, article)

            self._create_normalized_link_list()

        else:
            raise NoLinksInScanLevel

    def link_iterator(self):
        for u in self._normalized_link_list:
            parsed_url = urlparse(u)
            host = parsed_url.netloc

            request_headers = self._for_gatherer.request_headers.update({"Host": host})

            yield grequests.get(
                url=u,
                headers=request_headers,
                verify=self.verify_ssl,
                timeout=self.timeout,
            )

    def scan_links(self):
        # Lix had a lot more but even now most are obsolete for a link scanner.
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

        if self.verbose:
            print("Generating request set")

        request_set = (u for u in self.link_iterator())

        print("Firing requests and waiting for them to come back.")
        all_results = grequests.map(
            request_set, exception_handler=self.request_exception_handler
        )

        for result in all_results:
            print("In Resultloop")
            if result is not None:
                # VERY Interesting :-)
                hist = result.history
                if len(hist) > 0:
                    self.link_status[
                        urllib.parse.unquote(hist[0].url)
                    ] = response_code_readable_dict[hist[0].status_code].format(
                        result.url
                    )
                else:
                    self.link_status[
                        urllib.parse.unquote(result.url)
                    ] = response_code_readable_dict[result.status_code]

    def get_link_status(self, link):
        try:
            return self.link_status[link]
        except KeyError:
            return self.link_status[
                link + "/"
            ]  # 3 goddamn hours. If this raises a frigging error you can have it xD

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

        # Response object will be none so we need to add it to dict here
        try:
            self.link_status[request.url] = exception_readable_dict[type(exception)]
        except KeyError as ex:
            print(ex)
            raise UnknownDictExceptionError

    def print_basic_scan_report(self):
        for article in self.get_article_link_dict:
            print(f"Running article {article}")
            for link in self.get_article_link_dict[article]:
                if link in self.get_normalized_link_list:
                    print(f"\t{link} => {self.get_link_status(link)}")

    @property
    def get_normalized_link_list(self):
        return self._normalized_link_list

    @property
    def get_article_link_dict(self):
        return self.article_link_dict

    @property
    def get_link_status_dict(self):
        return self.link_status
