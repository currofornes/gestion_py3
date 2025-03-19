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

# Borrar los registros duplicados que dan error de unique together

with connection.cursor() as cursor:
    cursor.execute("PRAGMA foreign_keys = OFF;")  # Desactiva restricciones
    try:
        # guardias.TiempoGuardia
        cursor.execute(""" DELETE FROM guardias_tiempoguardia WHERE rowid NOT IN (
                               SELECT MIN(rowid) FROM guardias_tiempoguardia
                               GROUP BY profesor_id, dia_semana, tramo, tiempo_asignado, item_guardia_id, curso_academico_id); """)

        # convivencia.Sanciones
        cursor.execute(""" DELETE FROM convivencia_sanciones WHERE rowid NOT IN (
                               SELECT MIN(rowid) FROM convivencia_sanciones
                               GROUP BY IdAlumno_id, Fecha, Fecha_fin, Sancion, Comentario, curso_academico_id); """)

        # convivencia.Amonestaciones
        cursor.execute(""" DELETE FROM convivencia_amonestaciones WHERE rowid NOT IN (
                               SELECT MIN(rowid) FROM convivencia_amonestaciones
                               GROUP BY IdAlumno_id, Fecha, Hora, Profesor_id, Tipo_id, Comentario, DerivadoConvivencia,
                                        FamiliarComunicado, FechaComunicado, HoraComunicado, Medio, TelefonoComunicado,
                                        ObservacionComunicado, curso_academico_id); """)

        # tde.IncidenciasTIC
        cursor.execute(""" DELETE FROM tde_incidenciastic WHERE rowid NOT IN (
                               SELECT MIN(rowid) FROM tde_incidenciastic
                               GROUP BY profesor_id, aula_id, prioridad_id, comentario, curso_academico_id); """)

        cursor.execute(""" DELETE FROM tde_incidenciastic_elementos WHERE incidenciastic_id NOT IN (
                                SELECT rowid FROM tde_incidenciastic);""")
    finally:
        cursor.execute("PRAGMA foreign_keys = ON;")  # Reactiva restricciones



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
    "analres_calificaciones",
    "analres_indicadoresalumnado",
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

# Desvincular la base de datos antigua
cursor.execute("DETACH DATABASE antigua;")

# Cerrar conexión
conn.close()

print("✅ Datos copiados con éxito.")

# Borrar propuestas de sanción para empezar desde cero
from convivencia.models import PropuestasSancion
PropuestasSancion.objects.all().delete()