# ============================================================================
# EXECUTION SERVICE
# services/execution-service/app/main.py
# ============================================================================
"""
Execution Service - Main Application
Port: 8003
Handles execution lifecycle and WebSocket connections
"""
import sys
sys.path.append('/app')

from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Dict, Set
from celery import Celery
import asyncio
import json
import os

from shared.database.session import get_db, create_tables
from shared.security.dependencies import get_current_user_data
from shared.security.auth import decode_token

app = FastAPI(title="Execution Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Celery client to executor service
celery_client = Celery(broker=os.getenv("CELERY_BROKER_URL"))