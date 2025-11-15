from app import app
from app.models import Goober
from flask import request, jsonify  
from app import db

@app.route('/hello')
def index():
    return 'Hello, World!'

@app.route('/goobers', methods=['GET'])
def get_goobers():
    goobers: list[Goober] = Goober.query.all()
    return {'goobers': [goober.name for goober in goobers]}

@app.route('/goobers', methods=['POST'])
def create_goober():
    data = request.get_json()
    name: str = data.get('name')
    fingerprint: str = data.get('fingerprint')

    if not name or not fingerprint:
        return jsonify({'error': 'Name and fingerprint are required'}), 400

    existing_goober = Goober.query.filter_by(fingerprint=fingerprint).first()
    if existing_goober:
        return jsonify({'error': 'Goober with this fingerprint already exists'}), 400

    new_goober: Goober = Goober(name=name, fingerprint=fingerprint)
    db.session.add(new_goober)
    db.session.commit()

    return jsonify({'message': 'Goober created successfully', 'goober': {'name': new_goober.name, 'fingerprint': new_goober.fingerprint}}), 201