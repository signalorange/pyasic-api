import uvicorn
from fastapi import FastAPI
from redis import asyncio as aioredis
import json
from typing import List, Dict
import asyncio
from contextlib import asynccontextmanager
from asyncio import create_task, Task
from pyasic.network import MinerNetwork
from pyasic import get_miner
import os
from pyasic import settings
import yaml
import subprocess
import time

# Load subnets from environment variable
SUBNETS = os.getenv('SCAN_SUBNETS', '10.66.10.0/24').split(',')
SCAN_INTERVAL = int(os.getenv('SCAN_INTERVAL', '300'))  # 5 minutes default

    
class RedisCache:
    def __init__(self, redis_url: str = "redis://localhost"):
        self.redis = aioredis.from_url(redis_url, decode_responses=True)
        
    async def set_miners_data(self, subnet: str, miners_data: List[Dict]):
        # Store miners data with subnet as key, expire after 5 minutes
        await self.redis.set(f"miners:{subnet}", miners_data, ex=SCAN_INTERVAL)
        
    async def get_miners_data(self, subnet: str):
        data = await self.redis.get(f"miners:{subnet}")
        return json.loads(data) if data else None
    
def start_redis_server():
    # Start Redis server in the background
    redis_process = subprocess.Popen(['redis-server'])
    # Give Redis a moment to start up
    time.sleep(1)
    return redis_process

def load_settings():
    # Define settings mapping
    SUBNETS = os.getenv('SCAN_SUBNETS', '10.66.10.0/24').split(',')
    settings_map = {
        "NETWORK_PING_RETRIES": ("network_ping_retries", int, 1),
        "NETWORK_PING_TIMEOUT": ("network_ping_timeout", int, 3),
        "NETWORK_SCAN_SEMAPHORE": ("network_scan_semaphore", int, None),
        "FACTORY_GET_RETRIES": ("factory_get_retries", int, 1),
        "FACTORY_GET_TIMEOUT": ("factory_get_timeout", int, 3),
        "GET_DATA_RETRIES": ("get_data_retries", int, 1),
        "API_FUNCTION_TIMEOUT": ("api_function_timeout", int, 5),
        "ANTMINER_MINING_MODE_AS_STR": ("antminer_mining_mode_as_str", bool, False),
        "WHATSMINER_RPC_PASSWORD": ("default_whatsminer_rpc_password", str, "admin"),
        "INNOSILICON_WEB_PASSWORD": ("default_innosilicon_web_password", str, "admin"),
        "ANTMINER_WEB_PASSWORD": ("default_antminer_web_password", str, "root"),
        "BOSMINER_WEB_PASSWORD": ("default_bosminer_web_password", str, "root"),
        "VNISH_WEB_PASSWORD": ("default_vnish_web_password", str, "admin"),
        "GOLDSHELL_WEB_PASSWORD": ("default_goldshell_web_password", str, "123456789"),
        "AURADINE_WEB_PASSWORD": ("default_auradine_web_password", str, "admin"),
        "EPIC_WEB_PASSWORD": ("default_epic_web_password", str, "letmein"),
        "HIVE_WEB_PASSWORD": ("default_hive_web_password", str, "admin"),
        "ANTMINER_SSH_PASSWORD": ("default_antminer_ssh_password", str, "miner"),
        "BOSMINER_SSH_PASSWORD": ("default_bosminer_ssh_password", str, "root"),
        "SOCKET_LINGER_TIME": ("socket_linger_time", int, 1000),
    }

    # Try to load config file
    config = {}
    if os.path.exists('config.yaml'):
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)

    # Update settings from environment variables or config file
    for env_key, (setting_key, type_cast, default) in settings_map.items():
        # Priority: ENV > config.yaml > default
        value = os.getenv(env_key) or config.get(env_key.lower()) or default
        
        # Cast value to correct type
        if value is not None:
            if type_cast == bool:
                value = str(value).lower() in ('true', '1', 'yes')
            else:
                value = type_cast(value)
            
            # Update pyasic setting
            settings.update(setting_key, value)

redis_process = start_redis_server()

## Initialize cache and background tasks set
cache = RedisCache()
background_tasks: set[Task] = set()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create periodic scan task
    async def periodic_scan_task():
        while True:
            try:
                for subnet in SUBNETS:
                    subnet = subnet.strip()
                    network = MinerNetwork.from_subnet(subnet)
                    miners = await network.scan()
                    miner_data = await asyncio.gather(*[miner.get_data() for miner in miners])
                    await cache.set_miners_data(subnet, [data.as_json() for data in miner_data])
                    print(f"Completed scan of subnet {subnet}")
            except Exception as e:
                print(f"Error during periodic scan: {str(e)}")
            
            await asyncio.sleep(SCAN_INTERVAL)

    # Start the background task
    task = create_task(periodic_scan_task())
    background_tasks.add(task)
    
    yield
    
    # Shutdown: Clean up tasks
    for task in background_tasks:
        task.cancel()
    await asyncio.gather(*background_tasks, return_exceptions=True)


app = FastAPI(lifespan=lifespan)

#app = FastAPI()
# Add to existing imports
cache = RedisCache()

# @app.get("/miners")
# async def get_miners(subnet: str = "10.66.10.0/24"):
#     # Create a network scanner for the given subnet
#     network = MinerNetwork.from_subnet(subnet)
#     # Scan for miners
#     miners = await network.scan()
    
#     # Gather all miner data concurrently
#     miner_data = await asyncio.gather(*[miner.get_data() for miner in miners])
    
#     # Convert each MinerData instance to dict for JSON response
#     return [data.as_dict() for data in miner_data]

@app.get("/miners")
async def get_miners(subnet: str = "10.66.10.0/24"):
    # scan network and cache results
    network = MinerNetwork.from_subnet(subnet)
    miners = await network.scan()
    miner_data = await asyncio.gather(*[miner.get_data() for miner in miners])
    data = [data.as_json() for data in miner_data]
    
    # Store in cache
    await cache.set_miners_data(subnet, data)
    return data

@app.get("/cache/miners")
async def get_miners(subnet: str = "10.66.10.0/24"):
    # Try to get from cache first
    cached_data = await cache.get_miners_data(subnet)
    if cached_data:
        return cached_data
    # If not in cache, scan network and cache results
    return get_miners(subnet)

@app.get("/miner/{ip}")
async def get_single_miner(ip: str):
    miner = await get_miner(ip)
    if miner:
        data = await miner.get_data()
        return data.as_dict()
    return {"error": "Miner not found"}

@app.get("/miner/{ip}/config")
async def get_miner_config(ip: str):
    miner = await get_miner(ip)
    if miner:
        config = await miner.get_config()
        return config.as_dict()
    return {"error": "Miner not found"}

@app.get("/miner/{ip}/errors")
async def get_miner_errors(ip: str):
    miner = await get_miner(ip)
    if miner:
        errors = await miner.get_errors()
        return {"errors": errors}
    return {"error": "Miner not found"}

@app.post("/miner/{ip}/fault-light/on")
async def turn_fault_light_on(ip: str):
    miner = await get_miner(ip)
    if miner:
        result = await miner.fault_light_on()
        return {"status": "success", "result": result}
    return {"error": "Miner not found"}

@app.post("/miner/{ip}/fault-light/off")
async def turn_fault_light_off(ip: str):
    miner = await get_miner(ip)
    if miner:
        result = await miner.fault_light_off()
        return {"status": "success", "result": result}
    return {"error": "Miner not found"}

@app.get("/miner/{ip}/check-light")
async def check_light(ip: str):
    miner = await get_miner(ip)
    if miner:
        result = await miner.check_light()
        return {"status": "success", "light_status": result}
    return {"error": "Miner not found"}

@app.post("/miner/{ip}/reboot")
async def reboot_miner(ip: str):
    miner = await get_miner(ip)
    if miner:
        result = await miner.reboot()
        return {"status": "success", "result": result}
    return {"error": "Miner not found"}

@app.post("/miner/{ip}/restart-backend")
async def restart_miner_backend(ip: str):
    miner = await get_miner(ip)
    if miner:
        result = await miner.restart_backend()
        return {"status": "success", "result": result}
    return {"error": "Miner not found"}

@app.post("/miner/{ip}/stop")
async def stop_miner(ip: str):
    miner = await get_miner(ip)
    if miner:
        result = await miner.stop_mining()
        return {"status": "success", "result": result}
    return {"error": "Miner not found"}

@app.post("/miner/{ip}/resume")
async def resume_miner(ip: str):
    miner = await get_miner(ip)
    if miner:
        result = await miner.resume_mining()
        return {"status": "success", "result": result}
    return {"error": "Miner not found"}

@app.get("/miner/{ip}/mining-status")
async def get_mining_status(ip: str):
    miner = await get_miner(ip)
    if miner:
        result = await miner.is_mining()
        return {"status": "success", "is_mining": result}
    return {"error": "Miner not found"}

@app.post("/miner/{ip}/config")
async def set_miner_config(ip: str, config: dict):
    miner = await get_miner(ip)
    if miner:
        result = await miner.send_config(config)
        return {"status": "success", "result": result}
    return {"error": "Miner not found"}

@app.post("/miner/{ip}/power-limit")
async def set_miner_power_limit(ip: str, limit: int):
    miner = await get_miner(ip)
    if miner:
        result = await miner.set_power_limit(limit)
        return {"status": "success", "result": result}
    return {"error": "Miner not found"}

if __name__ == "__main__":
    load_settings()
    uvicorn.run(app, host="0.0.0.0", port=9000)
    # try:
    #     uvicorn.run(app, host="0.0.0.0", port=9000)
    # finally:
    #     # Clean up Redis server on shutdown
    #     redis_process.terminate()