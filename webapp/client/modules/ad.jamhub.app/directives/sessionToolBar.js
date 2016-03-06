'use strict';
/*global $:false */
angular.module('ad.jamhub.app').directive('sessionToolBar', ['$uibModal', 'moment', function ($uibModal, Moment) {
    return {
        restrict: 'AE',
        replace: true,
        scope: {
            currentSession: '=',
            showSideBar: '=',
            options: '=',
        },
        templateUrl: 'modules/ad.jamhub.app/directives/sessionToolBar.html',
        controller: ['$scope', 'jhEmailSharingSrv', '$location', 'jhApiSrv', '$rootScope',
            function ($scope, jhEmailSharingSrv, $location, jhApiSrv, $rootScope) {

                var sessionDisplayDate;

                function deleteSession() {
                    $scope.options.delete();
                }

                $scope.share = function () {
                    var subject = 'Session: ' + $scope.currentSession.id + ' | ' + $scope.currentSession.name,
                        body = 'Hi All,' + encodeURIComponent('\n') +
                            'Here\'s a link to the session ' + $scope.currentSession.id + ' | ' + $scope.currentSession.name + ' check it out: ' + encodeURIComponent('\n') +
                            encodeURIComponent('http://localhost:3000/#!/preview?id=' + $scope.currentSession.id + '&user=' + jhApiSrv.getUser());

                    jhEmailSharingSrv.sendMail(subject, body);
                };

                $scope.openConfirmModal = function () {

                    var modalInstance = $uibModal.open({
                        animation: true,
                        templateUrl: 'modules/ad.jamhub.app/directives/modalConfirm.html',
                        controller: 'modalConfirmCtl',
                        backdrop: true,
                        resolve: {
                            options: {
                                title: 'Delete Session',
                                message: 'Are you sure you want to delete session "'+ $scope.currentSession.name+'" forever?',
                                message2: 'ID: ' + $scope.currentSession.id + ', Date: ' + sessionDisplayDate,
                                action: 'Delete'
                            }
                        }
                    });

                    modalInstance.result.then(function (result) {
                        console.log('modalInstance.result', result);
                        if ('Delete') {
                            deleteSession();
                        }
                    }, function () {
                        console.log('Modal dismissed at: ' + new Date());
                    });

                };

                $scope.$watch('currentSession', function () {
                    if ($scope.currentSession) {

                        sessionDisplayDate = new Moment(parseInt($scope.currentSession.date * 1000)).format('llll');
                        

                        if ($scope.currentSession.name) {
                            $scope.sessionName = $scope.currentSession.name;
                        } else {
                            $scope.sessionName = sessionDisplayDate;
                        }
                    }
                });

                $scope.inputWidth = function () {
                    var width = $('#inputShadow').width();
                    return width + 10 + 'px';
                };

                $scope.inputFocuse = function () {
                    $rootScope.keybordIsBusy = true;
                };

                $scope.setSessionName = function () {
                    $scope.inputEditMode = false;
                    $rootScope.keybordIsBusy = false;
                    $scope.options.setSessionName($scope.sessionName);
                };

            }],
        link: function postLink(scope, element, attrs) {

        }
    };
}]);