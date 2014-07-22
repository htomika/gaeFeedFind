__author__ = 'style'

from google.appengine.ext import ndb

TIME_FORMAT_STRING = '%b %d, %Y %I:%M:%S %p'


class Report(ndb.Model):
    """Models an individual Report entry."""
    author = ndb.UserProperty()
    url = ndb.StringProperty(indexed=True)
    feeds = ndb.TextProperty()
    date = ndb.DateTimeProperty(auto_now_add=True)
    status = ndb.TextProperty(default='SENT', indexed=True)

    def to_dict(self):
        result = super(Report,self).to_dict()
        result['id'] = self.key.id() #get the key as a string
        return result

    # @property
    # def timestamp(self):
    #     """Property to format a datetime object to string."""
    #     return self.date.strftime(TIME_FORMAT_STRING)

