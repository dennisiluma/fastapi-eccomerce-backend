from email.message import EmailMessage
from pathlib import Path
from typing import Any

import aiosmtplib
from jinja2 import Environment, FileSystemLoader

from app.core.config import settings
from app.core.exceptions import ApiException
from app.models.order import Order

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"
jinja_env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))


# ==========================================
# CENTRAL HELPER FUNCTION
# ==========================================


async def _send_email(
    to_email: str,
    subject: str,
    template_name: str,
    context: dict[str, Any],
    fallback_text: str | None = None,
    raise_on_error: bool = False,
) -> None:
    """Core helper that handles Jinja rendering, Email construction, and SMTP delivery."""
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.MAIL_FROM
    message["To"] = to_email

    # 1. Render Template
    try:
        template = jinja_env.get_template(template_name)
        html_content = template.render(**context)
        message.add_alternative(html_content, subtype="html")
    except Exception as e:
        print(f"⚠️ Template Error [{template_name}]: {e}")
        if fallback_text:
            message.set_content(fallback_text)
        else:
            if raise_on_error:
                raise ApiException(
                    message=f"Template rendering failed: {e}", status_code=500
                )
            return

    # 2. Send Email via SMTP
    try:
        await aiosmtplib.send(
            message,
            hostname=settings.MAIL_HOST,
            port=int(settings.MAIL_PORT),
            username=settings.MAIL_USER,
            password=settings.MAIL_PASS,
            start_tls=True,
        )
        print(f"✅ Email [{subject}] successfully sent to {to_email}")

    except Exception as e:
        print(f"❌ SMTP Error sending [{subject}] to {to_email}: {e}")
        if raise_on_error:
            raise ApiException(message=f"Error sending email: {e}", status_code=500)


# ==========================================
# PUBLIC EMAIL FUNCTIONS
# ==========================================
async def send_welcome_email(email: str, name: str) -> None:
    await _send_email(
        to_email=email,
        subject="Welcome to ShopEase",
        template_name="welcome.html",
        context={"name": name, "frontendUrl": settings.FRONTEND_URL},
        fallback_text=f"Hello {name}, welcome to ShopEase",
        raise_on_error=True,
    )


async def send_reset_password_email(
    email: str, name: str, code: str, reset_url: str
) -> None:
    await _send_email(
        to_email=email,
        subject="Password Reset Request - Action Required",
        template_name="reset-password.html",
        context={"name": name, "code": code, "reset_url": reset_url},
        fallback_text=f"Hello {name}, your reset code is: {code}. Link: {reset_url}",
        raise_on_error=True,
    )


async def send_order_status_update_email(email: str, name: str, order: Order) -> None:
    await _send_email(
        to_email=email,
        subject=f"Update: Order #{order.id} is now {order.status.value}",
        template_name="order-status.html",
        context={
            "name": name,
            "order_id": order.id,
            "status": order.status.value.upper(),
            "address": order.shipping_address,
            "total_price": order.total_price,
            "items": order.items,
        },
    )


async def send_order_confirmation_email(email: str, name: str, order: Order) -> None:
    await _send_email(
        to_email=email,
        subject=f"Confirmation: Order #{order.id}",
        template_name="order_confirmation.html",
        context={
            "name": name,
            "order_id": order.id,
            "total": order.total_price,
            "address": order.shipping_address,
        },
    )


async def notify_delivery_team_of_order(order: Order, customer_name: str) -> None:
    payment_status = order.payment.status if order.payment else "Unknown"
    order_date = order.created_at.strftime("%Y-%m-%d %H:%M") if order.created_at else ""

    await _send_email(
        to_email=settings.DELIVERY_PERSON_EMAIL,
        subject=f"🚨 New Order Received: #{order.id}",
        template_name="delivery_person_order_notification.html",
        context={
            "customer_name": customer_name,
            "order_id": order.id,
            "order_status": order.status,
            "payment_status": payment_status,
            "total": order.total_price,
            "address": order.shipping_address,
            "items": order.items,
            "order_date": order_date,
        },
    )


async def send_payment_notification(
    email: str,
    name: str,
    order_id: int,
    status: str,
    amount: str | None = None,
    error: str | None = None,
) -> None:
    is_success = status == "success"
    template_name = "payment-success.html" if is_success else "payment-failed.html"
    subject = (
        f"Payment Successful - Order #{order_id}"
        if is_success
        else f"Payment Failed - Order #{order_id}"
    )

    await _send_email(
        to_email=email,
        subject=subject,
        template_name=template_name,
        context={
            "name": name,
            "order_id": order_id,
            "amount": amount,
            "currency": "USD",
            "error_message": error,
        },
    )
