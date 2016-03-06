var express = require('express');

var app = express();
app.use(express.static(__dirname + '/public'));

var server = app.listen(3000, function() {
    console.log('Listening on port %d', server.address().port);
});

app.post('api/v1/save', function(req, res){
    console.log(req.body);
    res.json({saved: true});
});
