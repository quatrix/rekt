/**
 * Created by AsafDavidi on 20/12/2015.
 */
'use strict';
angular.module('ad.jamhub.app').controller('jhSigninCtrl',
    ['$scope', 'jhAuthSrv', '$location', 'jhApiSrv', function ($scope, auth, $location, dataSrv) {

        var localStorageUserKey = 'user';
        function init(){
            $scope.user = auth.getLocalStorage(localStorageUserKey);
            if($scope.user){
               $location.url('sessions');
            }
        }

        $scope.signIn = function(){
            $scope.user.userName = $scope.user.userName.toLowerCase();
            auth.setLocalStorage(localStorageUserKey, $scope.user);
            init();
        };
        $scope.signOut = function(){
            auth.removeLocalStorageItem(localStorageUserKey);
            init();
        };
        init();

    }]);