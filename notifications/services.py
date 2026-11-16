import logging
import requests
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


# ==================================================================
# Log helper — inaandika NotificationLog papo hapo
# ==================================================================
def _log(channel: str, recipient: str, message: str, subject: str = "",
         success: bool = False, error: str = "") -> None:
    try:
        from notifications.models import NotificationLog
        NotificationLog.objects.create(
            channel=channel, recipient=recipient, subject=subject,
            message=message, success=success, error=error,
        )
    except Exception:
        logger.exception("NotificationLog save failed")


# ==================================================================
# SMS — Africa's Talking
# ==================================================================
def send_sms(phone: str, message: str) -> dict:
    if not phone:
        return {"ok": False, "error": "Phone required"}

    phone = phone.strip().replace(" ", "").replace("-", "")
    if phone.startswith("0"):
        phone = "+255" + phone[1:]
    elif not phone.startswith("+"):
        phone = "+255" + phone

    headers = {
        "apiKey": settings.AT_API_KEY,
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
    }
    payload = {
        "username": settings.AT_USERNAME,
        "to": phone,
        "message": message,
        "from": settings.AT_SENDER_ID,
    }
    try:
        r = requests.post(settings.AT_BASE_URL, headers=headers,
                          data=payload, timeout=15)
        ok = r.status_code == 201
        _log("sms", phone, message, success=ok,
             error="" if ok else r.text[:300])
        return {"ok": ok, "response": r.json() if r.text else {}}
    except requests.RequestException as exc:
        _log("sms", phone, message, success=False, error=str(exc))
        return {"ok": False, "error": str(exc)}


def send_bulk_sms(recipients: list[str], message: str) -> list[dict]:
    return [{"phone": p, **send_sms(p, message)} for p in recipients]


# ==================================================================
# EMAIL — Gmail SMTP
# ==================================================================
def send_email(subject: str, message: str, recipients: list[str],
               html_message: str | None = None) -> dict:
    if not recipients:
        return {"ok": False, "error": "No recipients"}
    try:
        send_mail(
            subject=subject, message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
            html_message=html_message, fail_silently=False,
        )
        _log("email", ",".join(recipients), message, subject=subject, success=True)
        return {"ok": True}
    except Exception as exc:
        _log("email", ",".join(recipients), message, subject=subject,
             success=False, error=str(exc))
        return {"ok": False, "error": str(exc)}


# ==================================================================
# Templates za ujumbe
# ==================================================================
def sms_otp(otp: str) -> str:
    return f"SmartShop: OTP yako ni {otp}. Usiitume kwa mtu mwingine."


def sms_order_confirmed(order_id: str, total: str) -> str:
    return f"SmartShop: Order {order_id[:8]} imethibitishwa. Jumla: TZS {total}."


def sms_payment_confirmed(order_id: str) -> str:
    return f"SmartShop: Malipo ya order {order_id[:8]} yamethibitishwa. Asante!"


def sms_salary_paid(month: str, total: str) -> str:
    return f"SmartShop: Mshahara wa {month} umelipwa. Jumla: TZS {total}."


def sms_expense_decision(request_id: str, approved: bool, amount: str) -> str:
    hali = "imekubaliwa" if approved else "imekataliwa"
    return f"SmartShop: Ombi {request_id[:8]} ({amount}) {hali}."


def email_otp_html(otp: str, name: str) -> str:
    return f"""
    <div style="font-family:Arial;max-width:480px;margin:auto;
                border:1px solid #e2e8f0;border-radius:12px;padding:24px">
      <h2 style="color:#1e293b">Habari {name},</h2>
      <p style="color:#475569">OTP yako ya SmartShop ni:</p>
      <div style="font-size:32px;font-weight:bold;letter-spacing:6px;
                  background:#f1f5f9;padding:16px;text-align:center;
                  border-radius:8px;color:#2563eb">{otp}</div>
      <p style="color:#64748b;font-size:12px;margin-top:16px">
        OTP hii ni ya matumizi ya mara moja.
      </p>
    </div>
    """