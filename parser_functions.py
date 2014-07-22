__author__ = 'style'

from BeautifulSoup import BeautifulSoup
from google.appengine.api import urlfetch
# import pusher
# import logging
# from utils import JSONEncoder, GAEChannelFix
# from utils import JSONEncoder
# from constants import PUSHER


def parsepage(k):
    report = k.get()
    report.status = 'STARTED'
    report.put()
    error = False
    try:
        fetched_url = urlfetch.fetch(report.url)
    except urlfetch.InvalidURLError as ex:
        error = "Invalid URL: %s" % ex
    except urlfetch.DownloadError as ex:
        error = "Download error: %s" % ex
    except Exception as ex:
        error = "Unexpected error: %s" % ex
        # raise

    if not error and fetched_url.status_code == 200:
        report.feeds = unicode(detect_feeds_in_HTML(fetched_url.content))
        report.status = 'DONE'
    else:
        status = error if error else fetched_url.status_code
        report.feeds = unicode({"error": "URL fetch fail: %s" % status})
        report.status = 'FAIL'
    report.put()
    # p = pusher.Pusher(
    #     app_id=PUSHER['app_id'],
    #     key=PUSHER['key'],
    #     secret=PUSHER['secret']
    # )
    # pusher.channel_type = GAEChannelFix
    # logging.log(logging.INFO, "report: %s" % report.to_dict())
    # p['reports'].trigger('update', JSONEncoder().encode(report.to_dict()))


def detect_feeds_in_HTML(input):
    """ examines an opened url with HTML for referenced feeds.

    This is achieved by detecting all ``link`` tags with appropriate types that reference a feed in HTML.

    :param input: an arbitrary opened urlfetch content
    :type input: an opened url (e.g. urlfetch.fetch(url))
    :return: a dict with atom and rss links ``{atom(list), rss(list)}``
    :rtype: ``dict(atom(list), rss(list))``
    """

    feeds = {'atom': [], 'rss':[]}
    # get the textual data (the HTML) from the input
    html = BeautifulSoup(input)
    # find all links that have an "application/atom+xml" type
    atom_urls = html.findAll("link", type="application/atom+xml")
    # find all links that have an "application/atom+xml" type
    rss_urls = html.findAll("link", type="application/rss+xml")
    # TODO: not standard links
    # extract URL and type
    feeds['atom'] = [link.get("href", None) for link in atom_urls] if atom_urls else []
    feeds['rss'] = [link.get("href", None) for link in rss_urls] if rss_urls else []

    return feeds