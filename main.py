import time
from datetime import datetime, timedelta
import random
import base64
from flask import Flask, flash, render_template, request, redirect, session, url_for
from flask_socketio import SocketIO, emit
from flask_mail import Mail, Message
from flask_mysqldb import MySQL
import MySQLdb
import hashlib


obj = Flask(__name__, template_folder="theme")
socketio = SocketIO(obj, cors_allowed_origins="*", manage_session=False)
obj.secret_key = "one_login_activity_system_2023"

obj.config["MYSQL_HOST"] = 'localhost'
obj.config["MYSQL_USER"] = 'root'
obj.config["MYSQL_PASSWORD"] = ''
obj.config["MYSQL_DB"] = 'one_active_login_system'

db_obj = MySQL(obj)

# configuration of mail
obj.config['MAIL_SERVER']='smtp-relay.sendinblue.com'
obj.config['MAIL_PORT'] = 587
obj.config['MAIL_USERNAME'] = 'indureddy.2529@gmail.com'
obj.config['MAIL_PASSWORD'] = 'bDZ3rSjn14vYHVKz'
obj.config['MAIL_DEFAULT_SENDER'] = 'indureddy.2529@gmail.com'
mail = Mail(obj)

def send_verification_link_to_email(full_name, email, registration_id):
    try:
        expiry_datetime = datetime.now() + timedelta(minutes=30)
        expiry_datetime = expiry_datetime.strftime("%Y-%m-%d %H:%M:%S")
        encoded_expiry_datetime = base64.b64encode(expiry_datetime.encode('ascii'))
        email_url = f"http://127.0.0.1:5000/verify/{registration_id}/{encoded_expiry_datetime.decode('ascii')}"
        subject = "Please verify your account."
        body = f"<p>Hello {full_name}</p><p>Your account has been created successfully. Please click below link and verify your account.</p>"
        body += f"<p>Link - {email_url}</p>"
        body += "<p>Your,</p><p>Team One active login system</p>"
        message = Message(
            subject=subject,
            recipients=[email],
            body=body,
        )

        mail.send(message)
    except Exception as ex:
        print("Code Error: {}".format(ex))

def send_password_reset_link(full_name, email, registration_id):
    try:
        expiry_datetime = datetime.now() + timedelta(minutes=30)
        expiry_datetime = expiry_datetime.strftime("%Y-%m-%d %H:%M:%S")
        encoded_expiry_datetime = base64.b64encode(expiry_datetime.encode('ascii'))
        email_url = f"http://127.0.0.1:5000/reset/{registration_id}/{encoded_expiry_datetime.decode('ascii')}"
        subject = "Reset your password."
        body = f"<p>Hello {full_name}</p><p>As you forgot your password. Here it is your reset password link. Please click on the link. If you have not requested the link then please ignore this email.</p>"
        body += f"<p>Link - {email_url}</p>"
        body += "<p>Your,</p><p>Team One active login system</p>"
        message = Message(
            subject=subject,
            recipients=[email],
            body=body,
        )

        mail.send(message)
    except Exception as ex:
        print("Code Error: {}".format(ex))

def add_in_login_history(user_id, user_agent):
    try:
        query = "INSERT INTO login_history(`registration_id`,`socket_id`,`login_status`,`user_agent`,`signin_date`) VALUES({},'{}',{},'{}','{}');".format(user_id, '', 1, user_agent, datetime.today())
        mysql_cursor = db_obj.connection.cursor(MySQLdb.cursors.DictCursor)
        mysql_cursor.execute(query)
        db_obj.connection.commit()
        history_id = mysql_cursor.lastrowid
        mysql_cursor.close()
        return history_id
    except Exception as ex:
        print("Code Error: {}".format(ex))

def get_already_logged_in_socket_ids(my_id, history_id):
    try:
        socket_ids = []
        query = "SELECT socket_id FROM login_history WHERE registration_id={} AND history_id != {};".format(my_id, history_id)
        mysql_cursor = db_obj.connection.cursor(MySQLdb.cursors.DictCursor)
        mysql_cursor.execute(query)
        rows = mysql_cursor.fetchall()
        mysql_cursor.close()
        for row in rows:
            socket_ids.append(row['socket_id'])
        return socket_ids
    except Exception as ex:
        print("Code Error: {}".format(ex))

@obj.route('/', methods=['GET', 'POST'])
def index():
    try:
        data = {}
        data['type'] = 'login'
        return render_template("registration.html", data=data)
    except Exception as ex:
        print("Code Error: {}".format(ex))

@obj.route('/registration_process', methods=['POST'])
def registration_process():
    data = {}
    data['type'] = 'registration'
    try:
        first_name = request.form['first_name'].title()
        last_name = request.form['last_name'].title()
        email = request.form['email'].casefold()
        mysql_cursor = db_obj.connection.cursor(MySQLdb.cursors.DictCursor)
        mysql_cursor.execute("SELECT * FROM registrations WHERE email='{}'".format(email))
        if mysql_cursor.rowcount > 0:
            flash("Please enter unique email. Requested email is already taken.")
            return render_template('registration.html', data=data)
        mysql_cursor.close()
        password = hashlib.sha512(request.form['password'].encode()).hexdigest()
        query = "INSERT INTO registrations(first_name,last_name,email,password,verified) VALUES('{}','{}','{}','{}',{})".format(first_name, last_name, email, password, 0)
        mysql_cursor = db_obj.connection.cursor(MySQLdb.cursors.DictCursor)
        mysql_cursor.execute(query)
        db_obj.connection.commit()
        if mysql_cursor.rowcount > 0:
            registration_id = mysql_cursor.lastrowid
            mysql_cursor.close()
            session['verified'] = 'no'
            session['registration_id'] = registration_id
            send_verification_link_to_email(f"{first_name} {last_name}", email, registration_id)
            flash('Registration is successfully done. Please check your email for verification link.')
        return redirect(url_for('index'))
    except Exception as ex:
        print("Code Error: {}".format(ex))

@obj.route('/verify/<int:id>/<string:expiry_date>')
def verify(id, expiry_date):
    try:
        data = {}
        data['type'] = 'login'
        registration_id = id
        expiry_date_decode = base64.b64decode(expiry_date.encode('ascii')).decode('ascii')
        expiry_date_in_format = datetime.strptime(expiry_date_decode, "%Y-%m-%d %H:%M:%S")
        now_date = datetime.now()
        if now_date <= expiry_date_in_format:
            query = "UPDATE registrations SET verified=1 WHERE id={}".format(registration_id)
            mysql_cursor = db_obj.connection.cursor(MySQLdb.cursors.DictCursor)
            mysql_cursor.execute(query)
            db_obj.connection.commit()
            mysql_cursor.close()
            session['verified'] = 'yes'
            flash("Your email address is verified.")
        else:
            flash("Link is expired. Please sign-in and you will get the new verification link.")
        return render_template("registration.html", data=data)
    except Exception as ex:
        print("Code Error: {}".format(ex))

@obj.route('/login', methods=['POST', 'GET'])
def login():
    try:
        data = {}
        data['type'] = 'login'
        if request.method == 'POST':
            email = request.form['email']
            password = hashlib.sha512(request.form['password'].encode()).hexdigest()
            query = "SELECT * FROM registrations WHERE email = '{}' AND password = '{}' LIMIT 1;".format(email, password)
            mysql_cursor = db_obj.connection.cursor(MySQLdb.cursors.DictCursor)
            mysql_cursor.execute(query)
            user_row = mysql_cursor.fetchone()
            mysql_cursor.close()
            if user_row is not None:
                if user_row['verified'] == 0:
                    session['verified'] = 'no'
                    session['registration_id'] = user_row['id']
                    send_verification_link_to_email(f"{user_row['first_name']} {user_row['last_name']}", email, user_row['id'])
                    flash('Your account is not verified. Verification link is sent to your registered email. Please verify it.')
                    return redirect('index')
                else:
                    session['history_id'] = add_in_login_history(user_row['id'], request.headers.get('User-Agent'))
                    session['my_full_name'] = f"{user_row['first_name']} {user_row['last_name']}"
                    session['my_id'] = user_row['id']
                    session['unique_id'] = random.randrange(1111,9999)
                    return redirect('history')
            else:
                flash('Invalid credentials.')
                return render_template("registration.html", data=data)
        else:
            return render_template("registration.html", data={'type': 'login'})
    except Exception as ex:
        print("Code Error: {}".format(ex))

@obj.route('/forgot', methods=['GET', 'POST'])
def forgot_password():
    try:
        if request.method == 'POST':
            email = request.form['email'].casefold()
            query = "SELECT * FROM registrations WHERE email = '{}';".format(email)
            mysql_cursor = db_obj.connection.cursor(MySQLdb.cursors.DictCursor)
            mysql_cursor.execute(query)
            data = mysql_cursor.fetchone()
            mysql_cursor.close()
            if data:
                # Send verification link
                send_password_reset_link(f"{data['first_name']} {data['last_name']}", email, data['id'])
                flash('Reset Password link has been sent to your email.')
            else:
                # Not found
                flash('Your email is not registered with us.')
    except Exception as ex:
        print("Code Error: {}".format(ex))
    return render_template("password_request.html")

@obj.route('/reset/<int:id>/<string:expiry_date>', methods=['GET', 'POST'])
def reset(id, expiry_date):
    try:
        data = {}
        data['id'] = id
        data['expiry_date'] = expiry_date
        if request.method == 'POST':
            retype_password = hashlib.sha512(request.form['retype_password'].encode()).hexdigest()
            new_password = hashlib.sha512(request.form['new_password'].encode()).hexdigest()
            if retype_password != new_password:
                flash('New password and repeat password is not same.')
                data['my_id'] = request.form['my_id']
                return render_template('reset_password.html', data=data)
            else:
                query = "UPDATE registrations SET password = '{}' WHERE id = {}".format(new_password, request.form['my_id'])
                mysql_cursor = db_obj.connection.cursor(MySQLdb.cursors.DictCursor)
                mysql_cursor.execute(query)
                data = mysql_cursor.fetchone()
                mysql_cursor.close()
                db_obj.connection.commit()
                flash('Your new password is updated.')
                return redirect(url_for('index'))
        registration_id = id
        expiry_date_decode = base64.b64decode(expiry_date.encode('ascii')).decode('ascii')
        expiry_date_in_format = datetime.strptime(expiry_date_decode, "%Y-%m-%d %H:%M:%S")
        now_date = datetime.now()
        if now_date <= expiry_date_in_format:
            data['my_id'] = registration_id
            return render_template('reset_password.html', data=data)
        else:
            flash("Link is expired. Please request once again from forgot password.")
    except Exception as ex:
        print("Code Error: {}".format(ex))

@obj.route('/history', methods=['GET', 'POST'])
def history():
    data = {}
    try:
        if session['unique_id'] is None:
            return redirect(url_for('index'))
    except Exception as ex:
        return redirect(url_for('index'))
    query = "SELECT * FROM login_history WHERE registration_id = {} ORDER BY signout_date".format(session['my_id'])
    mysql_cursor = db_obj.connection.cursor(MySQLdb.cursors.DictCursor)
    mysql_cursor.execute(query)
    data['records'] = mysql_cursor.fetchall()
    mysql_cursor.close()
    data['history_id'] = session['history_id']
    data['my_id'] = session['my_id']
    return render_template("login_history.html", data=data)

@obj.route('/change_pass', methods=['GET', 'POST'])
def change_pass():
    try:
        if session['unique_id'] is None:
            return redirect(url_for('index'))
    except Exception as ex:
        return redirect(url_for('index'))
    params = {}
    params['history_id'] = session['history_id']
    params['my_id'] = session['my_id']
    if request.method == 'POST':
        old_password = hashlib.sha512(request.form['old_password'].encode()).hexdigest()
        new_password = hashlib.sha512(request.form['new_password'].encode()).hexdigest()
        repeat_password = hashlib.sha512(request.form['repeat_password'].encode()).hexdigest()
        if new_password != repeat_password:
            flash('New password and repeat password is not same.')
            return render_template("change_password.html")
        query = "SELECT * FROM registrations WHERE id = {} AND password = '{}'".format(session['my_id'], old_password)
        mysql_cursor = db_obj.connection.cursor(MySQLdb.cursors.DictCursor)
        mysql_cursor.execute(query)
        data = mysql_cursor.fetchone()
        mysql_cursor.close()
        if data:
            # Change password
            query = "UPDATE registrations SET password = '{}' WHERE id = {}".format(new_password, session['my_id'])
            mysql_cursor = db_obj.connection.cursor(MySQLdb.cursors.DictCursor)
            mysql_cursor.execute(query)
            data = mysql_cursor.fetchone()
            mysql_cursor.close()
            db_obj.connection.commit()
            flash('Your new password is updated.')
        else:
            # Old password is incorrect
            flash('Old Password is invalid. Please try again.')
    return render_template("change_password.html", data=params)

@obj.route('/signout', methods=['GET', 'POST'])
def signout():
    if session['unique_id'] is None:
        redirect('index')
    query = "UPDATE login_history SET signout_date='{}',login_status={} WHERE history_id={}".format(datetime.today(), 2, session['history_id'])
    mysql_cursor = db_obj.connection.cursor(MySQLdb.cursors.DictCursor)
    mysql_cursor.execute(query)
    db_obj.connection.commit()
    mysql_cursor.close()
    session['history_id'] = None
    session['my_full_name'] = None
    session['my_id'] = None
    session['unique_id'] = None
    return redirect(url_for('index'))

def get_last_history_id():
    query = "SELECT history_id FROM login_history ORDER BY 1 DESC LIMIT 1;"
    mysql_cursor = db_obj.connection.cursor(MySQLdb.cursors.DictCursor)
    mysql_cursor.execute(query)
    db_obj.connection.commit()
    mysql_cursor.close()

@socketio.on('connect')
def test_connect():
    emit('get_client_data',  {'data':'get_client_data'})

@socketio.on('update_my_socket_id')
def my_socket_id(data):
    socket_id = request.sid
    history_id = data['history_id']
    my_id = data['my_id']
    query = "UPDATE login_history SET socket_id='{}' WHERE history_id={}".format(socket_id, history_id)
    mysql_cursor = db_obj.connection.cursor(MySQLdb.cursors.DictCursor)
    mysql_cursor.execute(query)
    db_obj.connection.commit()
    mysql_cursor.close()
    signout_socket_ids = get_already_logged_in_socket_ids(my_id, history_id)
    for signout_socket_id in signout_socket_ids:
        emit('signout_from_system', to=signout_socket_id)
    print(f"signout_socket_ids - {signout_socket_ids}")
    print(f"data - {history_id}, {my_id}")

@socketio.on('signout_me')
def signout_from_system(data):
    history_id = data['history_id']
    query = "UPDATE login_history SET signout_date='{}',login_status={} WHERE history_id={}".format(datetime.today(), 2, history_id)
    mysql_cursor = db_obj.connection.cursor(MySQLdb.cursors.DictCursor)
    mysql_cursor.execute(query)
    db_obj.connection.commit()
    mysql_cursor.close()
    session['history_id'] = None
    session['my_full_name'] = None
    session['my_id'] = None
    session['unique_id'] = None

if __name__ == '__main__':
    socketio.run(obj, debug=True, host="127.0.0.1", port="5000")
