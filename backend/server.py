from fastapi import FastAPI, APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import httpx
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from enum import Enum

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== MODELS ====================

class User(BaseModel):
    user_id: str
    email: str
    name: str
    picture: Optional[str] = None
    created_at: datetime

class UserSession(BaseModel):
    user_id: str
    session_token: str
    expires_at: datetime
    created_at: datetime

class SessionDataResponse(BaseModel):
    id: str
    email: str
    name: str
    picture: Optional[str] = None
    session_token: str

class Wallet(BaseModel):
    user_id: str
    coins_balance: float = 0.0
    stars_balance: float = 0.0
    bonus_balance: float = 0.0
    withdrawable_balance: float = 0.0
    total_deposited: float = 0.0
    total_withdrawn: float = 0.0
    created_at: datetime
    updated_at: datetime

class TransactionType(str, Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    VIP_SUBSCRIPTION = "vip_subscription"
    VIP_RENEWAL = "vip_renewal"
    BONUS = "bonus"
    GAME_BET = "game_bet"
    GAME_WIN = "game_win"
    TRANSFER = "transfer"
    ACTIVITY_REWARD = "activity_reward"
    DAILY_REWARD = "daily_reward"
    REFERRAL_COMMISSION = "referral_commission"
    CHARITY_CONTRIBUTION = "charity_contribution"

class TransactionStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class WalletTransaction(BaseModel):
    transaction_id: str
    user_id: str
    transaction_type: TransactionType
    amount: float
    currency_type: str = "coins"
    status: TransactionStatus
    reference_id: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime

class VIPLevel(BaseModel):
    level: int
    name: str
    recharge_requirement: float
    monthly_fee: float
    charity_bonus: float = 0.0
    free_spins_daily: int = 0
    education_discount: float = 0.0
    priority_support: bool = False
    withdrawal_priority: bool = False
    exclusive_games: bool = False
    badge_color: str = "#808080"
    icon: str = "star"

class UserVIPStatus(BaseModel):
    user_id: str
    vip_level: int = 0
    subscription_start: Optional[datetime] = None
    subscription_end: Optional[datetime] = None
    total_recharged: float = 0.0
    is_active: bool = False
    auto_renew: bool = True
    created_at: datetime
    updated_at: datetime

class Notification(BaseModel):
    notification_id: str
    user_id: str
    title: str
    message: str
    notification_type: str
    is_read: bool = False
    action_url: Optional[str] = None
    created_at: datetime

# ==================== VIP LEVELS DATA ====================

VIP_LEVELS_DATA = [
    {
        "level": 0,
        "name": "Basic",
        "recharge_requirement": 0,
        "monthly_fee": 0,
        "charity_bonus": 0,
        "free_spins_daily": 0,
        "education_discount": 0,
        "priority_support": False,
        "withdrawal_priority": False,
        "exclusive_games": False,
        "badge_color": "#808080",
        "icon": "user"
    },
    {
        "level": 1,
        "name": "Bronze",
        "recharge_requirement": 500,
        "monthly_fee": 99,
        "gaming_bonus": 5,
        "free_spins_daily": 2,
        "education_discount": 5,
        "priority_support": False,
        "withdrawal_priority": False,
        "exclusive_games": False,
        "badge_color": "#CD7F32",
        "icon": "star"
    },
    {
        "level": 2,
        "name": "Silver",
        "recharge_requirement": 2000,
        "monthly_fee": 299,
        "gaming_bonus": 10,
        "free_spins_daily": 5,
        "education_discount": 10,
        "priority_support": True,
        "withdrawal_priority": False,
        "exclusive_games": False,
        "badge_color": "#C0C0C0",
        "icon": "star"
    },
    {
        "level": 3,
        "name": "Gold",
        "recharge_requirement": 5000,
        "monthly_fee": 599,
        "gaming_bonus": 15,
        "free_spins_daily": 10,
        "education_discount": 15,
        "priority_support": True,
        "withdrawal_priority": True,
        "exclusive_games": True,
        "badge_color": "#FFD700",
        "icon": "crown"
    },
    {
        "level": 4,
        "name": "Platinum",
        "recharge_requirement": 15000,
        "monthly_fee": 999,
        "gaming_bonus": 20,
        "free_spins_daily": 20,
        "education_discount": 20,
        "priority_support": True,
        "withdrawal_priority": True,
        "exclusive_games": True,
        "badge_color": "#E5E4E2",
        "icon": "crown"
    },
    {
        "level": 5,
        "name": "Diamond",
        "recharge_requirement": 50000,
        "monthly_fee": 1999,
        "gaming_bonus": 30,
        "free_spins_daily": 50,
        "education_discount": 30,
        "priority_support": True,
        "withdrawal_priority": True,
        "exclusive_games": True,
        "badge_color": "#B9F2FF",
        "icon": "diamond"
    }
]

# ==================== AUTH HELPERS ====================

async def get_session_token(request: Request) -> Optional[str]:
    """Get session token from cookie or Authorization header"""
    # Try cookie first
    session_token = request.cookies.get("session_token")
    if session_token:
        return session_token
    
    # Try Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:]
    
    return None

async def get_current_user(request: Request) -> User:
    """Get current user from session token"""
    session_token = await get_session_token(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = await db.user_sessions.find_one(
        {"session_token": session_token},
        {"_id": 0}
    )
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    # Check expiry (handle timezone-naive datetimes from MongoDB)
    expires_at = session["expires_at"]
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Session expired")
    
    user_doc = await db.users.find_one(
        {"user_id": session["user_id"]},
        {"_id": 0}
    )
    if not user_doc:
        raise HTTPException(status_code=401, detail="User not found")
    
    return User(**user_doc)

async def get_optional_user(request: Request) -> Optional[User]:
    """Get current user if authenticated, None otherwise"""
    try:
        return await get_current_user(request)
    except HTTPException:
        return None

# ==================== AUTH ENDPOINTS ====================

@api_router.post("/auth/session")
async def exchange_session(request: Request, response: Response):
    """Exchange session_id for session_token"""
    body = await request.json()
    session_id = body.get("session_id")
    
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")
    
    # Exchange session_id with Emergent Auth
    async with httpx.AsyncClient() as client:
        try:
            auth_response = await client.get(
                "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
                headers={"X-Session-ID": session_id}
            )
            
            if auth_response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid session_id")
            
            user_data = auth_response.json()
            session_data = SessionDataResponse(**user_data)
            
        except httpx.RequestError as e:
            logger.error(f"Auth request failed: {e}")
            raise HTTPException(status_code=500, detail="Auth service unavailable")
    
    # Generate our own user_id
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    
    # Check if user exists by email
    existing_user = await db.users.find_one({"email": session_data.email}, {"_id": 0})
    
    if existing_user:
        user_id = existing_user["user_id"]
    else:
        # Create new user
        await db.users.insert_one({
            "user_id": user_id,
            "email": session_data.email,
            "name": session_data.name,
            "picture": session_data.picture,
            "created_at": datetime.now(timezone.utc)
        })
        
        # Create wallet for new user
        await db.wallets.insert_one({
            "user_id": user_id,
            "coins_balance": 1000.0,  # Welcome bonus
            "stars_balance": 0.0,
            "bonus_balance": 100.0,  # Bonus balance
            "withdrawable_balance": 0.0,
            "total_deposited": 0.0,
            "total_withdrawn": 0.0,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        })
        
        # Create VIP status for new user
        await db.vip_status.insert_one({
            "user_id": user_id,
            "vip_level": 0,
            "subscription_start": None,
            "subscription_end": None,
            "total_recharged": 0.0,
            "is_active": False,
            "auto_renew": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        })
        
        # Add welcome notification
        await db.notifications.insert_one({
            "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
            "user_id": user_id,
            "title": "Welcome to VIP Club! 🎉",
            "message": "You've received 1000 coins and 100 bonus as a welcome gift!",
            "notification_type": "welcome",
            "is_read": False,
            "action_url": "/wallet",
            "created_at": datetime.now(timezone.utc)
        })
    
    # Create session
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    await db.user_sessions.insert_one({
        "user_id": user_id,
        "session_token": session_data.session_token,
        "expires_at": expires_at,
        "created_at": datetime.now(timezone.utc)
    })
    
    # Set cookie
    response.set_cookie(
        key="session_token",
        value=session_data.session_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=7 * 24 * 60 * 60
    )
    
    # Get user data
    user_doc = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    
    return {
        "success": True,
        "user": user_doc,
        "session_token": session_data.session_token
    }

@api_router.get("/auth/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user info"""
    return current_user

@api_router.post("/auth/logout")
async def logout(request: Request, response: Response):
    """Logout user"""
    session_token = await get_session_token(request)
    
    if session_token:
        await db.user_sessions.delete_one({"session_token": session_token})
    
    response.delete_cookie(key="session_token", path="/")
    
    return {"success": True, "message": "Logged out successfully"}

@api_router.get("/auth/check")
async def check_auth(request: Request):
    """Check if user is authenticated"""
    user = await get_optional_user(request)
    return {"authenticated": user is not None, "user": user}

# ==================== WALLET ENDPOINTS ====================

@api_router.get("/wallet")
async def get_wallet(current_user: User = Depends(get_current_user)):
    """Get user's wallet"""
    wallet = await db.wallets.find_one(
        {"user_id": current_user.user_id},
        {"_id": 0}
    )
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    
    return wallet

@api_router.get("/wallet/transactions")
async def get_transactions(
    limit: int = 20,
    offset: int = 0,
    transaction_type: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get user's wallet transactions"""
    query = {"user_id": current_user.user_id}
    if transaction_type:
        query["transaction_type"] = transaction_type
    
    transactions = await db.wallet_transactions.find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).skip(offset).limit(limit).to_list(limit)
    
    total = await db.wallet_transactions.count_documents(query)
    
    return {
        "transactions": transactions,
        "total": total,
        "limit": limit,
        "offset": offset
    }

class DepositRequest(BaseModel):
    amount: float

@api_router.post("/wallet/deposit")
async def deposit(
    request: DepositRequest,
    current_user: User = Depends(get_current_user)
):
    """Deposit coins to wallet (mock - for MVP)"""
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    
    if request.amount > 100000:
        raise HTTPException(status_code=400, detail="Maximum deposit is 100,000")
    
    # Update wallet
    wallet = await db.wallets.find_one_and_update(
        {"user_id": current_user.user_id},
        {
            "$inc": {
                "coins_balance": request.amount,
                "total_deposited": request.amount
            },
            "$set": {"updated_at": datetime.now(timezone.utc)}
        },
        return_document=True,
        projection={"_id": 0}
    )
    
    # Create transaction
    transaction_id = f"txn_{uuid.uuid4().hex[:12]}"
    await db.wallet_transactions.insert_one({
        "transaction_id": transaction_id,
        "user_id": current_user.user_id,
        "transaction_type": TransactionType.DEPOSIT,
        "amount": request.amount,
        "currency_type": "coins",
        "status": TransactionStatus.COMPLETED,
        "description": f"Deposit of {request.amount} coins",
        "created_at": datetime.now(timezone.utc)
    })
    
    # Update VIP recharge total
    await db.vip_status.update_one(
        {"user_id": current_user.user_id},
        {
            "$inc": {"total_recharged": request.amount},
            "$set": {"updated_at": datetime.now(timezone.utc)}
        }
    )
    
    # Check for VIP eligibility
    vip_status = await db.vip_status.find_one(
        {"user_id": current_user.user_id},
        {"_id": 0}
    )
    
    # Find eligible VIP level
    eligible_level = 0
    for level_data in VIP_LEVELS_DATA:
        if vip_status["total_recharged"] >= level_data["recharge_requirement"]:
            eligible_level = level_data["level"]
    
    # Add notification
    await db.notifications.insert_one({
        "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
        "user_id": current_user.user_id,
        "title": "Deposit Successful! 💰",
        "message": f"Your deposit of {request.amount} coins has been credited.",
        "notification_type": "wallet",
        "is_read": False,
        "action_url": "/wallet",
        "created_at": datetime.now(timezone.utc)
    })
    
    return {
        "success": True,
        "wallet": wallet,
        "transaction_id": transaction_id,
        "eligible_vip_level": eligible_level
    }

class WithdrawRequest(BaseModel):
    amount: float

@api_router.post("/wallet/withdraw")
async def withdraw(
    request: WithdrawRequest,
    current_user: User = Depends(get_current_user)
):
    """Withdraw coins from wallet (mock - for MVP)"""
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    
    wallet = await db.wallets.find_one(
        {"user_id": current_user.user_id},
        {"_id": 0}
    )
    
    if wallet["withdrawable_balance"] < request.amount:
        raise HTTPException(status_code=400, detail="Insufficient withdrawable balance")
    
    # Update wallet
    wallet = await db.wallets.find_one_and_update(
        {"user_id": current_user.user_id},
        {
            "$inc": {
                "withdrawable_balance": -request.amount,
                "total_withdrawn": request.amount
            },
            "$set": {"updated_at": datetime.now(timezone.utc)}
        },
        return_document=True,
        projection={"_id": 0}
    )
    
    # Create transaction
    transaction_id = f"txn_{uuid.uuid4().hex[:12]}"
    await db.wallet_transactions.insert_one({
        "transaction_id": transaction_id,
        "user_id": current_user.user_id,
        "transaction_type": TransactionType.WITHDRAWAL,
        "amount": -request.amount,
        "currency_type": "coins",
        "status": TransactionStatus.PENDING,
        "description": f"Withdrawal of {request.amount} coins",
        "created_at": datetime.now(timezone.utc)
    })
    
    # Add notification
    await db.notifications.insert_one({
        "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
        "user_id": current_user.user_id,
        "title": "Withdrawal Requested 📤",
        "message": f"Your withdrawal of {request.amount} coins is being processed.",
        "notification_type": "wallet",
        "is_read": False,
        "action_url": "/wallet",
        "created_at": datetime.now(timezone.utc)
    })
    
    return {
        "success": True,
        "wallet": wallet,
        "transaction_id": transaction_id
    }

class TransferRequest(BaseModel):
    amount: float
    from_balance: str  # "coins", "bonus", "stars"
    to_balance: str

@api_router.post("/wallet/transfer")
async def transfer_balance(
    request: TransferRequest,
    current_user: User = Depends(get_current_user)
):
    """Transfer between wallet balances"""
    valid_balances = ["coins_balance", "bonus_balance", "stars_balance", "withdrawable_balance"]
    from_field = f"{request.from_balance}_balance"
    to_field = f"{request.to_balance}_balance"
    
    if from_field not in valid_balances or to_field not in valid_balances:
        raise HTTPException(status_code=400, detail="Invalid balance type")
    
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    
    wallet = await db.wallets.find_one(
        {"user_id": current_user.user_id},
        {"_id": 0}
    )
    
    if wallet[from_field] < request.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    # Update wallet
    wallet = await db.wallets.find_one_and_update(
        {"user_id": current_user.user_id},
        {
            "$inc": {
                from_field: -request.amount,
                to_field: request.amount
            },
            "$set": {"updated_at": datetime.now(timezone.utc)}
        },
        return_document=True,
        projection={"_id": 0}
    )
    
    return {"success": True, "wallet": wallet}

# ==================== VIP ENDPOINTS ====================

@api_router.get("/vip/levels")
async def get_vip_levels():
    """Get all VIP levels and their benefits"""
    return {"levels": VIP_LEVELS_DATA}

@api_router.get("/vip/status")
async def get_vip_status(current_user: User = Depends(get_current_user)):
    """Get user's VIP status"""
    vip_status = await db.vip_status.find_one(
        {"user_id": current_user.user_id},
        {"_id": 0}
    )
    
    if not vip_status:
        raise HTTPException(status_code=404, detail="VIP status not found")
    
    # Get current level details
    current_level_data = next(
        (l for l in VIP_LEVELS_DATA if l["level"] == vip_status["vip_level"]),
        VIP_LEVELS_DATA[0]
    )
    
    # Find eligible level based on recharge
    eligible_level = 0
    for level_data in VIP_LEVELS_DATA:
        if vip_status["total_recharged"] >= level_data["recharge_requirement"]:
            eligible_level = level_data["level"]
    
    # Calculate days remaining
    days_remaining = None
    if vip_status["subscription_end"]:
        sub_end = vip_status["subscription_end"]
        if sub_end.tzinfo is None:
            sub_end = sub_end.replace(tzinfo=timezone.utc)
        remaining = sub_end - datetime.now(timezone.utc)
        days_remaining = max(0, remaining.days)
    
    return {
        **vip_status,
        "current_level_data": current_level_data,
        "eligible_level": eligible_level,
        "days_remaining": days_remaining
    }

class SubscribeVIPRequest(BaseModel):
    level: int

@api_router.post("/vip/subscribe")
async def subscribe_vip(
    request: SubscribeVIPRequest,
    current_user: User = Depends(get_current_user)
):
    """Subscribe to a VIP level"""
    # Get level details
    level_data = next(
        (l for l in VIP_LEVELS_DATA if l["level"] == request.level),
        None
    )
    
    if not level_data:
        raise HTTPException(status_code=400, detail="Invalid VIP level")
    
    # Get current VIP status
    vip_status = await db.vip_status.find_one(
        {"user_id": current_user.user_id},
        {"_id": 0}
    )
    
    # Check recharge requirement
    if vip_status["total_recharged"] < level_data["recharge_requirement"]:
        raise HTTPException(
            status_code=400,
            detail=f"Need to recharge {level_data['recharge_requirement']} to unlock this level"
        )
    
    # Check wallet balance
    wallet = await db.wallets.find_one(
        {"user_id": current_user.user_id},
        {"_id": 0}
    )
    
    if wallet["coins_balance"] < level_data["monthly_fee"]:
        raise HTTPException(status_code=400, detail="Insufficient coins balance")
    
    # Deduct fee from wallet
    await db.wallets.update_one(
        {"user_id": current_user.user_id},
        {
            "$inc": {"coins_balance": -level_data["monthly_fee"]},
            "$set": {"updated_at": datetime.now(timezone.utc)}
        }
    )
    
    # Update VIP status
    now = datetime.now(timezone.utc)
    subscription_end = now + timedelta(days=30)
    
    await db.vip_status.update_one(
        {"user_id": current_user.user_id},
        {
            "$set": {
                "vip_level": request.level,
                "subscription_start": now,
                "subscription_end": subscription_end,
                "is_active": True,
                "updated_at": now
            }
        }
    )
    
    # Create transaction
    transaction_id = f"txn_{uuid.uuid4().hex[:12]}"
    await db.wallet_transactions.insert_one({
        "transaction_id": transaction_id,
        "user_id": current_user.user_id,
        "transaction_type": TransactionType.VIP_SUBSCRIPTION,
        "amount": -level_data["monthly_fee"],
        "currency_type": "coins",
        "status": TransactionStatus.COMPLETED,
        "description": f"VIP {level_data['name']} subscription",
        "created_at": now
    })
    
    # Add notification
    await db.notifications.insert_one({
        "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
        "user_id": current_user.user_id,
        "title": f"VIP {level_data['name']} Activated! 👑",
        "message": f"Enjoy your exclusive benefits for the next 30 days!",
        "notification_type": "vip",
        "is_read": False,
        "action_url": "/vip",
        "created_at": now
    })
    
    # Get updated status
    updated_status = await db.vip_status.find_one(
        {"user_id": current_user.user_id},
        {"_id": 0}
    )
    
    return {
        "success": True,
        "vip_status": updated_status,
        "level_data": level_data,
        "transaction_id": transaction_id
    }

@api_router.post("/vip/toggle-auto-renew")
async def toggle_auto_renew(current_user: User = Depends(get_current_user)):
    """Toggle auto-renewal for VIP subscription"""
    vip_status = await db.vip_status.find_one(
        {"user_id": current_user.user_id},
        {"_id": 0}
    )
    
    new_value = not vip_status["auto_renew"]
    
    await db.vip_status.update_one(
        {"user_id": current_user.user_id},
        {
            "$set": {
                "auto_renew": new_value,
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )
    
    return {"success": True, "auto_renew": new_value}

@api_router.post("/vip/cancel")
async def cancel_vip(current_user: User = Depends(get_current_user)):
    """Cancel VIP subscription (will remain active until expiry)"""
    await db.vip_status.update_one(
        {"user_id": current_user.user_id},
        {
            "$set": {
                "auto_renew": False,
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )
    
    # Add notification
    await db.notifications.insert_one({
        "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
        "user_id": current_user.user_id,
        "title": "VIP Subscription Cancelled",
        "message": "Your VIP benefits will remain active until the subscription period ends.",
        "notification_type": "vip",
        "is_read": False,
        "action_url": "/vip",
        "created_at": datetime.now(timezone.utc)
    })
    
    return {"success": True, "message": "VIP subscription cancelled. Benefits remain active until expiry."}

# ==================== NOTIFICATION ENDPOINTS ====================

@api_router.get("/notifications")
async def get_notifications(
    limit: int = 20,
    unread_only: bool = False,
    current_user: User = Depends(get_current_user)
):
    """Get user notifications"""
    query = {"user_id": current_user.user_id}
    if unread_only:
        query["is_read"] = False
    
    notifications = await db.notifications.find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    unread_count = await db.notifications.count_documents({
        "user_id": current_user.user_id,
        "is_read": False
    })
    
    return {
        "notifications": notifications,
        "unread_count": unread_count
    }

@api_router.post("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user)
):
    """Mark notification as read"""
    await db.notifications.update_one(
        {
            "notification_id": notification_id,
            "user_id": current_user.user_id
        },
        {"$set": {"is_read": True}}
    )
    
    return {"success": True}

@api_router.post("/notifications/read-all")
async def mark_all_notifications_read(current_user: User = Depends(get_current_user)):
    """Mark all notifications as read"""
    await db.notifications.update_many(
        {"user_id": current_user.user_id},
        {"$set": {"is_read": True}}
    )
    
    return {"success": True}

# ==================== ACTIVITY REWARD SYSTEM ====================

# Reward Configuration
ACTIVITY_REWARD_CONFIG = {
    "minutes_required": 15,
    "coins_reward": 200,
    "max_daily_rewards": 6,  # Maximum rewards per day (6 x 15 mins = 90 mins max)
    "daily_bonus_coins": 50,  # Bonus for first activity of the day
}

class ActivitySession(BaseModel):
    session_id: str
    user_id: str
    started_at: datetime
    last_active_at: datetime
    total_active_minutes: int = 0
    rewards_claimed: int = 0
    date: str  # YYYY-MM-DD format for daily tracking

@api_router.get("/rewards/activity-status")
async def get_activity_status(current_user: User = Depends(get_current_user)):
    """Get user's current activity status and progress towards reward"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Get or create today's activity session
    activity = await db.activity_sessions.find_one(
        {"user_id": current_user.user_id, "date": today},
        {"_id": 0}
    )
    
    if not activity:
        activity = {
            "session_id": f"activity_{uuid.uuid4().hex[:12]}",
            "user_id": current_user.user_id,
            "started_at": datetime.now(timezone.utc),
            "last_active_at": datetime.now(timezone.utc),
            "total_active_minutes": 0,
            "rewards_claimed": 0,
            "date": today
        }
        await db.activity_sessions.insert_one(activity)
    
    # Calculate progress
    minutes_towards_next = activity["total_active_minutes"] % ACTIVITY_REWARD_CONFIG["minutes_required"]
    rewards_available = min(
        (activity["total_active_minutes"] // ACTIVITY_REWARD_CONFIG["minutes_required"]) - activity["rewards_claimed"],
        ACTIVITY_REWARD_CONFIG["max_daily_rewards"] - activity["rewards_claimed"]
    )
    
    return {
        "today": today,
        "total_active_minutes": activity["total_active_minutes"],
        "minutes_towards_next": minutes_towards_next,
        "minutes_required": ACTIVITY_REWARD_CONFIG["minutes_required"],
        "progress_percent": (minutes_towards_next / ACTIVITY_REWARD_CONFIG["minutes_required"]) * 100,
        "rewards_claimed_today": activity["rewards_claimed"],
        "rewards_available": max(0, rewards_available),
        "max_daily_rewards": ACTIVITY_REWARD_CONFIG["max_daily_rewards"],
        "coins_per_reward": ACTIVITY_REWARD_CONFIG["coins_reward"]
    }

@api_router.post("/rewards/track-activity")
async def track_activity(
    current_user: User = Depends(get_current_user)
):
    """Track user activity - call every minute from frontend"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    now = datetime.now(timezone.utc)
    
    # Get or create today's activity session
    activity = await db.activity_sessions.find_one(
        {"user_id": current_user.user_id, "date": today},
        {"_id": 0}
    )
    
    if not activity:
        activity = {
            "session_id": f"activity_{uuid.uuid4().hex[:12]}",
            "user_id": current_user.user_id,
            "started_at": now,
            "last_active_at": now,
            "total_active_minutes": 1,
            "rewards_claimed": 0,
            "date": today
        }
        await db.activity_sessions.insert_one(activity)
    else:
        # Update activity
        await db.activity_sessions.update_one(
            {"user_id": current_user.user_id, "date": today},
            {
                "$set": {"last_active_at": now},
                "$inc": {"total_active_minutes": 1}
            }
        )
        activity["total_active_minutes"] += 1
    
    # Check if reward is available
    rewards_earned = activity["total_active_minutes"] // ACTIVITY_REWARD_CONFIG["minutes_required"]
    rewards_available = min(
        rewards_earned - activity["rewards_claimed"],
        ACTIVITY_REWARD_CONFIG["max_daily_rewards"] - activity["rewards_claimed"]
    )
    
    return {
        "success": True,
        "total_active_minutes": activity["total_active_minutes"],
        "rewards_available": max(0, rewards_available),
        "can_claim": rewards_available > 0
    }

@api_router.post("/rewards/claim-activity-reward")
async def claim_activity_reward(current_user: User = Depends(get_current_user)):
    """Claim activity reward after 15 minutes of activity"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    activity = await db.activity_sessions.find_one(
        {"user_id": current_user.user_id, "date": today},
        {"_id": 0}
    )
    
    if not activity:
        raise HTTPException(status_code=400, detail="No activity recorded today")
    
    # Check if reward is available
    rewards_earned = activity["total_active_minutes"] // ACTIVITY_REWARD_CONFIG["minutes_required"]
    rewards_available = min(
        rewards_earned - activity["rewards_claimed"],
        ACTIVITY_REWARD_CONFIG["max_daily_rewards"] - activity["rewards_claimed"]
    )
    
    if rewards_available <= 0:
        raise HTTPException(status_code=400, detail="No rewards available to claim")
    
    # Check if reached daily limit
    if activity["rewards_claimed"] >= ACTIVITY_REWARD_CONFIG["max_daily_rewards"]:
        raise HTTPException(status_code=400, detail="Daily reward limit reached")
    
    # Calculate reward amount
    reward_amount = ACTIVITY_REWARD_CONFIG["coins_reward"]
    is_first_reward = activity["rewards_claimed"] == 0
    
    # Add daily bonus for first reward
    if is_first_reward:
        reward_amount += ACTIVITY_REWARD_CONFIG["daily_bonus_coins"]
    
    # Update activity rewards claimed
    await db.activity_sessions.update_one(
        {"user_id": current_user.user_id, "date": today},
        {"$inc": {"rewards_claimed": 1}}
    )
    
    # Add reward to wallet
    wallet = await db.wallets.find_one_and_update(
        {"user_id": current_user.user_id},
        {
            "$inc": {"coins_balance": reward_amount},
            "$set": {"updated_at": datetime.now(timezone.utc)}
        },
        return_document=True,
        projection={"_id": 0}
    )
    
    # Create transaction
    transaction_id = f"txn_{uuid.uuid4().hex[:12]}"
    description = f"Activity reward ({activity['rewards_claimed'] + 1}/{ACTIVITY_REWARD_CONFIG['max_daily_rewards']})"
    if is_first_reward:
        description += " + Daily bonus"
    
    await db.wallet_transactions.insert_one({
        "transaction_id": transaction_id,
        "user_id": current_user.user_id,
        "transaction_type": TransactionType.ACTIVITY_REWARD,
        "amount": reward_amount,
        "currency_type": "coins",
        "status": TransactionStatus.COMPLETED,
        "description": description,
        "created_at": datetime.now(timezone.utc)
    })
    
    # Add notification
    await db.notifications.insert_one({
        "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
        "user_id": current_user.user_id,
        "title": "Activity Reward Claimed! 🎉",
        "message": f"You earned {reward_amount} coins for being active!",
        "notification_type": "reward",
        "is_read": False,
        "action_url": "/rewards",
        "created_at": datetime.now(timezone.utc)
    })
    
    return {
        "success": True,
        "reward_amount": reward_amount,
        "is_first_reward": is_first_reward,
        "daily_bonus_included": is_first_reward,
        "rewards_claimed_today": activity["rewards_claimed"] + 1,
        "wallet_balance": wallet["coins_balance"],
        "transaction_id": transaction_id
    }

@api_router.get("/rewards/daily-summary")
async def get_daily_summary(current_user: User = Depends(get_current_user)):
    """Get summary of daily rewards and activity"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Get activity for last 7 days
    seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")
    
    activities = await db.activity_sessions.find(
        {
            "user_id": current_user.user_id,
            "date": {"$gte": seven_days_ago}
        },
        {"_id": 0}
    ).to_list(7)
    
    # Get today's transactions
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_rewards = await db.wallet_transactions.find(
        {
            "user_id": current_user.user_id,
            "transaction_type": TransactionType.ACTIVITY_REWARD,
            "created_at": {"$gte": today_start}
        },
        {"_id": 0}
    ).to_list(20)
    
    total_earned_today = sum(t["amount"] for t in today_rewards)
    
    # Calculate streak
    streak = 0
    sorted_activities = sorted(activities, key=lambda x: x["date"], reverse=True)
    for activity in sorted_activities:
        if activity["rewards_claimed"] > 0:
            streak += 1
        else:
            break
    
    return {
        "today": today,
        "total_earned_today": total_earned_today,
        "rewards_today": len(today_rewards),
        "activity_streak": streak,
        "weekly_activities": activities,
        "config": ACTIVITY_REWARD_CONFIG
    }

# ==================== AGENCY/COMMISSION SYSTEM ====================

# Agency Level Configuration
AGENCY_LEVELS = {
    0: {"name": "Member", "commission_rate": 0, "monthly_threshold": 0},
    1: {"name": "Sub-Agent Level 1", "commission_rate": 12, "monthly_threshold": 500},
    2: {"name": "Sub-Agent Level 2", "commission_rate": 16, "monthly_threshold": 1500},
    3: {"name": "Agency Level 20", "commission_rate": 20, "monthly_threshold": 3000},
}

STARS_TO_COINS_FEE = 8  # 8% service fee

class AgencyStatus(BaseModel):
    user_id: str
    agency_level: int = 0
    referral_code: str
    total_referrals: int = 0
    active_referrals: int = 0
    total_commission_earned: float = 0
    monthly_volume: float = 0
    monthly_volume_reset_date: str
    created_at: datetime
    updated_at: datetime

class Referral(BaseModel):
    referral_id: str
    referrer_id: str
    referred_id: str
    status: str = "pending"  # pending, active, inactive
    total_transactions: float = 0
    commission_earned: float = 0
    created_at: datetime

@api_router.get("/agency/status")
async def get_agency_status(current_user: User = Depends(get_current_user)):
    """Get user's agency status and commission info"""
    agency = await db.agency_status.find_one(
        {"user_id": current_user.user_id},
        {"_id": 0}
    )
    
    if not agency:
        # Create agency status for user
        referral_code = f"MN{uuid.uuid4().hex[:8].upper()}"
        agency = {
            "user_id": current_user.user_id,
            "agency_level": 0,
            "referral_code": referral_code,
            "total_referrals": 0,
            "active_referrals": 0,
            "total_commission_earned": 0,
            "monthly_volume": 0,
            "monthly_volume_reset_date": datetime.now(timezone.utc).strftime("%Y-%m-01"),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        await db.agency_status.insert_one(agency)
    
    # Get current level info
    level_info = AGENCY_LEVELS.get(agency["agency_level"], AGENCY_LEVELS[0])
    
    # Calculate next level requirements
    next_level = agency["agency_level"] + 1
    next_level_info = AGENCY_LEVELS.get(next_level, None)
    
    # Get referrals
    referrals = await db.referrals.find(
        {"referrer_id": current_user.user_id},
        {"_id": 0}
    ).to_list(100)
    
    return {
        **agency,
        "level_info": level_info,
        "next_level_info": next_level_info,
        "referrals": referrals,
        "all_levels": AGENCY_LEVELS
    }

class ApplyReferralRequest(BaseModel):
    referral_code: str

@api_router.post("/agency/apply-referral")
async def apply_referral_code(
    request: ApplyReferralRequest,
    current_user: User = Depends(get_current_user)
):
    """Apply a referral code during signup"""
    # Check if user already has a referrer
    existing_referral = await db.referrals.find_one(
        {"referred_id": current_user.user_id},
        {"_id": 0}
    )
    
    if existing_referral:
        raise HTTPException(status_code=400, detail="You already have a referrer")
    
    # Find referrer by code
    referrer_agency = await db.agency_status.find_one(
        {"referral_code": request.referral_code.upper()},
        {"_id": 0}
    )
    
    if not referrer_agency:
        raise HTTPException(status_code=404, detail="Invalid referral code")
    
    if referrer_agency["user_id"] == current_user.user_id:
        raise HTTPException(status_code=400, detail="Cannot use your own referral code")
    
    # Create referral
    referral = {
        "referral_id": f"ref_{uuid.uuid4().hex[:12]}",
        "referrer_id": referrer_agency["user_id"],
        "referred_id": current_user.user_id,
        "status": "active",
        "total_transactions": 0,
        "commission_earned": 0,
        "created_at": datetime.now(timezone.utc)
    }
    await db.referrals.insert_one(referral)
    
    # Update referrer stats
    await db.agency_status.update_one(
        {"user_id": referrer_agency["user_id"]},
        {
            "$inc": {"total_referrals": 1, "active_referrals": 1},
            "$set": {"updated_at": datetime.now(timezone.utc)}
        }
    )
    
    # Add notification to referrer
    await db.notifications.insert_one({
        "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
        "user_id": referrer_agency["user_id"],
        "title": "New Referral! 🎉",
        "message": f"A new user joined using your referral code!",
        "notification_type": "agency",
        "is_read": False,
        "action_url": "/agency",
        "created_at": datetime.now(timezone.utc)
    })
    
    return {"success": True, "message": "Referral code applied successfully"}

class ConvertStarsRequest(BaseModel):
    stars_amount: float

@api_router.post("/agency/convert-stars")
async def convert_stars_to_coins(
    request: ConvertStarsRequest,
    current_user: User = Depends(get_current_user)
):
    """Convert stars to coins (8% service fee)"""
    if request.stars_amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    
    wallet = await db.wallets.find_one(
        {"user_id": current_user.user_id},
        {"_id": 0}
    )
    
    if wallet["stars_balance"] < request.stars_amount:
        raise HTTPException(status_code=400, detail="Insufficient stars balance")
    
    # Calculate conversion with 8% fee
    fee_amount = request.stars_amount * (STARS_TO_COINS_FEE / 100)
    coins_received = request.stars_amount - fee_amount
    
    # Update wallet
    await db.wallets.update_one(
        {"user_id": current_user.user_id},
        {
            "$inc": {
                "stars_balance": -request.stars_amount,
                "coins_balance": coins_received
            },
            "$set": {"updated_at": datetime.now(timezone.utc)}
        }
    )
    
    # Create transaction
    transaction_id = f"txn_{uuid.uuid4().hex[:12]}"
    await db.wallet_transactions.insert_one({
        "transaction_id": transaction_id,
        "user_id": current_user.user_id,
        "transaction_type": "stars_conversion",
        "amount": coins_received,
        "currency_type": "coins",
        "status": TransactionStatus.COMPLETED,
        "description": f"Converted {request.stars_amount} stars to {coins_received} coins (8% fee: {fee_amount})",
        "created_at": datetime.now(timezone.utc)
    })
    
    return {
        "success": True,
        "stars_converted": request.stars_amount,
        "fee_amount": fee_amount,
        "fee_percent": STARS_TO_COINS_FEE,
        "coins_received": coins_received,
        "transaction_id": transaction_id
    }

@api_router.get("/agency/commissions")
async def get_commission_history(
    limit: int = 20,
    current_user: User = Depends(get_current_user)
):
    """Get commission history"""
    commissions = await db.commissions.find(
        {"user_id": current_user.user_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    total = await db.commissions.count_documents({"user_id": current_user.user_id})
    
    return {
        "commissions": commissions,
        "total": total
    }

# ==================== WITHDRAWAL SYSTEM ====================

WITHDRAWAL_CONFIG = {
    "min_stars_required": 100000,
    "processing_time_days": 3,
    "vip_processing_time_days": 1,
}

class WithdrawalStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

class BankDetails(BaseModel):
    account_holder_name: str
    account_number: str
    ifsc_code: str
    bank_name: str

class UPIDetails(BaseModel):
    upi_id: str

class WithdrawalRequest(BaseModel):
    amount: float
    withdrawal_method: str  # "bank" or "upi"
    bank_details: Optional[BankDetails] = None
    upi_details: Optional[UPIDetails] = None

@api_router.get("/withdrawal/config")
async def get_withdrawal_config(current_user: User = Depends(get_current_user)):
    """Get withdrawal configuration and user eligibility"""
    wallet = await db.wallets.find_one(
        {"user_id": current_user.user_id},
        {"_id": 0}
    )
    
    vip_status = await db.vip_status.find_one(
        {"user_id": current_user.user_id},
        {"_id": 0}
    )
    
    is_vip = vip_status and vip_status.get("is_active", False)
    is_eligible = wallet["stars_balance"] >= WITHDRAWAL_CONFIG["min_stars_required"]
    
    # Get saved payment methods
    saved_methods = await db.payment_methods.find(
        {"user_id": current_user.user_id},
        {"_id": 0}
    ).to_list(10)
    
    return {
        "config": WITHDRAWAL_CONFIG,
        "current_stars": wallet["stars_balance"],
        "is_eligible": is_eligible,
        "is_vip": is_vip,
        "processing_time_days": WITHDRAWAL_CONFIG["vip_processing_time_days"] if is_vip else WITHDRAWAL_CONFIG["processing_time_days"],
        "saved_payment_methods": saved_methods,
        "stars_needed": max(0, WITHDRAWAL_CONFIG["min_stars_required"] - wallet["stars_balance"])
    }

class SavePaymentMethodRequest(BaseModel):
    method_type: str  # "bank" or "upi"
    bank_details: Optional[BankDetails] = None
    upi_details: Optional[UPIDetails] = None
    is_default: bool = False

@api_router.post("/withdrawal/save-payment-method")
async def save_payment_method(
    request: SavePaymentMethodRequest,
    current_user: User = Depends(get_current_user)
):
    """Save a payment method for withdrawals"""
    method_id = f"pm_{uuid.uuid4().hex[:12]}"
    
    method_data = {
        "method_id": method_id,
        "user_id": current_user.user_id,
        "method_type": request.method_type,
        "is_default": request.is_default,
        "is_verified": False,
        "created_at": datetime.now(timezone.utc)
    }
    
    if request.method_type == "bank" and request.bank_details:
        method_data["bank_details"] = request.bank_details.dict()
    elif request.method_type == "upi" and request.upi_details:
        method_data["upi_details"] = request.upi_details.dict()
    else:
        raise HTTPException(status_code=400, detail="Invalid payment method details")
    
    # If setting as default, unset other defaults
    if request.is_default:
        await db.payment_methods.update_many(
            {"user_id": current_user.user_id},
            {"$set": {"is_default": False}}
        )
    
    await db.payment_methods.insert_one(method_data)
    
    return {"success": True, "method_id": method_id}

class CreateWithdrawalRequest(BaseModel):
    amount: float
    payment_method_id: str

@api_router.post("/withdrawal/request")
async def create_withdrawal_request(
    request: CreateWithdrawalRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a withdrawal request"""
    wallet = await db.wallets.find_one(
        {"user_id": current_user.user_id},
        {"_id": 0}
    )
    
    # Check minimum stars requirement
    if wallet["stars_balance"] < WITHDRAWAL_CONFIG["min_stars_required"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Minimum {WITHDRAWAL_CONFIG['min_stars_required']} stars required for withdrawal"
        )
    
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    
    if request.amount > wallet["stars_balance"]:
        raise HTTPException(status_code=400, detail="Insufficient stars balance")
    
    # Get payment method
    payment_method = await db.payment_methods.find_one(
        {"method_id": request.payment_method_id, "user_id": current_user.user_id},
        {"_id": 0}
    )
    
    if not payment_method:
        raise HTTPException(status_code=404, detail="Payment method not found")
    
    # Check VIP status for priority
    vip_status = await db.vip_status.find_one(
        {"user_id": current_user.user_id},
        {"_id": 0}
    )
    is_vip = vip_status and vip_status.get("is_active", False)
    
    # Create withdrawal request
    withdrawal_id = f"wd_{uuid.uuid4().hex[:12]}"
    processing_days = WITHDRAWAL_CONFIG["vip_processing_time_days"] if is_vip else WITHDRAWAL_CONFIG["processing_time_days"]
    
    withdrawal = {
        "withdrawal_id": withdrawal_id,
        "user_id": current_user.user_id,
        "amount": request.amount,
        "status": WithdrawalStatus.PENDING,
        "payment_method_id": request.payment_method_id,
        "payment_method_type": payment_method["method_type"],
        "payment_details": payment_method.get("bank_details") or payment_method.get("upi_details"),
        "is_vip": is_vip,
        "estimated_completion": datetime.now(timezone.utc) + timedelta(days=processing_days),
        "face_verified": False,  # Will be updated after face verification
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    
    await db.withdrawals.insert_one(withdrawal)
    
    # Deduct stars from wallet
    await db.wallets.update_one(
        {"user_id": current_user.user_id},
        {
            "$inc": {"stars_balance": -request.amount},
            "$set": {"updated_at": datetime.now(timezone.utc)}
        }
    )
    
    # Create transaction
    await db.wallet_transactions.insert_one({
        "transaction_id": f"txn_{uuid.uuid4().hex[:12]}",
        "user_id": current_user.user_id,
        "transaction_type": TransactionType.WITHDRAWAL,
        "amount": -request.amount,
        "currency_type": "stars",
        "status": TransactionStatus.PENDING,
        "reference_id": withdrawal_id,
        "description": f"Withdrawal request of {request.amount} stars",
        "created_at": datetime.now(timezone.utc)
    })
    
    # Add notification
    await db.notifications.insert_one({
        "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
        "user_id": current_user.user_id,
        "title": "Withdrawal Request Submitted 📤",
        "message": f"Your withdrawal of {request.amount} stars is being processed. Face verification required.",
        "notification_type": "withdrawal",
        "is_read": False,
        "action_url": "/withdrawal",
        "created_at": datetime.now(timezone.utc)
    })
    
    return {
        "success": True,
        "withdrawal_id": withdrawal_id,
        "amount": request.amount,
        "status": WithdrawalStatus.PENDING,
        "estimated_completion": withdrawal["estimated_completion"].isoformat(),
        "requires_face_verification": True
    }

@api_router.get("/withdrawal/history")
async def get_withdrawal_history(
    limit: int = 20,
    current_user: User = Depends(get_current_user)
):
    """Get withdrawal history"""
    withdrawals = await db.withdrawals.find(
        {"user_id": current_user.user_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    return {"withdrawals": withdrawals}

@api_router.post("/withdrawal/{withdrawal_id}/verify-face")
async def verify_face_for_withdrawal(
    withdrawal_id: str,
    current_user: User = Depends(get_current_user)
):
    """Mark face verification as complete for withdrawal (mock)"""
    withdrawal = await db.withdrawals.find_one(
        {"withdrawal_id": withdrawal_id, "user_id": current_user.user_id},
        {"_id": 0}
    )
    
    if not withdrawal:
        raise HTTPException(status_code=404, detail="Withdrawal not found")
    
    if withdrawal["status"] != WithdrawalStatus.PENDING:
        raise HTTPException(status_code=400, detail="Withdrawal cannot be verified")
    
    # Update withdrawal status
    await db.withdrawals.update_one(
        {"withdrawal_id": withdrawal_id},
        {
            "$set": {
                "face_verified": True,
                "status": WithdrawalStatus.PROCESSING,
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )
    
    # Add notification
    await db.notifications.insert_one({
        "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
        "user_id": current_user.user_id,
        "title": "Face Verification Complete ✅",
        "message": "Your withdrawal is now being processed.",
        "notification_type": "withdrawal",
        "is_read": False,
        "action_url": "/withdrawal",
        "created_at": datetime.now(timezone.utc)
    })
    
    return {"success": True, "message": "Face verification completed, withdrawal is now processing"}

# ==================== CHARITY SYSTEM ====================

CHARITY_CONFIG = {
    "vip_gift_charity_percent": 2,  # 2% of VIP gift income goes to charity
}

@api_router.get("/charity/stats")
async def get_charity_stats(current_user: User = Depends(get_current_user)):
    """Get charity statistics"""
    # Get global charity wallet
    charity_wallet = await db.charity_wallet.find_one({}, {"_id": 0})
    
    if not charity_wallet:
        charity_wallet = {
            "total_balance": 0,
            "total_received": 0,
            "total_distributed": 0,
            "lives_helped": 0,
            "updated_at": datetime.now(timezone.utc)
        }
        await db.charity_wallet.insert_one(charity_wallet)
    
    # Get user's charity contributions
    user_contributions = await db.charity_contributions.find(
        {"user_id": current_user.user_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(10).to_list(10)
    
    total_user_contribution = sum(c["amount"] for c in user_contributions)
    
    # Get recent distributions
    distributions = await db.charity_distributions.find(
        {},
        {"_id": 0}
    ).sort("created_at", -1).limit(5).to_list(5)
    
    return {
        "global_stats": charity_wallet,
        "user_contributions": user_contributions,
        "total_user_contribution": total_user_contribution,
        "recent_distributions": distributions,
        "config": CHARITY_CONFIG
    }

@api_router.get("/charity/leaderboard")
async def get_charity_leaderboard():
    """Get charity contribution leaderboard"""
    # Aggregate top contributors
    pipeline = [
        {"$group": {
            "_id": "$user_id",
            "total_donated": {"$sum": "$amount"}
        }},
        {"$sort": {"total_donated": -1}},
        {"$limit": 20}
    ]
    
    top_contributors = await db.charity_contributions.aggregate(pipeline).to_list(20)
    
    # Get user details for each contributor
    leaderboard = []
    for i, contributor in enumerate(top_contributors):
        user = await db.users.find_one(
            {"user_id": contributor["_id"]},
            {"_id": 0, "user_id": 1, "name": 1, "picture": 1}
        )
        if user:
            leaderboard.append({
                "rank": i + 1,
                "user": user,
                "total_donated": contributor["total_donated"]
            })
    
    return {"leaderboard": leaderboard}

# ==================== GIFT SYSTEM ====================

# Signature Gift Categories with Unique Designs
SIGNATURE_GIFTS = {
    "basic": [
        {"gift_id": "rose", "name": "Red Rose", "emoji": "rose", "price": 10, "category": "basic", "animation": "float"},
        {"gift_id": "heart", "name": "Love Heart", "emoji": "heart", "price": 20, "category": "basic", "animation": "pulse"},
        {"gift_id": "star", "name": "Shining Star", "emoji": "star", "price": 30, "category": "basic", "animation": "sparkle"},
        {"gift_id": "coffee", "name": "Hot Coffee", "emoji": "coffee", "price": 15, "category": "basic", "animation": "steam"},
        {"gift_id": "kiss", "name": "Flying Kiss", "emoji": "kiss", "price": 25, "category": "basic", "animation": "fly"},
    ],
    "premium": [
        {"gift_id": "diamond_ring", "name": "Diamond Ring", "emoji": "ring", "price": 500, "category": "premium", "animation": "shine"},
        {"gift_id": "gold_crown", "name": "Royal Crown", "emoji": "crown", "price": 1000, "category": "premium", "animation": "glow"},
        {"gift_id": "sports_car", "name": "Sports Car", "emoji": "car", "price": 2000, "category": "premium", "animation": "drive"},
        {"gift_id": "private_jet", "name": "Private Jet", "emoji": "airplane", "price": 5000, "category": "premium", "animation": "takeoff"},
        {"gift_id": "yacht", "name": "Luxury Yacht", "emoji": "boat", "price": 8000, "category": "premium", "animation": "wave"},
    ],
    "signature": [
        {"gift_id": "mugaddas_star", "name": "Mugaddas Star", "emoji": "sparkles", "price": 10000, "category": "signature", "animation": "supernova", "exclusive": True},
        {"gift_id": "golden_palace", "name": "Golden Palace", "emoji": "castle", "price": 25000, "category": "signature", "animation": "build", "exclusive": True},
        {"gift_id": "universe", "name": "Gift of Universe", "emoji": "galaxy", "price": 50000, "category": "signature", "animation": "cosmic", "exclusive": True},
        {"gift_id": "eternal_love", "name": "Eternal Love", "emoji": "infinity", "price": 100000, "category": "signature", "animation": "eternal", "exclusive": True},
    ],
    "special": [
        {"gift_id": "birthday_cake", "name": "Birthday Cake", "emoji": "cake", "price": 100, "category": "special", "animation": "candles"},
        {"gift_id": "fireworks", "name": "Fireworks", "emoji": "fireworks", "price": 200, "category": "special", "animation": "explode"},
        {"gift_id": "trophy", "name": "Winner Trophy", "emoji": "trophy", "price": 300, "category": "special", "animation": "shine"},
        {"gift_id": "lucky_charm", "name": "Lucky Charm", "emoji": "clover", "price": 88, "category": "special", "animation": "lucky"},
    ]
}

# Messaging Rewards Config
MESSAGING_REWARDS = {
    "chat_reward": 20,  # Coins for chatting with someone
    "female_bonus": 20,  # Additional bonus for female interaction
    "max_daily_chat_rewards": 50,  # Maximum chat rewards per day
}

@api_router.get("/gifts/catalog")
async def get_gift_catalog():
    """Get all available gifts"""
    return {
        "gifts": SIGNATURE_GIFTS,
        "categories": ["basic", "premium", "signature", "special"]
    }

class SendGiftRequest(BaseModel):
    gift_id: str
    receiver_id: str
    quantity: int = 1
    message: Optional[str] = None

@api_router.post("/gifts/send")
async def send_gift(
    request: SendGiftRequest,
    current_user: User = Depends(get_current_user)
):
    """Send a gift to another user"""
    # Find the gift
    gift = None
    for category_gifts in SIGNATURE_GIFTS.values():
        for g in category_gifts:
            if g["gift_id"] == request.gift_id:
                gift = g
                break
        if gift:
            break
    
    if not gift:
        raise HTTPException(status_code=404, detail="Gift not found")
    
    # Check receiver exists
    receiver = await db.users.find_one(
        {"user_id": request.receiver_id},
        {"_id": 0}
    )
    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver not found")
    
    if request.receiver_id == current_user.user_id:
        raise HTTPException(status_code=400, detail="Cannot send gift to yourself")
    
    total_cost = gift["price"] * request.quantity
    
    # Check sender's balance
    wallet = await db.wallets.find_one(
        {"user_id": current_user.user_id},
        {"_id": 0}
    )
    
    if wallet["coins_balance"] < total_cost:
        raise HTTPException(status_code=400, detail="Insufficient coins balance")
    
    # Deduct from sender
    await db.wallets.update_one(
        {"user_id": current_user.user_id},
        {
            "$inc": {"coins_balance": -total_cost},
            "$set": {"updated_at": datetime.now(timezone.utc)}
        }
    )
    
    # Calculate charity contribution (2%)
    charity_amount = total_cost * (CHARITY_CONFIG["vip_gift_charity_percent"] / 100)
    receiver_amount = total_cost - charity_amount
    
    # Add to receiver's stars (gifts convert to stars)
    await db.wallets.update_one(
        {"user_id": request.receiver_id},
        {
            "$inc": {"stars_balance": receiver_amount},
            "$set": {"updated_at": datetime.now(timezone.utc)}
        }
    )
    
    # Add to charity wallet
    await db.charity_wallet.update_one(
        {},
        {
            "$inc": {
                "total_balance": charity_amount,
                "total_received": charity_amount
            },
            "$set": {"updated_at": datetime.now(timezone.utc)}
        },
        upsert=True
    )
    
    # Record charity contribution
    await db.charity_contributions.insert_one({
        "contribution_id": f"char_{uuid.uuid4().hex[:12]}",
        "user_id": current_user.user_id,
        "amount": charity_amount,
        "source": "gift",
        "gift_id": gift["gift_id"],
        "created_at": datetime.now(timezone.utc)
    })
    
    # Create gift record
    gift_record_id = f"gift_{uuid.uuid4().hex[:12]}"
    await db.gift_records.insert_one({
        "gift_record_id": gift_record_id,
        "sender_id": current_user.user_id,
        "receiver_id": request.receiver_id,
        "gift_id": gift["gift_id"],
        "gift_name": gift["name"],
        "gift_price": gift["price"],
        "quantity": request.quantity,
        "total_value": total_cost,
        "message": request.message,
        "charity_amount": charity_amount,
        "created_at": datetime.now(timezone.utc)
    })
    
    # Create transactions
    await db.wallet_transactions.insert_one({
        "transaction_id": f"txn_{uuid.uuid4().hex[:12]}",
        "user_id": current_user.user_id,
        "transaction_type": "gift_sent",
        "amount": -total_cost,
        "currency_type": "coins",
        "status": TransactionStatus.COMPLETED,
        "reference_id": gift_record_id,
        "description": f"Sent {request.quantity}x {gift['name']} to {receiver['name']}",
        "created_at": datetime.now(timezone.utc)
    })
    
    await db.wallet_transactions.insert_one({
        "transaction_id": f"txn_{uuid.uuid4().hex[:12]}",
        "user_id": request.receiver_id,
        "transaction_type": "gift_received",
        "amount": receiver_amount,
        "currency_type": "stars",
        "status": TransactionStatus.COMPLETED,
        "reference_id": gift_record_id,
        "description": f"Received {request.quantity}x {gift['name']} from {current_user.name}",
        "created_at": datetime.now(timezone.utc)
    })
    
    # Send notification to receiver
    await db.notifications.insert_one({
        "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
        "user_id": request.receiver_id,
        "title": f"Gift Received! 🎁",
        "message": f"{current_user.name} sent you {request.quantity}x {gift['name']}!" + (f"\nMessage: {request.message}" if request.message else ""),
        "notification_type": "gift",
        "is_read": False,
        "action_url": "/gifts",
        "created_at": datetime.now(timezone.utc)
    })
    
    return {
        "success": True,
        "gift_record_id": gift_record_id,
        "gift": gift,
        "quantity": request.quantity,
        "total_cost": total_cost,
        "charity_contribution": charity_amount,
        "receiver_earned": receiver_amount
    }

@api_router.get("/gifts/sent")
async def get_sent_gifts(
    limit: int = 20,
    current_user: User = Depends(get_current_user)
):
    """Get gifts sent by current user"""
    gifts = await db.gift_records.find(
        {"sender_id": current_user.user_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    # Get receiver details
    for gift in gifts:
        receiver = await db.users.find_one(
            {"user_id": gift["receiver_id"]},
            {"_id": 0, "name": 1, "picture": 1}
        )
        gift["receiver"] = receiver
    
    return {"gifts": gifts}

@api_router.get("/gifts/received")
async def get_received_gifts(
    limit: int = 20,
    current_user: User = Depends(get_current_user)
):
    """Get gifts received by current user"""
    gifts = await db.gift_records.find(
        {"receiver_id": current_user.user_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    # Get sender details
    for gift in gifts:
        sender = await db.users.find_one(
            {"user_id": gift["sender_id"]},
            {"_id": 0, "name": 1, "picture": 1}
        )
        gift["sender"] = sender
    
    return {"gifts": gifts}

@api_router.get("/gifts/leaderboard")
async def get_gift_leaderboard():
    """Get top gift senders and receivers"""
    # Top senders
    sender_pipeline = [
        {"$group": {
            "_id": "$sender_id",
            "total_sent": {"$sum": "$total_value"},
            "gifts_count": {"$sum": "$quantity"}
        }},
        {"$sort": {"total_sent": -1}},
        {"$limit": 10}
    ]
    
    top_senders = await db.gift_records.aggregate(sender_pipeline).to_list(10)
    
    # Top receivers
    receiver_pipeline = [
        {"$group": {
            "_id": "$receiver_id",
            "total_received": {"$sum": "$total_value"},
            "gifts_count": {"$sum": "$quantity"}
        }},
        {"$sort": {"total_received": -1}},
        {"$limit": 10}
    ]
    
    top_receivers = await db.gift_records.aggregate(receiver_pipeline).to_list(10)
    
    # Get user details
    senders_leaderboard = []
    for i, sender in enumerate(top_senders):
        user = await db.users.find_one(
            {"user_id": sender["_id"]},
            {"_id": 0, "user_id": 1, "name": 1, "picture": 1}
        )
        if user:
            senders_leaderboard.append({
                "rank": i + 1,
                "user": user,
                "total_sent": sender["total_sent"],
                "gifts_count": sender["gifts_count"]
            })
    
    receivers_leaderboard = []
    for i, receiver in enumerate(top_receivers):
        user = await db.users.find_one(
            {"user_id": receiver["_id"]},
            {"_id": 0, "user_id": 1, "name": 1, "picture": 1}
        )
        if user:
            receivers_leaderboard.append({
                "rank": i + 1,
                "user": user,
                "total_received": receiver["total_received"],
                "gifts_count": receiver["gifts_count"]
            })
    
    return {
        "top_senders": senders_leaderboard,
        "top_receivers": receivers_leaderboard
    }

# ==================== MESSAGING REWARDS ====================

@api_router.post("/messages/reward")
async def claim_messaging_reward(
    current_user: User = Depends(get_current_user)
):
    """Claim reward for chatting (20 coins per chat)"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Get today's messaging rewards count
    rewards_today = await db.messaging_rewards.count_documents({
        "user_id": current_user.user_id,
        "date": today
    })
    
    if rewards_today >= MESSAGING_REWARDS["max_daily_chat_rewards"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Daily limit of {MESSAGING_REWARDS['max_daily_chat_rewards']} chat rewards reached"
        )
    
    reward_amount = MESSAGING_REWARDS["chat_reward"]
    
    # Add reward to wallet
    await db.wallets.update_one(
        {"user_id": current_user.user_id},
        {
            "$inc": {"coins_balance": reward_amount},
            "$set": {"updated_at": datetime.now(timezone.utc)}
        }
    )
    
    # Record reward
    await db.messaging_rewards.insert_one({
        "reward_id": f"msg_{uuid.uuid4().hex[:12]}",
        "user_id": current_user.user_id,
        "reward_type": "chat",
        "amount": reward_amount,
        "date": today,
        "created_at": datetime.now(timezone.utc)
    })
    
    # Create transaction
    await db.wallet_transactions.insert_one({
        "transaction_id": f"txn_{uuid.uuid4().hex[:12]}",
        "user_id": current_user.user_id,
        "transaction_type": "messaging_reward",
        "amount": reward_amount,
        "currency_type": "coins",
        "status": TransactionStatus.COMPLETED,
        "description": f"Chat reward ({rewards_today + 1}/{MESSAGING_REWARDS['max_daily_chat_rewards']})",
        "created_at": datetime.now(timezone.utc)
    })
    
    return {
        "success": True,
        "reward_amount": reward_amount,
        "rewards_claimed_today": rewards_today + 1,
        "max_daily_rewards": MESSAGING_REWARDS["max_daily_chat_rewards"]
    }

@api_router.get("/messages/reward-status")
async def get_messaging_reward_status(current_user: User = Depends(get_current_user)):
    """Get messaging reward status for today"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    rewards_today = await db.messaging_rewards.count_documents({
        "user_id": current_user.user_id,
        "date": today
    })
    
    total_earned_today = rewards_today * MESSAGING_REWARDS["chat_reward"]
    
    return {
        "rewards_claimed_today": rewards_today,
        "max_daily_rewards": MESSAGING_REWARDS["max_daily_chat_rewards"],
        "reward_per_chat": MESSAGING_REWARDS["chat_reward"],
        "total_earned_today": total_earned_today,
        "can_claim_more": rewards_today < MESSAGING_REWARDS["max_daily_chat_rewards"]
    }

# ==================== HEALTH CHECK ====================

@api_router.get("/")
async def root():
    return {"message": "VIP Wallet API", "status": "running"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
