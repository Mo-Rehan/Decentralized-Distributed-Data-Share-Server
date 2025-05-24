document.addEventListener("DOMContentLoaded", () => {
    /**
     * Utility function to send JSON POST requests.
     * @param {string} url - The endpoint URL.
     * @param {Object} data - Data to send in the request body.
     * @returns {Promise<Object>} - The response data.
     */
    const postData = async (url, data) => {
        try {
            const response = await fetch(url, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(data),
            });
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || "Request failed");
            }
            return await response.json();
        } catch (error) {
            console.error("Error:", error);
            throw error;
        }
    };

    /**
     * Handle file upload form submission.
     */
    const handleFileUpload = () => {
        const form = document.getElementById("uploadForm");
        const status = document.getElementById("uploadStatus");
        if (form) {
            form.addEventListener("submit", async (e) => {
                e.preventDefault();
                const fileName = document.getElementById("fileName").value.trim();

                if (!fileName) {
                    status.textContent = "Error: File name is required.";
                    return;
                }

                try {
                    const result = await postData("/upload", { file_name: fileName });
                    status.textContent = `Success: File uploaded with hash ${result.hash}`;
                } catch (error) {
                    status.textContent = `Error: ${error.message}`;
                }
            });
        }
    };

    /**
     * Handle peer registration form submission.
     */
    const handlePeerRegistration = () => {
        const form = document.getElementById("peerForm");
        const status = document.getElementById("peerStatus");
        if (form) {
            form.addEventListener("submit", async (e) => {
                e.preventDefault();
                const peerIp = document.getElementById("peerIp").value.trim();
                const peerPort = document.getElementById("peerPort").value.trim();

                if (!peerIp || !peerPort) {
                    status.textContent = "Error: Peer IP and Port are required.";
                    return;
                }

                try {
                    const result = await postData("/register_peer", {
                        ip: peerIp,
                        port: peerPort,
                    });
                    status.textContent = `Success: ${result.status}`;
                } catch (error) {
                    status.textContent = `Error: ${error.message}`;
                }
            });
        }
    };

    /**
     * Handle file request form submission.
     */
    const handleFileRequest = () => {
        const form = document.getElementById("requestForm");
        const status = document.getElementById("requestStatus");
        if (form) {
            form.addEventListener("submit", async (e) => {
                e.preventDefault();
                const fileName = document.getElementById("fileName").value.trim();

                if (!fileName) {
                    status.textContent = "Error: File name is required.";
                    return;
                }

                try {
                    const result = await postData("/request_file", { file_name: fileName });
                    if (result.status === "File found") {
                        status.innerHTML = `Success: File found! <a href="${result.url}" target="_blank">Download here</a>`;
                    } else {
                        status.textContent = `Error: ${result.status}`;
                    }
                } catch (error) {
                    status.textContent = `Error: ${error.message}`;
                }
            });
        }
    };

    /**
     * Initialize the JavaScript handlers.
     */
    const init = () => {
        handleFileUpload();
        handlePeerRegistration();
        handleFileRequest();
    };

    init();
    const canvas = document.getElementById("webCanvas");
const ctx = canvas.getContext("2d");
canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

const particles = [];
const maxParticles = 180; // Decreased number of particles
const lineDistance = 150; // Increased distance for visible webs
let mouse = { x: null, y: null };

// Particle Class
class Particle {
    constructor(x, y) {
        this.x = x || Math.random() * canvas.width;
        this.y = y || Math.random() * canvas.height;
        this.speedX = (Math.random() - 0.5) * 1.5;
        this.speedY = (Math.random() - 0.5) * 1.5;
        this.size = Math.random() * 4 + 2; // Reduced size range
    }

    update() {
        this.x += this.speedX;
        this.y += this.speedY;

        // Bounce off edges
        if (this.x < 0 || this.x > canvas.width) this.speedX *= -1;
        if (this.y < 0 || this.y > canvas.height) this.speedY *= -1;

        // Attract to mouse
        const dx = mouse.x - this.x;
        const dy = mouse.y - this.y;
        const distance = Math.sqrt(dx * dx + dy * dy);

        if (distance < 150) {
            this.x += dx / distance;
            this.y += dy / distance;
        }
    }

    draw() {
        ctx.beginPath();
        const gradient = ctx.createRadialGradient(this.x, this.y, 0, this.x, this.y, this.size * 5);
        gradient.addColorStop(0, "rgba(0, 229, 255, 1)");
        gradient.addColorStop(1, "rgba(0, 229, 255, 0)");
        ctx.fillStyle = gradient;
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.fill();
    }
}

// Create particles
const createParticles = () => {
    for (let i = 0; i < maxParticles; i++) {
        particles.push(new Particle());
    }
};

// Connect particles with lines
const connectParticles = () => {
    for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
            const dx = particles[i].x - particles[j].x;
            const dy = particles[i].y - particles[j].y;
            const distance = Math.sqrt(dx * dx + dy * dy);

            if (distance < lineDistance) {
                ctx.beginPath();
                ctx.moveTo(particles[i].x, particles[i].y);
                ctx.lineTo(particles[j].x, particles[j].y);
                ctx.strokeStyle = `rgba(0, 229, 255, ${1 - distance / lineDistance})`;
                ctx.lineWidth = 1; // Slightly thinner lines
                ctx.stroke();
                ctx.closePath();
            }
        }
    }
};

// Animate particles
const animateParticles = () => {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    particles.forEach((particle) => {
        particle.update();
        particle.draw();
    });

    connectParticles();

    requestAnimationFrame(animateParticles);
};

// Mouse Interaction
window.addEventListener("mousemove", (event) => {
    mouse.x = event.clientX;
    mouse.y = event.clientY;
});

// Reset mouse position on leave
window.addEventListener("mouseout", () => {
    mouse.x = null;
    mouse.y = null;
});

// Resize canvas on window resize
window.addEventListener("resize", () => {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
});

// Initialize particles and start animation
createParticles();
animateParticles();

    
});

