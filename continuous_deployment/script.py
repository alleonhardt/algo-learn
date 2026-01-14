import os
import http.server
import socketserver
import tomllib
import json
import subprocess
import urllib.request
import random, string
import sys

import hashlib
import hmac
def verify_signature(payload_body, secret_token, signature_header):
    """Verify that the payload was sent from GitHub by validating SHA256.

    Raise and return 403 if not authorized.

    Args:
        payload_body: original request body to verify (request.body())
        secret_token: GitHub app webhook token (WEBHOOK_SECRET)
        signature_header: header received from GitHub (x-hub-signature-256)
    """
    if not signature_header:
        return False
    hash_object = hmac.new(secret_token.encode('utf-8'), msg=payload_body, digestmod=hashlib.sha256)
    expected_signature = "sha256=" + hash_object.hexdigest()
    if not hmac.compare_digest(expected_signature, signature_header):
        return False
    return True

class BuildServer(http.server.BaseHTTPRequestHandler):
    secret_token = ""
    branches = set()
    base_path = ""

    def do_POST(self):
        if self.headers["Content-Type"] != "application/json":
           print("Error received invalid POST request (only json payloads are allowed)",file=sys.stderr)
           self.send_response(200)
           self.end_headers()
           return
        content_len = int(self.headers.get('Content-Length'))
        post_body = self.rfile.read(content_len)
        if not verify_signature(post_body, BuildServer.secret_token, self.headers.get("X-Hub-Signature-256")):
            self.send_error(403)
            self.end_headers()
            return
        payload = json.loads(post_body.decode("utf-8"))


        worktree_name = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(16))
        if self.headers.get('X-GitHub-Event') == 'push':
            ref = payload['ref'].split('/')[-1]
            if ref in BuildServer.branches:
                result = subprocess.run(["git", "fetch", "--all"], cwd=BuildServer.base_path)
                result = subprocess.run(["git", "worktree", "prune"], cwd=BuildServer.base_path)
                result = subprocess.run(["git", "worktree", "add", "--detach", f"../{worktree_name}", payload["after"]], cwd=BuildServer.base_path)
                path = f"/var/www/localhost/htdocs/logs/{ref}/{payload['after']}"
                os.makedirs(path)
                with open(os.path.join(path,"stdout.log"),"w") as stdout:
                    with open(os.path.join(path,"stderr.log"),"w") as stderr:
                        result = subprocess.Popen(["sh", "../build_deploy.sh"], cwd=worktree_name, env={"TARGET": f"/{ref}"},shell=False,stdin=None,stdout=stdout,stderr=stderr)
            else:
                print(f"Registered push to {payload['ref']}, but the branch was not among the tracked branches",file=sys.stderr)
        elif self.headers.get('X-GitHub-Event') == 'pull_request':
            if payload["action"] == "opened" or payload["action"] == "synchronize":
                path = f"/var/www/localhost/htdocs/logs/pr/{payload['number']}/{payload['after']}"
                os.makedirs(path)
                result = subprocess.run(["git", "fetch", "--all"], cwd=BuildServer.base_path)
                result = subprocess.run(["git", "worktree", "prune"], cwd=BuildServer.base_path)
                result = subprocess.run(["git", "worktree", "add", "--detach", f"../{worktree_name}",  payload["pull_request"]["base"]["sha"]], cwd=BuildServer.base_path)
                urllib.request.urlretrieve(payload["pull_request"]["patch_url"], os.path.join(worktree_name,"patch.patch"))
                result = subprocess.run(["git", "apply", "--reject","--whitespace=fix", "patch.patch"], cwd=worktree_name)
                with open(os.path.join(path,"stdout.log"),"w") as stdout:
                    with open(os.path.join(path,"stderr.log"),"w") as stderr:
                        result = subprocess.Popen(["sh", "../build_deploy.sh"], cwd=worktree_name, env={"TARGET": "/pr/"+str(payload['number'])},shell=False,stdin=None,stdout=stdout,stderr=stderr)
            elif payload['action'] == "closed":
                result = subprocess.run(["rm", "-rf", "/var/www/localhost/htdocs/pr/"+str(payload['number'])])
                print(f"Removed PR {payload['number']} from server.",file=sys.stderr)
            else:
                print(f"Registered pull request action {payload['action']}, but this is not a tracked action",file=sys.stderr)
        else:
            print(f"Received {self.headers.get('X-GitHub-Event')} ignoring request",file=sys.stderr)
        self.send_response(200)
        self.end_headers()

with open("configuration.toml", "rb") as f:
    configuration = tomllib.load(f)

    with http.server.HTTPServer((configuration["url"],configuration["port"]),BuildServer) as httpd:
        BuildServer.secret_token = configuration["secret_token"]
        BuildServer.base_path = configuration["base_path"]
        BuildServer.branches = set(configuration["branches"])
        print("serving at port", configuration["port"])
        httpd.serve_forever()
