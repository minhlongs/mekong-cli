// serve-colab.js
const http = require('http');
const fs = require('fs');

http.createServer((req, res) => {
    if (req.url === '/script.py') {
        res.writeHead(200, { 'Content-Type': 'text/plain' });
        res.end(fs.readFileSync(__dirname + '/colab-one-click.py'));
    } else {
        res.writeHead(404);
        res.end();
    }
}).listen(8999, () => {
    console.log('Serving colab script on port 8999');
});
