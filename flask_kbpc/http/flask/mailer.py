import logging
from threading import Thread

from flask_mail import Message

logger = logging.getLogger(__name__)


def send_async_mail(message, state):
    with state.app_context():
        with mail.record_messages() as outbox:
            mail.send(message=message)
            assert len(outbox) == 1


def send_email(app, to, subject, template, sender):
    message = Message(
        subject,
        recipients=to,
        html=template,
        sender=sender
    )
    thread = Thread(target=send_async_mail, args=[message, app._get_current_object()])
    thread.start()
