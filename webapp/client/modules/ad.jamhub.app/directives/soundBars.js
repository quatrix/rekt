/**
 * Created by AsafDavidi on 17/12/2015.
 */
'use strict';
/*global $:false */
angular.module('ad.jamhub.app').directive('soundBars', [ function(){
    return {
        restrict: 'AE',
        replace: true,
        scope: {
            isPlaying: '='
        },
        templateUrl : 'modules/ad.jamhub.app/directives/soundBars.html',
        controller: ['$scope', function($scope){

        }],
        link: function postLink(scope, element, attrs) {
        }
    };
}]);