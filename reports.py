# -*- coding: utf-8 -*-
#!/usr/bin/python
#
# Copyright 2011 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Contains all the logic to display, schedule, download and return reports."""

import copy
import datetime
import logging
import urllib
#import wsgiref.handlers
from os.path import join

from google.appengine.api import taskqueue
from google.appengine.api import files
from google.appengine.ext import blobstore
from google.appengine.ext import db
import webapp2
from google.appengine.ext.blobstore import BlobInfo
from google.appengine.ext.db import Key
from google.appengine.ext.webapp import blobstore_handlers

import awapi
import constants
import models
import utils

import csv
from xlrd import open_workbook
from xlutils.save import save
from xlutils.copy import copy as xlcopy
import xlwt
from xlwtformatkeep import setOutCell
from constants import XLS_REPORTS
from utils import downloadInBrowser, sendEmailReport, mergeCsvToXls, saveMergedXls

#TODO: ha nem lesz kozvetlen letoltes, vissza kell irni webapp2.RequestHandler-re
class TestCsvCase(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self):
        #Preformatted workbook with styles
        if constants.DEV:
            origdata = open_workbook(r'D:\dev\gae_sdk\adwordsapi_reporting_demo-1.1.0\samples\reportsample2.xls',
                                     formatting_info=1, encoding_override='utf8')
        else:
            origdata = open_workbook(join("./", "samples", "reportsample2.xls"),
                                     formatting_info=1, encoding_override='utf8')
        newWb = xlcopy(origdata)

        reportFileName = "report.xls"

        #CSV processing
        #TODO: itt kell megnyitni a letoltott csv-ket
        if constants.DEV:
            #Campaigns
            mergeCsvToXls(newWb, r'D:\dev\gae_sdk\adwordsapi_reporting_demo-1.1.0\samples\campaign-encsv2.csv', 1)
            #Groups
            mergeCsvToXls(newWb, r'D:\dev\gae_sdk\adwordsapi_reporting_demo-1.1.0\samples\adgroup.csv', 2)
            #Keywords
            mergeCsvToXls(newWb, r'D:\dev\gae_sdk\adwordsapi_reporting_demo-1.1.0\samples\keyword.csv', 3)
            #Ad Texts
            mergeCsvToXls(newWb, r'D:\dev\gae_sdk\adwordsapi_reporting_demo-1.1.0\samples\ad.csv', 4)
        else:
            #Campaigns
            mergeCsvToXls(newWb, join("./", "samples", "campaign-encsv.csv"), 1)
            #Groups
            mergeCsvToXls(newWb, join("./", "samples", "adgroup.csv"), 2)
            #Keywords
            mergeCsvToXls(newWb, join("./", "samples", "keyword.csv"), 3)
            #Ad Texts
            mergeCsvToXls(newWb, join("./", "samples", "ad.csv"), 4)

        #Save Workbook to GAE Files API blobstore
        xlsBlobKey = saveMergedXls(newWb, reportFileName)
        #logging.info('Blob key: %s', xlsBlobKey)
        #Save to db
        app_user = utils.GetAppUser()
        #TODO: client_customer_id-t be kell irni, vagy a nevet, ha megerkezik az api-bol
        report = models.Report(user=app_user.user, blob_key=xlsBlobKey, key_name=reportFileName)
        db.put(report)
        #Send report per e-mail
        sendEmailReport(reportFileName, xlsBlobKey)
        #Download report immediately in browser
        downloadInBrowser(reportFileName, xlsBlobKey)


class AllReportScheduler(webapp2.RequestHandler):
    def get(self):
        """Handle get request."""
        app_user = utils.GetAppUser()
        if app_user.oauth2_token_verified:
            # Load Client instance.
            client = awapi.GetClient(app_user)
            # Fetch account info for all client accounts.
            accounts = awapi.GetAccountInfo(client, app_user)
            #TODO: ManagedCustomerService miatt nem mukodik. ez nem megy test accounts-szal
            #TODO: osszehasonlitani a tarolt ugyfelek enable beallitasaval
            #TODO: ha enabled alapjan megy, akkor kezelni kell az uj ugyfelek beadasat. mehet uj ugyfel mindenkeppen OK

            # all_accounts = awapi.GetAccountInfo(client, app_user)
            # stored_accounts = models.Client.get().filter('enabled =', True)
            # accounts = []
            # for account in all_accounts:
            #     if account.customerId in stored_accounts.client_customer_id:
            #         accounts.append(account)

            #num_account] = len(pb['accounts'])
            reports = XLS_REPORTS.itervalues()
            # Use template to write output to the page.
            #utils.Render(self, 'index.html', pb)

            reports_created = []
            from models import Client
            from datetime import datetime

            for account in accounts:
                #TODO: itt is ossze kell hasonlitani a meglevoket es enabled szerint szurni
                client_customer_id = account['customerId']
                client_name = account['name']
                #newClient = Client(key_name=client_customer_id, client_name=client_name, client_customer_id=client_customer_id)
                newClient = Client.get_or_insert(client_customer_id)
                if newClient.enabled is None:
                    newClient.client_name = client_name
                    newClient.enabled = True
                    newClient.last_call = datetime.now()
                    newClient.put
                elif newClient.enabled == False:
                    continue
                report_request = CreateReportRequest(app_user, client_customer_id, reports, client_name)
                reports_created.append(report_request)
                # Save the created reports.
            db.put(reports_created)
            # Queue tasks to download them.
            for report_request in reports_created:
                taskqueue.add(queue_name='reportdownload',
                              url='/tasks/downloadXlsReport',
                              params={'reportRequest': report_request.key()})
                #self.redirect('/viewReports')

        else:
            self.redirect('/oauth2')


class SwitchEnabledHandler(webapp2.RequestHandler):
    def get(self, resource):
        #client_id = self.request.get('client_id')
        client_id = str(urllib.unquote(resource))
        client = models.Client.get_by_key_name(client_id)
        if client.enabled == True:
            client.enabled = False
        else:
            client.enabled = True
        client.put()
        self.redirect('/viewClients')


class ViewReportHandler(webapp2.RequestHandler):
    """Implements ReportHandler."""

    def get(self):
        """Handle get request."""
        app_user = utils.GetAppUser()
        if not app_user.oauth2_token_verified:
            self.redirect('/oauth2')
        else:
            pb = {}
            pb['user'] = app_user
            # Print out all reports
            completed_reports = db.GqlQuery(
                'SELECT * from ReportRequest where completed_date != NULL '
                'and user = :1 order by completed_date DESC', app_user.user)
            pending_reports = db.GqlQuery(
                'SELECT * from ReportRequest where completed_date = NULL '
                'and user = :1 order by requested_date DESC', app_user.user)
            completed_reports.fetch(constants.MAX_FETCH)
            pending_reports.fetch(constants.MAX_FETCH)
            pb['completedReports'] = completed_reports
            pb['haveCompletedReports'] = completed_reports.count(1)
            pb['pendingReports'] = pending_reports
            pb['havePendingReports'] = pending_reports.count(1)
            utils.Render(self, 'reports.html', pb)


class ViewClientHandler(webapp2.RequestHandler):
    """Implements ReportHandler."""

    def get(self):
        """Handle get request."""
        app_user = utils.GetAppUser()
        if not app_user.oauth2_token_verified:
            self.redirect('/oauth2')
        else:
            from models import Client
            clients = Client.all()
            pb = {}
            pb['user'] = app_user
            # Print out all reports
            pb['clients'] = clients
            utils.Render(self, 'clients.html', pb)


class ScheduleReportHandler(webapp2.RequestHandler):
    """"Handles scheduling a report request."""

    def get(self):
        app_user = utils.GetAppUser()
        if not app_user.oauth2_token_verified:
            self.redirect('/oauth2')
        else:
            pb = {}
            # Schedule the report
            report_type = self.request.get('reportType')
            if report_type not in constants.DEFINED_REPORTS:
                pb['error'] = ('Unknown report type %s not defined in %s'
                               % (report_type, repr(constants.DEFINED_REPORTS)))
                utils.Render(self, 'reports.html', pb)
                return
            elif report_type == 'ALL_TO_XLS':
                pb['error'] = ('This can be only run in auto mode or testing')
                utils.Render(self, 'reports.html', pb)
                return
            else:
                reports_created = []
                for client_customer_id in self.request.get_all('clientCustomerId'):
                    report_request = CreateReportRequest(app_user, client_customer_id,
                                                         report_type, client_name=client_customer_id)
                    #TODO: igazi nevre cserelni
                    reports_created.append(report_request)

                # Save the created reports.
                db.put(reports_created)

                # Queue tasks to download them.
                for report_request in reports_created:
                    taskqueue.add(queue_name='reportdownload',
                                  url='/tasks/downloadReport',
                                  params={'reportRequest': report_request.key()})
                self.redirect('/viewReports')

class ScheduleXlsReportHandler(webapp2.RequestHandler):
    """"Handles scheduling a report request."""

    def get(self):
        app_user = utils.GetAppUser()
        if not app_user.oauth2_token_verified:
            self.redirect('/oauth2')
        else:
            pb = {}
            # Schedule the report
            report_type = self.request.get('reportType')
            #if report_type not in constants.DEFINED_REPORTS:
            if report_type != 'ALL_TO_XLS':
                pb['error'] = ('Unknown report type %s not defined in %s'
                               % (report_type, repr(constants.DEFINED_REPORTS)))
                utils.Render(self, 'reports.html', pb)
                return
            else:
                reports_created = []
                #clients = models.Client.all()
                for client_customer_id in self.request.get_all('clientCustomerId'):
                    client_name = models.Client.get_by_key_name(client_customer_id).client_name
                    report_request = CreateReportRequest(app_user, client_customer_id,
                                                         report_type, client_name=client_name)
                    #TODO: igazi nevre cserelni
                    reports_created.append(report_request)

                # Save the created reports.
                db.put(reports_created)

                # Queue tasks to download them.
                for report_request in reports_created:
                    taskqueue.add(queue_name='reportdownload',
                                  url='/tasks/downloadXlsReport',
                                  params={'reportRequest': report_request.key()})
                self.redirect('/viewReports')


class DownloadReportTaskHandler(webapp2.RequestHandler):
    """Implements a task to download a report via the API."""

    def post(self):
        # Retrieve the ReportRequest
        report_request = models.ReportRequest.get(
            Key(self.request.get('reportRequest')))
        app_user = utils.GetAppUser(report_request.user)
        client_customer_id = report_request.client_customer_id
        client = awapi.GetClient(app_user)
        report = CopyReport(report_request.report_type, client_customer_id)

        # Invoke the API to download it to the blobstore file.
        blob_key = awapi.DownloadReport(client, report, client_customer_id)
        report_request.downloaded_blob_key = BlobInfo.get(blob_key)
        report_request.completed_date = datetime.datetime.now()
        report_request.success = True
        report_request.put()


class DownloadAllReportTaskHandler(webapp2.RequestHandler):
    """Implements a task to download all the needed reports via the API."""

    def post(self):
        # Retrieve the ReportRequest
        report_request = models.ReportRequest.get(
            Key(self.request.get('reportRequest')))
        app_user = utils.GetAppUser(report_request.user)
        client_customer_id = report_request.client_customer_id
        client_name = report_request.client_name
        client = awapi.GetClient(app_user)

        file_names = []
        #file_names = {}
        #blob_keys = []
        for reportiter in XLS_REPORTS.itervalues():
            report = CopyReportAll(reportiter['reportType'], client_customer_id)
            # Invoke the API to download it to the blobstore file.
            #logging.info('Reporting %s', reportiter['reportType'])
            file_name = awapi.DownloadReportFile(client, report, client_customer_id)

            if reportiter['reportType'] == 'CAMPAIGN_PERFORMANCE_REPORT':
                activeSheet = 1
            elif reportiter['reportType'] == 'ADGROUP_PERFORMANCE_REPORT':
                activeSheet = 2
            elif reportiter['reportType'] == 'KEYWORDS_PERFORMANCE_REPORT':
                activeSheet = 3
            elif reportiter['reportType'] == 'AD_PERFORMANCE_REPORT':
                activeSheet = 4
            #logging.info('Activesheet: %s', activeSheet)
            filedict = (file_name, activeSheet)
            #logging.info('File list: %s', filedict)
            file_names.append(filedict)
            #blob_key = files.blobstore.get_blob_key(blob_file_name)
            #blob_keys.append(blob_key)

        # report_request.downloaded_blob_key = BlobInfo.get(blob_keys[0])
        # report_request.adgroups_blob_key = BlobInfo.get(blob_keys[1])
        # report_request.keywords_blob_key = BlobInfo.get(blob_keys[2])
        # report_request.ads_blob_key = BlobInfo.get(blob_keys[3])
        report_request.completed_date = datetime.datetime.now()
        report_request.success = True
        #report_request.put()

        #Preformatted workbook with styles
        if constants.DEV:
            #origdata = open_workbook(r'D:\dev\gae_sdk\adwordsapi_reporting_demo-1.1.0\samples\km-sample.xls',
            #                         formatting_info=1, encoding_override='utf8')
            origdata = open_workbook(r'D:\dev\gae_sdk\adwordsapi_reporting_demo-1.1.0\samples\km-sample.xls',
                                     formatting_info=1, encoding_override='utf8')
        else:
            origdata = open_workbook(join("./", "samples", "km-sample.xls"),
                                     formatting_info=1, encoding_override='utf8')
        newWb = xlcopy(origdata)
        #CSV processing
        #sheet = 0
        for file_name in file_names:
            #sheet += 1
            #if sheet > 4:
            #    logging.warning('More file names than sheets!')
            #    continue
            result = mergeCsvToXls(newWb, file_name[0], file_name[1])


        #Save Workbook to GAE Files API blobstore
        reportFileName = client_customer_id + "-" + client_name + ".xls"
        xlsBlobKey = saveMergedXls(newWb, reportFileName)
        #logging.info('Blob key: %s', xlsBlobKey)
        #Save to db
        report = models.Report(user=app_user.user, blob_key=xlsBlobKey, key_name=reportFileName,
                               client_customer_id=client_customer_id, client_name=client_name, errors=result)
        db.put(report)
        report_request.downloaded_blob_key = xlsBlobKey
        db.put(report_request)
        #Send report per e-mail
        sendEmailReport(reportFileName, xlsBlobKey, client_customer_id, client_name)
        #Download report immediately in browser
        #downloadInBrowser(reportFileName, xlsBlobKey)


class DownloadReportHandler(blobstore_handlers.BlobstoreDownloadHandler):
    """Allows user to download a report from the blobstore."""

    def get(self, resource):
        app_user = utils.GetAppUser()
        if not app_user.oauth2_token_verified:
            self.redirect('/oauth2')
        else:
            resource = str(urllib.unquote(resource))
            blob_info = blobstore.BlobInfo.get(resource)
            self.send_blob(blob_info, save_as=constants.REPORT_FILENAME)


def CopyReport(report_type, client_customer_id):
    """Defensively copies the report and assigns a name tied to clientCustomerId.

  Args:
    report_type: str type of the report we're copying.
    client_customer_id: str customer Id the report is for, for the report name.

  Returns:
    dict a copy of the report with a name populated.
  """
    # Make a defensive copy before assigning a name.
    report = copy.deepcopy(constants.DEFINED_REPORTS[report_type])
    report['reportName'] = ('%s scheduled for %s'
                            % (report_type, client_customer_id))
    return report

def CopyReportAll(report_type, client_customer_id):
    """Defensively copies the report and assigns a name tied to clientCustomerId.

  Args:
    report_type: str type of the report we're copying.
    client_customer_id: str customer Id the report is for, for the report name.

  Returns:
    dict a copy of the report with a name populated.
  """
    # Make a defensive copy before assigning a name.
    report = copy.deepcopy(constants.XLS_REPORTS[report_type])
    report['reportName'] = ('%s scheduled for %s'
                            % (report_type, client_customer_id))
    return report


def CreateReportRequest(app_user, client_customer_id, report_type, client_name):
    """Creates a new ReportRequest.

  Args:
    app_user: AppUser this ReportRequest will be for.
    client_customer_id: Id this report will be downloaded for.
    report_type: str Type of report to download.

  Returns:
    ReportRequest with the provided args.
  """
    report_request = models.ReportRequest(user=app_user.user,
                                          client_customer_id=client_customer_id,
                                          report_type=report_type, client_name=client_name)
    return report_request


if constants.DEBUG:
    logging.getLogger().setLevel(logging.DEBUG)
app = webapp2.WSGIApplication([('/viewReports', ViewReportHandler),
                               ('/viewClients', ViewClientHandler),
                               ('/switchEnabled/([^/]+)?', SwitchEnabledHandler),
                               ('/downloadReport/([^/]+)?', DownloadReportHandler),
                               ('/scheduleReport', ScheduleReportHandler),
                               ('/scheduleXlsReport', ScheduleXlsReportHandler),
                               ('/scheduleAllReport', AllReportScheduler),
                               ('/tasks/downloadReport', DownloadReportTaskHandler),
                               ('/tasks/downloadXlsReport', DownloadAllReportTaskHandler),
                               ('/testcase', TestCsvCase)],
                              debug=constants.DEBUG)