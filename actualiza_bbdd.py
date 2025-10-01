import os
import csv
import sqlite3
from pathlib import Path
import django
from django.core.management import call_command


# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion.settings')
django.setup()

# Función para verificar la existencia de una tabla
def table_exists(cursor, table_name):
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';")
    return cursor.fetchone() is not None


# Función para verificar la existencia de una columna en una tabla
def column_exists(cursor, table_name, column_name):
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = [info[1] for info in cursor.fetchall()]
    return column_name in columns


################################################## APP CENTRO ####################################################

def migrate_centro_data(conn):
    cursor = conn.cursor()
    # Actualizar la tabla centro_alumnos
    if table_exists(cursor,'centro_alumnos'):
        # Añadir columnas si no existen


        if not column_exists(cursor,'centro_alumnos', 'Unidad_id'):
            cursor.execute("ALTER TABLE centro_alumnos ADD COLUMN Unidad_id INTEGER REFERENCES centro_curso(id)")

        if not column_exists(cursor,'centro_alumnos', 'NIE'):
            cursor.execute("ALTER TABLE centro_alumnos ADD COLUMN NIE VARCHAR(20)")

        # Actualizar las definiciones de columna según sea necesario
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS centro_alumnos_new (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            Nombre VARCHAR(50) NOT NULL,
            DNI VARCHAR(10),
            Direccion VARCHAR(60),
            CodPostal VARCHAR(5),
            Localidad VARCHAR(30),
            Fecha_nacimiento DATE NOT NULL,
            Provincia VARCHAR(30),
            Ap1tutor VARCHAR(20),
            Ap2tutor VARCHAR(20),
            Nomtutor VARCHAR(20),
            Telefono1 VARCHAR(12),
            Telefono2 VARCHAR(12),
            email VARCHAR(70),
            Obs TEXT,
            Unidad_id INTEGER REFERENCES centro_cursos (id),
            NIE VARCHAR(20)
        );
        """)

        # Insertar los datos relevantes de la tabla antigua a la nueva
        # Construir la consulta de inserción según la existencia de la columna NIE
        if column_exists(cursor,'centro_alumnos', 'NIE'):
            insert_query = """
                INSERT INTO centro_alumnos_new (
                    id, Nombre, DNI, Direccion, CodPostal, Localidad, Fecha_nacimiento, Provincia,
                    Ap1tutor, Ap2tutor, Nomtutor, Telefono1, Telefono2, email, Obs, Unidad_id, NIE
                ) SELECT
                    id, Nombre, DNI, Direccion, CodPostal, Localidad, Fecha_nacimiento, Provincia,
                    Ap1tutor, Ap2tutor, Nomtutor, Telefono1, Telefono2, email, Obs, Unidad_id, NIE
                FROM centro_alumnos
                """
        else:
            insert_query = """
                INSERT INTO centro_alumnos_new (
                    id, Nombre, DNI, Direccion, CodPostal, Localidad, Fecha_nacimiento, Provincia,
                    Ap1tutor, Ap2tutor, Nomtutor, Telefono1, Telefono2, email, Obs, Unidad_id, NIE
                ) SELECT
                    id, Nombre, DNI, Direccion, CodPostal, Localidad, Fecha_nacimiento, Provincia,
                    Ap1tutor, Ap2tutor, Nomtutor, Telefono1, Telefono2, email, Obs, Unidad_id, ''
                FROM centro_alumnos
                """

        cursor.execute(insert_query)
        cursor.execute("DROP TABLE centro_alumnos")
        cursor.execute("ALTER TABLE centro_alumnos_new RENAME TO centro_alumnos")

    # Actualizar la tabla centro_profesores
    if table_exists(cursor,'centro_profesores'):
        # Añadir columnas si no existen
        if not column_exists(cursor,'centro_profesores', 'DNI'):
            cursor.execute("ALTER TABLE centro_profesores ADD COLUMN DNI VARCHAR(10)")

        if not column_exists(cursor,'centro_profesores', 'password_changed'):
            cursor.execute("ALTER TABLE centro_profesores ADD COLUMN password_changed BOOL DEFAULT 0")

        if not column_exists(cursor,'centro_profesores', 'user_id'):
            cursor.execute("ALTER TABLE centro_profesores ADD COLUMN user_id INTEGER REFERENCES auth_user (id)")

        # Actualizar las definiciones de columna según sea necesario
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS centro_profesores_new (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            Nombre VARCHAR(20) NOT NULL,
            Apellidos VARCHAR(30) NOT NULL,
            DNI VARCHAR(10),
            Telefono VARCHAR(9),
            Movil VARCHAR(9),
            Email VARCHAR(254) NOT NULL,
            Baja BOOL NOT NULL,
            Departamento_id INTEGER REFERENCES centro_departamentos (id),
            password_changed BOOL DEFAULT 0,
            user_id INTEGER REFERENCES auth_user (id)
        );
        """)

        insert_query = """
                    INSERT INTO centro_profesores_new (
                        id, Nombre, Apellidos, DNI, Telefono, Movil, Email, Baja,
                        Departamento_id, password_changed, user_id
                    ) SELECT
                        id, Nombre, Apellidos, DNI, Telefono, Movil, Email, Baja,
                        Departamento_id, password_changed, user_id
                    FROM centro_profesores
                    """

        cursor.execute(insert_query)
        cursor.execute("DROP TABLE centro_profesores")
        cursor.execute("ALTER TABLE centro_profesores_new RENAME TO centro_profesores")

    # Crear nuevas tablas si no existen
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS centro_cursoacademico (
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        nombre VARCHAR(100) NOT NULL,
        año_inicio INTEGER,
        año_fin INTEGER
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS centro_aulas (
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        Aula VARCHAR(30) NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS centro_niveles (
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        Nombre VARCHAR(255) NOT NULL,
        Abr VARCHAR(50) NOT NULL
    );
    """)

    # Actualizar la tabla centro_cursos
    if table_exists(cursor,'centro_cursos'):

        # Añadir columnas si no existen

        if not column_exists(cursor,'centro_cursos', 'Nivel_id'):
            cursor.execute("ALTER TABLE centro_cursos ADD COLUMN Abe VARCHAR(10)")

        if not column_exists(cursor,'centro_cursos', 'Nivel_id'):
            cursor.execute("ALTER TABLE centro_cursos ADD COLUMN Nivel_id INTEGER REFERENCES centro_niveles (id)")

        if not column_exists(cursor,'centro_cursos', 'Aula_id'):
            cursor.execute("ALTER TABLE centro_cursos ADD COLUMN Aula_id INTEGER REFERENCES centro_aulas (id)")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS centro_cursos_new (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            Curso VARCHAR(30) NOT NULL,
            Tutor_id INTEGER REFERENCES centro_profesores (id),
            Abe VARCHAR(10),
            Nivel_id INTEGER REFERENCES centro_niveles (id),
            Aula_id INTEGER REFERENCES centro_aulas (id)
        );
        """)

        cursor.execute(
            "INSERT INTO centro_cursos_new SELECT id, Curso, Tutor_id, Abe, Nivel_id, Aula_id FROM centro_cursos")
        cursor.execute("DROP TABLE centro_cursos")
        cursor.execute("ALTER TABLE centro_cursos_new RENAME TO centro_cursos")

    # Actualizar la tabla centro_areas
    if table_exists(cursor,'centro_areas'):
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS centro_areas_new (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            Nombre VARCHAR(30) NOT NULL
        );
        """)

        cursor.execute("INSERT INTO centro_areas_new SELECT * FROM centro_areas")
        cursor.execute("DROP TABLE centro_areas")
        cursor.execute("ALTER TABLE centro_areas_new RENAME TO centro_areas")

    # Actualizar la tabla centro_departamentos
    if table_exists(cursor,'centro_departamentos'):
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS centro_departamentos_new (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            Abr VARCHAR(4) NOT NULL,
            Nombre VARCHAR(30) NOT NULL
        );
        """)

        cursor.execute("INSERT INTO centro_departamentos_new SELECT * FROM centro_departamentos")
        cursor.execute("DROP TABLE centro_departamentos")
        cursor.execute("ALTER TABLE centro_departamentos_new RENAME TO centro_departamentos")

    # Actualizar la tabla centro_areas_departamentos
    if table_exists(cursor,'centro_areas_Departamentos'):
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS centro_areas_Departamentos_new (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            areas_id INTEGER NOT NULL REFERENCES centro_areas (id),
            departamentos_id INTEGER NOT NULL REFERENCES centro_departamentos (id)
        );
        """)

        cursor.execute("INSERT INTO centro_areas_Departamentos_new SELECT * FROM centro_areas_Departamentos")
        cursor.execute("DROP TABLE centro_areas_Departamentos")
        cursor.execute("ALTER TABLE centro_areas_Departamentos_new RENAME TO centro_areas_departamentos")

    if table_exists(cursor,'centro_cursos_EquipoEducativo'):
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS centro_cursos_EquipoEducativo_new (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                cursos_id INTEGER NOT NULL REFERENCES centro_cursos(id),
                profesores_id INTEGER NOT NULL REFERENCES centro_profesores(id)
            );
            """)

        cursor.execute("INSERT INTO centro_cursos_EquipoEducativo_new SELECT * FROM centro_cursos_EquipoEducativo")
        cursor.execute("DROP TABLE centro_cursos_EquipoEducativo")
        cursor.execute("ALTER TABLE centro_cursos_EquipoEducativo_new RENAME TO centro_cursos_EquipoEducativo")

    # Confirmar los cambios
    conn.commit()


################################################## APP ABSENTISMO ####################################################

def migrate_absentismo_data(conn):
    cursor = conn.cursor()
    # Crear nuevas tablas si no existen
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS absentismo_tiposactuaciones (
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        TipoActuacion VARCHAR(60) NOT NULL
    );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS absentismo_protocoloabs (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            alumno_id INTEGER REFERENCES centro_alumnos (id),
            tutor_id INTEGER REFERENCES centro_profesores (id),
            fecha_apertura DATE NOT NULL,
            fecha_cierre DATE,
            abierto BOOL NOT NULL,
            curso_academico_id INTEGER REFERENCES centro_cursoacademico (id)
        );
        """)

    # Actualizar la tabla absentismo_actuaciones
    if table_exists(cursor,'absentismo_actuaciones'):
        # Añadir columnas si no existen
        if not column_exists(cursor,'absentismo_actuaciones', 'Telefono'):
            cursor.execute("ALTER TABLE absentismo_actuaciones ADD COLUMN Telefono TEXT")

        if not column_exists(cursor,'absentismo_actuaciones', 'Protocolo_id'):
            cursor.execute(
                "ALTER TABLE absentismo_actuaciones ADD COLUMN Protocolo_id INTEGER NOT NULL REFERENCES absentismo_protocoloabs (id)")

        if not column_exists(cursor,'absentismo_actuaciones', 'curso_academico_id'):
            cursor.execute(
                "ALTER TABLE absentismo_actuaciones ADD COLUMN curso_academico_id INTEGER REFERENCES centro_cursoacademico (id)")

        # Crear la nueva tabla con la estructura actualizada
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS absentismo_actuaciones_new (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            Fecha DATE NOT NULL,
            Notificada BOOL NOT NULL,
            Medio VARCHAR(1),
            Comentario TEXT NOT NULL,
            Protocolo_id INTEGER NOT NULL REFERENCES absentismo_protocoloabs (id),
            Tipo_id INTEGER REFERENCES absentismo_tiposactuaciones (id),
            Telefono TEXT,
            curso_academico_id INTEGER REFERENCES centro_cursoacademico (id)
        );
        """)

        # Insertar los datos relevantes de la tabla antigua a la nueva
        cursor.execute("""
        INSERT INTO absentismo_actuaciones_new (
            id, Fecha, Notificada, Medio, Comentario, Protocolo_id, Tipo_id, Telefono, curso_academico_id
        ) SELECT
            id, Fecha, Notificada, Medio, Comentario, Protocolo_id, Tipo_id, Telefono, curso_academico_id
        FROM absentismo_actuaciones
        """)

        cursor.execute("DROP TABLE absentismo_actuaciones")
        cursor.execute("ALTER TABLE absentismo_actuaciones_new RENAME TO absentismo_actuaciones")

    # Actualizar la tabla ProtocoloAbs
    if table_exists(cursor,'absentismo_protocoloabs'):
        # Crear la nueva tabla con la estructura actualizada
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS absentismo_protocoloabs_new (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            alumno_id INTEGER REFERENCES centro_alumnos (id),
            tutor_id INTEGER REFERENCES centro_profesores (id),
            fecha_apertura DATE NOT NULL,
            fecha_cierre DATE,
            abierto BOOL NOT NULL,
            curso_academico_id INTEGER REFERENCES centro_cursoacademico (id)
        );
        """)

        # Insertar los datos relevantes de la tabla antigua a la nueva
        cursor.execute("""
        INSERT INTO absentismo_protocoloabs_new (
            id, alumno_id, tutor_id, fecha_apertura, fecha_cierre, abierto, curso_academico_id
        ) SELECT
            id, alumno_id, tutor_id, fecha_apertura, fecha_cierre, abierto, curso_academico_id
        FROM absentismo_protocoloabs
        """)

        cursor.execute("DROP TABLE absentismo_protocoloabs")
        cursor.execute("ALTER TABLE absentismo_protocoloabs_new RENAME TO absentismo_protocoloabs")

    # Confirmar los cambios
    conn.commit()


################################################## APP CONVIVENCIA ####################################################

def migrate_convivencia_data(conn):
    cursor = conn.cursor()

    if table_exists(cursor,'convivencia_amonestaciones'):
        # Añadir columnas si no existen
        if not column_exists(cursor,'convivencia_amonestaciones', 'Enviado'):
            cursor.execute("ALTER TABLE convivencia_amonestaciones ADD COLUMN Enviado BOOL NOT NULL default 0")

        if not column_exists(cursor,'convivencia_amonestaciones', 'DerivadoConvivencia'):
            cursor.execute(
                "ALTER TABLE convivencia_amonestaciones ADD COLUMN DerivadoConvivencia BOOL NOT NULL default 0")

        if not column_exists(cursor,'convivencia_amonestaciones', 'ComunicadoFamilia'):
            cursor.execute(
                "ALTER TABLE convivencia_amonestaciones ADD COLUMN ComunicadoFamilia BOOL NOT NULL default 0")



        if not column_exists(cursor,'convivencia_amonestaciones', 'FamiliarComunicado'):
            cursor.execute("ALTER TABLE convivencia_amonestaciones ADD COLUMN FamiliarComunicado TEXT")

        if not column_exists(cursor,'convivencia_amonestaciones', 'FechaComunicado'):
            cursor.execute("ALTER TABLE convivencia_amonestaciones ADD COLUMN FechaComunicado DATE")

        if not column_exists(cursor,'convivencia_amonestaciones', 'HoraComunicado'):
            cursor.execute("ALTER TABLE convivencia_amonestaciones ADD COLUMN HoraComunicado TIME")

        if not column_exists(cursor,'convivencia_amonestaciones', 'Medio'):
            cursor.execute("ALTER TABLE convivencia_amonestaciones ADD COLUMN Medio VARCHAR(1)")

        if not column_exists(cursor,'convivencia_amonestaciones', 'ObservacionComunicado'):
            cursor.execute("ALTER TABLE convivencia_amonestaciones ADD COLUMN ObservacionComunicado TEXT")

        if not column_exists(cursor,'convivencia_amonestaciones', 'TelefonoComunicado'):
            cursor.execute("ALTER TABLE convivencia_amonestaciones ADD COLUMN TelefonoComunicado TEXT")

        if not column_exists(cursor,'convivencia_amonestaciones', 'curso_academico_id'):
            cursor.execute(
                "ALTER TABLE convivencia_amonestaciones ADD COLUMN curso_academico_id INTEGER REFERENCES centro_cursoacademico (id)")

        # Crear la nueva tabla con la estructura actualizada
        cursor.execute("""
            CREATE TABLE convivencia_amonestaciones_new (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            Fecha DATE NOT NULL,
            Hora VARCHAR (1) NOT NULL,
            Comentario TEXT NOT NULL,
            IdAlumno_id INTEGER REFERENCES centro_alumnos (id),
            Profesor_id INTEGER REFERENCES centro_profesores (id),
            Tipo_id INTEGER REFERENCES convivencia_tiposamonestaciones (id),
            Enviado BOOL NOT NULL,
            DerivadoConvivencia BOOL NOT NULL,
            ComunicadoFamilia BOOL NOT NULL,
            FamiliarComunicado TEXT,
            FechaComunicado DATE,
            HoraComunicado TIME,
            Medio VARCHAR (1),
            ObservacionComunicado TEXT,
            TelefonoComunicado TEXT,
            curso_academico_id INTEGER REFERENCES centro_cursoacademico (id)
        );
        """)

        # Insertar los datos relevantes de la tabla antigua a la nueva
        cursor.execute("""
        INSERT INTO convivencia_amonestaciones_new (
            id, Fecha, Hora, Comentario, IdAlumno_id, Profesor_id, Tipo_id, Enviado, DerivadoConvivencia, ComunicadoFamilia, FamiliarComunicado, FechaComunicado, HoraComunicado, Medio, ObservacionComunicado, TelefonoComunicado, curso_academico_id 
        ) SELECT
            id, Fecha, Hora, Comentario, IdAlumno_id, Profesor_id, Tipo_id, Enviado, DerivadoConvivencia, ComunicadoFamilia, FamiliarComunicado, FechaComunicado, HoraComunicado, Medio, ObservacionComunicado, TelefonoComunicado, curso_academico_id
        FROM convivencia_amonestaciones
        """)

        cursor.execute("DROP TABLE convivencia_amonestaciones")
        cursor.execute("ALTER TABLE convivencia_amonestaciones_new RENAME TO convivencia_amonestaciones")

    if table_exists(cursor,'convivencia_sanciones'):
        # Añadir columnas si no existen

        if not column_exists(cursor,'convivencia_sanciones', 'curso_academico_id'):
            cursor.execute(
                "ALTER TABLE convivencia_sanciones ADD COLUMN curso_academico_id INTEGER REFERENCES centro_cursoacademico (id)")

        # Crear la nueva tabla con la estructura actualizada
        cursor.execute("""
            CREATE TABLE convivencia_sanciones_new (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            Fecha DATE NOT NULL,
            Fecha_fin DATE NOT NULL,
            Sancion VARCHAR (100) NOT NULL,
            Comentario TEXT NOT NULL,
            NoExpulsion BOOL NOT NULL,
            IdAlumno_id INTEGER REFERENCES centro_alumnos (id),
            curso_academico_id INTEGER REFERENCES centro_cursoacademico (id)
        );
        """)

        # Insertar los datos relevantes de la tabla antigua a la nueva
        cursor.execute("""
        INSERT INTO convivencia_sanciones_new (
            id, Fecha, Fecha_fin, Sancion, Comentario, NoExpulsion, IdAlumno_id, curso_academico_id 
        ) SELECT
            id, Fecha, Fecha_fin, Sancion, Comentario, NoExpulsion, IdAlumno_id, curso_academico_id
        FROM convivencia_sanciones
        """)

        cursor.execute("DROP TABLE convivencia_sanciones")
        cursor.execute("ALTER TABLE convivencia_sanciones_new RENAME TO convivencia_sanciones")

    if table_exists(cursor,'convivencia_tiposamonestaciones'):
        # Añadir columnas si no existen

        if not column_exists(cursor,'convivencia_tiposamonestaciones', 'TipoFalta'):
            cursor.execute("ALTER TABLE convivencia_tiposamonestaciones ADD COLUMN TipoFalta VARCHAR (1) DEFAULT 'L'")

        # Crear la nueva tabla con la estructura actualizada
        cursor.execute("""
            CREATE TABLE convivencia_tiposamonestaciones_new (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            TipoAmonestacion VARCHAR (60) NOT NULL,
            TipoFalta VARCHAR (1)  NOT NULL DEFAULT 'L'
        );
        """)

        # Insertar los datos relevantes de la tabla antigua a la nueva
        cursor.execute("""
        INSERT INTO convivencia_tiposamonestaciones_new (
            id, TipoAmonestacion, TipoFalta 
        ) SELECT
            id, TipoAmonestacion, TipoFalta
        FROM convivencia_tiposamonestaciones
        """)

        cursor.execute("DROP TABLE convivencia_tiposamonestaciones")
        cursor.execute("ALTER TABLE convivencia_tiposamonestaciones_new RENAME TO convivencia_tiposamonestaciones")

    # Confirmar los cambios
    conn.commit()


######################## BORRAMOS TABLAS NO NECESARIAS #############################

def borrar_tablas_antiguas(conn):
    cursor = conn.cursor()
    if table_exists(cursor,'correo_correos'):
        cursor.execute("DROP TABLE correo_correos")

    if table_exists(cursor,'correo_correos_Destinatarios'):
        cursor.execute("DROP TABLE correo_correos_Destinatarios")

    if table_exists(cursor,'registro_registro'):
        cursor.execute("DROP TABLE registro_registro")

    if table_exists(cursor,'registro_clasedocumento'):
        cursor.execute("DROP TABLE registro_clasedocumento")

    if table_exists(cursor,'registro_procedencia'):
        cursor.execute("DROP TABLE registro_procedencia")

    if table_exists(cursor,'registro_remitente'):
        cursor.execute("DROP TABLE registro_remitente")

    # Confirmar los cambios
    conn.commit()


################################################## APP RESERVAS ####################################################
def migrate_reservas_data(conn):
    cursor = conn.cursor()
    # Crear nuevas tablas si no existen
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reservas_tiposreserva (
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        TipoReserva VARCHAR (60) NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reservas_reservables (
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        Nombre VARCHAR (255) NOT NULL,
        Descripcion VARCHAR (255) NOT NULL,
        TiposReserva_id BIGINT REFERENCES reservas_tiposreserva (id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reservas_reservas (
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        Fecha DATE NOT NULL,
        Hora VARCHAR (1) NOT NULL,
        Profesor_id INTEGER REFERENCES centro_profesores (id),
        Reservable_id BIGINT REFERENCES reservas_reservables (id),
        curso_academico_id INTEGER REFERENCES centro_cursoacademico (id)
    );
    """)

    # Confirmar los cambios
    conn.commit()


################################################## APP TDE ####################################################

def migrate_tde_data(conn):
    cursor = conn.cursor()
    # Crear nuevas tablas si no existen
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tde_prioridad (
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        nombre VARCHAR (100) NOT NULL,
        comentario VARCHAR (200) NOT NULL,
        prioridad INTEGER NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tde_elemento (
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        nombre VARCHAR (100) NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tde_incidenciastic (
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        comentario TEXT NOT NULL,
        resuelta BOOL NOT NULL,
        solucion TEXT,
        aula_id INTEGER NOT NULL REFERENCES centro_aulas (id),
        prioridad_id BIGINT REFERENCES tde_prioridad (id),
        profesor_id INTEGER NOT NULL REFERENCES centro_profesores (id),
        fecha DATE NOT NULL,
        curso_academico_id INTEGER REFERENCES centro_cursoacademico (id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tde_incidenciastic_elementos (
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        incidenciastic_id BIGINT NOT NULL REFERENCES tde_incidenciastic (id),
        elemento_id BIGINT NOT NULL REFERENCES tde_elemento (id)
    );
    """)

    # Confirmar los cambios
    conn.commit()


################################################## POBLAR TABLAS NUEVAS CON DATOS INICIALES ####################################################

def load_initial_absentismo_data(conn, cursor):
    csv_file_path = Path(__file__).resolve().parent / 'absentismo/datos_iniciales/inicio_absentismo_tiposactuaciones.csv'

    if not table_exists(cursor, 'absentismo_tiposactuaciones'):
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS absentismo_tiposactuaciones (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            TipoActuacion VARCHAR(60) NOT NULL
        );
        """)
        conn.commit()

    cursor.execute("""
            DELETE FROM absentismo_tiposactuaciones;
            """)
    conn.commit()

    with open(csv_file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            cursor.execute("""
            INSERT INTO absentismo_tiposactuaciones (id, TipoActuacion) VALUES (?, ?)
            ON CONFLICT(id) DO NOTHING;
            """, (row['id'], row['TipoActuacion']))
        conn.commit()



def load_initial_centro_areas_data(conn, cursor):
    csv_file_path = Path(__file__).resolve().parent / 'centro/datos_iniciales/inicio_centro_areas.csv'

    if not table_exists(cursor, 'centro_areas'):
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS centro_areas (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            Nombre VARCHAR(30) NOT NULL
        );
        """)
        conn.commit()

    cursor.execute("""
            DELETE FROM centro_areas;
            """)
    conn.commit()

    with open(csv_file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            cursor.execute("""
            INSERT INTO centro_areas (id, Nombre) VALUES (?, ?)
            ON CONFLICT(id) DO NOTHING;
            """, (row['id'], row['Nombre']))
        conn.commit()

def load_initial_centro_departamentos_data(conn, cursor):
    csv_file_path = Path(__file__).resolve().parent / 'centro/datos_iniciales/inicio_centro_departamentos.csv'

    if not table_exists(cursor, 'centro_departamentos'):
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS centro_departamentos (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            Abr VARCHAR(4) NOT NULL,
            Nombre VARCHAR(30) NOT NULL
        );
        """)
        conn.commit()

    cursor.execute("""
            DELETE FROM centro_departamentos;
            """)
    conn.commit()

    with open(csv_file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            cursor.execute("""
            INSERT INTO centro_departamentos (id, Abr, Nombre) VALUES (?, ?, ?)
            ON CONFLICT(id) DO NOTHING;
            """, (row['id'], row['Abr'], row['Nombre']))
        conn.commit()


def load_initial_centro_areas_departamentos_data(conn, cursor):
    csv_file_path = Path(__file__).resolve().parent / 'centro/datos_iniciales/inicio_centro_areas_departamentos.csv'

    if not table_exists(cursor, 'centro_areas_departamentos'):
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS centro_areas_departamentos (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            areas_id INTEGER NOT NULL REFERENCES centro_areas(id),
            departamentos_id INTEGER NOT NULL REFERENCES centro_departamentos(id)
        );
        """)
        conn.commit()

    cursor.execute("""
            DELETE FROM centro_areas_departamentos;
            """)
    conn.commit()

    with open(csv_file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            cursor.execute("""
            INSERT INTO centro_areas_departamentos (id, areas_id, departamentos_id) VALUES (?, ?, ?)
            ON CONFLICT(id) DO NOTHING;
            """, (row['id'], row['areas_id'], row['departamentos_id']))
        conn.commit()


def load_initial_centro_aulas_data(conn, cursor):
    csv_file_path = Path(__file__).resolve().parent / 'centro/datos_iniciales/inicio_centro_aulas.csv'

    if not table_exists(cursor, 'centro_aulas'):
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS centro_aulas (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            Aula VARCHAR(30) NOT NULL
        );
        """)
        conn.commit()

    cursor.execute("""
            DELETE FROM centro_aulas;
            """)
    conn.commit()

    with open(csv_file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            cursor.execute("""
            INSERT INTO centro_aulas (id, Aula) VALUES (?, ?)
            ON CONFLICT(id) DO NOTHING;
            """, (row['id'], row['Aula']))
        conn.commit()


def load_initial_centro_niveles_data(conn, cursor):
    csv_file_path = Path(__file__).resolve().parent / 'centro/datos_iniciales/inicio_centro_niveles.csv'

    if not table_exists(cursor, 'centro_niveles'):
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS centro_niveles (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            Nombre VARCHAR(255) NOT NULL,
            Abr VARCHAR(50) NOT NULL
        );
        """)
        conn.commit()

    cursor.execute("""
            DELETE FROM centro_niveles;
            """)
    conn.commit()

    with open(csv_file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            cursor.execute("""
            INSERT INTO centro_niveles (id, Nombre, Abr) VALUES (?, ?, ?)
            ON CONFLICT(id) DO NOTHING;
            """, (row['id'], row['Nombre'], row['Abr']))
        conn.commit()

def load_initial_centro_cursoacademico_data(conn, cursor):
    csv_file_path = Path(__file__).resolve().parent / 'centro/datos_iniciales/inicio_centro_cursoacademico.csv'

    if not table_exists(cursor, 'centro_cursoacademico'):
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS centro_cursoacademico (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            nombre VARCHAR(100) NOT NULL,
            año_inicio INTEGER,
            año_fin INTEGER
        );
        """)
        conn.commit()

    cursor.execute("""
            DELETE FROM centro_cursoacademico;
            """)
    conn.commit()

    with open(csv_file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            cursor.execute("""
            INSERT INTO centro_cursoacademico (id, nombre, año_inicio, año_fin) VALUES (?, ?, ?, ?)
            ON CONFLICT(id) DO NOTHING;
            """, (row['id'], row['nombre'], row['año_inicio'], row['año_fin']))
        conn.commit()


def load_initial_centro_data(conn, cursor):

    load_initial_centro_areas_data(conn,cursor)
    load_initial_centro_departamentos_data(conn,cursor)
    load_initial_centro_areas_departamentos_data(conn, cursor)
    load_initial_centro_aulas_data(conn, cursor)
    load_initial_centro_niveles_data(conn,cursor)
    load_initial_centro_cursoacademico_data(conn,cursor)


def load_initial_convivencia_tiposamonestaciones_data(conn, cursor):
    csv_file_path = Path(__file__).resolve().parent / 'convivencia/datos_iniciales/inicio_convivencia_tiposamonestaciones.csv'

    if not table_exists(cursor, 'convivencia_tiposamonestaciones'):
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS convivencia_tiposamonestaciones (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            TipoAmonestacion VARCHAR(60) NOT NULL,
            TipoFalta VARCHAR(1) NOT NULL DEFAULT 'L'
        );
        """)
        conn.commit()

    cursor.execute("""
            DELETE FROM convivencia_tiposamonestaciones;
            """)
    conn.commit()

    with open(csv_file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            cursor.execute("""
            INSERT INTO convivencia_tiposamonestaciones (id, TipoAmonestacion, TipoFalta) VALUES (?, ?, ?)
            ON CONFLICT(id) DO NOTHING;
            """, (row['id'], row['TipoAmonestacion'], row['TipoFalta']))
        conn.commit()

def load_initial_reservas_tiposreserva_data(conn, cursor):
    csv_file_path = Path(__file__).resolve().parent / 'reservas/datos_iniciales/inicio_reservas_tiposreserva.csv'

    if not table_exists(cursor, 'reservas_tiposreserva'):
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS reservas_tiposreserva (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            TipoReserva VARCHAR(60) NOT NULL
        );
        """)
        conn.commit()

    cursor.execute("""
            DELETE FROM reservas_tiposreserva;
            """)
    conn.commit()

    with open(csv_file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            cursor.execute("""
            INSERT INTO reservas_tiposreserva (id, TipoReserva) VALUES (?, ?)
            ON CONFLICT(id) DO NOTHING;
            """, (row['id'], row['TipoReserva']))
        conn.commit()


def load_initial_reservas_reservables_data(conn, cursor):
    csv_file_path = Path(__file__).resolve().parent / 'reservas/datos_iniciales/inicio_reservas_reservables.csv'

    if not table_exists(cursor, 'reservas_reservables'):
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS reservas_reservables (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            Nombre VARCHAR(255) NOT NULL,
            Descripcion VARCHAR(255) NOT NULL,
            TiposReserva_id BIGINT REFERENCES reservas_tiposreserva(id)
        );
        """)
        conn.commit()

    cursor.execute("""
            DELETE FROM reservas_reservables;
            """)
    conn.commit()

    with open(csv_file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            cursor.execute("""
            INSERT INTO reservas_reservables (id, Nombre, Descripcion, TiposReserva_id) VALUES (?, ?, ?, ?)
            ON CONFLICT(id) DO NOTHING;
            """, (row['id'], row['Nombre'], row['Descripcion'], row['TiposReserva_id']))
        conn.commit()

def load_initial_reservas_data(conn, cursor):
    load_initial_reservas_tiposreserva_data(conn, cursor)
    load_initial_reservas_reservables_data(conn, cursor)


def load_initial_tde_prioridad_data(conn, cursor):
    csv_file_path = Path(__file__).resolve().parent / 'tde/datos_iniciales/inicio_tde_prioridad.csv'

    if not table_exists(cursor, 'tde_prioridad'):
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS tde_prioridad (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            nombre VARCHAR(100) NOT NULL,
            comentario VARCHAR(200) NOT NULL,
            prioridad INTEGER NOT NULL
        );
        """)
        conn.commit()

    cursor.execute("""
            DELETE FROM tde_prioridad;
            """)
    conn.commit()

    with open(csv_file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            cursor.execute("""
            INSERT INTO tde_prioridad (id, nombre, comentario, prioridad) VALUES (?, ?, ?, ?)
            ON CONFLICT(id) DO NOTHING;
            """, (row['id'], row['nombre'], row['comentario'], row['prioridad']))
        conn.commit()


def load_initial_tde_elemento_data(conn, cursor):
    csv_file_path = Path(__file__).resolve().parent / 'tde/datos_iniciales/inicio_tde_elemento.csv'

    if not table_exists(cursor, 'tde_elemento'):
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS tde_elemento (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            nombre VARCHAR(100) NOT NULL
        );
        """)
        conn.commit()

    cursor.execute("""
            DELETE FROM tde_elemento;
            """)
    conn.commit()

    with open(csv_file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            cursor.execute("""
            INSERT INTO tde_elemento (id, nombre) VALUES (?, ?)
            ON CONFLICT(id) DO NOTHING;
            """, (row['id'], row['nombre']))
        conn.commit()


def load_initial_tde_data(conn, cursor):
    load_initial_tde_prioridad_data(conn, cursor)
    load_initial_tde_elemento_data(conn, cursor)


def remove_old_migrations():
    migrations_dirs = [
        Path(__file__).resolve().parent / 'absentismo' / 'migrations',
        Path(__file__).resolve().parent / 'centro' / 'migrations',
        Path(__file__).resolve().parent / 'convivencia' / 'migrations',
        Path(__file__).resolve().parent / 'reservas' / 'migrations',
        Path(__file__).resolve().parent / 'tde' / 'migrations',
    ]

    for migrations_dir in migrations_dirs:
        # Eliminar archivos de migraciones (excepto __init__.py)
        for file in migrations_dir.glob('*.py'):
            if file.name != '__init__.py':
                file.unlink()
        for file in migrations_dir.glob('*.pyc'):
            file.unlink()

def clear_migration_records(conn, cursor):
    cursor.execute("DELETE FROM django_migrations")
    conn.commit()

def update_last_login_field(conn, cursor):
    cursor.execute("UPDATE auth_user SET last_login = CURRENT_TIMESTAMP WHERE last_login IS NULL")
    conn.commit()




def main():
    # Conectar a la base de datos SQLite
    conn = sqlite3.connect('basededatos/db.sqlite3')

    try:
        cursor = conn.cursor()





        migrate_centro_data(conn)
        migrate_absentismo_data(conn)
        migrate_convivencia_data(conn)
        migrate_reservas_data(conn)
        migrate_tde_data(conn)
        borrar_tablas_antiguas(conn)

        load_initial_absentismo_data(conn, cursor)
        load_initial_centro_data(conn, cursor)
        load_initial_convivencia_tiposamonestaciones_data(conn, cursor)

        load_initial_reservas_data(conn, cursor)
        load_initial_tde_data(conn,cursor)




        # Eliminar archivos de migraciones anteriores
        remove_old_migrations()

        # Eliminar registros de migraciones anteriores de la base de datos
        clear_migration_records(conn, cursor)

        # Actualizar el campo last_login para evitar el error NOT NULL constraint failed
        update_last_login_field(conn, cursor)

        # Crear nuevas migraciones iniciales
        call_command('makemigrations')

        # Aplicar migraciones de forma "fake"
        call_command('migrate', fake=True)

        # Llamar al comando personalizado import_profesores
        call_command('import_profesores', 'centro/datos_iniciales/RelPerCen_24_25.csv')

        # Llamar al comando personalizado import_cursos
        call_command('import_cursos', 'centro/datos_iniciales/RegUnidades_24_25.csv', 'centro/datos_iniciales/EquipoEducativo_24_25.csv')




        # Llamar al comando personalizado import_alumnos
        call_command('import_alumnos', 'centro/datos_iniciales/RegAlum_24_25.csv', False)
        


        # Llamar al comando personalizado asignar_curso_academico para el curso 20/21
        call_command('asignar_cursoacademico', 6)

        
        call_command('asignar_superusuario', 'jefe1')

        call_command('asignar_grupo', 'jefe1', 'jefatura de estudios')


        call_command('crear_grupo', 'tde')
        call_command('crear_grupo', 'orientacion')




    finally:
        conn.close()


if __name__ == "__main__":
    main()
