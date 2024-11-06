import uvicorn
from fastapi import FastAPI
from typing import List, Dict
import asyncio
from pyasic.network import MinerNetwork
from pyasic import get_miner

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

if __name__ == "__main__":
    uvicorn.run(app, port=9000)