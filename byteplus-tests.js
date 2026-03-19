const https = require('https');
const key = process.env.BYTEPLUS_API_KEY || '5cee0d73-2a72-4f29-b001-c19f3e1c32ba';

function testAPI(hostname, model) {
    console.log(`Testing ${hostname} with model ${model}...`);
    const payload = JSON.stringify({ model, messages: [{ role: 'user', content: 'Hi' }] });
    
    const req = https.request({
        hostname,
        path: '/api/v3/chat/completions',
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json', 
            'Authorization': `Bearer ${key}`,
            'Content-Length': Buffer.byteLength(payload)
        }
    }, (res) => {
        let data = '';
        res.on('data', c => data += c);
        res.on('end', () => console.log(`${hostname} | ${model}:`, JSON.parse(data).error ? JSON.parse(data).error : 'SUCCESS'));
    });

    req.on('error', (e) => console.error(`${hostname} | ${model} ERROR:`, e.message));
    req.write(payload);
    req.end();
}

testAPI('ark.cn-beijing.volces.com', 'ep-20241029192931-qj2k6');
testAPI('ark.cn-beijing.volces.com', 'doubao-pro-32k');
testAPI('ark.byteplus.com', 'doubao-pro-32k');
testAPI('open.volcengineapi.com', 'doubao-pro-32k');
