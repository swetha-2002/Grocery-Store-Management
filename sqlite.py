# import sqlite3

# # Function to create a connection and cursor to the database
# def get_db_connection():
#     return sqlite3.connect('my_database.db')

# # Function to add products to the database
# def add_products():
#     products_data = [
#         ("Apple", 1.50, 100),
#         ("Banana", 0.75, 80),
#         ("Milk", 3.25, 50),
#         ("Bread", 2.50, 30)
#     ]

#     conn = get_db_connection()
#     cursor = conn.cursor()

#     # Create the 'products' table if it doesn't exist
#     cursor.execute('CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, price REAL, quantity INTEGER)')

#     # Insert the example products into the 'products' table
#     cursor.executemany('INSERT INTO products (name, price, quantity) VALUES (?, ?, ?)', products_data)

#     conn.commit()
#     cursor.close()
#     conn.close()

# if __name__ == '__main__':
#     add_products()


import sqlite3


# Function to create a connection and cursor to the database
def get_db_connection():
  return sqlite3.connect('my_database.db')


# Function to add product categories and products to the database
def add_categories_and_products():
  categories_data = [("Fruits", ), ("Vegetables", ), ("Dairy", ), ("Meat", ),
                     ("Snacks", ), ("Beverages", )]

#(ITEM_NAME, CATEGORY,PRICE,QUANTITY)
  products_data = [
    ("Apple", "Fruits", 15.0, 40), ("Banana", "Fruits", 7.50, 80),
    ("Dragon Fruit", "Fruits", 200.0, 0), ("Milk", "Dairy", 32.5, 50),
    ("Bread", "Dairy", 25.0, 30), ("Milk", "Dairy", 30, 0),
    ("Carrot", "Vegetables", 25.0, 20), ("Potato", "Vegetables", 15.0, 40),
    ("Tomato", "Vegetables", 150.0, 0), ("Chicken", "Meat", 200, 0),
    ("Kurkure", "Snacks", 10.0, 100), ("Lays", "Snacks", 10.0, 100),
    ("Chips", "Snacks", 15, 0), ("Chocolates", "Snacks", 5, 0),
    ("CoCo Cola", "Beverages", 20.0, 50), ("Pepsi", "Beverages", 20.0, 50),
    ("AppyFizz", "Beverages", 20.0, 100), ("Fruti", "Beverages", 10.0, 0),
    ("Fanta", "Beverages", 20.0, 0)
  ]

  conn = get_db_connection()
  cursor = conn.cursor()

  # Create the 'products' table if it doesn't exist
  cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT,
            category TEXT,
            price REAL,
            quantity INTEGER
        )
    ''')

  # Create the 'categories' table if it doesn't exist
  cursor.execute(
    'CREATE TABLE IF NOT EXISTS categories (id INTEGER PRIMARY KEY, name TEXT)'
  )

  # Create the 'cart' table if it doesn't exist
  cursor.execute('''
        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY,
            name TEXT,
            price REAL,
            quantity INTEGER,
            total_price REAL
        )
    ''')

  # Check if the 'category' column exists in the 'products' table
  cursor.execute("PRAGMA table_info(products)")
  columns = cursor.fetchall()
  has_category_column = any(column[1] == 'category' for column in columns)

  # If the 'category' column does not exist, add it to the 'products' table
  if not has_category_column:
    cursor.execute('ALTER TABLE products ADD COLUMN category TEXT')

  # Insert the product categories into the 'categories' table
  cursor.executemany('INSERT INTO categories (name) VALUES (?)',
                     categories_data)

  # Insert the example products into the 'products' table
  cursor.executemany(
    'INSERT INTO products (name, category, price, quantity) VALUES (?, ?, ?, ?)',
    products_data)

  # Create the 'orders' table if it doesn't exist
  cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            total_price REAL NOT NULL,
            order_date TEXT NOT NULL
        )
    ''')

  # Create users table
  cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT
        )
    ''')

  # Create admins table
  cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT
        )
    ''')

  # Add some sample user credentials for testing
  cursor.execute(
    "INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)",
    ('user1', 'password123'))
  cursor.execute(
    "INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)",
    ('user2', 'qwerty789'))

  # Add some sample admin credentials for testing
  cursor.execute(
    "INSERT OR IGNORE INTO admins (username, password) VALUES (?, ?)",
    ('admin1', 'adminpassword1'))
  cursor.execute(
    "INSERT OR IGNORE INTO admins (username, password) VALUES (?, ?)",
    ('admin2', 'adminpassword2'))

  conn.commit()
  cursor.close()
  conn.close()


if __name__ == '__main__':
  add_categories_and_products()
