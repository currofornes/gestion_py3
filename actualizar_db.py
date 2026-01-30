# Este código para poder usar ORM de django
import os
import django

# Especifica la configuración de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion.settings')

# Inicializa Django
django.setup()

# Aquí el resto del código
from django.apps import apps
from django.db import connection
import subprocess

# Hacer las migraciones
print(f'Calculando migraciones')
subprocess.run(['python', 'manage.py', 'makemigrations'])
subprocess.run(['python', 'manage.py', 'migrate'])


# Copiar los datos relacionados con Análisis de Resultados
import sqlite3

# Rutas de las bases de datos
DB_ACTUAL = "basededatos/db.sqlite3"
DB_ANTIGUA = "basededatos/db_antigua.sqlite3"

# Conectar a la base de datos actual
conn = sqlite3.connect(DB_ACTUAL)
cursor = conn.cursor()

# Adjuntar la base de datos antigua
cursor.execute(f"ATTACH DATABASE '{DB_ANTIGUA}' AS antigua;")

# Copiar los datos de cada tabla
tablas = [
    "centro_centros",
    "centro_infoalumnos",
]

for tabla in tablas:
    print(f"Copiando datos de {tabla}...")
    cursor.execute(f"""
        INSERT INTO {tabla}
        SELECT * FROM antigua.{tabla}
        WHERE id NOT IN (SELECT id FROM {tabla});
    """)
    conn.commit()

# Actualizar los centros de cada alumno
print(f"Actualizando Centros de EP y ESO para alumnos en centro_alumnos...")

# 1. Actualizar Centro_EP_id
cursor.execute(f"""
    UPDATE centro_alumnos
    SET Centro_EP_id = (
        SELECT antigua_a.Centro_EP_id 
        FROM antigua.centro_alumnos AS antigua_a
        WHERE antigua_a.id = centro_alumnos.id
    )
    WHERE Centro_EP_id IS NULL 
      AND (SELECT antigua_a.Centro_EP_id FROM antigua.centro_alumnos AS antigua_a WHERE antigua_a.id = centro_alumnos.id) IS NOT NULL;
""")

# 2. Actualizar Centro_ESO_id
cursor.execute(f"""
    UPDATE centro_alumnos
    SET Centro_ESO_id = (
        SELECT antigua_a.Centro_ESO_id 
        FROM antigua.centro_alumnos AS antigua_a
        WHERE antigua_a.id = centro_alumnos.id
    )
    WHERE Centro_ESO_id IS NULL 
      AND (SELECT antigua_a.Centro_ESO_id FROM antigua.centro_alumnos AS antigua_a WHERE antigua_a.id = centro_alumnos.id) IS NOT NULL;
""")

conn.commit()
# Desvincular la base de datos antigua
cursor.execute("DETACH DATABASE antigua;")

# Cerrar conexión
conn.close()

print("✅ Datos copiados con éxito.")