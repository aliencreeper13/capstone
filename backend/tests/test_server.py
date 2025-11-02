# server.py
from fastapi import FastAPI, WebSocket
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import asyncio
print("runnig")
app = FastAPI()

# Simple model
class SimpleCity(BaseModel):
    population: int
    wealth: int

# Example city state (could come from your game engine)
city = SimpleCity(population=1000, wealth=500)

@app.get("/city")
async def get_city():
    """Regular endpoint: client can fetch snapshot of city data."""
    return JSONResponse(content=city.model_dump())

@app.websocket("/ws/city")
async def websocket_city(websocket: WebSocket):
    """WebSocket endpoint: sends real-time updates."""
    await websocket.accept()
    try:
        while True:
            # Example: update city data periodically
            city.population += 5
            city.wealth += 10

            # Send JSON-encoded city data
            await websocket.send_json(city.model_dump())

            await asyncio.sleep(2)  # Send updates every 2 seconds
    except Exception:
        await websocket.close()
