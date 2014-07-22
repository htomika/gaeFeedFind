/**
 * Created by style on 22/07/14.
 */

// https://github.com/Sfeir/hello-world-oauth2-endpoints-angularjs/tree/master/src/main/webapp/js
//
var app = angular.module('main', ['ngTable']);
//var app = angular.module('main', ['ngTable', 'doowb.angular-pusher'])
//app.config(['PusherServiceProvider',
//    function (PusherServiceProvider) {
//        PusherServiceProvider
//            .setToken('b4646cbdcd6f65dae3f8')
//            .setOptions({})
//    }]);
//app.controller('ParserCtrl', function ($scope, ngTableParams, Pusher, $window) {
app.controller('ParserCtrl', function ($scope, ngTableParams, $http) {
        $scope.is_backend_ready = true;
        $scope.reports = [];


        $scope.addUrl = function () {
            $http.post('/scheduleReport', {url: $scope.newurl}).success(function (data) {
                $scope.reports = [];
                $scope.reports.push(data.result);
                $scope.total = data.total;
                $scope.apply();
            });
        };

        $scope.reportList = function () {
            $http.post('/data', {}).success(function (data) {
                $scope.reports = data.result;
                $scope.total = data.total;
                $scope.apply();
            });
        };

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

    }
);
