from flask_cors import CORS
app = Flask(__name__)
CORS(app)
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import qrcode
from io import BytesIO
import base64
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///event.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    checked_in = db.Column(db.Boolean, default=False)

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    if not name or not email:
        return jsonify({'error': 'Nombre y email requeridos'}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email ya registrado'}), 400
    
    user = User(name=name, email=email)
    db.session.add(user)
    db.session.commit()
    
    qr = qrcode.make(str(user.id))
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    qr_b64 = base64.b64encode(buffer.getvalue()).decode()
    
    # Nota: Para email real, configura SMTP (e.g., SendGrid en Render)
    return jsonify({'message': 'Registrado exitosamente', 'user_id': user.id, 'qr_code': qr_b64})

@app.route('/api/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([{'id': u.id, 'name': u.name, 'email': u.email, 'checked_in': u.checked_in} for u in users])

@app.route('/api/sync', methods=['POST'])
def sync():
    data = request.json
    for user_data in data:
        user = User.query.get(user_data['id'])
        if user and not user.checked_in and user_data['checked_in']:
            user.checked_in = True
            db.session.commit()
    return jsonify({'message': 'Sincronizado exitosamente'})

if __name__ == '__main__':
    os.makedirs(os.path.dirname('event.db'), exist_ok=True)
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

