from flask import Flask, render_template, request, redirect, flash
import mysql.connector

app = Flask(__name__)
app.secret_key = "abc@0622"  # For flash messages

# Database connection
db = mysql.connector.connect(
    host="localhost",
    user="root",  # Replace with your MySQL username
    password="Sanya@0622",  # Replace with your MySQL password
    database="student_management"
)
cursor = db.cursor()

# Homepage: List students with search and filter
@app.route('/')
def index():
    search = request.args.get('search', '')
    grade = request.args.get('grade', '')

    query = "SELECT * FROM students WHERE name LIKE %s"
    params = [f"%{search}%"]

    if grade:
        query += " AND grade = %s"
        params.append(grade)

    cursor.execute(query, params)
    students = cursor.fetchall()
    return render_template('index.html', students=students)

# Add student page
@app.route('/add', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        grade = request.form['grade']

        cursor.execute("INSERT INTO students (name, age, grade) VALUES (%s, %s, %s)", (name, age, grade))
        db.commit()
        flash("Student added successfully!", "success")
        return redirect('/')
    return render_template('add.html')

# Edit student page
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_student(id):
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        grade = request.form['grade']

        cursor.execute("UPDATE students SET name = %s, age = %s, grade = %s WHERE id = %s", (name, age, grade, id))
        db.commit()
        flash("Student updated successfully!", "success")
        return redirect('/')

    cursor.execute("SELECT * FROM students WHERE id = %s", (id,))
    student = cursor.fetchone()
    if not student:
        flash("Student not found!", "danger")
        return redirect('/')
    return render_template('edit.html', student=student)

# Delete confirmation page
@app.route('/delete/<int:id>')
def delete_student(id):
    cursor.execute("SELECT * FROM students WHERE id = %s", (id,))
    student = cursor.fetchone()
    if not student:
        flash("Student not found!", "danger")
        return redirect('/')
    return render_template('delete.html', student=student)

# Confirm delete student
@app.route('/delete/<int:id>/confirm')
def confirm_delete_student(id):
    cursor.execute("DELETE FROM students WHERE id = %s", (id,))
    db.commit()
    flash("Student deleted successfully!", "success")
    return redirect('/')

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
