from google.appengine.api import users
from parse_api_messages import ReportResponseMessage
# from parser import parsepage

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

    # def to_dict(self):
    #     result = super(Report,self).to_dict()
    #     result['id'] = self.key.id() #get the key as a string
    #     return result

    @property
    def timestamp(self):
        """Property to format a datetime object to string."""
        return self.date.strftime(TIME_FORMAT_STRING)

    def to_message(self):
        """Turns the Report entity into a ProtoRPC object.

        This is necessary so the entity can be returned in an API request.

        Returns:
            An instance of ReportResponseMessage with the ID set to the datastore
            ID of the current entity and status set to SENT.
        """
        return ReportResponseMessage(id=self.key.id(),
                                     author=self.author.email(),
                                     url=self.url,
                                     feeds=self.feeds,
                                     status=self.status,
                                     date=self.timestamp)

    @classmethod
    def put_from_message(cls, message):
        """Gets the current user and inserts a report.

        Args:
            message: A ReportRequestMessage instance to be inserted.

        Returns:
            The Report entity that was inserted.
        """
        current_user = users.get_current_user()
        entity = cls(
            author=current_user,
            url=message.url)
        entity.put()
        return entity

    @classmethod
    def query_current_user(cls):
        """Creates a query for the reports of the current user.

        Returns:
            An ndb.Query object bound to the current user. This can be used
            to filter for other properties or order by them.
        """
        current_user = users.get_current_user()
        return cls.query(cls.author == current_user)

    # @classmethod
    # def parse_page(self):
    #     return deferred.defer(parsepage, self, _countdown=30, _queue="parsequeue")