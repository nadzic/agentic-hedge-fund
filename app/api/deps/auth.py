import os
from functools import lru_cache
from typing import TypedDict

import httpx
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

class AuthUser(TypedDict):
  sub: str
  email: str | None
  role: str | None