#!/usr/bin/python3
#
# die.net man pages crawler
# Copyright 2011 Chuan Ji <jichuan89@gmail.com>
#

import urllib.request
import re
import sqlite3
import sys

def fetchURL(url):
  return urllib.request.urlopen(url).read().decode(errors='ignore')

def getSections():
  sectionListURL = 'http://linux.die.net/man/'
  _sectionList = re.findall('^<dt><a href="(.)/">Section .</a><dd>([a-zA-Z ]*)',
                            fetchURL(sectionListURL), re.MULTILINE)
  sectionList = []
  for (section, desc) in _sectionList:
    sectionList.append((section, desc.strip()))
  return sectionList


def getPageList(section):
  sectionURL = 'http://linux.die.net/man/%s/' % (section)
  return re.findall('^<dt><a href=".*">(.*)</a>\(.*\)<dd>(.*)$',
                    fetchURL(sectionURL), re.MULTILINE)

def getPage(section, page):
  pageURL = 'http://linux.die.net/man/%s/%s' % (section, page)
  contentStartMarker = '<!-- google_ad_section_start -->'
  contentEndMarkers = ['<div id=adbottom>', '</div>\n<div id=menu>']
  adrightStartMarker = '<div id=adright>'
  adrightEndMarker = '</div>'
  html = fetchURL(pageURL)
  contentStart = html.index(contentStartMarker) + len(contentStartMarker)
  adrightStart = html.find(adrightStartMarker, contentStart)
  adrightEnd = html.find(adrightEndMarker, adrightStart) + len(adrightEndMarker)
  for contentEndMarker in contentEndMarkers:
    p = html.find(contentEndMarker, adrightEnd)
    if p != -1:
      contentEnd = p
      break
  if contentEnd == -1:
    print('Error processing %s/%s' % (section, page))
    sys.exit()
  if adrightStart == -1:
    return html[contentStart:contentEnd]
  else:
    return html[contentStart:adrightStart] + html[adrightEnd:contentEnd]

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
    for (pageName, pageDesc) in pageList:
      print('\r\t(%05d/%05d) %40s' % (i, len(pageList), pageName), end = '')
      dbCursor.execute('INSERT INTO pages(name, section, desc, content) VALUES(?, ?, ?, ?)',
                       (pageName, sectionName, pageDesc, getPage(sectionName, pageName)))
      i += 1
    print()

  # finalize DB
  dbHandle.commit()


buildDB('die_net.db')

