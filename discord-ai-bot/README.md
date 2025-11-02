# Discord AI Bot with Qwen2.5

Local Discord bot powered by Qwen2.5-7B via Ollama and MCP.

## Features

- **Local Processing**: Runs Qwen2.5-7B completely on your machine
- **Discord Integration**: Responds to messages via Model Context Protocol
- **Conversation Context**: Maintains conversation history
- **TypeScript**: Type-safe MCP server
- **Clean Python**: Readable, well-structured bot code

## Quick Start

### 1. Install Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### 2. Start Ollama & Pull Model

```bash
# Terminal 1
ollama serve

# Terminal 2 (downloads ~4.4GB)
ollama pull qwen2.5:7b
```

### 3. Create Discord Bot

1. Go to https://discord.com/developers/applications
2. Create application → Add Bot
3. Enable **Message Content Intent** (Privileged Gateway Intents)
4. Copy bot token
5. OAuth2 → URL Generator:
   - Scopes: `bot`
   - Permissions: `Read Messages`, `Send Messages`, `Read Message History`
6. Use generated URL to invite bot

### 4. Configure

```bash
cd discord-ai-bot
cp config/.env.example config/.env
nano config/.env
```

Add your Discord token and channel IDs.

**Get Channel IDs**: Discord Settings → Advanced → Enable Developer Mode → Right-click channel → Copy ID

### 5. Run

```bash
./start.sh
```

## Configuration

`config/.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `DISCORD_TOKEN` | Discord bot token | Required |
| `MONITORED_CHANNEL_IDS` | Comma-separated channel IDs | Empty |
| `OLLAMA_MODEL` | Ollama model | `qwen2.5:7b` |
| `BOT_TRIGGER_PREFIX` | Message trigger | `!ai` |
| `SYSTEM_PROMPT` | AI system prompt | Default |

## Model Options

| Model | RAM | Speed | Quality |
|-------|-----|-------|---------|
| `qwen2.5:7b` | 8GB | ⚡⚡⚡ | ⭐⭐⭐ |
| `qwen2.5:14b` | 16GB | ⚡⚡ | ⭐⭐⭐⭐ |
| `qwen2.5:32b` | 32GB | ⚡ | ⭐⭐⭐⭐⭐ |

## Troubleshooting

**Bot not responding?**
- Check Message Content Intent is enabled
- Verify channel ID in `MONITORED_CHANNEL_IDS`
- Ensure message starts with trigger prefix

**Connection refused?**
- Run `ollama serve`

## Project Structure

```
discord-ai-bot/
├── ai-agent/
│   ├── bot.py              # Main Python bot
│   └── requirements.txt
├── mcp-server/
│   ├── src/
│   │   └── server.ts       # TypeScript MCP server
│   ├── package.json
│   └── tsconfig.json
├── config/
│   └── .env.example
├── start.sh
└── README.md
```

## Development

Build TypeScript:
```bash
cd mcp-server
npm run build
```

Run bot:
```bash
cd ai-agent
python3 bot.py
```
