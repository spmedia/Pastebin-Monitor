#!/usr/bin/env python2.7

import json
import time
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email import Encoders
from collections import deque
import os.path
import requests

#################################################
#                                               #
#              Pastebin-Monitor.py              #
#                     v2.0                      #
#               A pastebin monitor              #
#                                               #
#             By s0ups (@ynots0ups)             #
#                                               #
# https://github.com/ynots0ups/Pastebin-Monitor #
#                                               #
#################################################
# Whitelist your IP @ https://pastebin.com/api_scraping_faq
# The scraping API can only be reached from whitelisted IPs!

########### Shit For You To Change ##############
#
# Connection specific settings
#
PASTE_LIMIT = 500 # Number of pastes to query for; max 500
WAIT_TIME = 60 # In seconds

#
# Directory to save raw pastes relative to run dir
#
SAVE_DIR = "saved/"  # Directory to save files into.

#
# Keywords that will cause the script to save a paste
#
KEYWORD_LIST = [
	"your",
	"mom",
	"likes",
	"s0ups"
]

#
# Mail Settings
#
SERVER = 'localhost'
SENDER = ''
RECIPIENT = ''

#################################################
################## The Code #####################
paste_tracker = deque(maxlen=PASTE_LIMIT)
sapi_url = 'http://pastebin.com/api_scraping.php'

# Populate tracker for inital usage
for x in range(0, PASTE_LIMIT):
    paste_tracker.append(x)

def ParsePaste(paste):
    for keyword in KEYWORD_LIST:
        if keyword.lower() in paste.lower():
            return keyword
    return 0

def ProcessHit(key, title, user, timestamp, paste, keyword):
    filename = SAVE_DIR + key + ".txt"
    file = open(filename,"a")
    save_data = "Title: %s\r\nUser: %s\r\nTimestamp: %s\r\nSource: http://pastebin.com/%s\r\n\r\n=================\r\n\r\n%s\r\n" % (title, user, time.ctime(int(timestamp)), key, paste.encode('ascii', 'ignore'))
    file.write(save_data)
    file.close()

    # Send notification e-mail
    msg = MIMEMultipart()
    msg['Subject'] = 'Found paste matching keyword: %s' % keyword
    msg['From']    = SENDER
    msg['To']      = RECIPIENT
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(open(filename, 'rb').read())
    Encoders.encode_base64(part)
    part.add_header('Content-Disposition', 'attachment; filename="%s.txt"' % key)
    msg.attach(part)
    try:
        smtpObj = smtplib.SMTP(SERVER)
        smtpObj.sendmail(SENDER, RECIPIENT, msg.as_string())
    except:
        pass
    return

while True:
    # pull list of pastes
    r = requests.get(sapi_url + '?limit=%s' % PASTE_LIMIT)
    paste_list = json.loads(r.text)

    for i in reversed(paste_list):
        seen = i['key'] in paste_tracker
        if not seen:
            paste_tracker.append(str(i['key']))
            paste = requests.get(i['scrape_url']).text
            # Check for keywords
            result = ParsePaste(paste)
            if result:
                ProcessHit(i['key'], i['title'], i['user'], i['date'], paste, result)

    r.connection.close()
    time.sleep(WAIT_TIME)