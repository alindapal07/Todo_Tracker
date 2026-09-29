import base64
import logging
import mailtrap as mt
from core.config import settings

logger = logging.getLogger("api.email")


# sends welcome email in the background after successful registration
def send_registration_email(
    email: str,
    name: str | None = None,
):
    recipient_name = name or "User"

    mail = mt.Mail(
        sender=mt.Address(
            email="alindapal83@gmail.com",
            name="Todo App",
        ),
        to=[
            mt.Address(
                email=email,
                name=recipient_name,
            )
        ],
        subject="Welcome to Todo App!",
        text=f"""
Hello {recipient_name},

Welcome to Todo App!

Your account has been successfully created.

You can now start creating and managing your todos.

Regards,
Todo App Team
""",
        category="User Registration",
    )

    try:
        client = mt.MailtrapClient(
            token=settings.MAILTRAP_TOKEN, sandbox=True, inbox_id="4933373"
        )
        response = client.send(mail)
        return response
    except Exception as exc:
        logger.error("Failed to send registration email to %s: %s", email, exc)
        return None


# sends exported todos file as an email attachment
def send_export_email(
    email: str,
    name: str | None = None,
    file_content: str = "",
    file_format: str = "json",
):
    recipient_name = name or "User"
    filename = f"todos.{file_format}"
    mimetype = "application/json" if file_format == "json" else "text/csv"

    # base64 encode file content for mail attachment
    encoded_bytes = base64.b64encode(file_content.encode("utf-8"))

    attachment = mt.Attachment(
        content=encoded_bytes,
        filename=filename,
        mimetype=mimetype,
        disposition="attachment",
    )

    mail = mt.Mail(
        sender=mt.Address(
            email="alindapal83@gmail.com",
            name="Todo App",
        ),
        to=[
            mt.Address(
                email=email,
                name=recipient_name,
            )
        ],
        subject="Your Exported Todos",
        text=f"""
Hello {recipient_name},

Here is your exported todos file ({filename}).
You can download and view your tasks using the attached file.

Regards,
Todo App Team
""",
        category="Todo Export",
        attachments=[attachment],
    )

    try:
        client = mt.MailtrapClient(
            token=settings.MAILTRAP_TOKEN, sandbox=True, inbox_id="4933373"
        )
        response = client.send(mail)
        return response
    except Exception as exc:
        logger.error("Failed to send export email to %s: %s", email, exc)
        return None
