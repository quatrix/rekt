/**
 * Created by asafd on 5/22/15.
 */
'use strict';
/*global $:false */
angular.module('ad.jamhub.app').directive('navbar', [ 'jhAuthSrv', '$location', function(auth, $location){
    return {
        restrict: 'AE',
        replace: true,
        scope: {
            isPreview:'='
        },
        templateUrl : 'modules/ad.jamhub.app/directives/navbar.html',
        controller: ['$scope', function($scope){
            $scope.signOut = function(){
                auth.removeLocalStorageItem('user');
                $location.url('signin');
            };
            $scope.user = auth.getLocalStorage('user');
        }],
        link: function postLink(scope, element, attrs) {

        }
    };
}]);