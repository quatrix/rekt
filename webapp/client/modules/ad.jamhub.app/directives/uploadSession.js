/**
 * Created by AsafDavidi on 24/12/2015.
 */
'use strict';
/*global $:false */
angular.module('ad.jamhub.app').directive('uploadSession', ['jhApiSrv', 'Upload', '$timeout', function (dataSrv, Upload, $timeout) {
    return {
        restrict: 'AE',
        replace: true,
        scope: {
            reloadSessions: '='
        },
        templateUrl: 'modules/ad.jamhub.app/directives/uploadSession.html',
        controller: ['$scope', function ($scope) {


            function getFileName(fullName) {

                console.log('fullName', fullName);
                var name = fullName.substr(0, fullName.indexOf('.mp3'));

                return name;
            }


            $scope.$watch('file', function () {
                $scope.upload($scope.file);
            });

            $scope.upload = function (file) {

                $scope.uploadingFiles = [];
                $scope.uploadFile = [];
                if (file) {
                    Upload.http({
                        url: dataSrv.uploadUrl(getFileName(file.name)),
                        headers : {
                            'Content-Type': file.type
                        },
                        data: file
                    }).then(function (response) {
                        $timeout(function () {
                            $scope.reloadSessions();
                        });
                    }, function (response) {
                        if (response.status > 0) {
                            console.log('upload err: ', response.status);
                        }
                    }, function (evt) {
                        $scope.progress =
                            Math.min(100, parseInt(100.0 * evt.loaded / evt.total));
                    });

                }


            };
        }],
        link: function postLink(scope, element, attrs) {
        }
    };
}]);