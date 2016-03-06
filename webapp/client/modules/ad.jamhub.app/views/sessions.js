'use strict';
/*global $:false */
angular.module('ad.jamhub.app').controller('jhSessionsCtrl',
    ['$scope', 'jhApiSrv', 'jhUtilsSrv', function ($scope, jhApiSrv, jhUtilsSrv) {

        function init() {
            $scope.sessionOptions = {
                delete: deleteSession,
                setSessionName: setSessionName,
            };
            jhApiSrv.getSessions().then(function (sessions) {
                if (sessions.length) {

                    sessions = _.sortBy(sessions, function(o) {
                        return o.date;
                    });

                    $scope.sessions = sessions.slice().reverse();
                    $scope.currentSessionId = $scope.sessions[0].id;
                    jhApiSrv.updateAllTags($scope.sessions);
                    update();
                } else {
                    console.log('No sessions');
                    //alert('No sessions ');
                }
            });
        }

        function getSessionById(id) {
            for (var i = 0; i < $scope.sessions.length; i++) {
                if ($scope.sessions[i].id === id) {
                    return $scope.sessions[i];
                }
            }
        }

        function update() {
            $scope.sessionsTableOptions = {
                sessions: $scope.sessions,
                currentSessionId: $scope.currentSessionId,
                switchSession: $scope.switchSession
            };
            $scope.currentSession = getSessionById($scope.currentSessionId);
        }

        function deleteSession() {
            if (!$scope.currentSessionId) {
                return;
            }
            jhApiSrv.deleteSession($scope.currentSessionId).then(function (response) {
                init();
            });
        }

        function setSessionName(name) {
            if (!$scope.currentSessionId) {
                return;
            }
            jhApiSrv.setSessionName($scope.currentSession.id, {name: name}).then(function (response) {
                console.log('setSessionName response:', response);
                init();
            });
        }

        $scope.saveSessionTags = function (tags) {
            if (!$scope.currentSessionId) {
                return;
            }
            $scope.currentSession.tags = tags;
            jhApiSrv.setSessionData($scope.currentSession.id, {tags: tags}).then(function (response) {
                jhApiSrv.updateAllTags($scope.sessions);
                console.log(jhApiSrv.getAllTags());
            });
        };

        $scope.showSideBar = false;

        $scope.showSessionInfo = false;

        $scope.reloadSessions = function () {
            init();
        };

        $scope.clearSlices = function () {
            $scope.$broadcast('clearSlices');
            $scope.currentSession.slices = [];
            $scope.isLoading = true;
        };

        $scope.updateSlices = function () {
            $scope.$broadcast('updateSlices');
            $scope.isLoading = true;
        };

        $scope.addSlice = function () {
            $scope.$broadcast('addSlice');
        };

        $scope.switchSession = function (id) {
            $scope.currentSessionId = id;
            $scope.showSideBar = false;
            update();
        };

        $scope.showNoSlicesMessage = function () {
            if (!$scope.sessions || !$scope.currentSession.slices) {
                return true;
            }

            if ((!$scope.currentSession.slices.length) && !$scope.isLoading) {
                return true;
            } else {
                return false;
            }
        };

        $scope.setActiveSlice = function (slice) {
            $scope.activeSlice = slice ? slice : {start: -1, end: -1,};
        };

        $scope.secsToTimeStamp = function (seconds) {
            return jhUtilsSrv.secsToTimeStamp(seconds);
        };

        $scope.$watch('currentSession', function (newVal) {
            $scope.isLoading = false;
        });

        $scope.setCustomMarkers = function () {

            var markers = [
                486.5212869644165,
                524.1489300727844,
                904.2117331027985
            ];

            jhApiSrv.setSessionData($scope.currentSession.id, {markers: markers}).then(function (response) {
                console.log('DONE');
            });
        };

        init();

    }]);