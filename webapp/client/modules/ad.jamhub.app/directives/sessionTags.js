'use strict';
angular.module('ad.jamhub.app').directive('sessionTags', [ function(){
    return {
        restrict: 'AE',
        replace: true,
        scope: {
            saveSessionTags : '=',
            currentSession: '='
        },
        templateUrl : 'modules/ad.jamhub.app/directives/sessionTags.html',
        controller: ['$scope', 'jhApiSrv', function($scope, jhApiSrv){

            $scope.loadTags = function(query) {
                return jhApiSrv.getAllTags();
            };

            $scope.saveTags = function(){
                $scope.saveSessionTags($scope.tags);
            };

            $scope.$watch('currentSession', function(){
                if($scope.currentSession && $scope.currentSession.tags){
                    $scope.tags = $scope.currentSession.tags;

                }else{
                    $scope.tags = [];
                }
            });

        }],
        link: function postLink(scope, element, attrs) {
        }
    };
}]);