from pyblix import Gatherer, GatherLevel, ScanLevel, Scanner


def toe_runner():
    # Create a gather level
    gl = GatherLevel("ul", "class", "uk-nav-side")

    # Create and prepare the gatherer
    g = Gatherer(
        domain="clamytoe.github.io",
        verify_ssl=True,
        article_root_page="https://clamytoe.github.io/",
        parent_level=gl,
        verbose=True,
    )

    # prepare the scanner and scanlevel
    sl_1 = ScanLevel("section", "itemprop", "articleBody")

    # Create Scanner
    s = Scanner(g, timeout=5)

    # Add level
    s.add_level(sl_1)

    # Collect and scan links
    s.collect_links()
    s.scan_links()

    # Now we can print the scan report.
    s.print_basic_scan_report()


def pybit_runner():
    # Create a gather level
    gl = GatherLevel("ul", "id", "articleList")

    # Create and prepare the gatherer
    g = Gatherer(
        domain="pybit.es",
        verify_ssl=True,
        article_root_page="https://pybit.es/pages/articles.html",
        parent_level=gl,
        verbose=True,
    )

    # prepare the scanner and scanlevel
    sl_1 = ScanLevel("article", "class", "single")

    # Create Scanner
    s = Scanner(g, timeout=3)

    # Add level
    s.add_level(sl_1)

    # Collect and scan links
    s.collect_links()
    s.scan_links()

    # Now we can print the scan report.
    s.print_basic_scan_report()


if __name__ == '__main__':
    #pybit_runner()
    toe_runner()
