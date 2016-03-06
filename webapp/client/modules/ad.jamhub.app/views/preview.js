/**
 * Created by AsafDavidi on 27/12/2015.
 */
'use strict';
angular.module('ad.jamhub.app').controller('jhPreviewCtrl',
    ['$scope', '$location',  'jhApiSrv', function ($scope, $location, jhApiSrv) {

        console.log('jhPreviewCtrl', $location.search().id);


        function init(){

            jhApiSrv.getOneSessions(id, user).then(function (session) {
                $scope.currentSession = session[0];
            });

        }

        $scope.showNoSlicesMessage = function () {
            if (!$scope.sessions) {
                return true;
            }

            if ((!$scope.currentSession.slices.length) && !$scope.isLoading) {
                return true;
            } else {
                return false;
            }
        };

        var id = $location.search().id,
            user = $location.search().user;

        if(id && user){
            init();
        }

    }]);
