# was planning to use celery to send email reminders to participants of an event but since the time was not enough to deploy it on a server, I used apscheduler instead.
from .models import Event, User
from flask_mail import Message
from . import mail
from . import create_app
import json


def send_event_notification(event_id):
    app = create_app()
    with app.app_context():
        event = Event.query.get(event_id)
        if event.started:
            return
        event.started = True
        app.db.session.commit()
        user_id = event.user_id
        user = User.query.get(user_id)
        participants = json.loads(event.participants)
        if user.email not in participants:
            participants.append(user.email)
        if event:
            msg = Message(
                subject=f"Event Reminder: {event.title}",
                body=f"Reminder for your event: {event.title}\nDescription: {event.description}",
                recipients=participants
            )
            mail.send(msg)
        
