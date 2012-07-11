import mechanize

# 3 bedrooms, still set the neighborhood
CRAIG_URL = 'http://sfbay.craigslist.org/search/apa/sfc?query=&srchType=A&minAsk=&maxAsk=&bedrooms=3&nh=%s'

# File with neighborhoods to URL
NBHDS_REF_FILE = 'neighborhoods.html'

# Neighborhoods...
NBHDS_WANT = [ 'marina', 'russian hill', 'nob hill', 'mission',
               'noe valley', 'soma', 'pacific heights',
               'potrero hill' ]

# Returns the craigslist urls of the different neighborhoods we want
# The ret is an array of tuples (url, neighboorhood str)
def get_neighborhoods_urls():
    f = open(NBHDS_REF_FILE, 'r')
    TAG = 'value="'
    urls = []

    for line in f.readlines():
        # Determine if the line is relevant
        if not TAG in line: continue
        happy = False
        for nbhd in NBHDS_WANT:
            if nbhd in line.lower():
                happy = True; break
        if not happy: continue

        # Add it.
        start = line.index(TAG) + len(TAG)
        end = line.index('"', start)
        url = CRAIG_URL % line[start : end]
        urls.append( (url, nbhd) )
    return urls

# THis is to do the opening. May want to add delays or error handling.
def get_html(br, url):
    resp = br.open(url)
    s = resp.read()
    resp.close()
    return s

# Takes a line and strips out all HTML tags
def strip_tags(x):
    found = [' ']
    i = 0
    while i < len(x):
        c = x[i]
        if c == '<':
            while i < len(x) and x[i] != '>': i += 1
            i += 1
            if not found[len(found) - 1] == ' ': found.append(' ')
        else: found.append(c); i += 1
    return ''.join(found).strip()

def get_listings(s):
    ROW_TAG = '<p class="row">'
    listings = []; end = 0
    while ROW_TAG in s[end:]:
        start = s.index(ROW_TAG, end) + len(ROW_TAG)
        end = s.index('</p>', start)
        lines = s[start : end].strip().split('\n')

        listing = map(lambda line: strip_tags(line.strip()), lines)
        listings.append(listing)
    return listings

# Talks to craigslist, returns a list of string results
def talk_to_craig(br, url, nbhd):
    print '%s\t%s' % (nbhd, url)
    s = get_html(br, url)
    listings = get_listings(s)
    import pdb; pdb.set_trace()
    return listings

def go():
    # Set up: neighboorhoods + browser
    ns = get_neighborhoods_urls()
    br = mechanize.Browser()
    br.set_handle_robots(False) # sorry :(
    br.addheaders = [
        ('User-agent',
         'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_3) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.142 Safari/535.19')] # not necessary

    # Go thorugh them all and read them
    results = map(lambda (u, n): talk_to_craig(br, u, n), ns)
    print results

if __name__ == '__main__':
    go()
