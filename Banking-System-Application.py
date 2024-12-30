import sqlite3
import random
import re
from datetime import datetime

# Database connection
conn = sqlite3.connect('banking_system.db')
cursor = conn.cursor()

# Create necessary tables
def create_tables():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        account_number TEXT UNIQUE NOT NULL,
        dob TEXT NOT NULL,
        city TEXT NOT NULL,
        password TEXT NOT NULL,
        balance REAL NOT NULL,
        contact_number TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        address TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Active'
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_number TEXT NOT NULL,
        type TEXT NOT NULL,
        amount REAL NOT NULL,
        date TEXT NOT NULL
    )
    """)
    conn.commit()

# Validation functions
def validate_name(name):
    return re.match(r'^[A-Za-z ]+$', name)

def validate_email(email):
    return re.match(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$', email)

def validate_password(password):
    return len(password) >= 8 and any(char.isdigit() for char in password)

def validate_contact(contact):
    return re.match(r'^\d{10}$', contact)

# Add User
def add_user():
    name = input("Enter Name (Only alphabets and spaces): ")
    if not validate_name(name):
        print("Invalid name. Only alphabets and spaces are allowed.")
        return

    dob = input("Enter DOB (YYYY-MM-DD): ")
    city = input("Enter City: ")
    password = input("Enter Password (It should consist of minimum 8 characters and a number): ")
    if not validate_password(password):
        print("Password must be at least 8 characters with a number.")
        return

    balance = float(input("Enter Initial Balance (min 2000): "))
    if balance < 2000:
        print("Minimum balance must be 2000.")
        return

    contact_number = input("Enter Contact Number (10 digits): ")
    if not validate_contact(contact_number):
        print("Invalid Contact Number!")
        return

    email = input("Enter Email ID (example@example.com): ")
    if not validate_email(email):
        print("Invalid Email ID!")
        return

    address = input("Enter Address: ")
    
    account_number = str(random.randint(1000000000, 9999999999))

    cursor.execute('''
    INSERT INTO users (name, account_number, dob, city, password, balance, contact_number, email, address)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (name, account_number, dob, city, password, balance, contact_number, email, address))
    conn.commit()
    print(f"User added successfully! Account Number: {account_number}")

# Show Users
def show_users():
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    if not users:
        print("No users found.")
        return

    for user in users:
        print(f"""
        Name: {user[1]}
        Account Number: {user[2]}
        DOB: {user[3]}
        City: {user[4]}
        Password: {user[5]}
        Balance: {user[6]:.2f}
        Contact: {user[7]}
        Email: {user[8]}
        Address: {user[9]}
        Status: {user[10]}
        """)

# Transfer Amount
def transfer_amount(logged_in_user):
    from_acc = logged_in_user
    to_acc = input("Enter Beneficiary Account Number: ")
    amount = float(input("Enter Amount to Transfer: "))

    # Check sender's balance
    cursor.execute("SELECT balance FROM users WHERE account_number=? AND status='Active'", (from_acc,))
    sender_balance = cursor.fetchone()

    if not sender_balance or sender_balance[0] < amount:
        print("Insufficient balance or inactive account.")
        return

    # Check if beneficiary exists and is active
    cursor.execute("SELECT * FROM users WHERE account_number=? AND status='Active'", (to_acc,))
    if not cursor.fetchone():
        print("Beneficiary account not found or inactive.")
        return

    # Update balances
    cursor.execute("UPDATE users SET balance = balance - ? WHERE account_number = ?", (amount, from_acc))
    cursor.execute("UPDATE users SET balance = balance + ? WHERE account_number = ?", (amount, to_acc))

    # Record transactions
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO transactions (account_number, type, amount, date) VALUES (?, 'Debit', ?, ?)",
                   (from_acc, amount, current_time))
    cursor.execute("INSERT INTO transactions (account_number, type, amount, date) VALUES (?, 'Credit', ?, ?)",
                   (to_acc, amount, current_time))

    conn.commit()
    print("Transfer successful.")

# Show Balance
def show_balance(logged_in_user):
    cursor.execute("SELECT balance FROM users WHERE account_number=? AND status='Active'", (logged_in_user,))
    balance = cursor.fetchone()
    if balance:
        print(f"Your current balance is: {balance[0]:.2f}")
    else:
        print("Account not found or inactive.")

# Show Transactions
def show_transactions(logged_in_user):
    cursor.execute("SELECT * FROM transactions WHERE account_number=?", (logged_in_user,))
    transactions = cursor.fetchall()
    if not transactions:
        print("No transactions found.")
        return

    for txn in transactions:
        print(f"""
        Transaction ID: {txn[0]}
        Account Number: {txn[1]}
        Type: {txn[2]}
        Amount: {txn[3]:.2f}
        Date: {txn[4]}
        """)

# Credit Amount
def credit_amount(logged_in_user):
    amount = float(input("Enter amount to credit: "))
    cursor.execute("UPDATE users SET balance = balance + ? WHERE account_number=?", (amount, logged_in_user))
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO transactions (account_number, type, amount, date) VALUES (?, 'Credit', ?, ?)",
                   (logged_in_user, amount, current_time))
    conn.commit()
    print("Amount credited successfully.")

# Debit Amount
def debit_amount(logged_in_user):
    amount = float(input("Enter amount to debit: "))
    cursor.execute("SELECT balance FROM users WHERE account_number=? AND status='Active'", (logged_in_user,))
    balance = cursor.fetchone()
    if balance and balance[0] >= amount:
        cursor.execute("UPDATE users SET balance = balance - ? WHERE account_number=?", (amount, logged_in_user))
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO transactions (account_number, type, amount, date) VALUES (?, 'Debit', ?, ?)",
                       (logged_in_user, amount, current_time))
        conn.commit()
        print("Amount debited successfully.")
    else:
        print("Insufficient balance or inactive account.")

# Activate/Deactivate Account
def toggle_account_status(logged_in_user):
    status = input("Enter 'Active' to activate or 'Inactive' to deactivate your account: ").capitalize()
    if status not in ['Active', 'Inactive']:
        print("Invalid status.")
        return

    cursor.execute("UPDATE users SET status=? WHERE account_number=?", (status, logged_in_user))
    conn.commit()
    print(f"Account status updated to {status}.")

# Change Password
def change_password(logged_in_user):
    new_password = input("Enter new password (minimum 8 characters and a number): ")
    if not validate_password(new_password):
        print("Password does not meet the required conditions.")
        return

    cursor.execute("UPDATE users SET password=? WHERE account_number=?", (new_password, logged_in_user))
    conn.commit()
    print("Password updated successfully.")

# Update Profile
def update_profile(logged_in_user):
    name = input("Enter new name: ")
    if not validate_name(name):
        print("Invalid name.")
        return

    dob = input("Enter new DOB (YYYY-MM-DD): ")
    city = input("Enter new City: ")
    contact_number = input("Enter new Contact Number (10 digits): ")
    if not validate_contact(contact_number):
        print("Invalid Contact Number!")
        return

    email = input("Enter new Email ID (example@example.com): ")
    if not validate_email(email):
        print("Invalid Email ID!")
        return

    address = input("Enter new Address: ")

    cursor.execute('''UPDATE users SET name=?, dob=?, city=?, contact_number=?, email=?, address=? WHERE account_number=?''',
                   (name, dob, city, contact_number, email, address, logged_in_user))
    conn.commit()
    print("Profile updated successfully.")

# Login
def login():
    acc_number = input("Enter Account Number: ")
    password = input("Enter Password: ")

    cursor.execute("SELECT * FROM users WHERE account_number=? AND password=?", (acc_number, password))
    user = cursor.fetchone()

    if not user:
        print("Invalid login credentials.")
        return None

    print(f"Welcome, {user[1]}!")
    return user[2]

# Main Menu
create_tables()
logged_in_user = None

while True:
    print("""
    BANKING SYSTEM
    1. Add User
    2. Show Users
    3. Login
    4. Exit
    """)
    choice = input("Enter your choice: ")
    if choice == "1":
        add_user()
    elif choice == "2":
        show_users()
    elif choice == "3":
        logged_in_user = login()
        if logged_in_user:
            while True:
                print("""
                1. Transfer Amount
                2. Show Balance
                3. Show Transactions
                4. Credit Amount
                5. Debit Amount
                6. Activate/Deactivate Account
                7. Change Password
                8. Update Profile
                9. Logout
                """)
                choice = input("Enter your choice: ")

                if choice == "1":
                    transfer_amount(logged_in_user)
                elif choice == "2":
                    show_balance(logged_in_user)
                elif choice == "3":
                    show_transactions(logged_in_user)
                elif choice == "4":
                    credit_amount(logged_in_user)
                elif choice == "5":
                    debit_amount(logged_in_user)
                elif choice == "6":
                    toggle_account_status(logged_in_user)
                elif choice == "7":
                    change_password(logged_in_user)
                elif choice == "8":
                    update_profile(logged_in_user)
                elif choice == "9":
                    print("Logged out.")
                    logged_in_user = None
                    break
                else:
                    print("Invalid choice!")
    elif choice == "4":
        print("Thank you for using the Banking System!")
        break
    else:
        print("Invalid choice! Try again.")
