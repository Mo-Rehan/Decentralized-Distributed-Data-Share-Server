📂 P2P File Sharing System (Flask-based)

This project implements a peer-to-peer (P2P) file-sharing network using Flask as the backend framework.
Each node in the network runs as a Flask server, can upload, announce, request, replicate, and download files, and maintains a routing table of peers and their available files.

The system supports:

File upload & replication across peers

Peer registration & routing table exchange

File request & distributed downloading

Heartbeat monitoring to remove unreachable nodes

🚀 Features
1. Peer-to-Peer Networking

Each node is a server (IP:Port) that connects with peers at startup or runtime.

Nodes share files and metadata with each other.

2. File Management

Upload Files (/upload) → Add file to local storage & announce to peers.

Download Files (/download_file/<file_name>) → Retrieve file if available locally.

Request Files (/request_file) → Search network for file availability & download from peers.

Replication → Files are replicated to at least one peer for redundancy.

3. Peer Discovery & Routing

Register Peer (/register_peer) → Share routing tables, merge knowledge of the network.

Announce Peer (/announce_peer) → Notify others about a new peer & its files.

Routing Table (/get_routing_table, /view_routing_table) → Maintains live map of peers, files, and last-seen timestamps.

4. Health Monitoring

Heartbeat/Ping (/ping) → Check peer availability.

Ping Thread → Periodically pings all known peers. If a peer is unresponsive for 30+ seconds, it is removed from the routing table.

5. Web Interface

Basic HTML templates for:

Upload files (upload.html)

Request files (request_file.html)

View routing table (view_routing_table.html)

Landing & Index pages (landing.html, index.html)

⚙️ Installation & Setup
1. Clone the repository
git clone https://github.com/yourusername/p2p-file-sharing.git
cd p2p-file-sharing

2. Install dependencies
pip install flask requests

3. Run a node
python app.py --ip 127.0.0.1 --port 5000 --peers 127.0.0.1:5001 127.0.0.1:5002


Arguments:

--ip → IP address to bind (default 127.0.0.1)

--port → Port number (default 5000)

--peers → Space-separated list of peer addresses (IP:Port)

Example:

python app.py --ip 127.0.0.1 --port 5001 --peers 127.0.0.1:5000

🛠️ API Endpoints
File Operations

POST /upload → Upload and announce a file

GET /download_file/<file_name> → Download file if available locally

POST /request_file → Search and download file from peers

Peer Operations

POST /register_peer → Register a peer & exchange routing tables

POST /announce_peer → Announce presence to the network

GET /get_routing_table → Fetch raw routing table (JSON)

GET /view_routing_table → View routing table in HTML

Replication & Announcements

POST /announce_file → Notify peers about new file

POST /replicate_file → Accept replicated file from a peer

Health Monitoring

GET /ping → Check if node is alive

UI Pages

/ → Landing page

/index → Main index

/upload → Upload page

/request_file → Request file page

/view_routing_table → Routing table page

🔄 Workflow

Node Startup

Node starts Flask server at given IP:Port.

Registers with provided peers (--peers).

Fetches and merges routing tables.

File Upload

User uploads a file → File is hashed & added to local storage.

File announcement sent to peers.

File replicated to at least one peer.

File Request

User requests a file.

Node searches its routing table for peers holding the file.

If found, file is downloaded from available peer.

Peer Monitoring

Background thread pings peers every 10s.

If a peer is unreachable for 30+ seconds, it is removed.

📦 Example Usage
Start Node 1:
python app.py --ip 127.0.0.1 --port 5000

Start Node 2 (connect to Node 1):
python app.py --ip 127.0.0.1 --port 5001 --peers 127.0.0.1:5000

Upload file on Node 1:
curl -X POST http://127.0.0.1:5000/upload -H "Content-Type: application/json" -d '{"file_name": "sample.txt"}'

Request file on Node 2:
curl -X POST http://127.0.0.1:5001/request_file -H "Content-Type: application/json" -d '{"file_name": "sample.txt"}'

⚠️ Limitations & Future Improvements

No authentication → Any peer can join.

No chunked file transfer → Large files may be inefficient.

Replication factor fixed to 1 → Can be improved with configurable redundancy.

No DHT (Distributed Hash Table) → Routing is limited to peers’ routing tables.

Files are read/written directly → No dedicated storage directory.

📖 License

MIT License. Free to use and modify.
