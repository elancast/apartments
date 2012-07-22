import os, shutil, sys
import datetime, time
from datetime import date

# Old time format...
TIME_FORMAT = '%d-%m-%y-%H:%M'

# New time format
NEW_TIME_FORMAT = '%m/%d/%y %H:%M'

DIR = 'out'

def fix_date(s):
    try:
        d = datetime.datetime.strptime(s, TIME_FORMAT)
        return datetime.datetime.strftime(d, NEW_TIME_FORMAT)
    except:
        return s

def get_date(s):
    return datetime.datetime.strptime(s, NEW_TIME_FORMAT)

def subtract(end, begin):
    end = date(2012, end.month, end.day)
    begin = date(2012, begin.month, begin.day)
    return (end - begin).days

def fix_inactive(parts):
    if parts[2] != 'I': return parts
    off = get_date(parts[1])
    on = datetime.datetime.strptime(parts[4] + '12', '%b %d%y')
    days = str(subtract(off, on))
    return parts[0:3] + [days] + parts[3:]

def fix_file(fileName):
    f = open(fileName)
    s = f.read()
    f.close()
    f = open(fileName + '.bak', 'w')

    for line in s.split('\n'):
        if line == '': continue
        parts = line.split('\t')
        out = map(fix_date, parts)
        out = fix_inactive(out)
        f.write('\t'.join(out) + '\n')
    f.close()

    shutil.move(fileName + '.bak', fileName)

def fix_all_files(base_dir):
    try:
        files = os.listdir(base_dir)
    except:
#        import pdb; pdb.set_trace()
        fix_file(base_dir)
        print base_dir
        return
    for file in files:
        if file.endswith('.bak'): continue
        fix_all_files(os.path.join(base_dir, file))

fix_all_files(DIR)
