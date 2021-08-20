import json

import feedparser
from trafilatura import feeds


with open("links.txt") as f:
    for link in f.readlines():
        feedUrls = feeds.find_feed_urls(link)
        feedUrls.append(link)
        for url in feedUrls:
            print(url)
            result = feedparser.parse(url)
            with open('output.txt', 'w') as f:
                f.write(json.dumps(result, indent=4, default=str))
                
            o = {}

            # Entries
            o['entries'] = []
            for entry in result['entries']:
                e = {}
                if 'title' in entry:
                    e['title'] = entry['title']
                if 'id' in entry:
                    e['id'] = entry['id']
                e['link'] = entry['link']
                if 'summary' in entry:
                    e['summary'] = entry['summary']
                if 'content' in entry:
                    e['content'] = entry['content'][0]['value']
                if 'authors' in entry:
                    e['authors'] = entry['authors']
                if 'published' in entry:
                    e['published'] = entry['published']
                if 'tags' in entry:
                    e['tags'] = []
                    for tag in entry['tags']:
                        e['tags'].append(tag['term'])
                if 'updated' in entry:
                    e['updated'] = entry['updated']
                if 'comments' in entry:
                    e['comments'] = entry['comments']
                if 'wfw_commentrss' in entry:
                    e['comments-link-rss'] = entry['wfw_commentrss']
                o['entries'].append(e)

            # Feeds
            o['feed'] = {}
            if 'title' in result['feed']:
                o['feed']['title'] = result['feed']['title']
            if 'subtitle' in result['feed']:
                o['feed']['subtitle'] = result['feed']['subtitle']
            if 'generator' in result['feed']:
                o['feed']['generator'] = result['feed']['generator']
            o['feed']['links'] = []
            if 'links' in result['feed']:
                for link in result['feed']['links']:
                    l = {}
                    l['rel'] = link['rel']
                    l['href'] = link['href']
                    o['feed']['links'].append(l)

            # Headers
            o['headers'] = {}
            if 'headers' in result:
                o['headers'] = result['headers']

            # Href
            o['href'] = {}
            if 'href' in result:
                o['href'] = result['href']

            # Namespaces
            o['namespaces'] = {}
            if 'namespaces' in result:
                o['namespaces'] = result['namespaces']

            if 'updated' in result:
                o['updated'] = result['updated']
            if 'encoding' in result:
                o['encoding'] = result['encoding']
            if 'version' in result:
                o['version'] = result['version']
            if 'etag' in result:
                o['etag'] = result['etag']

            print(json.dumps(o, indent=4, default=str))