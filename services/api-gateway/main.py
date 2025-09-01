"""
CertCoach API Gateway
Main entry point for all client requests with authentication, routing, and rate limiting
"""

from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
import httpx
from typing import Optional
import os
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="CertCoach API Gateway",
    description="Main API gateway for CertCoach services",
    version="0.1.0",
    docs_url="/docs" if os.getenv("ENVIRONMENT") == "development" else None,
    redoc_url="/redoc" if os.getenv("ENVIRONMENT") == "development" else None,
)

# Security
security = HTTPBearer()

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:19006"],  # Next.js and Expo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.certcoach.com"]
)

# Service endpoints configuration
SERVICES = {
    "planner": {
        "base_url": f"http://localhost:{os.getenv('PLANNER_SERVICE_PORT', 8001)}",
        "prefix": "/api/v1/planner"
    },
    "practice": {
        "base_url": f"http://localhost:{os.getenv('PRACTICE_ENGINE_SERVICE_PORT', 8002)}",
        "prefix": "/api/v1/practice"
    },
    "items": {
        "base_url": f"http://localhost:{os.getenv('ITEM_FACTORY_SERVICE_PORT', 8003)}",
        "prefix": "/api/v1/items"
    },
    "mastery": {
        "base_url": f"http://localhost:{os.getenv('MASTERY_SRS_SERVICE_PORT', 8004)}",
        "prefix": "/api/v1/mastery"
    },
    "explain": {
        "base_url": f"http://localhost:{os.getenv('EXPLAIN_RAG_SERVICE_PORT', 8005)}",
        "prefix": "/api/v1/explain"
    },
    "telemetry": {
        "base_url": f"http://localhost:{os.getenv('TELEMETRY_SERVICE_PORT', 8006)}",
        "prefix": "/api/v1/telemetry"
    }
}

# Rate limiting (in-memory for now, should use Redis in production)
rate_limit_storage = {}

def check_rate_limit(client_ip: str, endpoint: str, limit: int = 60) -> bool:
    """Simple rate limiting implementation"""
    current_time = time.time()
    key = f"{client_ip}:{endpoint}"
    
    if key not in rate_limit_storage:
        rate_limit_storage[key] = []
    
    # Clean old requests (older than 1 minute)
    rate_limit_storage[key] = [
        req_time for req_time in rate_limit_storage[key]
        if current_time - req_time < 60
    ]
    
    # Check if limit exceeded
    if len(rate_limit_storage[key]) >= limit:
        return False
    
    # Add current request
    rate_limit_storage[key].append(current_time)
    return True

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Verify JWT token (placeholder implementation)"""
    # TODO: Implement actual JWT verification
    # This would validate the token signature, expiration, etc.
    token = credentials.credentials
    
    if not token or token == "invalid":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Mock user info (replace with actual token decoding)
    return {
        "user_id": "user_123", 
        "email": "user@example.com",
        "roles": ["student"]
    }

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Apply rate limiting to all requests"""
    client_ip = request.client.host
    endpoint = request.url.path
    
    # Different limits for different endpoint types
    if "/auth/" in endpoint:
        limit = 5  # Stricter for auth endpoints
    elif "/practice/" in endpoint:
        limit = 10  # Moderate for practice
    else:
        limit = 60  # Default limit
    
    if not check_rate_limit(client_ip, endpoint, limit):
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded. Please try again later."}
        )
    
    response = await call_next(request)
    return response

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "CertCoach API Gateway",
        "version": "0.1.0",
        "status": "healthy",
        "timestamp": time.time()
    }

@app.get("/health")
async def health_check():
    """Detailed health check including downstream services"""
    service_health = {}
    
    async with httpx.AsyncClient() as client:
        for service_name, config in SERVICES.items():
            try:
                response = await client.get(
                    f"{config['base_url']}/health",
                    timeout=5.0
                )
                service_health[service_name] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "response_time_ms": response.elapsed.total_seconds() * 1000
                }
            except Exception as e:
                service_health[service_name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
    
    overall_healthy = all(
        service["status"] == "healthy" 
        for service in service_health.values()
    )
    
    return {
        "gateway": "healthy",
        "services": service_health,
        "overall_status": "healthy" if overall_healthy else "degraded"
    }

# Authentication endpoints (placeholder)
@app.post("/auth/login")
async def login(request: Request):
    """User login endpoint"""
    # TODO: Implement actual authentication
    body = await request.json()
    email = body.get("email")
    password = body.get("password")
    
    # Mock authentication
    if email and password:
        return {
            "access_token": "mock_jwt_token",
            "token_type": "bearer",
            "expires_in": 1800,
            "user": {
                "id": "user_123",
                "email": email,
                "roles": ["student"]
            }
        }
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials"
    )

@app.post("/auth/refresh")
async def refresh_token(user: dict = Depends(verify_token)):
    """Refresh JWT token"""
    # TODO: Implement token refresh logic
    return {
        "access_token": "new_mock_jwt_token",
        "token_type": "bearer", 
        "expires_in": 1800
    }

# Service proxy endpoints
async def proxy_request(
    service_name: str,
    path: str,
    request: Request,
    user: dict = Depends(verify_token)
) -> JSONResponse:
    """Proxy requests to backend services"""
    if service_name not in SERVICES:
        raise HTTPException(status_code=404, detail="Service not found")
    
    service_config = SERVICES[service_name]
    target_url = f"{service_config['base_url']}/{path}"
    
    # Add user context to headers
    headers = dict(request.headers)
    headers["X-User-ID"] = user["user_id"]
    headers["X-User-Email"] = user["email"]
    headers["X-User-Roles"] = ",".join(user["roles"])
    
    async with httpx.AsyncClient() as client:
        try:
            if request.method == "GET":
                response = await client.get(
                    target_url,
                    headers=headers,
                    params=request.query_params
                )
            elif request.method == "POST":
                body = await request.body()
                response = await client.post(
                    target_url,
                    headers=headers,
                    content=body
                )
            elif request.method == "PUT":
                body = await request.body()
                response = await client.put(
                    target_url,
                    headers=headers,
                    content=body
                )
            elif request.method == "DELETE":
                response = await client.delete(
                    target_url,
                    headers=headers
                )
            else:
                raise HTTPException(status_code=405, detail="Method not allowed")
            
            return JSONResponse(
                status_code=response.status_code,
                content=response.json() if response.headers.get("content-type", "").startswith("application/json") else {"data": response.text}
            )
            
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Service timeout")
        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail="Service unavailable")
        except Exception as e:
            logger.error(f"Proxy error for {service_name}: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

# Route all service requests through the gateway
@app.api_route("/api/v1/planner/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def planner_proxy(path: str, request: Request, user: dict = Depends(verify_token)):
    return await proxy_request("planner", path, request, user)

@app.api_route("/api/v1/practice/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def practice_proxy(path: str, request: Request, user: dict = Depends(verify_token)):
    return await proxy_request("practice", path, request, user)

@app.api_route("/api/v1/items/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def items_proxy(path: str, request: Request, user: dict = Depends(verify_token)):
    return await proxy_request("items", path, request, user)

@app.api_route("/api/v1/mastery/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def mastery_proxy(path: str, request: Request, user: dict = Depends(verify_token)):
    return await proxy_request("mastery", path, request, user)

@app.api_route("/api/v1/explain/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def explain_proxy(path: str, request: Request, user: dict = Depends(verify_token)):
    return await proxy_request("explain", path, request, user)

@app.api_route("/api/v1/telemetry/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def telemetry_proxy(path: str, request: Request, user: dict = Depends(verify_token)):
    return await proxy_request("telemetry", path, request, user)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=os.getenv("API_GATEWAY_HOST", "0.0.0.0"),
        port=int(os.getenv("API_GATEWAY_PORT", 8000)),
        log_level="info"
    )
