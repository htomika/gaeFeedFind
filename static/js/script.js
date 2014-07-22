/**
 * Created by style on 22/07/14.
 */

// https://github.com/Sfeir/hello-world-oauth2-endpoints-angularjs/tree/master/src/main/webapp/js
//
var app = angular.module('main', ['ngTable'])
//var app = angular.module('main', ['ngTable', 'doowb.angular-pusher'])
//app.config(['PusherServiceProvider',
//    function (PusherServiceProvider) {
//        PusherServiceProvider
//            .setToken('b4646cbdcd6f65dae3f8')
//            .setOptions({})
//    }]);
//app.controller('ParserCtrl', function ($scope, ngTableParams, Pusher, $window) {
app.controller('ParserCtrl', function ($scope, ngTableParams, $window) {
        $scope.is_backend_ready = false;
        $scope.reports = [];

        $scope.load_feedfind_lib = function () {
            gapi.client.load('feedfind', 'v1', function () {
                $scope.is_backend_ready = true;
                $scope.reportList();
            }, '/_ah/api');
        };

        $scope.addUrl = function () {
            message = {
                "url": $scope.newurl
            };
            gapi.client.feedfind.reports.insert(message).execute();
        }

        $scope.reportList = function () {
            gapi.client.feedfind.reports.list().execute(function (resp) {
                $scope.reports = resp.items;
                $scope.$apply();
            });
        }
        $scope.total = function () {
            return $scope.reports.length
        };

        $scope.tableParams = new ngTableParams({
            page: 1,            // show first page
            count: 10,          // count per page
            sorting: {
                date: 'desc'     // initial sorting
            }
        }, {
            total: $scope.total()           // length of data
        });

//        Pusher.subscribe('reports', 'update', function (item) {
//            // an item was updated. find it in our list and update it.
//            for (var i = 0; i < $scope.reports.length; i++) {
//                if ($scope.reports[i].id === item.id) {
//                    $scope.reports[i] = item;
//                    break;
//                }
//            }
//        });

        angular.element(document).ready(function () {
            $scope.$apply($scope.load_feedfind_lib);
        });
    }
);
