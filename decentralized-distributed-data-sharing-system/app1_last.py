from flask import Flask, request, jsonify, render_template, send_file
import requests
import time
import hashlib
import threading
import os, random
import argparse

app = Flask(__name__)

# Parse arguments to set up IP and port
parser = argparse.ArgumentParser(description="Start a P2P node")
parser.add_argument('--ip', type=str, default="127.0.0.1", help="IP to run the Flask app on")
parser.add_argument('--port', type=int, default=5000, help="Port to run the Flask app on")
parser.add_argument('--peers', nargs='*', default=[], help="List of peers in the format IP:Port")
args = parser.parse_args()

local_ip = args.ip
local_port = args.port

files = set()  # Files available on this node
routing_table = {}  # Other nodes and their files

def get_file_hash(file_name):
    return hashlib.sha256(file_name.encode()).hexdigest()

def save_file(file_name):
    with open(file_name, 'rb') as f:
        _ = f.read()

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file_name = request.json.get("file_name")
        if not file_name:
            return jsonify({"status": "Error", "message": "File name is required"}), 400

        file_hash = get_file_hash(file_name)
        files.add(file_name)
        save_file(file_name)

        # Update routing table for local node
        node_id = f"{local_ip}:{local_port}"
        routing_table[node_id] = {
            "ip": local_ip,
            "port": local_port,
            "files": files,
            "last_seen": time.time(),
        }

        # Announce the file to peers
        for peer_id, peer_info in routing_table.items():
            if peer_id != node_id:
                announce_file_to_peer(peer_info["ip"], peer_info["port"], file_name)

        replicate_file_to_peers(file_name)
        return jsonify({"status": "File added", "hash": file_hash}), 200

    return render_template('upload.html')

def announce_file_to_peer(peer_ip, peer_port, file_name):
    try:
        response = requests.post(
            f"http://{peer_ip}:{peer_port}/announce_file",
            json={"file": file_name, "node": f"{local_ip}:{local_port}"}
        )
        if response.status_code == 200:
            print(f"File '{file_name}' announced to {peer_ip}:{peer_port}")
    except Exception as e:
        print(f"Failed to announce file '{file_name}' to {peer_ip}:{peer_port}: {e}")

@app.route('/announce_file', methods=['POST'])
def announce_file():
    data = request.get_json()
    file_name = data["file"]
    node = data["node"]
    if node in routing_table:
        routing_table[node]["files"].add(file_name)
        routing_table[node]["last_seen"] = time.time()
    else:
        ip, port = node.split(":")
        routing_table[node] = {
            "ip": ip,
            "port": int(port),
            "files": {file_name},
            "last_seen": time.time()
        }
    return jsonify({"status": "success"}), 200

@app.route('/register_peer', methods=['GET', 'POST'])
def register_peer():
    if request.method == 'POST':
        peer_ip = request.json["ip"]
        peer_port = request.json["port"]
        # 1. Fetch routing table from joining peer
        try:
            r = requests.get(f"http://{peer_ip}:{peer_port}/get_routing_table", timeout=5)
            if r.status_code == 200:
                remote_table = r.json()["routing_table"]
                # Merge remote table: always keep latest last_seen for each node
                for node_id, node_info in remote_table.items():
                    node_files = set(node_info["files"])
                    if (
                        node_id not in routing_table or
                        node_info["last_seen"] > routing_table[node_id]["last_seen"]
                    ):
                        routing_table[node_id] = {
                            "ip": node_info["ip"],
                            "port": node_info["port"],
                            "files": node_files,
                            "last_seen": node_info["last_seen"]
                        }
                    else:
                        routing_table[node_id]["files"].update(node_files)
        except Exception as e:
            print(f"Failed to fetch routing table from {peer_ip}:{peer_port}: {e}")

        # 2. Add self to routing table
        node_id = f"{local_ip}:{local_port}"
        routing_table[node_id] = {
            "ip": local_ip,
            "port": local_port,
            "files": set(files),
            "last_seen": time.time()
        }

        # 3. Announce self (and files) to all known peers (except self)
        for peer_id, peer_info in routing_table.items():
            if peer_id != node_id:
                try:
                    requests.post(
                        f"http://{peer_info['ip']}:{peer_info['port']}/announce_peer",
                        json={
                            "ip": local_ip,
                            "port": local_port,
                            "files": list(files)
                        }
                    )
                except Exception as e:
                    print(f"Failed to announce self to {peer_info['ip']}:{peer_info['port']}: {e}")

        return jsonify({"status": "Peer registered"}), 200

    return render_template('register_peer.html')

@app.route('/get_routing_table', methods=['GET'])
def get_routing_table():
    serializable_routing_table = {
        node: {
            "ip": info["ip"],
            "port": info["port"],
            "files": list(info["files"]),
            "last_seen": info["last_seen"]
        }
        for node, info in routing_table.items()
    }
    return jsonify({"routing_table": serializable_routing_table}), 200

@app.route('/announce_peer', methods=['POST'])
def announce_peer():
    data = request.get_json()
    ip = data["ip"]
    port = data["port"]
    node_id = f"{ip}:{port}"
    node_files = set(data.get("files", []))
    # Only update if last_seen is newer
    if (
        node_id not in routing_table or
        time.time() > routing_table[node_id]["last_seen"]
    ):
        routing_table[node_id] = {
            "ip": ip,
            "port": port,
            "files": node_files,
            "last_seen": time.time()
        }
    else:
        routing_table[node_id]["files"].update(node_files)
    return jsonify({"status": "success"}), 200

@app.route('/download_file/<file_name>', methods=['GET'])
def download_file(file_name):
    if file_name in files:
        try:
            return send_file(file_name, as_attachment=True)
        except Exception as e:
            return jsonify({"status": "Error", "message": str(e)}), 500
    return jsonify({"status": "File not available on this node"}), 404

@app.route('/request_file', methods=['GET', 'POST'])
def request_file():
    if request.method == 'GET':
        return render_template('request_file.html')
    elif request.method == 'POST':
        file_name = request.json["file_name"]
        nodes_with_file = [
            node_info
            for node_id, node_info in routing_table.items()
            if file_name in node_info["files"]
        ]

        if not nodes_with_file:
            return jsonify({"status": "File not found on the network"}), 404

        for node_info in nodes_with_file:
            file_url = f"http://{node_info['ip']}:{node_info['port']}/download_file/{file_name}"
            try:
                response = requests.get(file_url, timeout=5)
                if response.status_code == 200:
                    return jsonify({"status": "File found", "url": file_url}), 200
            except requests.exceptions.RequestException:
                continue

        return jsonify({"status": "File not accessible on available nodes"}), 404

@app.route('/view_routing_table', methods=['GET'])
def view_routing_table():
    serializable_routing_table = {
        node: {'files': list(info['files'])} for node, info in routing_table.items()
    }
    return render_template('view_routing_table.html', routing_table=serializable_routing_table)

def replicate_file_to_peers(file_name):
    if file_name not in files:
        print(f"File '{file_name}' not found locally for replication.")
        return

    node_id = f"{local_ip}:{local_port}"
    peers = [peer for peer in routing_table if peer != node_id]
    replication_factor = min(len(peers), 1)
    if replication_factor == 0:
        return
    selected_peers = random.sample(peers, replication_factor)

    try:
        with open(file_name, 'rb') as f:
            file_content = f.read()
    except Exception as e:
        print(f"Error reading file '{file_name}' for replication: {e}")
        return

    for peer_id in selected_peers:
        peer_info = routing_table[peer_id]
        try:
            response = requests.post(
                f"http://{peer_info['ip']}:{peer_info['port']}/replicate_file",
                json={
                    "file_name": file_name,
                    "file_content": file_content.decode('latin1')
                }
            )
            if response.status_code == 200:
                print(f"File '{file_name}' replicated to {peer_info['ip']}:{peer_info['port']}")
        except Exception as e:
            print(f"Failed to replicate file '{file_name}' to {peer_info['ip']}:{peer_info['port']}: {e}")

@app.route('/replicate_file', methods=['POST'])
def replicate_file():
    data = request.get_json()
    file_name = data["file_name"]
    file_content = data["file_content"]

    with open(file_name, 'wb') as f:
        f.write(file_content.encode('latin1'))

    files.add(file_name)

    node_id = f"{local_ip}:{local_port}"
    if node_id not in routing_table:
        routing_table[node_id] = {
            "ip": local_ip,
            "port": local_port,
            "files": {file_name},
            "last_seen": time.time()
        }
    else:
        routing_table[node_id]["files"].add(file_name)

    return jsonify({"status": "File replicated successfully"}), 200

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({"status": "Node is alive"}), 200

def ping_nodes():
    while True:
        current_time = time.time()
        nodes_to_remove = []
        for node_id, node_info in list(routing_table.items()):
            if node_id == f"{local_ip}:{local_port}":
                continue
            try:
                response = requests.get(f"http://{node_info['ip']}:{node_info['port']}/ping", timeout=5)
                if response.status_code == 200:
                    routing_table[node_id]["last_seen"] = current_time
            except requests.exceptions.RequestException:
                if current_time - node_info["last_seen"] > 30:
                    nodes_to_remove.append(node_id)
        for node_id in nodes_to_remove:
            print(f"Removing unreachable node: {node_id}")
            del routing_table[node_id]
        time.sleep(10)

@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/index')
def index():
    return render_template('index.html')

def register_with_peers_on_startup():
    for peer in args.peers:
        peer_ip, peer_port = peer.split(":")
        try:
            requests.post(f"http://{peer_ip}:{peer_port}/register_peer", json={"ip": local_ip, "port": local_port})
        except Exception as e:
            print(f"Failed to register with peer {peer_ip}:{peer_port}: {e}")

if __name__ == "__main__":
    # Register with peers given at startup (fetch RT, announce self)
    register_with_peers_on_startup()

    ping_thread = threading.Thread(target=ping_nodes, daemon=True)
    ping_thread.start()

    app.run(host=local_ip, port=local_port, debug=True)
