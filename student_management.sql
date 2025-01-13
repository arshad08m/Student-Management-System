-- Create the database
CREATE DATABASE IF NOT EXISTS student_management_personal;

-- Use the created database
USE student_management_personal;

-- Create the users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL
);

-- Create the students table with a 6-digit registration_number and link to users via user_id
CREATE TABLE IF NOT EXISTS students (
    registration_number INT UNSIGNED UNIQUE PRIMARY KEY,  -- 6-digit unique registration number
    name VARCHAR(255) NOT NULL,
    age INT NOT NULL,
    grade VARCHAR(10) NOT NULL,
    user_id INT,  -- Added user_id to associate students with users
    CHECK (registration_number BETWEEN 100000 AND 999999),  -- Ensures 6-digit number
    FOREIGN KEY (user_id) REFERENCES users(id)  -- Foreign key constraint to link students with users
);

