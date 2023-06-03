import streamlit as st
from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import unpad
from Cryptodome.Util.Padding import pad
import os
import base64
from io import BytesIO
import PyPDF2
from streamlit_option_menu import option_menu
import mysql.connector


selected = option_menu(None, ["Import Data", "Encryption", "Decryption", "About"],
                       icons=['cloud-upload', 'gear', "kanban", "gear"],
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



        
if selected == "About":
    st.title("Enkripsi Dekripsi File Rangkuman Transaksi Jual Beli SahamKeuangan dengan AES")

    st.write("Program ini adalah sebuah aplikasi yang menggunakan algoritma AES (Advanced Encryption Standard) untuk melakukan enkripsi dan dekripsi file yang berisi rangkuman transaksi keuangan. Algoritma AES merupakan salah satu algoritma kriptografi yang kuat dan sering digunakan untuk melindungi keamanan data. Dengan menggunakan aplikasi ini, Anda dapat mengunggah file rangkuman transaksi keuangan yang ingin Anda amankan. Setelah mengunggah file, Anda dapat memasukkan kunci enkripsi yang terdiri dari 16 karakter. Setelah proses enkripsi selesai, aplikasi akan menghasilkan file terenkripsi yang dapat Anda simpan. File ini hanya dapat diakses dengan menggunakan kunci dekripsi yang sama yang digunakan saat melakukan enkripsi.")

    st.write("Selain itu, aplikasi juga menyediakan fitur dekripsi untuk mengembalikan file terenkripsi ke bentuk aslinya. Anda dapat memilih file terenkripsi yang ingin Anda dekripsi dan memasukkan kunci dekripsi yang sesuai. Setelah proses dekripsi selesai, Anda dapat melihat isi file terdekripsi dan mendownloadnya dalam format yang diinginkan, seperti file teks (.txt) atau file PDF (.pdf). Dengan menggunakan algoritma AES dan aplikasi ini, Anda dapat melindungi keamanan dan kerahasiaan file rangkuman transaksi keuangan Anda, sehingga hanya dapat diakses oleh pihak yang memiliki kunci dekripsi yang tepat.")

    # Tambahkan kode Streamlit untuk fitur-fitur lainnya (unggah file, enkripsi, dekripsi, dll.)


