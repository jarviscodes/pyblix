from pyblix import GatherLevel, Gatherer, ScanLevel, Scanner

# Create a gather level
gl = GatherLevel("ul", "id", "articleList")

# Create and prepare the gatherer
g = Gatherer(domain="pybit.es", verify_ssl=True, article_root_page="https://pybit.es/pages/articles.html", parent_level=gl, verbose=True)

# prepare the scanner and scanlevel
sl_1 = ScanLevel("article", "class", "single")

# Create Scanner
s = Scanner(g)

# Add level
s.add_level(sl_1)

# Collect and scan links
s.collect_links()
s.scan_links()

# Now we can print the scan report.
s.print_basic_scan_report()
