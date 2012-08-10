import os, shutil, sys
import mechanize
import datetime, time
from datetime import date

from emailer import alert

# 3 bedrooms, still set the neighborhood
CRAIG_URL = 'http://sfbay.craigslist.org/search/apa/sfc?query=&srchType=A&minAsk=&maxAsk=&bedrooms=3&nh=%s'

# File with neighborhoods to URL
NBHDS_REF_FILE = 'neighborhoods.html'

# Will be writing and reading datetimes from file
#TIME_FORMAT = '%d-%m-%y-%H:%M'
TIME_FORMAT = '%m/%d/%y %H:%M'
NOW = datetime.datetime.strftime(datetime.datetime.now(), TIME_FORMAT)

# Neighborhoods...
NBHDS_WANT = [ 'marina', 'russian hill', 'nob hill', 'mission',
               'noe valley', 'soma', 'pacific heights',
               'lower haight', 'cole', 'bernal', 'civic' ]

# Inactive + active listings files
DIR = 'out'
DIR_BACKUP = 'backup'
FILE_INACTIVE = 'out/inactive'
FILE_ACTIVE = 'out/active'
FILE_BACKUP = 'listings'

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
            if nbhd in line.lower() and not 'excelsior' in line:
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
    return filter(lambda x: x != None, map(fix_listing, listings))

def fix_listing_new_craiggy(list):
    s = list[6]
    try:
        start = s.index(' / ') + 3
        bds = int(s[start : s.index('br')])
    except: bds = 3
    if bds > 3: return None

    # Find the price...
    try:
        start = s.index('$') + 1
        price = int(s[start : s.index(' ')])
    except: price = 0
    if price > 6000: return None

    s = s[:len(s) - 2]
    xx = [list[0], NOW, list[2], str(price),
            list[8], s, list[4]] + list[10:]
    if len(xx) > 8:
        xx[5] += ' ' + xx[6]
        xx[6:] = xx[7:]
    return xx

# Adds the time and strips out useless fields from the listing. Also
# parses number of bedrooms and returns None if more than 3. Parses
# price and puts in own field.
def fix_listing(list):
    # Find the number of bedrooms...
    s = list[3]
    try:
        start = s.index(' / ') + 3
        bds = int(s[start : s.index('br')])
    except: bds = 3
    if bds > 3: return None

    # Find the price...
    try:
        start = s.index('$') + 1
        price = int(s[start : s.index(' ')])
    except: return fix_listing_new_craiggy(list)
    if price > 6000: return None

    return [list[0], NOW, list[1], str(price), list[5], list[3]] + list[6:]

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
def get_current_listings(test=False):
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

def get_days_on_market(parts):
    def subtract(end, begin):
        end = date(2012, end.month, end.day)
        begin = date(2012, begin.month, begin.day)
        return (end - begin).days
    print parts
    if parts[2] == MARKER:
        off = datetime.datetime.strptime(parts[1], TIME_FORMAT)
        on = datetime.datetime.strptime(parts[4], '%b %d')
    else:
        off = datetime.datetime.strptime(NOW, TIME_FORMAT)
        on = datetime.datetime.strptime(parts[2], '%b %d')
    return str(subtract(off, on))

# Adds the current time to the listing so know when it entered inactive
def fix_inactive(inactive):
    out = []
    for i in inactive:
        if i[2] == MARKER: out.append(i)
        else: out.append([i[0], NOW, MARKER, get_days_on_market(i)] + i[1:])
    return out

# So craigslist is silly and some listings will disappear and then come
# back. Surprise!
def fix_inact_to_act(listing):
    if listing[2] != MARKER: return listing
    return [listing[0]] + listing[4:]

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

def quietly_create(path):
    try: os.mkdir(path)
    except: pass

# Losing things sucks. Since this is all cumulative, let's remember what
# happened every time in case something awful happens.
def backup(active, inactive):
    path = os.path.join(DIR, DIR_BACKUP)
    quietly_create(path)
    path = os.path.join(path, NOW.replace(' ', '_').replace('/', '-'))
    quietly_create(path)
    path = os.path.join(path, FILE_BACKUP)
    dump_listings(path, 'w', active + inactive)

def get_listing_alert(l):
    thing = [ l[3], l[4], l[5], l[0] ]
    return '\n'.join(thing)

def alert_of_nice_stuff(active):
    count = 0
    for listing in active:
        if count >= 4: break
        if listing[1] != NOW: continue
        price = int(listing[3])
        if price > 6000: continue
        alert(get_listing_alert(listing), False)
        count += 1
    return count

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
    backup(acive, old)

    # Print for fun
    print "Wrote %d active and %d inactive listings" % (
        len(acive), len(old))

    # Alert
    print 'Alerted of %d' % alert_of_nice_stuff(acive)

if __name__ == '__main__':
    go()
