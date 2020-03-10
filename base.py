class PybLevel(object):
    def __init__(self, html_tag: str, html_attrib: str, html_attrib_val: str):
        self.html_tag = html_tag
        self.html_attrib = html_attrib
        self.html_attrib_val = html_attrib_val

    def __str__(self):
        return f"<{self.html_tag} {self.html_attrib}='{self.html_attrib_val}'>"


class PybLink(object):
    def __init__(self, text: str, link: str):
        self.text = text
        self.link = link

    def __str__(self):
        return f"{self.text} @ {self.link}"


class PybActivity(object):
    def __init__(self, verbose, domain, verify_ssl):
        self.verbose = verbose
        self.domain = domain
        self.verify_ssl = verify_ssl
