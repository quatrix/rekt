'use strict';
/*global $:false */
/*global WaveSurfer:false */
angular.module('ad.jamhub.app').directive('slicePlayer', [function () {
    return {
        restrict: 'AE',
        replace: true,
        scope: {
            currentSession: '=',
            slice: '=',
            sliceIndex: '=',
            activeSlice: '='
        },
        templateUrl: 'modules/ad.jamhub.app/directives/slicePlayer.html',
        controller: ['$scope', 'jhApiSrv','$interval', '$document', '$timeout', '$element', 'jhBufferToFileSrv', '$uibModal', '$rootScope', 'jhUtilsSrv',
            function ($scope, jhApiSrv, $interval, $document, $timeout, $element, jhBufferToFileSrv, $uibModal, $rootScope, jhUtilsSrv) {

                var activeUrl = null,
                    progressInterval,
                    trimed = false;


                function trim(segmentDuration, startSecond) {

                    trimed = true;

                    var originalBuffer = $scope.wavesurfer.backend.buffer;
                    var sampleRate = originalBuffer.sampleRate;
                    var trimedBufferSize = parseInt(segmentDuration * sampleRate);
                    var offset = parseInt(startSecond * sampleRate);

                    var trimedSegment = $scope.wavesurfer.backend.ac.createBuffer(
                        originalBuffer.numberOfChannels,
                        trimedBufferSize,
                        sampleRate
                    );

                    for (var i = 0; i < originalBuffer.numberOfChannels; i++) {

                        var chanData = originalBuffer.getChannelData(i);
                        var segmentChanData = trimedSegment.getChannelData(i);

                        for (var j = 0, len = segmentChanData.length; j < len; j++) {
                            segmentChanData[j] = chanData[j + offset];
                        }
                    }

                    $scope.wavesurfer.empty();
                    $scope.wavesurfer.createBackend();
                    $scope.wavesurfer.backend.load(trimedSegment);
                    $scope.wavesurfer.drawBuffer();
                    $scope.wavesurfer.fireEvent('ready');

                }

                function startProgressInterval() {
                    progressInterval = $interval(function () {
                        $scope.currentTime = $scope.wavesurfer.getCurrentTime();
                    }, 100);
                }

                function downloadSlice(fileName) {
                    jhBufferToFileSrv.toMp3($scope.wavesurfer.backend.buffer, fileName);
                }

                function deleteSlice() {
                    console.log('deleteSlice');


                    $scope.currentSession.slices.splice($scope.sliceIndex,1);
                    jhApiSrv.putSession($scope.currentSession.id, {'slices': $scope.currentSession.slices}).then(function (response) {
                        //$scope.$apply();
                    });
                }

                $scope.waveOptions = {
                    waveColor: '#606060',
                    progressColor: '#606060',
                    normalize: true,
                    hideScrollbar: true,
                    skipLength: 15,
                    height: 80,
                    cursorColor: '#2A9FD6'
                };

                $scope.paused = true;

                $scope.$on('wavesurferInit', function (e, wavesurfer) {
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

                    $scope.wavesurfer.on('loading', function (prc) {

                        if ($scope.loadingPrc !== prc) {
                            $scope.loadingPrc = prc;
                            $scope.$apply();
                        }
                    });


                    $scope.wavesurfer.on('ready', function () {

                        var sliceDuration = $scope.slice.end - $scope.slice.start;

                        if (!trimed) {
                            trim(sliceDuration, $scope.slice.start);
                        } else {
                            var timeline = WaveSurfer.Timeline;
                            timeline.init({
                                wavesurfer: $scope.wavesurfer,
                                container: '#slice-wave-timeline' + $scope.sliceIndex,
                            });

                        }


                    });

                });

                $scope.secsToTimeStamp = function (seconds) {
                    return jhUtilsSrv.secsToTimeStamp(seconds);
                };

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

                $scope.isActive = function () {
                    if (!$scope.activeSlice) {
                        return;
                    }
                    if ($scope.activeSlice[0] === $scope.slice.start && $scope.activeSlice[1] === $scope.slice.end) {
                        return true;
                    }
                    return false;
                };

                $scope.openSaveSliceModal = function () {

                    $rootScope.keybordIsBusy = true;

                    var modalInstance = $uibModal.open({
                        animation: true,
                        templateUrl: 'modules/ad.jamhub.app/directives/modalSaveSlice.html',
                        controller: 'modalSaveSliceCtl',
                        backdrop: true,
                        resolve: {}
                    });

                    modalInstance.result.then(function (result) {
                        downloadSlice(result);
                        $rootScope.keybordIsBusy = false;
                    }, function () {
                        console.log('Modal dismissed at: ' + new Date());
                        $rootScope.keybordIsBusy = false;
                    });

                };

                $scope.openConfirmModal = function () {

                    var modalInstance = $uibModal.open({
                        animation: true,
                        templateUrl: 'modules/ad.jamhub.app/directives/modalConfirm.html',
                        controller: 'modalConfirmCtl',
                        backdrop: true,
                        resolve: {
                            options: {
                                title: 'Delete Slice',
                                message: 'Are you sure you want to delete this slice',
                                action: 'Delete'
                            }
                        }
                    });

                    modalInstance.result.then(function (result) {
                        console.log('modalInstance.result', result);
                        if ('Delete') {
                            deleteSlice();
                        }
                    }, function () {
                        console.log('Modal dismissed at: ' + new Date());
                    });

                };

                $scope.$on('$destroy', function () {
                    $scope.wavesurfer.destroy();
                });

            }],
        link: function postLink(scope, element, attrs) {

        }
    };
}]);