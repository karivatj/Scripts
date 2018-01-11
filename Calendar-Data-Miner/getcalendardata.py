#!/usr/bin/python3.4
#  -*- coding: UTF-8 -*-

from __future__ import print_function
from builtins import input
from builtins import str
from builtins import range

import collections
import codecs
import datetime
import logging
import requests
import sys
import certifi

from auth_credentials import *
from dateutil.parser import parse
from requests_ntlm import HttpNtlmAuth
from xml.etree import ElementTree

# setup logging
# create logger with 'ipost_converter'
logger = logging.getLogger('getcalendardata')
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler('debug.log')
fh.setLevel(logging.DEBUG)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)

#content-type header must be this or server responds with 451
headers = {'Content-Type': 'text/xml; charset=utf-8'} # set what your server accepts

#date format
format = "%Y-%m-%d"

#Sample message used to query calendar data. Remember to replace relevant parts of this message
sample_getcalendar = '''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
       xmlns:m="http://schemas.microsoft.com/exchange/services/2006/messages" 
       xmlns:t="http://schemas.microsoft.com/exchange/services/2006/types" 
       xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Header>
    <t:RequestServerVersion Version="Exchange2010_SP2" />
  </soap:Header>
  <soap:Body>
    <m:FindItem Traversal="Shallow">
      <m:ItemShape>
        <t:BaseShape>IdOnly</t:BaseShape>
        <t:AdditionalProperties>
          <t:FieldURI FieldURI="item:Subject" />
          <t:FieldURI FieldURI="calendar:Start" />
          <t:FieldURI FieldURI="calendar:End" />
        </t:AdditionalProperties>
      </m:ItemShape>
      <m:CalendarView MaxEntriesReturned="10" StartDate="!Start_Date!" EndDate="!End_Date!" />
      <m:ParentFolderIds>
        <t:DistinguishedFolderId Id="calendar">
          <t:Mailbox>
            <t:EmailAddress>!Replace_Email_Of_Calendar!</t:EmailAddress>
          </t:Mailbox>
        </t:DistinguishedFolderId>
      </m:ParentFolderIds>
    </m:FindItem>
  </soap:Body>
</soap:Envelope>'''

#Calendars that are going to be parsed
calendar_list = ["calendar_email@domain.com"]

if __name__ == "__main__":
    logger.debug("Starting up...")
    calendar_data = {} #dictionary containing the data
    try:
        logger.info("Establishing connection to {0}...".format(server))
        response = requests.get(server, auth=HttpNtlmAuth(username, password), verify=certifi.where())
    except requests.exceptions.ConnectionError as e:
        logger.info("Connection error ({0})".format(e))
        sys.exit(0)

    if(response.status_code != 200):
        logger.error("Connection error. Status Code was {0}".format(response_status_code))
        sys.exit(0)
    else:
        logger.info("Connection OK - Continuing with the task")

    #Send a GetFolder request. Use Sample request as a template and replace necessary parts from it
    for calendar in calendar_list:
        calendar_name = ""

        if("TestLab" in calendar):
            calendar_name = "OYS TestLab"
        elif("Aortta" in calendar):
            calendar_name = "Aortta (Big Room)"
        elif("Cave" in calendar):
            calendar_name = "Cave"
        elif("Lappa" in calendar):
            calendar_name = "Läppä"
        elif("OikKammio" in calendar):
            calendar_name = "Oikea Kammio"
        elif("VasKammio" in calendar):
            calendar_name = "Vasen Kammio"
        elif("Pulssi" in calendar):
            calendar_name = "Pulssi"
        elif("Laskimo" in calendar):
            calendar_name = "Laskimo"
        elif("Valtimo" in calendar):
            calendar_name = "Valtimo"
        else:
            continue

        logger.debug("Creating field for " + calendar_name)
        calendar_data[calendar_name] = []

        logger.debug("Get Calendar: " + calendar_name)
        start_time = datetime.datetime.today().strftime(format) + "T00:00:00.000Z"
        end_time = datetime.datetime.today().strftime(format) + "T23:59:59.999Z"
        
        message = sample_getcalendar.replace("!Replace_Email_Of_Calendar!", calendar)
        message = message.replace("!Start_Date!", start_time)
        message = message.replace("!End_Date!", end_time)
        
        response = requests.post(server, data=message, headers=headers, auth=HttpNtlmAuth(username, password), verify=certifi.where())
        
        if(response.status_code != 200):
            logger.error("Error occured while fetching calendar: " + calendar)
            continue
        else:
            logger.debug("Response OK. Parsing data...")        
            tree = ElementTree.fromstring(response.content)
            today = datetime.datetime.now()
            timedelta = 2

            if today > datetime.datetime(datetime.date.today().year, 3, 26, 3, 0, 0) and today < datetime.datetime(datetime.date.today().year, 10, 29, 4, 0, 0):
                timedelta = 3    

            for elem in tree.iter(tag='{http://schemas.microsoft.com/exchange/services/2006/types}CalendarItem'):
                for child in elem:
                    print(child.text)
                    if("Subject" in child.tag):
                        calendar_data[calendar_name].append(child.text)
                    elif("Start" in child.tag):
                        date = parse(child.text)
                        date = date + datetime.timedelta(hours=timedelta) #add timedifference
                        calendar_data[calendar_name].append(date.strftime("%H:%M"))
                    elif("End" in child.tag):
                        date = parse(child.text)                   
                        date = date + datetime.timedelta(hours=timedelta) #add timedifference
                        calendar_data[calendar_name].append(date.strftime("%H:%M"))
        logger.debug("Success!")
        print()
             
    logger.debug("Calendar data retrieved. Outputting into HTML...")
    now = datetime.datetime.now()
    calendar_data = collections.OrderedDict(sorted(calendar_data.items(), key=lambda t: t[0]))

    with codecs.open("meetings.txt", "w", "utf-8") as f:
            f.write("<table>\n")
            f.write("<colgroup\n")
            f.write("<col class=\"column10\"/>\n")
            f.write("<col class=\"column30\"/>\n")
            f.write("<col class=\"column15\"/>\n")
            f.write("<col class=\"column30\"/>\n")
            f.write("<col class=\"column15\"/>\n")
            f.write("</colgroup>\n")
            f.write("<tr>")
            f.write("<th>Huone</th>")
            f.write("<th>Tällä hetkellä / Seuraavaksi</th>")
            f.write("<th></th>")
            f.write("<th>Myöhemmin tänä päivänä</th>")
            f.write("<th></th>")
            f.write("</tr>")

            for calendar in calendar_data:
                primary_event_found = False
                secondary_event_found = False
                f.write("<tr>\n")
                f.write("<td class=\"meetingroom\">" + calendar + "</td>\n")

                for item in range(0, len(calendar_data[calendar]), 3):
                    end_date = parse(calendar_data[calendar][item+2])
                    if(now < end_date and primary_event_found == False):
                        primary_event_found = True
                        f.write("<td class=\"event_primary\">" + calendar_data[calendar][item] + "</td>\n")
                        f.write("<td class=\"eventdate_primary\">"+ calendar_data[calendar][item+1] + " - " + calendar_data[calendar][item+2] + "</td>\n")

                    elif(now < end_date and secondary_event_found == False):
                        secondary_event_found = True
                        f.write("<td class=\"event_secondary\">" + calendar_data[calendar][item] + "</td>\n")
                        f.write("<td class=\"eventdate_secondary\">"+ calendar_data[calendar][item+1] + " - " + calendar_data[calendar][item+2] + "</td>\n")
                        break
         
                if(primary_event_found != True):
                    f.write("<td class=\"event_primary\">Vapaa</td>\n")
                    f.write("<td class=\"eventdate_primary\"></td>\n")
                if(secondary_event_found != True):
                    f.write("<td class=\"event_secondary\">Vapaa</td>\n")
                    f.write("<td class=\"eventdate_secondary\"></td>\n")

                f.write("</tr>\n")
            f.write("</table>")

    logger.debug("Ready. Thank you and come again!")