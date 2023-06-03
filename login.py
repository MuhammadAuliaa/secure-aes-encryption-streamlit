import streamlit as st
import mysql.connector
import bcrypt
import subprocess

# Fungsi untuk membuat koneksi ke database MySQL
def create_connection():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="kriptografi"
    )
    return conn

# Fungsi untuk menambahkan pengguna baru ke tabel
def add_user(username, password, level):
    conn = create_connection()
    cursor = conn.cursor()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    query = "INSERT INTO users (username, password, level) VALUES (%s, %s, %s)"
    values = (username, hashed_password, level)
    cursor.execute(query, values)
    conn.commit()
    conn.close()

# Fungsi untuk mendapatkan pengguna berdasarkan username
def get_user(username):
    conn = create_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM users WHERE username = %s"
    values = (username,)
    cursor.execute(query, values)
    user = cursor.fetchone()
    conn.close()
    return user

# Fungsi untuk memverifikasi kata sandi
def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password)

# Main program
def main():
    page = st.sidebar.selectbox("Select Page", ["Login", "Register"])

    if page == "Login":
        st.title("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            user = get_user(username)
            if user:
                if verify_password(password, user[2]):
                    if user[3] == "user":
                        st.success("Logged in as User")
                        subprocess.Popen(["streamlit", "run", "user.py"]) 
                    elif user[3] == "admin":
                        st.success("Logged in as Admin")
                        subprocess.Popen(["streamlit", "run", "admin.py"])
                else:
                    st.warning("Incorrect password")
            else:
                st.warning("Username not found")

    elif page == "Register":
        st.title("Register")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        level = st.selectbox("Level", ["user", "admin"])
        if st.button("Register"):
            user = get_user(username)
            if user:
                st.warning("Username already exists")
            else:
                add_user(username, password, level)
                st.success("Registration successful")

if __name__ == '__main__':
    main()
