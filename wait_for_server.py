import socket
import time
import sys
import argparse
import requests

def wait_for_server(host, port, timeout=60, path="/health"):
    """
    Waits for a server to start listening and respond with 200 OK at the given path.
    """
    url = f"http://{host}:{port}{path}"
    start_time = time.time()
    
    print(f"Waiting for server at {url}...")
    
    while time.time() - start_time < timeout:
        # First check if the port is even open
        try:
            with socket.create_connection((host, port), timeout=1):
                pass
        except (socket.timeout, ConnectionRefusedError):
            time.sleep(1)
            continue
            
        # If port is open, try the health check
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                print(f"Server is ready! (Started in {int(time.time() - start_time)}s)")
                return True
        except Exception:
            pass
            
        time.sleep(1)
        
    print(f"Error: Timeout waiting for server at {url} after {timeout}s")
    return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Wait for server readiness")
    parser.add_argument("--host", default="localhost", help="Server host")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    parser.add_argument("--timeout", type=int, default=120, help="Wait timeout in seconds")
    parser.add_argument("--path", default="/health", help="Health check path")
    
    args = parser.parse_args()
    
    if wait_for_server(args.host, args.port, args.timeout, args.path):
        sys.exit(0)
    else:
        sys.exit(1)
