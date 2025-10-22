from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import qrcode
from io import BytesIO
import base64
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, Email, To, Content

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    company = db.Column(db.String(100))
    position = db.Column(db.String(100))
    pass_type = db.Column(db.String(50))
    interests = db.Column(db.String(200))
    checked_in = db.Column(db.Boolean, default=False)

with app.app_context():
    db.create_all()

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.json
        name = data.get('name')
        email = data.get('email')
        company = data.get('company')
        position = data.get('position')
        pass_type = data.get('passType')
        interests = data.get('interests')
        if not name or not email:
            return jsonify({'error': 'Nombre y email requeridos'}), 400
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email ya registrado'}), 400
        
        user = User(name=name, email=email, company=company, position=position, pass_type=pass_type, interests=interests)
        db.session.add(user)
        db.session.commit()
        
        qr = qrcode.make(str(user.id))
        buffer = BytesIO()
        qr.save(buffer, format="PNG")
        qr_b64 = base64.b64encode(buffer.getvalue()).decode()
        
        return jsonify({'message': 'Registrado exitosamente', 'user_id': user.id, 'qr_code': qr_b64})
    except Exception as e:
        print(f"Error en register: {str(e)}")
        return jsonify({'error': 'Error interno del servidor', 'detail': str(e)}), 500

@app.route('/api/users', methods=['GET'])
def get_users():
    try:
        users = User.query.all()
        if not users:
            return jsonify([]), 200
        return jsonify([{'id': u.id, 'name': u.name, 'email': u.email, 'checked_in': u.checked_in} for u in users])
    except Exception as e:
        print(f"Error en get_users: {str(e)}")
        return jsonify({'error': 'Error al obtener usuarios', 'detail': str(e)}), 500

@app.route('/api/sync', methods=['POST'])
def sync():
    try:
        data = request.json
        for user_data in data:
            user = User.query.get(user_data['id'])
            if user and not user.checked_in and user_data.get('checked_in'):
                user.checked_in = True
                db.session.commit()
        return jsonify({'message': 'Sincronizado exitosamente'})
    except Exception as e:
        print(f"Error en sync: {str(e)}")
        return jsonify({'error': 'Error al sincronizar', 'detail': str(e)}), 500

@app.route('/api/send-email', methods=['POST'])
def send_email():
    try:
        data = request.json
        email = data.get('email')
        qr_code = data.get('qrCode')
        if not email or not qr_code:
            return jsonify({'error': 'Email y QR requeridos'}), 400

        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        from_email = Email(os.environ.get('EMAIL_USER', 'hola@redspace.mx'))
        to_email = To(email)
        subject = 'Tu QR para el Evento'
        content = Content("text/plain", 'Adjunto encontrarás tu QR para el check-in del evento.')
        mail = Mail(from_email, to_email, subject, content)

        # Adjuntar el QR
        qr_image = base64.b64decode(qr_code)
        attachment = Attachment()
        attachment.content = base64.b64encode(qr_image).decode()
        attachment.type = 'image/png'
        attachment.filename = f"qr_{email}.png"
        attachment.disposition = 'attachment'
        attachment.content_id = 'qr_image'
        mail.attachment = attachment

        response = sg.send(mail)
        print(f"Email enviado: {response.status_code} - {response.body}")
        return jsonify({'message': 'Email enviado exitosamente'})
    except Exception as e:
        print(f"Error en send_email: {str(e)}")
        return jsonify({'error': 'Error al enviar email', 'detail': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))