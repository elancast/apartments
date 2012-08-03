import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
import datetime

FROM_EMAIL = "CRAIGGY <elancast@cs.princeton.edu>"
EMILY_EMAIL = '6094238157@tmomail.net'
CHRIS_EMAIL = '6313552173@txt.att.net'
RAFII_EMAIL = '3057736239@txt.att.net'

def getSmtp(file, host="smtp.princeton.edu", port=587):
    a = smtplib.SMTP(host, port)
    f = open(file, 'r')
    creds = map(lambda x: x.strip(), f.readlines())
    a.login(creds[0], creds[1])
    a.starttls()
    return a

def sendit(smtp, msg, subject, tos, fro):
    addrs = setMeta(msg, subject, tos, fro)
    s = msg.as_string()
    ret = smtp.sendmail(fro, addrs, s)
    print "Sent with return %s to %s" % (str(ret), str(addrs))

def setMeta(msg, subject, tos, fro):
    msg['Subject'] = subject
    msg['From'] = fro
    msg['To'] = ','.join(tos)
    return tos

def getSubject():
    date = datetime.date.today().strftime('%a %b %d, %Y')
    return '[VDay emails] Happy %s!' % date

def alert(email, test=True):
    cnt = getSmtp('/u/elancast/v/.shhhh')
    msg = MIMEText(email)

    tos = [ EMILY_EMAIL ]
    if not test: tos += [ CHRIS_EMAIL, RAFII_EMAIL ]
    for email in tos:
        sendit(cnt, msg, 'Craigslist Alert', [email], FROM_EMAIL)

if __name__ == '__main__':
    alert("hello world")
