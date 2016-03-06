/**
 * Created by AsafDavidi on 30/12/2015.
 */
'use strict';
/*global Recorder:false */

angular.module('ad.jamhub.app').factory('jhBufferToFileSrv',
    [function () {

        var exports = {
            toMp3: function (buffer, fileName) {

                // assuming a var named `buffer` exists and is an AudioBuffer instance


                // start a new worker
                // we can't use Recorder directly, since it doesn't support what we're trying to do
                var worker = new Worker('modules/ad.jamhub.app/services/recorderWorker.js');

                // initialize the new worker
                worker.postMessage({
                    command: 'init',
                    config: {sampleRate: 44100}
                });

                // callback for `exportWAV`
                worker.onmessage = function (e) {
                    var blob = e.data;
                    Recorder.forceDownload(blob, fileName+'.wav');

                    console.log('worker.onmessage');
                    // this is would be your WAV blob
                };

                // send the channel data from our buffer to the worker
                worker.postMessage({
                    command: 'record',
                    buffer: [
                        buffer.getChannelData(0),
                        buffer.getChannelData(1)
                    ]
                });

                // ask the worker for a WAV
                worker.postMessage({
                    command: 'exportWAV',
                    type: 'audio/wav'
                });

            }
        };

        return exports;
    }]);