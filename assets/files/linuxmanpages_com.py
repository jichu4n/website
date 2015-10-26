#!/usr/bin/python3
#
# linuxmanpages.com man pages crawler
# Copyright 2011 Chuan Ji <jichuan89@gmail.com>
#

import urllib.request
import re
import sqlite3
import sys

def fetchURL(url):
  return urllib.request.urlopen(url).read().decode(errors='ignore')

def getSections():
  sectionListURL = 'http://www.linuxmanpages.com'
  return re.findall('^<option value="(.)">\d\. (.*)</option>$',
                    fetchURL(sectionListURL), re.MULTILINE)


def getPageList(section):
  sectionURL = 'http://www.linuxmanpages.com/man%s/' % (section)
  _pageList = re.findall('<li><a href=\'(.*)\'>(.*)</a>$',
                         fetchURL(sectionURL), re.MULTILINE)
  pageList = []
  for (pageURL, page) in _pageList:
    pageList.append((page, pageURL))
  return pageList

def getPage(pageURL):
  pageURL = 'http://www.linuxmanpages.com%s' % (pageURL)
  contentStartMarker = '\n</script></div>\n'
  contentEndMarker = '<HR>'
  html = fetchURL(pageURL)
  contentStart = html.index(contentStartMarker) + len(contentStartMarker)
  contentEnd = html.find(contentEndMarker, contentStart)
  return re.sub('"\.\./man(.).*/.*?\.php">(.*?)</A>',
                '"/man/\g<1>/\g<2>">\g<2></A>', html[contentStart:contentEnd])

def buildDB(path):
  # initialize DB
  dbHandle = sqlite3.connect(path)
  dbCursor = dbHandle.cursor()

  # build sections table
  sections = getSections()
  dbCursor.execute('DROP TABLE IF EXISTS sections')
  dbCursor.execute('CREATE TABLE sections(name TEXT, desc TEXT)')
  dbCursor.executemany('INSERT INTO sections(name, desc) VALUES (?, ?)',
                       sections)

  # build pages - this could take a while
  dbCursor.execute('DROP TABLE IF EXISTS pages')
  dbCursor.execute('CREATE TABLE pages(name TEXT, section TEXT, desc TEXT, content TEXT)')
  for (sectionName, sectionDesc) in sections:
    print('Processing section %s:' % (sectionName))
    pageList = getPageList(sectionName)
    i = 1
    for (pageName, pageURL) in pageList:
      print('\r\t(%05d/%05d) %40s' % (i, len(pageList), pageName), end = '')
      dbCursor.execute('INSERT INTO pages(name, section, desc, content) VALUES(?, ?, ?, ?)',
                       (pageName, sectionName, '', getPage(pageURL)))
      i += 1
    print()

  # finalize DB
  dbHandle.commit()

buildDB('linuxmanpages_com.db')

