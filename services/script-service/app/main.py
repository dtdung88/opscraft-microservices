"""
Script Service - Main Application
Port: 8002
"""
import sys
sys.path.append('/app')

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from shared.database.session import get_db, create_tables
from shared.security.dependencies import get_current_user_data, require_role

app = FastAPI(title="Script Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger(__name__)