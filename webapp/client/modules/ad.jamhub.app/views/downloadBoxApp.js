'use strict';
angular.module('ad.jamhub.app').controller('jhBoxFilesCtrl',
    ['$scope', 'jhApiSrv', function ($scope, jhApiSrv) {

        $scope.updateData = function () {
            $scope.data = 'text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify({
                    username: $scope.userName,
                    wifi: {
                        ssid: $scope.wifiName,
                        pass: $scope.wifiPassword
                    }
                }));
        };

        $scope.updateBoxWifi = function () {
            $scope.isLoading = true;
            var configJson = {
                username: $scope.userName,
                wifi: {
                    ssid: $scope.wifiName,
                    pass: $scope.wifiPassword
                }
            };

            jhApiSrv.updateBoxConfig(configJson).then(function (response) {
                console.log('updateBoxConfig response:', response);
                $scope.isLoading = false;

                alert('The configuration  update was successful! Boot the Mimosa box and it should connect to:' + $scope.wifiName);
            }, function (err) {
                alert('The configuration  update failed! Please try again');
            });
        };

        $scope.showPassword = false;

        $scope.userName = jhApiSrv.getUser();
        $scope.wifiName = '';
        $scope.wifiPassword = '';
        $scope.fileName = 'mimosa.json';

    }]);