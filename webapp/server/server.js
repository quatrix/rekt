var express = require('express'),
    registration = require('./lib/registration');




var app = express();
app.use(express.static(__dirname + '/public'));

var server = app.listen(3000, function() {
    console.log('Listening on port %d', server.address().port);
});


app.post('api/v1/registration/mail', function(req, res){
    console.log(req.body);
    res.json({sent: true});
});

app.post('api/v1/registration/confirm', function(req, res){
    console.log(req.body);
    res.json({sent: true});
});

app.post('api/v1/save', function(req, res){
    console.log(req.body);
    res.json({saved: true});
});
