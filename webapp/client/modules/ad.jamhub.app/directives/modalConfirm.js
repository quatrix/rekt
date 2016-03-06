/**
 * Created by AsafDavidi on 27/12/2015.
 */
'use strict';
angular.module('ad.jamhub.app').controller('modalConfirmCtl',
    ['$scope', '$uibModalInstance', 'options',
        function ($scope, $uibModalInstance , options ) {

            $scope.options = options;

            $scope.ok = function () {
                $uibModalInstance.close('ok');
            };

            $scope.cancel = function () {
                $uibModalInstance.dismiss('cancel');
            };
        }]);