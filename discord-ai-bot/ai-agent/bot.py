#!/usr/bin/env python3
import os
import json
import asyncio
import subprocess
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv
import ollama

load_dotenv(Path(__file__).parent.parent / 'config' / '.env')


@dataclass
class Config:
    model: str
    channels: list[str]
    trigger: str
    system_prompt: str
    poll_interval: int = 3
    context_window: int = 8192
    max_history: int = 10

    @classmethod
    def from_env(cls) -> 'Config':
        # Load system prompt from file if specified
        system_prompt = os.getenv(
            'SYSTEM_PROMPT',
            'You are a helpful AI assistant integrated with Discord.',
        )

        prompt_file = os.getenv('SYSTEM_PROMPT_FILE')
        if prompt_file:
            prompt_path = Path(__file__).parent.parent / prompt_file
            if prompt_path.exists():
                system_prompt = prompt_path.read_text().strip()
            else:
                print(f'⚠️  System prompt file not found: {prompt_path}')
                print('   Using default system prompt')

        return cls(
            model=os.getenv('OLLAMA_MODEL', 'qwen2.5:7b'),
            channels=os.getenv('MONITORED_CHANNEL_IDS', '').split(','),
            trigger=os.getenv('BOT_TRIGGER_PREFIX', '!ai'),
            system_prompt=system_prompt,
        )


class MCPClient:
    def __init__(self, server_path: Path):
        self.server_path = server_path
        self.process: Optional[asyncio.subprocess.Process] = None
        self._request_id = 0

    async def start(self) -> None:
        self.process = await asyncio.create_subprocess_exec(
            'node',
            str(self.server_path),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        print('✅ MCP server started')

    async def stop(self) -> None:
        if self.process:
            self.process.terminate()
            await self.process.wait()
            print('✅ MCP server stopped')

    def _next_id(self) -> int:
        self._request_id += 1
        return self._request_id

    async def _send_request(self, method: str, params: dict = None) -> dict:
        if not self.process:
            raise RuntimeError('MCP server not started')

        request = {
            'jsonrpc': '2.0',
            'id': self._next_id(),
            'method': method,
            'params': params or {},
        }

        request_json = json.dumps(request) + '\n'
        self.process.stdin.write(request_json.encode())
        await self.process.stdin.drain()

        response_line = await self.process.stdout.readline()
        response = json.loads(response_line.decode())

        if 'error' in response:
            raise Exception(f"MCP Error: {response['error']}")

        return response.get('result', {})

    async def call_tool(self, tool_name: str, arguments: dict) -> dict:
        return await self._send_request(
            'tools/call', {'name': tool_name, 'arguments': arguments}
        )

    async def get_messages(self, channel_id: str, limit: int = 10) -> list[dict]:
        result = await self.call_tool(
            'read_discord_messages', {'channel_id': channel_id, 'limit': limit}
        )
        content = result.get('content', [{}])[0].get('text', '{}')
        data = json.loads(content)
        return data.get('messages', [])

    async def send_message(self, channel_id: str, message: str) -> dict:
        return await self.call_tool(
            'send_discord_message', {'channel_id': channel_id, 'message': message}
        )

    async def list_channels(self) -> list[dict]:
        result = await self.call_tool('list_discord_channels', {})
        content = result.get('content', [{}])[0].get('text', '{}')
        data = json.loads(content)
        return data.get('channels', [])


class DiscordAIBot:
    def __init__(self, config: Config):
        self.config = config
        self.mcp: Optional[MCPClient] = None
        self.conversation_history: dict[str, list[dict]] = {}
        self.processed_messages: set[str] = set()

    async def initialize(self) -> None:
        print(f'🚀 Initializing Discord AI Bot')
        print(f'   Model: {self.config.model}')
        print(f'   Trigger: {self.config.trigger}')

        await self._ensure_model_available()

        mcp_server_path = Path(__file__).parent.parent / 'mcp-server' / 'dist' / 'server.js'
        self.mcp = MCPClient(mcp_server_path)
        await self.mcp.start()

        await asyncio.sleep(2)
        print('✅ Bot initialized successfully\n')

    async def _ensure_model_available(self) -> None:
        try:
            models = ollama.list()
            # Handle both dict and object-style access for different ollama library versions
            if hasattr(models, 'models'):
                model_list = models.models
            else:
                model_list = models.get('models', [])

            model_names = []
            for m in model_list:
                if hasattr(m, 'name'):
                    model_names.append(m.name)
                elif isinstance(m, dict):
                    model_names.append(m['name'])

            if not any(self.config.model in name for name in model_names):
                print(f'⬇️  Pulling model {self.config.model}...')
                ollama.pull(self.config.model)
                print(f'✅ Model {self.config.model} downloaded')
        except Exception as e:
            print(f'❌ Error checking Ollama: {e}')
            print('   Make sure Ollama is running: ollama serve')
            raise

    def _build_context(self, channel_id: str, messages: list[dict]) -> list[dict]:
        if channel_id not in self.conversation_history:
            self.conversation_history[channel_id] = []

        for msg in messages:
            msg_id = f"{channel_id}:{msg['id']}"
            if msg_id not in self.processed_messages:
                self.conversation_history[channel_id].append(msg)
                self.processed_messages.add(msg_id)

        # No limit - use ALL messages for analysis
        context = [{'role': 'system', 'content': self.config.system_prompt}]

        for msg in self.conversation_history[channel_id]:
            context.append({
                'role': 'user',
                'content': f"[{msg['author']}]: {msg['content']}",
            })

        print(f"📝 Using {len(self.conversation_history[channel_id])} messages for context")
        return context

    async def _generate_response(self, context: list[dict]) -> str:
        try:
            response = ollama.chat(
                model=self.config.model,
                messages=context,
                options={
                    'temperature': 0.7,
                    'num_ctx': self.config.context_window,
                },
            )
            return response['message']['content']

        except Exception as e:
            error_msg = f'Error generating response: {e}'
            print(f'❌ {error_msg}')
            return error_msg

    async def _process_channel(self, channel_id: str) -> None:
        try:
            # Fetch maximum messages allowed by Discord API (100 per request)
            messages = await self.mcp.get_messages(channel_id, limit=100)

            if not messages:
                return

            last_message = messages[-1]
            msg_id = f"{channel_id}:{last_message['id']}"

            if msg_id in self.processed_messages:
                return

            if not last_message['content'].startswith(self.config.trigger):
                self.processed_messages.add(msg_id)
                return

            print(f"💬 [{last_message['author']}]: {last_message['content'][:50]}...")
            print(f"📊 Fetched {len(messages)} messages for analysis")

            user_message = last_message['content'][len(self.config.trigger) :].strip()
            last_message['content'] = user_message

            context = self._build_context(channel_id, messages)
            response = await self._generate_response(context)

            await self.mcp.send_message(channel_id, response)
            print(f'✅ Response sent\n')

        except Exception as e:
            print(f'❌ Error processing channel {channel_id}: {e}')

    async def run(self) -> None:
        print('👀 Starting monitoring loop...')

        if not self.config.channels or self.config.channels == ['']:
            print('\n⚠️  No channels configured!')
            print('   Listing available channels:\n')

            channels = await self.mcp.list_channels()
            for ch in channels:
                print(f"   • {ch['name']} (ID: {ch['id']}) in {ch['guild']}")

            print('\n   Add channel IDs to MONITORED_CHANNEL_IDS in config/.env')
            return

        print(f"   Monitoring {len(self.config.channels)} channel(s)\n")

        try:
            while True:
                for channel_id in self.config.channels:
                    if channel_id.strip():
                        await self._process_channel(channel_id.strip())

                await asyncio.sleep(self.config.poll_interval)

        except KeyboardInterrupt:
            print('\n\n👋 Shutting down bot...')
        finally:
            if self.mcp:
                await self.mcp.stop()


async def main():
    config = Config.from_env()
    bot = DiscordAIBot(config)

    try:
        await bot.initialize()
        await bot.run()
    except Exception as e:
        print(f'\n❌ Fatal error: {e}')
        if bot.mcp:
            await bot.mcp.stop()
        raise


if __name__ == '__main__':
    asyncio.run(main())
