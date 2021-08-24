import argparse
import base64
import configparser
import json
import logging
import signal
import sys

import feedparser
import newspaper
import redis
import validators
from newspaper.article import ArticleException
from pyail import PyAIL
from trafilatura import feeds
from urlextract import URLExtract


def urlExtract(urls, link, origin):
    for url in urls:
        # If the url is not valid, drop it and continue
        if not validators.url(url):
            continue
    
        output = {}
        output['source'] = ailurlextract
        output['source-uuid'] = uuid
        output['default-encoding'] = 'UTF-8'

        output['meta'] = {}
        output['meta']['atom-rss-link'] = link

        output['meta']['atom-rss:url-extracted'] = url

        signal.alarm(10)
        try:
            article = newspaper.Article(url)
        except TimeoutError:
            if args.verbose:
                logging.error(f"Timeout reached for {url}")
            continue
        else:
            signal.alarm(0)

        # Caching
        if r.exists(f"cu:{base64.b64encode(url.encode())}"):
            if args.verbose:
                logging.info(f"URL {url} already processed")
            if not args.nocache:
                continue
        else:
            r.set(f"cu:{base64.b64encode(url.encode())}", origin)
            r.expire(f"cu:{base64.b64encode(url.encode())}", cache_expire)
        
        if args.verbose:
            logging.info(f"Downloading and parsing {url}")

        try:
            article.download()
            article.parse()
        except ArticleException:
            if args.verbose:
                logging.error(f"Unable to download/parse {url}")
            continue

        output['data'] = article.html

        nlpFailed = False

        try:
            article.nlp()
        except:
            if args.verbose:
                logging.error(f"Unable to nlp {url}")
            nlpFailed = True

            if args.verbose:
                logging.info("Uploading the URL to AIL...\n")
                logging.info(json.dumps(output, indent=4, default=str))
            pyail.feed_json_item(output['data'], output['meta'], ailurlextract, uuid)
            continue
    
        if nlpFailed:
            continue
        
        output['meta']['newspaper:text'] = article.text
        output['meta']['newspaper:authors'] = article.authors
        output['meta']['newspaper:keywords'] = article.keywords
        output['meta']['newspaper:publish_date'] = article.publish_date
        output['meta']['newspaper:top_image'] = article.top_image
        output['meta']['newspaper:movies'] = article.movies

        if args.verbose:
            logging.info("Uploading the URL to AIL...\n")
            logging.info(json.dumps(output, indent=4, default=str))
        pyail.feed_json_item(output['data'], output['meta'], ailurlextract, uuid)


logging.basicConfig(format='%(asctime)s %(name)s %(levelname)s:%(message)s', level=logging.INFO, datefmt='%I:%M:%S')

# Information about the feeder
uuid = "26755b8d-6451-42c6-84aa-26a5a2b13744"
ailfeedertype = "ail_feeder_atom-rss"
ailurlextract = "ail_feeder_urlextract"

# Config reader
config = configparser.ConfigParser()
config.read('etc/ail-feeder-atom-rss.cfg')

if 'general' in config:
    uuid = config['general']['uuid']

if 'redis' in config:
    r = redis.Redis(host=config['redis']['host'], port=config['redis']['port'], db=config['redis']['db'])
else:
    r = redis.Redis()

if 'cache' in config:
    cache_expire = config['cache']['expire']
else:
    cache_expire = 86400

if 'ail' in config:
    ail_url = config['ail']['url']
    ail_key = config['ail']['apikey']
else:
    logging.error("Ail section not found in the config file. Add it and the necessary fields and try again!")
    sys.exit(0)
try:
    pyail = PyAIL(ail_url, ail_key, ssl=False)
except Exception as e:
    logging.error(e)
    sys.exit(0)

# Argument parsing
parser = argparse.ArgumentParser()
parser.add_argument("--verbose", help="verbose output", action="store_true")
parser.add_argument("--nocache", help="disable cache", action="store_true")
parser.add_argument("--urlextract", help="extract urls", action="store_true")
parser.add_argument("--link", help="single link to be extracted", type=str, default='')
args = parser.parse_args()

with open("links.txt") as f:
    lines = f.readlines()
    if args.link != '':
        lines.append(args.link)
    for link in lines:
        # Find feeds from the given link
        # feedUrls = feeds.find_feed_urls(link)
        feedUrls = []
        feedUrls.append(link.replace('\n', ''))
        for url in feedUrls:
            if args.verbose:
                logging.info(url)
            if r.exists(f"c:{url}"):
                if args.verbose:
                    logging.info(f"URL {url} already processed")
                if not args.nocache:
                    continue
            else:
                # TODO: What should be the value?
                r.set(f"c:{url}", url)
                r.expire(f"c:{url}", cache_expire)

            result = feedparser.parse(url)
                
            o = {}

            o['source'] = ailfeedertype
            o['uuid'] = uuid
            o['default-encoding'] = 'UTF-8'

            o['meta'] = {}
            o['meta']['url'] = url

            extractor = URLExtract()

            # Entries
            if args.verbose:
                logging.info("Extracting entries...")
            o['meta']['entries'] = []
            for entry in result['entries']:
                if r.exists(f"c:{entry['link']}"):
                    if args.verbose:
                        logging.info(f"Entry {entry['link']} already processed")
                    if not args.nocache:
                        continue
                else:
                    if 'content' in entry:
                        r.set(f"c:{entry['link']}", entry['content'][0]['value'])
                    else:
                        r.set(f"c:{entry['link']}", '')
                    r.expire(f"c:{entry['link']}", cache_expire)

                e = {}
                e['meta'] = {}
                e['meta']['link'] = entry['link']
                if 'title' in entry:
                    e['meta']['title'] = entry['title']
                if 'id' in entry:
                    e['meta']['id'] = entry['id']
                if 'summary' in entry:
                    e['meta']['summary'] = entry['summary']
                    urls = extractor.find_urls(entry['summary'])
                    if len(urls) != 0 and args.urlextract:
                        if args.verbose:
                            logging.info("Extracting URLs...")
                        urlExtract(urls, link, entry['summary'])

                e['content'] = ''
                if 'content' in entry:
                    e['content'] = entry['content'][0]['value']
                    urls = extractor.find_urls(entry['content'][0]['value'])
                    if len(urls) != 0 and args.urlextract:
                        if args.verbose:
                            logging.info("Extracting URLs...")
                        urlExtract(urls, link, entry['content'][0]['value'])

                if 'authors' in entry:
                    e['meta']['authors'] = entry['authors']
                if 'published' in entry:
                    e['meta']['published'] = entry['published']
                if 'tags' in entry:
                    e['meta']['tags'] = []
                    for tag in entry['tags']:
                        e['meta']['tags'].append(tag['term'])
                if 'updated' in entry:
                    e['meta']['updated'] = entry['updated']
                if 'comments' in entry:
                    e['meta']['comments'] = entry['comments']
                if 'wfw_commentrss' in entry:
                    e['meta']['comments-link-rss'] = entry['wfw_commentrss']

                pyail.feed_json_item(e['content'], e['meta'], ailfeedertype, uuid)
                o['meta']['entries'].append(e['meta']['link'])

            if args.verbose:
                logging.info("Done extracting entries.")
                logging.info("Extracting feeds...")

            # Feeds
            o['meta']['feed'] = {}
            if 'title' in result['feed']:
                o['meta']['feed']['title'] = result['feed']['title']
            if 'subtitle' in result['feed']:
                o['meta']['feed']['subtitle'] = result['feed']['subtitle']
            if 'generator' in result['feed']:
                o['meta']['feed']['generator'] = result['feed']['generator']
            o['meta']['feed']['links'] = []
            if 'links' in result['feed']:
                for link in result['feed']['links']:
                    l = {}
                    l['rel'] = link['rel']
                    l['href'] = link['href']
                    o['meta']['feed']['links'].append(l)

            if args.verbose:
                logging.info("Done extracting feeds.")
                logging.info("Extracting other data...")

            # Others
            if 'headers' in result:
                o['meta']['headers'] = result['headers']
            if 'href' in result:
                o['meta']['href'] = result['href']
            if 'namespaces' in result:
                o['meta']['namespaces'] = result['namespaces']
            if 'updated' in result:
                o['meta']['updated'] = result['updated']
            if 'encoding' in result:
                o['meta']['encoding'] = result['encoding']
            if 'version' in result:
                o['meta']['version'] = result['version']
            if 'etag' in result:
                o['meta']['etag'] = result['etag']

            if args.verbose:
                logging.info("Done extracting everything!")
                logging.info(json.dumps(o, indent=4, default=str))
                logging.info("Uploading to AIL...")
            # TODO: should url be the content?
            pyail.feed_json_item(url, o['meta'], ailfeedertype, uuid)
