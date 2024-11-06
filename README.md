# pyasic-api

A RESTful API wrapper for pyasic that provides easy access to ASIC miner information and management capabilities.

## Features

- Scan network subnets for ASIC miners
- Retrieve detailed miner information
- Get miner configurations
- Check miner error states
- Async implementation for efficient performance

## API Endpoints

### GET /miners
Scans a subnet for miners and returns data for all discovered devices.
- Query parameter: `subnet` (default: "10.66.10.0/24")
- Returns: Array of miner data objects

### GET /miner/{ip}
Retrieves detailed information for a specific miner.
- Path parameter: `ip` (miner's IP address)
- Returns: Miner data object

### GET /miner/{ip}/config
Fetches configuration details for a specific miner.
- Path parameter: `ip` (miner's IP address)
- Returns: Miner configuration object

### GET /miner/{ip}/errors
Gets error information from a specific miner.
- Path parameter: `ip` (miner's IP address)
- Returns: Object containing miner errors

## Installation

1. Clone the repository:
``git clone https://github.com/yourusername/pyasic-api.git```

2. Install dependencies:
```pip install fastapi uvicorn pyasic`

## Usage

Start the API server:
``python app.py`

The API will be available at http://localhost:9000

## Example Requests

Get all miners in a subnet:
`curl http://localhost:9000/miners?subnet=192.168.1.0/24`

Get specific miner data:
`curl http://localhost:9000/miner/192.168.1.100`

## Docker Deployment

### Using Docker Compose (Recommended)

1. Build and start the container:
`docker-compose up -d`

### Using Docker CLI
1. Build the Docker image:
   `docker build -t pyasic-api .`
2. Run the Docker container:
   `docker run -d -p 9000:9000 pyasic-api`

## Pre-built Docker Image
You can directly use the pre-built Docker image available on Docker Hub: signalorange/pyasic-api.

## Requirements

Python 3.7+
FastAPI
uvicorn
pyasic

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

Built with pyasic
Powered by FastAPI