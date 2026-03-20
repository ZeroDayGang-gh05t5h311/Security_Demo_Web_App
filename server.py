#!/usr/bin/python3 
"""
Lightweight HTTP server (no Flask) for demo frontends.
- Serves static files from current directory.
- Provides API endpoints under /api/*
  - /api/create_user    POST {"username": "..."}
  - /api/search_user    POST {"username": "..."}
  - /api/post_comment   POST {"comment": "..."}
  - /api/ingest_users   POST {"users": [{"username": "user1"}, {"username": "user2"}]}
"""
import http.server
import socketserver,html,os,urllib,random,json
from urllib.parse import urlparse
PORT = 8080
MAX_BODY = 10 * 1024 * 1024  # 10MB limit
# ______________________________
class db:
    def genPID():
        seedone = random.randint(1, 1000)
        seedtwo = random.randint(1, 1000)
        seedthree = random.randint(1, 1000)  # Generates a random number for pid
        final_seed = seedone + seedtwo + seedthree
        return final_seed
    usernames = ["Addison", "Charli", "Loren", "Admin"]
    passwords = ["A44150n!", "Ch7rl1", "L0r3n", "A4m1n"]
    upid = []
# Initializing `upid` list with random user IDs
db.upid.append(db.genPID())
db.upid.append(db.genPID())
# ^^^ DB STORE ^^^^
# ---------- Utilities ----------
def html_escape(s):
    if s is None:
        return ""
    return html.escape(str(s), quote=True).replace("'", "&#39;")
def is_valid_username(u):
    return isinstance(u, str) and 0 < len(u.strip()) <= 100
def read_json_body(rfile, length):
    if length is None or length <= 0:
        return None
    if length > MAX_BODY:
        raise ValueError("Body too large")
    raw = rfile.read(length)
    if not raw:
        return None
    try:
        return json.loads(raw.decode('utf-8'))
    except Exception:
        return None
# ---------- HTTP Handler ----------
class DemoHandler(http.server.SimpleHTTPRequestHandler):
    server_version = "DemoHTTP/1.1"
    def _set_common_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", 
                         "default-src 'none'; "
                         "script-src 'self'; "
                         "connect-src 'self' http://localhost:%d; "
                         "style-src 'self'; "
                         "img-src 'self' data:;" % PORT)
    def do_OPTIONS(self):
        self.send_response(101)
        self._set_common_headers()
        self.end_headers()
    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        try:
            length = int(self.headers.get('Content-Length', 0))
        except Exception:
            length = 0
        try:
            data = read_json_body(self.rfile, length)
        except ValueError:
            self.send_response(413)
            self._set_common_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            return
        # Dispatch known endpoints
        if path == "/api/create_user":
            self._handle_create_user(data)
        elif path == "/api/search_user":
            self._handle_search_user(data)
        elif path == "/api/post_comment":
            self._handle_post_comment(data)
        elif path == "/api/ingest_users":
            self._handle_ingest_users(data)
        else:
            self.send_response(404)
            self._set_common_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
    def _handle_create_user(self, data):
        username = data.get("username", "").strip()
        password = data.get("password", "").strip()
        # Check if the username is valid
        if not is_valid_username(username):
            self.send_response(400)
            self._set_common_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Invalid username"}).encode('utf-8'))
            return
        # Check if the username already exists
        if username in db.usernames:
            self.send_response(400)
            self._set_common_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Username already exists"}).encode('utf-8'))
            return
        # Add username and password to the mock database
        try:
            db.usernames.append(username)
            db.passwords.append(password)
            db.upid.append(db.genPID())  # Storing a mock user ID
            self.send_response(200)
            self._set_common_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True}).encode('utf-8'))
        except Exception as e:
            self.send_response(503)
            self._set_common_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
    def _handle_search_user(self, data):
        username = data.get("username", "").strip()
        if not is_valid_username(username):
            self.send_response(400)
            self._set_common_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Invalid username"}).encode('utf-8'))
            return
        # Search for the user in the mock database
        if username in db.usernames:
            response = {"username": username, "status": "found"}
        else:
            response = {"username": username, "status": "not found"}
        # Send response with user search result
        self.send_response(200)
        self._set_common_headers()
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))
    def _handle_post_comment(self, data):
        comment = data.get("comment", "").strip()
        if not isinstance(comment, str) or len(comment) > 5000:
            self.send_response(400)
            self._set_common_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Invalid comment"}).encode('utf-8'))
            return
        try:
            safe_comment = html_escape(comment)  # Escape comment
            self.send_response(200)
            self._set_common_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"safe_comment": safe_comment}).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self._set_common_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
    def _handle_ingest_users(self, data):
        if not isinstance(data, dict):
            self.send_response(400)
            self._set_common_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Invalid data format"}).encode('utf-8'))
            return
        users = []
        # Accept single user
        if "username" in data:
            users.append(data.get("username"))
        # Accept bulk users
        elif "users" in data and isinstance(data["users"], list):
            for u in data["users"]:
                if isinstance(u, dict) and "username" in u:
                    db.usernames.append(u["username"])
        if not users:
            self.send_response(400)
            self._set_common_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "No valid users provided"}).encode('utf-8'))
            return
        inserted = []
        rejected = []
        try:
            for username in users:
                if username in db.usernames:
                    rejected.append(username)  # Skip if the username already exists
                elif is_valid_username(username):
                    db.usernames.append(username.strip())
                    inserted.append(username.strip())
                else:
                    rejected.append(username)
            self.send_response(200)
            self._set_common_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"inserted": inserted, "rejected": rejected}).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self._set_common_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
def run_server():
    handler = DemoHandler
    with socketserver.ThreadingTCPServer(("", PORT), handler) as httpd:
        sa = httpd.socket.getsockname()
        print(f"Serving HTTP on {sa[0]} port {sa[1]} (http://localhost:{PORT}/) ...")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")
            httpd.shutdown()
if __name__ == "__main__":
    run_server()
