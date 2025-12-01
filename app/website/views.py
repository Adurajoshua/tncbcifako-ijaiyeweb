from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from app.website.models import Events, User
from app.website.forms import EventForm, LoginForm, RegisterForm
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from flask_mail import Message
from app.website import db
from app.website import mail
from sqlalchemy import or_
import os
import time
import requests
from dotenv import load_dotenv
load_dotenv()

livestream_cache = {'data': None, 'timestamp': 0}

# Create main blueprint
mainbp = Blueprint('main', __name__)

@mainbp.route('/')
def home():
    events = Events.query.all()
    return render_template('index.html', all_events=events)


@mainbp.route('/prayer-request')
def prayer_requests():
    return render_template('prayer_requests.html')


@mainbp.route('/show-event')
def single_event():
    return render_template('events-single.html')


@mainbp.route('/events')
def events():
    events = Events.query.all()
    return render_template('events.html', all_events=events)


@mainbp.route('/about')
def about():
    return render_template('about.html')


@mainbp.route('/contact')
def contact():
    return render_template('contact.html')



# ---------------------------- ADMIN -------------------------------------#

@mainbp.route('/register', methods=['GET', 'POST'])
def register():
    register_form = RegisterForm()
    
    if register_form.validate_on_submit():
        user_name = register_form.user_name.data.lower()
        email = register_form.email.data
        password = register_form.password.data
        
        # Check if user already exists
        existing_user = User.query.filter_by(name=user_name).first()
        if existing_user:
            flash("Username already exists, please try another one.")
            return redirect(url_for('main.register'))
        
        # Create new user with hashed password
        hashed_password = generate_password_hash(password)
        new_user = User(name=user_name, password_hash=hashed_password, email_id=email)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash("Registration successful! Please login.")
        return redirect(url_for('main.login'))
    
    return render_template('register.html', form=register_form)


@mainbp.route('/login', methods=['GET', 'POST'])
def login():
    user_login = LoginForm()

    if user_login.validate_on_submit():
        user_name = user_login.name.data.lower()
        user = User.query.filter_by(name=user_name).first()

        if user is not None:
            if check_password_hash(user.password_hash, user_login.password.data):
                login_user(user)

                return redirect(url_for("main.admin"))
            else:
                flash("Password incorrect, please try again.")
        else:
            flash("The user does not exist, please try again.")

    return render_template("login.html", form=user_login, logged_in=current_user.is_authenticated)

@mainbp.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    event_form = EventForm()


    if event_form.validate_on_submit():
        new_event = Events(
            name = event_form.name.data,
            description = event_form.description.data,
            date = event_form.date.data,
            time = event_form.time.data,
            location = event_form.location.data
        )

        db.session.add(new_event)
        db.session.commit()
        

        return redirect(url_for("main.all_post"))
    
    return render_template('admin.html', form=event_form)


@mainbp.route('/admin/all-post')
def all_post():
    events = Events.query.all()

    return render_template('admin-events.html', all_events=events)


@mainbp.route("/admin/delete/<int:event_id>")
@login_required
def delete_post(event_id):
    event_to_delete = Events.query.get(event_id)
    Events.query.filter(Events.id == event_id).delete()
    db.session.delete(event_to_delete)
    db.session.commit()
    return redirect(url_for('main.all_post'))


@mainbp.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have successfully logged out!", 'success')
    return redirect(url_for('main.login'))


# ---------------------------- API -------------------------------------#

@mainbp.route('/api/livestream-status')
def livestream_status():
    global livestream_cache
    
    # Return cached result if less than 5 minutes old
    if livestream_cache['data'] and (time.time() - livestream_cache['timestamp']) < 900:
        print("Returning cached livestream status")
        return livestream_cache['data']
    
    channel_id = "UCACyJw_Amn34mmY3DP0gIsw"
    api_key = os.environ.get('YOUTUBE_API_KEY')
    
    try:
        response = requests.get(
            "https://www.googleapis.com/youtube/v3/search",
            params={
                'part': 'snippet',
                'channelId': channel_id,
                'type': 'video',
                'eventType': 'live',
                'key': api_key
            }
        )
        data = response.json()
        print(f"YouTube API response: {data}")
        
        if data.get('items') and len(data['items']) > 0:
            result = {'live': True, 'videoId': data['items'][0]['id']['videoId']}
        else:
            if data.get('error'):
                print(f"YouTube API error: {data['error']}")
            result = {'live': False}
        
        # Cache the result
        livestream_cache = {'data': result, 'timestamp': time.time()}
        return result
        
    except Exception as e:
        print(f"Livestream check error: {e}")
        return {'live': False}


# ---------------------------- MAIL -------------------------------------#
@mainbp.route('/send-contact', methods=['POST'])
def send_contact():
    try:
        name = request.form.get('cName')
        email = request.form.get('cEmail')
        message = request.form.get('cMessage')

        print(f"Mail username: {current_app.config['MAIL_USERNAME']}")
        print(f"Mail server: {current_app.config['MAIL_SERVER']}")
        
        msg = Message(
            subject=f"Contact Form: Message from {name}",
            sender=email,
            recipients=['tncbctv@gmail.com'],
            reply_to=email,
            body=f"Name: {name}\nEmail: {email}\n\nMessage: {message}"
        )
        mail.send(msg)
        flash("Your message has been sent successfully!", "success")
    except Exception as e:
        print(f"Email error: {e}")
        flash("Failed to send message. Please try again.", "error")
    
    return redirect(url_for('main.contact'))


@mainbp.route('/send-prayer-request', methods=['POST'])
def send_prayer_request():
    try:
        name = request.form.get('cName')
        email = request.form.get('cEmail')
        message = request.form.get('cMessage')
        
        msg = Message(
            subject=f"Prayer Request from {name}",
            sender=email,
            recipients=['tncbctv@gmail.com'],
            reply_to=email,
            body=f"Name: {name}\nEmail: {email}\n\nPrayer Request: {message}"
        )
        mail.send(msg)
        flash("Your prayer request has been submitted. We will be praying with you!", "success")
    except Exception as e:
        print(f"Email error: {e}")
        flash("Failed to submit prayer request. Please try again.", "error")
    
    return redirect(url_for('main.prayer_requests'))