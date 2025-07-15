import sqlite3

import unicodedata


# Función para normalizar el texto
def normalizar_texto(texto):
    texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII')
    return texto.lower()


def limpia_bbdd(conn, cursor):
    cursor.execute("""
                DELETE FROM convivencia_amonestaciones;
                """)

    cursor.execute("""
                    DELETE FROM centro_alumnos;
                    """)

    cursor.execute("""
                    DELETE FROM centro_profesores;
                    """)

    cursor.execute("""
                        DELETE FROM convivencia_sanciones;
                        """)

    cursor.execute("""
                    DELETE FROM sqlite_sequence WHERE name='convivencia_amonestaciones';
                    """)

    cursor.execute("""
                        DELETE FROM sqlite_sequence WHERE name='convivencia_sanciones';
                        """)

    cursor.execute("""
                        DELETE FROM sqlite_sequence WHERE name='centro_alumnos';
                        """)
    cursor.execute("""
                        DELETE FROM sqlite_sequence WHERE name='centro_profesores';
                        """)

    cursor.execute("""
                            UPDATE SQLITE_SEQUENCE SET SEQ=0 WHERE NAME='centro_profesores';
                            """)

    conn.commit()


# Función para verificar la existencia de una columna en una tabla
def columna_existe(cursor, tabla, columna):
    cursor.execute(f"PRAGMA table_info({tabla})")
    columnas = [info[1] for info in cursor.fetchall()]
    return columna in columnas


# Función para insertar alumnos y obtener el nuevo id
# Función para insertar o buscar un alumno y obtener el nuevo ID
def get_or_insert_alumno(cursor_fusionada, alumno, alumno_map):
    nombre_normalizado = normalizar_texto(alumno['Nombre'])
    fecha_nacimiento = alumno['Fecha_nacimiento']
    clave_alumno = (nombre_normalizado, fecha_nacimiento)

    if clave_alumno in alumno_map:
        return alumno_map[clave_alumno]

    cursor_fusionada.execute("""
        SELECT id FROM centro_alumnos 
        WHERE LOWER(Nombre)=? AND Fecha_nacimiento=?
    """, (nombre_normalizado, fecha_nacimiento))
    result = cursor_fusionada.fetchone()
    if result:
        nuevo_id = result[0]
    else:
        cursor_fusionada.execute("""
            INSERT INTO centro_alumnos 
            (Nombre, DNI, Direccion, CodPostal, Localidad, Fecha_nacimiento, Provincia,
             Ap1tutor, Ap2tutor, Nomtutor, Telefono1, Telefono2, Obs, email)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (alumno['Nombre'], alumno['DNI'], alumno['Direccion'], alumno['CodPostal'], alumno['Localidad'],
              alumno['Fecha_nacimiento'], alumno['Provincia'], alumno['Ap1tutor'], alumno['Ap2tutor'],
              alumno['Nomtutor'], alumno['Telefono1'], alumno['Telefono2'], alumno['Obs'], alumno.get('email', '')))
        nuevo_id = cursor_fusionada.lastrowid

    alumno_map[clave_alumno] = nuevo_id
    return nuevo_id


# Función para insertar o buscar un profesor y obtener el nuevo ID
def get_or_insert_profesor(cursor_fusionada, profesor, profesor_map):
    nombre_normalizado = normalizar_texto(profesor['Nombre'])
    apellidos_normalizados = normalizar_texto(profesor['Apellidos'])
    clave_profesor = (nombre_normalizado, apellidos_normalizados)

    if clave_profesor in profesor_map:
        return profesor_map[clave_profesor]

    cursor_fusionada.execute("""
        SELECT id FROM centro_profesores 
        WHERE LOWER(Nombre)=? AND LOWER(Apellidos)=?
    """, (nombre_normalizado, apellidos_normalizados))
    result = cursor_fusionada.fetchone()
    if result:
        nuevo_id = result[0]
    else:
        cursor_fusionada.execute("""
            INSERT INTO centro_profesores 
            (Nombre, Apellidos, Telefono, Movil, Email, Baja, Ce, Etcp, Tic, Bil, Departamento_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (profesor['Nombre'], profesor['Apellidos'], profesor['Telefono'], profesor['Movil'],
              profesor['Email'], profesor['Baja'], profesor['Ce'], profesor['Etcp'],
              profesor['Tic'], profesor['Bil'], profesor['Departamento_id']))
        nuevo_id = cursor_fusionada.lastrowid

    profesor_map[clave_profesor] = nuevo_id
    return nuevo_id


# Conexión a la nueva base de datos fusionada
conn_fusionada = sqlite3.connect('olddbs/fusionada_hastadb2024.sqlite3')
cursor_fusionada = conn_fusionada.cursor()

limpia_bbdd(conn_fusionada, cursor_fusionada)

# Diccionario para mapear rutas de base de datos a IDs personalizados de curso academico
db_ids = {
    'olddbs/db2017.sqlite3': 12,
    'olddbs/db2018.sqlite3': 13,
    'olddbs/db2019.sqlite3': 14,
    'olddbs/db2020.sqlite3': 1,
    'olddbs/db2021.sqlite3': 6,
    'olddbs/db2022.sqlite3': 5,
    'olddbs/db2023.sqlite3': 4,
    'olddbs/db2024.sqlite3': 3
}

# Diccionarios para mapear IDs originales a IDs fusionados
alumno_map = {}
profesor_map = {}

# Procesar cada base de datos original
for db_path, curso_academico_id in db_ids.items():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Comprobar si la columna 'email' existe en la tabla centro_alumnos
    email_existe = columna_existe(cursor, 'centro_alumnos', 'email')

    # Comprobar si la columna 'NoExpulsion' existe en la tabla convivencia_sanciones
    noexpulsion_existe = columna_existe(cursor, 'convivencia_sanciones', 'NoExpulsion')

    # Migrar alumnos y profesores antes de migrar las amonestaciones
    cursor.execute("SELECT * FROM centro_alumnos")
    alumnos = cursor.fetchall()
    for alumno in alumnos:
        alumno_data = {
            'Nombre': alumno[1],
            'DNI': alumno[2],
            'Direccion': alumno[3],
            'CodPostal': alumno[4],
            'Localidad': alumno[5],
            'Fecha_nacimiento': alumno[6],
            'Provincia': alumno[7],
            'Ap1tutor': alumno[8],
            'Ap2tutor': alumno[9],
            'Nomtutor': alumno[10],
            'Telefono1': alumno[11],
            'Telefono2': alumno[12],
            'Obs': alumno[13],
        }

        if email_existe:
            alumno_data['email'] = alumno[15]

        # Insertar o recuperar ID en la base fusionada
        get_or_insert_alumno(cursor_fusionada, alumno_data, alumno_map)

    cursor.execute("SELECT * FROM centro_profesores")
    profesores = cursor.fetchall()
    for profesor in profesores:
        profesor_data = {
            'Nombre': profesor[1],
            'Apellidos': profesor[2],
            'Telefono': profesor[3],
            'Movil': profesor[4],
            'Email': profesor[5],
            'Baja': profesor[6],
            'Ce': profesor[7],
            'Etcp': profesor[8],
            'Tic': profesor[9],
            'Bil': profesor[10],
            'Departamento_id': profesor[11]
        }

        # Insertar o recuperar ID en la base fusionada
        get_or_insert_profesor(cursor_fusionada, profesor_data, profesor_map)

    # Migrar amonestaciones
    cursor.execute("SELECT * FROM convivencia_amonestaciones")
    amonestaciones = cursor.fetchall()
    for amonestacion in amonestaciones:
        # Obtener el ID de Alumno y Profesor desde la tabla amonestaciones
        alumno_id_original = amonestacion[4]  # IdAlumno_id
        profesor_id_original = amonestacion[5]  # Profesor_id

        # Buscar el alumno en el mapa de IDs fusionados
        cursor.execute("SELECT Nombre, Fecha_nacimiento FROM centro_alumnos WHERE id=?", (alumno_id_original,))
        alumno_original = cursor.fetchone()
        if alumno_original:
            nombre_normalizado = normalizar_texto(alumno_original[0])  # Nombre del alumno
            fecha_nacimiento = alumno_original[1]  # Fecha_nacimiento del alumno
            IdAlumno_id = alumno_map.get((nombre_normalizado, fecha_nacimiento))
        else:
            IdAlumno_id = None

        # Buscar el profesor en el mapa de IDs fusionados
        cursor.execute("SELECT Nombre, Apellidos FROM centro_profesores WHERE id=?", (profesor_id_original,))
        profesor_original = cursor.fetchone()
        if profesor_original:
            nombre_normalizado_profesor = normalizar_texto(profesor_original[0])  # Nombre del profesor
            apellidos_normalizados_profesor = normalizar_texto(profesor_original[1])  # Apellidos del profesor
            Profesor_id = profesor_map.get((nombre_normalizado_profesor, apellidos_normalizados_profesor))
        else:
            Profesor_id = None

        # Verificar si se encontraron los IDs de alumno y profesor
        if IdAlumno_id is None or Profesor_id is None:
            print(
                f"Advertencia: Amonestación omitida porque no se encontró el ID para el alumno o profesor en la base de datos original '{db_path}'")
            continue

        # Insertar la amonestación con los IDs fusionados
        cursor_fusionada.execute("""
                INSERT INTO convivencia_amonestaciones (Fecha, Hora, Comentario, IdAlumno_id, Profesor_id, Tipo_id, curso_academico_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
            amonestacion[1], amonestacion[2], amonestacion[3], IdAlumno_id, Profesor_id, amonestacion[6], curso_academico_id))

    # Obtener la estructura de la tabla de sanciones para identificar la posición de IdAlumno_id
    cursor.execute("PRAGMA table_info(convivencia_sanciones)")
    columnas = cursor.fetchall()
    col_index = {col[1]: col[0] for col in columnas}
    id_alumno_index = col_index.get('IdAlumno_id')
    sancion_index = col_index.get('Sancion')
    comentario_index = col_index.get('Comentario')

    # Migrar sanciones
    cursor.execute("SELECT * FROM convivencia_sanciones")
    sanciones = cursor.fetchall()
    for sancion in sanciones:
        # Obtener el ID de Alumno desde la tabla sanciones
        alumno_id_original = sancion[id_alumno_index]

        # Buscar el alumno en el mapa de IDs fusionados
        cursor.execute("SELECT Nombre, Fecha_nacimiento FROM centro_alumnos WHERE id=?", (alumno_id_original,))
        alumno_original = cursor.fetchone()
        if alumno_original:
            nombre_normalizado = normalizar_texto(alumno_original[0])  # Nombre del alumno
            fecha_nacimiento = alumno_original[1]  # Fecha_nacimiento del alumno
            IdAlumno_id = alumno_map.get((nombre_normalizado, fecha_nacimiento))
        else:
            IdAlumno_id = None

        # Verificar si se encontraron los IDs de alumno
        if IdAlumno_id is None:
            print(
                f"Advertencia: Sanción omitida porque no se encontró el ID para el alumno en la base de datos original '{db_path}'")
            continue

        # Insertar la sancion con los IDs fusionados
        cursor_fusionada.execute("""
                INSERT INTO convivencia_sanciones (Fecha, Fecha_fin, Sancion, Comentario, IdAlumno_id, NoExpulsion, curso_academico_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
            sancion[1], sancion[2], sancion[sancion_index], sancion[comentario_index], IdAlumno_id, 0,
            curso_academico_id))

    conn.commit()
    conn.close()

conn_fusionada.commit()
conn_fusionada.close()
print("Fusión completada.")
