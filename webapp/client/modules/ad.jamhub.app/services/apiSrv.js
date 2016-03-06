/**
 * Created by asafd on 5/25/15.
 */
'use strict';

angular.module('ad.jamhub.app').factory('jhApiSrv',
    ['$http', 'jhAuthSrv', '$location', function ($http, auth, $location) {


        var _baseUrl = 'http://128.199.47.105:55666/',
            allTags,
            constants = {
                imgRoot: 'modules/ad.jamhub.app/style/images/',
            };


        function getUserId() {

            var user = auth.getLocalStorage('user');

            if (!user && $location.path() !== '/preview') {
                $location.url('signin');
                return null;
            } else {
                return user.userName;
            }

        }

        function updateAllTags(sessions) {
            var arr = [];
            _.each(sessions, function (session) {
                if (session.tags) {
                    arr = arr.concat(session.tags);
                }
            });
            allTags = _.uniq(arr, 'text');
        }

        function putSession(sessionId, sessionJSON) {
            var url = _baseUrl + 'sessions/' + getUserId() + '/' + sessionId;
            return $http.put(url, sessionJSON).then(function (result) {
                return result;
            }, function (err) {
                console.log('err putSession', err);
                return err;
            });
        }

        var exports = {
            sessions: constants.sessions,
            imgRoot: constants.imgRoot,
            getUser: function () {
                return getUserId();
            },
            updateAllTags: function (sessions) {
                return updateAllTags(sessions);
            },
            getAllTags: function () {
                return allTags;
            },
            setSessionName: function (sessionId, sessionJSON) {
                return putSession(sessionId, sessionJSON);
            },
            setSessionData: function (sessionId, sessionJSON) {
                return putSession(sessionId, sessionJSON);
            },
            setSlices: function (sessionId, slicesJSON) {
                return putSession(sessionId, slicesJSON);
            },
            putSession: function (sessionId, sessionJSON) {
                return putSession(sessionId, sessionJSON);
            },
            uploadUrl: function (sessionId) {
                return _baseUrl + 'upload/' + getUserId() + '/' + sessionId + '?override=1';
            },
            getSessions: function () {
                var url = _baseUrl + 'sessions/' + getUserId();
                return $http.get(url).then(function (result) {
                    var sessions = result.data.res;
                    return sessions;
                }, function (err) {
                    console.log('err getSessions', err);
                    return err;
                });
            },
            getOneSessions: function (sessionId, userId) {
                var user = userId ? userId : getUserId();
                var url = _baseUrl + 'sessions/' + user + '/' + sessionId;
                return $http.get(url).then(function (result) {
                    return result.data.res;
                }, function (err) {
                    console.log('err getSessions', err);
                    return err;
                });
            },
            deleteSession: function (sessionId) {
                var url = _baseUrl + 'sessions/' + getUserId() + '/' + sessionId;
                return $http.delete(url).then(function (result) {
                    return result;
                }, function (err) {
                    console.log('err deleteSession', err);
                    return err;
                });
            },
            updateBoxConfig: function (configJson) {
                var url = _baseUrl + 'config/' + getUserId();
                return $http.put(url, configJson).then(function (result) {
                    return result;
                }, function (err) {
                    console.log('err updateBoxConfig', err);
                    return err;
                });
            }
        };

        return exports;
    }
    ]
);
