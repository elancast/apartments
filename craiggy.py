import os, shutil, sys
import mechanize
import datetime, time

# 3 bedrooms, still set the neighborhood
CRAIG_URL = 'http://sfbay.craigslist.org/search/apa/sfc?query=&srchType=A&minAsk=&maxAsk=&bedrooms=3&nh=%s'

# File with neighborhoods to URL
NBHDS_REF_FILE = 'neighborhoods.html'

# Will be writing and reading datetimes from file
TIME_FORMAT = '%m-%d-%y %H:%M'
NOW = datetime.datetime.strftime(datetime.datetime.now(), TIME_FORMAT)

# Neighborhoods...
NBHDS_WANT = [ 'marina', 'russian hill', 'nob hill', 'mission',
               'noe valley', 'soma', 'pacific heights',
               'potrero hill' ]

# Inactive + active listings files
FILE_INACTIVE = 'out/inactive'
FILE_ACTIVE = 'out/active'

# Useful
N_I = 0
MARKER = 'I'

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
    try:
        resp = br.open(url)
        s = resp.read()
        resp.close()
    except:
        time.sleep(10)
        s = get_html(br, url)
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

# Returns all of the listings for the given HTML string s
def get_listings(s):
    ROW_TAG = '<p class="row">'
    listings = []; end = 0
    while ROW_TAG in s[end:]:
        start = s.index(ROW_TAG, end) + len(ROW_TAG)
        end = s.index('</p>', start)
        lines = s[start : end].strip().split('\n')
        listing = map(lambda line: strip_tags(line.strip()), lines)

        # Add in the url toooo [ of the listing ]
        TAG = 'href="'
        st = s.index(TAG, start) + len(TAG)
        e = s.index('"', st)
        listings.append([ s[st:e] ] + listing)
    return map(fix_listing, listings)

# Adds the time and strips out useless fields from the listing
def fix_listing(list):
    return [list[0], NOW, list[1], list[3]] + list[5:]

# Returns an array of listing parts for the listing string
def get_listing_for_str(s):
    return s.split('\t')

# ['http://sfbay.craigslist.org/sfc/apa/3117256667.html', 'Jul 11', '-', '$3900 / 3br - Fully Remodeled 3 Bed 2 Bath Convenient Location', '-', '(SOMA / south beach)', 'pic', '']
def get_listing_str(list):
    better = map(lambda x: x.replace('\t', ' '), list)
    return '\t'.join(better)

def dump_listings(listings):
    print '\n'.join(listings)
    print ''

# Talks to craigslist, returns a list of string results
def talk_to_craig(br, url, nbhd):
    print '%s\t%s' % (nbhd, url)
    s = get_html(br, url)
    listings = get_listings(s)
    return listings

def handle_file(file):
    f = open(file)
    listings = get_listings(f.read())
    f.close()
    return listings

# Talks to craigslist to get the current flights
def get_current_listings(test=True):
    # Testing -- just read from file
    if test:
        DIR = 'pgs'
        fs = os.listdir(DIR)
        results = map(lambda x: handle_file(os.path.join(DIR, x)), fs)
        return reduce(lambda x, y: x + y, results)

    # Set up: neighboorhoods + browser
    ns = get_neighborhoods_urls()
    br = mechanize.Browser()
    br.set_handle_robots(False) # sorry :(
    br.addheaders = [
        ('User-agent',
         'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_3) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.142 Safari/535.19')] # not necessary

    # Go thorugh them all and read them
    results = map(lambda (u, n): talk_to_craig(br, u, n), ns)
    return reduce(lambda x, y: x + y, results)

def dump_listings(fileName, mode, listings):
    f = open(fileName, mode)
    for listing in listings:
        f.write('%s\n' % get_listing_str(listing))
    f.close()

def read_listings(fileName):
    try:
        f = open(fileName, 'r')
        lines = f.read().split('\n')
        lines = lines[:len(lines) - 1]
        f.close()
        return map(get_listing_for_str, lines)
    except:
        return []

# Adds the current time to the listing so know when it entered inactive
def fix_inactive(inactive):
    out = []
    for i in inactive:
        if i[2] == MARKER: out.append(i)
        else: out.append([i[0], NOW, MARKER] + i[1:])
    return out

# So craigslist is silly and some listings will disappear and then come
# back. Surprise!
def fix_inact_to_act(listing):
    if listing[2] != MARKER: return listing
    return [listing[0]] + listing[3:]

# Expects the time string field to be 2nd, sorts by time
def sort_listings(listings):
    def get_time(listing):
        return datetime.datetime.strptime(listing[1], TIME_FORMAT)
    return sorted(listings, key=get_time)

# Returns a dictionary of listings
def get_listing_map(listings):
    d = {}
    for l in listings: d[l[N_I]] = l
    return d

# Take the new, old, and inactive listings. Things:
# If listing is in new and old, keep in new
# If listing is in old or inactive and not new, put in inactive
# If listing in inactive, not old, but new, WEIRD. put in new. take out.
# Listings are identified by their URLs. Assuming unique.
def combine_active_listings(curr_l, old_l, in_l):
    # Run through the old and inactive and check if they're in new
    (new_inactive, new_current) = ([], {})
    curr = get_listing_map(curr_l)
    for listing in old_l + in_l:
        key = listing[N_I]
        if key in curr: new_current[key] = fix_inact_to_act(listing)
        else: new_inactive.append(listing)

    # Add any new actives and reformat the inactives
    for key in curr:
        if not key in new_current: new_current[key] = curr[key]
    new_inactive = fix_inactive(new_inactive)

    # Sort all by time and return
    return map(sort_listings, [new_current.values(), new_inactive])

def go():
    # Get the current listings...
    current = get_current_listings()
    print '\n'.join(map(str, current))

    # Get the old active listings
    old = read_listings(FILE_ACTIVE)
    inactive = read_listings(FILE_INACTIVE)

    # Find any old active that no longer exist, write to inactive
    (acive, old) = combine_active_listings(current, old, inactive)
    dump_listings(FILE_ACTIVE, 'w', acive)
    dump_listings(FILE_INACTIVE, 'w', old)

    # Print for fun
    print "Wrote %d active and %d inactive listings" % (
        len(acive), len(old))

if __name__ == '__main__':
    go()
