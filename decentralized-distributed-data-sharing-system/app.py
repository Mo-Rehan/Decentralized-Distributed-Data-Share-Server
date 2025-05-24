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
parser.add_argument('--ip', type=str, default="127.0.0.1", help="Port to run the Flask app on")
parser.add_argument('--port', type=int, default=5000, help="Port to run the Flask app on")
parser.add_argument('--peers', nargs='*', default=[], help="List of peers in the format IP:Port")
args = parser.parse_args()

local_ip = args.ip
local_port = args.port

files = set()  # Files available on this node
routing_table = {}  # Other nodes and their files

# Hashing function for unique file identification
def get_file_hash(file_name):
    return hashlib.sha256(file_name.encode()).hexdigest()

# Function to simulate file storage for testing
def save_file(file_name):
    with open(file_name, 'rb') as f:
        file_data = f.read()


# Route for uploading a file
# @app.route('/add_file', methods=['POST'])
# def add_file():
#     file_name = request.json["file_name"]
#     file_hash = get_file_hash(file_name)
#     files.add(file_name)
#     save_file(file_name)  # Simulate file storage for testing
    
#     node_id = f"{local_ip}:{local_port}"
#     routing_table[node_id] = {
#         "ip": local_ip,
#         "port": local_port,
#         "files": files,
#         "last_seen": time.time()
#     }

#     # Announce the file to peers
#     for peer_id, peer_info in routing_table.items():
#         if peer_id != node_id:
#             announce_file_to_peer(peer_info["ip"], peer_info["port"], file_name)
    
#     return jsonify({"status": "File added", "hash": file_hash}), 200

# Announce file to peer
def announce_file_to_peer(peer_ip, peer_port, file_name):
    try:
        response = requests.post(f"http://{peer_ip}:{peer_port}/announce_file", json={"file": file_name, "node": f"{local_ip}:{local_port}"})
        if response.status_code == 200:
            print(f"File '{file_name}' announced to {peer_ip}:{peer_port}")
    except Exception as e:
        print(f"Failed to announce file '{file_name}' to {peer_ip}:{peer_port}: {e}")

# Endpoint for receiving file announcements
@app.route('/announce_file', methods=['POST'])
def announce_file():
    data = request.get_json()
    file_name = data["file"]
    node = data["node"]
    if node in routing_table:
        routing_table[node]["files"].add(file_name)
    else:
        ip, port = node.split(":")
        routing_table[node] = {
            "ip": ip,
            "port": int(port),
            "files": {file_name},
            "last_seen": time.time()
        }
    return jsonify({"status": "success"}), 200

# Register node to another peer for discovery
@app.route('/register_peer', methods=['GET', 'POST'])
def register_peer():
    if request.method == 'POST':
        peer_ip = request.json["ip"]
        peer_port = request.json["port"]
        try:
            response = requests.post(f"http://{peer_ip}:{peer_port}/announce_peer", json={"ip": local_ip, "port": local_port, "files": list(files)})
            if response.status_code == 200:
                print(f"Registered with peer {peer_ip}:{peer_port}")
        except Exception as e:
            print(f"Failed to register with peer {peer_ip}:{peer_port}: {e}")
        return jsonify({"status": "Peer registered"}), 200

    return render_template('register_peer.html')  # Render the register peer page

# Endpoint to handle peer registration
@app.route('/announce_peer', methods=['POST'])
def announce_peer():
    data = request.get_json()
    ip = data["ip"]
    port = data["port"]
    node_id = f"{ip}:{port}"
    routing_table[node_id] = {
        "ip": ip,
        "port": port,
        "files": set(data["files"]),
        "last_seen": time.time()
    }
    return jsonify({"status": "success"}), 200

# Request a file from the network
@app.route('/request_file', methods=['GET', 'POST'])
def request_file():
    if request.method == 'GET':
        # Render the request_file.html template
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
                # Check if the file is accessible from this node
                response = requests.get(file_url, timeout=5)
                if response.status_code == 200:
                    return jsonify({"status": "File found", "url": file_url}), 200
            except requests.exceptions.RequestException:
                # If a node is unreachable, try the next one
                continue

        return jsonify({"status": "File not accessible on available nodes"}), 404
    


# Endpoint to download file
@app.route('/download_file/<file_name>', methods=['GET'])
def download_file(file_name):
    if file_name in files:
        try:
            return send_file(file_name, as_attachment=True)
        except Exception as e:
            return jsonify({"status": "Error", "message": str(e)}), 500
    return jsonify({"status": "File not available on this node"}), 404

# View routing table
@app.route('/view_routing_table', methods=['GET'])
def view_routing_table():
    serializable_routing_table = {
        node: {'files': list(info['files'])} for node, info in routing_table.items()
    }
    return render_template('view_routing_table.html', routing_table=serializable_routing_table)

# Gossip protocol to share routing table information with all peers
def gossip_routing_table():
    peer_ids = list(routing_table.keys())
    random.shuffle(peer_ids)
    
    # Gossip to all known peers
    for peer_id in peer_ids:
        peer_info = routing_table[peer_id]
        
        # Create a serializable version of the routing table
        serializable_routing_table = {
            node_id: {
                "ip": node_info["ip"],
                "port": node_info["port"],
                "files": list(node_info["files"]),  # Convert set to list
                "last_seen": node_info["last_seen"]
            }
            for node_id, node_info in routing_table.items()
        }
        
        try:
            response = requests.post(
                f"http://{peer_info['ip']}:{peer_info['port']}/update_routing_table",
                json={"routing_table": serializable_routing_table}  # Send serialized routing table
            )
            if response.status_code == 200:
                print(f"Gossiped with {peer_info['ip']}:{peer_info['port']}")
        except Exception as e:
            print(f"Failed to gossip with {peer_info['ip']}:{peer_info['port']}: {e}")

# Endpoint to receive routing table updates
@app.route('/update_routing_table', methods=['POST'])
def update_routing_table():
    incoming_routing_table = request.get_json()["routing_table"]
    for node_id, node_info in incoming_routing_table.items():
        if node_id in routing_table:
            routing_table[node_id]["last_seen"] = node_info["last_seen"]
            routing_table[node_id]["files"].update(node_info["files"])
        else:
            routing_table[node_id] = {
                "ip": node_info["ip"],
                "port": node_info["port"],
                "files": set(node_info["files"]),
                "last_seen": node_info["last_seen"]
            }
    return jsonify({"status": "success"}), 200

# Frontend
@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/index')
def index():
    return render_template('index.html')

# Register and gossip with peers at startup
def register_and_gossip_with_peers():
    # Register with all peers provided at startup
    for peer in args.peers:
        peer_ip, peer_port = peer.split(":")
        requests.post(f"http://{peer_ip}:{peer_port}/register_peer", json={"ip": local_ip, "port": local_port})
    # Start gossiping in the background
    while True:
        gossip_routing_table()
        time.sleep(3)  # Gossip every 10 seconds

replication_factor = 2  # Number of nodes to replicate each file

# Route for uploading a file with replication
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


    return render_template('upload.html')  # Render the upload page

# Function to replicate a file to other peers
def replicate_file_to_peers(file_name):
    if file_name not in files:
        print(f"File '{file_name}' not found locally for replication.")
        return

    node_id = f"{local_ip}:{local_port}"
    peers = [peer for peer in routing_table if peer != node_id]
    replication_factor = min(len(peers), 1)  # Replicate to up to 3 peers
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

# Endpoint to receive replicated files
# Endpoint to receive replicated files
@app.route('/replicate_file', methods=['POST'])
def replicate_file():
    data = request.get_json()
    file_name = data["file_name"]
    file_content = data["file_content"]  # File content sent as base64

    # Save the replicated file locally
    with open(file_name, 'wb') as f:
        f.write(file_content.encode('latin1'))  # Convert back to bytes

    # Add to local file list
    files.add(file_name)

    # Update the routing table for this node
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

def ping_nodes():
    while True:
        current_time = time.time()
        nodes_to_remove = []

        for node_id, node_info in list(routing_table.items()):
            try:
                response = requests.get(f"http://{node_info['ip']}:{node_info['port']}/ping", timeout=5)
                if response.status_code == 200:
                    routing_table[node_id]["last_seen"] = current_time
            except requests.exceptions.RequestException:
                # Mark node for removal if unreachable for a long time
                if current_time - node_info["last_seen"] > 30:  # 30 seconds threshold
                    nodes_to_remove.append(node_id)

        for node_id in nodes_to_remove:
            print(f"Removing unreachable node: {node_id}")
            del routing_table[node_id]

        time.sleep(10)  # Ping every 10 seconds


@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({"status": "Node is alive"}), 200


# Start gossip thread
if __name__ == "__main__":
    gossip_thread = threading.Thread(target=register_and_gossip_with_peers, daemon=True)
    gossip_thread.start()

    ping_thread = threading.Thread(target=ping_nodes, daemon=True)
    ping_thread.start()

    app.run(host=local_ip, port=local_port, debug=True)
