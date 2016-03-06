'use strict';

angular.module('ad.jamhub.app', ['uuid', 'ngTouch', 'ngSanitize', 'ui.router', 'ui.bootstrap',
    'ui.utils', 'ngAnimate', 'angularMoment', 'LocalStorageModule', 'ngFileUpload', 'ngTagsInput']);

angular.element(document).ready(function () {
    angular.bootstrap(document, ['ad.jamhub.app']);
});

angular.module('ad.jamhub.app').run(['$templateCache', '$state', '$rootScope', 'amMoment', function($templateCache, $state, $rootScope, amMoment){
    $templateCache.put('shell.html', '<div ng-include="\'/modules/ad.jamhub.app/views/shell.html\'"></div>');
}]);


angular.module('ad.jamhub.app').config(function (localStorageServiceProvider) {
    localStorageServiceProvider
        .setPrefix('jamhub');
});
