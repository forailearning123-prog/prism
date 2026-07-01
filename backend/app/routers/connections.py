from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/connections", tags=["connections"])

class ConnectionResponse(BaseModel):
    id: str
    name: str
    type: str
    status: str

connections_db = []

@router.get("/", response_model=List[ConnectionResponse])
async def list_connections():
    return connections_db

@router.post("/")
async def create_connection(conn: ConnectionResponse):
    connections_db.append(conn)
    return conn

@router.post("/{conn_id}/test")
async def test_connection(conn_id: str):
    return {"status": "success", "message": "Connection test successful"}
