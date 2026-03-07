import json
import os
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

# Need to import python-dotenv
try:
    from dotenv import dotenv_values, set_key
except ImportError:
    print("Error: python-dotenv is not installed. Please install it using 'pip install python-dotenv'")
    exit(1)

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"
ENV_EXAMPLE_FILE = PROJECT_ROOT / ".env.example"
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

if not ENV_FILE.exists() and ENV_EXAMPLE_FILE.exists():
    import shutil
    shutil.copy(ENV_EXAMPLE_FILE, ENV_FILE)
    print(f"Created {ENV_FILE} from {ENV_EXAMPLE_FILE}")

class ConfigServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            # Serve the HTML UI
            ui_path = TEMPLATES_DIR / "config_ui.html"
            if not ui_path.exists():
                self.send_error(404, "UI template not found")
                return
            
            with open(ui_path, "rb") as f:
                content = f.read()
                
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/api/config':
            # Return current configuration as JSON
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            # Read .env (or .env.example keys as fallback)
            config = {}
            if ENV_FILE.exists():
                config = dotenv_values(ENV_FILE)
            elif ENV_EXAMPLE_FILE.exists():
                config = dotenv_values(ENV_EXAMPLE_FILE)
                
            response = json.dumps(config)
            self.wfile.write(response.encode('utf-8'))
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        if self.path == '/api/config':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                # Parse JSON payload
                new_config = json.loads(post_data.decode('utf-8'))
                
                # Make sure .env exists
                if not ENV_FILE.exists():
                    ENV_FILE.touch()
                
                # Update each key using dotenv set_key to preserve comments
                env_path_str = str(ENV_FILE)
                for key, value in new_config.items():
                    # Handle boolean values properly for string storage
                    if isinstance(value, bool):
                        value_str = "true" if value else "false"
                    else:
                        value_str = str(value)
                    
                    # Remove surrounding quotes if they were added accidentally in the UI
                    if value_str.startswith('"') and value_str.endswith('"'):
                        value_str = value_str[1:-1]
                        
                    set_key(
                        env_path_str, 
                        key, 
                        value_str, 
                        quote_mode="always" if ' ' in value_str or key.endswith('_KEY') or key.endswith('_TOKEN') else "never"
                    )
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success", "message": "Configuration saved successfully"}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))
        else:
            self.send_error(404, "Not Found")

def run(server_class=HTTPServer, handler_class=ConfigServerHandler, port=8080):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"============================================================")
    print(f" SecretarAI Configurator running at: http://localhost:{port} ")
    print(f"============================================================")
    print("Press Ctrl+C to stop the server.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print("\nServer stopped.")

if __name__ == '__main__':
    run()
