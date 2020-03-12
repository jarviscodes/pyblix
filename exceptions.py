class InvalidTargetException(Exception):
    def __init__(self):
        msg = (
            "The target you have specified is not valid. \n"
            "This is likely due to a connection failure to the 'article_root_page' "
            "parameter \nor a problem with requests. "
        )
        super(InvalidTargetException, self).__init__(self, msg)


class InvalidParentLevelException(Exception):
    def __init__(self):
        msg = "The parent you have specified does not appear to be found in the page."
        super(InvalidParentLevelException, self).__init__(self, msg)


class DuplicateLevelException(Exception):
    def __init__(self, level):
        msg = (
            f"Duplicate scan level found. We are already scanning {level},"
            " no need to add it again"
        )
        super(DuplicateLevelException, self).__init__(self, msg)


class InvalidLinkEntryException(Exception):
    def __init__(self):
        msg = (
            f"The link we tried to normalize is not a string nor a list, this"
            " shouldn't happen and needs debugging :("
        )
        super(InvalidLinkEntryException, self).__init__(self, msg)


class NoLinksInScanLevel(Exception):
    def __init__(self):
        msg = (
            "There are no links in the dictionary, either your scanlevel is "
            "incorrect or there simply weren't any links!"
        )
        super(NoLinksInScanLevel, self).__init__(self, msg)


class UnknownDictExceptionError(Exception):
    def __init__(self):
        # Todo: Write docs for how to fix.
        msg = "Oof! You ran into an exception that's not yet in our dict"
        super(NoLinksInScanLevel, self).__init__(self, msg)
