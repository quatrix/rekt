/**
 * Created by AsafDavidi on 29/12/2015.
 */
'use strict';
angular.module('ad.jamhub.app').factory('jhUtilsSrv',
    ['$window', function ($window) {

        var exports = {
            secsToTimeStamp: function (secs) {
                var sec_num = parseInt(secs, 10); // don't forget the second param
                var hours = Math.floor(sec_num / 3600);
                var minutes = Math.floor((sec_num - (hours * 3600)) / 60);
                var seconds = sec_num - (hours * 3600) - (minutes * 60);

                if (hours < 10) {
                    hours = '0' + hours;
                }
                if (minutes < 10) {
                    minutes = '0' + minutes;
                }
                if (seconds < 10) {
                    seconds = '0' + seconds;
                }
                var time = hours + ':' + minutes + ':' + seconds;
                return time;
            },
            diluteArray: function (arr, step) {
                for (var i = 0; i < arr.length; i += step) {

                    console.log('delete: ', i);
                    arr.splice(i,1);
                }
                return arr;
            },
            deviceScreenSize: function () {

                var windowWidth = angular.element($window).width(),
                    size;

                if (windowWidth <= 750) {
                    size = 'small';
                } else if (windowWidth <= 1200) {
                    size = 'normal';
                } else {
                    size = 'big';
                }

                return size;

            },
            pixToSeconds: function (duration, totalWidth) {
                return duration / totalWidth * 2;
            }
        };
        return exports;
    }]);
