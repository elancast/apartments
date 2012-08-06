#!/usr/bin/python
import json, sys, time
import urllib2 as urllib

#------------------------------------------------------------------------------#

# # # # # # # # # # # # # #
#                         #
#     CLOSEST BUSSTOP     #
#                         #
# # # # # # # # # # # # # #

busStopsStr = '''
Cesar_Chavez_&_Folsom         Cesar+Chavez+st+at+Folsom     The_Mission
Cesar_Chavez_&_Mission        Cesar+Chavez+st+at+Mission    The_Mission
Valencia_&_24th/25th          24th+st+at+Valencia           The_Mission
18th_&_Church                 18th+st+at+Church             Castro

Hermann_&_Fillmore            Fillmore+st+at+Hermann        Lower_Haight
Stanyan_&_Frederick           Stanyan+st+at+Frederick       Upper_Haight

8th_&_Market                  8th+st+at+Market              SoMa
Van_Ness_&_O'Farrell          O+Farrell+st+at+Van+Ness      Nob_Hill
Van_Ness_&_Sacramento/Clay    Sacramento+st+at+Van+Ness     Nob_Hill
Van_Ness_&_Union              Union+st+at+Van+Ness          Russian_Hill
Lombard_&_Fillmore            Lombard+st+at+Fillmore        Marina
'''                                                #+San+Francisco+CA+US

busStops = busStopsStr.split('\n')
busStops = filter(lambda x : len(x), busStops)
busStops = map(lambda x : tuple(x.split()), busStops)
busStops = map(lambda x : (x[0], x[1]+'+San+Francisco+CA+US', x[2]), busStops)

# --- #

def distToClosestBusStop(addr):
    measuredStops = map(lambda x : x + dist(addr,x[1]), busStops)
    bestStop = reduce(lambda x,y : x if x[3] < y[3] else y, measuredStops)
    return bestStop

def prettyPrint(measuredStop):
    (intersection, param, district, feet, minutes) = measuredStop

    #intersection = intersection.replace('_',' ')
    #district = district.replace('_',' ')

    miles = feet / 5280.0
    blocks = feet / 350.0

    tup = (miles, blocks, intersection, district, minutes)
    return '%.2f_miles/%.2f_blocks to %s in %s (%.2f_minutes)' % tup

def humanReadableToClosest(addr):
    return prettyPrint( distToClosestBusStop(addr) )

#------------------------------------------------------------------------------#

# # # # # # # # # # # # #
#                       #
#     DISTANCE STUF     #
#                       #
# # # # # # # # # # # # #

# given two addresses,
# return directions as JSON string
def getDirections(pointA, pointB):
    formatStr = 'http://maps.googleapis.com/maps/api/directions/json?origin=%s&destination=%s&sensor=false&mode=walking&units=imperial';
    request = formatStr % (pointA, pointB)

    SLEEP_TIME = 0.5
    while 1:
        time.sleep(SLEEP_TIME)
        response = urllib.urlopen(request)
        s = response.read()
        response.close()

        # print so we know stuff is still happening.....
        sys.stderr.write('%s / %s\n' % (pointA, pointB))

        status = json.loads(s)['status']
        if status != 'OVER_QUERY_LIMIT': break

        SLEEP_TIME *= 2
        sys.stderr.write('%s %f\n' % (status,SLEEP_TIME))

    return s

# given JSON string of directions
# returns (distance in Feet, duration in Minutes)
def parseDirections(dir):
    obj = json.loads(dir)
    if obj['status'] != 'OK':
        inf = float('inf')
        return (inf, inf)

    legs = obj['routes'][0]['legs'][0]
    distMeters = legs['distance']['value']
    durSeconds = legs['duration']['value']

                            # cm        # inches   # feet
    distFeet = distMeters * (100/1.0) * (1/2.54) * (1/12.0)
    durMinutes = durSeconds * (1/60.0)
                              # minutes

    return (distFeet, durMinutes)

def dist(pointA, pointB):
    return parseDirections( getDirections(pointA,pointB) )

#------------------------------------------------------------------------------#

# # # # # # # # # # # # #
#                       #
#     ADDRESS STUFF     #
#                       #
# # # # # # # # # # # # #

def getAddress(url):

    time.sleep(1.0)
    response = urllib.urlopen(url)
    html = response.read()
    response.close()

    gMapsNode = '(<a target="_blank" href="http://maps.google.com/?q=loc%3A+'
    if gMapsNode in html:
        after = html.split(gMapsNode)[1]
        trunc = after.split('">google map</a>)')[0]
        return trunc

    return None

#------------------------------------------------------------------------------#

# # # # # # # # # # # # # #
#                         #
#     CALLER FUNCTION     #
#                         #
# # # # # # # # # # # # # #

def modifyLine(line):
    if True: return line
    if line[-1] == '\n': # strip off new line if at end
        line = line[:-1]

    fields = line.split('\t') # split on the tab

    # append ADDR/DIST fields if not already
    if 'DIST=' != fields[-1][:5]:
        fields += ['ADDR=', 'DIST=']

    # has no ADDR
    if fields[-2] == 'ADDR=':
        url = fields[0] # URL
        addr = getAddress(url) # get Address
        if addr:
            fields[-2] += addr

    # has ADDR but no DIST
    if fields[-2] != 'ADDR=' and fields[-1] == 'DIST=':
        addr = fields[-2][5:]
        dist = humanReadableToClosest(addr)
        fields[-1] += dist

    return '\t'.join(fields)

#------------------------------------------------------------------------------#

# Stuff emily added hiii

""" Takes the old lines and new lines of listings. Returns the same
number of lines as in the new but replaces any common lines with the
text from the old """
def mergeListings(olds, news):
    d = {}
    for line in olds:
        if line == '': continue
        d[line.split('\t')[0]] = line

    final = []
    for line in news:
        key = line.split('\t')[0]
        if key in d: final.append(d[key])
        else: final.append(line)
    return final

""" So Emily wants to do partial runs of Rafi's program. She'll run it
on listings at time A, but then in the future, at time B, she'll have a
new file of listings. Some of these will be in common with time A's
listings. So this should take the results of Rafi's at time A and the
new at time B, and merge them so no work is repeated.
Returns the lines if this is how it was run or None otherwise. """
def runWithMerge():
    if len(sys.argv) < 3: return None
    old_file = sys.argv[1]
    new_file = sys.argv[2]

    # Read the lines of the files
    old_lines = open(old_file).readlines()
    new_lines = open(new_file).readlines()
    old_lines = killNewLines(old_lines)
    new_lines = killNewLines(new_lines)

    # Merge them
    lines = mergeListings(old_lines, new_lines)
    return lines

""" Lol I turned Rafi's line into a function. """
def killNewLines(lines):
    return map(lambda x: x[:-1], lines)


# --- #


if __name__ == '__main__':
    lines = runWithMerge()

    # Maybe not being run with two files...
    if lines == None:
        lines = sys.stdin.readlines() # grab all stdin lines
        lines = killNewLines(lines)

    for line in lines:
        print modifyLine(line)

