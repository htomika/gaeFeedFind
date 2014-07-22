#!/usr/bin/python

"""Client script to handle user interface.

Responsible for building web forms, providing get and post handlers, and
maintaining user interface.
"""
import logging
from google.appengine.ext import deferred

import os
# import logging

import webapp2
from webapp2_extras import json
import jinja2
from google.appengine.api import users

from models import Report
from parser_functions import parsepage
from utils import JSONEncoder


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


class MainPage(webapp2.RequestHandler):
    def get(self):
        # Checks for active Google account session
        user = users.get_current_user()

        if user:
            reports_query = Report.query(Report.author == user).order(-Report.date)
            reports = reports_query.fetch(10)
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        template_values = {
            'reports': reports,
            'url': url,
            'url_linktext': url_linktext,
        }

        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))


class ScheduleReport(webapp2.RequestHandler):
    def post(self):
        user = users.get_current_user()
        if user:
            data = json.decode(self.request.body)
            # logging.log(logging.INFO, data)
            url = data['url']
            if url[:3] != 'http':
                url = 'http://' + url
            report = Report(
                author=user,
                url=url,
                status='SENT'
            )
            key = report.put()
            deferred.defer(parsepage, key, _countdown=30, _queue="parsequeue")
            result = {
                'result': JSONEncoder().encode(key.get()),
            }
            self.response.headers['Content-Type'] = 'application/json'
            self.response.write(json.encode(result))


class Data(webapp2.RequestHandler):
    def post(self):
        user = users.get_current_user()
        if user:
            # data = json.loads(self.request.body)
            reports = Report.query(Report.author == user).fetch()

            # json_query_data = JSONEncoder().encode(reports)
            result = {
                'result': reports,
                'total': len(reports)
            }
            self.response.headers['Content-Type'] = 'application/json'
            self.response.write(JSONEncoder().encode(result))


application = webapp2.WSGIApplication([
                                          ('/', MainPage),
                                          ('/scheduleReport', ScheduleReport),
                                          ('/data', Data)
                                      ], debug=True)