#! /usr/bin/python
# -*- coding: utf-8 -*-

"""A program to import JSON bookmarks from firefox/chrome, test the site to see if it's still live (no 404), prune any duplicates, and return a list for me to process"""

import csv, json, pprint, datetime, time, requests
from bs4 import BeautifulSoup
from collections import namedtuple

iso_date = '%Y-%m-%d %H:%M:%S'
Bookmark = namedtuple('Bookmark', 'title, uri, date_added, last_modified, location')
uniqueBookmarks = set()
goodBookmarks = set()
Bookmarks = []

def iso_timestamp (unix_timestamp):
    return datetime.datetime.fromtimestamp(unix_timestamp).strftime(iso_date)

def parse_bookmarks (jsonBookmark, container):
    if 'children' in jsonBookmark:
        # this is a container, recurse
        if 'title' in jsonBookmark:
            container = container + ' > ' + jsonBookmark['title']
        else:
            container = 'ROOT'
        for child in jsonBookmark['children']:
            parse_bookmarks(child, container)
    elif 'uri' not in jsonBookmark:
        # this is not a bookmark (or it doesn't have a uri)
        pass
    else:
        # this is a bookmark, process
        # pprint.pprint(jsonBookmark)
        if jsonBookmark['uri'] in uniqueBookmarks:
            # this bookmark is already in the list, ignore it
            pass
        else:
            # this is a new, unique bookmark
            # add it to the unique set
            uniqueBookmarks.add(jsonBookmark['uri'])

            # create the new Bookmark record and add it to the list
            bookmark = Bookmark(jsonBookmark.get('title', ''),
                                jsonBookmark['uri'],
                                jsonBookmark.get('dateAdded', 0)/1000000.0,
                                jsonBookmark.get('lastModified', 0)/1000000.0,
                                container)
            Bookmarks.append(bookmark)
            
def parse_chrome (fpChrome):
    soup = BeautifulSoup(fpChrome.read(), 'html.parser')
    for tag in soup.select('a'):
        if tag.attrs['href'] in uniqueBookmarks:
            # this bookmark is already in the list, ignore it
            pass
        else:
            # this is a new, unique bookmark
            # add it to the unique set
            uniqueBookmarks.add(tag.attrs['href'])

            bookmark = Bookmark(tag.getText(),
                                tag.attrs.get('href', ''),
                                tag.attrs.get('ADD_DATE', ''),
                                tag.attrs.get('LAST_MODIFIED', ''),
                                'unknown')
            Bookmarks.append(bookmark)


def check_links ():
    for uri in uniqueBookmarks:
        try:
            res = requests.get(uri)
            if res.status_code == requests.codes.ok:
                # this is a good, live link - add it to the good list
                goodBookmarks.add(uri)
        except:
            pass

def csvWrite ():
    csvOutput = open('/home/bhorn/scripts/test/bookmarks.csv', 'w', newline='')
    outputWriter = csv.writer(csvOutput)
    for bookmark in Bookmarks:
        if bookmark.uri in goodBookmarks:
            outputWriter.writerow(list(bookmark))

    csvOutput.close()

# import bookmarks

fpFirefoxBookmarks = open('/home/bhorn/bookmarks-2016-03-03.json', 'r')
fpChromeBookmarks = open('/home/bhorn/chrome-bookmarks_3_3_16.html', 'r')

bookmarks = json.load(fpFirefoxBookmarks)

print('Parsing bookmarks...')
parse_bookmarks(bookmarks, '')
parse_chrome(fpChromeBookmarks)
fpFirefoxBookmarks.close()
fpChromeBookmarks.close()
print('Unique Bookmarks: %s' % len(uniqueBookmarks))

print('Checking bookmarks...')
check_links()
print('Good Bookmarks: %s' % len(goodBookmarks))

print('Writing good links to file...')
csvWrite()

