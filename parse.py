from jinja2 import Template
import json
from datetime import datetime
import requests
from typing import Optional, Dict, Any

def call_fastapi_endpoint(
    url: str,
    method: str = "GET",
    params: Optional[Dict] = None,
    data: Optional[Dict] = None,
    headers: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Makes a request to a FastAPI endpoint and returns the JSON response.
    
    Args:
        url (str): The complete URL of the FastAPI endpoint
        method (str): HTTP method (GET, POST, PUT, DELETE, etc.)
        params (dict, optional): Query parameters for the request
        data (dict, optional): JSON body data for POST/PUT requests
        headers (dict, optional): Request headers
        
    Returns:
        dict: The JSON response from the API
        
    Raises:
        requests.exceptions.RequestException: If the request fails
        ValueError: If the response is not valid JSON
    """
    try:
        # Set default headers if none provided
        if headers is None:
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        
        # Make the request
        response = requests.request(
            method=method.upper(),
            url=url,
            params=params,
            json=data,  # requests will automatically JSON-encode the data
            headers=headers
        )
        
        # Raise an exception for bad status codes
        response.raise_for_status()
        
        # Return the JSON response
        return response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        raise
    except ValueError as e:
        print(f"Failed to parse JSON response: {e}")
        raise
    
# Jinja2 template for miner status
MINER_TEMPLATE = """
=== Miner Status Report ===
📍 IP: {{ miner.ip }}
⏰ Last Update: {{ miner.datetime | format_datetime }}
🔧 Hardware: {{ miner.make }} {{ miner.model }}
📊 Status: {{ "🟢 Active" if miner.is_mining else "🔴 Inactive" }}

📈 Hashrate: {{ miner.hashrate.rate | format_hashrate }} TH/s
🌡️ Average Temperature: {{ miner.temperature_avg }}°C

Hashboards Status:
{% for board in miner.hashboards %}
Board {{ board.slot }}: 
    - Hashrate: {{ board.hashrate.rate | format_hashrate }} TH/s
    - Temperature: {{ board.temp }}°C
    - Chips: {{ board.chips }}/{{ board.expected_chips }}
{% endfor %}

Fan Status:
{% for fan in miner.fans %}
Fan {{ loop.index }}: {{ fan.speed if fan.speed > 0 else "Inactive" }} RPM
{% endfor %}

Pool Information:
{% for pool in miner.pools if pool.url %}
Pool {{ pool.index }}:
    - URL: {{ pool.url.host }}:{{ pool.url.port }}
    - User: {{ pool.user }}
    - Accepted: {{ pool.accepted }}
    - Rejected: {{ "%.2f"|format(pool.pool_rejected_percent) }}%
{% endfor %}
"""

def format_hashrate(rate):
    """Format hashrate to 2 decimal places"""
    return f"{rate:.2f}"

def format_datetime(dt_str):
    """Format datetime string to readable format"""
    dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    return dt.strftime('%Y-%m-%d %H:%M:%S UTC')

def parse_and_display_miner_status(json_data):
    """Parse miner JSON data and display formatted status"""
    # Create Jinja2 template
    template = Template(MINER_TEMPLATE)
    
    # Add custom filters
    template.globals['format_hashrate'] = format_hashrate
    template.globals['format_datetime'] = format_datetime
    
    # Parse JSON if string is provided
    if isinstance(json_data, str):
        data = json.loads(json_data)
    else:
        data = json_data
    
    # Render template
    return template.render(miner=data)

# Example usage
def parse():
    # Example JSON string or dict can be passed

    try:
        response = call_fastapi_endpoint(
            url="http://localhost:9000/miners_dict"
        )
        parse_and_display_miner_status(json.loads(response))
    except Exception as e:
        print(f"Error: {e}")

    # with open('miner_data.json', 'r') as f:
    #     miner_data = json.load(f)
    
    # print(parse_and_display_miner_status(miner_data))