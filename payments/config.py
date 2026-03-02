from pydantic_settings import BaseSettings
from typing import Optional

class PaymentSettings(BaseSettings):
    # Stripe (USA/Global)
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_PUBLISHABLE_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None

    # SSLCommerz (Bangladesh)
    SSLCOMMERZ_STORE_ID: Optional[str] = None
    SSLCOMMERZ_STORE_PASSWORD: Optional[str] = None
    SSLCOMMERZ_SANDBOX: bool = True

    # bKash (Bangladesh Mobile)
    BKASH_APP_KEY: Optional[str] = None
    BKASH_APP_SECRET: Optional[str] = None
    BKASH_SANDBOX: bool = True

    # Plans config
    PLAN_FREE_MESSAGES: int = 20
    PLAN_PRO_MESSAGES: int = 999999
    PLAN_BUSINESS_MESSAGES: int = 999999

    # URLs
    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_URL: str = "http://localhost:8000"

    # Active provider
    PAYMENT_PROVIDER: str = "stripe"  # stripe, sslcommerz, bkash

    class Config:
        env_file = ".env"
        extra = "allow"

payment_settings = PaymentSettings()