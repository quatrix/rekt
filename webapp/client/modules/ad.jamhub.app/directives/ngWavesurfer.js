/**
 * Created by AsafDavidi on 15/12/2015.
 */
'use strict';
/*global WaveSurfer:false */

angular.module('ad.jamhub.app').directive('ngWavesurfer', [ function(){
    return {
        restrict: 'AE',
        replace: true,
        scope: {
            url: '@',
            windowWidth: '='
        },
        controller: ['$scope', function($scope){

        }],
        link: function postLink($scope, $element, $attrs) {
            $element.css('display', 'block');

            var options = angular.extend({ container: $element[0]}, $attrs);
            var wavesurfer = WaveSurfer.create(options);


            $scope.$watch('url', function(){
                if ($attrs.url) {
                    if($attrs.peaks){
                        wavesurfer.load($attrs.url, JSON.parse($attrs.peaks));
                    }else{
                        wavesurfer.load($attrs.url,null);
                    }
                }
            });
            $scope.$watch('windowWidth', function(){
                //wavesurfer.empty();
                //wavesurfer.drawBuffer();
            });
            $scope.$emit('wavesurferInit', wavesurfer);
        }
    };
}]);