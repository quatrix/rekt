/**
 * Created by AsafDavidi on 27/12/2015.
 */

'use strict';
angular.module('ad.jamhub.app').factory('jhEmailSharingSrv',
    [function () {

        var exports = {
            sendMail: function (subject, body, mailTo) {
                window.open('mailto:' + (mailTo || '') + '?Subject=' + (subject || '') + '&Body=' + (body || ''), '_blank');
            }
        };

        return exports;
    }]);
