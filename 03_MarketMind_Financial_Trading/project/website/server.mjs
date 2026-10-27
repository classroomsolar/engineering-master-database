/* Portable single-owner protection for the offline research website.
 * No external packages. Not a live data engine or broker connection.
 * Configure APP_USERNAME, APP_PASSWORD and SESSION_SECRET on a private HTTPS host.
 */
import http from 'node:http';
import { readFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { randomBytes, createHmac, timingSafeEqual, scryptSync, createHash } from 'node:crypto';
const dir = dirname(fileURLToPath(import.meta.url));
const username = process.env.APP_USERNAME || '';
const password = process.env.APP_PASSWORD || '';
const secret = process.env.SESSION_SECRET || '';
if (!username || password.length < 12 || secret.length < 32) {
  console.error('Owner credentials not configured: APP_USERNAME, APP_PASSWORD >=12 chars, SESSION_SECRET >=32 chars are required.');
  process.exit(1);
}
const html = readFileSync(join(dir,'index.html'),'utf8');
const cspHashes = [...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)]
  .map(m=>`'sha256-${createHash('sha256').update(m[1]).digest('base64')}'`);
const prod = (process.env.PUBLIC_BASE_URL || '').startsWith('https://');
const cookieName = prod ? '__Host-imi' : 'imi_session';
const cookieBase = `Path=/; HttpOnly; SameSite=Strict${prod ? '; Secure' : ''}`;
const expectedPasswordDigest = scryptSync(password, 'imi-static-verifier-v1', 64);
const failures = new Map();
const revoked = new Set();
const maxAge = 12*60*60;
function headers(extra={}) {
  return {'Cache-Control':'no-store', 'X-Content-Type-Options':'nosniff',
    'X-Frame-Options':'DENY','Referrer-Policy':'no-referrer',
    'Permissions-Policy':'geolocation=(), camera=(), microphone=()',
    'Content-Security-Policy':"default-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'; img-src 'self' data:; style-src 'unsafe-inline'; script-src "+(cspHashes.join(' ')||"'none'")+"; connect-src 'self'",
    ...(prod?{'Strict-Transport-Security':'max-age=31536000; includeSubDomains'}:{}),...extra};
}
function send(res,status,body,type='text/plain; charset=utf-8',extra={}) {res.writeHead(status,headers({'Content-Type':type,...extra}));res.end(body);}
function sign(payload) {return createHmac('sha256',secret).update(payload).digest('base64url');}
function validSession(req) {
  const raw=(req.headers.cookie||'').split(';').map(v=>v.trim()).find(v=>v.startsWith(cookieName+'='));
  const value=raw?.slice(cookieName.length+1)||'';
  const parts=value.split('.');if(parts.length!==3)return false;
  const [token,expStr,mac]=parts;
  if(!/^[a-zA-Z0-9_-]{43}$/.test(token)|| !/^\d{10}$/.test(expStr) || !/^[a-zA-Z0-9_-]{43}$/.test(mac))return false;
  const exp=Number(expStr); if(!Number.isSafeInteger(exp) ||exp<Math.floor(Date.now()/1000)||exp>Math.floor(Date.now()/1000)+maxAge)return false;
  const expected=sign(`${token}.${expStr}`);
  if(!timingSafeEqual(Buffer.from(mac),Buffer.from(expected)))return false;
  return !revoked.has(createHash('sha256').update(token).digest('hex'));
}
function mintSession(){let token=randomBytes(32).toString('base64url');let exp=String(Math.floor(Date.now()/1000)+maxAge);return `${token}.${exp}.${sign(`${token}.${exp}`)}`;}
const loginForm=`<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Private Investor Login</title><style>body{margin:0;background:#101c30;color:#eef3ff;font:16px/1.5 system-ui;min-height:100vh;display:grid;place-items:center}.card{background:#1d2a41;padding:34px;width:min(92vw,390px);border-radius:20px;box-shadow:0 16px 80px #090d1890}h1{font-size:24px}label{display:block;margin:17px 0 5px}input{width:100%;box-sizing:border-box;padding:13px;border-radius:10px;border:1px solid #72849d;background:#f6f9ff;color:#162033}button{width:100%;margin-top:24px;padding:13px;background:#7698ff;border:0;border-radius:10px;color:#101b31;font-weight:bold;cursor:pointer}small{color:#bac9e0}</style></head><body><form class="card" method="post" action="/login"><h1>Indian Market Intelligence</h1><p>Private owner access</p><label for="u">Username</label><input id="u" name="username" autocomplete="username" required><label for="p">Password</label><input id="p" type="password" name="password" autocomplete="current-password" required><button type="submit">Sign in</button><p><small>Private holdings are never served before authentication. No trading is enabled.</small></p></form></body></html>`;
const server=http.createServer(async(req,res)=>{
  const pathname = new URL(req.url||'/', 'http://localhost').pathname;
  if(pathname==='/health'&&req.method==='GET')return send(res,200,'OK');
  if(pathname==='/login'&&req.method==='GET')return send(res,200,loginForm,'text/html; charset=utf-8');
  if(pathname==='/login'&&req.method==='POST'){
    const addr=req.socket.remoteAddress||'unknown';const now=Date.now();
    const previous=failures.get(addr)||[];const hits=previous.filter(t=>now-t<15*60*1000);
    if(hits.length>=5){failures.set(addr,hits);return send(res,429,'Too many attempts. Try again later.');}
    let body='';try{for await(const chunk of req){body+=chunk.toString('utf8');if(body.length>8192)throw Error('Request too large');}}
    catch{return send(res,413,'Invalid form');}
    const data=new URLSearchParams(body);
    const pass=data.get('password')||'';const user=data.get('username')||'';
    const candidate=scryptSync(pass,'imi-static-verifier-v1',64);
    const ok=user===username&&timingSafeEqual(candidate,expectedPasswordDigest);
    if(!ok){failures.set(addr,[...hits,now]);return send(res,401,'Invalid credentials');}
    failures.delete(addr);
    return send(res,303,'', 'text/plain; charset=utf-8', {'Location':'/','Set-Cookie':`${cookieName}=${mintSession()}; Max-Age=${maxAge}; ${cookieBase}`});
  }
  if(!validSession(req))return send(res,401,'Private. Sign in at /login.');
  if(pathname==='/logout' && req.method==='POST'){
    const raw=(req.headers.cookie||'').split(';').map(v=>v.trim()).find(v=>v.startsWith(cookieName+'='));
    const token=raw?.slice(cookieName.length+1).split('.')[0];if(token)revoked.add(createHash('sha256').update(token).digest('hex'));
    return send(res,303,'', 'text/plain; charset=utf-8', {'Location':'/login','Set-Cookie':`${cookieName}=; Max-Age=0; ${cookieBase}`});
  }
  if((pathname==='/'||pathname==='/index.html') && req.method==='GET')return send(res,200,html,'text/html; charset=utf-8');
  return send(res,404,'Not found');
});
const port=Number(process.env.PORT || 3000);
const host=process.env.HOST || '127.0.0.1';
server.listen(port,host,()=>console.log(`PRIVATE SITE LISTENING on ${host}:${server.address().port}`));
