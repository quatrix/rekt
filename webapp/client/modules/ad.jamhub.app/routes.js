'use strict';

angular.module('ad.jamhub.app').config(['$stateProvider', '$urlRouterProvider', '$locationProvider',
    function ($stateProvider, $urlRouterProvider, $locationProvider) {

        $locationProvider.hashPrefix('!');

        $urlRouterProvider.otherwise('/sessions');

        $stateProvider.
            state('home', {
                url: '/home',
                templateUrl: 'modules/ad.jamhub.app/views/home.html',
                controller: 'jhHomeCtrl',
                sticky:true
            }).
            state('signin', {
                url: '/signin',
                templateUrl: 'modules/ad.jamhub.app/views/signin.html',
                controller: 'jhSigninCtrl'
            }).
            state('preview', {
                url: '/preview',
                templateUrl: 'modules/ad.jamhub.app/views/preview.html',
                controller: 'jhPreviewCtrl'
            }).
            state('sessions', {
                url: '/sessions',
                templateUrl: 'modules/ad.jamhub.app/views/sessions.html',
                controller: 'jhSessionsCtrl'
            }).
            state('player', {
                url: '/player',
                templateUrl: 'modules/ad.jamhub.app/views/player.html',
                controller: 'jhPlayerCtrl'
            }).
            state('boxapp', {
                url: '/boxapp',
                templateUrl: 'modules/ad.jamhub.app/views/downloadBoxApp.html',
                controller: 'jhBoxFilesCtrl'
            });
    }
]);