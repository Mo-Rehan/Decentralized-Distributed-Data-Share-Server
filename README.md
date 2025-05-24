Peer-to-Peer File Sharing Network
A distributed file-sharing system built using Flask that enables nodes to:

Upload and share files

Discover files across peers

Maintain decentralized routing tables via a gossip protocol

Ensure availability through file replication

Detect and handle peer failures with periodic ping checks

This project demonstrates core principles of decentralized networking, fault tolerance, and peer coordination.

📌 Features
✅ Decentralized Peer Discovery — No central server required

🔄 Gossip Protocol — Periodic exchange of routing data among peers

🧩 File Replication — Redundant storage for high availability

🔍 File Request & Retrieval — Seamless file lookup across the network

🧠 Fault Detection — Automatic removal of unresponsive nodes

🌐 Web Interface — User-friendly interaction for file sharing and monitoring

🚀 Getting Started
🔧 Prerequisites
Ensure Python 3.7+ is installed.

Install dependencies:

bash
Copy
Edit
pip install flask requests

Running the Application
🖥️ On a Single Machine (Simulated Network)
Use different ports to simulate multiple nodes:

bash
Copy
Edit
# Terminal 1 (Node A)
python app.py --port 5000

# Terminal 2 (Node B)
python app.py --port 5001 --peers 127.0.0.1:5000

# Terminal 3 (Node C)
python app.py --port 5002 --peers 127.0.0.1:5000 127.0.0.1:5001
🌐 On a Local Network (Different Machines)
Ensure all machines are connected to the same LAN and firewalls allow communication.

Step 1: Get Local IPs
Use ipconfig (Windows) or ifconfig/ip a (Linux/macOS) to find each machine’s IP.

Step 2: Start Nodes
On Machine A:

bash
Copy
Edit
python app.py --ip 192.168.1.10 --port 5000
On Machine B:

bash
Copy
Edit
python app.py --ip 192.168.1.11 --port 5001 --peers 192.168.1.10:5000
On Machine C:

bash
Copy
Edit
python app.py --ip 192.168.1.12 --port 5002 --peers 192.168.1.10:5000 192.168.1.11:5001
Ensure that the IPs are accessible by pinging across machines.

🌐 Web Interface
Once the app is running, open in a browser:

php-template
Copy
Edit
http://<node-ip>:<port>
🔹 Available Pages
Route	Description
/ or /index	Landing page
/upload	Upload and replicate a file
/request_file	Request a file from the network
/register_peer	Register a new peer manually
/view_routing_table	View the known peers and their files

🛠️ How It Works
📡 Gossip Protocol
Nodes periodically exchange routing tables to learn about new peers and files.

🔁 File Replication
Each file is replicated to other nodes (replication_factor = 2 by default) to ensure durability.

🧠 Health Checks
Each node pings peers every 10 seconds. Unreachable nodes (for 30+ seconds) are automatically removed.

⚙️ Configuration Options
Argument	Type	Description
--ip	string	IP address to bind (default: 127.0.0.1)
--port	int	Port to run the node on (default: 5000)
--peers	list	List of initial peers in ip:port format

📦 Future Enhancements
 Docker support for deployment

 NAT traversal (e.g., STUN/TURN)

 File search with metadata filters

 Role-based access or authentication

 Upload via drag & drop UI

 CLI client integration
