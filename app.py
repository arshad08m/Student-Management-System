import os
from flask import Flask, get_flashed_messages, render_template, request, redirect, flash, session, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import mysql.connector
from mysql.connector.errors import IntegrityError
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.secret_key = "abc@0622"  

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

def get_db_connection():
    try:
        db = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Sanya@0622",
            database="student_management_personal",
            port=os.getenv("DB_PORT", 3306)  # Use 3306 as default if DB_PORT is not set
        )
        return db
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, username, email):
        self.id = id
        self.username = username
        self.email = email

# Flask-Login user loader
@login_manager.user_loader
def load_user(user_id):
    db = get_db_connection()
    if db:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        cursor.close()  
        db.close()  
        if user:
            return User(id=user[0], username=user[1], email=user[2])
    return None

# Homepage: List students with search and filter
@app.route('/')
@login_required
def index():
    search = request.args.get('search', '')
    grade = request.args.get('grade', '')
    reg_number = request.args.get('reg_number', '')  

    query = "SELECT * FROM students WHERE name LIKE %s AND user_id = %s"
    params = [f"%{search}%", current_user.id]

    if grade:
        query += " AND grade = %s"
        params.append(grade)

    if reg_number:
        query += " AND registration_number = %s"  
        params.append(reg_number)

    db = get_db_connection()
    if db:
        cursor = db.cursor()
        cursor.execute(query, params)
        students = cursor.fetchall()  
        cursor.close()  
        db.close()  
        return render_template('index.html', students=students)

    flash("Unable to connect to the database.", "danger")
    return redirect('/login')

# Add student PAGE
@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_student():
    if request.method == 'POST':
        name = request.form.get('name', '')
        age = request.form.get('age', '')
        grade = request.form.get('grade', '')
        reg_number = request.form.get('registration_number', '')  

        # Validate age
        try:
            age = int(age)  
        except ValueError:
            flash("Please enter a valid age.", "danger")
            return render_template('add.html', messages=get_flashed_messages())

        # Validate grade
        if not grade.isalpha() or len(grade) > 2:  
            flash("Please enter a valid grade.", "danger")
            return render_template('add.html', messages=get_flashed_messages())

        if not reg_number:  # Validate if registration number is not empty
            flash("Registration number is required!", "danger")
            return render_template('add.html', messages=get_flashed_messages())

        db = get_db_connection()
        if db:
            cursor = db.cursor()
            try:
                # Attempt to insert the new student record
                cursor.execute(
                    "INSERT INTO students (name, age, grade, registration_number, user_id) VALUES (%s, %s, %s, %s, %s)",
                    (name, age, grade, reg_number, current_user.id)  # Link to current user
                )
                db.commit()
                flash("Student added successfully!", "success")
                return redirect('/')
            except IntegrityError as e:  
                error_message = str(e)  
                if "Duplicate entry" in error_message:
                    flash(f"Registration number '{reg_number}' already exists. Please use a unique registration number.", "danger")
                else:
                    flash(f"An error occurred while adding the student: {error_message}", "danger")
                return render_template('add.html', messages=get_flashed_messages())
            finally:
                cursor.close()
                db.close()

        flash("Unable to connect to the database.", "danger")
        return redirect('/')

    session.pop('_flashes', None)  
    return render_template('add.html', messages=[])

# Edit student page
@app.route('/edit/<int:registration_number>', methods=['GET', 'POST'])
@login_required
def edit_student(registration_number):
    session.pop('_flashes', None)  

    db = get_db_connection()
    if db:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM students WHERE registration_number = %s AND user_id = %s", (registration_number, current_user.id))
        student = cursor.fetchone()
        cursor.close()
        db.close()

        if not student:
            flash("Student not found!", "danger")
            return redirect('/')

        if request.method == 'POST':
            name = request.form.get('name', '')
            age = request.form.get('age', '')
            grade = request.form.get('grade', '')

            # Validate age
            try:
                age = int(age)  
            except ValueError:
                flash("Please enter a valid age.", "danger")
                return render_template('edit.html', student=student)

            # Validate grade
            if not grade.isalpha() or len(grade) > 2:  
                flash("Please enter a valid grade.", "danger")
                return render_template('edit.html', student=student)

            reg_number = student[0]  

            db = get_db_connection()
            if db:
                cursor = db.cursor()
                cursor.execute("UPDATE students SET name = %s, age = %s, grade = %s WHERE registration_number = %s AND user_id = %s", 
                               (name, age, grade, reg_number, current_user.id))  # Ensure the user is the owner
                db.commit()
                cursor.close()
                db.close()
                flash("Student updated successfully!", "success")
                return redirect('/')

            flash("Unable to connect to the database.", "danger")
            return redirect('/')

        return render_template('edit.html', student=student)

    flash("Unable to connect to the database.", "danger")
    return redirect('/')

# Delete confirmation page
@app.route('/delete/<int:registration_number>', methods=['GET'])
@login_required
def delete_student(registration_number):
    db = get_db_connection()
    if db:
        try:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM students WHERE registration_number = %s AND user_id = %s", (registration_number, current_user.id))
            student = cursor.fetchone()
        finally:
            cursor.close()
            db.close()

        if not student:
            flash("Student not found!", "danger")
            return redirect('/')

        return render_template('delete.html', student=student)

    flash("Unable to connect to the database.", "danger")
    return redirect('/')

# Confirm delete student
@app.route('/delete/<int:registration_number>/confirm', methods=['POST'])
@login_required
def confirm_delete_student(registration_number):
    db = get_db_connection()
    if db:
        try:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM students WHERE registration_number = %s AND user_id = %s", (registration_number, current_user.id))
            student = cursor.fetchone()

            if not student:
                flash("Student not found!", "danger")
                return redirect('/')

            cursor.execute("DELETE FROM students WHERE registration_number = %s AND user_id = %s", (registration_number, current_user.id))  # Ensure only the user's students can be deleted
            db.commit()
            flash(f"Student '{student[1]}' deleted successfully!", "success")
        finally:
            cursor.close()
            db.close()

        return redirect('/')

    flash("Unable to connect to the database.", "danger")
    return redirect('/')

# Register page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        db = get_db_connection()
        if db:
            cursor = db.cursor()
            
            # Check if the username already exists
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            existing_user = cursor.fetchone()

            # Check if the email already exists
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            existing_email = cursor.fetchone()

            if existing_user:
                flash("Username already exists. Please choose a different one.", "danger")
                cursor.close()
                db.close()
                return redirect('/register')

            if existing_email:
                flash("Email already registered. Please use a different email.", "danger")
                cursor.close()
                db.close()
                return redirect('/register')

            # Proceed with registration if no duplicates found
            cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", (username, email, password))
            db.commit()
            cursor.close()
            db.close()
            flash("Registration successful! Please log in.", "success")
            return redirect('/login')

        flash("Unable to connect to the database.", "danger")
        return redirect('/register')

    return render_template('register.html')

# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect('/')  # Redirect to the homepage if logged in

    # This will ensure that flash messages from previous requests do not persist
    # and that only relevant messages are shown on the login page.
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        db = get_db_connection()
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            cursor.close()
            db.close()

            if user:
                # Check if the provided password matches the stored one
                if user[3] == password:  
                    login_user(User(id=user[0], username=user[1], email=user[2]))
                    # Flash success message for login
                    flash("Login successful!", "success")
                    return redirect('/')
                else:
                    # Flash message for invalid password
                    flash("Invalid email or password. Please try again.", "danger")
                    return redirect('/login')  # Redirect to login page

            # Flash message for user not found
            flash("Invalid email or password. Please try again.", "danger")
            return redirect('/login')  # Redirect to login page

        # Flash message only for database connection failure
        flash("Unable to connect to the database.", "danger")
        return redirect('/login')

    return render_template('login.html')


# Logout page
@app.route('/logout')
@login_required
def logout():
    # Clear all flash messages
    session.pop('_flashes', None)
    
    # Log the user out
    logout_user()
    flash("You have been logged out successfully.", "success")
    return redirect(url_for('login'))


# Main entry point to run the app
if __name__ == '__main__':
    app.run(debug=True)
