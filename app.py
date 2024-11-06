import uvicorn
from fastapi import FastAPI
from typing import List, Dict
import asyncio
from pyasic.network import MinerNetwork
from pyasic import get_miner
import os
from dotenv import load_dotenv
from pyasic import settings
import yaml

def load_settings():
    # Define settings mapping
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

app = FastAPI()

@app.get("/miners")
async def get_miners(subnet: str = "10.66.10.0/24"):
    # Create a network scanner for the given subnet
    network = MinerNetwork.from_subnet(subnet)
    # Scan for miners
    miners = await network.scan()
    
    # Gather all miner data concurrently
    miner_data = await asyncio.gather(*[miner.get_data() for miner in miners])
    
    # Convert each MinerData instance to dict for JSON response
    return [data.as_dict() for data in miner_data]

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
    uvicorn.run(app, port=9000)