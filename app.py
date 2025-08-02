from flask import Flask, render_template, request, redirect, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)

app.secret_key = '1234ab'


UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
@app.route('/')
def landing_page():
    return render_template('landing.html')

@app.route('/chef/signup', methods=['GET', 'POST'])
def chef_signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO chefs (name, email, password) VALUES (?, ?, ?)", (name, email, password))
            conn.commit()
            flash("Signup successful! Please log in.", "success")
            return redirect('/chef/login')
        except:
            flash("Email already exists.", "danger")
        finally:
            conn.close()
    return render_template('chef_signup.html')
@app.route('/chef/login', methods=['GET', 'POST'])
def chef_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM chefs WHERE email = ?", (email,))
        chef = c.fetchone()
        conn.close()

        if chef and check_password_hash(chef[3], password):
            session['chef_id'] = chef[0]
            flash("Login successful!", "success")
            return redirect('/chef/dashboard')
        else:
            flash("Invalid email or password.", "danger")
    return render_template('chef_login.html')
@app.route('/chef/dashboard')
def chef_dashboard():
    if 'chef_id' not in session:
        return redirect('/chef/login')
    return render_template('chef_dashboard.html')
@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect('/chef/login')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/chef/upload', methods=['GET', 'POST'])
def upload_dish():
    if 'chef_id' not in session:
        return redirect('/chef/login')

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        prep_time = request.form['prep_time']
        image = request.files.get('image')

        if image and allowed_file(image.filename):
            image_filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))

            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO dishes (chef_id, name, description, price, prep_time, image_filename)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (session['chef_id'], name, description, price, prep_time, image_filename))
            conn.commit()
            conn.close()

            return redirect('/chef/upload')
        else:
            flash("Invalid image file. Please upload a PNG, JPG, JPEG, or GIF.", "danger")
            return redirect('/chef/upload')

    return render_template('upload_dish.html')

@app.route('/chef/dishes')
def view_orders():
    if 'chef_id' not in session:
        return redirect('/chef/login')

    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM dishes WHERE chef_id = ?', (session['chef_id'],))
    dishes = cursor.fetchall()
    conn.close()
    return render_template('view_dishes.html', dishes=dishes)
@app.route('/menu')
def view_menu():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''
        SELECT dishes.*, chefs.name AS chef_name
        FROM dishes
        JOIN chefs ON dishes.chef_id = chefs.id
        WHERE dishes.available = 1
    ''')
    dishes = cursor.fetchall()
    conn.close()
    return render_template('menu.html', dishes=dishes)

@app.route('/place_order/<int:dish_id>', methods=['GET', 'POST'])
def place_order(dish_id):
    if 'customer_id' not in session:
        return redirect('/customer_login')
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM dishes WHERE id = ? AND available = 1", (dish_id,))
    dish = cursor.fetchone()

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        address = request.form['address']
        phone = request.form['phone']
        quantity = request.form['quantity']
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('''
            INSERT INTO orders (customer_id, dish_id, customer_name, customer_email, customer_address, customer_phone, quantity, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (session['customer_id'], dish_id, name, email, address, phone, quantity, timestamp))
        conn.commit()
        order_id = cursor.lastrowid
        conn.close()

        return redirect(f'/fake_payment/{order_id}?price={dish["price"]}&qty={quantity}')

    return render_template('place_order.html', dish=dish)
@app.route('/fake_payment/<int:order_id>', methods=['GET', 'POST'])
def fake_payment(order_id):
    price = float(request.args.get('price', 0))
    qty = int(request.args.get('qty', 1))
    total = price * qty

    if request.method == 'POST':
        flash("Payment successful!", "success")
        return redirect('/thank_you')

    return render_template('fake_payment.html', order_id=order_id, total_amount=total)
@app.route('/chef/manage-orders')
def manage_orders():
    if 'chef_id' not in session:
        return redirect('/chef/login')

    chef_id = session['chef_id']
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Fetch pending orders
    c.execute('''
        SELECT orders.id, orders.customer_name, orders.customer_email,
               orders.quantity, orders.status, dishes.name as dish_name
        FROM orders
        JOIN dishes ON orders.dish_id = dishes.id
        WHERE dishes.chef_id = ? AND orders.status != 'Completed'
    ''', (chef_id,))
    pending_orders = c.fetchall()

    # Fetch completed orders
    c.execute('''
        SELECT orders.id, orders.customer_name, orders.customer_email,
               orders.quantity, orders.status, dishes.name as dish_name
        FROM orders
        JOIN dishes ON orders.dish_id = dishes.id
        WHERE dishes.chef_id = ? AND orders.status = 'Completed'
    ''', (chef_id,))
    completed_orders = c.fetchall()

    conn.close()
    return render_template('manage_orders.html',
                           pending_orders=pending_orders,
                           completed_orders=completed_orders)
@app.route('/chef/mark-completed/<int:order_id>', methods=['POST'])
def mark_order_completed(order_id):
    if 'chef_id' not in session:
        return redirect('/chef/login')

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("UPDATE orders SET status = 'Completed' WHERE id = ?", (order_id,))
    conn.commit()
    conn.close()

    return redirect('/chef/manage-orders')

@app.route('/mark_unavailable/<int:dish_id>', methods=['POST'])
def mark_unavailable(dish_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE dishes SET available = 0 WHERE id = ?", (dish_id,))
    conn.commit()
    conn.close()
    return redirect('/chef/dishes')


@app.route('/mark_available/<int:dish_id>', methods=['POST'])
def mark_available(dish_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE dishes SET available = 1 WHERE id = ?", (dish_id,))
    conn.commit()
    conn.close()
    return redirect('/chef/dishes')
@app.route('/customer_signup', methods=['GET', 'POST'])
def customer_signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO customers (name, email, password) VALUES (?, ?, ?)", 
                           (name, email, password))
            conn.commit()
        except sqlite3.IntegrityError:
            return render_template('customer_signup.html', error="Email already exists.")
        finally:
            conn.close()
        
        return redirect('/customer_login')
    return render_template('customer_signup.html')
@app.route('/customer_login', methods=['GET', 'POST'])
def customer_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, password FROM customers WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            session['customer_id'] = user[0]
            session['customer_name'] = user[1]
            return redirect('/customer/dashboard')
        else:
            return render_template('customer_login.html', error="Invalid credentials")
    return render_template('customer_login.html')
@app.route('/customer/dashboard')
def customer_dashboard():
    if 'customer_id' not in session:
        return redirect('/customer_login')

    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row  
    cursor = conn.cursor()
    cursor.execute('''
        SELECT dishes.*, chefs.name as chef_name
        FROM dishes
        JOIN chefs ON dishes.chef_id = chefs.id
        WHERE dishes.available = 1
    ''')
    dishes = cursor.fetchall()  
    cursor.execute('''
        SELECT o.*, d.name AS dish_name, c.name AS chef_name
        FROM orders o
        JOIN dishes d ON o.dish_id = d.id
        JOIN chefs c ON d.chef_id = c.id
        WHERE o.customer_id = ?
        ORDER BY o.timestamp DESC
    ''', (session['customer_id'],))
    orders = cursor.fetchall()

    conn.close()
    return render_template('customer_dashboard.html', dishes=dishes, orders=orders)
@app.route('/customer_logout')
def customer_logout():
    session.clear()
    flash("You’ve been logged out successfully.", "info")
    return redirect('/customer_login')
@app.route('/thank_you')
def thank_you():
    return render_template('thankyou.html')

if __name__ == '__main__':
    app.run(debug=True)


