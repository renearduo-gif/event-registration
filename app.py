from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
import uuid
import qrcode
from io import BytesIO
from flask_mail import Mail, Message
import os

app = Flask(__name__)

# ================= DATABASE =================
# Use Render managed PostgreSQL
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# ================= EMAIL =================
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.environ.get("MAIL_PASSWORD")
mail = Mail(app)

# ================= DATABASE MODEL =================
class Registration(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)

# ================= ROUTES =================
@app.route("/", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]

        # Check duplicate
        if Registration.query.filter_by(email=email).first():
            return "This email is already registered."

        unique_id = str(uuid.uuid4())

        # Save user to database
        user = Registration(id=unique_id, name=name, email=email)
        db.session.add(user)
        db.session.commit()

        # Generate QR code
        qr = qrcode.make(unique_id)
        buffer = BytesIO()
        qr.save(buffer, format="PNG")
        buffer.seek(0)

        # Send email
        try:
            msg = Message(
                "Your Event QR Code",
                sender=app.config['MAIL_USERNAME'],
                recipients=[email]
            )
            msg.body = f"Hello {name},\n\nYour Registration ID:\n{unique_id}"
            msg.attach("qrcode.png", "image/png", buffer.read())
            mail.send(msg)
        except Exception as e:
            return f"Registration saved but email failed: {str(e)}"

        return "Registration successful! QR sent to your email."

    # Registration form
    return '''
    <h2>Event Registration</h2>
    <form method="POST">
        Name: <input type="text" name="name" required><br><br>
        Email: <input type="email" name="email" required><br><br>
        <input type="submit" value="Register">
    </form>
    '''

# ================= ADMIN PAGE =================
@app.route("/admin")
def admin():
    users = Registration.query.all()
    result = "<h2>Registered Users</h2>"
    for u in users:
        result += f"<p>{u.name} - {u.email} - {u.id}</p>"
    return result

# ================= START APP =================
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000)
