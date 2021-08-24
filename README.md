# ail-feeder-rss-atom

External Atom and RSS feeder for AIL framework.

## Install & Requirements

Install the Python dependencies:

```
pip3 install -U -r requirements.txt
```

This script will install the following Python libraries:

- [pyail](https://github.com/ail-project/PyAIL)
- [trafilatura](https://github.com/adbar/trafilatura)
- [feedparser](https://github.com/kurtmckee/feedparser)
- [newspaper3k](https://github.com/codelucas/newspaper)
- [redis](https://github.com/andymccurdy/redis-py)
- [validators](https://github.com/kvesteri/validators)
- [urlextract](https://github.com/lipoja/URLExtract)

## How to use

1. Create the `ail-feeder-atom-rss.cfg` file in the `/etc` folder. There is a sample which you can use and adapt already in the `/etc` folder. Fill in the necessary details.
2. Start up an instance of the AIL-framework so that the upload can happen.
3. If you want to scan multiple links, add them to the `links.txt` file, separated by newlines.
4. Run the following command with the desired parameters:

```
ail-feeder-atom-rss: python3 bin/feeder.py --help          
usage: feeder.py [-h] [--verbose] [--nocache] [--urlextract] [--link LINK]

optional arguments:
  -h, --help    show this help message and exit
  --verbose     verbose output
  --nocache     disable cache
  --urlextract  extract urls
  --link LINK   single link to be extracted
```