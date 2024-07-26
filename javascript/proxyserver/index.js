process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';
import express from 'express';

const fetch = (...args) => import('node-fetch').then(({ default: fetch }) => fetch(...args));

const createProxyServer = (port, accessKey, secretKey) => {
  const app = express();
  const targetUrl = 'https://aip.baidubce.com';
  let combinedUrl = '';

  app.use(express.json());

  let accessToken = '';

  // 处理preflight 
  app.use((req, res, next) => {
    res.header('Access-Control-Allow-Origin', '*'); // Allow all origins
    res.header('Access-Control-Allow-Methods', 'GET, PUT, POST, DELETE, OPTIONS'); // Allow these methods
    res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization'); // Allow these headers
    next();
  });

  app.options('*', (req, res) => {
    res.sendStatus(200);
  });

  app.use(async (req, res) => {
    try {
      const isTokenRequest = req.url.includes('access_token');
      combinedUrl = `https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=${accessKey}&client_secret=${secretKey}`;

      const next_req = {
        method: req.method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: ['POST', 'PUT'].includes(req.method) ? JSON.stringify(req.body) : undefined,
      };

      const apiRes = await fetch(combinedUrl, next_req);
      const responseBody = await apiRes.json();

      accessToken = responseBody.access_token;

      const combinedUrls = `https://aip.baidubce.com${req.url}?access_token=${accessToken}`;

      const apiFin = await fetch(combinedUrls, next_req);
      const responseFinal = await apiFin.json();

      res.status(apiFin.status).send(responseFinal);
    } catch (error) {
      console.error('Error proxying request:', error);
      res.status(500).send('Internal Server Error');
    }
  });

  app.listen(port, () => {
    console.log(`Proxy server is running on port ${port}`);
  });
};

const args = process.argv.slice(2);
const ak = args[0];
const sk = args[1];
if (!ak || !sk) {
  console.log('please enter access key or secret key');
}

createProxyServer(3001, ak, sk);
