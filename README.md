# PagePal: Your AI buddy for chatting with websites

<p align="center">
  <img src="./assets/logo.webp" alt="PagePal Logo" width="250"/>
</p>

## About PagePal

PagePal is your intelligent AI-powered Telegram bot that transforms any website into a conversational experience. Simply send a URL, and PagePal will crawl the content, extract key insights, and let you chat with the data using advanced AI. Whether you're researching articles, summarizing pages, or querying specific details, PagePal makes web interaction seamless and intuitive.

## Description

🔹 **Instant Website Crawling** – Send a URL, and PagePal will analyze its content.  
🔹 **AI-Powered Conversations** – Ask questions and get precise answers from the webpage.  
🔹 **Summarization & Insights** – Get key takeaways without reading the entire page.  
🔹 **Easy Telegram Integration** – No need for extra apps; chat directly in Telegram.  
🔹 **Fast & Reliable** – Uses advanced LLMs to process and understand content efficiently.

🚀 Try PagePal and turn the web into your personal AI assistant!

<p align="center">
  <img src="./assets/qr_code.png" alt="PagePal Telegram Bot QR Code" width="300"/>
  <br>
  <em>Scan to access @PAGE_PAL_619_BOT on Telegram</em>
</p>

## Features

- **Web Crawling**: Crawl any website URL sent by users
- **Intelligent Chunking**: Automatically process and chunk content for optimal retrieval
- **Vector Storage**: Store embeddings for efficient retrieval using ChromaDB
- **Conversational Interface**: Maintain conversation context for follow-up questions
- **Source Attribution**: Include source URLs in answers for transparency
- **Content Caching**: Cache website content to avoid unnecessary recrawling
- **Supabase Integration**: Use PostgreSQL for persistent storage
- **Response Streaming**: See the AI response as it's being generated in real-time

## Architecture

PagePal uses a modular and maintainable architecture:

- **Bot Module**: Handles Telegram interactions and user messages
- **Crawler Module**: Manages website crawling and content processing
- **RAG Module**: Handles embeddings, LLM, and Q&A chains
- **Database Module**: Manages persistent storage with Supabase
- **Vector Store Module**: Manages document embeddings with ChromaDB

## Prerequisites

- Python 3.12+
- Pipenv
- Telegram Bot Token (from BotFather)
- Google AI API Key (for Gemini models)
- Supabase account (free tier available)
- Crawl4AI API Token
- Docker and Docker Compose (for containerized deployment)

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/pagepal.git
   cd pagepal
   ```

2. Set up the environment with Pipenv:

   ```bash
   pipenv install
   ```

3. Create a `.env` file from the example:

   ```bash
   cp .env.example .env
   ```

4. Edit the `.env` file with your API keys and configuration.

## Usage

### Running with Pipenv

1. Start the bot:

   ```bash
   pipenv run start
   ```

### Running with Docker

1. Build and start the containers:

   ```bash
   docker-compose up -d
   ```

2. Open Telegram and find your bot.

3. Send a website URL to start crawling.

4. Once crawled, ask questions about the website content.

## Available Commands

- `/start`: Introduction message
- `/help`: Shows available commands
- `/status`: Shows current website context
- `/reset`: Resets conversation history

## Streaming Responses

PagePal supports streaming responses, which means:

- You'll see the bot's responses appear word by word in real-time
- Long answers don't require waiting until completion
- The experience feels more interactive and engaging
- Sources are added at the end of the streamed response

You can disable streaming by setting `STREAMING_ENABLED=False` in your `.env` file.

## Development

### Project Structure

```bash
pagepal/               # Main package
├── __init__.py
├── config.py          # Configuration and settings
├── main.py            # Application entry point
│
├── bot/               # Telegram bot functionality
│   ├── __init__.py
│   ├── handlers.py    # Message handlers
│   ├── commands.py    # Bot commands
│   └── utils.py       # Bot utilities
│
├── crawler/           # Web crawling functionality
│   ├── __init__.py
│   ├── crawler.py     # Crawler integration
│   └── processor.py   # Content processing
│
├── db/                # Database functionality
│   ├── __init__.py
│   ├── supabase.py    # Supabase client
│   └── vector_store.py # Vector database operations
│
├── rag/               # RAG functionality
│   ├── __init__.py
│   ├── embeddings.py  # Embedding models
│   ├── llm.py         # LLM models
│   ├── chains.py      # LangChain chains
│   └── prompts.py     # Prompt templates
|
|__ tools/             # Tools
│   |__ __init__.py
|   |__ crawl4ai.py    # Cral4AI API wrapper
|
└── utils/             # Utility functions
    ├── __init__.py
    └── logger.py      # Logging configurati

```

### Code Formatting

```bash
pipenv run format
pipenv run lint
```

## Docker Deployment

The bot includes Docker and Docker Compose configurations that set up:

1. **PagePal**: The main bot service
2. **Crawl4AI**: The crawling service that handles website scraping

The services are linked via a Docker network and volume for persistent data.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Privacy Policy

PagePal is an AI-powered bot that allows users to interact with website content. By using this bot, you agree to the following:

- **No Ownership:** I do not own or control any content retrieved from websites.
- **No Guarantees:** Information provided may not be accurate or up to date. AI can make mistakes.
- **Educational Use Only:** Do not use this bot for financial, medical, or legal purposes.
- **Website Compliance:** PagePal respects website privacy policies and does not crawl pages blocked by robots.txt.
- **User Responsibility:** Use this bot at your own risk. Always review the website’s privacy policy before interacting.

By using PagePal, you acknowledge these terms. 🚀
