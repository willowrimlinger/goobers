from app import app, version_blueprint
from app.models import Goober, Fingerprint, CheckIn, Event, GooberHistory
from flask import request, jsonify, render_template
from app import db
from datetime import datetime, timedelta
import hashlib
import json


@version_blueprint.route('/hello')
def index():
    return 'Hello, World!'

@version_blueprint.route('/goobers', methods=['GET'])
def get_goobers():
    goobers = Goober.get_all()
    return {'goobers': [{'name': goober.name, 'fingerprint': goober.fingerprint.fingerprint} for goober in goobers]}

@DeprecationWarning
@version_blueprint.route('/goobers/<string:fingerprint>', methods=['GET'])
def get_goober_by_fingerprint(fingerprint: str):
    fingerprint_obj = Fingerprint.get_by_fingerprint(fingerprint)
    if not fingerprint_obj: 
        return jsonify({'error': 'Fingerprint not register not found'}), 404
    goober = Goober.get_by_fingerprint(Fingerprint.get_by_fingerprint(fingerprint))
    if not goober:
        return jsonify({'error': 'Goober not found'}), 404
    
    history = GooberHistory.get_by_fingerprint(goober_id=goober.id)

    if not history or (datetime.now() - history[0].timestamp) > timedelta(days=6):
        event: Event = Event.get_random_event()
        db.session.add(GooberHistory(goober_id=goober.id, event_id=event.id, timestamp=datetime.now()))
        db.session.commit()

    return jsonify(goober.to_json()), 200

@version_blueprint.route('/goobers', methods=['POST'])
def create_goober():
    data = request.get_json()
    name: str = data.get('name')
    fingerprint: str = data.get('fingerprint')

    if not name or not fingerprint:
        return jsonify({'error': 'Name and fingerprint are required'}), 400

    existing_goober = Goober.query.join(Fingerprint).filter_by(fingerprint=fingerprint).first()
    if existing_goober:
        return jsonify({'error': 'Goober with this fingerprint already exists'}), 400
    
    new_goober: Goober = Goober(name=name, fingerprint=Fingerprint.query.filter_by(fingerprint=fingerprint).first())
    db.session.add(new_goober)
    db.session.commit()

    return jsonify({'message': 'Goober created successfully', 'goober': {'name': new_goober.name, 'fingerprint': new_goober.fingerprint.fingerprint}}), 201

@version_blueprint.route('/sessions', methods=['GET'])
def get_latest_session():
    checkin = CheckIn.get_latest()
    
    if (not checkin or ((datetime.now() -checkin.timestamp) > timedelta(minutes=5))):
        return jsonify({'error': 'No recent sessions found'}), 404
    
    goober = Goober.get_by_fingerprint(checkin.fingerprint)
    if (goober is None):
        hash = hashlib.sha256((str(checkin.fingerprint) + str(checkin.timestamp)).encode('utf-8')).hexdigest()
        return jsonify({'url': f"https://goober.garden?access_token={hash}"}), 200
    else:
        goober.go_on_adventure()
        return goober.to_json(), 200


@version_blueprint.route('/sessions', methods=['POST'])
def check_in_fingerprint():
    data = request.get_json()
    fingerprint: str = data.get('fingerprint')

    if not fingerprint:
        return jsonify({'error': 'Fingerprint is required'}), 400

    existing_fingerprint = Fingerprint.query.filter_by(fingerprint=fingerprint).first()

    if not existing_fingerprint:
        existing_fingerprint = Fingerprint(fingerprint=fingerprint)
        db.session.add(existing_fingerprint)

    new_checkin: CheckIn = CheckIn(fingerprint_id=db.session.query(Fingerprint).filter_by(fingerprint=fingerprint).first().id, timestamp=datetime.now())
    db.session.add(new_checkin)
    db.session.commit()

    return jsonify({'message': 'Check-in successful', 'fingerprint': existing_fingerprint.fingerprint}), 201

@version_blueprint.route('/events', methods=['POST'])
def create_event():
    data = request.get_json()
    name: str = data.get('name')
    description: str = data.get('description')
    stat_name: str = data.get('stat_name')
    type: str = data.get('type')
    if type == 'str':
        valuestring: str = data.get('value_string')
    if type == 'float':
        valuefloat: float = data.get('value_float')

    if not name or not description:
        return jsonify({'error': 'Name, description, and timestamp are required'}), 400

    new_event: Event = Event(name=name, description=description, stat_name=stat_name, type=type, value_string=valuestring if type == 'str' else None, value_float=valuefloat if type == 'float' else None)
    db.session.add(new_event)
    db.session.commit()

    return jsonify({'message': 'Event created successfully', 'event': {'name': new_event.name, 'description': new_event.description}}), 201

@version_blueprint.route('/gimme-new-one', methods=['GET'])
def get_available_fingerprint():
    fingerprint: str = Fingerprint.get_available_fingerprints()
    if not fingerprint:
        return jsonify({'error': 'No available fingerprints'}), 404
    return str(fingerprint), 200

@version_blueprint.route('/bubba-gum-shimp', methods=['GET'])
def get_bubba_gum_shimp():
    return render_template('index.html')


app.register_blueprint(version_blueprint, url_prefix='/v1')