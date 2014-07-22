#!/usr/bin/python

"""Client script to handle user interface.

Responsible for building web forms, providing get and post handlers, and
maintaining user interface.
"""

import os
# import logging

import webapp2
import jinja2
from google.appengine.api import users

from models import Report


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


application = webapp2.WSGIApplication([
                                          ('/', MainPage),
                                      ], debug=True)