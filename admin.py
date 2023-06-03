import hashlib
import streamlit as st
import pandas as pd
from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import unpad
from Cryptodome.Util.Padding import pad
import os
import base64
from io import BytesIO
import PyPDF2
from streamlit_option_menu import option_menu
import mysql.connector


selected = option_menu(None, ["Import Data", "Encryption", "Decryption", "Database"],
                       icons=['cloud-upload', 'gear', "kanban", "house"],
                       menu_icon="cast", default_index=0, orientation="horizontal")

def encrypt_file(key, input_file, output_file):
    cipher = AES.new(key, AES.MODE_CBC)
    filesize = os.path.getsize(input_file)

    with open(input_file, 'rb') as file:
        plaintext = file.read()

    encrypted_data = cipher.encrypt(pad(plaintext, AES.block_size))

    with open(output_file, 'wb') as file:
        file.write(cipher.iv)
        file.write(encrypted_data)

def save_uploaded_file(uploaded_file):
    with open(uploaded_file.name, 'wb') as file:
        file.write(uploaded_file.getbuffer())
    # st.success(f"File '{uploaded_file.name}' berhasil disimpan.")

def decrypt_file(key, input_file, output_file):
    with open(input_file, 'rb') as file:
        iv = file.read(16)
        ciphertext = file.read()

    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted_data = unpad(cipher.decrypt(ciphertext), AES.block_size)

    with open(output_file, 'wb') as file:
        file.write(decrypted_data)

def read_pdf(file_content):
    pdf_file = BytesIO(file_content)
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    num_pages = len(pdf_reader.pages)

    st.text(f"Jumlah halaman: {num_pages}")
    st.text("Isi file terdekripsi (hanya halaman pertama ditampilkan):")
    for page_num in range(num_pages):
        page = pdf_reader.pages[page_num]
        st.write(page.extract_text())

def download_file(file_content, file_name, file_format):
    b64 = base64.b64encode(file_content).decode()
    href = f'<a href="data:file/{file_format};base64,{b64}" download="{file_name}">Download {file_name}</a>'
    st.markdown(href, unsafe_allow_html=True)

# Fungsi untuk membuat koneksi ke database MySQL
def create_connection():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="kriptografi"
    )
    return conn

# Fungsi untuk menyimpan file PDF ke dalam database
def save_pdf_to_db(nama_file, file_path):
    conn = create_connection()
    cursor = conn.cursor()

    with open(file_path, 'rb') as file:
        pdf_data = file.read()

    query = "INSERT INTO pdf_files (nama_file, data_pdf) VALUES (%s, %s)"
    values = (nama_file, pdf_data)

    cursor.execute(query, values)
    conn.commit()

    cursor.close()
    conn.close()

if selected == "Import Data":
    st.title("Import Data PDF")

    nama_file = st.text_input("Nama File")
    file = st.file_uploader("Upload File PDF")

    if st.button("Import"):
        if nama_file.strip() == "":
            st.error("Nama file tidak boleh kosong.")
        elif file is None:
            st.error("File PDF belum diunggah.")
        else:
            save_pdf_to_db(nama_file, file.name)
            st.success(f"File '{nama_file}' berhasil diimpor ke dalam database.")

# Fungsi untuk menyimpan hasil enkripsi ke dalam tabel pdf_enkripsi
def save_encrypted_file(input_file, output_file, key):
    conn = create_connection()
    cursor = conn.cursor()

    # Query untuk menyimpan data hasil enkripsi ke dalam tabel pdf_enkripsi
    query = "INSERT INTO pdf_enkripsi (nama_file, file_terenkripsi, kunci) VALUES (%s, %s, %s)"
    cursor.execute(query, (input_file, output_file, key))
    conn.commit()

    cursor.close()
    conn.close()

if selected == 'Encryption':
    st.write("Pilih file yang akan dienkripsi (.pdf) :")
    input_file = st.file_uploader("Upload File")

    if input_file:
        save_uploaded_file(input_file)
        key = st.text_input("Masukkan Kunci Enkripsi (16 karakter):")

        if len(key) == 16:
            output_file = f"encrypted_{input_file.name}"
            encrypt_file(key.encode(), input_file.name, output_file)

            st.success(f"File '{input_file.name}' berhasil dienkripsi dan disimpan sebagai '{output_file}' dan ditransfer ke Database.")

            # Simpan hasil enkripsi ke dalam tabel pdf_enkripsi
            save_encrypted_file(input_file.name, output_file, key)

        elif len(key) > 0:
            st.error("Kunci enkripsi harus memiliki 16 karakter.")

        if len(key) == 0:
            st.info("Masukkan kunci enkripsi.")


if selected == "Decryption":
    st.write("Pilih file yang akan didekripsi (.pdf) :")
    input_file = st.file_uploader("Upload File")

    if input_file:
        save_uploaded_file(input_file)
        key = st.text_input("Masukkan Kunci Dekripsi (16 karakter):")

        if len(key) == 16:
            output_file = f"decrypted_{input_file.name}"
            decrypt_file(key.encode(), input_file.name, output_file)

            st.success(f"File '{input_file.name}' berhasil didekripsi dan disimpan sebagai '{output_file}'.")

            st.write("Isi file terdekripsi:")
            with open(output_file, 'rb') as file:
                file_content = file.read()
            read_pdf(file_content)

            st.write("Pilih format file yang akan diunduh:")
            download_format = st.selectbox("Format", [".txt", ".pdf"])
            if download_format == ".txt":
                st.text("Download file terdekripsi sebagai:")
                download_file(file_content, output_file + ".txt", "text/plain")
            elif download_format == ".pdf":
                st.text("Download file terdekripsi sebagai:")
                download_file(file_content, output_file, "application/pdf")

            # Simpan file terdekripsi ke tabel pdf_dekripsi
            conn = create_connection()
            cursor = conn.cursor()
            with open(output_file, 'rb') as file:
                file_data = file.read()
            file_data_encoded = base64.b64encode(file_data)
            cursor.execute("ALTER TABLE pdf_dekripsi MODIFY data_pdf MEDIUMBLOB")
            cursor.execute("INSERT INTO pdf_dekripsi (nama_file, data_pdf) VALUES (%s, %s)", (output_file, file_data_encoded))
            conn.commit()
            conn.close()

        elif len(key) > 0:
            st.error("Kunci dekripsi harus memiliki 16 karakter.")

        if len(key) == 0:
            st.info("Masukkan kunci dekripsi.")

# Fungsi untuk menghasilkan hash dari nilai atribut kunci
def generate_hash(key):
    hash_object = hashlib.sha256(key.encode())
    return hash_object.hexdigest()

# Fungsi untuk menampilkan isi tabel
def tampilkan_tabel(conn, nama_tabel):
    cursor = conn.cursor()
    cursor.execute(f"SHOW COLUMNS FROM {nama_tabel}")
    columns = [column[0] for column in cursor.fetchall()]

    # Hapus kolom dengan tipe data BigInt64Array
    columns_to_ignore = ['id']  # Ganti dengan nama kolom BigInt64Array yang ada di tabel
    columns = [column for column in columns if column not in columns_to_ignore]

    query = f"SELECT {', '.join(columns)} FROM {nama_tabel}"
    cursor.execute(query)
    data = cursor.fetchall()

    # Membuat salinan data dengan nilai atribut kunci di-hash
    hashed_data = []
    for row in data:
        hashed_row = list(row)
        if 'kunci' in columns:  # Periksa apakah atribut 'kunci' ada dalam tabel
            kunci_index = columns.index('kunci')
            hashed_key = generate_hash(hashed_row[kunci_index])  # Menghash nilai atribut kunci
            hashed_row[kunci_index] = hashed_key
        hashed_data.append(tuple(hashed_row))

    df = pd.DataFrame(hashed_data, columns=columns)
    st.dataframe(df)    

# Function to delete data based on ID
def delete_data(conn, table_name, id):
    query = f"DELETE FROM {table_name} WHERE id = {id}"
    cursor = conn.cursor()
    cursor.execute(query)
    conn.commit()
    st.write(f"Data with ID {id} successfully deleted from {table_name}.")

if selected == "Database":
    # Judul aplikasi
    st.title("Tampilan Tabel Database MySQL")

    # Buat koneksi ke database
    conn = create_connection()

    # Daftar tabel
    daftar_tabel = ['users', 'pdf_files', 'pdf_enkripsi', 'pdf_dekripsi']  # Ganti dengan nama tabel yang sesuai

    # Pilihan tabel
    pilihan_tabel = st.selectbox("Pilih Tabel", daftar_tabel)

    # Tombol tampilkan
    if st.button("Tampilkan"):
        if pilihan_tabel == "pdf_enkripsi":
            tampilkan_tabel(conn, pilihan_tabel)
        else:
            tampilkan_tabel(conn, pilihan_tabel)

    # Tutup koneksi
    conn.close()