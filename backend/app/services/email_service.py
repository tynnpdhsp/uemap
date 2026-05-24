from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from app.core.config import settings


async def send_otp_email(email: str, full_name: str, otp_code: str, purpose: str) -> None:
    if purpose == "activation":
        subject = "mã kích hoạt tài khoản bản đồ sinh viên sư phạm"
        text_template = "Chào {full_name},\nMã kích hoạt tài khoản của bạn là: {otp_code}\nMã có hiệu lực trong 15 phút."
        html_template = """
        <html>
            <body>
                <h3>Chào {full_name},</h3>
                <p>Mã kích hoạt tài khoản bản đồ sinh viên sư phạm của bạn là: <strong>{otp_code}</strong></p>
                <p>Mã này có hiệu lực trong 15 phút kể từ lúc gửi.</p>
            </body>
        </html>
        """
    else:
        subject = "mã đặt lại mật khẩu bản đồ sinh viên sư phạm"
        text_template = "Chào {full_name},\nMã đặt lại mật khẩu của bạn là: {otp_code}\nMã có hiệu lực trong 15 phút."
        html_template = """
        <html>
            <body>
                <h3>Chào {full_name},</h3>
                <p>Mã đặt lại mật khẩu bản đồ sinh viên sư phạm của bạn là: <strong>{otp_code}</strong></p>
                <p>Mã này có hiệu lực trong 15 phút kể từ lúc gửi.</p>
            </body>
        </html>
        """

    text_content = text_template.format(full_name=full_name, otp_code=otp_code)
    html_content = html_template.format(full_name=full_name, otp_code=otp_code)

    if settings.ENV == "dev" and (not settings.SMTP_USER or not settings.SMTP_PASSWORD):
        print(f"\n[DEV MODE] Gửi mail tới {email} | Tiêu đề: {subject} | OTP: {otp_code}\n")
        return

    message = MIMEMultipart("alternative")
    message["From"] = (
        f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL or settings.SMTP_USER}>"
    )
    message["To"] = email
    message["Subject"] = subject

    message.attach(MIMEText(text_content, "plain", "utf-8"))
    message.attach(MIMEText(html_content, "html", "utf-8"))

    try:
        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            start_tls=settings.SMTP_PORT == 587,
            use_tls=settings.SMTP_PORT == 465,
        )
    except Exception as e:
        print(f"Lỗi gửi email: {e}. [DEV-FALLBACK] OTP: {otp_code}")
        if settings.ENV != "dev":
            raise e
