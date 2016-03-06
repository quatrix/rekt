'use strict';
/*global $:false */
/*global WaveSurfer:false */
angular.module('ad.jamhub.app').directive('sessionPlayer', [function () {
    return {
        restrict: 'AE',
        replace: true,
        scope: {
            currentSession: '=',
            activeSlice: '=',
            updateSlices: '='
        },
        templateUrl: 'modules/ad.jamhub.app/directives/sessionPlayer.html',
        controller: ['$scope', '$interval', 'jhApiSrv', '$document', '$timeout', '$element', 'jhUtilsSrv', '$rootScope', 'jhUtilsSrv',
            function ($scope, $interval, jhApiSrv, $document, $timeout, $element, jhUtilsSrv, $rootScope, utils) {

                var activeUrl = null,
                    progressInterval,
                    slices = [],
                    regions = [];


                function init(){
                    $scope.waveOptions = {
                        waveColor: '#FFC107',
                        progressColor: '#FFC107',
                        normalize: true,
                        hideScrollbar: true,
                        skipLength: 15,
                        height: 200,
                        cursorColor: '#fff',
                        markerColors: ['#ff0000', '#B51EE9'],
                        sliceColor: 'rgba(255,255,255,.2)',
                        activeSliceColor: 'rgba(255,255,255,.3)',
                    };
                    $scope.paused = true;
                    $scope.currentTime = 0;
                }

                function startProgressInterval() {
                    progressInterval = $interval(function () {
                        $scope.currentTime = $scope.wavesurfer.getCurrentTime();
                    }, 100);
                }

                function onSliceClick(slice) {
                    $scope.currentSlice = slice;
                    $timeout(function () {
                        var seekPrc = slice.start / $scope.wavesurfer.getDuration();
                        $scope.wavesurfer.seekTo(seekPrc);
                    }, 10);
                    $scope.$apply();
                    $scope.updateSlices();
                }

                function documentKeyDown($event) {


                    if($rootScope.keybordIsBusy){
                        return;
                    }

                    if ($event.keyCode === 32 ) { // spacebar
                        $event.preventDefault();
                        $scope.wavesurfer.playPause();
                    }else if($event.keyCode === 190){// >
                        $scope.skipToMarker('next');
                    }else if($event.keyCode === 188){ // <
                        $scope.skipToMarker('prev');
                    }


                }

                function setMarkers() {
                    var markerWidth = utils.pixToSeconds($scope.wavesurfer.getDuration(), $element.outerWidth());

                    _.each($scope.currentSession.markers, function (marker) {
                        regions.push($scope.wavesurfer.addRegion({
                            start: marker.offset,
                            end: marker.offset + markerWidth,
                            color: $scope.waveOptions.markerColors[marker.pedal_id],
                            resize: false,
                            drag: false
                        }));
                    });
                }

                function removeMarkersAndSlices() {
                    _.each(regions, function (region) {
                        region.remove();
                    });
                    regions = [];
                    _.each(slices, function (slice) {
                        slice.remove();
                    });
                    slices = [];
                }

                function initTimeline() {
                    var timeline = WaveSurfer.Timeline;

                    var timeInterval,
                        deviceScreenSize = utils.deviceScreenSize(),
                        timelineSegmentsCount;

                    if (deviceScreenSize === 'small') {
                        timelineSegmentsCount = 10;
                    } else if (deviceScreenSize === 'normal') {
                        timelineSegmentsCount = 20;
                    } else {
                        timelineSegmentsCount = 30;
                    }
                    timeInterval = parseInt($scope.wavesurfer.getDuration() / timelineSegmentsCount);

                    timeline.init({
                        wavesurfer: $scope.wavesurfer,
                        container: '#session-wave-timeline',
                        primaryColor: '#fff',
                        primaryFontColor: '#fff',
                        secondaryColor: '#a8a8a8',
                        secondaryFontColor: '#a8a8a8',
                        timeInterval: timeInterval,
                        primaryLabelInterval: 2,
                        secondaryLabelInterval: 1
                    });
                }

                function redraw() {
                    removeMarkersAndSlices();

                    setMarkers();

                    _.each($scope.currentSession.slices, function (slice) {
                        $scope.addSlice(slice);
                    });

                    $scope.maxZoom = parseInt($scope.wavesurfer.getDuration() / 100);

                    initTimeline();
                }

                $scope.addSlice = function (sessionSlice) {

                    var sliceWidth,
                        startSec,
                        slice;

                    if (sessionSlice) {
                        sliceWidth = sessionSlice.end - sessionSlice.start;
                        startSec = sessionSlice.start;
                    } else {
                        sliceWidth = utils.pixToSeconds($scope.wavesurfer.getDuration(), $element.outerWidth()) * 40;
                        startSec = $scope.wavesurfer.getCurrentTime();
                    }
                    slice = $scope.wavesurfer.addRegion({
                        start: startSec,
                        end: startSec + sliceWidth,
                        color: $scope.waveOptions.sliceColor
                    });

                    slice.on('click', function (ev) {
                        onSliceClick(slice);
                    });

                    slice.on('mouseenter', function (ev) {
                        $scope.activeSlice = [slice.start, slice.end];
                        $scope.$apply();
                    });

                    slice.on('mouseleave', function (ev) {
                        $scope.activeSlice = [-1, -1];
                        $scope.$apply();
                    });

                    slices.push(slice);
                };

                $scope.$on('wavesurferInit', function (e, wavesurfer) {

                    if ($scope.wavesurfer) {
                        $scope.wavesurfer.destroy();
                    }

                    $scope.wavesurfer = wavesurfer;

                    $scope.wavesurfer.on('play', function () {
                        $scope.paused = false;
                        startProgressInterval();
                    });

                    $scope.wavesurfer.on('pause', function () {
                        $scope.paused = true;
                        $interval.cancel(progressInterval);
                    });

                    $scope.wavesurfer.on('finish', function () {
                        $scope.paused = true;
                        $scope.wavesurfer.seekTo(0);
                        $scope.$apply();
                    });

                    $scope.wavesurfer.on('redraw', function (peaks, width) {


                        if (peaks.length) {
                            jhApiSrv.putSession($scope.currentSession.id, {'peaks': peaks}).then(function (response) {
                            });
                        }
                        redraw();
                    });

                    $scope.wavesurfer.on('loading', function (prc) {
                        if ($scope.loadingPrc !== prc) {
                            $scope.loadingPrc = prc;
                            $scope.$apply();
                        }
                    });

                    $scope.wavesurfer.on('zoom', function () {
                        redraw();
                    });

                    $scope.wavesurfer.on('ready', function () {
                        //redraw();
                    });
                });

                $scope.play = function (url) {
                    if (!$scope.wavesurfer) {
                        return;
                    }

                    activeUrl = url;

                    $scope.wavesurfer.once('ready', function () {
                        $scope.wavesurfer.play();
                        $scope.$apply();
                    });

                    $scope.wavesurfer.load(activeUrl);
                };

                $scope.isPlaying = function (url) {
                    return url === activeUrl;
                };

                $scope.saveSlices = function (clearSlices) {
                    var slicesToSave = [];
                    if (clearSlices) {
                        _.each(slices, function (slice) {
                            slice.remove();
                        });
                        slices = [];
                    } else {
                        _.each(slices, function (slice) {
                            slicesToSave.push({
                                start: slice.start,
                                end: slice.end
                            });
                        });
                    }

                    jhApiSrv.setSlices($scope.currentSession.id, {'slices': slicesToSave}).then(function (response) {
                        console.log('setSlices', response);
                        jhApiSrv.getOneSessions($scope.currentSession.id).then(function (response) {
                            $scope.currentSession = response[0];
                        });
                    });
                };

                $scope.secsToTimeStamp = function (secs) {
                    return jhUtilsSrv.secsToTimeStamp(secs);
                };

                $scope.skipToMarker = function (direction) {

                    var currentTime = $scope.wavesurfer.getCurrentTime(),
                        markers = $scope.currentSession.markers,
                        nextmarkerIndex,
                        i;

                    if (direction === 'next') {

                        nextmarkerIndex =  markers.length -1 ;
                        for (i in markers) {
                            if (parseInt(markers[i].offset) > parseInt(currentTime)) {
                                nextmarkerIndex = parseInt(i);
                                break;
                            }
                        }

                        $scope.wavesurfer.skipForward(
                            markers[nextmarkerIndex].offset - currentTime
                        );

                    } else {
                        nextmarkerIndex =  0;
                        for (i in markers) {
                            if (parseInt(markers[i].offset) >= parseInt(currentTime)) {
                                nextmarkerIndex = parseInt(i);
                                break;
                            }
                        }

                        $scope.wavesurfer.skipBackward(
                            markers[nextmarkerIndex-1] ? currentTime - markers[nextmarkerIndex-1].offset : currentTime
                        );

                    }

                };

                $document.on('keydown', documentKeyDown);

                $scope.$on('$destroy', function () {
                    $document.off('keydown', documentKeyDown);
                    $scope.wavesurfer.destroy();
                });

                $scope.$watch('currentSession', function (newValue, oldValue) {
                    if (!newValue || !oldValue || newValue.id === oldValue.id) {
                        return;
                    }
                    for(var i=0; i<3;i++) {
                        $scope.currentSession.peaks = utils.diluteArray($scope.currentSession.peaks, 2);
                    }
                    removeMarkersAndSlices();
                });

                $scope.$watch('activeSlice', function () {
                    _.each(slices, function (slice) {
                        var color;
                        if ($scope.activeSlice[0] === slice.start && $scope.activeSlice[1] === slice.end) {
                            color = $scope.waveOptions.activeSliceColor;
                        } else {
                            color = $scope.waveOptions.sliceColor;
                        }

                        slice.update({
                            color: color
                        });

                    });
                });

                init();

            }],
        link: function postLink(scope, element, attrs) {

            document.querySelector('#sessionZoomSlider').oninput = function () {
                scope.wavesurfer.zoom(Number(this.value));
            };

            scope.$on('updateSlices', function (event) {
                scope.saveSlices();
            });

            scope.$on('clearSlices', function (event) {
                scope.saveSlices(true);
            });

            scope.$on('addSlice', function (event) {
                scope.addSlice();
            });
        }
    };
}]);