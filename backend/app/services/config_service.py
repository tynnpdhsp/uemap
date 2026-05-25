from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib
from bson import ObjectId
from fastapi import HTTPException, status

from app.core.config import settings
from app.core.database import get_db
from app.services import audit_service


async def get_map_config() -> dict:
    db = get_db()
    config = await db["app_config"].find_one({"_id": "map"})
    if not config:
        return {}
    config.pop("_id", None)
    return config


async def update_map_config(data: dict, admin_id: ObjectId, ip_address: str) -> dict:
    db = get_db()
    update_fields: dict = {"updated_at": datetime.utcnow()}

    if data.get("default_center"):
        update_fields["default_center"] = data["default_center"]
    if data.get("default_zoom") is not None:
        update_fields["default_zoom"] = data["default_zoom"]
    if data.get("geofence"):
        geofence = data["geofence"]
        if geofence.get("type") == "radius":
            if not geofence.get("center") or not geofence.get("radius_meters"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "success": False,
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": "Geofence radius cần center và radius_meters.",
                            "details": [],
                        },
                    },
                )
        update_fields["geofence"] = geofence
    if data.get("cluster_zoom_threshold") is not None:
        update_fields["cluster_zoom_threshold"] = data["cluster_zoom_threshold"]

    await db["app_config"].update_one({"_id": "map"}, {"$set": update_fields}, upsert=True)

    await audit_service.log_event(
        event_code="CONFIG_MAP_UPDATE",
        actor_role="admin",
        actor_id=admin_id,
        object_type="config",
        object_id="map",
        result="success",
        description="Cập nhật cấu hình bản đồ.",
        ip_address=ip_address,
    )

    return await get_map_config()


async def get_email_templates() -> dict:
    db = get_db()
    doc = await db["app_config"].find_one({"_id": "email_templates"})
    if not doc:
        return {}
    doc.pop("_id", None)
    return doc


async def update_email_templates(data: dict, admin_id: ObjectId, ip_address: str) -> dict:
    db = get_db()
    update_fields: dict = {"updated_at": datetime.utcnow()}

    for key in ("activation", "password_reset"):
        if data.get(key):
            tpl = data[key]
            if "{full_name}" not in tpl.get("html_body", "") or "{otp_code}" not in tpl.get(
                "html_body", ""
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "success": False,
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": f"Mẫu {key} phải chứa biến {{full_name}} và {{otp_code}}.",
                            "details": [],
                        },
                    },
                )
            update_fields[key] = tpl

    await db["app_config"].update_one(
        {"_id": "email_templates"}, {"$set": update_fields}, upsert=True
    )

    await audit_service.log_event(
        event_code="CONFIG_EMAIL_UPDATE",
        actor_role="admin",
        actor_id=admin_id,
        object_type="config",
        object_id="email_templates",
        result="success",
        description="Cập nhật mẫu email OTP.",
        ip_address=ip_address,
    )

    return await get_email_templates()


async def test_email(
    to_email: str, template_type: str, admin_id: ObjectId, ip_address: str
) -> dict:
    db = get_db()
    doc = await db["app_config"].find_one({"_id": "email_templates"})
    tpl = doc.get(template_type, {}) if doc else {}

    subject = tpl.get("subject", f"[TEST] {template_type}")
    html_body = tpl.get("html_body", "<p>Test email</p>")
    text_body = tpl.get("text_body", "Test email")

    html_content = html_body.replace("{full_name}", "Nguyễn Văn A").replace("{otp_code}", "123456")
    text_content = text_body.replace("{full_name}", "Nguyễn Văn A").replace("{otp_code}", "123456")

    smtp_success = False
    error_message = None

    if settings.ENV == "dev" and (not settings.SMTP_USER or not settings.SMTP_PASSWORD):
        smtp_success = True
        error_message = "[DEV MODE] Không gửi thực tế do chưa cấu hình SMTP."
    else:
        try:
            message = MIMEMultipart("alternative")
            message["From"] = (
                f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL or settings.SMTP_USER}>"
            )
            message["To"] = to_email
            message["Subject"] = f"[TEST] {subject}"
            message.attach(MIMEText(text_content, "plain", "utf-8"))
            message.attach(MIMEText(html_content, "html", "utf-8"))

            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                start_tls=settings.SMTP_PORT == 587,
                use_tls=settings.SMTP_PORT == 465,
            )
            smtp_success = True
        except Exception as e:
            error_message = str(e)

    await audit_service.log_event(
        event_code="CONFIG_EMAIL_TEST",
        actor_role="admin",
        actor_id=admin_id,
        object_type="config",
        object_id="email_templates",
        result="success" if smtp_success else "failure",
        description=f"Gửi email thử nghiệm tới {to_email} ({template_type}).",
        ip_address=ip_address,
    )

    return {"smtp_success": smtp_success, "message": error_message}
