# Using Cherry with AI agent

This project demonstrates the integration of Cherry ETL with an AI agent to fetch and process ERC20 token events from Ethereum blockchain.

## Quickstart

```bash
uv sync
python src/cherry_ai_experiment/agent.py --provider sqd

# Try with prompt
python src/cherry_ai_experiment/agent.py \
--provider sqd \
--prompt 'Get all logs from contract address 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48 with event signature Transfer(address indexed from, address indexed to, uint256 amount)'
```

## Features

- Uses GPT-4 to parse natural language queries into structured event filters
- Supports multiple data providers (Hypersync and SQD)
- Streams and decodes ERC20 token events
- Configurable block range and event signature filtering

## Prerequisites

- Python 3.12 or higher
- OpenAI API key set in environment variables
- Access to either Hypersync or SQD data providers
