from flask_restful import Resource, reqparse
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from flask_cors import cross_origin
from .models import User, Event, db
from datetime import datetime
from flask import request, current_app as app
import requests
import json


def init_routes(api):
    api.add_resource(UserRegistration, '/register')
    api.add_resource(UserLogin, '/login')
    api.add_resource(EventManagement, '/events', '/events/<int:event_id>')
    api.add_resource(UserManagement, '/auth/me')
    api.add_resource(HolidayManagement, '/holidays',
                     '/holidays/<string:country_code>')


class HolidayManagement(Resource):

    @jwt_required()
    def get(self, country_code=None):
        holidays = requests.get("https://holidayapi.com/v1/holidays", headers={"Content-Type": "application/json"}, params={
                                "country": country_code, "year": "2023", "key": app.config['HOLIDAY_API_KEY'], "pretty": True})
        return holidays.json()["holidays"], 200


class UserManagement(Resource):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        return {
            'id': user.id,
            'email': user.email
        }, 200


class UserRegistration(Resource):
    @cross_origin()
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('email', required=True)
        parser.add_argument('password', required=True)
        data = parser.parse_args()

        if User.query.filter_by(email=data['email']).first():
            return {'message': 'User already exists'}, 400

        new_user = User(email=data['email'], password=data['password'])
        db.session.add(new_user)
        db.session.commit()
        return {'message': 'User created successfully'}, 201


class UserLogin(Resource):
    @cross_origin()
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('email', required=True)
        parser.add_argument('password', required=True)
        data = parser.parse_args()

        user = User.query.filter_by(email=data['email']).first()

        if user and user.password == data['password']:
            access_token = create_access_token(identity=user.id)
            return {'access_token': access_token, 'user': {'id': user.id, 'email': user.email}}, 200
        return {'message': 'Invalid credentials'}, 401


class EventManagement(Resource):
    @jwt_required()
    def get(self, event_id=None):
        user_id = get_jwt_identity()
        if event_id:
            event = Event.query.filter_by(id=event_id, user_id=user_id).first()
            if event:
                return {
                    'id': event.id,
                    'title': event.title,
                    'start_time': event.start_time.isoformat(),
                    'end_time': event.end_time.isoformat(),
                    'description': event.description,
                    'participants': event.participants
                }, 200
            return {'message': 'Event not found'}, 404
        events = Event.query.filter_by(user_id=user_id).all()
        return [{
            'id': event.id,
            'title': event.title,
            'start_time': event.start_time.isoformat(),
            'end_time': event.end_time.isoformat(),
            'description': event.description,
            'participants': json.loads(event.participants) if event.participants != '' else [],
            'timezone': event.timezone
        } for event in events], 200

    @jwt_required()
    def post(self):
        user_id = get_jwt_identity()
        parser = reqparse.RequestParser()
        parser.add_argument('title', required=True)
        parser.add_argument('start_time', required=True)
        parser.add_argument('end_time', required=True)
        parser.add_argument('description')
        parser.add_argument('participants')
        parser.add_argument('timezone', required=True)
        data = parser.parse_args()

        start_time = datetime.fromisoformat(data['start_time'])
        end_time = datetime.fromisoformat(data['end_time'])
        
        # check if another event is scheduled at the same time
        
        overlapping_events = Event.query.filter(
            Event.start_time <= end_time, Event.end_time >= start_time, Event.user_id == user_id).first()
        
       
        # 12:10 - 12:30 12:11 
        
        
        if overlapping_events:
            print(overlapping_events)
            return {'message': 'Another event is scheduled at the same time'}, 400

        if not data['participants']:
            participants = []
        participants = json.dumps(request.json['participants'])

        new_event = Event(
            title=data['title'],
            start_time=start_time,
            end_time=end_time,
            description=data.get('description'),
            participants=participants,
            timezone=data['timezone'],
            user_id=user_id
        )

        db.session.add(new_event)
        db.session.commit()
        from .tasks import send_event_notification
        app.scheduler.add_job(send_event_notification,
                              'date', run_date=start_time, args=[new_event.id], id=f"event_{new_event.id}")

        return {'message': 'Event created successfully'}, 201

    @jwt_required()
    def put(self, event_id):
        user_id = get_jwt_identity()
        event = Event.query.filter_by(id=event_id, user_id=user_id).first()

        if not event:
            return {'message': 'Event not found'}, 404

        parser = reqparse.RequestParser()
        parser.add_argument('title')
        parser.add_argument('start_time')
        parser.add_argument('end_time')
        parser.add_argument('description')
        parser.add_argument('participants')
        parser.add_argument('timezone', required=True)
        data = parser.parse_args()

        if data.get('title'):
            event.title = data['title']
        if data.get('start_time'):
            event.start_time = datetime.fromisoformat(data['start_time'])
            if app.scheduler.get_job(f"event_{event.id}"):
                app.scheduler.reschedule_job(
                    f"event_{event.id}", run_date=event.start_time)
        if data.get('end_time'):
            event.end_time = datetime.fromisoformat(data['end_time'])
        if data.get('description'):
            event.description = data['description']
        if data.get('participants'):
            participants = json.dumps(request.json['participants'])
            event.participants = participants
        if data.get('timezone'):
            event.timezone = data['timezone']

        db.session.commit()

        return {'message': 'Event updated successfully'}, 200

    @jwt_required()
    def delete(self, event_id):
        user_id = get_jwt_identity()
        event = Event.query.filter_by(id=event_id, user_id=user_id).first()

        if not event:
            return {'message': 'Event not found'}, 404

        db.session.delete(event)
        db.session.commit()

        if app.scheduler.get_job(f"event_{event.id}"):
            app.scheduler.remove_job(f"event_{event.id}")
        return {'message': 'Event deleted successfully'}, 200
