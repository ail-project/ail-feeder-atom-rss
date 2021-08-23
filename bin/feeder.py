import argparse
import configparser
import json
import logging
import sys

import feedparser
import redis
from pyail import PyAIL
from trafilatura import feeds


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
args = parser.parse_args()


# TODO: URLextract
with open("links.txt") as f:
    for link in f.readlines():
        # feedUrls = feeds.find_feed_urls(link)
        feedUrls = []
        feedUrls.append(link.replace('\n', ''))
        for url in feedUrls:
            print(url)
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

            # Entries
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
                e['content'] = ''
                if 'content' in entry:
                    e['content'] = entry['content'][0]['value']
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

            print(json.dumps(o, indent=4, default=str))
            # TODO: should url be the content?
            pyail.feed_json_item(url, o['meta'], ailfeedertype, uuid)