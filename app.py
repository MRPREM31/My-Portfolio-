from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flask_bcrypt import Bcrypt
from datetime import datetime
import os
import random
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "default_secret")

# SQLite database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///submissions.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
mail = Mail(app)

# DB model for user submissions
class ContactSubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    message = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# DB model for admin users
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))

# Temporary store for OTPs
otp_store = {}

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/journey")
def journey():
    return render_template("journey.html")

@app.route("/work_experience")
def work_experience():
    return render_template("work-experience.html")

@app.route("/contact", methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']

        new_entry = ContactSubmission(name=name, email=email, message=message)
        db.session.add(new_entry)
        db.session.commit()

        admin_msg = Message("New Contact Submission",
                            sender=app.config['MAIL_USERNAME'],
                            recipients=[os.getenv("ADMIN_EMAIL")])
        admin_msg.body = f"Name: {name}\nEmail: {email}\nMessage: {message}\nTime: {new_entry.timestamp}"
        mail.send(admin_msg)

        user_msg = Message("Thanks for contacting!",
                           sender=app.config['MAIL_USERNAME'],
                           recipients=[email])
        user_msg.body = f"Hi {name},\n\nThanks for reaching out! We’ll get back to you soon."
        mail.send(user_msg)

        return redirect(url_for('thank_you', name=name))

    return render_template("contact.html")

@app.route("/thank_you")
def thank_you():
    name = request.args.get('name', '')
    return render_template("thank_you.html", name=name)

@app.route("/admin_login", methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        admin = Admin.query.filter_by(email=email).first()

        if admin and bcrypt.check_password_hash(admin.password, password):
            session['admin'] = email
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Invalid login credentials")

    return render_template("admin_login.html")

@app.route("/admin_dashboard")
def admin_dashboard():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    submissions = ContactSubmission.query.order_by(ContactSubmission.timestamp.desc()).all()
    return render_template("admin_dashboard.html", submissions=submissions)

@app.route("/change_password", methods=['GET', 'POST'])
def change_password():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        new_password = request.form['new_password']
        admin = Admin.query.filter_by(email=session['admin']).first()
        admin.password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        db.session.commit()
        flash("Password updated successfully!")
        return redirect(url_for('admin_dashboard'))

    return render_template("change_password.html")

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        admin = Admin.query.filter_by(email=email).first()

        if not admin:
            flash("Email not registered!", "error")
            return redirect(url_for('forgot_password'))

        otp = str(random.randint(100000, 999999))
        otp_store[email] = otp

        msg = Message("Your OTP for Password Reset",
                      sender=app.config['MAIL_USERNAME'],
                      recipients=[email])
        msg.body = f"Hi,\n\nYour OTP is: {otp}\nUse this to reset your admin password."
        mail.send(msg)

        flash("OTP sent to your email!", "success")
        return redirect(url_for('verify_otp', email=email))

    return render_template("forgot_password.html")

@app.route('/verify_otp/<email>', methods=['GET', 'POST'])
def verify_otp(email):
    if request.method == 'POST':
        entered_otp = request.form['otp']
        new_password = request.form['new_password']

        if otp_store.get(email) == entered_otp:
            admin = Admin.query.filter_by(email=email).first()
            admin.password = bcrypt.generate_password_hash(new_password).decode('utf-8')
            db.session.commit()

            otp_store.pop(email)
            flash("Password reset successfully!", "success")
            return redirect(url_for('admin_login'))
        else:
            flash("Invalid OTP!", "error")

    return render_template("verify_otp.html", email=email)

@app.route("/logout")
def logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))

@app.route("/create_admin")
def create_admin():
    email = "mr.prem2006@gmail.com"
    password = "12345678"

    if Admin.query.filter_by(email=email).first():
        return "❌ Admin already exists!"

    hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
    new_admin = Admin(email=email, password=hashed_pw)
    db.session.add(new_admin)
    db.session.commit()

    return f"✅ Admin created!\nEmail: {email}\nPassword: {password}"

# ✅ Entry point for Render
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
