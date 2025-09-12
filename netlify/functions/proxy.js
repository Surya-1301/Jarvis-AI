// Netlify function to proxy requests to a backend URL defined in BACKEND_URL

export async function handler(event, context) {
  const backend = process.env.BACKEND_URL;
  if (!backend) {
    return {
      statusCode: 500,
      body: 'BACKEND_URL is not set in Netlify environment variables.'
    };
  }

  const stripPrefix = '/.netlify/functions/proxy';
  const path = event.path.startsWith(stripPrefix)
    ? event.path.slice(stripPrefix.length)
    : event.path;
  const qs = event.rawQuery ? `?${event.rawQuery}` : '';
  const url = `${backend}${path}${qs}`;

  const headers = { ...event.headers };
  delete headers.host;
  delete headers.connection;
  delete headers['accept-encoding'];

  const init = {
    method: event.httpMethod,
    headers,
    body: event.body && event.isBase64Encoded ? Buffer.from(event.body, 'base64') : event.body,
  };

  try {
    const resp = await fetch(url, init);
    const buf = await resp.arrayBuffer();
    const ct = resp.headers.get('content-type') || '';
    const isText = ct.startsWith('text/') || ct.includes('application/json');

    const headersOut = {};
    resp.headers.forEach((v, k) => {
      if (!['content-encoding', 'transfer-encoding'].includes(k.toLowerCase())) headersOut[k] = v;
    });

    return {
      statusCode: resp.status,
      headers: headersOut,
      body: isText ? Buffer.from(buf).toString('utf8') : Buffer.from(buf).toString('base64'),
      isBase64Encoded: !isText,
    };
  } catch (e) {
    return {
      statusCode: 502,
      body: `Proxy error: ${e}`,
    };
  }
}
