#!/usr/bin/python
"""
Simple scraper of simplified Chinese characters from web pages.
Characters are counted and their frequencies are put in a database.
It's then possible to query the database for the list of
most frequent characters.

Consider this code in the public domain.
Matteo Mecucci
"""
import sys
import codecs
import argparse
from cjk import isCharacterCJK, get_conv_table
from pymongo import Connection, DESCENDING
from bs4 import BeautifulSoup
import requests

def updateFrequenciesDB(frequencies, db_collection):
  """
  Update the DB with the specified characters frequencies.
  """
  total_chars = 0
  for c, incr in frequencies.iteritems():
    total_chars += incr
    if db_collection.find_one({"character": c}):
      db_collection.update({"character": c}, {"$inc": {"count": incr}})
    else:
      db_collection.insert({"character": c, "count": incr})
  # update the total count of analyzed characters
  if db_collection.find_one({"meta": "total_count"}):
    db_collection.update({"meta": "total_count"}, {"$inc": {"count": total_chars}})
  else:
    db_collection.insert({"meta": "total_count", "count": total_chars})

def clearStats(db_collection):
  """
  Delete everything from the db.
  """
  db_collection.remove()
  print "All data removed."

def printTopWords(db_collection, numwords):
  """
  Print out the most frequent characters found so far, in descending order.
  """
  totalcountitem = db_collection.find_one({"meta": "total_count"})
  if not totalcountitem:
    print "No statistics found in the database."
    return

  # use a conversion table from unicode to pinyin to print nicely each character
  convtable = get_conv_table()

  num_chars = db_collection.count()-1 # 1 is the meta total count
  totalcount = totalcountitem["count"]

  print "{} distinct characters collected so far.".format(num_chars)
  print "The {} most frequent ones are:".format(numwords)

  countsum = 0
  for cdict in db_collection.find(
      {"character": { "$exists": True }, "count": { "$exists": True }},
      limit=numwords,
      sort=[("count", DESCENDING)]):
    countsum += cdict["count"]
    perc = cdict["count"] * 100.0 / totalcount
    ucode = ord(cdict["character"])
    pinyin = convtable[ucode]
    print u"{character} (U+{ucode:4X}: {pinyin:5s}): {count} ({perc:.2f}%)".format(
        ucode=ucode, pinyin=pinyin, perc=perc, **cdict)

  print "------------"
  print "Total occurrencies: {}/{} ({:.2f}%)".format(countsum, totalcount, countsum*100.0/totalcount)

def scrapeText(url, encoding):
  """
  Get the text from the specified URL.
  If encoding is None, it gets guessed.
  """
  r = requests.get(url)
  if encoding:
    r.encoding = encoding
  htmlSoup = BeautifulSoup(r.text)
  return htmlSoup.get_text()

def parseArgs():
  """
  Parse command-line arguments.
  """
  parser = argparse.ArgumentParser(
    usage='%(prog)s ([options] URL [URL ...] | [-n NUMWORDS] | --clear-stats)',
    description="""
    Scrape web pages to collect CJK characters frequencies.
    If URLs are omitted, the most frequent characters collected so far are shown.
    """)

  parser.add_argument('urls', metavar='URL', help='the URLs of the documents to scrape',
      nargs='*')

  parser.add_argument('-e', '--encoding', help='encoding for the web pages to scrape, default: guessed')
  parser.add_argument('-n', '--numwords', help='max number of words to print out -- use with no other argument',
      type=int, default=10)
  parser.add_argument('--clear-stats', help='clear all statistics gathered so far -- use with no other argument',
      action='store_true')

  return parser.parse_args()

def dbCollection():
  dbconn = Connection()
  db = dbconn.characters_db
  return db.characters_frequencies

def scrapeUrls(args):
  """
  Scrape all the urls stored in the command line arguments
  for CJK characters, counts their frequencies and stores
  them in the db.
  """
  read_chars_cjk_total = 0
  db_collection = dbCollection()

  for url in args.urls:
    print "Scraping {}...".format(url),
    sys.stdout.flush()

    htmlText = scrapeText(url, args.encoding)

    read_chars_all = 0
    read_chars_cjk = 0

    frequencies = {}

    for c in htmlText:
      if isCharacterCJK(c):
        if c in chars:
          frequencies[c] += 1
        else:
          frequencies[c] = 1
        read_chars_cjk += 1
      read_chars_all += 1

    updateFrequenciesDB(frequencies, db_collection)
    read_chars_cjk_total += read_chars_cjk

    print "{}/{} CJK chars found.".format(read_chars_cjk, read_chars_all)

  print "Added {} CJK characters to the database.".format(read_chars_cjk_total)


def main():
  args = parseArgs()

  if args.clear_stats:
    clearStats(dbCollection())
    return

  if len(args.urls) == 0:
    printTopWords(dbCollection(), args.numwords)
    return

  scrapeUrls(args)

if __name__ == "__main__":
  main()
