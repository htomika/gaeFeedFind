"""Hello World API implemented using Google Cloud Endpoints.

Defined here are the ProtoRPC messages needed to define Schemas for methods
as well as those methods defined in an API.
"""
from google.appengine.api import users
import endpoints
from google.appengine.ext import deferred
from protorpc import messages
from protorpc import message_types
from protorpc import remote
from models import Report
from parse_api_messages import ReportResponseMessage, ReportRequestMessage, ReportsListRequest, ReportsListResponse
from constants import CLIENT_ID
from parser_functions import parsepage
import logging

package = 'FeedFind'


@endpoints.api(name='feedfind', version='v1',
               description='Feed Finder API',
               allowed_client_ids=[CLIENT_ID, endpoints.API_EXPLORER_CLIENT_ID],
               # audiences=[CLIENT_ID],
               scopes=[endpoints.EMAIL_SCOPE]
               )
class FeedFindApi(remote.Service):
    """FeedFind API v1."""

    @endpoints.method(ReportsListRequest, ReportsListResponse,
                      path='reports', http_method='GET',
                      name='reports.list')
    def reports_list(self, request):
        """Exposes an API endpoint to query for reports for the current user.

        Args:
            request: An instance of ReportsListRequest parsed from the API
                request.

        Returns:
            An instance of ReportsListResponse containing the reports for the
            current user returned in the query. If the API request specifies an
            order of WHEN (the default), the results are ordered by time from
            most recent to least recent. If the API request specifies an order
            of TEXT, the results are ordered by the string value of the reports.
        """
        query = Report.query_current_user()
        if request.order == ReportsListRequest.Order.TEXT:
            query = query.order(Report.url)
        elif request.order == ReportsListRequest.Order.WHEN:
            query = query.order(-Report.date)
        items = [entity.to_message() for entity in query.fetch(request.limit)]
        return ReportsListResponse(items=items)

    @endpoints.method(ReportRequestMessage, ReportResponseMessage,
                      path='reports', http_method='POST',
                      name='reports.insert')
    def reports_insert(self, request):
        """Exposes an API endpoint to insert a report for the current user.

        Args:
            request: An instance of ReportRequestMessage parsed from the API
                request.

        Returns:
            An instance of ReportResponseMessage containing the report inserted,
            the time the report was inserted and the ID of the report.
        """
        current_user = users.get_current_user()
        if not current_user:
            logging.log(logging.INFO, current_user)
            # raise endpoints.ForbiddenException()
        entity = Report.put_from_message(request)
        deferred.defer(parsepage, entity, _countdown=30, _queue="parsequeue")
        return entity.to_message()

    ID_RESOURCE = endpoints.ResourceContainer(
        message_types.VoidMessage,
        id=messages.IntegerField(1, variant=messages.Variant.INT32))

    @endpoints.method(ID_RESOURCE, ReportResponseMessage,
                      path='report/{id}', http_method='GET',
                      name='reports.getReport')
    def report_get(self, request):
        item = Report.get_by_id(request.id)
        current_user = users.get_current_user()
        if item and item.author == current_user.author:
            return item.to_message()
        else:
            raise endpoints.NotFoundException('Report %s not found.' %
                                              (request.id,))


# from raven import Client
# from raven.middleware import Sentry
# from constants import SENTRY
# from raven_appengine import register_transport
#
# register_transport()

APPLICATION = endpoints.api_server([FeedFindApi],
                                   restricted=False)

# APPLICATION = Sentry(
#     pre_app,
#     Client(SENTRY)
# )