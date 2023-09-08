from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)


def get_db_connection():
  conn = sqlite3.connect('my_database.db')
  conn.row_factory = sqlite3.Row  # Enable row access using column names
  return conn


def get_categories():
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute('SELECT name FROM categories')
  categories = [row[0] for row in cursor.fetchall()]
  cursor.close()
  conn.close()
  return categories


#landing page route
@app.route('/')
def landing_page():
  return render_template('home.html')


@app.route('/login', methods=['POST'])
def login():
  username = request.form['username']
  password = request.form['password']

  conn = sqlite3.connect("my_database.db")
  c = conn.cursor()

  # Check if it's a user login
  c.execute("SELECT * FROM users WHERE username = ? AND password = ?",
            (username, password))
  user = c.fetchone()

  if user:
    conn.close()
    # Redirect to user's dashboard after successful login
    return redirect(url_for('user_dashboard'))
  else:
    # If user doesn't exist, check if it's an admin login
    c.execute("SELECT * FROM admins WHERE username = ? AND password = ?",
              (username, password))
    admin = c.fetchone()
    if admin:
      conn.close()
      # Redirect to admin dashboard after successful login
      return redirect(url_for('admin_dashboard'))
    else:
      # Redirect to user registration page if user doesn't exist
      conn.close()
      return redirect(url_for('user_registration'))


# User dashboard
@app.route('/dashboard')
def user_dashboard():
  return redirect(url_for('home_with_nav'))


# Admin dashboard
@app.route('/admin/dashboard')
def admin_dashboard():
  return redirect(url_for('user_home'))


#user
#home page route
@app.route('/home_with_nav')
def home_with_nav():
  categories = get_categories()
  return render_template('test2.html', categories=categories)


# Route to view products in a specific category
@app.route('/category/<string:category>')
def view_category(category):
  print(f"Cat: {category}")
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute("SELECT name FROM categories WHERE name=?", (category, ))
  existing_category = cursor.fetchone()

  if existing_category:
    cursor.execute("SELECT * FROM products WHERE category=?", (category, ))
    products = cursor.fetchall()
    cursor.close()
    conn.close()

    # Convert the sqlite3.Row objects to dictionaries
    products = [dict(product) for product in products]

    # Add the 'is_out_of_stock' property to each product
    for product in products:
      product['is_out_of_stock'] = product['quantity'] == 0

    return render_template('category.html',
                           category=category,
                           products=products)
  else:
    return 'Category not found.'


@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
  if request.method == 'POST':
    product_name = request.form.get('product_name')
    quantity = request.form.get('quantity')

    try:
      quantity = int(quantity)
      if quantity <= 0:
        raise ValueError("Quantity must be a positive integer.")
    except (ValueError, TypeError):
      return 'Invalid quantity. Please enter a positive integer.'

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products WHERE name=?', (product_name, ))
    product = cursor.fetchone()

    if not product:
      cursor.close()
      conn.close()
      return 'Product not found.'

    if product['quantity'] < quantity:
      cursor.close()
      conn.close()
      return 'Entered quantity exceeds available stock. Maximum available quantity: ' + str(
        product['quantity'])

    # Check if the product is already in the cart
    cursor.execute('SELECT * FROM cart WHERE name=?', (product_name, ))
    existing_item = cursor.fetchone()

    if existing_item:
      # If the product is already in the cart, update the quantity and total price
      updated_quantity = existing_item['quantity'] + quantity
      total_price = product['price'] * updated_quantity
      cursor.execute('UPDATE cart SET quantity=?, total_price=? WHERE name=?',
                     (updated_quantity, total_price, product_name))
    else:
      # If the product is not in the cart, insert the new cart item
      total_price = product['price'] * quantity
      cursor.execute(
        'INSERT INTO cart (name, price, quantity, total_price) VALUES (?, ?, ?, ?)',
        (product['name'], product['price'], quantity, total_price))

    # Update the available quantity in the products table
    updated_quantity = product['quantity'] - quantity
    cursor.execute('UPDATE products SET quantity=? WHERE name=?',
                   (updated_quantity, product_name))

    conn.commit()
    cursor.close()
    conn.close()

    return 'Product added to cart successfully!'

  return redirect(url_for('home_with_nav'))


@app.route('/remove_from_cart/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
  conn = get_db_connection()
  cursor = conn.cursor()

  # Fetch the cart item based on the product_id
  cursor.execute("SELECT * FROM cart WHERE id=?", (product_id, ))
  cart_item = cursor.fetchone()

  if cart_item:
    # Update the available quantity in the products table
    product_name = cart_item['name']
    quantity_in_cart = cart_item['quantity']
    cursor.execute("SELECT quantity FROM products WHERE name=?",
                   (product_name, ))
    product = cursor.fetchone()

    if product:
      available_quantity = product['quantity'] + quantity_in_cart
      cursor.execute("UPDATE products SET quantity=? WHERE name=?",
                     (available_quantity, product_name))

    # Remove the item from the cart
    cursor.execute("DELETE FROM cart WHERE id=?", (product_id, ))
    conn.commit()

  cursor.close()
  conn.close()
  return redirect(url_for('view_cart'))


# Route to view the cart
@app.route('/cart')
def view_cart():
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute("SELECT * FROM cart")
  cart_items = cursor.fetchall()
  # Calculate the total order price
  total_order_price = sum(item['total_price'] for item in cart_items)
  cursor.close()
  conn.close()
  return render_template('cart.html',
                         cart_items=cart_items,
                         total_order_price=total_order_price)


@app.route('/checkout')
def checkout():
  conn = get_db_connection()
  cursor = conn.cursor()

  # Fetch cart items from the cart table
  cursor.execute("SELECT * FROM cart")
  cart_items = cursor.fetchall()

  if not cart_items:
    cursor.close()
    conn.close()
    return 'Your cart is empty. Nothing to checkout.'

  # Calculate the total order price
  total_order_price = sum(item['total_price'] for item in cart_items)

  # Insert order details into the 'orders' table
  order_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
  for item in cart_items:
    cursor.execute(
      'INSERT INTO orders (product_name, quantity, total_price, order_date) VALUES (?, ?, ?, ?)',
      (item['name'], item['quantity'], item['total_price'], order_date))

  # Clear the cart by removing all items from the 'cart' table
  cursor.execute('DELETE FROM cart')

  conn.commit()
  cursor.close()
  conn.close()
  return render_template('checkout.html', total_order_price=total_order_price)
  #return f'Thank you for your order! Total amount: ${total_order_price:.2f}'


# admin
# Route to display all available products in the grocery store
@app.route('/user_home')
def user_home():
  # Fetch all products for the user view
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute("SELECT * FROM products")
  products = cursor.fetchall()
  cursor.close()
  conn.close()
  return render_template('test1.html', products=products)


# Route to add new product to the store
@app.route('/add', methods=['GET', 'POST'])
def add_product():
  if request.method == 'POST':
    name = request.form['name']
    category = request.form['category']
    price = request.form['price']
    quantity = request.form['quantity']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
      "INSERT INTO products (name, category, price, quantity) VALUES (?, ?, ?, ?)",
      (name, category, price, quantity))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('user_home'))
  # Fetch categories for displaying in the add_product.html template
  categories = get_categories()
  return render_template('add_product.html', categories=categories)


# Route to update product details
@app.route('/update/<int:product_id>', methods=['GET', 'POST'])
def update_product(product_id):
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute("SELECT * FROM products WHERE id=?", (product_id, ))
  row = cursor.fetchone()
  cursor.close()
  conn.close()

  if not row:
    # Handle product not found scenario
    return 'Product not found.'

  product = {
    'id': row[0],
    'name': row[1],
    'category': row[2],
    'price': row[3],
    'quantity': row[4]
  }

  if request.method == 'POST':
    name = request.form['name']
    category = request.form['category']
    price = request.form['price']
    quantity = request.form['quantity']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
      "UPDATE products SET name=?, category=?, price=?, quantity=? WHERE id=?",
      (name, category, price, quantity, product_id))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('user_home'))

  categories = get_categories()
  return render_template('update_product.html',
                         product=product,
                         categories=categories)


# Route to delete product from the store
@app.route('/delete/<int:product_id>', methods=['POST'])
def delete_product(product_id):
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute("DELETE FROM products WHERE id=?", (product_id, ))
  conn.commit()
  cursor.close()
  conn.close()
  return redirect(url_for('user_home'))


@app.route('/search', methods=['GET', 'POST'])
def search():
  if request.method == 'POST':
    search_query = request.form['search_query']
    # Perform the search query in your database
    # You can modify the query as per your database schema
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
      "SELECT * FROM products WHERE name LIKE ? OR category LIKE ?",
      ('%' + search_query + '%', '%' + search_query + '%'))
    search_results = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('search_results.html', results=search_results)

  return render_template('search.html')


# Route for user login page
@app.route('/user_login')
def user_login():
  return render_template('user_login.html')


# Route for admin login page
@app.route('/admin_login')
def admin_login():
  return render_template('admin_login.html')


# Route for user registration page
@app.route('/user_registration')
def user_registration():
  return render_template('user_registration.html')


@app.route('/register_user', methods=['POST'])
def register_user():
  username = request.form['username']
  password = request.form['password']

  conn = get_db_connection()
  cursor = conn.cursor()

  # Check if the username already exists in the database
  cursor.execute("SELECT * FROM users WHERE username = ?", (username, ))
  existing_user = cursor.fetchone()

  if existing_user:
    conn.close()
    return 'User already exists. Please choose a different username.'

  # If the user doesn't exist, insert the new user into the 'users' table
  cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                 (username, password))
  conn.commit()
  conn.close()

  # Redirect to user's dashboard after successful registration
  return redirect(url_for('user_dashboard'))


app.run(host='0.0.0.0', port=81)
