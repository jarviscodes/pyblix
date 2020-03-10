class InvalidTargetException(Exception):
    def __init__(self):
        msg = "The target you have specified is not valid. \n" \
              "This is likely due to a connection failure to the 'article_root_page' parameter \n" \
              "or a problem with requests. "
        super(InvalidTargetException, self).__init__(self, msg)


class InvalidParentLevelException(Exception):
    def __init__(self):
        msg = "The parent you have specified does not appear to be found in the page."
        super(InvalidParentLevelException, self).__init__(self, msg)


class DuplicateLevelException(Exception):
    def __init__(self, level):
        msg = f"Duplicate scan level found. We are already scanning {level}, no need to add it again"
        super(DuplicateLevelException, self).__init__(self, msg)