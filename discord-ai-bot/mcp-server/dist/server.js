import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { CallToolRequestSchema, ListToolsRequestSchema, } from '@modelcontextprotocol/sdk/types.js';
import { Client, GatewayIntentBits } from 'discord.js';
import dotenv from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
dotenv.config({ path: join(__dirname, '../../config/.env') });
const DISCORD_TOKEN = process.env.DISCORD_TOKEN;
const ALLOWED_CHANNEL_IDS = process.env.ALLOWED_CHANNEL_IDS?.split(',').filter(Boolean) || [];
if (!DISCORD_TOKEN) {
    console.error('❌ DISCORD_TOKEN not found in environment variables');
    process.exit(1);
}
const discord = new Client({
    intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent,
    ],
});
const mcpServer = new Server({
    name: 'discord-mcp-server',
    version: '1.0.0',
}, {
    capabilities: {
        tools: {},
        resources: {},
    },
});
discord.on('clientReady', () => {
    console.error(`✅ Discord bot logged in as ${discord.user?.tag}`);
});
function isChannelAllowed(channelId) {
    if (ALLOWED_CHANNEL_IDS.length === 0)
        return true;
    return ALLOWED_CHANNEL_IDS.includes(channelId);
}
function createTextResponse(text) {
    return {
        content: [{ type: 'text', text }],
    };
}
function createErrorResponse(error) {
    const message = error instanceof Error ? error.message : String(error);
    return `Error: ${message}`;
}
async function handleSendMessage(channelId, message) {
    if (!isChannelAllowed(channelId)) {
        return createTextResponse(`Error: Channel ${channelId} is not in the allowed channels list`);
    }
    try {
        const channel = await discord.channels.fetch(channelId);
        if (!channel || !channel.isTextBased()) {
            throw new Error('Invalid channel or not a text channel');
        }
        // Type guard to ensure channel has send method
        if (!('send' in channel)) {
            throw new Error('Channel does not support sending messages');
        }
        const sentMessage = await channel.send(message);
        return createTextResponse(JSON.stringify({
            success: true,
            message_id: sentMessage.id,
            channel_id: channelId,
            content: message,
        }));
    }
    catch (error) {
        return createTextResponse(createErrorResponse(error));
    }
}
async function handleReadMessages(channelId, limit = 10) {
    try {
        const channel = await discord.channels.fetch(channelId);
        if (!channel || !channel.isTextBased()) {
            throw new Error('Invalid channel or not a text channel');
        }
        const messages = await channel.messages.fetch({
            limit: Math.min(limit, 100),
        });
        const formattedMessages = messages.map((msg) => ({
            id: msg.id,
            author: msg.author.username,
            content: msg.content,
            timestamp: msg.createdAt.toISOString(),
            attachments: msg.attachments.map((att) => att.url),
        }));
        return createTextResponse(JSON.stringify({
            channel_id: channelId,
            messages: formattedMessages.reverse(),
        }));
    }
    catch (error) {
        return createTextResponse(createErrorResponse(error));
    }
}
async function handleListChannels() {
    try {
        const channelList = [];
        for (const [, guild] of discord.guilds.cache) {
            const channels = guild.channels.cache
                .filter((ch) => ch.isTextBased())
                .map((ch) => ({
                id: ch.id,
                name: ch.name,
                guild: guild.name,
                type: ch.type,
            }));
            channelList.push(...channels);
        }
        return createTextResponse(JSON.stringify({ channels: channelList }));
    }
    catch (error) {
        return createTextResponse(createErrorResponse(error));
    }
}
mcpServer.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;
    if (!args) {
        throw new Error('Missing arguments');
    }
    const typedArgs = args;
    switch (name) {
        case 'send_discord_message':
            return handleSendMessage(typedArgs.channel_id, typedArgs.message);
        case 'read_discord_messages':
            return handleReadMessages(typedArgs.channel_id, typedArgs.limit);
        case 'list_discord_channels':
            return handleListChannels();
        default:
            throw new Error(`Unknown tool: ${name}`);
    }
});
mcpServer.setRequestHandler(ListToolsRequestSchema, async () => {
    return {
        tools: [
            {
                name: 'send_discord_message',
                description: 'Send a message to a Discord channel',
                inputSchema: {
                    type: 'object',
                    properties: {
                        channel_id: {
                            type: 'string',
                            description: 'Discord channel ID',
                        },
                        message: {
                            type: 'string',
                            description: 'Message content to send',
                        },
                    },
                    required: ['channel_id', 'message'],
                },
            },
            {
                name: 'read_discord_messages',
                description: 'Read recent messages from a Discord channel',
                inputSchema: {
                    type: 'object',
                    properties: {
                        channel_id: {
                            type: 'string',
                            description: 'Discord channel ID',
                        },
                        limit: {
                            type: 'number',
                            description: 'Number of messages to fetch (max 100)',
                            default: 10,
                        },
                    },
                    required: ['channel_id'],
                },
            },
            {
                name: 'list_discord_channels',
                description: 'List all available Discord channels the bot has access to',
                inputSchema: {
                    type: 'object',
                    properties: {},
                },
            },
        ],
    };
});
async function main() {
    try {
        await discord.login(DISCORD_TOKEN);
        const transport = new StdioServerTransport();
        await mcpServer.connect(transport);
        console.error('✅ Discord MCP Server started successfully');
    }
    catch (error) {
        console.error('❌ Failed to start server:', error);
        process.exit(1);
    }
}
main();
//# sourceMappingURL=server.js.map