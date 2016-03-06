'use strict';
angular.module('ad.jamhub.app').controller('modalSaveSliceCtl',
    ['$scope', '$uibModalInstance',
        function ($scope, $uibModalInstance) {

            $scope.ok = function () {
                $uibModalInstance.close($scope.sliceName);
            };

            $scope.cancel = function () {
                $uibModalInstance.dismiss('cancel');
            };
        }]);