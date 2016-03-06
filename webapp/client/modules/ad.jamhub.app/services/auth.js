/**
 * Created by AsafDavidi on 20/12/2015.
 */
/**
 * Created by asafd on 5/25/15.
 */
'use strict';

angular.module('ad.jamhub.app').factory('jhAuthSrv',
    ['localStorageService', function (localStorageService) {

        var exports = {
            getLocalStorage: function (key) {
                return localStorageService.get(key);
            },
            setLocalStorage: function (key, val) {
                return localStorageService.set(key, val);
            },
            removeLocalStorageItem: function (key) {
                return localStorageService.remove(key);
            }
        };

        return exports;
    }
    ]
);
