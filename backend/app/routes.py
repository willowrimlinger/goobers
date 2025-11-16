from app import app, version_blueprint
from app.models import Goober, Fingerprint, CheckIn, Event, GooberHistory
from flask import request, jsonify  
from app import db
from datetime import datetime, timedelta
import hashlib


@version_blueprint.route('/hello')
def index():
    return 'Hello, World!'

@version_blueprint.route('/goobers', methods=['GET'])
def get_goobers():
    goobers = Goober.query.all()
    return {'goobers': [{'name': goober.name, 'fingerprint': goober.fingerprint.fingerprint} for goober in goobers]}

@version_blueprint.route('/goobers/<string:fingerprint>', methods=['GET'])
def get_goober_by_fingerprint(fingerprint):
    goober = Goober.query.join(Fingerprint).filter_by(fingerprint=fingerprint).first()
    if goober:
        return {'name': goober.name, 'fingerprint': goober.fingerprint.fingerprint}
    else:
        return jsonify({'error': 'Goober not found'}), 404

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
    checkin = CheckIn.query.order_by(CheckIn.timestamp.desc()).first()
    if (not checkin or ((datetime.now() -checkin.timestamp) > timedelta(minutes=5))):
        return jsonify({'error': 'No recent sessions found'}), 404
    
    goober = Goober.query.filter_by(fingerprint_id=checkin.fingerprint_id).join(Fingerprint).first()
    if (goober is None):
        hash = hashlib.sha256((str(checkin.fingerprint) + str(checkin.timestamp)).encode('utf-8')).hexdigest()
        return jsonify({'url': f"https://goober.garden?access_token={hash}"}), 200
    else:
        return jsonify({'id': f"{goober.fingerprint.fingerprint}"}), 200


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

app.register_blueprint(version_blueprint, url_prefix='/v1')