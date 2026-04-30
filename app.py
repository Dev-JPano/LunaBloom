from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import os
import uuid
from datetime import datetime
from functools import wraps
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'lunabloom_secret_key_2024')

# ── DATABASE CONFIG ──
# Supabase provides a postgresql:// URL; SQLAlchemy needs psycopg2
DATABASE_URL = os.getenv('DATABASE_URL', '')
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql+psycopg2://', 1)
elif DATABASE_URL.startswith('postgresql://'):
    DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+psycopg2://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin123'

# ══════════════════════════════════════════════
#   ORM MODELS
# ══════════════════════════════════════════════

class Customer(db.Model):
    __tablename__ = 'customers'

    id             = db.Column(db.String(8),   primary_key=True)
    name           = db.Column(db.String(100), nullable=False)
    email          = db.Column(db.String(100), unique=True, nullable=False)
    contact        = db.Column(db.String(30),  nullable=False)
    password       = db.Column(db.String(200), nullable=False)
    date_registered= db.Column(db.String(20),  nullable=False)

    def to_dict(self):
        return {
            'id':              self.id,
            'name':            self.name,
            'email':           self.email,
            'contact':         self.contact,
            'date_registered': self.date_registered,
        }


class Order(db.Model):
    __tablename__ = 'orders'

    id             = db.Column(db.String(20),  primary_key=True)
    customer_name  = db.Column(db.String(100), nullable=False)
    customer_email = db.Column(db.String(100), nullable=True)
    service        = db.Column(db.String(200), nullable=False)
    quantity       = db.Column(db.String(5),   default='1')
    date           = db.Column(db.String(20),  nullable=False)
    time           = db.Column(db.String(10),  nullable=False)
    status         = db.Column(db.String(20),  default='Pending')
    notes          = db.Column(db.Text,         nullable=True)
    created_at     = db.Column(db.String(20),  nullable=True)

    def to_dict(self):
        return {
            'id':             self.id,
            'customer_name':  self.customer_name,
            'customer_email': self.customer_email,
            'service':        self.service,
            'quantity':       self.quantity,
            'date':           self.date,
            'time':           self.time,
            'status':         self.status,
            'notes':          self.notes or '',
            'created_at':     self.created_at,
        }

# ══════════════════════════════════════════════
#   AUTH DECORATORS
# ══════════════════════════════════════════════

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('is_admin'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ══════════════════════════════════════════════
#   PAGE ROUTES
# ══════════════════════════════════════════════

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/book')
def book():
    return render_template('book.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/dashboard')
@admin_required
def dashboard():
    total_customers = Customer.query.count()
    orders          = Order.query.all()
    pending         = sum(1 for o in orders if o.status == 'Pending')
    processing      = sum(1 for o in orders if o.status == 'Processing')
    completed       = sum(1 for o in orders if o.status == 'Completed')
    stats = {
        'total_customers': total_customers,
        'total_orders':    len(orders),
        'pending':         pending,
        'processing':      processing,
        'completed':       completed,
    }
    return render_template('dashboard.html', stats=stats)

@app.route('/customers')
@admin_required
def customers_page():
    return render_template('customers.html')

@app.route('/orders')
@admin_required
def orders_page():
    return render_template('orders.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# ══════════════════════════════════════════════
#   API: AUTH
# ══════════════════════════════════════════════

@app.route('/api/register', methods=['POST'])
def api_register():
    data     = request.get_json()
    name     = data.get('name', '').strip()
    email    = data.get('email', '').strip()
    contact  = data.get('contact', '').strip()
    password = data.get('password', '').strip()

    if not all([name, email, contact, password]):
        return jsonify({'success': False, 'message': 'All fields are required.'}), 400

    if Customer.query.filter_by(email=email).first():
        return jsonify({'success': False, 'message': 'Email already registered.'}), 400

    new_customer = Customer(
        id              = str(uuid.uuid4())[:8].upper(),
        name            = name,
        email           = email,
        contact         = contact,
        password        = password,   # NOTE: hash in production!
        date_registered = datetime.now().strftime('%Y-%m-%d %H:%M'),
    )
    db.session.add(new_customer)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Registration successful! You can now log in.'})


@app.route('/api/login', methods=['POST'])
def api_login():
    data     = request.get_json()
    email    = data.get('email', '').strip()
    password = data.get('password', '').strip()

    # Admin shortcut
    if email == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        session['logged_in']  = True
        session['is_admin']   = True
        session['user_name']  = 'Admin'
        session['user_email'] = 'admin'
        return jsonify({'success': True, 'redirect': '/dashboard', 'message': 'Welcome, Admin!'})

    # Regular user
    customer = Customer.query.filter_by(email=email, password=password).first()
    if customer:
        session['logged_in']  = True
        session['is_admin']   = False
        session['user_name']  = customer.name
        session['user_email'] = customer.email
        return jsonify({'success': True, 'redirect': '/book', 'message': f'Welcome, {customer.name}!'})

    return jsonify({'success': False, 'message': 'Invalid email or password.'}), 401

# ══════════════════════════════════════════════
#   API: CUSTOMERS
# ══════════════════════════════════════════════

@app.route('/api/customers', methods=['GET'])
def api_get_customers():
    search = request.args.get('search', '').lower()
    query  = Customer.query
    if search:
        query = query.filter(
            db.or_(
                Customer.name.ilike(f'%{search}%'),
                Customer.email.ilike(f'%{search}%'),
                Customer.contact.ilike(f'%{search}%'),
            )
        )
    customers = query.order_by(Customer.date_registered.desc()).all()
    return jsonify([c.to_dict() for c in customers])


@app.route('/api/customers/<customer_id>', methods=['PUT'])
def api_update_customer(customer_id):
    data     = request.get_json()
    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({'success': False, 'message': 'Customer not found.'}), 404

    if data.get('name'):    customer.name    = data['name']
    if data.get('email'):   customer.email   = data['email']
    if data.get('contact'): customer.contact = data['contact']
    db.session.commit()
    return jsonify({'success': True, 'message': 'Customer updated.'})


@app.route('/api/customers/<customer_id>', methods=['DELETE'])
def api_delete_customer(customer_id):
    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({'success': False, 'message': 'Customer not found.'}), 404
    db.session.delete(customer)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Customer deleted.'})

# ══════════════════════════════════════════════
#   API: ORDERS
# ══════════════════════════════════════════════

@app.route('/api/orders', methods=['GET'])
def api_get_orders():
    search        = request.args.get('search', '').lower()
    status_filter = request.args.get('status', '').strip()
    query         = Order.query

    if search:
        query = query.filter(
            db.or_(
                Order.customer_name.ilike(f'%{search}%'),
                Order.service.ilike(f'%{search}%'),
                Order.id.ilike(f'%{search}%'),
            )
        )
    if status_filter:
        query = query.filter(Order.status == status_filter)

    orders = query.order_by(Order.created_at.asc()).all()
    return jsonify([o.to_dict() for o in orders])


@app.route('/api/orders', methods=['POST'])
def api_create_order():
    data           = request.get_json()
    customer_name  = data.get('customer_name', '').strip()
    customer_email = data.get('customer_email', '').strip()
    service        = data.get('service', '').strip()
    quantity       = data.get('quantity', '1')
    date           = data.get('date', '').strip()
    time           = data.get('time', '').strip()
    notes          = data.get('notes', '').strip()

    if not all([service, date, time, customer_name]):
        return jsonify({'success': False, 'message': 'Please fill in all required fields.'}), 400

    new_order = Order(
        id             = 'ORD-' + str(uuid.uuid4())[:6].upper(),
        customer_name  = customer_name,
        customer_email = customer_email,
        service        = service,
        quantity       = str(quantity),
        date           = date,
        time           = time,
        status         = 'Pending',
        notes          = notes,
        created_at     = datetime.now().strftime('%Y-%m-%d %H:%M'),
    )
    db.session.add(new_order)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Booking confirmed! Salamat po! 💅'})


@app.route('/api/orders/<order_id>/status', methods=['PUT'])
def api_update_order_status(order_id):
    data       = request.get_json()
    new_status = data.get('status', '')
    order      = Order.query.get(order_id)
    if not order:
        return jsonify({'success': False, 'message': 'Order not found.'}), 404
    order.status = new_status
    db.session.commit()
    return jsonify({'success': True, 'message': f'Order status updated to {new_status}.'})


@app.route('/api/orders/<order_id>', methods=['PUT'])
def api_update_order(order_id):
    data  = request.get_json()
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'success': False, 'message': 'Order not found.'}), 404

    for field in ['customer_name', 'customer_email', 'service', 'quantity', 'date', 'time', 'notes']:
        if data.get(field) is not None:
            setattr(order, field, str(data[field]))
    db.session.commit()
    return jsonify({'success': True, 'message': 'Order updated.'})


@app.route('/api/orders/<order_id>', methods=['DELETE'])
def api_delete_order(order_id):
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'success': False, 'message': 'Order not found.'}), 404
    db.session.delete(order)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Order deleted.'})


@app.route('/api/dashboard/stats', methods=['GET'])
def api_dashboard_stats():
    today  = datetime.now().strftime('%Y-%m-%d')
    orders = Order.query.all()
    return jsonify({
        'total_customers': Customer.query.count(),
        'total_orders':    len(orders),
        'pending':         sum(1 for o in orders if o.status == 'Pending'),
        'processing':      sum(1 for o in orders if o.status == 'Processing'),
        'completed':       sum(1 for o in orders if o.status == 'Completed'),
        'today_orders':    sum(1 for o in orders if o.date == today),
    })

# ══════════════════════════════════════════════
#   RUN
# ══════════════════════════════════════════════

if __name__ == '__main__':
    with app.app_context():
        db.create_all()   # creates tables if they don't exist yet
    app.run(debug=True, port=5000)
