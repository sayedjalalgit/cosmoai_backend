from abc import ABC, abstractmethod
from typing import Optional

class BasePaymentProvider(ABC):
    """
    Abstract base class for payment providers.
    To add a new provider (PayPal, bKash etc):
    1. Create new file in payments/providers/
    2. Inherit from this class
    3. Implement all methods
    4. Register in payments/providers/__init__.py
    That is all! Never touch core AI code.
    """

    @abstractmethod
    def create_checkout_session(
        self,
        user_id: int,
        user_email: str,
        plan: str,
        success_url: str,
        cancel_url: str,
    ) -> dict:
        """Create payment checkout session"""
        pass

    @abstractmethod
    def cancel_subscription(
        self,
        subscription_id: str
    ) -> bool:
        """Cancel an active subscription"""
        pass

    @abstractmethod
    def get_subscription_status(
        self,
        subscription_id: str
    ) -> dict:
        """Get current subscription status"""
        pass

    @abstractmethod
    def handle_webhook(
        self,
        payload: bytes,
        signature: str
    ) -> dict:
        """Handle webhook from payment provider"""
        pass

    def get_plan_price(self, plan: str, currency: str = "usd") -> float:
        prices = {
            "pro": {"usd": 9.99, "bdt": 1100},
            "business": {"usd": 29.99, "bdt": 3300},
            "enterprise": {"usd": 99.99, "bdt": 11000},
        }
        return prices.get(plan, {}).get(currency, 0)