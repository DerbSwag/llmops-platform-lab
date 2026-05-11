#!/bin/bash
# ============================================================
# LLMOps Platform Lab — One-Click VM Setup
# OS: Ubuntu 22.04 Server
# Run: curl -sSL https://raw.githubusercontent.com/DerbSwag/llmops-platform-lab/main/setup-vm.sh | bash
# ============================================================

set -e

echo "=========================================="
echo "  LLMOps Platform Lab — VM Setup"
echo "=========================================="

# --- 1. System Update ---
echo "[1/6] Updating system..."
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl git htop

# --- 2. Install Docker ---
echo "[2/6] Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker $USER
    sudo systemctl enable docker
    echo "Docker installed. You may need to re-login for group changes."
fi
docker --version

# --- 3. Install Docker Compose ---
echo "[3/6] Installing Docker Compose..."
sudo apt install -y docker-compose-plugin
docker compose version

# --- 4. Install Ollama ---
echo "[4/6] Installing Ollama..."
if ! command -v ollama &> /dev/null; then
    curl -fsSL https://ollama.com/install.sh | sh
fi
ollama --version

# --- 5. Clone Project + Pull Models ---
echo "[5/6] Cloning project & pulling models..."
cd ~
if [ ! -d "llmops-platform-lab" ]; then
    git clone https://github.com/DerbSwag/llmops-platform-lab.git
fi
cd llmops-platform-lab

# Pull AI model
ollama pull qwen2.5

# Create IT Bot
ollama create it-bot -f models/Modelfile.it-bot

# --- 6. Start Services ---
echo "[6/6] Starting services..."
docker compose up -d

# --- Done ---
echo ""
echo "=========================================="
echo "  ✅ Setup Complete!"
echo "=========================================="
echo ""
echo "  Services:"
echo "  - LLM Gateway:  http://$(hostname -I | awk '{print $1}'):8000/docs"
echo "  - RAG Service:  http://$(hostname -I | awk '{print $1}'):8001/docs"
echo "  - Grafana:      http://$(hostname -I | awk '{print $1}'):3000"
echo "  - Prometheus:   http://$(hostname -I | awk '{print $1}'):9090"
echo "  - Ollama API:   http://$(hostname -I | awk '{print $1}'):11434"
echo ""
echo "  Test IT Bot:"
echo "  ollama run it-bot 'ปริ้นไม่ออก'"
echo ""
echo "  Stop:  docker compose down"
echo "  Start: docker compose up -d"
echo "=========================================="
