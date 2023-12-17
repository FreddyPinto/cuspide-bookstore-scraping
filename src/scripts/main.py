# Importaciones necesarias
import os
import requests
import pymysql
from bs4 import BeautifulSoup
from dotenv import load_dotenv
print("Iniciando")

# Carga las variables de entorno
load_dotenv()

host = os.getenv('DB_HOST')
user = os.getenv('DB_USERNAME')
password = os.getenv('DB_PASSWORD')

# Conexión a la base de datos MySQL
try:
    conn = pymysql.connect(host=host, user=user, password=password)
    cursor = conn.cursor()
    print("Conexión a la base de datos MySQL exitosa")
except Exception as e:
    print("Ocurrió un error al conectar a la base de datos MySQL:", e)

# Ejecuta una consulta para crear la base de datos
try:
    cursor.execute('CREATE DATABASE IF NOT EXISTS cuspide')
    print("Base de datos creada con exito")
except Exception as e:
    print("Ocurrió un error al crear la base de datos:", e)

try:
    # Usa la base de datos "cuspide"
    cursor.execute('USE cuspide')

    # Crea la tabla books
    query = """
    CREATE TABLE IF NOT EXISTS books (
        id_Libro INT AUTO_INCREMENT PRIMARY KEY,
        titulo VARCHAR(255),
        url VARCHAR(255),
        precio FLOAT,
        precio_usd FLOAT,
        precio_usd_blue FLOAT,
        fecha DATE
    )
    """
    cursor.execute(query)

    # Crea la tabla de auditoría de errores
    query = """
    CREATE TABLE IF NOT EXISTS errors (
        idError INT AUTO_INCREMENT PRIMARY KEY,
        titulo VARCHAR(255),
        url VARCHAR(255),
        fecha DATE
    )
    """
    cursor.execute(query)

    print("Tablas creadas con exito")
except Exception as e:
    print("Ocurrió un error al crear las tablas:", e)

# Obtiene el valor del dolar blue
url = 'https://dolarhoy.com/cotizaciondolarblue'
try:
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    dolar_blue = float(soup.find_all('div', class_='value')[1].get_text(strip=True).replace('$', ''))
    print('Valor dolar blue:', dolar_blue)
except Exception as e:
    print("Ocurrió un error al obtener el valor del dolar blue:", e)

# Obtener la página web de cuspide   
url = 'https://cuspide.com/100-mas-vendidos/'
try:
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    print("Solicitud a la página web de cuspide exitosa \nExtrayendo los datos de los libros:")
except Exception as e:
    print("Hay un problema con la solicitud a la página web de cuspide.", e)

    # Buscamos todos los elementos <h3> que contienen el título y la URL de cada libro
books = soup.find_all(
    "h3", class_="name product-title woocommerce-loop-product__title")

# Itera sobre cada elemento <h3> y extrae la URL y el título
for book in books:
    link = book.find("a")  
    title = link.text  
    url = link["href"]  
    try:
        # Obtiene la página web con la descripción de cada libro
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        # Obtiene el precio del libro en pesos y dolares
        p = soup.find("p", class_="price product-page-price")
        span1 = p.find('span', string='$').next_sibling
        span2 = soup.find("span", style="font-size: 1.3em")
        precio = float(span1.get_text(strip=True).replace('.', '').replace(',', '.'))
        precio_usd = float(span2.get_text(strip=True).replace('.', '').replace(',', '.'))
        # Calcula el precio del libro en dolares blue
        precio_usd_blue = round(precio/dolar_blue, 2)

        # Inserta los datos en la tabla books
        query = f"""
        INSERT INTO books (titulo, url, precio, precio_usd, precio_usd_blue, fecha)
        VALUES ("{title}", "{url}", {precio}, {precio_usd}, {precio_usd_blue}, NOW())
        """
        cursor.execute(query)
        conn.commit()

        # Imprime el libro
        print(f"Título: {title}") 
        print(f"URL: {url}") 
        print(f"AR$: {precio}")
        print(f"U$s: {precio_usd}") 
        print(f"U$s Blue: {precio_usd_blue}") 
        print()
        
    except Exception as e:
        # Imprime el titulo del libro y el error que ocurrió al extraer los datos
        print(f"Ocurrió un error al extraer los datos del libro {title}:", e)
        print()
        # Inserta los datos en la tabla de auditoría de errores
        query = f"""
        INSERT INTO errors (titulo, url, fecha)
        VALUES ("{title}", "{url}", NOW())
        """
        cursor.execute(query)
        conn.commit()

# Cierra la conexión a la base de datos
cursor.close()
conn.close()
print("Hecho")