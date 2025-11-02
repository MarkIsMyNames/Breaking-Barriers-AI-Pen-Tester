# Pen Tester AI

AI-powered penetration testing toolkit for security awareness training and authorized security assessments. This project combines local language models with practical security testing tools.

## Overview

Pen Tester AI is a collection of AI-driven tools designed for cybersecurity professionals, red teams, and organizations conducting authorized security assessments. All tools run locally, ensuring privacy and control over sensitive data.

## Components

### 1. Email Creator (Phishing Simulation)
AI-powered phishing email generator using Qwen3-8B for security awareness training and penetration testing.

- **Model**: Qwen3-8B (5GB GGUF format)
- **Interface**: Web-based Gradio UI
- **Processing**: 100% local, no cloud dependencies
- **Use Cases**: Employee security training, phishing campaign testing, awareness programs

[View Email Creator Documentation](Email%20creater/README.md)

### 2. Discord AI Bot
Local Discord bot powered by Qwen2.5-7B via Ollama, designed for security-focused interactions.

- **Model**: Qwen2.5-7B via Ollama
- **Technology**: Python + TypeScript MCP server
- **Integration**: Discord API with custom commands
- **Features**: Conversation context, customizable system prompts

[View Discord Bot Documentation](discord-ai-bot/README.md)
