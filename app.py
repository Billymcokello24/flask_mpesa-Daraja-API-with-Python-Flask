# app.py
import base64
import io
from datetime import datetime
from decimal import Decimal

import yagmail
from PIL import Image
from africastalking.AfricasTalkingGateway import AfricasTalkingGateway, AfricasTalkingGatewayException
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, json, flash
from flask_mail import Mail, Message
from flask_mysqldb import MySQL
from flask_socketio import SocketIO, emit

import MySQLdb.cursors
import MySQLdb.cursors, re, hashlib
from werkzeug.security import generate_password_hash
from flask_mpesa import MpesaAPI

app = Flask(__name__)
mpesa_api = MpesaAPI(app)

app = Flask(__name__)
app.secret_key = 'your secret key'
socketio = SocketIO(app)

# Enter your database connection details below
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Billy39016716...'
app.config['MYSQL_DB'] = 'RuralConnect'


app.config['MPESA_CONSUMER_KEY'] = 'QqHG2xa0RNXMIUn5TnkHg0Ecq6cuR5qiH6I8qDh2OAN7UI7G'
app.config['MPESA_CONSUMER_SECRET'] = '5ArztdLSBmqSiHPLcOMYuc23pT8qr1RhnXZGEuVkm5AmCZxwu79LGl8BiOGd1lcM'
app.config['MPESA_SHORTCODE'] = 'your_shortcode'
app.config['MPESA_PASSKEY'] = 'Billy39016716#'
app.config['MPESA_CALLBACK_URL'] = 'localhost:5000/paid'






mail = Mail(app)

username = "RuralConnect"
api_key = "d811c9c7b262a131121d328f5b5d36220f0da1c1034bc6e788cc410b1b6d9442"
phone_number = "+254759814390"



gmail_username = "cloudpioneercodinghub@gmail.com"
gmail_app_password = "eeip dvha lgwn qrtj"
yag = yagmail.SMTP(gmail_username, gmail_app_password)

# Intialize MySQL
mysql = MySQL(app)

from collections import defaultdict


@app.route('/')
def home():
    return render_template('index.html')


@socketio.on('service_added')
def handle_service_added(data):
    # Broadcast new service to all clients
    socketio.emit('new_service', data, broadcast=True)




@app.route("/client_dashboard/add_tokens/process_payment", methods=["POST"])
def process_payment():
    if request.method == 'POST':
        phone_number = request.form['phonenumber']
        amount = request.form['Amount']

        # Initiate M-Pesa payment
        response = mpesa_api.customer_to_business(
            phone_number=phone_number,
            amount=amount,
            account_reference='Payment for tokens',
            transaction_desc='Purchase of tokens'
        )

        if response.get('ResponseCode') == '0':
            # Payment successful
            flash('Payment successful!', 'success')
        else:
            # Payment failed
            flash('Payment failed. Please try again.', 'error')

    return redirect(url_for('add_tokens'))





import requests
@app.route("/client_dashboard/add_tokens", methods=["GET", "POST"])
def add_tokens():
    if request.method == 'POST':
        id_number = request.form[
            'id_number']  # Assuming you have a function to retrieve the id_number of the logged-in user
        phone_number = request.form['phonenumber']
        amount = request.form['Amount']

        # Create cursor
        cur = mysql.connection.cursor()

        # Insert data into the add_tokens table
        cur.execute(
            "INSERT INTO add_tokens (id_number, phonenumber, Amount) VALUES (%s, %s, %s)",
            (id_number, phone_number, amount)
        )
        mysql.connection.commit()

        # Retrieve all records from the add_tokens table for the logged-in user
        cur.execute(
            "SELECT id_number, SUM(Amount) FROM add_tokens GROUP BY id_number"
        )
        user_tokens_data = cur.fetchall()

        # Dictionary to store aggregated user token amounts
        aggregated_tokens = defaultdict(int)
        for row in user_tokens_data:
            aggregated_tokens[row[0]] += row[1]

        # Clear existing data from user_tokens table
        cur.execute("DELETE FROM user_tokens")

        # Insert aggregated data into user_tokens table
        for id_number, total_amount in aggregated_tokens.items():
            cur.execute(
                "INSERT INTO user_tokens (id_number, Amount) VALUES (%s, %s)",
                (id_number, total_amount)
            )
        mysql.connection.commit()

        # Close connection
        cur.close()

    return render_template("Pages/add_tokens.html")

@app.route('/client_dashboard/chats')
def chat():
    # Fetch profiles of the service provider and the client from the database
    provider_profile = 'Billy'  # Implement this function to fetch provider profile
    client_profile = 'Patrick'  # Implement this function to fetch client profile

    return render_template('Pages/chat.html', provider_name=provider_profile, client_name=client_profile)


from flask import request

from flask import request


@app.route("/client_dashboard/pay", methods=["POST"])
def process_payments():
    if request.method == 'POST':
        service_id = request.form['service_id']  # Assuming you have a way to get the service_id
        amount_payable = request.form['Amount_Payable']  # Assuming you have a way to get the Amount_Payable

        # Deduct Amount_Payable from the user's Amount in user_tokens table
        cur = mysql.connection.cursor()
        cur.execute(
            "UPDATE user_tokens SET Amount = Amount - %s WHERE id_number = %s",
            (amount_payable, get_id())
        )
        mysql.connection.commit()

        # Update received table with id_number and deducted amount
        cur.execute(
            "INSERT INTO received (id_number, service_id,Amount) VALUES (%s,%s, %s)",
            (get_id(), service_id, amount_payable)
        )
        mysql.connection.commit()

        cur.close()

    return redirect(url_for('dashboard'))  # Redirect to the dashboard after payment


def count_bookings(id_number):
    try:
        # Connect to the database
        cursor = mysql.connection.cursor()

        # Query to count the number of bookings for the specific user
        cursor.execute("SELECT COUNT(*) FROM book_service WHERE id_number = %s", (id_number,))
        booking_count = cursor.fetchone()[0]

        # Close the cursor
        cursor.close()

        return booking_count
    except Exception as e:
        # Handle any exceptions, such as database errors
        print("Error counting bookings:", e)
        return 0  # Return 0 if an error occurs


def my_service_count(id_number):
    try:
        # Connect to the database
        cursor = mysql.connection.cursor()

        # Query to count the number of bookings for the specific user
        cursor.execute("SELECT COUNT(*) FROM services WHERE id_number = %s", (id_number,))
        booking_count = cursor.fetchone()[0]

        # Close the cursor
        cursor.close()

        return booking_count
    except Exception as e:
        # Handle any exceptions, such as database errors
        print("Error counting bookings:", e)
        return 0  # Return 0 if an error occurs


def service_counts():
    try:
        # Connect to the database
        cursor = mysql.connection.cursor()

        # Query to count available services
        cursor.execute("SELECT COUNT(*) FROM services")

        # Fetch the count
        service_count = cursor.fetchone()[0]

        # Close the cursor
        cursor.close()

        # Render the dashboard template with the service count
        return service_count
    except Exception as e:
        # Handle any exceptions, such as database errors
        return str(e)


def show_service():
    try:
        # Connect to the database
        cursor = mysql.connection.cursor()

        # Query to count available services
        cursor.execute("SELECT * FROM services")

        # Fetch the count
        services = cursor.fetchall()

        # Close the cursor
        cursor.close()

        # Render the dashboard template with the service count
        return services
    except Exception as e:
        # Handle any exceptions, such as database errors
        return str(e)


def booking_counts():
    try:
        # Connect to the database
        cursor = mysql.connection.cursor()

        # Query to count available services
        cursor.execute("SELECT COUNT(*) FROM book_service")

        # Fetch the count
        book_count = cursor.fetchone()[0]

        # Close the cursor
        cursor.close()

        # Render the dashboard template with the service count
        return book_count
    except Exception as e:
        # Handle any exceptions, such as database errors
        return str(e)


def send_sms_notification(to_phone_number):
    try:
        gateway = AfricasTalkingGateway(username, api_key)
        # Send notification to the service provider
        message = (
            f"Hello ! Someone is interested in your service. "
        )
        recipients = [to_phone_number]
        gateway.sendMessage(recipients, message)

        return True
    except AfricasTalkingGatewayException as e:
        print(f"Error sending SMS: {e}")
        return False


def send_email_notification(email):
    try:
        # Compose email
        subject = "New Booking Notification"
        body = f"Hello,\n\nYour Booking is successfully recieved. The service Provider will get to you shortly.\n\nRegards,\n RuralConnect Admin"

        # Send email
        yag.send(email, subject, body)

        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def send_email_notification_provider(email):
    try:
        # Compose email
        subject = "Confirmation Email"
        body = (f"Hello,\n\nThanks for booking a service with us. \n\n "
                f"It was nice service you.Keep connected to RuralConnect for more services\n\nRegards,\n RuralConnect Admin")

        # Send email
        yag.send(email, subject, body)

        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def client_screen():
    # Fetch uploaded service data from the database
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM services")
    services = cursor.fetchall()
    cursor.close()
    return render_template('services.html', services=services)


@app.route('/provider_screen')
def providers_screen():
    try:
        # Connect to the database
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Query to fetch all services
        cursor.execute("SELECT * FROM services")

        # Fetch all services
        services = cursor.fetchall()

        # Close the cursor
        cursor.close()

        # Convert images to base64 strings
        for service in services:
            image_path = service['image']
            if image_path:  # Ensure there is a valid image path
                with open(image_path, 'rb') as f:
                    img = Image.open(f)
                    img_byte_array = io.BytesIO()
                    img.save(img_byte_array, format=img.format)
                    img_base64 = base64.b64encode(img_byte_array.getvalue()).decode('utf-8')
                    service['image_base64'] = img_base64

        return render_template('Pages/my_services.html', services=services)

    except Exception as e:
        return str(e)


@socketio.on('service_added')
def handle_service_added(data):
    # Broadcast new service to all clients
    socketio.emit('new_service', data, broadcast=True)


@app.route('/upload_service')
def upload_service():
    return render_template('Pages/upload.html')


@app.route("/services/<category>")
def services_by_category(category):
    try:
        # Fetch services from the database based on the selected category
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM services WHERE category = %s", (category,))
        services = cur.fetchall()
        cur.close()

        for service in services:
            with open(service['image'], "rb") as img_file:
                service['image_base64'] = base64.b64encode(img_file.read()).decode('utf-8')

        # Render HTML template with the fetched services
        return render_template('Pages/services_by_category.html', services=services, category=category)
    except Exception as e:
        return str(e)


@app.route('/add_service', methods=['POST', 'GET'])
def add_service():
    if request.method == 'POST':
        # Fetch form data
        service_id = request.form['service_id']
        image = request.files['image']
        name = request.form['name']
        category = request.form['category']
        description = request.form['description']
        Amt = request.form['Amount']
        email = request.form['email']
        phonenumber = request.form['phonenumber']
        location = request.form['location']
        status = request.form['status']

        # Save image to a location or store its path in the database
        # For simplicity, let's assume we're saving the image to a folder named "uploads" in the same directory
        image_path = f"templates/Pages/uploads/{image.filename}"
        image.save(image_path)

        try:
            cur = mysql.connection.cursor()
            cur.execute(
                "INSERT INTO services (service_id,image, name, category, description,Amount, email, phonenumber, location, status) VALUES (%s,%s,%s, %s, %s, %s, %s, %s, %s, %s)",
                (service_id, image_path, name, category, description, Amt, email, phonenumber, location, status))
            mysql.connection.commit()
            cur.close()

            socketio.emit('new_service_notification', {'message': 'A new service has been added!'})

            # Check if the category table exists, if not create it
            category = category.replace(' ', '_')
            cur = mysql.connection.cursor()
            cur.execute(f"SHOW TABLES LIKE '{category}'")
            result = cur.fetchone()
            if not result:
                # Create the category table
                cur.execute(
                    f"CREATE TABLE {category} (id INT AUTO_INCREMENT PRIMARY KEY, service_id VARCHAR(255), image BLOB, name VARCHAR(255),  description TEXT, Amount VARCHAR(255), email VARCHAR(255), phonenumber VARCHAR(255), location VARCHAR(255), status VARCHAR(255))")
            cur.close()

            # Insert data into the category table
            cur = mysql.connection.cursor()
            cur.execute(
                f"INSERT INTO {category} (service_id,image, name,  description,Amount, email, phonenumber, location, status) VALUES (%s,%s, %s, %s, %s, %s, %s, %s, %s)",
                (service_id, image_path, name, description, Amt, email, phonenumber, location, status))
            mysql.connection.commit()
            cur.close()

            return render_template("Pages/upload.html")
        except MySQLdb.Error as e:
            # Handle MySQL errors
            return str(e)
        except Exception as e:
            # Handle other exceptions
            return str(e)
    return render_template("Pages/upload.html")


@app.route('/provider/bookings')
def provider_bookings():
    try:

        # Fetch all bookings from the book_service table
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM book_service")
        bookings = cur.fetchall()
        cur.close()

        # Render the provider's bookings screen with the fetched data
        return render_template('Pages/provider_booking.html', bookingss=bookings)
    except Exception as e:
        return str(e)


@app.route('/client_dashboard/check_payments')
def client_payments():
    try:
        id_number = get_id()
        # Fetch all bookings from the book_service tablepy
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM received WHERE id_number = %s", (id_number,))
        payments = cur.fetchall()
        cur.close()

        # Render the provider's bookings screen with the fetched data
        return render_template('Pages/client_payments.html', client_payments=payments)
    except Exception as e:
        return str(e)


@app.route('/provider/check_payments')
def check_payments():
    return render_template("Pages/payments.html")


@app.route('/provider/payments')
def my_payments():
    try:

        # Fetch all bookings from the book_service table
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM received")
        payments = cur.fetchall()
        cur.close()

        # Render the provider's bookings screen with the fetched data
        return render_template('Pages/Payments.html', payments=payments)
    except Exception as e:
        return str(e)


@app.route('/mark_done', methods=['POST', 'GET'])
def mark_done():
    if request.method == 'POST':
        # Fetch form data

        service_id = request.form['service_id']
        name = request.form['name']
        email = request.form['email']
        Email = get_email()
        phone_number = request.form['phonenumber']

        try:
            # Create cursor
            cur = mysql.connection.cursor()

            # Insert data into the database
            cur.execute(
                "INSERT INTO mark_done (service_id,name,email, phonenumber) VALUES ( %s, %s, %s, %s)",
                (service_id, name, email, phone_number))

            cur.execute("DELETE FROM book_service WHERE service_id = %s", (service_id,))

            # Commit to DB
            mysql.connection.commit()

            # Fetch service provider's email and phone number from the database
            # Fetch service provider's email and phone number from the database
            # Fetch service provider's email and phone number from the database
            cur.execute("SELECT email, phonenumber FROM services")
            service_provider_info = cur.fetchone()
            service_provider_email = service_provider_info[0]  # Access email by index 0
            service_provider_phonenumber = service_provider_info[1]  # Access phone number by index 1

            # Close connection
            cur.close()

            # Send SMS notification to both client and service provider
            send_sms_notification(phone_number)
            send_sms_notification(service_provider_phonenumber)
            # Send email notification to both client and service provider
            send_email_notification_provider(Email)
            send_email_notification_provider(service_provider_email)


        except Exception as e:
            return str(e)

    return render_template("Pages/mark_done.html")


def get_email():
    if 'loggedin' in session:
        try:
            # Connect to the database
            cursor = mysql.connection.cursor()

            # Retrieve the id_number of the logged-in user using their username
            cursor.execute("SELECT email FROM Auth WHERE username = %s", (session['username'],))
            id_number = cursor.fetchone()[0]  # Assuming username is unique, fetch the first result

            # Close the cursor
            cursor.close()

            return id_number
        except Exception as e:
            # Handle any exceptions, such as database errors
            print("Error fetching email:", e)
            return None  # Return None if an error occurs
    else:
        return None  # Return None if the user is not logged in


@app.route('/book_service', methods=['POST', 'GET'])
def book_service():
    if request.method == 'POST':
        # Fetch form data
        id_no = request.form['id_number']
        service_id = request.form['service_id']
        service_name = request.form['service_booked']
        amount_payable = request.form['Amount_Payable']
        name = request.form['name']
        client_email = request.form['email']
        client_phonenumber = request.form['phonenumber']
        location = request.form['location']
        urgency = request.form['urgency']

        try:
            # Create cursor
            cur = mysql.connection.cursor()

            # Insert data into the database
            cur.execute(
                "INSERT INTO book_service (id_number,service_id,service_booked,Amount_Payable,name, email, "
                "phonenumber, location, urgency) VALUES (%s,%s,%s,%s,%s, %s, %s, %s, %s)",
                (id_no, service_id, service_name, amount_payable, name, client_email, client_phonenumber, location,
                 urgency))

            # Commit to DB
            mysql.connection.commit()

            # Fetch service provider's email and phone number from the database
            # Fetch service provider's email and phone number from the database
            # Fetch service provider's email and phone number from the database
            cur.execute("SELECT email, phonenumber FROM services")
            service_provider_info = cur.fetchone()
            service_provider_email = service_provider_info[0]  # Access email by index 0
            service_provider_phonenumber = service_provider_info[1]  # Access phone number by index 1

            # Close connection
            cur.close()

            # Send SMS notification to both client and service provider
            send_sms_notification(client_phonenumber)
            send_sms_notification(service_provider_phonenumber)
            # Send email notification to both client and service provider
            send_email_notification(client_email)
            send_email_notification(service_provider_email)

        except Exception as e:
            return str(e)

    return render_template("Pages/book_service.html")


@app.route('/Available_bookings')
def available_bookings():
    return render_template('Pages/provider_booking.html')


@app.route('/my_services')
def my_services():
    return render_template('Pages/my_services.html')


@app.route('/delete_service', methods=['POST'])
def delete_service():
    if request.method == 'POST':
        # Fetch service ID from the form data
        service_id = request.form['service_id']

        try:
            # Create cursor
            cur = mysql.connection.cursor()

            # Delete associated records in the mark_done table
            cur.execute("DELETE FROM mark_done WHERE service_id = %s", (service_id,))

            # Then, delete the service from the services table
            cur.execute("DELETE FROM services WHERE service_id = %s", (service_id,))

            # Commit to DB
            mysql.connection.commit()

            # Close connection
            cur.close()

            # Redirect to the provider screen after deletion
            return redirect(url_for('providers_screen'))

        except Exception as e:
            # Handle any exceptions, such as database errors
            return str(e)


@app.route('/bookings_page')
def bookings():
    return render_template('Pages/bookings.html')


@app.route('/client_screen')
def client_screen():
    try:
        # Connect to the database
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Query to fetch all services
        cursor.execute("SELECT * FROM services")

        # Fetch all services
        services = cursor.fetchall()

        # Close the cursor
        cursor.close()

        # Convert images to base64 strings
        for service in services:
            image_path = service['image']
            if image_path:  # Ensure there is a valid image path
                with open(image_path, 'rb') as f:
                    img = Image.open(f)
                    img_byte_array = io.BytesIO()
                    img.save(img_byte_array, format=img.format)
                    img_base64 = base64.b64encode(img_byte_array.getvalue()).decode('utf-8')
                    service['image_base64'] = img_base64

        # Render the client screen template with the services data
        return render_template('Pages/services.html', services=services)

    except Exception as e:
        return str(e)


@app.route('/display_service_providers')
def display_service_providers():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM services')
        providers = cursor.fetchall()
        return render_template("services.html", providers=providers)
    return redirect(url_for('login'))


def get_username_from_db_client():
    if 'username' in session:
        cur = mysql.connection.cursor()
        cur.execute("SELECT username FROM Auth WHERE username = %s", (session['username'],))
        username = cur.fetchone()[0]  # Assuming username is unique
        cur.close()
        return username
    return None


@app.route('/book')
def book():
    return render_template("Pages/book_service.html")


@app.route('/client_sign_out')
def sign_out_client():
    session.pop('username')
    return redirect(url_for('login'))


@app.route('/provider_sign_out')
def sign_out_provider():
    session.pop('username')
    return redirect(url_for('provider_login'))


@app.route("/update", methods=['GET', 'POST'])
def updateClient():
    msg = ''
    if 'loggedin' in session:
        if request.method == 'POST' and 'name' in request.form and 'email' in request.form and 'username' in request.form and 'password' in request.form:
            username = request.form['username']
            password = request.form['password']
            email = request.form['email']
            name = request.form['name']
            profile_image = request.form['profile_image']
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute(
                'SELECT * FROM Auth WHERE username = % s',
                (username,))
            account = cursor.fetchone()
            if account:
                msg = 'Account already exists !'
            elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
                msg = 'Invalid email address !'
            elif not re.match(r'[A-Za-z0-9]+', username):
                msg = 'name must contain only characters and numbers !'
            else:
                cursor.execute('UPDATE accounts SET username =% s,\
                password =% s, email =% s, organisation =% s, \
                address =% s, city =% s, state =% s, \
                country =% s, postalcode =% s WHERE id =% s', (
                    username, password, email, name,
                    profile_image,
                    (session['id'],),))
                mysql.connection.commit()
                msg = 'You have successfully updated !'
                return render_template("Pages/userProfile.html", msg=msg)
        elif request.method == 'POST':
            msg = 'Please fill out the form !'
        return render_template("Pages/userProfile.html", msg=msg)
    return redirect(url_for('login'))


@app.route('/display_client')
def display1():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM Auth WHERE id = % s',
                       (session['id'],))
        Auth = cursor.fetchone()
        return render_template("Pages/userProfile.html", Auth=Auth)
    return redirect(url_for('login'))


@app.route('/display_provider')
def display2():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM provider_auth WHERE id = % s',
                       (session['id'],))
        provider = cursor.fetchone()
        return render_template("Pages/providerProfile.html", provider=provider)
    return redirect(url_for('provider_login'))


@app.route('/login/home')
def dashboard():
    if 'loggedin' in session:
        id_number = get_id()
        username = get_username_from_db_client()
        count = service_counts()  # Assuming this function fetches the total count of services

        # Fetch sum of tokens for the logged-in user from user_tokens table
        if id_number:
            cur = mysql.connection.cursor()
            cur.execute("SELECT Amount FROM user_tokens WHERE id_number = %s", (id_number,))
            token_sum = cur.fetchone()
            cur.close()
            if token_sum:
                token_sum = token_sum[0]
            else:
                token_sum = 0
            booking_count = count_bookings(id_number)
            return render_template('dashboard/index.html', Username=username, booking_count=booking_count,
                                   service_count=count, token_sum=token_sum)
        else:
            flash('Failed to retrieve user information.', 'error')
            return render_template('dashboard/index.html', Username=username, service_count=count)
    else:
        # User is not logged in, redirect to the login page
        return redirect(url_for('login'))


def get_id_provider():
    if 'loggedin' in session:
        try:
            # Connect to the database
            cursor = mysql.connection.cursor()

            # Retrieve the id_number of the logged-in user using their username
            cursor.execute("SELECT id_number FROM provider_auth WHERE username = %s", (session['username'],))
            id_number = cursor.fetchone()[0]  # Assuming username is unique, fetch the first result

            # Close the cursor
            cursor.close()

            return id_number
        except Exception as e:
            # Handle any exceptions, such as database errors
            print("Error fetching id_number:", e)
            return None  # Return None if an error occurs


@app.route('/my_services')
def my_servicess():
    if 'loggedin' in session:
        try:
            # Get the id_number of the logged-in user
            id_number = get_id_provider()

            if id_number:
                # Connect to the database
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

                # Query to fetch bookings for the logged-in user
                cursor.execute("SELECT * FROM services WHERE id_number = %s", (id_number,))
                services = cursor.fetchall()

                # Close the cursor
                cursor.close()

                # Render the template with the bookings data
                return render_template('Pages/my_services.html', servicess=services)
            else:
                flash('Failed to retrieve user information.', 'error')
                return redirect(url_for('login'))
        except Exception as e:
            # Handle database errors
            flash('Error retrieving bookings: ' + str(e), 'error')
            return redirect(url_for('login'))
    else:
        # If user is not logged in, redirect to login page
        return redirect(url_for('login'))


@app.route('/my_bookings')
def my_bookings():
    if 'loggedin' in session:
        try:
            # Get the id_number of the logged-in user
            id_number = get_id()

            if id_number:
                # Connect to the database
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

                # Query to fetch bookings for the logged-in user
                cursor.execute("SELECT * FROM book_service WHERE id_number = %s", (id_number,))
                bookings = cursor.fetchall()

                # Close the cursor
                cursor.close()

                # Render the template with the bookings data
                return render_template('Pages/my_bookings.html', bookings=bookings)
            else:
                flash('Failed to retrieve user information.', 'error')
                return redirect(url_for('login'))
        except Exception as e:
            # Handle database errors
            flash('Error retrieving bookings: ' + str(e), 'error')
            return redirect(url_for('login'))
    else:
        # If user is not logged in, redirect to login page
        return redirect(url_for('login'))


@app.route('/delete_booking', methods=['POST'])
def delete_booking():
    if request.method == 'POST':
        # Fetch service ID from the form data
        service_id = request.form['service_id']

        try:
            # Create cursor
            cur = mysql.connection.cursor()

            # Delete associated records in the mark_done table
            cur.execute("DELETE FROM book_service WHERE service_id = %s", (service_id,))

            # Then, delete the service from the services table
            cur.execute("DELETE FROM book_service WHERE service_id = %s", (service_id,))

            # Commit to DB
            mysql.connection.commit()

            # Close connection
            cur.close()

            # Redirect to the provider screen after deletion
            return redirect(url_for('my_bookings'))

        except Exception as e:
            # Handle any exceptions, such as database errors
            return str(e)


def get_id():
    if 'loggedin' in session:
        try:
            # Connect to the database
            cursor = mysql.connection.cursor()

            # Retrieve the id_number of the logged-in user using their username
            cursor.execute("SELECT id_number FROM Auth WHERE username = %s", (session['username'],))
            id_number = cursor.fetchone()[0]  # Assuming username is unique, fetch the first result

            # Close the cursor
            cursor.close()

            return id_number
        except Exception as e:
            # Handle any exceptions, such as database errors
            print("Error fetching id_number:", e)
            return None  # Return None if an error occurs
    else:
        return None  # Return None if the user is not logged in


def get_username_from_db_client():
    if 'username' in session:
        cur = mysql.connection.cursor()
        cur.execute("SELECT username FROM Auth WHERE username = %s", (session['username'],))
        username = cur.fetchone()[0]  # Assuming username is unique
        cur.close()
        return username
    return None


def get_username_from_db_provider():
    if 'username' in session:
        cur = mysql.connection.cursor()
        cur.execute("SELECT username FROM provider_auth WHERE username = %s", (session['username'],))
        username = cur.fetchone()[0]  # Assuming username is unique
        cur.close()
        return username
    return None


@app.route("/provider_dashboard/Home")
def provider_dashboard():
    # Get counts and username
    counts = booking_counts()
    service_countsss = service_counts()
    username = get_username_from_db_provider()

    if username:
        # Fetch the sum of received amounts from the database
        cur = mysql.connection.cursor()
        cur.execute("SELECT SUM(Amount) FROM received")
        total_received = cur.fetchone()[0]
        cur.close()

        # Pass the total_received to the template
        return render_template('provider/provider_dashboard.html',
                               Username=session['username'],
                               counts=counts,
                               service_countsss=service_countsss,
                               total_received=total_received)
    else:
        return redirect(url_for('provider_login'))

    return redirect(url_for('provider_login'))


@app.route('/login/', methods=['GET', 'POST'])
def login():
    # Output a message if something goes wrong...
    msg = ''
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM Auth WHERE username = %s AND password = %s', (username, password,))
        # Fetch one record and return result
        account = cursor.fetchone()
        # If account exists in accounts table in out database
        if account:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            msg = 'Logged in successfully !'
            return redirect(url_for('dashboard'))
        else:
            # Account doesn't exist or username/password incorrect
            msg = 'Incorrect username/password!'
    # Show the login form with message (if any)

    return render_template('login.html', success_message=msg)


@app.route("/contact")
def contact():
    return render_template('contact.html')


@app.route("/login/register", methods=['GET', 'POST'])
def register():
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'id_number' in request.form and 'name' in request.form and 'email' in request.form and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        id_number = request.form['id_number']
        name = request.form['name']
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM Auth WHERE username = %s', (username,))
        account = cursor.fetchone()
        # If account exists show error and validation checks
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            # Hash the password
            # Account doesn't exist, and the form data is valid, so insert the new account into the accounts table
            cursor.execute('INSERT INTO Auth (id_number, name, email, username, password) VALUES (%s, %s, %s, %s, %s)',
                           (id_number, name, email, username, password,))
            mysql.connection.commit()
            msg = 'You have successfully registered!'
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'

    return render_template('pages-register.html', msg=msg)


@app.route('/provider_login/', methods=['GET', 'POST'])
def provider_login():
    # Output a message if something goes wrong...
    msg = ''
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM provider_auth WHERE username = %s AND password = %s', (username, password,))
        # Fetch one record and return result
        account = cursor.fetchone()
        # If account exists in accounts table in out database
        if account:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            msg = 'Logged in successfully !'
            return redirect(url_for('provider_dashboard', msg=msg))
        else:
            # Account doesn't exist or username/password incorrect
            msg = 'Incorrect username/password!'
    # Show the login form with message (if any)

    return render_template('provider/provider_login.html', msg=msg)


@app.route("/provider_login/provider_register", methods=['GET', 'POST'])
def provider_register():
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'id_number' in request.form and 'name' in request.form and 'email' in request.form and 'service' in request.form and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        id_number = request.form['id_number']
        service = request.form['service']
        name = request.form['name']
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM provider_auth WHERE username = %s', (username,))
        account = cursor.fetchone()
        # If account exists show error and validation checks
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            # Hash the password
            # Account doesn't exist, and the form data is valid, so insert the new account into the accounts table
            cursor.execute(
                'INSERT INTO provider_auth (id_number, name, email, service, username, password) VALUES (%s,%s,%s,%s,%s, %s)',
                (id_number, name, email, service, username, password,))
            mysql.connection.commit()
            msg = 'You have successfully registered!, now login'
            return redirect(url_for('provider_login', msg=msg))


    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'

    return render_template('provider/provider_register.html', msg=msg)


@app.route("/about/")
def about():
    return render_template('about.html')


@app.route("/services")
def services():
    return render_template('services.html')


@app.route("/Bookings")
def Bookings():
    return render_template('bookings.html')


@app.route("/details")
def details():
    return render_template('bookingsDetails.html')


@app.route("/Payments")
def Payments():
    return render_template('team.html')


@app.route("/blog")
def blog():
    return render_template('blog.html')


@app.route("/payment")
def payment():
    return render_template('payments.html')


@app.route("/beauty")
def beauty():
    return render_template('Services/beauty.html')


@app.route("/plumbing")
def plumbing():
    return render_template('Services/Plumbing.html')


@app.route("/Carpentry")
def carpentry():
    return render_template('Services/capentry.html')


@app.route("/education")
def education():
    return render_template('Services/education.html')


@app.route("/veterinary")
def veterinary():
    return render_template('Services/veterinary.html')


@app.route("/userProfile")
def userProfile():
    return render_template('Pages/userProfile.html')


@app.route("/providerProfile")
def providerProfile():
    return render_template('Pages/providerProfile.html')


@app.route("/available_services")
def available_services():
    return render_template('Pages/services.html')


if __name__ == '__main__':
    socketio.run(app, debug=True)
