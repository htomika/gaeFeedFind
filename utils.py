from google.appengine.api import users

__author__ = 'style'

from datetime import datetime, date, time
import json
# import socket
from google.appengine.ext import ndb

# from pusher import GoogleAppEngineChannel, AuthenticationError, NotFoundError, AppDisabledOrMessageQuotaError, UnexpectedReturnStatusError


class JSONEncoder(json.JSONEncoder):

    def default(self, o):
        # If this is a key, you might want to grab the actual model.
        # if isinstance(o, ndb.Key):
        #     o = ndb.get(o)

        if isinstance(o, ndb.Model):
            return o.to_dict()
        elif isinstance(o, users.User):
            return str(o.email())
        elif isinstance(o, (datetime, date, time)):
            return str(o)  # Or whatever other date format you're OK with...


# class GAEChannelFix(GoogleAppEngineChannel):
#     def trigger(self, event, data={}, socket_id=None, timeout=socket._GLOBAL_DEFAULT_TIMEOUT):
#         json_data = json.dumps(data, cls=self.pusher.encoder)
#         query_string = self.signed_query(event, json_data, socket_id)
#         signed_path = "%s?%s" % (self.path, query_string)
#         status, resp_content = self.send_request(signed_path, json_data)
#         if status == 202:
#             return True
#         elif status == 401:
#             raise AuthenticationError("Status: 401; Message: %s" % resp_content)
#         elif status == 404:
#             raise NotFoundError("Status: 404; Message: %s" % resp_content)
#         elif status == 403:
#             raise AppDisabledOrMessageQuotaError("Status: 403; Message: %s" % resp_content)
#         else:
#             raise UnexpectedReturnStatusError("Status: %s; Message: %s" % (status, resp_content))



# def obj_to_json(obj):
#     return obj.to_dict()
#
#
# def gql_json_parser(query_obj):
#     result = []
#     for entry in query_obj:
#         result.append(obj_to_json(entry))
#     return result