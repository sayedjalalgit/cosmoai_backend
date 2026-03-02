from payments.config import payment_settings

def get_payment_provider():
    provider = payment_settings.PAYMENT_PROVIDER

    if provider == "stripe":
        from payments.providers.stripe_provider import StripeProvider
        return StripeProvider()

    elif provider == "sslcommerz":
        from payments.providers.sslcommerz_provider import SSLCommerzProvider
        return SSLCommerzProvider()

    elif provider == "bkash":
        from payments.providers.bkash_provider import BkashProvider
        return BkashProvider()

    else:
        raise Exception(f"Unknown payment provider: {provider}")