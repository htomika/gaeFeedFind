__author__ = 'style'

import endpoints
from protorpc import messages
from protorpc import message_types
from protorpc import remote


class ReportsListRequest(messages.Message):
    """ProtoRPC message definition to represent a scores query."""
    limit = messages.IntegerField(1, default=10)

    class Order(messages.Enum):
        WHEN = 1
        TEXT = 2
    order = messages.EnumField(Order, 2, default=Order.WHEN)


class ReportRequestMessage(messages.Message):
    """ProtoRPC message definition to represent a score to be inserted."""
    url = messages.StringField(1, required=True)


class ReportResponseMessage(messages.Message):
    """Greeting that stores a message."""
    id = messages.IntegerField(1)
    author = messages.StringField(2)
    url = messages.StringField(3)
    feeds = messages.StringField(4)
    date = messages.StringField(5)
    status = messages.StringField(6)


class ReportsListResponse(messages.Message):
    """ProtoRPC message definition to represent a list of stored scores."""
    items = messages.MessageField(ReportResponseMessage, 1, repeated=True)


# class ReportMessageCollection(messages.Message):
#     """Collection of Greetings."""
#     items = messages.MessageField(ReportResponseMessage, 1, repeated=True)