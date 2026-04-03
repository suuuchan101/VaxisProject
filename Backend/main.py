import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import stripe
from supabase import create_client, Client

# .env ファイルの読み込み
load_dotenv()

app = FastAPI(
    title="VAXIS Unified API",
    description="VAXIS XR Pipeline のバックエンドコア。クレジット管理、Stripe 決済、Supabase 認証を統合します。",
    version="1.0.0"
)

# CORS の設定（Blender/Unity からのアクセスを許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Stripe 設定
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# Supabase 設定
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

class HealthResponse(BaseModel):
    status: str
    version: str

@app.get("/", response_model=HealthResponse)
async def root():
    """サーバーの稼働状態を確認するルートエンドポイント"""
    return {"status": "VAXIS System Online", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """詳細なヘルスチェック"""
    return {
        "api": "online",
        "database": "connected" if supabase else "waiting_configuration",
        "payments": "initialized" if stripe.api_key else "waiting_configuration"
    }

# 著作者: VAXIS Development Team
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
