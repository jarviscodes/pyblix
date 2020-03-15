from pyblix import Gatherer, GatherLevel, ScanLevel, Scanner
from collections import defaultdict


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

    all_results = s.all_results

    groups = defaultdict(list)
    for scanresult in all_results:
        groups[scanresult.parent_text].append(scanresult)

    # Don't mind the output, it's just an example :P
    for group in groups:
        print(f"Level {group}")
        print(
            f"{'Scan Link':.20}\t\t{'Scanned':.10}\t\t{'code':.5}\t\t{'Exception':.10}\t\t{'Message':.20}"
        )
        for entry in groups[group]:
            # Now you can filter here too :-)
            # if entry.code not in 302,201...
            print(
                f"{entry.scan_link:.20}\t\t{entry.scan_done:>10}\t\t{entry.status_code:>5}\t\t{entry.threw_exception:>10}\t\t{entry.result_text:.20}"
            )


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
    # s.print_basic_scan_report()


if __name__ == "__main__":
    # pybit_runner()
    toe_runner()
