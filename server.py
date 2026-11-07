import json, subprocess, sys, tempfile, os, base64, urllib.request, urllib.error
from http.server import BaseHTTPRequestHandler, HTTPServer

PAGE = r"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Local Studio</title>
<style>
body{background:#050505;color:#eee;font-family:sans-serif;margin:0;padding:10px}
h3{margin:14px 0 6px;color:#ffd966}
textarea,input{width:100%;box-sizing:border-box;background:#111;color:#eee;border:1px solid #333;border-radius:6px;padding:8px;margin:3px 0;font-family:monospace}
textarea{height:220px}
button{background:#ffd966;color:#000;border:0;border-radius:6px;padding:10px 16px;font-weight:bold;margin:4px 4px 4px 0}
pre{background:#111;padding:8px;border-radius:6px;white-space:pre-wrap;min-height:40px}
</style></head><body>
<h3>Editor (Termux)</h3>
<textarea id="code" placeholder="print('hello')"></textarea>
<button onclick="run()">▶ Run</button>
<pre id="out"></pre>

<h3>Claude</h3>
<input id="ak" type="password" placeholder="Anthropic API key">
<textarea id="q" style="height:80px" placeholder="Claude से कुछ पूछो या कोड माँगो"></textarea>
<button onclick="ask()">Claude को भेजो</button>
<pre id="ans"></pre>

<h3>GitHub</h3>
<input id="gt" type="password" placeholder="GitHub token">
<input id="repo" placeholder="username/repo">
<input id="path" placeholder="main.py">
<button onclick="push()">Push करो</button>
<pre id="gh"></pre>

<script>
const $=id=>document.getElementById(id);
for(const k of ['ak','gt','repo','path','code']){
  $(k).value=localStorage.getItem(k)||'';
  $(k).addEventListener('input',()=>localStorage.setItem(k,$(k).value));
}
async function post(u,d){const r=await fetch(u,{method:'POST',body:JSON.stringify(d)});return r.json();}
async function run(){
  $('out').textContent='चल रहा है...';
  const r=await post('/run',{code:$('code').value});
  $('out').textContent=r.out;
}
async function ask(){
  $('ans').textContent='सोच रहा है...';
  const r=await post('/claude',{key:$('ak').value,prompt:$('q').value});
  $('ans').textContent=r.out;
  const m=r.out.match(/```(?:python)?\n([\s\S]*?)```/);
  if(m){$('code').value=m[1];localStorage.setItem('code',m[1]);}
}
async function push(){
  $('gh').textContent='भेज रहा है...';
  const r=await post('/github',{token:$('gt').value,repo:$('repo').value,path:$('path').value,code:$('code').value});
  $('gh').textContent=r.out;
}
</script></body></html>"""


try:
    import ssl, certifi
    CTX = ssl.create_default_context(cafile=certifi.where())
except Exception:
    CTX = None


def call(url, method, headers, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60, context=CTX) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read())
        except Exception:
            return e.code, {}
    except Exception as e:
        return 0, {"error": str(e)}


def run_code(code):
    import io, contextlib, traceback
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            exec(compile(code, "<editor>", "exec"), {"__name__": "__main__"})
    except BaseException:
        buf.write(traceback.format_exc())
    return buf.getvalue() or "(कोई output नहीं)"


def ask_claude(key, prompt):
    if not key:
        return "API key डालिए"
    s, d = call("https://api.anthropic.com/v1/messages", "POST",
                {"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                {"model": "claude-sonnet-5-5", "max_tokens": 2000,
                 "messages": [{"role": "user", "content": prompt}]})
    if s == 200:
        return "".join(b.get("text", "") for b in d.get("content", []))
    return "Error %s: %s" % (s, d)


def push_github(token, repo, path, code):
    if not (token and repo and path):
        return "token, repo और path भरिए"
    url = "https://api.github.com/repos/%s/contents/%s" % (repo, path)
    h = {"Authorization": "Bearer " + token, "User-Agent": "local-studio",
         "Accept": "application/vnd.github+json"}
    s, d = call(url, "GET", h)
    body = {"message": "update " + path, "content": base64.b64encode(code.encode()).decode()}
    if s == 200 and "sha" in d:
        body["sha"] = d["sha"]
    s, d = call(url, "PUT", h, body)
    return "Push हो गया ✅" if s in (200, 201) else "Error %s: %s" % (s, d.get("message", d))


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send(self, body, ctype):
        b = body.encode()
        self.send_response(200)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        self.send(PAGE, "text/html")

    def do_POST(self):
        d = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        if self.path == "/run":
            out = run_code(d.get("code", ""))
        elif self.path == "/claude":
            out = ask_claude(d.get("key"), d.get("prompt", ""))
        elif self.path == "/github":
            out = push_github(d.get("token"), d.get("repo"), d.get("path"), d.get("code", ""))
        else:
            out = "unknown"
        self.send(json.dumps({"out": out}), "application/json")


if __name__ == "__main__":
    print("चालू: http://localhost:8080  (browser में खोलिए)")
    HTTPServer(("127.0.0.1", 8080), H).serve_forever()
