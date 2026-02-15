from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
import uuid
import qrcode
from io import BytesIO
from flask_mail import Mail, Message

app = Flask(__name__)

# ================= DATABASE (LOCAL SQLITE) =================
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///registrations.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# ================= EMAIL CONFIG =================
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'rene.arduo@gmail.com'   # <-- replace
app.config['MAIL_PASSWORD'] = 'tbdbdcebjbpawneh'     # <-- replace

mail = Mail(app)

# ================= DATABASE MODEL =================
class Registration(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)

# ================= ROUTE =================
@app.route("/", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]

        unique_id = str(uuid.uuid4())

        # Save to database
        user = Registration(id=unique_id, name=name, email=email)
        db.session.add(user)
        db.session.commit()

        # Generate QR code
        qr = qrcode.make(unique_id)
        buffer = BytesIO()
        qr.save(buffer, format="PNG")
        buffer.seek(0)

        # Send email
        msg = Message(
            "Your Event QR Code",
            sender=app.config['MAIL_USERNAME'],
            recipients=[email]
        )
        msg.body = f"Hello {name},\n\nYour Registration ID:\n{unique_id}"
        msg.attach("qrcode.png", "image/png", buffer.read())

        mail.send(msg)

        return "Registration successful! QR sent to your email."

    return '''
    <h2>Event Registration</h2>
    <form method="POST">
        Name: <input type="text" name="name" required><br><br>
        Email: <input type="email" name="email" required><br><br>
        <input type="submit" value="Register">
    </form>
    '''

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
