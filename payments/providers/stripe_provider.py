import stripe
import uuid
from payments.providers.base import BasePaymentProvider
from payments.config import payment_settings

class StripeProvider(BasePaymentProvider):
    def __init__(self):
        stripe.api_key = payment_settings.STRIPE_SECRET_KEY

        self.price_ids = {
            "pro": "price_1T6YNBRAhz6ttP9jvAo2GJO6",      # Replace with real Stripe price IDs
            "business": "price_1T6YNfRAhz6ttP9jhrWbIy6r",
            "enterprise": "price_1T6YO7RAhz6ttP9jzLLfaXQY",
        }

    def create_checkout_session(
        self,
        user_id: int,
        user_email: str,
        plan: str,
        success_url: str,
        cancel_url: str,
    ) -> dict:
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                mode="subscription",
                customer_email=user_email,
                line_items=[{
                    "price": self.price_ids[plan],
                    "quantity": 1,
                }],
                success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
                cancel_url=cancel_url,
                metadata={
                    "user_id": str(user_id),
                    "plan": plan,
                }
            )
            return {
                "checkout_url": session.url,
                "session_id": session.id,
                "provider": "stripe"
            }
        except Exception as e:
            raise Exception(f"Stripe checkout failed: {e}")

    def cancel_subscription(self, subscription_id: str) -> bool:
        try:
            stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True
            )
            return True
        except Exception:
            return False

    def get_subscription_status(self, subscription_id: str) -> dict:
        try:
            sub = stripe.Subscription.retrieve(subscription_id)
            return {
                "status": sub.status,
                "current_period_end": sub.current_period_end,
                "plan": sub.metadata.get("plan", "pro")
            }
        except Exception:
            return {"status": "unknown"}

    def handle_webhook(self, payload: bytes, signature: str) -> dict:
        try:
            event = stripe.Webhook.construct_event(
                payload,
                signature,
                payment_settings.STRIPE_WEBHOOK_SECRET
            )
            return {
                "type": event.type,
                "data": event.data.object,
                "provider": "stripe"
            }
        except Exception as e:
            raise Exception(f"Webhook error: {e}")