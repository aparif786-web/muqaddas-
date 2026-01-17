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
import random

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

# ==================== CROWN SYSTEM MODELS ====================

class CrownType(str, Enum):
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    GIFTER = "gifter"
    QUEEN = "queen"
    VIDEO_CREATOR = "video_creator"

class UserCrown(BaseModel):
    crown_id: str
    user_id: str
    crown_type: CrownType
    earned_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool = True

# ==================== VIDEO LEADERBOARD MODELS ====================

class VideoEntry(BaseModel):
    video_id: str
    user_id: str
    title: str
    description: Optional[str] = None
    likes_count: int = 0
    views_count: int = 0
    shares_count: int = 0
    gifts_received: float = 0.0
    created_at: datetime
    month_year: str  # Format: "2025-01"

class LeaderboardEntry(BaseModel):
    rank: int
    user_id: str
    user_name: str
    user_picture: Optional[str] = None
    score: int
    crown_type: Optional[CrownType] = None
    prize: Optional[str] = None

# ==================== MHA EVENT MODELS ====================

class MHAEvent(BaseModel):
    event_id: str
    event_name: str
    event_type: str  # "monthly", "weekly", "special"
    start_date: datetime
    end_date: datetime
    prize_pool: dict  # {"1st": "iPhone 16", "2nd": "Android Phone", ...}
    is_active: bool = True
    created_at: datetime

class MHAParticipant(BaseModel):
    participant_id: str
    event_id: str
    user_id: str
    total_score: int = 0
    rank: Optional[int] = None
    crown_earned: Optional[CrownType] = None
    prize_won: Optional[str] = None
    joined_at: datetime

# ==================== CHARITY SYSTEM CONSTANTS ====================

# Company revenue milestones
CHARITY_PHASE_1_THRESHOLD = 10_000_000_000  # 10 Billion
CHARITY_PHASE_1_RATE = 0.02  # 2% before 10B
CHARITY_PHASE_2_RATE = 0.45  # 45% after 10B
SECURITY_FUND_RATE = 0.01   # 1% always

# Monthly Video Leaderboard Prizes
MONTHLY_PRIZES = {
    1: {"prize": "iPhone 16 Pro Max", "coins": 100000},
    2: {"prize": "Samsung Galaxy S24 Ultra", "coins": 75000},
    3: {"prize": "MacBook Air M3", "coins": 50000},
    4: {"prize": "iPad Pro", "coins": 30000},
    5: {"prize": "AirPods Pro", "coins": 20000},
    6: {"prize": "10,000 Coins", "coins": 10000},
    7: {"prize": "10,000 Coins", "coins": 10000},
    8: {"prize": "10,000 Coins", "coins": 10000},
    9: {"prize": "10,000 Coins", "coins": 10000},
    10: {"prize": "10,000 Coins", "coins": 10000},
}

# Crown requirements
CROWN_REQUIREMENTS = {
    CrownType.BRONZE: {"min_likes": 100, "min_videos": 5},
    CrownType.SILVER: {"min_likes": 1000, "min_videos": 20},
    CrownType.GOLD: {"min_likes": 10000, "min_videos": 50},
    CrownType.GIFTER: {"min_gifts_sent": 10000},
    CrownType.QUEEN: {"special_achievement": True},
    CrownType.VIDEO_CREATOR: {"min_videos": 100, "min_total_views": 100000},
}

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
        "charity_bonus": 5,
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
        "charity_bonus": 10,
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
        "charity_bonus": 15,
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
        "charity_bonus": 20,
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
        "charity_bonus": 30,
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

"""
DETAILED AGENT COMMISSION STRUCTURE:

1. Commission rates based on Last 30 Days Total Earnings:
   - 0 - 2,000,000: 4% Commission
   - 2,000,001 - 10,000,000: 8% Commission
   - 10,000,001 - 50,000,000: 12% Commission
   - 50,000,001 - 150,000,000: 16% Commission
   - Over 150,000,000: 20% Commission

2. Total Earnings Components:
   - All host's total income (video calls, voice calls, text chats, gifts)
   - Total income of all invite agents
   - Excludes: Platform rewards, tasks, rankings

3. Rules:
   - If agent inactive for 7+ days: commission doesn't count
   - If agent temporarily banned: commission doesn't count
   - Commissions paid in Agent Coins
"""

# Commission Brackets based on 30-day earnings
COMMISSION_BRACKETS = [
    {"min": 0, "max": 2000000, "rate": 4},
    {"min": 2000001, "max": 10000000, "rate": 8},
    {"min": 10000001, "max": 50000000, "rate": 12},
    {"min": 50000001, "max": 150000000, "rate": 16},
    {"min": 150000001, "max": 999999999999, "rate": 20},
]

# Legacy Agency Levels (for backward compatibility)
AGENCY_LEVELS = {
    0: {"name": "Member", "commission_rate": 0, "monthly_threshold": 0},
    1: {"name": "Agent Level 1", "commission_rate": 4, "monthly_threshold": 0},
    2: {"name": "Agent Level 2", "commission_rate": 8, "monthly_threshold": 2000000},
    3: {"name": "Agent Level 3", "commission_rate": 12, "monthly_threshold": 10000000},
    4: {"name": "Agent Level 4", "commission_rate": 16, "monthly_threshold": 50000000},
    5: {"name": "Agent Level 5", "commission_rate": 20, "monthly_threshold": 150000000},
}

STARS_TO_COINS_FEE = 8  # 8% service fee
AGENT_INACTIVE_DAYS = 7  # Days after which agent is considered inactive

def get_commission_rate(total_earnings: float) -> dict:
    """Get commission rate based on 30-day total earnings"""
    for bracket in COMMISSION_BRACKETS:
        if bracket["min"] <= total_earnings <= bracket["max"]:
            return {"rate": bracket["rate"], "bracket": bracket}
    return {"rate": 20, "bracket": COMMISSION_BRACKETS[-1]}

def get_agent_level(total_earnings: float) -> int:
    """Get agent level based on 30-day earnings"""
    for level, info in sorted(AGENCY_LEVELS.items(), reverse=True):
        if total_earnings >= info["monthly_threshold"]:
            return level
    return 0

class AgencyStatus(BaseModel):
    user_id: str
    agency_level: int = 0
    referral_code: str
    total_referrals: int = 0
    active_referrals: int = 0
    total_commission_earned: float = 0
    agent_coins: float = 0  # Agent Coins balance
    last_30_days_earnings: float = 0
    monthly_volume: float = 0
    monthly_volume_reset_date: str
    last_active_date: str
    is_active: bool = True
    is_banned: bool = False
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
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        agency = {
            "user_id": current_user.user_id,
            "agency_level": 0,
            "referral_code": referral_code,
            "total_referrals": 0,
            "active_referrals": 0,
            "total_commission_earned": 0,
            "agent_coins": 0,
            "last_30_days_earnings": 0,
            "monthly_volume": 0,
            "monthly_volume_reset_date": datetime.now(timezone.utc).strftime("%Y-%m-01"),
            "last_active_date": today,
            "is_active": True,
            "is_banned": False,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        await db.agency_status.insert_one(agency)
    
    # Calculate 30-day earnings
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    
    # Get host income (video, voice, text, gifts) - excludes platform rewards
    host_income = await db.host_sessions.aggregate([
        {"$match": {
            "user_id": current_user.user_id,
            "created_at": {"$gte": thirty_days_ago},
            "status": "completed"
        }},
        {"$group": {"_id": None, "total": {"$sum": "$stars_earned"}}}
    ]).to_list(1)
    
    gift_income = await db.gift_records.aggregate([
        {"$match": {
            "receiver_id": current_user.user_id,
            "created_at": {"$gte": thirty_days_ago}
        }},
        {"$group": {"_id": None, "total": {"$sum": "$total_value"}}}
    ]).to_list(1)
    
    # Get invite agent income
    referrals = await db.referrals.find(
        {"referrer_id": current_user.user_id},
        {"_id": 0}
    ).to_list(100)
    
    invite_agent_income = 0
    for ref in referrals:
        ref_income = await db.agent_commissions.aggregate([
            {"$match": {
                "from_user_id": ref["referred_id"],
                "created_at": {"$gte": thirty_days_ago}
            }},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]).to_list(1)
        if ref_income:
            invite_agent_income += ref_income[0].get("total", 0)
    
    total_30_day_earnings = (
        (host_income[0].get("total", 0) if host_income else 0) +
        (gift_income[0].get("total", 0) if gift_income else 0) +
        invite_agent_income
    )
    
    # Get commission rate based on earnings
    commission_info = get_commission_rate(total_30_day_earnings)
    agent_level = get_agent_level(total_30_day_earnings)
    
    # Check if agent is active (last 7 days)
    last_active = agency.get("last_active_date", "")
    if last_active:
        try:
            last_active_date = datetime.strptime(last_active, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            days_inactive = (datetime.now(timezone.utc) - last_active_date).days
            is_active = days_inactive < AGENT_INACTIVE_DAYS
        except:
            is_active = True
    else:
        is_active = True
    
    # Update agency status
    await db.agency_status.update_one(
        {"user_id": current_user.user_id},
        {
            "$set": {
                "agency_level": agent_level,
                "last_30_days_earnings": total_30_day_earnings,
                "is_active": is_active,
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )
    
    level_info = AGENCY_LEVELS.get(agent_level, AGENCY_LEVELS[0])
    next_level = agent_level + 1
    next_level_info = AGENCY_LEVELS.get(next_level, None)
    
    return {
        **agency,
        "agency_level": agent_level,
        "last_30_days_earnings": total_30_day_earnings,
        "current_commission_rate": commission_info["rate"],
        "commission_bracket": commission_info["bracket"],
        "level_info": level_info,
        "next_level_info": next_level_info,
        "referrals": referrals,
        "is_active": is_active,
        "inactive_warning": not is_active,
        "all_levels": AGENCY_LEVELS,
        "commission_brackets": COMMISSION_BRACKETS,
        "earnings_breakdown": {
            "host_income": host_income[0].get("total", 0) if host_income else 0,
            "gift_income": gift_income[0].get("total", 0) if gift_income else 0,
            "invite_agent_income": invite_agent_income
        }
    }
    
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

# ==================== CHARITY LUCKY WALLET (GAME SYSTEM) ====================

"""
CHARITY LUCKY WALLET - Game Rules:
1. Winning Rate: EXACTLY 45%
2. If WIN: User gets 70% of bet amount, 30% goes to Charity
3. If LOSE: 45% goes to Charity, 55% goes to Platform
4. All transactions are tracked for transparency
5. No errors allowed - calculations must be accurate
"""

CHARITY_LUCKY_WALLET_CONFIG = {
    "winning_rate": 45,  # 45% chance of winning
    "win_user_percent": 70,  # Winner gets 70% of bet
    "win_charity_percent": 30,  # 30% of bet goes to charity on win
    "lose_charity_percent": 45,  # 45% of lost bet goes to charity
    "lose_platform_percent": 55,  # 55% of lost bet goes to platform
    "min_bet": 10,  # Minimum bet amount
    "max_bet": 100000,  # Maximum bet amount
}

class PlayLuckyWalletRequest(BaseModel):
    bet_amount: float
    charity_boost: bool = False  # If true, extra goes to charity

@api_router.get("/lucky-wallet/config")
async def get_lucky_wallet_config():
    """Get Charity Lucky Wallet configuration"""
    return {
        "config": CHARITY_LUCKY_WALLET_CONFIG,
        "description": "Charity Lucky Wallet - 45% winning chance. Help charity while playing!"
    }

@api_router.get("/lucky-wallet/stats")
async def get_lucky_wallet_stats(current_user: User = Depends(get_current_user)):
    """Get user's Lucky Wallet game statistics"""
    # Get user's game history
    games = await db.lucky_wallet_games.find(
        {"user_id": current_user.user_id},
        {"_id": 0}
    ).to_list(1000)
    
    total_games = len(games)
    wins = sum(1 for g in games if g["result"] == "win")
    losses = total_games - wins
    total_bet = sum(g["bet_amount"] for g in games)
    total_won = sum(g["won_amount"] for g in games if g["result"] == "win")
    total_charity = sum(g["charity_amount"] for g in games)
    
    win_rate = (wins / total_games * 100) if total_games > 0 else 0
    
    # Today's stats
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    today_games = await db.lucky_wallet_games.find(
        {"user_id": current_user.user_id, "date": today},
        {"_id": 0}
    ).to_list(100)
    
    today_total = len(today_games)
    today_wins = sum(1 for g in today_games if g["result"] == "win")
    today_bet = sum(g["bet_amount"] for g in today_games)
    today_won = sum(g["won_amount"] for g in today_games if g["result"] == "win")
    today_charity = sum(g["charity_amount"] for g in today_games)
    
    return {
        "all_time": {
            "total_games": total_games,
            "wins": wins,
            "losses": losses,
            "win_rate": round(win_rate, 2),
            "total_bet": total_bet,
            "total_won": total_won,
            "net_profit": total_won - total_bet,
            "total_charity_contribution": total_charity
        },
        "today": {
            "total_games": today_total,
            "wins": today_wins,
            "losses": today_total - today_wins,
            "total_bet": today_bet,
            "total_won": today_won,
            "total_charity_contribution": today_charity
        }
    }

@api_router.post("/lucky-wallet/play")
async def play_lucky_wallet(
    request: PlayLuckyWalletRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Play Charity Lucky Wallet Game
    
    GAME RULES:
    - 45% chance of winning
    - WIN: User gets 70% of bet, 30% to charity
    - LOSE: 45% to charity, 55% to platform
    """
    
    # Validate bet amount
    if request.bet_amount < CHARITY_LUCKY_WALLET_CONFIG["min_bet"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Minimum bet is {CHARITY_LUCKY_WALLET_CONFIG['min_bet']} coins"
        )
    
    if request.bet_amount > CHARITY_LUCKY_WALLET_CONFIG["max_bet"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Maximum bet is {CHARITY_LUCKY_WALLET_CONFIG['max_bet']} coins"
        )
    
    # Check user's wallet balance
    wallet = await db.wallets.find_one(
        {"user_id": current_user.user_id},
        {"_id": 0}
    )
    
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    
    if wallet["coins_balance"] < request.bet_amount:
        raise HTTPException(
            status_code=400, 
            detail=f"Insufficient balance. You have {wallet['coins_balance']} coins, need {request.bet_amount} coins"
        )
    
    # Generate random number for game result (1-100)
    random_number = random.randint(1, 100)
    is_winner = random_number <= CHARITY_LUCKY_WALLET_CONFIG["winning_rate"]  # 45% chance
    
    # Calculate amounts based on result
    bet_amount = float(request.bet_amount)
    
    if is_winner:
        # USER WINS - Gets 70% of bet, 30% to charity
        won_amount = round(bet_amount * (CHARITY_LUCKY_WALLET_CONFIG["win_user_percent"] / 100), 2)
        charity_amount = round(bet_amount * (CHARITY_LUCKY_WALLET_CONFIG["win_charity_percent"] / 100), 2)
        platform_amount = 0.0
        result = "win"
        
        # User profit = won_amount - bet_amount (can be negative if 70% < 100%)
        # Actually, user gets back won_amount, so net = won_amount - bet_amount
        # 70% of bet means user loses 30% net
        # Let me recalculate: If bet 100, win: get 70 back. Net = 70 - 100 = -30
        # That doesn't seem right. Let me reconsider...
        
        # Better logic: Win means user gets bet + 70% bonus
        # So if bet 100 and win: get back 100 + 70 = 170
        # 30% of WINNINGS goes to charity
        # Winnings = 70% of bet = 70
        # Charity from win = 30% of 70 = 21
        # User gets = 100 + 70 - 21 = 149? 
        
        # Simplest interpretation: 
        # WIN: User gets 70% of bet back (loses 30%), 30% goes to charity
        # So bet 100, win: get 70, charity gets 30
        
        # Final user balance change on WIN
        balance_change = won_amount - bet_amount  # 70 - 100 = -30 (user still loses 30%)
        
    else:
        # USER LOSES - 45% to charity, 55% to platform
        won_amount = 0.0
        charity_amount = round(bet_amount * (CHARITY_LUCKY_WALLET_CONFIG["lose_charity_percent"] / 100), 2)
        platform_amount = round(bet_amount * (CHARITY_LUCKY_WALLET_CONFIG["lose_platform_percent"] / 100), 2)
        result = "lose"
        balance_change = -bet_amount  # User loses entire bet
    
    # Update user's wallet
    new_balance = wallet["coins_balance"] + balance_change
    
    await db.wallets.update_one(
        {"user_id": current_user.user_id},
        {
            "$set": {
                "coins_balance": round(new_balance, 2),
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )
    
    # Update charity wallet
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
    
    # Record game
    game_id = f"game_{uuid.uuid4().hex[:12]}"
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    game_record = {
        "game_id": game_id,
        "user_id": current_user.user_id,
        "bet_amount": bet_amount,
        "result": result,
        "random_number": random_number,
        "winning_threshold": CHARITY_LUCKY_WALLET_CONFIG["winning_rate"],
        "won_amount": won_amount,
        "charity_amount": charity_amount,
        "platform_amount": platform_amount,
        "balance_change": balance_change,
        "new_balance": round(new_balance, 2),
        "charity_boost": request.charity_boost,
        "date": today,
        "created_at": datetime.now(timezone.utc)
    }
    
    await db.lucky_wallet_games.insert_one(game_record)
    
    # Record charity contribution
    await db.charity_contributions.insert_one({
        "contribution_id": f"char_{uuid.uuid4().hex[:12]}",
        "user_id": current_user.user_id,
        "amount": charity_amount,
        "source": "lucky_wallet",
        "game_id": game_id,
        "result": result,
        "created_at": datetime.now(timezone.utc)
    })
    
    # Create wallet transaction
    transaction_id = f"txn_{uuid.uuid4().hex[:12]}"
    await db.wallet_transactions.insert_one({
        "transaction_id": transaction_id,
        "user_id": current_user.user_id,
        "transaction_type": "lucky_wallet_bet" if result == "lose" else "lucky_wallet_win",
        "amount": balance_change,
        "currency_type": "coins",
        "status": TransactionStatus.COMPLETED,
        "reference_id": game_id,
        "description": f"Charity Lucky Wallet - {'Won' if is_winner else 'Lost'} (Bet: {bet_amount}, Charity: {charity_amount})",
        "created_at": datetime.now(timezone.utc)
    })
    
    # Send notification
    if is_winner:
        notif_title = "You Won! 🎉"
        notif_message = f"Congratulations! You won {won_amount} coins. {charity_amount} coins went to charity!"
    else:
        notif_title = "Better luck next time! 💪"
        notif_message = f"You lost {bet_amount} coins. But {charity_amount} coins went to charity to help others!"
    
    await db.notifications.insert_one({
        "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
        "user_id": current_user.user_id,
        "title": notif_title,
        "message": notif_message,
        "notification_type": "lucky_wallet",
        "is_read": False,
        "action_url": "/lucky-wallet",
        "created_at": datetime.now(timezone.utc)
    })
    
    return {
        "success": True,
        "game_id": game_id,
        "result": result,
        "is_winner": is_winner,
        "bet_amount": bet_amount,
        "won_amount": won_amount,
        "charity_contribution": charity_amount,
        "platform_amount": platform_amount,
        "balance_change": balance_change,
        "new_balance": round(new_balance, 2),
        "random_number": random_number,
        "winning_threshold": CHARITY_LUCKY_WALLET_CONFIG["winning_rate"],
        "transaction_id": transaction_id
    }

@api_router.get("/lucky-wallet/history")
async def get_lucky_wallet_history(
    limit: int = 20,
    current_user: User = Depends(get_current_user)
):
    """Get user's Charity Lucky Wallet game history"""
    games = await db.lucky_wallet_games.find(
        {"user_id": current_user.user_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    return {"games": games}

@api_router.get("/lucky-wallet/leaderboard")
async def get_lucky_wallet_leaderboard():
    """Get Lucky Wallet leaderboard - top winners and charity contributors"""
    
    # Top winners by total won
    winner_pipeline = [
        {"$match": {"result": "win"}},
        {"$group": {
            "_id": "$user_id",
            "total_won": {"$sum": "$won_amount"},
            "games_won": {"$sum": 1}
        }},
        {"$sort": {"total_won": -1}},
        {"$limit": 10}
    ]
    
    top_winners = await db.lucky_wallet_games.aggregate(winner_pipeline).to_list(10)
    
    # Top charity contributors
    charity_pipeline = [
        {"$group": {
            "_id": "$user_id",
            "total_charity": {"$sum": "$charity_amount"},
            "total_games": {"$sum": 1}
        }},
        {"$sort": {"total_charity": -1}},
        {"$limit": 10}
    ]
    
    top_contributors = await db.lucky_wallet_games.aggregate(charity_pipeline).to_list(10)
    
    # Get user details
    winners_leaderboard = []
    for i, winner in enumerate(top_winners):
        user = await db.users.find_one(
            {"user_id": winner["_id"]},
            {"_id": 0, "user_id": 1, "name": 1, "picture": 1}
        )
        if user:
            winners_leaderboard.append({
                "rank": i + 1,
                "user": user,
                "total_won": winner["total_won"],
                "games_won": winner["games_won"]
            })
    
    contributors_leaderboard = []
    for i, contributor in enumerate(top_contributors):
        user = await db.users.find_one(
            {"user_id": contributor["_id"]},
            {"_id": 0, "user_id": 1, "name": 1, "picture": 1}
        )
        if user:
            contributors_leaderboard.append({
                "rank": i + 1,
                "user": user,
                "total_charity": contributor["total_charity"],
                "total_games": contributor["total_games"]
            })
    
    return {
        "top_winners": winners_leaderboard,
        "top_charity_contributors": contributors_leaderboard
    }

# ==================== HOST POLICY SYSTEM (VONE STYLE) ====================

"""
VONE STYLE HOST POLICY:

1. WELCOME PERIOD (First 7 Days):
   - Video Live: 1 hour = 2,000 Stars
   - Audio Live: 2 hours = 3,000 Stars (1,500 x 2 sessions)

2. NORMAL HOST POLICY (After 7 Days):
   - Video Live: 1 hour = 1,000 Stars
   - Daily Target: 3,000 Stars

3. HIGH-EARNER BONUS (300K Gift Rule):
   - If host receives 300K Stars in gifts = 3,000 Stars bonus
   
4. CHARITY: 2% of all high-earner gifts go to charity
"""

HOST_POLICY_CONFIG = {
    # Welcome Period (First 7 Days)
    "welcome_period_days": 7,
    "welcome_video_reward_per_hour": 2000,  # Stars
    "welcome_audio_reward_per_2hours": 3000,  # Stars (1500 x 2)
    
    # Normal Policy (After 7 Days)
    "normal_video_reward_per_hour": 1000,  # Stars
    "normal_audio_reward_per_hour": 500,  # Stars
    "daily_target_stars": 3000,
    
    # High-Earner Bonus
    "high_earner_threshold": 300000,  # 300K Stars
    "high_earner_bonus": 3000,  # Stars (1500 x 2)
    "high_earner_charity_percent": 2,  # 2% to charity
    
    # Minimum session requirements
    "min_video_minutes": 60,  # 1 hour minimum for video
    "min_audio_minutes": 120,  # 2 hours minimum for audio
}

class HostType(str, Enum):
    VIDEO = "video"
    AUDIO = "audio"

class HostSession(BaseModel):
    session_id: str
    user_id: str
    host_type: HostType
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_minutes: int = 0
    stars_earned: float = 0
    is_welcome_period: bool = False
    status: str = "active"  # active, completed, cancelled

@api_router.get("/host/policy")
async def get_host_policy():
    """Get host policy configuration"""
    return {
        "config": HOST_POLICY_CONFIG,
        "description": "Vone Style Host Policy - Earn stars by going live!"
    }

@api_router.get("/host/status")
async def get_host_status(current_user: User = Depends(get_current_user)):
    """Get user's host status and eligibility"""
    
    # Check if user is registered as host
    host_profile = await db.host_profiles.find_one(
        {"user_id": current_user.user_id},
        {"_id": 0}
    )
    
    if not host_profile:
        # Create host profile
        host_profile = {
            "user_id": current_user.user_id,
            "registered_at": datetime.now(timezone.utc),
            "total_live_minutes": 0,
            "total_stars_earned": 0,
            "total_gifts_received": 0,
            "is_verified": False,
            "level": "new",
            "created_at": datetime.now(timezone.utc)
        }
        await db.host_profiles.insert_one(host_profile)
    
    # Calculate days since registration
    registered_at = host_profile.get("registered_at", host_profile.get("created_at"))
    if registered_at.tzinfo is None:
        registered_at = registered_at.replace(tzinfo=timezone.utc)
    
    days_since_registration = (datetime.now(timezone.utc) - registered_at).days
    is_welcome_period = days_since_registration < HOST_POLICY_CONFIG["welcome_period_days"]
    
    # Get today's sessions
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    today_sessions = await db.host_sessions.find(
        {"user_id": current_user.user_id, "date": today, "status": "completed"},
        {"_id": 0}
    ).to_list(100)
    
    today_video_minutes = sum(s["duration_minutes"] for s in today_sessions if s["host_type"] == "video")
    today_audio_minutes = sum(s["duration_minutes"] for s in today_sessions if s["host_type"] == "audio")
    today_stars_earned = sum(s["stars_earned"] for s in today_sessions)
    
    # Check for active session
    active_session = await db.host_sessions.find_one(
        {"user_id": current_user.user_id, "status": "active"},
        {"_id": 0}
    )
    
    # Calculate current rewards based on policy
    if is_welcome_period:
        video_reward = HOST_POLICY_CONFIG["welcome_video_reward_per_hour"]
        audio_reward = HOST_POLICY_CONFIG["welcome_audio_reward_per_2hours"]
    else:
        video_reward = HOST_POLICY_CONFIG["normal_video_reward_per_hour"]
        audio_reward = HOST_POLICY_CONFIG["normal_audio_reward_per_hour"] * 2
    
    # Check high-earner status
    is_high_earner = host_profile.get("total_gifts_received", 0) >= HOST_POLICY_CONFIG["high_earner_threshold"]
    
    return {
        "user_id": current_user.user_id,
        "host_profile": host_profile,
        "days_since_registration": days_since_registration,
        "is_welcome_period": is_welcome_period,
        "welcome_days_remaining": max(0, HOST_POLICY_CONFIG["welcome_period_days"] - days_since_registration),
        "is_high_earner": is_high_earner,
        "current_rewards": {
            "video_per_hour": video_reward,
            "audio_per_2hours": audio_reward
        },
        "today_stats": {
            "video_minutes": today_video_minutes,
            "audio_minutes": today_audio_minutes,
            "stars_earned": today_stars_earned,
            "target_progress": (today_stars_earned / HOST_POLICY_CONFIG["daily_target_stars"]) * 100
        },
        "active_session": active_session
    }

class StartHostSessionRequest(BaseModel):
    host_type: HostType

@api_router.post("/host/start-session")
async def start_host_session(
    request: StartHostSessionRequest,
    current_user: User = Depends(get_current_user)
):
    """Start a live hosting session"""
    
    # Check for existing active session
    active_session = await db.host_sessions.find_one(
        {"user_id": current_user.user_id, "status": "active"},
        {"_id": 0}
    )
    
    if active_session:
        raise HTTPException(status_code=400, detail="You already have an active session")
    
    # Get host profile
    host_profile = await db.host_profiles.find_one(
        {"user_id": current_user.user_id},
        {"_id": 0}
    )
    
    if not host_profile:
        # Create host profile
        host_profile = {
            "user_id": current_user.user_id,
            "registered_at": datetime.now(timezone.utc),
            "total_live_minutes": 0,
            "total_stars_earned": 0,
            "total_gifts_received": 0,
            "is_verified": False,
            "level": "new",
            "created_at": datetime.now(timezone.utc)
        }
        await db.host_profiles.insert_one(host_profile)
    
    # Check if in welcome period
    registered_at = host_profile.get("registered_at", host_profile.get("created_at"))
    if registered_at.tzinfo is None:
        registered_at = registered_at.replace(tzinfo=timezone.utc)
    
    days_since_registration = (datetime.now(timezone.utc) - registered_at).days
    is_welcome_period = days_since_registration < HOST_POLICY_CONFIG["welcome_period_days"]
    
    # Create session
    session_id = f"session_{uuid.uuid4().hex[:12]}"
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    session = {
        "session_id": session_id,
        "user_id": current_user.user_id,
        "host_type": request.host_type,
        "started_at": datetime.now(timezone.utc),
        "ended_at": None,
        "duration_minutes": 0,
        "stars_earned": 0,
        "is_welcome_period": is_welcome_period,
        "status": "active",
        "date": today,
        "created_at": datetime.now(timezone.utc)
    }
    
    await db.host_sessions.insert_one(session)
    
    return {
        "success": True,
        "session_id": session_id,
        "host_type": request.host_type,
        "is_welcome_period": is_welcome_period,
        "started_at": session["started_at"].isoformat()
    }

@api_router.post("/host/end-session/{session_id}")
async def end_host_session(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """End a live hosting session and calculate rewards"""
    
    # Get session
    session = await db.host_sessions.find_one(
        {"session_id": session_id, "user_id": current_user.user_id, "status": "active"},
        {"_id": 0}
    )
    
    if not session:
        raise HTTPException(status_code=404, detail="Active session not found")
    
    # Calculate duration
    started_at = session["started_at"]
    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=timezone.utc)
    
    ended_at = datetime.now(timezone.utc)
    duration_minutes = int((ended_at - started_at).total_seconds() / 60)
    
    # Calculate rewards based on policy
    stars_earned = 0
    host_type = session["host_type"]
    is_welcome = session["is_welcome_period"]
    
    if host_type == "video":
        if is_welcome:
            # Welcome period: 2,000 Stars per hour
            if duration_minutes >= HOST_POLICY_CONFIG["min_video_minutes"]:
                hours = duration_minutes // 60
                stars_earned = hours * HOST_POLICY_CONFIG["welcome_video_reward_per_hour"]
        else:
            # Normal: 1,000 Stars per hour
            if duration_minutes >= HOST_POLICY_CONFIG["min_video_minutes"]:
                hours = duration_minutes // 60
                stars_earned = hours * HOST_POLICY_CONFIG["normal_video_reward_per_hour"]
    
    elif host_type == "audio":
        if is_welcome:
            # Welcome period: 3,000 Stars per 2 hours (1500 x 2)
            if duration_minutes >= HOST_POLICY_CONFIG["min_audio_minutes"]:
                two_hour_blocks = duration_minutes // 120
                stars_earned = two_hour_blocks * HOST_POLICY_CONFIG["welcome_audio_reward_per_2hours"]
        else:
            # Normal: 500 Stars per hour
            hours = duration_minutes // 60
            stars_earned = hours * HOST_POLICY_CONFIG["normal_audio_reward_per_hour"]
    
    # Update session
    await db.host_sessions.update_one(
        {"session_id": session_id},
        {
            "$set": {
                "ended_at": ended_at,
                "duration_minutes": duration_minutes,
                "stars_earned": stars_earned,
                "status": "completed"
            }
        }
    )
    
    # Credit stars to wallet if earned
    if stars_earned > 0:
        await db.wallets.update_one(
            {"user_id": current_user.user_id},
            {
                "$inc": {"stars_balance": stars_earned},
                "$set": {"updated_at": datetime.now(timezone.utc)}
            }
        )
        
        # Create transaction
        await db.wallet_transactions.insert_one({
            "transaction_id": f"txn_{uuid.uuid4().hex[:12]}",
            "user_id": current_user.user_id,
            "transaction_type": "host_reward",
            "amount": stars_earned,
            "currency_type": "stars",
            "status": TransactionStatus.COMPLETED,
            "reference_id": session_id,
            "description": f"{'Video' if host_type == 'video' else 'Audio'} Live Reward ({duration_minutes} mins)" + (" [Welcome Bonus]" if is_welcome else ""),
            "created_at": datetime.now(timezone.utc)
        })
        
        # Update host profile
        await db.host_profiles.update_one(
            {"user_id": current_user.user_id},
            {
                "$inc": {
                    "total_live_minutes": duration_minutes,
                    "total_stars_earned": stars_earned
                },
                "$set": {"updated_at": datetime.now(timezone.utc)}
            }
        )
        
        # Send notification
        await db.notifications.insert_one({
            "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
            "user_id": current_user.user_id,
            "title": "Live Session Completed! ⭐",
            "message": f"You earned {stars_earned} stars for your {duration_minutes} minute {'video' if host_type == 'video' else 'audio'} session!",
            "notification_type": "host_reward",
            "is_read": False,
            "action_url": "/host",
            "created_at": datetime.now(timezone.utc)
        })
    
    return {
        "success": True,
        "session_id": session_id,
        "duration_minutes": duration_minutes,
        "stars_earned": stars_earned,
        "is_welcome_period": is_welcome,
        "host_type": host_type,
        "message": f"Session ended. You earned {stars_earned} stars!" if stars_earned > 0 else f"Session ended. Minimum {HOST_POLICY_CONFIG['min_video_minutes'] if host_type == 'video' else HOST_POLICY_CONFIG['min_audio_minutes']} minutes required for rewards."
    }

@api_router.post("/host/check-high-earner-bonus")
async def check_high_earner_bonus(current_user: User = Depends(get_current_user)):
    """Check and claim high-earner bonus if eligible (300K gift rule)"""
    
    host_profile = await db.host_profiles.find_one(
        {"user_id": current_user.user_id},
        {"_id": 0}
    )
    
    if not host_profile:
        raise HTTPException(status_code=404, detail="Host profile not found")
    
    total_gifts = host_profile.get("total_gifts_received", 0)
    
    if total_gifts < HOST_POLICY_CONFIG["high_earner_threshold"]:
        remaining = HOST_POLICY_CONFIG["high_earner_threshold"] - total_gifts
        return {
            "eligible": False,
            "total_gifts_received": total_gifts,
            "threshold": HOST_POLICY_CONFIG["high_earner_threshold"],
            "remaining": remaining,
            "message": f"You need {remaining} more stars in gifts to qualify for high-earner bonus"
        }
    
    # Check if already claimed this month
    current_month = datetime.now(timezone.utc).strftime("%Y-%m")
    existing_bonus = await db.high_earner_bonuses.find_one({
        "user_id": current_user.user_id,
        "month": current_month
    })
    
    if existing_bonus:
        return {
            "eligible": True,
            "already_claimed": True,
            "total_gifts_received": total_gifts,
            "message": "You have already claimed your high-earner bonus this month"
        }
    
    # Credit bonus (3000 stars split into 2 instalments)
    bonus_amount = HOST_POLICY_CONFIG["high_earner_bonus"]
    instalment = bonus_amount / 2  # 1500 each
    
    # First instalment now
    await db.wallets.update_one(
        {"user_id": current_user.user_id},
        {
            "$inc": {"stars_balance": instalment},
            "$set": {"updated_at": datetime.now(timezone.utc)}
        }
    )
    
    # Record bonus
    await db.high_earner_bonuses.insert_one({
        "bonus_id": f"bonus_{uuid.uuid4().hex[:12]}",
        "user_id": current_user.user_id,
        "month": current_month,
        "total_bonus": bonus_amount,
        "instalment_1": instalment,
        "instalment_1_date": datetime.now(timezone.utc),
        "instalment_2": instalment,
        "instalment_2_date": datetime.now(timezone.utc) + timedelta(days=15),
        "status": "partial",
        "created_at": datetime.now(timezone.utc)
    })
    
    # Create transaction
    await db.wallet_transactions.insert_one({
        "transaction_id": f"txn_{uuid.uuid4().hex[:12]}",
        "user_id": current_user.user_id,
        "transaction_type": "high_earner_bonus",
        "amount": instalment,
        "currency_type": "stars",
        "status": TransactionStatus.COMPLETED,
        "description": f"High-Earner Bonus (Instalment 1/2) - 300K Gift Achievement",
        "created_at": datetime.now(timezone.utc)
    })
    
    # Calculate charity from gifts (2%)
    charity_amount = total_gifts * (HOST_POLICY_CONFIG["high_earner_charity_percent"] / 100)
    
    # Add to charity
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
    
    # Send notification
    await db.notifications.insert_one({
        "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
        "user_id": current_user.user_id,
        "title": "High-Earner Bonus Unlocked! 🏆",
        "message": f"Congratulations! You received {instalment} stars bonus (1st instalment). 2nd instalment in 15 days!",
        "notification_type": "high_earner",
        "is_read": False,
        "action_url": "/host",
        "created_at": datetime.now(timezone.utc)
    })
    
    return {
        "success": True,
        "eligible": True,
        "bonus_credited": instalment,
        "next_instalment": instalment,
        "next_instalment_date": (datetime.now(timezone.utc) + timedelta(days=15)).isoformat(),
        "charity_contribution": charity_amount,
        "message": f"High-Earner Bonus activated! {instalment} stars credited, {instalment} more in 15 days!"
    }

@api_router.get("/host/sessions")
async def get_host_sessions(
    limit: int = 20,
    current_user: User = Depends(get_current_user)
):
    """Get host session history"""
    sessions = await db.host_sessions.find(
        {"user_id": current_user.user_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    return {"sessions": sessions}

@api_router.get("/host/leaderboard")
async def get_host_leaderboard():
    """Get top hosts leaderboard"""
    
    # Top hosts by stars earned
    pipeline = [
        {"$group": {
            "_id": "$user_id",
            "total_stars": {"$sum": "$stars_earned"},
            "total_minutes": {"$sum": "$duration_minutes"},
            "session_count": {"$sum": 1}
        }},
        {"$sort": {"total_stars": -1}},
        {"$limit": 20}
    ]
    
    top_hosts = await db.host_sessions.aggregate(pipeline).to_list(20)
    
    # Get user details
    leaderboard = []
    for i, host in enumerate(top_hosts):
        user = await db.users.find_one(
            {"user_id": host["_id"]},
            {"_id": 0, "user_id": 1, "name": 1, "picture": 1}
        )
        if user:
            leaderboard.append({
                "rank": i + 1,
                "user": user,
                "total_stars": host["total_stars"],
                "total_minutes": host["total_minutes"],
                "session_count": host["session_count"]
            })
    
    return {"leaderboard": leaderboard}

# ==================== EDUCATION PLATFORM ====================

"""
EDUCATION PLATFORM FEATURES:
1. Gamified Learning - Courses with rewards
2. Mind Games - Cognitive skill enhancement games
3. Quizzes & Challenges - Knowledge testing with rewards
4. Learning Levels - Progress tracking (Seedling to Legend)
5. Study Groups - Peer-to-peer learning
6. Career Guidance - Counseling services
7. Charity Integration - Part of income to charity
"""

# Learning Levels (Labels)
LEARNING_LEVELS = {
    "seedling": {"min_hours": 0, "reward": 500, "badge_color": "#4CAF50"},
    "sprout": {"min_hours": 10, "reward": 1500, "badge_color": "#8BC34A"},
    "tree": {"min_hours": 25, "reward": 5000, "badge_color": "#CDDC39"},
    "star_learner": {"min_hours": 50, "reward": 15000, "badge_color": "#FFEB3B"},
    "diamond_scholar": {"min_hours": 100, "reward": 35000, "badge_color": "#03A9F4"},
    "master_guru": {"min_hours": 200, "reward": 75000, "badge_color": "#9C27B0"},
    "legend": {"min_hours": 500, "reward": 200000, "badge_color": "#FFD700"},
}

# Course Categories
COURSE_CATEGORIES = [
    "Mathematics", "Science", "English", "Computer Science", 
    "Business", "Arts", "Languages", "Life Skills", "Mind Games"
]

# Mind Games Configuration
MIND_GAMES = [
    {
        "game_id": "memory_match",
        "name": "Memory Match",
        "description": "Match pairs to improve memory",
        "category": "Mind Games",
        "difficulty": "easy",
        "coins_reward": 50,
        "time_limit_seconds": 120
    },
    {
        "game_id": "math_puzzle",
        "name": "Math Puzzle",
        "description": "Solve math problems quickly",
        "category": "Mind Games",
        "difficulty": "medium",
        "coins_reward": 100,
        "time_limit_seconds": 60
    },
    {
        "game_id": "word_scramble",
        "name": "Word Scramble",
        "description": "Unscramble words to build vocabulary",
        "category": "Mind Games",
        "difficulty": "easy",
        "coins_reward": 50,
        "time_limit_seconds": 90
    },
    {
        "game_id": "logic_puzzle",
        "name": "Logic Puzzle",
        "description": "Solve logical reasoning challenges",
        "category": "Mind Games",
        "difficulty": "hard",
        "coins_reward": 200,
        "time_limit_seconds": 180
    },
    {
        "game_id": "pattern_recognition",
        "name": "Pattern Recognition",
        "description": "Identify patterns and sequences",
        "category": "Mind Games",
        "difficulty": "medium",
        "coins_reward": 100,
        "time_limit_seconds": 120
    },
]

EDUCATION_CONFIG = {
    "quiz_correct_reward": 10,  # Coins per correct answer
    "quiz_completion_bonus": 50,  # Bonus for completing quiz
    "course_completion_bonus": 500,  # Bonus for completing course
    "daily_learning_target_minutes": 30,
    "daily_learning_reward": 100,
    "charity_percent": 5,  # 5% of education income to charity
}

@api_router.get("/education/config")
async def get_education_config():
    """Get education platform configuration"""
    return {
        "learning_levels": LEARNING_LEVELS,
        "categories": COURSE_CATEGORIES,
        "mind_games": MIND_GAMES,
        "config": EDUCATION_CONFIG
    }

@api_router.get("/education/profile")
async def get_education_profile(current_user: User = Depends(get_current_user)):
    """Get user's education profile and progress"""
    
    profile = await db.education_profiles.find_one(
        {"user_id": current_user.user_id},
        {"_id": 0}
    )
    
    if not profile:
        profile = {
            "user_id": current_user.user_id,
            "current_level": "seedling",
            "total_learning_hours": 0,
            "courses_completed": 0,
            "quizzes_completed": 0,
            "games_played": 0,
            "total_coins_earned": 0,
            "daily_streak": 0,
            "last_learning_date": None,
            "badges": [],
            "created_at": datetime.now(timezone.utc)
        }
        await db.education_profiles.insert_one(profile)
    
    # Calculate current level
    hours = profile.get("total_learning_hours", 0)
    current_level = "seedling"
    for level, info in sorted(LEARNING_LEVELS.items(), key=lambda x: x[1]["min_hours"], reverse=True):
        if hours >= info["min_hours"]:
            current_level = level
            break
    
    # Get today's learning stats
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    today_learning = await db.learning_sessions.aggregate([
        {"$match": {"user_id": current_user.user_id, "date": today}},
        {"$group": {"_id": None, "total_minutes": {"$sum": "$duration_minutes"}}}
    ]).to_list(1)
    
    today_minutes = today_learning[0].get("total_minutes", 0) if today_learning else 0
    
    # Get enrolled courses
    enrolled_courses = await db.course_enrollments.find(
        {"user_id": current_user.user_id},
        {"_id": 0}
    ).to_list(50)
    
    # Convert to list of dicts without ObjectId
    enrolled_courses_clean = []
    for course in enrolled_courses:
        if isinstance(course, dict):
            enrolled_courses_clean.append(course)
    
    level_info = LEARNING_LEVELS.get(current_level, LEARNING_LEVELS["seedling"])
    next_level = None
    for lvl, info in sorted(LEARNING_LEVELS.items(), key=lambda x: x[1]["min_hours"]):
        if info["min_hours"] > hours:
            next_level = {"name": lvl, **info}
            break
    
    return {
        **profile,
        "current_level": current_level,
        "level_info": level_info,
        "next_level": next_level,
        "hours_to_next_level": next_level["min_hours"] - hours if next_level else 0,
        "today_learning_minutes": today_minutes,
        "daily_target_minutes": EDUCATION_CONFIG["daily_learning_target_minutes"],
        "enrolled_courses": enrolled_courses_clean,
        "courses_enrolled": len(enrolled_courses_clean),
        "streak_days": profile.get("daily_streak", 0),
        "all_levels": LEARNING_LEVELS
    }

@api_router.get("/education/courses")
async def get_courses(
    category: Optional[str] = None,
    difficulty: Optional[str] = None
):
    """Get available courses"""
    
    # Sample courses (in real app, these would be in database)
    courses = [
        {
            "course_id": "math_basics",
            "title": "Mathematics Fundamentals",
            "description": "Learn basic math concepts",
            "category": "Mathematics",
            "difficulty": "beginner",
            "duration_hours": 10,
            "lessons_count": 20,
            "price": 0,  # Free
            "rating": 4.5,
            "enrollments": 1250,
            "instructor": "Prof. Ahmed Khan",
            "rewards": {"completion_coins": 500, "per_lesson_coins": 20}
        },
        {
            "course_id": "english_speaking",
            "title": "English Speaking Skills",
            "description": "Improve your spoken English",
            "category": "English",
            "difficulty": "beginner",
            "duration_hours": 15,
            "lessons_count": 30,
            "price": 0,
            "rating": 4.7,
            "enrollments": 2100,
            "instructor": "Sarah Wilson",
            "rewards": {"completion_coins": 750, "per_lesson_coins": 20}
        },
        {
            "course_id": "computer_basics",
            "title": "Computer Fundamentals",
            "description": "Learn basic computer skills",
            "category": "Computer Science",
            "difficulty": "beginner",
            "duration_hours": 8,
            "lessons_count": 16,
            "price": 0,
            "rating": 4.6,
            "enrollments": 1800,
            "instructor": "Tech Expert Ali",
            "rewards": {"completion_coins": 400, "per_lesson_coins": 20}
        },
        {
            "course_id": "business_skills",
            "title": "Business & Entrepreneurship",
            "description": "Learn business fundamentals",
            "category": "Business",
            "difficulty": "intermediate",
            "duration_hours": 20,
            "lessons_count": 40,
            "price": 500,  # Premium
            "rating": 4.8,
            "enrollments": 950,
            "instructor": "Business Coach Hassan",
            "rewards": {"completion_coins": 1000, "per_lesson_coins": 25}
        },
        {
            "course_id": "mind_training",
            "title": "Mind Training & Focus",
            "description": "Enhance cognitive abilities",
            "category": "Mind Games",
            "difficulty": "all",
            "duration_hours": 5,
            "lessons_count": 10,
            "price": 0,
            "rating": 4.9,
            "enrollments": 3200,
            "instructor": "Mind Coach",
            "rewards": {"completion_coins": 300, "per_lesson_coins": 30}
        },
    ]
    
    # Filter by category
    if category:
        courses = [c for c in courses if c["category"] == category]
    
    # Filter by difficulty
    if difficulty:
        courses = [c for c in courses if c["difficulty"] == difficulty or c["difficulty"] == "all"]
    
    return {"courses": courses, "total": len(courses)}

class EnrollCourseRequest(BaseModel):
    course_id: str

@api_router.post("/education/enroll")
async def enroll_in_course(
    request: EnrollCourseRequest,
    current_user: User = Depends(get_current_user)
):
    """Enroll in a course"""
    
    # Check if already enrolled
    existing = await db.course_enrollments.find_one({
        "user_id": current_user.user_id,
        "course_id": request.course_id
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="Already enrolled in this course")
    
    enrollment = {
        "enrollment_id": f"enroll_{uuid.uuid4().hex[:12]}",
        "user_id": current_user.user_id,
        "course_id": request.course_id,
        "progress_percent": 0,
        "lessons_completed": 0,
        "total_lessons": 20,  # Would come from course data
        "coins_earned": 0,
        "started_at": datetime.now(timezone.utc),
        "last_accessed": datetime.now(timezone.utc),
        "status": "in_progress"
    }
    
    await db.course_enrollments.insert_one(enrollment)
    
    # Update education profile
    await db.education_profiles.update_one(
        {"user_id": current_user.user_id},
        {"$set": {"updated_at": datetime.now(timezone.utc)}},
        upsert=True
    )
    
    return {"success": True, "enrollment": enrollment}

class CompleteLessonRequest(BaseModel):
    course_id: str
    lesson_id: str
    duration_minutes: int

@api_router.post("/education/complete-lesson")
async def complete_lesson(
    request: CompleteLessonRequest,
    current_user: User = Depends(get_current_user)
):
    """Complete a lesson and earn rewards"""
    
    enrollment = await db.course_enrollments.find_one({
        "user_id": current_user.user_id,
        "course_id": request.course_id
    })
    
    if not enrollment:
        raise HTTPException(status_code=404, detail="Not enrolled in this course")
    
    # Award coins for lesson
    coins_earned = 20  # Per lesson reward
    
    # Update wallet
    await db.wallets.update_one(
        {"user_id": current_user.user_id},
        {
            "$inc": {"coins_balance": coins_earned},
            "$set": {"updated_at": datetime.now(timezone.utc)}
        }
    )
    
    # Update enrollment
    new_lessons = enrollment["lessons_completed"] + 1
    new_progress = min(100, (new_lessons / enrollment["total_lessons"]) * 100)
    
    await db.course_enrollments.update_one(
        {"user_id": current_user.user_id, "course_id": request.course_id},
        {
            "$inc": {"lessons_completed": 1, "coins_earned": coins_earned},
            "$set": {
                "progress_percent": new_progress,
                "last_accessed": datetime.now(timezone.utc),
                "status": "completed" if new_progress >= 100 else "in_progress"
            }
        }
    )
    
    # Record learning session
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    await db.learning_sessions.insert_one({
        "session_id": f"learn_{uuid.uuid4().hex[:12]}",
        "user_id": current_user.user_id,
        "course_id": request.course_id,
        "lesson_id": request.lesson_id,
        "duration_minutes": request.duration_minutes,
        "coins_earned": coins_earned,
        "date": today,
        "created_at": datetime.now(timezone.utc)
    })
    
    # Update education profile
    hours_added = request.duration_minutes / 60
    await db.education_profiles.update_one(
        {"user_id": current_user.user_id},
        {
            "$inc": {
                "total_learning_hours": hours_added,
                "total_coins_earned": coins_earned
            },
            "$set": {
                "last_learning_date": today,
                "updated_at": datetime.now(timezone.utc)
            }
        },
        upsert=True
    )
    
    # Create transaction
    await db.wallet_transactions.insert_one({
        "transaction_id": f"txn_{uuid.uuid4().hex[:12]}",
        "user_id": current_user.user_id,
        "transaction_type": "education_reward",
        "amount": coins_earned,
        "currency_type": "coins",
        "status": TransactionStatus.COMPLETED,
        "description": f"Completed lesson in {request.course_id}",
        "created_at": datetime.now(timezone.utc)
    })
    
    # Check if course completed
    bonus_earned = 0
    if new_progress >= 100:
        bonus_earned = EDUCATION_CONFIG["course_completion_bonus"]
        await db.wallets.update_one(
            {"user_id": current_user.user_id},
            {"$inc": {"coins_balance": bonus_earned}}
        )
        
        await db.education_profiles.update_one(
            {"user_id": current_user.user_id},
            {"$inc": {"courses_completed": 1}}
        )
        
        await db.notifications.insert_one({
            "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
            "user_id": current_user.user_id,
            "title": "Course Completed! 🎓",
            "message": f"Congratulations! You completed the course and earned {bonus_earned} bonus coins!",
            "notification_type": "education",
            "is_read": False,
            "action_url": "/education",
            "created_at": datetime.now(timezone.utc)
        })
    
    return {
        "success": True,
        "coins_earned": coins_earned,
        "bonus_earned": bonus_earned,
        "new_progress": new_progress,
        "is_course_completed": new_progress >= 100
    }

# Mind Games
@api_router.get("/education/mind-games")
async def get_mind_games():
    """Get available mind games"""
    return {"games": MIND_GAMES}

class PlayMindGameRequest(BaseModel):
    game_id: str
    score: int
    time_taken_seconds: int

@api_router.post("/education/play-mind-game")
async def play_mind_game(
    request: PlayMindGameRequest,
    current_user: User = Depends(get_current_user)
):
    """Submit mind game result and earn rewards"""
    
    # Find the game
    game = next((g for g in MIND_GAMES if g["game_id"] == request.game_id), None)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    # Calculate rewards based on score and time
    max_score = 100
    score_percent = min(100, (request.score / max_score) * 100)
    
    # Reward calculation: Higher score = more coins
    base_reward = game["coins_reward"]
    earned_reward = int(base_reward * (score_percent / 100))
    
    # Time bonus: Faster = more coins
    if request.time_taken_seconds < game["time_limit_seconds"] * 0.5:
        earned_reward = int(earned_reward * 1.5)  # 50% bonus for fast completion
    
    # Award coins
    await db.wallets.update_one(
        {"user_id": current_user.user_id},
        {
            "$inc": {"coins_balance": earned_reward},
            "$set": {"updated_at": datetime.now(timezone.utc)}
        }
    )
    
    # Record game
    await db.mind_game_records.insert_one({
        "record_id": f"game_{uuid.uuid4().hex[:12]}",
        "user_id": current_user.user_id,
        "game_id": request.game_id,
        "score": request.score,
        "time_taken_seconds": request.time_taken_seconds,
        "coins_earned": earned_reward,
        "created_at": datetime.now(timezone.utc)
    })
    
    # Update education profile
    await db.education_profiles.update_one(
        {"user_id": current_user.user_id},
        {
            "$inc": {"games_played": 1, "total_coins_earned": earned_reward},
            "$set": {"updated_at": datetime.now(timezone.utc)}
        },
        upsert=True
    )
    
    # Create transaction
    await db.wallet_transactions.insert_one({
        "transaction_id": f"txn_{uuid.uuid4().hex[:12]}",
        "user_id": current_user.user_id,
        "transaction_type": "mind_game_reward",
        "amount": earned_reward,
        "currency_type": "coins",
        "status": TransactionStatus.COMPLETED,
        "description": f"Mind Game: {game['name']} - Score: {request.score}",
        "created_at": datetime.now(timezone.utc)
    })
    
    return {
        "success": True,
        "game": game["name"],
        "score": request.score,
        "score_percent": score_percent,
        "coins_earned": earned_reward,
        "time_taken": request.time_taken_seconds,
        "time_limit": game["time_limit_seconds"]
    }

@api_router.get("/education/leaderboard")
async def get_education_leaderboard():
    """Get education leaderboard"""
    
    # Top learners by hours
    pipeline = [
        {"$sort": {"total_learning_hours": -1}},
        {"$limit": 20}
    ]
    
    top_learners = await db.education_profiles.aggregate(pipeline).to_list(20)
    
    leaderboard = []
    for i, learner in enumerate(top_learners):
        user = await db.users.find_one(
            {"user_id": learner["user_id"]},
            {"_id": 0, "user_id": 1, "name": 1, "picture": 1}
        )
        if user:
            leaderboard.append({
                "rank": i + 1,
                "user": user,
                "total_hours": learner.get("total_learning_hours", 0),
                "courses_completed": learner.get("courses_completed", 0),
                "current_level": learner.get("current_level", "seedling")
            })
    
    return {"leaderboard": leaderboard}


# ==================== PHASE 1: LOGIC PK SYSTEM (WITH BETTING) ====================

class LogicPKChallenge(BaseModel):
    challenge_id: str
    challenger_id: str
    opponent_id: str
    bet_amount: int
    status: str = "pending"  # pending, accepted, in_progress, completed, cancelled
    question: Optional[dict] = None
    challenger_answer: Optional[str] = None
    opponent_answer: Optional[str] = None
    winner_id: Optional[str] = None
    created_at: datetime

# Logic PK Questions Bank
LOGIC_PK_QUESTIONS = [
    {
        "id": "q1",
        "question": "Agar 5 machines 5 minutes mein 5 widgets banati hain, toh 100 machines 100 minutes mein kitne widgets banayengi?",
        "options": ["100", "500", "1000", "2000"],
        "correct": "2000",
        "difficulty": "medium",
        "category": "logic"
    },
    {
        "id": "q2",
        "question": "Ek doctor ne kaha: 'Jo ladka hai wo mera beta hai, lekin main uska baap nahi.' Doctor kaun hai?",
        "options": ["Chacha", "Dada", "Maa", "Bhai"],
        "correct": "Maa",
        "difficulty": "easy",
        "category": "riddle"
    },
    {
        "id": "q3",
        "question": "3 friends ne ₹300 ka pizza liya. Har ek ne ₹100 diye. Waiter ne ₹50 wapas kiye. ₹20 tip mein gaye, ₹30 wapas. Har ek ko ₹10 mila. 3×90=270+20=290. ₹10 kahan gaye?",
        "options": ["Waiter ke paas", "Kahin nahi gaye", "Pizza mein", "Yeh puzzle hai"],
        "correct": "Kahin nahi gaye",
        "difficulty": "hard",
        "category": "math_puzzle"
    },
    {
        "id": "q4",
        "question": "Sultan ke paas 10 gold coins hain. Wo har din apne coins double karta hai. 10 din mein uske paas 10,240 coins honge. 9 din mein kitne the?",
        "options": ["5,120", "2,560", "1,024", "512"],
        "correct": "5,120",
        "difficulty": "medium",
        "category": "math"
    },
    {
        "id": "q5",
        "question": "Ek ethical dilemma: Train 5 logon ki taraf ja rahi hai. Aap lever khench kar 1 aadmi ki taraf bhej sakte ho. Kya karoge?",
        "options": ["Lever kheenchna", "Kuch nahi karna", "Train rok dena", "Bhag jana"],
        "correct": "Lever kheenchna",
        "difficulty": "hard",
        "category": "ethics"
    }
]

@api_router.post("/logic-pk/create-challenge")
async def create_logic_pk_challenge(
    opponent_id: str,
    bet_amount: int,
    current_user: dict = Depends(get_current_user)
):
    """Create a Logic PK challenge with betting"""
    
    # Betting limits
    MIN_BET = 10
    MAX_BET = 1000
    MAX_BET_PERCENTAGE = 0.20  # 20% of total coins
    
    if bet_amount < MIN_BET:
        raise HTTPException(status_code=400, detail=f"Minimum bet is {MIN_BET} coins")
    
    if bet_amount > MAX_BET:
        raise HTTPException(status_code=400, detail=f"Maximum bet is {MAX_BET} coins")
    
    # Check user's wallet
    wallet = await db.wallets.find_one({"user_id": current_user.user_id})
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    
    user_coins = wallet.get("coins_balance", 0)
    
    # Check 20% limit
    if bet_amount > user_coins * MAX_BET_PERCENTAGE:
        raise HTTPException(status_code=400, detail=f"Bet cannot exceed 20% of your balance ({int(user_coins * MAX_BET_PERCENTAGE)} coins)")
    
    if user_coins < bet_amount:
        raise HTTPException(status_code=400, detail="Insufficient coins")
    
    # Check consecutive losses (anti-addiction)
    recent_losses = await db.logic_pk_history.count_documents({
        "user_id": current_user.user_id,
        "result": "loss",
        "created_at": {"$gte": datetime.now(timezone.utc) - timedelta(hours=24)}
    })
    
    if recent_losses >= 3:
        raise HTTPException(status_code=400, detail="24-hour betting cooldown active due to consecutive losses")
    
    # Create challenge
    challenge_id = str(uuid.uuid4())
    challenge = {
        "challenge_id": challenge_id,
        "challenger_id": current_user.user_id,
        "opponent_id": opponent_id,
        "bet_amount": bet_amount,
        "status": "pending",
        "question": random.choice(LOGIC_PK_QUESTIONS),
        "created_at": datetime.now(timezone.utc)
    }
    
    await db.logic_pk_challenges.insert_one(challenge)
    
    # Hold bet amount from challenger
    await db.wallets.update_one(
        {"user_id": current_user.user_id},
        {"$inc": {"coins_balance": -bet_amount, "held_balance": bet_amount}}
    )
    
    return {
        "challenge_id": challenge_id,
        "message": f"Challenge sent! Bet amount: {bet_amount} coins",
        "question": challenge["question"]["question"],
        "options": challenge["question"]["options"]
    }

@api_router.post("/logic-pk/accept-challenge/{challenge_id}")
async def accept_logic_pk_challenge(
    challenge_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Accept a Logic PK challenge"""
    challenge = await db.logic_pk_challenges.find_one({"challenge_id": challenge_id})
    
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    if challenge["opponent_id"] != current_user.user_id:
        raise HTTPException(status_code=403, detail="This challenge is not for you")
    
    if challenge["status"] != "pending":
        raise HTTPException(status_code=400, detail="Challenge already processed")
    
    # Check opponent's wallet
    wallet = await db.wallets.find_one({"user_id": current_user.user_id})
    if not wallet or wallet.get("coins_balance", 0) < challenge["bet_amount"]:
        raise HTTPException(status_code=400, detail="Insufficient coins to accept challenge")
    
    # Hold bet amount from opponent
    await db.wallets.update_one(
        {"user_id": current_user.user_id},
        {"$inc": {"coins_balance": -challenge["bet_amount"], "held_balance": challenge["bet_amount"]}}
    )
    
    await db.logic_pk_challenges.update_one(
        {"challenge_id": challenge_id},
        {"$set": {"status": "in_progress"}}
    )
    
    return {
        "message": "Challenge accepted!",
        "question": challenge["question"]["question"],
        "options": challenge["question"]["options"],
        "time_limit": 60  # seconds
    }

@api_router.post("/logic-pk/submit-answer/{challenge_id}")
async def submit_logic_pk_answer(
    challenge_id: str,
    answer: str,
    current_user: dict = Depends(get_current_user)
):
    """Submit answer for Logic PK challenge"""
    challenge = await db.logic_pk_challenges.find_one({"challenge_id": challenge_id})
    
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    is_challenger = challenge["challenger_id"] == current_user.user_id
    is_opponent = challenge["opponent_id"] == current_user.user_id
    
    if not is_challenger and not is_opponent:
        raise HTTPException(status_code=403, detail="You are not part of this challenge")
    
    # Store answer
    field = "challenger_answer" if is_challenger else "opponent_answer"
    await db.logic_pk_challenges.update_one(
        {"challenge_id": challenge_id},
        {"$set": {field: answer}}
    )
    
    # Check if both answered
    challenge = await db.logic_pk_challenges.find_one({"challenge_id": challenge_id})
    
    if challenge.get("challenger_answer") and challenge.get("opponent_answer"):
        # Determine winner
        correct_answer = challenge["question"]["correct"]
        challenger_correct = challenge["challenger_answer"] == correct_answer
        opponent_correct = challenge["opponent_answer"] == correct_answer
        
        winner_id = None
        if challenger_correct and not opponent_correct:
            winner_id = challenge["challenger_id"]
        elif opponent_correct and not challenger_correct:
            winner_id = challenge["opponent_id"]
        elif challenger_correct and opponent_correct:
            winner_id = "tie"
        
        # Distribute rewards
        total_pot = challenge["bet_amount"] * 2
        platform_fee = int(total_pot * 0.10)  # 10% platform fee
        winner_prize = total_pot - platform_fee
        consolation = 50  # Loser gets 50 coins consolation
        
        if winner_id and winner_id != "tie":
            loser_id = challenge["opponent_id"] if winner_id == challenge["challenger_id"] else challenge["challenger_id"]
            
            # Winner gets 90% of pot
            await db.wallets.update_one(
                {"user_id": winner_id},
                {"$inc": {"coins_balance": winner_prize, "held_balance": -challenge["bet_amount"]}}
            )
            
            # Loser gets consolation
            await db.wallets.update_one(
                {"user_id": loser_id},
                {"$inc": {"coins_balance": consolation, "held_balance": -challenge["bet_amount"]}}
            )
            
            # Record history
            await db.logic_pk_history.insert_one({
                "user_id": winner_id,
                "challenge_id": challenge_id,
                "result": "win",
                "coins_won": winner_prize,
                "created_at": datetime.now(timezone.utc)
            })
            await db.logic_pk_history.insert_one({
                "user_id": loser_id,
                "challenge_id": challenge_id,
                "result": "loss",
                "coins_lost": challenge["bet_amount"] - consolation,
                "created_at": datetime.now(timezone.utc)
            })
        else:
            # Tie - return bets
            await db.wallets.update_one(
                {"user_id": challenge["challenger_id"]},
                {"$inc": {"coins_balance": challenge["bet_amount"], "held_balance": -challenge["bet_amount"]}}
            )
            await db.wallets.update_one(
                {"user_id": challenge["opponent_id"]},
                {"$inc": {"coins_balance": challenge["bet_amount"], "held_balance": -challenge["bet_amount"]}}
            )
        
        await db.logic_pk_challenges.update_one(
            {"challenge_id": challenge_id},
            {"$set": {"status": "completed", "winner_id": winner_id}}
        )
        
        return {
            "status": "completed",
            "winner": winner_id,
            "correct_answer": correct_answer,
            "prize": winner_prize if winner_id and winner_id != "tie" else 0
        }
    
    return {"status": "waiting", "message": "Waiting for opponent's answer"}

@api_router.get("/logic-pk/challenges")
async def get_logic_pk_challenges(current_user: dict = Depends(get_current_user)):
    """Get pending challenges for user"""
    challenges = await db.logic_pk_challenges.find({
        "$or": [
            {"challenger_id": current_user.user_id},
            {"opponent_id": current_user.user_id}
        ],
        "status": {"$in": ["pending", "in_progress"]}
    }).to_list(20)
    
    for c in challenges:
        c["_id"] = str(c["_id"])
    
    return {"challenges": challenges}

# ==================== PHASE 1: DAILY MISSIONS ====================

DAILY_MISSIONS = [
    {
        "mission_id": "complete_video",
        "title": "Watch 1 Course Video",
        "description": "Complete watching any course video",
        "reward_coins": 50,
        "target": 1,
        "type": "video"
    },
    {
        "mission_id": "solve_questions",
        "title": "Solve 10 Questions",
        "description": "Answer 10 quiz questions",
        "reward_coins": 30,
        "target": 10,
        "type": "quiz"
    },
    {
        "mission_id": "help_friend",
        "title": "Help a Friend",
        "description": "Answer someone's doubt in community",
        "reward_coins": 20,
        "target": 1,
        "type": "social"
    },
    {
        "mission_id": "study_time",
        "title": "Study for 30 Minutes",
        "description": "Spend 30 minutes learning",
        "reward_coins": 40,
        "target": 30,
        "type": "time"
    },
    {
        "mission_id": "gyan_yuddh",
        "title": "Play Gyan Yuddh",
        "description": "Complete 1 mind game",
        "reward_coins": 25,
        "target": 1,
        "type": "game"
    }
]

@api_router.get("/daily-missions")
async def get_daily_missions(current_user: dict = Depends(get_current_user)):
    """Get user's daily missions with progress"""
    today = datetime.now(timezone.utc).date()
    
    # Get or create today's mission progress
    progress = await db.daily_mission_progress.find_one({
        "user_id": current_user.user_id,
        "date": str(today)
    })
    
    if not progress:
        progress = {
            "user_id": current_user.user_id,
            "date": str(today),
            "missions": {m["mission_id"]: {"progress": 0, "completed": False, "claimed": False} for m in DAILY_MISSIONS},
            "all_completed_bonus_claimed": False
        }
        await db.daily_mission_progress.insert_one(progress)
    
    missions_with_progress = []
    for mission in DAILY_MISSIONS:
        mp = progress["missions"].get(mission["mission_id"], {"progress": 0, "completed": False, "claimed": False})
        missions_with_progress.append({
            **mission,
            "progress": mp["progress"],
            "completed": mp["completed"],
            "claimed": mp["claimed"]
        })
    
    all_completed = all(m["completed"] for m in missions_with_progress)
    
    return {
        "date": str(today),
        "missions": missions_with_progress,
        "all_completed": all_completed,
        "all_completed_bonus": 100,
        "all_completed_bonus_claimed": progress.get("all_completed_bonus_claimed", False)
    }

@api_router.post("/daily-missions/update-progress")
async def update_mission_progress(
    mission_id: str,
    progress_amount: int = 1,
    current_user: dict = Depends(get_current_user)
):
    """Update progress for a daily mission"""
    today = datetime.now(timezone.utc).date()
    
    mission = next((m for m in DAILY_MISSIONS if m["mission_id"] == mission_id), None)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    
    progress = await db.daily_mission_progress.find_one({
        "user_id": current_user.user_id,
        "date": str(today)
    })
    
    if not progress:
        progress = {
            "user_id": current_user.user_id,
            "date": str(today),
            "missions": {m["mission_id"]: {"progress": 0, "completed": False, "claimed": False} for m in DAILY_MISSIONS},
            "all_completed_bonus_claimed": False
        }
        await db.daily_mission_progress.insert_one(progress)
    
    current_progress = progress["missions"].get(mission_id, {"progress": 0, "completed": False, "claimed": False})
    new_progress = min(current_progress["progress"] + progress_amount, mission["target"])
    completed = new_progress >= mission["target"]
    
    await db.daily_mission_progress.update_one(
        {"user_id": current_user.user_id, "date": str(today)},
        {"$set": {f"missions.{mission_id}.progress": new_progress, f"missions.{mission_id}.completed": completed}}
    )
    
    return {
        "mission_id": mission_id,
        "progress": new_progress,
        "target": mission["target"],
        "completed": completed
    }

@api_router.post("/daily-missions/claim/{mission_id}")
async def claim_mission_reward(
    mission_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Claim reward for completed mission"""
    today = datetime.now(timezone.utc).date()
    
    mission = next((m for m in DAILY_MISSIONS if m["mission_id"] == mission_id), None)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    
    progress = await db.daily_mission_progress.find_one({
        "user_id": current_user.user_id,
        "date": str(today)
    })
    
    if not progress:
        raise HTTPException(status_code=400, detail="No mission progress found")
    
    mp = progress["missions"].get(mission_id, {})
    
    if not mp.get("completed"):
        raise HTTPException(status_code=400, detail="Mission not completed")
    
    if mp.get("claimed"):
        raise HTTPException(status_code=400, detail="Reward already claimed")
    
    # Give reward
    await db.wallets.update_one(
        {"user_id": current_user.user_id},
        {"$inc": {"coins_balance": mission["reward_coins"]}}
    )
    
    await db.daily_mission_progress.update_one(
        {"user_id": current_user.user_id, "date": str(today)},
        {"$set": {f"missions.{mission_id}.claimed": True}}
    )
    
    return {
        "message": f"Claimed {mission['reward_coins']} coins!",
        "coins_earned": mission["reward_coins"]
    }

@api_router.post("/daily-missions/claim-all-bonus")
async def claim_all_missions_bonus(current_user: dict = Depends(get_current_user)):
    """Claim bonus for completing all daily missions"""
    today = datetime.now(timezone.utc).date()
    
    progress = await db.daily_mission_progress.find_one({
        "user_id": current_user.user_id,
        "date": str(today)
    })
    
    if not progress:
        raise HTTPException(status_code=400, detail="No mission progress found")
    
    all_completed = all(progress["missions"][m["mission_id"]]["completed"] for m in DAILY_MISSIONS)
    
    if not all_completed:
        raise HTTPException(status_code=400, detail="Not all missions completed")
    
    if progress.get("all_completed_bonus_claimed"):
        raise HTTPException(status_code=400, detail="Bonus already claimed")
    
    # Give 100 coins bonus
    await db.wallets.update_one(
        {"user_id": current_user.user_id},
        {"$inc": {"coins_balance": 100}}
    )
    
    await db.daily_mission_progress.update_one(
        {"user_id": current_user.user_id, "date": str(today)},
        {"$set": {"all_completed_bonus_claimed": True}}
    )
    
    return {
        "message": "Congratulations! All missions completed! +100 bonus coins!",
        "bonus_coins": 100
    }

# ==================== PHASE 1: 5-CATEGORY LEADERBOARD ====================

@api_router.get("/leaderboard/multi-category")
async def get_multi_category_leaderboard():
    """Get 5-category leaderboard with auto-rewards info"""
    
    # 1. Education Rank (Most learning hours)
    education_leaders = await db.education_profiles.find().sort("total_learning_hours", -1).limit(10).to_list(10)
    
    # 2. Logic Rank (Best Logic PK win rate)
    logic_pipeline = [
        {"$match": {"result": "win"}},
        {"$group": {"_id": "$user_id", "wins": {"$sum": 1}}},
        {"$sort": {"wins": -1}},
        {"$limit": 10}
    ]
    logic_leaders = await db.logic_pk_history.aggregate(logic_pipeline).to_list(10)
    
    # 3. Charity Rank (Most charity contributions)
    charity_pipeline = [
        {"$group": {"_id": "$user_id", "total_charity": {"$sum": "$charity_amount"}}},
        {"$sort": {"total_charity": -1}},
        {"$limit": 10}
    ]
    charity_leaders = await db.charity_contributions.aggregate(charity_pipeline).to_list(10)
    
    # 4. Unity Rank (Most helpful in community)
    unity_pipeline = [
        {"$group": {"_id": "$helper_id", "help_count": {"$sum": 1}}},
        {"$sort": {"help_count": -1}},
        {"$limit": 10}
    ]
    unity_leaders = await db.community_help.aggregate(unity_pipeline).to_list(10)
    
    # 5. Global Sultan Rank (Combined score)
    global_pipeline = [
        {"$group": {
            "_id": "$user_id",
            "total_score": {"$sum": "$score_points"}
        }},
        {"$sort": {"total_score": -1}},
        {"$limit": 10}
    ]
    global_leaders = await db.user_scores.aggregate(global_pipeline).to_list(10)
    
    # Get user details for each leaderboard
    async def enrich_leaderboard(leaders, id_field="_id", score_field="total"):
        enriched = []
        for i, leader in enumerate(leaders):
            user = await db.users.find_one({"user_id": leader[id_field]})
            if user:
                # Get charity wallet balance
                charity_wallet = await db.charity_wallets.find_one({"user_id": leader[id_field]})
                enriched.append({
                    "rank": i + 1,
                    "user_id": leader[id_field],
                    "name": user.get("name", "Unknown"),
                    "score": leader.get(score_field, leader.get("wins", leader.get("total_charity", leader.get("help_count", 0)))),
                    "charity_wallet": charity_wallet.get("balance", 0) if charity_wallet else 0
                })
        return enriched
    
    return {
        "education": await enrich_leaderboard(education_leaders, "user_id", "total_learning_hours"),
        "logic": await enrich_leaderboard(logic_leaders, "_id", "wins"),
        "charity": await enrich_leaderboard(charity_leaders, "_id", "total_charity"),
        "unity": await enrich_leaderboard(unity_leaders, "_id", "help_count"),
        "global_sultan": await enrich_leaderboard(global_leaders, "_id", "total_score"),
        "rewards": {
            "daily": {"top1": 500, "top2": 300, "top3": 200},
            "weekly": {"top1": 5000, "top2": 3000, "top3": 2000, "top4_10": 1000},
            "monthly": {"top1": 5000, "top2": 3000, "top3": 2000, "top4_10": 500}
        },
        "next_reset": {
            "daily": "12:00 AM",
            "weekly": "Monday 12:00 AM",
            "monthly": "1st of month 12:00 AM"
        }
    }

# ==================== CHARITY 10B TRIGGER ====================

PLATFORM_CONFIG = {
    "total_revenue": 0,  # Will be fetched from DB
    "charity_threshold": 10_000_000_000,  # 10 Billion
    "current_charity_rate": 0.02,  # 2%
    "post_threshold_charity_rate": 0.35  # 35%
}

@api_router.get("/platform/charity-config")
async def get_charity_config():
    """Get current charity configuration based on revenue"""
    platform_stats = await db.platform_stats.find_one({"stat_id": "main"})
    
    if not platform_stats:
        platform_stats = {
            "stat_id": "main",
            "total_revenue": 0,
            "total_charity_collected": 0,
            "created_at": datetime.now(timezone.utc)
        }
        await db.platform_stats.insert_one(platform_stats)
    
    total_revenue = platform_stats.get("total_revenue", 0)
    threshold_reached = total_revenue >= PLATFORM_CONFIG["charity_threshold"]
    
    current_rate = PLATFORM_CONFIG["post_threshold_charity_rate"] if threshold_reached else PLATFORM_CONFIG["current_charity_rate"]
    
    return {
        "total_revenue": total_revenue,
        "charity_threshold": PLATFORM_CONFIG["charity_threshold"],
        "threshold_reached": threshold_reached,
        "current_charity_rate": current_rate,
        "charity_rate_display": f"{int(current_rate * 100)}%",
        "total_charity_collected": platform_stats.get("total_charity_collected", 0),
        "message": "35% Charity Mode Active! 🎉" if threshold_reached else f"Currently at {int(current_rate * 100)}% charity rate"
    }


# ==================== STAR TO COINS EXCHANGE SYSTEM ====================

# Exchange Configuration
STAR_EXCHANGE_CONFIG = {
    "rate": 0.92,  # 1 Star = 0.92 Coins
    "fee_percentage": 8,  # 8% platform fee
    "minimum_stars": 1000,
    "maximum_stars": None,  # No maximum
    "daily_limit": 1000000,  # 10 Lakh stars per day
    "monthly_limit": 10000000  # 1 Crore stars per month
}

class StarExchangeRequest(BaseModel):
    star_amount: int

@api_router.get("/star-exchange/config")
async def get_star_exchange_config():
    """Get Star to Coins exchange configuration"""
    return {
        "exchange_rate": STAR_EXCHANGE_CONFIG["rate"],
        "fee_percentage": STAR_EXCHANGE_CONFIG["fee_percentage"],
        "minimum_stars": STAR_EXCHANGE_CONFIG["minimum_stars"],
        "daily_limit": STAR_EXCHANGE_CONFIG["daily_limit"],
        "monthly_limit": STAR_EXCHANGE_CONFIG["monthly_limit"],
        "examples": [
            {"stars": 1000, "coins": 920},
            {"stars": 10000, "coins": 9200},
            {"stars": 50000, "coins": 46000},
            {"stars": 100000, "coins": 92000},
            {"stars": 1000000, "coins": 920000}
        ]
    }

@api_router.post("/star-exchange/calculate")
async def calculate_star_exchange(request: StarExchangeRequest):
    """Calculate exchange without executing"""
    star_amount = request.star_amount
    
    if star_amount < STAR_EXCHANGE_CONFIG["minimum_stars"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Minimum {STAR_EXCHANGE_CONFIG['minimum_stars']} stars required"
        )
    
    gross_coins = int(star_amount * STAR_EXCHANGE_CONFIG["rate"])
    fee_coins = int(star_amount * STAR_EXCHANGE_CONFIG["fee_percentage"] / 100)
    
    return {
        "stars_to_exchange": star_amount,
        "exchange_rate": STAR_EXCHANGE_CONFIG["rate"],
        "gross_coins": gross_coins,
        "fee_coins": fee_coins,
        "net_coins": gross_coins,
        "fee_percentage": STAR_EXCHANGE_CONFIG["fee_percentage"]
    }

@api_router.post("/star-exchange/execute")
async def execute_star_exchange(
    request: StarExchangeRequest,
    current_user: dict = Depends(get_current_user)
):
    """Execute Star to Coins exchange"""
    star_amount = request.star_amount
    
    # Validate minimum
    if star_amount < STAR_EXCHANGE_CONFIG["minimum_stars"]:
        raise HTTPException(
            status_code=400,
            detail=f"Minimum {STAR_EXCHANGE_CONFIG['minimum_stars']} stars required"
        )
    
    # Get user's wallet
    wallet = await db.wallets.find_one({"user_id": current_user.user_id})
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    
    current_stars = wallet.get("stars_balance", 0)
    
    # Check sufficient stars
    if current_stars < star_amount:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient stars. You have {current_stars} stars"
        )
    
    # Check daily limit
    today = datetime.now(timezone.utc).date()
    today_exchanges = await db.star_exchanges.aggregate([
        {
            "$match": {
                "user_id": current_user.user_id,
                "created_at": {"$gte": datetime.combine(today, datetime.min.time())}
            }
        },
        {"$group": {"_id": None, "total": {"$sum": "$stars_exchanged"}}}
    ]).to_list(1)
    
    today_total = today_exchanges[0]["total"] if today_exchanges else 0
    
    if today_total + star_amount > STAR_EXCHANGE_CONFIG["daily_limit"]:
        raise HTTPException(
            status_code=400,
            detail=f"Daily limit exceeded. You can exchange {STAR_EXCHANGE_CONFIG['daily_limit'] - today_total} more stars today"
        )
    
    # Calculate exchange
    coins_received = int(star_amount * STAR_EXCHANGE_CONFIG["rate"])
    fee_coins = int(star_amount * STAR_EXCHANGE_CONFIG["fee_percentage"] / 100)
    
    # Execute exchange - Deduct stars, Add coins
    await db.wallets.update_one(
        {"user_id": current_user.user_id},
        {
            "$inc": {
                "stars_balance": -star_amount,
                "coins_balance": coins_received
            }
        }
    )
    
    # Add fee to platform treasury
    await db.platform_stats.update_one(
        {"stat_id": "main"},
        {
            "$inc": {
                "exchange_fees_collected": fee_coins,
                "total_stars_exchanged": star_amount,
                "total_coins_issued": coins_received
            }
        },
        upsert=True
    )
    
    # Log exchange transaction
    exchange_record = {
        "user_id": current_user.user_id,
        "stars_exchanged": star_amount,
        "coins_received": coins_received,
        "fee_coins": fee_coins,
        "exchange_rate": STAR_EXCHANGE_CONFIG["rate"],
        "created_at": datetime.now(timezone.utc)
    }
    await db.star_exchanges.insert_one(exchange_record)
    
    # Create transaction record
    await db.wallet_transactions.insert_one({
        "user_id": current_user.user_id,
        "type": "star_to_coin_exchange",
        "stars_deducted": star_amount,
        "coins_added": coins_received,
        "fee": fee_coins,
        "description": f"Exchanged {star_amount:,} Stars → {coins_received:,} Coins",
        "created_at": datetime.now(timezone.utc)
    })
    
    # Get updated balances
    updated_wallet = await db.wallets.find_one({"user_id": current_user.user_id})
    
    return {
        "success": True,
        "message": f"Successfully exchanged {star_amount:,} Stars to {coins_received:,} Coins!",
        "stars_exchanged": star_amount,
        "coins_received": coins_received,
        "fee_coins": fee_coins,
        "new_star_balance": updated_wallet.get("stars_balance", 0),
        "new_coin_balance": updated_wallet.get("coins_balance", 0)
    }

@api_router.get("/star-exchange/history")
async def get_star_exchange_history(
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """Get user's star exchange history"""
    exchanges = await db.star_exchanges.find(
        {"user_id": current_user.user_id}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    for e in exchanges:
        e["_id"] = str(e["_id"])
        e["created_at"] = e["created_at"].isoformat() if e.get("created_at") else None
    
    # Get totals
    totals = await db.star_exchanges.aggregate([
        {"$match": {"user_id": current_user.user_id}},
        {"$group": {
            "_id": None,
            "total_stars_exchanged": {"$sum": "$stars_exchanged"},
            "total_coins_received": {"$sum": "$coins_received"},
            "total_fees": {"$sum": "$fee_coins"},
            "count": {"$sum": 1}
        }}
    ]).to_list(1)
    
    total_stats = totals[0] if totals else {
        "total_stars_exchanged": 0,
        "total_coins_received": 0,
        "total_fees": 0,
        "count": 0
    }
    
    return {
        "exchanges": exchanges,
        "totals": {
            "total_stars_exchanged": total_stats.get("total_stars_exchanged", 0),
            "total_coins_received": total_stats.get("total_coins_received", 0),
            "total_fees_paid": total_stats.get("total_fees", 0),
            "exchange_count": total_stats.get("count", 0)
        }
    }

@api_router.get("/star-exchange/daily-stats")
async def get_daily_exchange_stats(current_user: dict = Depends(get_current_user)):
    """Get today's exchange statistics for user"""
    today = datetime.now(timezone.utc).date()
    
    today_stats = await db.star_exchanges.aggregate([
        {
            "$match": {
                "user_id": current_user.user_id,
                "created_at": {"$gte": datetime.combine(today, datetime.min.time())}
            }
        },
        {"$group": {
            "_id": None,
            "today_stars_exchanged": {"$sum": "$stars_exchanged"},
            "today_coins_received": {"$sum": "$coins_received"},
            "exchange_count": {"$sum": 1}
        }}
    ]).to_list(1)
    
    stats = today_stats[0] if today_stats else {
        "today_stars_exchanged": 0,
        "today_coins_received": 0,
        "exchange_count": 0
    }
    
    remaining_daily_limit = STAR_EXCHANGE_CONFIG["daily_limit"] - stats.get("today_stars_exchanged", 0)
    
    return {
        "today_stars_exchanged": stats.get("today_stars_exchanged", 0),
        "today_coins_received": stats.get("today_coins_received", 0),
        "exchange_count": stats.get("exchange_count", 0),
        "daily_limit": STAR_EXCHANGE_CONFIG["daily_limit"],
        "remaining_daily_limit": max(0, remaining_daily_limit),
        "can_exchange_more": remaining_daily_limit > 0
    }





# ==================== HEALTH CHECK ====================

@api_router.get("/")
async def root():
    return {"message": "VIP Wallet API", "status": "running"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

# ==================== CROWN SYSTEM APIs ====================

@api_router.get("/crowns/types")
async def get_crown_types():
    """Get all available crown types and their requirements"""
    crown_data = []
    for crown_type, requirements in CROWN_REQUIREMENTS.items():
        crown_data.append({
            "type": crown_type.value,
            "name": crown_type.value.replace("_", " ").title(),
            "requirements": requirements,
            "icon": get_crown_icon(crown_type),
            "color": get_crown_color(crown_type)
        })
    return {"crowns": crown_data}

def get_crown_icon(crown_type: CrownType) -> str:
    icons = {
        CrownType.BRONZE: "🥉",
        CrownType.SILVER: "🥈",
        CrownType.GOLD: "🥇",
        CrownType.GIFTER: "🎁",
        CrownType.QUEEN: "👑",
        CrownType.VIDEO_CREATOR: "🎬"
    }
    return icons.get(crown_type, "⭐")

def get_crown_color(crown_type: CrownType) -> str:
    colors = {
        CrownType.BRONZE: "#CD7F32",
        CrownType.SILVER: "#C0C0C0",
        CrownType.GOLD: "#FFD700",
        CrownType.GIFTER: "#E91E63",
        CrownType.QUEEN: "#9C27B0",
        CrownType.VIDEO_CREATOR: "#2196F3"
    }
    return colors.get(crown_type, "#808080")

@api_router.get("/crowns/my-crowns")
async def get_my_crowns(user_id: str = Depends(get_current_user)):
    """Get all crowns earned by the current user"""
    crowns = await db.user_crowns.find({"user_id": user_id, "is_active": True}).to_list(100)
    return {
        "crowns": [{
            "crown_id": c["crown_id"],
            "crown_type": c["crown_type"],
            "icon": get_crown_icon(CrownType(c["crown_type"])),
            "color": get_crown_color(CrownType(c["crown_type"])),
            "earned_at": c["earned_at"],
            "expires_at": c.get("expires_at")
        } for c in crowns],
        "total_crowns": len(crowns)
    }

@api_router.post("/crowns/check-eligibility")
async def check_crown_eligibility(user_id: str = Depends(get_current_user)):
    """Check if user is eligible for any new crowns"""
    # Get user stats
    user_stats = await db.user_stats.find_one({"user_id": user_id}) or {}
    total_likes = user_stats.get("total_likes_received", 0)
    total_videos = user_stats.get("total_videos", 0)
    total_views = user_stats.get("total_views", 0)
    total_gifts_sent = user_stats.get("total_gifts_sent", 0)
    
    eligible_crowns = []
    
    # Check each crown type
    if total_likes >= 100 and total_videos >= 5:
        eligible_crowns.append(CrownType.BRONZE)
    if total_likes >= 1000 and total_videos >= 20:
        eligible_crowns.append(CrownType.SILVER)
    if total_likes >= 10000 and total_videos >= 50:
        eligible_crowns.append(CrownType.GOLD)
    if total_gifts_sent >= 10000:
        eligible_crowns.append(CrownType.GIFTER)
    if total_videos >= 100 and total_views >= 100000:
        eligible_crowns.append(CrownType.VIDEO_CREATOR)
    
    # Check which crowns user already has
    existing_crowns = await db.user_crowns.find(
        {"user_id": user_id, "is_active": True}
    ).to_list(100)
    existing_types = {c["crown_type"] for c in existing_crowns}
    
    # Filter out already earned crowns
    new_eligible = [c for c in eligible_crowns if c.value not in existing_types]
    
    return {
        "eligible_crowns": [c.value for c in new_eligible],
        "user_stats": {
            "total_likes": total_likes,
            "total_videos": total_videos,
            "total_views": total_views,
            "total_gifts_sent": total_gifts_sent
        }
    }

@api_router.post("/crowns/claim/{crown_type}")
async def claim_crown(crown_type: str, user_id: str = Depends(get_current_user)):
    """Claim an eligible crown"""
    # Verify eligibility
    eligibility = await check_crown_eligibility(user_id)
    if crown_type not in eligibility["eligible_crowns"]:
        raise HTTPException(status_code=400, detail="Not eligible for this crown")
    
    # Create crown
    crown_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    
    await db.user_crowns.insert_one({
        "crown_id": crown_id,
        "user_id": user_id,
        "crown_type": crown_type,
        "earned_at": now,
        "expires_at": None,  # Permanent
        "is_active": True
    })
    
    # Send notification
    await create_notification(
        user_id=user_id,
        title=f"🎉 New Crown Earned!",
        message=f"Congratulations! You've earned the {crown_type.replace('_', ' ').title()} Crown!",
        notification_type="crown_earned"
    )
    
    return {
        "success": True,
        "crown_id": crown_id,
        "crown_type": crown_type,
        "icon": get_crown_icon(CrownType(crown_type)),
        "message": f"Successfully claimed {crown_type.replace('_', ' ').title()} Crown!"
    }

# ==================== VIDEO LEADERBOARD APIs ====================

@api_router.get("/leaderboard/video/monthly")
async def get_monthly_video_leaderboard(
    month: Optional[str] = None  # Format: "2025-01"
):
    """Get monthly video leaderboard with prizes"""
    if not month:
        month = datetime.now(timezone.utc).strftime("%Y-%m")
    
    # Aggregate top videos for the month
    pipeline = [
        {"$match": {"month_year": month}},
        {"$group": {
            "_id": "$user_id",
            "total_likes": {"$sum": "$likes_count"},
            "total_views": {"$sum": "$views_count"},
            "video_count": {"$sum": 1}
        }},
        {"$sort": {"total_likes": -1}},
        {"$limit": 150}  # Top 150 models
    ]
    
    results = await db.videos.aggregate(pipeline).to_list(150)
    
    leaderboard = []
    for i, entry in enumerate(results, 1):
        user = await db.users.find_one({"user_id": entry["_id"]})
        user_crowns = await db.user_crowns.find(
            {"user_id": entry["_id"], "is_active": True}
        ).to_list(10)
        
        # Determine prize for top 10
        prize_info = MONTHLY_PRIZES.get(i, {"prize": None, "coins": 0})
        
        # Determine crown based on rank
        crown = None
        if i == 1:
            crown = CrownType.GOLD
        elif i <= 10:
            crown = CrownType.SILVER
        elif i <= 50:
            crown = CrownType.BRONZE
        
        leaderboard.append({
            "rank": i,
            "user_id": entry["_id"],
            "user_name": user["name"] if user else "Unknown",
            "user_picture": user.get("picture") if user else None,
            "total_likes": entry["total_likes"],
            "total_views": entry["total_views"],
            "video_count": entry["video_count"],
            "prize": prize_info["prize"],
            "prize_coins": prize_info["coins"],
            "crown": crown.value if crown else None,
            "crown_icon": get_crown_icon(crown) if crown else None,
            "existing_crowns": [c["crown_type"] for c in user_crowns]
        })
    
    return {
        "month": month,
        "leaderboard": leaderboard,
        "total_participants": len(leaderboard),
        "prizes": MONTHLY_PRIZES,
        "last_updated": datetime.now(timezone.utc).isoformat()
    }

@api_router.get("/leaderboard/top-150")
async def get_top_150_models():
    """Get top 150 models across all categories"""
    # Aggregate user scores
    pipeline = [
        {"$group": {
            "_id": "$user_id",
            "total_likes": {"$sum": "$likes_count"},
            "total_views": {"$sum": "$views_count"},
            "total_gifts": {"$sum": "$gifts_received"},
            "video_count": {"$sum": 1}
        }},
        {"$addFields": {
            "score": {
                "$add": [
                    {"$multiply": ["$total_likes", 1]},
                    {"$multiply": ["$total_views", 0.1]},
                    {"$multiply": ["$total_gifts", 10]}
                ]
            }
        }},
        {"$sort": {"score": -1}},
        {"$limit": 150}
    ]
    
    results = await db.videos.aggregate(pipeline).to_list(150)
    
    top_models = []
    for i, entry in enumerate(results, 1):
        user = await db.users.find_one({"user_id": entry["_id"]})
        top_models.append({
            "rank": i,
            "user_id": entry["_id"],
            "user_name": user["name"] if user else "Unknown",
            "user_picture": user.get("picture") if user else None,
            "score": int(entry["score"]),
            "total_likes": entry["total_likes"],
            "total_views": entry["total_views"],
            "total_gifts": entry["total_gifts"],
            "video_count": entry["video_count"],
            "tier": "gold" if i <= 10 else "silver" if i <= 50 else "bronze"
        })
    
    return {
        "top_models": top_models,
        "tiers": {
            "gold": {"range": "1-10", "count": min(10, len(top_models))},
            "silver": {"range": "11-50", "count": max(0, min(40, len(top_models) - 10))},
            "bronze": {"range": "51-150", "count": max(0, len(top_models) - 50)}
        }
    }

# ==================== MHA EVENT APIs ====================

@api_router.get("/events/mha/active")
async def get_active_mha_events():
    """Get all active MHA events"""
    now = datetime.now(timezone.utc)
    events = await db.mha_events.find({
        "is_active": True,
        "start_date": {"$lte": now},
        "end_date": {"$gte": now}
    }).to_list(100)
    
    return {
        "events": [{
            "event_id": e["event_id"],
            "event_name": e["event_name"],
            "event_type": e["event_type"],
            "start_date": e["start_date"],
            "end_date": e["end_date"],
            "prize_pool": e["prize_pool"],
            "days_remaining": (e["end_date"] - now).days
        } for e in events]
    }

@api_router.post("/events/mha/join/{event_id}")
async def join_mha_event(event_id: str, user_id: str = Depends(get_current_user)):
    """Join an MHA event"""
    # Check event exists and is active
    event = await db.mha_events.find_one({"event_id": event_id, "is_active": True})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found or not active")
    
    # Check if already joined
    existing = await db.mha_participants.find_one({
        "event_id": event_id,
        "user_id": user_id
    })
    if existing:
        return {"success": True, "message": "Already joined this event", "participant_id": existing["participant_id"]}
    
    # Join event
    participant_id = str(uuid.uuid4())
    await db.mha_participants.insert_one({
        "participant_id": participant_id,
        "event_id": event_id,
        "user_id": user_id,
        "total_score": 0,
        "rank": None,
        "crown_earned": None,
        "prize_won": None,
        "joined_at": datetime.now(timezone.utc)
    })
    
    return {
        "success": True,
        "message": f"Successfully joined {event['event_name']}!",
        "participant_id": participant_id
    }

@api_router.get("/events/mha/{event_id}/leaderboard")
async def get_mha_event_leaderboard(event_id: str):
    """Get leaderboard for specific MHA event"""
    event = await db.mha_events.find_one({"event_id": event_id})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    participants = await db.mha_participants.find(
        {"event_id": event_id}
    ).sort("total_score", -1).to_list(150)
    
    leaderboard = []
    for i, p in enumerate(participants, 1):
        user = await db.users.find_one({"user_id": p["user_id"]})
        leaderboard.append({
            "rank": i,
            "user_id": p["user_id"],
            "user_name": user["name"] if user else "Unknown",
            "user_picture": user.get("picture") if user else None,
            "total_score": p["total_score"],
            "crown_earned": p.get("crown_earned"),
            "prize_won": p.get("prize_won")
        })
    
    return {
        "event": {
            "event_id": event["event_id"],
            "event_name": event["event_name"],
            "prize_pool": event["prize_pool"]
        },
        "leaderboard": leaderboard,
        "total_participants": len(leaderboard)
    }

# ==================== CHARITY STATUS API ====================

@api_router.get("/charity/status")
async def get_charity_status():
    """Get current charity contribution status and rates"""
    # Get company revenue (mock for now)
    company_stats = await db.company_stats.find_one({"type": "revenue"}) or {
        "total_revenue": 0,
        "total_charity_contributed": 0
    }
    
    total_revenue = company_stats.get("total_revenue", 0)
    
    # Determine current phase
    if total_revenue >= CHARITY_PHASE_1_THRESHOLD:
        current_charity_rate = CHARITY_PHASE_2_RATE
        phase = "Phase 2 (45% Charity)"
    else:
        current_charity_rate = CHARITY_PHASE_1_RATE
        phase = "Phase 1 (2% Charity)"
    
    return {
        "current_phase": phase,
        "charity_rate": current_charity_rate * 100,
        "security_fund_rate": SECURITY_FUND_RATE * 100,
        "total_charity_contributed": company_stats.get("total_charity_contributed", 0),
        "revenue_to_next_phase": max(0, CHARITY_PHASE_1_THRESHOLD - total_revenue),
        "phase_threshold": CHARITY_PHASE_1_THRESHOLD,
        "message": "45% of company income goes to charity after ₹10 Billion revenue milestone"
    }

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
