from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
import uuid, secrets, time

app = FastAPI()

# MongoDB setup
MONGO_DETAILS = "mongodb://localhost:27017/"
client = AsyncIOMotorClient(MONGO_DETAILS)
db = client.tododb
policyholders_collection = db.policyholders
clients_collection = db.clients

print("Connected to DB:", db.name)
print("Using collection:", policyholders_collection.name)

# --- Models ---

class RegisterClientRequest(BaseModel):
    client_name: str

class RegisterClientResponse(BaseModel):
    client_id: str
    client_secret: str

class TokenRequest(BaseModel):
    client_id: str
    client_secret: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class PolicyHolderRequest(BaseModel):
    polNum: str
    lastName: str

class PolicyHolderResponse(BaseModel):
    policyNumber: str
    Status: Optional[str]
    DecentFirstName: Optional[str]
    DecentLastName: Optional[str]

# --- In-Memory Token Store (for demo, replace with Redis or DB in prod) ---
tokens = {}

# --- Security ---
security = HTTPBearer()

# --- Routes ---


@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI application! CICD check"}

@app.post("/register-client", response_model=RegisterClientResponse, tags=["Auth"])
async def register_client(data: RegisterClientRequest):
    client_id = str(uuid.uuid4())
    client_secret = secrets.token_urlsafe(32)

    # Store client in DB
    await clients_collection.insert_one({
        "client_id": client_id,
        "client_secret": client_secret,
        "client_name": data.client_name,
        "created_at": time.time()
    })

    return RegisterClientResponse(client_id=client_id, client_secret=client_secret)


@app.post("/get-token", response_model=TokenResponse, tags=["Auth"])
async def get_token(data: TokenRequest):
    client_data = await clients_collection.find_one({"client_id": data.client_id})

    if not client_data or client_data["client_secret"] != data.client_secret:
        raise HTTPException(status_code=401, detail="Invalid client credentials")

    # Generate access token (random string for demo)
    token = secrets.token_urlsafe(32)
    tokens[token] = {"client_id": data.client_id, "created": time.time()}

    return TokenResponse(access_token=token)


# Dependency to verify token
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    if token not in tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token",
        )
    return token


@app.post("/get-policyholder", response_model=PolicyHolderResponse, tags=["Policyholder"])
async def get_policyholder(
    request_data: PolicyHolderRequest,
    token: str = Depends(verify_token)
):
    query = {
        "polNum": request_data.polNum,
        "DecentLastName": request_data.lastName
    }
    policyholder = await policyholders_collection.find_one(query)

    if not policyholder:
        raise HTTPException(status_code=404, detail="Policyholder not found")

    return PolicyHolderResponse(
        policyNumber=policyholder.get("polNum", ""),
        Status=policyholder.get("polContractStatus", ""),
        DecentFirstName=policyholder.get("DecentFirstName", ""),
        DecentLastName=policyholder.get("DecentLastName", "")
    )
