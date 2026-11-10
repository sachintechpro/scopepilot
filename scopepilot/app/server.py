"""Zero-dependency HTTP interface, suitable for small portfolio demonstration."""
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlsplit
import json
import os
from .core import review, catalog
from .handoff import prepare
from .ai import assist

HOME = Path(__file__).resolve().parents[1] / 'web' / 'index.html'
class Handler(BaseHTTPRequestHandler):
    def send(self, code, text, mime='application/json'):
        encoded = text.encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type',mime+'; charset=utf-8')
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Length',str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)
    def do_HEAD(self):
        route=urlsplit(self.path).path
        if route in ('/','/api/health'):
            self.send_response(200)
        else:
            self.send_response(404)
        self.end_headers()
    def do_GET(self):
        path=urlsplit(self.path).path
        if path == '/':
            return self.send(200, HOME.read_text(encoding='utf-8'),'text/html')
        if path == '/api/health':
            return self.send(200,json.dumps({'status':'ok'}))
        if path == '/api/catalog':
            return self.send(200,json.dumps([{'code':k,'description':v['description'],'unit':v['unit']} for k,v in catalog().items()]))
        if path == '/api/modes':
            return self.send(200,json.dumps({'rules':True,'ai':bool(os.environ.get('OPENAI_API_KEY'))}))
        self.send(404,json.dumps({'error':'Not found'}))
    def do_POST(self):
        route=urlsplit(self.path).path
        if route not in ('/api/review','/api/handoff'):
            return self.send(404,json.dumps({'error':'Not found'}))
        size=int(self.headers.get('Content-Length','0'))
        if size<1 or size>18000:
            return self.send(413,json.dumps({'error':'Request size invalid'}))
        try:
            data=json.loads(self.rfile.read(size))
            if not isinstance(data,dict):
                raise ValueError('Request must be a JSON object')
            if route == '/api/handoff':
                return self.send(200,json.dumps(prepare(data)))
            text=data.get('request','')
            if not isinstance(text,str) or not 10<=len(text.strip())<=6000:
                raise ValueError('Enter a request between 10 and 6,000 characters.')
            mode=data.get('mode','rules')
            if mode not in ('rules','ai'):
                raise ValueError('Unsupported mode')
            result=assist(text) if mode=='ai' else review(text)
            return self.send(200,json.dumps(result))
        except (ValueError,json.JSONDecodeError) as e:
            return self.send(400,json.dumps({'error':str(e)}))
        except Exception:
            return self.send(502,json.dumps({'error':'External AI request failed. Try Rules Demo mode.'}))

if __name__=='__main__':
    port=int(os.environ.get('PORT','8000'))
    print(f'ScopePilot listening on port {port}',flush=True)
    ThreadingHTTPServer(('0.0.0.0',port),Handler).serve_forever()
