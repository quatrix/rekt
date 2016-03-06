/**
 * Created by AsafDavidi on 13/12/2015.
 */
'use strict';
/*global $:false */
angular.module('ad.jamhub.app').directive('sessionsTable', [function () {
    return {
        restrict: 'AE',
        replace: true,
        scope: {
            options: '='
        },
        templateUrl: 'modules/ad.jamhub.app/directives/sessionsTable.html',
        controller: ['$scope', 'moment', function ($scope, Moment) {
            $scope.sessionName = function (sessionName, sessionId) {
                if (sessionName) {
                    return sessionName;
                } else {
                    return new Moment(parseInt(sessionId * 1000)).format('llll');
                }
            };

        }],
        link: function postLink(scope, element, attrs) {

        }
    };
}]);