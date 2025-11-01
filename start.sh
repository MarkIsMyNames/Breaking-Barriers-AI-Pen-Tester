#!/bin/bash
set -e

echo "Discord AI Bot with Qwen2.5"
echo "==========================="
echo

if [ ! -f config/.env ]; then
    echo "❌ Config file not found!"
    echo "   cp config/.env.example config/.env"
    echo "   nano config/.env"
    exit 1
fi

if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama not installed!"
    echo "   curl -fsSL https://ollama.com/install.sh | sh"
    exit 1
fi

if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
    echo "⚠️  Starting Ollama..."
    ollama serve &
    sleep 3
fi

export $(grep -v '^#' config/.env | xargs)

MODEL=${OLLAMA_MODEL:-qwen2.5:7b}
echo "Checking model: $MODEL"

if ! ollama list | grep -q "${MODEL%:*}"; then
    echo "⬇️  Pulling model..."
    ollama pull "$MODEL"
fi

if [ ! -d "mcp-server/node_modules" ]; then
    echo "📦 Installing Node.js dependencies..."
    cd mcp-server && npm install && cd ..
fi

if [ ! -d "mcp-server/dist" ]; then
    echo "🔨 Building TypeScript..."
    cd mcp-server && npm run build && cd ..
fi

echo "📦 Installing Python dependencies..."
pip3 install -q -r ai-agent/requirements.txt

echo
echo "✅ Starting bot..."
echo

cd ai-agent
python3 bot.py
