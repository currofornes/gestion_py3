"""
╔════════════════════════════════════════════════════════════════════════════╗
║                          GESTION@ - GESTIÓN DE CENTROS EDUCATIVOS          ║
║                                                                            ║
║ Copyright © 2023-2026 Francisco Fornés Rumbao, Raúl Reina Molina           ║
║                          Proyecto base por José Domingo Muñoz Rodríguez    ║
║                                                                            ║
║ Todos los derechos reservados. Prohibida la reproducción, distribución,    ║
║ modificación o comercialización sin consentimiento expreso de los autores. ║
║                                                                            ║
║ Este archivo es parte de la aplicación Gestion@.                           ║
║                                                                            ║
║ Para consultas sobre licencias o permisos:                                 ║
║ Email: fforrum559@g.educaand.es                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
"""


import time
import calendar
from datetime import date, timedelta
import os
import re
import subprocess
import csv
from io import TextIOWrapper, BytesIO

from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import When, Case
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.contrib import messages
from django.views.decorators.http import require_POST

from absentismo.forms import ActuacionProtocoloForm, CargaFaltasCSVForm,\
    ResumenFaltasForm, InformeFMForm, InformeSSCForm
from absentismo.models import ProtocoloAbs, FaltasProtocolo, InformeFM, \
    InformeSSC, AdjuntoInformeFM, AdjuntoInformeSSC, Actuaciones
from centro.models import Cursos, Alumnos, Profesores, CursoAcademico, CalendariosLectivos
from centro.views import group_check_je, group_check_prof_and_tutor_or_je, \
    group_check_je_or_orientacion, group_check_prof_and_tutor_or_je_or_orientacion
from centro.utils import get_encoding, get_current_academic_year
from absentismo.utils import campos_informe_FM, campos_informe_SSC, \
    cumplimentar_pdf_form, _leyenda, _clasificar_dia, _gradiente, _datos_dia, \
    TRAMOS_DIA

from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration


# Create your views here.
PLANTILLA_FM  = os.path.join(settings.BASE_DIR, 'static', 'pdfs', 'absentismo', 'Ax I editable.pdf')
PLANTILLA_SSC = os.path.join(settings.BASE_DIR, 'static', 'pdfs', 'absentismo', 'ProtAbs - Modelo.pdf')

ASIGNACION_CHOICES = [
    ('1P_2M',   'Tutor 1 → Padre / Tutor 2 → Madre'),
    ('1M_2P',   'Tutor 1 → Madre / Tutor 2 → Padre'),
    ('SOLO_1P', 'Solo Tutor 1, figura paterna'),
    ('SOLO_1M', 'Solo Tutor 1, figura materna'),
    ('SOLO_2P', 'Solo Tutor 2, figura paterna'),
    ('SOLO_2M', 'Solo Tutor 2, figura materna'),
]

HERMANOS_CHOICES = [
    ('SI', 'Sí'),
    ('NO', 'No'),
    ('NS', 'No se conoce'),
]

PSICO_CHOICES = [
    ('psi_des',    'DES – Desfavorecido/a Socialmente'),
    ('psi_dia',    'DIA – Dificultades de Aprendizaje'),
    ('psi_dis',    'DIS – Diversidad Funcional'),
    ('psi_tdah',   'TDAH – Déficit de Atención e Hiperactividad'),
    ('psi_aaccii', 'AACCII – Altas Capacidades Intelectuales'),
]

SERVICIOS_CHOICES = [
    ('serv_aula_matinal',     'Aula Matinal'),
    ('serv_atal',             'ATAL – Adaptación Lingüística'),
    ('serv_comedor',          'Comedor Escolar'),
    ('serv_acompanamiento',   'Programa de Acompañamiento'),
    ('serv_parcep',           'PARCEP / PARCES – Refuerzo'),
    ('serv_deporte',          'Deporte en la Escuela'),
    ('serv_actividades_ayto', 'Actividades Ayuntamiento / ESFL'),
    ('serv_pale',             'PALE – Apoyo Lengua Extranjera'),
    ('serv_pali',             'PALI – Apoyo Alumnado Inmigrante'),
    ('serv_otras_act',        'Otras Actividades Complementarias / Extraescolares'),
]

# (val, etiqueta, descripcion_dirección)
DIRIGIDO_CHOICES = [
    ('SS_CC',        'Servicios Sociales Comunitarios',   'Parque de la Alquería, S/N · Dos Hermanas'),
    ('MESA_TECNICA', 'Mesa Técnica de Absentismo',        'Edif. Huerta Palacios, 2ª planta'),
    ('FISCALIA',     'Comisión Municipal → Fiscalía',     'Edif. Huerta Palacios, 2ª planta'),
]

DIFICULTADES_CHOICES = [
    ('dif_iguales',     'Relaciones disfuncionales con el grupo de iguales'),
    ('dif_profesorado', 'Relaciones disfuncionales con el profesorado'),
    ('dif_disruptivo',  'Comportamiento disruptivo en el aula'),
    ('dif_salud_mental','Diagnosticado/a por entidades sanitarias (salud mental)'),
]

MEDIDAS_CHOICES = [
    ('med_compromisos',      'Compromisos adoptados (educativo, de convivencia, etc.)'),
    ('med_aula_convivencia', 'Aula de convivencia'),
    ('med_talleres',         'Talleres o escuelas de padres y madres'),
    ('med_mediacion',        'Mediación de conflictos'),
]

FAMILIAR_CHOICES = [
    ('fam_relaciones', 'Relaciones disfuncionales con la madre/padre/representante legal'),
    ('fam_economicas', 'Dificultades económicas en el hogar'),
    ('fam_educativas', 'Dificultades educativas del padre/madre/tutor legal'),
    ('fam_riesgo',     'Posibles indicadores de riesgo en el contexto socio-familiar'),
]

INDIVIDUALES_CHOICES = [
    ('ind_refuerzo', 'Refuerzo educativo'),
    ('ind_tutorial', 'Acción tutorial (trabajo cooperativo, responsabilidades, etc.)'),
    ('ind_eoe',      'Atención por parte del E.O.E./D.O.'),
]


@login_required(login_url='/')
@user_passes_test(group_check_prof_and_tutor_or_je_or_orientacion, login_url='/')
def verprotocolo(request, alum_id):
    alum = Alumnos.objects.get(pk=alum_id)
    protocolo = alum.protocolos.filter(abierto=True).last()
    actuaciones = Actuaciones.objects.filter(Protocolo=protocolo).order_by("Fecha").all()

    protocolos_cerrados = alum.protocolos.filter(abierto=False)
    protocolos_cerrados = sorted(protocolos_cerrados, key=lambda x: x.fecha_cierre, reverse=False)

    context = {'alum': alum, 'protocolo': protocolo, 'actuaciones': actuaciones, 'protocolos_cerrados': protocolos_cerrados}
    return render(request, 'protocolos.html', context)


# @login_required(login_url='/')
# @user_passes_test(group_check_prof_and_tutor, login_url='/')
# def misalumnos(request):
#     if not hasattr(request.user, 'profesor'):
#         return render(request, 'error.html', {'message': 'No tiene un perfil de profesor asociado.'})
#
#     profesor = request.user.profesor
#
#     cursos = Cursos.objects.filter(Tutor_id=profesor.id)
#     try:
#         primer_id = cursos.order_by('Curso').first().id
#     except:
#         primer_id = 0
#
#     request.session['Unidad'] = primer_id
#
#     lista_alumnos = Alumnos.objects.filter(Unidad__id=primer_id)
#     lista_alumnos = sorted(lista_alumnos, key=lambda d: d.Nombre)
#
#
#     # Obtener los IDs de los alumnos
#     ids = [elem.id for elem in lista_alumnos]
#
#     # Obtener edades y protocolos
#     edades = obtener_edades_alumnos(ids)
#     protocolos = obtener_protocolos(ids)
#
#     # Combinar alumnos con edades y protocolos
#     lista_combinada = list(zip(lista_alumnos, edades, protocolos))
#
#
#     try:
#         context = {'alumnos': lista_combinada, 'curso': cursos.get(id=primer_id), 'profesor': profesor}
#     except:
#         context = {'alumnos': lista_combinada, 'curso': None, 'profesor': profesor}
#     return render(request, 'misalumnosabs.html', context)


def calcular_edad(fecha_nacimiento, fecha_referencia):
    anos = fecha_referencia.year - fecha_nacimiento.year
    if (fecha_referencia.month, fecha_referencia.day) < (fecha_nacimiento.month, fecha_nacimiento.day):
        anos -= 1
    return anos


def obtener_edades_alumnos(ids_alumnos):
    fecha_referencia = date.today()

    # Obtener la lista de alumnos usando los IDs proporcionados
    #alumnos = get_list_or_404(Alumnos, id__in=ids_alumnos)
    # Mantener el orden de los IDs proporcionados
    alumnos = Alumnos.objects.filter(id__in=ids_alumnos).order_by(
        Case(*[When(id=pk, then=pos) for pos, pk in enumerate(ids_alumnos)])
    )

    # Calcular la edad de cada alumno a la fecha de referencia
    edades = [calcular_edad(alumno.Fecha_nacimiento, fecha_referencia) for alumno in alumnos]


    return edades


def obtener_protocolos(ids_alumnos):
    # Obtener alumnos por sus IDs
    #alumnos = get_list_or_404(Alumnos, id__in=ids_alumnos)
    alumnos = Alumnos.objects.filter(id__in=ids_alumnos).order_by(
        Case(*[When(id=pk, then=pos) for pos, pk in enumerate(ids_alumnos)])
    )

    # Crear el listado de resultados
    resultados = []
    for alumno in alumnos:
        protocolo = ProtocoloAbs.objects.filter(alumno=alumno).last()
        if protocolo:
            actuacion = protocolo.actuaciones.last()
            resultados.append({
                'alumno_id': alumno.id,
                'protocolo_id': protocolo.id,
                'tiene_protocolo': True,
                'protocolo_abierto': protocolo.abierto,
                'fecha_apertura': protocolo.fecha_apertura,
                'fecha_cierre': protocolo.fecha_cierre if protocolo.fecha_cierre else None,
                'ultima_actuacion': actuacion.Tipo if actuacion else None,
                'fecha_ultima': actuacion.Fecha if actuacion else None
            })
        else:
            resultados.append({
                'alumno_id': alumno.id,
                'tiene_protocolo': False,
                'protocolo_abierto': None,
                'fecha_apertura': None,
                'fecha_cierre': None,
                'ultima_actuacion': None,
                'fecha_ultima': None
            })


    return resultados


@login_required(login_url='/')
@user_passes_test(group_check_prof_and_tutor_or_je, login_url='/')
def nuevaactuacion(request, proto_id):
    protocolo = ProtocoloAbs.objects.get(pk=proto_id)
    alum_id = protocolo.alumno.id

    if request.method == 'POST':
        form = ActuacionProtocoloForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/absentismo/' + str(alum_id) + '/protocolo')
        else:
            print(form.errors)
    else:
        form = ActuacionProtocoloForm(
            initial={'Fecha': time.strftime("%d/%m/%Y"), 'Protocolo': protocolo}
        )

    titulo = "Actuaciones Absentismo"

    context = {'form': form, 'titulo': titulo, 'protocolo': protocolo}
    return render(request, 'actuacionprotocolo.html', context)


@csrf_exempt
def cerrar_protocolo(request):
    if request.method == 'POST':
        protocolo_id = request.POST.get('id')
        if not protocolo_id:
            return JsonResponse(
                {'success': False, 'error': 'Falta el ID del protocolo'})

        try:
            protocolo = ProtocoloAbs.objects.get(id=int(protocolo_id))
            protocolo.abierto = False
            protocolo.fecha_cierre = date.today()  # Django se encarga del formato
            protocolo.save()
            return JsonResponse({'success': True})
        except ProtocoloAbs.DoesNotExist:
            return JsonResponse(
                {'success': False, 'error': 'Protocolo no encontrado'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Método no permitido'})


@login_required(login_url='/')
@user_passes_test(group_check_prof_and_tutor_or_je, login_url='/')
def abrirprotocolo(request, alum_id):
    alumno = get_object_or_404(Alumnos, id=alum_id)  # Obtiene el alumno o lanza 404 si no existe
    tutor = Profesores.objects.get(user=request.user)

    # Verificar si ya existe un ProtocoloAbs abierto para ese alumno
    protocolo_existente = ProtocoloAbs.objects.filter(alumno=alumno, tutor=tutor, abierto=True).first()

    if protocolo_existente:
        # Si ya existe un protocolo abierto, lo utilizamos
        nuevo_protocolo = protocolo_existente
    else:
        nuevo_protocolo = ProtocoloAbs.objects.create(
            alumno=alumno,
            tutor=tutor,
            fecha_apertura=date.today().strftime('%Y-%m-%d'),  # Asigna la fecha actual
            fecha_cierre=None,
            abierto=True
        )

    form = ActuacionProtocoloForm(
        initial={'Fecha': time.strftime("%d/%m/%Y"), 'Protocolo': nuevo_protocolo}
    )

    titulo = "Actuaciones Absentismo"

    context = {'form': form, 'titulo': titulo, 'protocolo': nuevo_protocolo}
    return render(request, 'actuacionprotocolo.html', context)


@login_required(login_url='/')
@user_passes_test(group_check_prof_and_tutor_or_je_or_orientacion, login_url='/')
def verprotocolocerrado(request, proto_id):
    protocolo = ProtocoloAbs.objects.get(pk=proto_id)
    alumno = protocolo.alumno
    tutor = protocolo.tutor

    context = {'alumno': alumno, 'protocolo': protocolo, 'tutor': tutor}
    return render(request, 'protocolocerrado.html', context)


@login_required(login_url='/')
@user_passes_test(group_check_je_or_orientacion, login_url='/')
def alumnos(request):
    # Obtener todos los protocolos abiertos
    protocolos_abiertos = ProtocoloAbs.objects.filter(abierto=True)

    if not protocolos_abiertos.exists():
        alumnos = []
        context = {'alumnos': alumnos}
    else:
        # Crear una lista de tuplas con (alumno, tutor, edad, protocolo)
        lista_alumnos = []
        for protocolo in protocolos_abiertos:
            alumno = protocolo.alumno
            tutor = protocolo.tutor
            edad = obtener_edades_alumnos([alumno.id])[0]  # Suponiendo que obtener_edades_alumnos devuelve una lista
            protocolo_info = obtener_protocolos([alumno.id])[0]  # Suponiendo que obtener_protocolos devuelve una lista

            # Añadir la tupla a la lista
            lista_alumnos.append((alumno, tutor, edad, protocolo_info))

        # Pasar la lista de tuplas al contexto
        context = {'alumnos': lista_alumnos, 'menu_absentismo': True}

    return render(request, 'alumnosabs.html', context)


@login_required(login_url='/')
@user_passes_test(group_check_je, login_url='/')
def todoalumnado(request):
    if not hasattr(request.user, 'profesor'):
        return render(request, 'error.html', {'message': 'No tiene un perfil de profesor asociado.'})

    profesor = request.user.profesor
    cursos = Cursos.objects.filter(Nivel__isnull=False).order_by('Orden').all()

    # Obtener el curso seleccionado desde el formulario (POST)
    curso_id = request.POST.get('curso', None)

    if curso_id:
        lista_alumnos = Alumnos.objects.filter(Unidad_id=curso_id)
        lista_alumnos = sorted(lista_alumnos, key=lambda d: d.Nombre)

        # Obtener los IDs de los alumnos
        ids = [elem.id for elem in lista_alumnos]

        # Obtener edades y protocolos
        edades = obtener_edades_alumnos(ids)
        protocolos = obtener_protocolos(ids)

        # Combinar alumnos con edades y protocolos
        lista_combinada = list(zip(lista_alumnos, edades, protocolos))

        curso_seleccionado = Cursos.objects.get(id=curso_id)
    else:
        # Si no se ha seleccionado ningún curso, inicializamos una lista vacía
        lista_combinada = []
        curso_seleccionado = None

    context = {
        'cursos': cursos,
        'alumnos': lista_combinada,
        'curso_seleccionado': curso_seleccionado,
        'profesor': profesor
    }

    return render(request, 'todoalumnado.html', context)

# Funciones auxiliares para parsear el informe de faltas de Séneca
def extraer_faltas(line):
    parts = line.strip().split(',')
    # Procesar cada parte
    date = parts[0]
    numbers = []

    for part in parts[1:]:
        # Separar por espacios y convertir a enteros
        nums = list(map(int, part.split()))
        numbers.extend(nums)  # Agregar los números a la lista

    # Combinar fecha y números en una sola lista
    return [date] + numbers


def procesar_pdf(proto_id):
    # Construir el comando como una lista
    jar_path = os.path.join(settings.BASE_DIR, 'tabula-1.0.5-jar-with-dependencies.jar')

    file_path = os.path.join('informes_faltas_seneca', f'informe_{proto_id}.pdf')
    full_path = os.path.join(settings.MEDIA_ROOT, file_path)

    temp_file_path = os.path.join('informes_faltas_seneca', f'informe_{proto_id}.txt')
    temp_full_path = os.path.join(settings.MEDIA_ROOT, temp_file_path)

    comando = ['java', '-jar', jar_path, '-o', temp_full_path, '-p', 'all', full_path]

    # Ejecutar el comando usando subprocess.run
    resultado = subprocess.run(comando, capture_output=True, text=True)

    # Verificar si hubo errores al ejecutar Tabula
    if resultado.returncode != 0:
        print(comando)
        print(f"Error al ejecutar Tabula: {resultado.stderr}")
        return

    # Leer archivo de texto generado

    with open(temp_full_path, 'r', encoding='utf-8') as archivo:
        lineas = archivo.readlines()

    alumno = ""
    unidad = ""
    faltas = []
    # Expresión regular para una fecha en formato DD/MM/AAAA
    patron_fecha = r'^\d{2}/\d{2}/\d{4}'

    for linea in lineas:
        # Identificar las líneas de faltas que empiezan con una fecha
        if re.match(patron_fecha, linea):
            # Partir la línea de faltas en columnas
            datos_faltas = extraer_faltas(linea)

            # Verificar que la línea tiene suficientes columnas
            if len(datos_faltas) >= 10:
                faltas.append(datos_faltas)

        if linea.startswith("UNIDAD:"):
            patron = r'UNIDAD:,\s*([^,]+)'

            unidad = linea
            coincidencia = re.search(patron, linea)
            if coincidencia:
                unidad = coincidencia.group(1)
                patron = r'(\d)o'
                unidad = re.sub(patron, r'\1º', unidad)

        if linea.startswith("ALUMNO:"):
            patron = r'ALUMNO:,"([^"]+)"'
            coincidencia = re.search(patron, linea)
            if coincidencia:
                alumno = coincidencia.group(1)


    return faltas
# Fin de funciones auxiliares

@login_required(login_url='/')
@user_passes_test(group_check_prof_and_tutor_or_je_or_orientacion, login_url='/')
def cargarfaltas(request, proto_id):
    MESES = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']

    protocolo = ProtocoloAbs.objects.get(pk=proto_id)
    alum_id = protocolo.alumno.id

    if request.method == 'POST':
        form = CargaFaltasCSVForm(request.POST, request.FILES)
        if form.is_valid():
            # En tu CBV accedías a request.FILES['archivo_csv']
            csv_file = request.FILES.get('archivo_csv')
            curso_academico_id = request.POST.get('curso_academico')
            curso_academico = CursoAcademico.objects.get(pk=curso_academico_id)
            if not csv_file:
                messages.error(request,
                               "No se ha proporcionado ningún archivo.")
                return redirect(request.path)

            try:
                encoding = get_encoding(csv_file)
                csv_file.seek(0)
                csvfile = TextIOWrapper(csv_file, encoding=encoding)
                reader = csv.DictReader(csvfile)

                # Formato esperado: Apellidos, Nombre (coincidiendo con el CSV de Séneca)
                nombre_completo_alumno = protocolo.alumno.Nombre.upper()
                found = False
                for row in reader:
                    # Comprobar si la fila pertenece al alumno del protocolo
                    if row['Alumno/a'].upper() == nombre_completo_alumno:
                        found = True

                        # Recorrer columnas de fechas (desde la 1 en adelante)
                        for campo, valor in row.items():
                            if campo != 'Alumno/a':
                                fecha_str = campo

                                if not valor or not fecha_str:
                                    continue

                                try:
                                    s = fecha_str.split(' ')
                                    dia = int(s[0])
                                    mes = MESES.index(s[1]) + 1
                                    año = curso_academico.año_inicio if 9 <= mes <= 12 else curso_academico.año_fin
                                    fecha_obj = date(año, mes, dia)
                                    # Intentar parsear la fecha del encabezado

                                    # Inicializar contadores
                                    dcj, dcnj, tj, tnj = 0, 0, 0, 0

                                    if valor == 'CI':
                                        dcnj = 1
                                    elif valor == 'CJ':
                                        dcj = 1
                                    else:
                                        # Parsear formato XJ-YI-ZR (Tramos)
                                        match = re.match(r'(\d+)J-(\d+)I-(\d+)R',
                                                         valor)
                                        if match:
                                            tj = int(match.group(1))
                                            tnj = int(match.group(2))

                                    # Guardar o actualizar registro de faltas
                                    FaltasProtocolo.objects.update_or_create(
                                        Protocolo=protocolo,
                                        Fecha=fecha_obj,
                                        defaults={
                                            'DiaCompletoJustificada': dcj,
                                            'DiaCompletoNoJustificada': dcnj,
                                            'TramosJustificados': tj,
                                            'TramosNoJustificados': tnj,
                                        }
                                    )
                                except (ValueError, IndexError):
                                    continue  # Saltar si no es una fecha válida o falta la columna

                if found:
                    print(f"Faltas de {protocolo.alumno} actualizadas correctamente.")
                else:
                    print("No se encontró al alumno en el archivo CSV.")

                return redirect(f'/absentismo/{protocolo.alumno.id}/protocolo')

            except Exception as e:
                print(f"Error procesando CSV: {e}")  # Log the error for debugging
    else:
        # Petición GET: Inicializar formulario vacío
        form = CargaFaltasCSVForm()

    context = {
        'form': form,
        'protocolo': protocolo,
        'titulo': 'Cargar faltas desde Séneca (CSV)'
    }
    return render(request, 'carga_faltas_csv.html', context)

    # if request.method == 'POST':
    #     form = CargaInformeFaltasSeneca(request.POST, request.FILES)
    #     print(f'El formulario {"" if form.is_valid() else "no"} es válido')
    #     if form.is_valid():
    #         informe_pdf = form.cleaned_data['InformePDF']
    #
    #         # Define la ruta completa donde deseas guardar el archivo
    #         file_path = os.path.join('informes_faltas_seneca', f'informe_{proto_id}.pdf')
    #         full_path = os.path.join(settings.MEDIA_ROOT, file_path)
    #
    #         # Guarda el archivo en la ubicación especificada
    #         with default_storage.open(full_path, 'wb+') as destination:
    #             for chunk in informe_pdf.chunks():
    #                 destination.write(chunk)
    #
    #
    #         lista_faltas = procesar_pdf(proto_id)
    #
    #         for falta in lista_faltas:
    #             fecha = datetime.strptime(falta[0], "%d/%m/%Y").date()
    #
    #             dia_completo_justificada_prof = falta[1]
    #             dia_completo_justificada_tutor = falta[2]
    #             dia_completo_no_justificada = falta[3]
    #             tramos_justificados_prof = falta[4]
    #             tramos_justificados_tutor = falta[5]
    #             tramos_no_justificada = falta[6]
    #             tramos_retraso = falta[7]
    #             notificacion_dia_completo = falta[8]
    #             notificacion_tramos = falta[9]
    #
    #             # Usamos una transacción para garantizar atomicidad
    #             with transaction.atomic():
    #                 # Busca o crea el registro para la fecha y protocolo especificados
    #                 obj, created = FaltasProtocolo.objects.get_or_create(
    #                     Protocolo=protocolo,
    #                     Fecha=fecha,
    #                     defaults={
    #                         'DiaCompletoJustificada': dia_completo_justificada_prof + dia_completo_justificada_tutor,
    #                         'DiaCompletoNoJustificada': dia_completo_no_justificada,
    #                         'TramosJustificados': tramos_justificados_prof + tramos_justificados_tutor,
    #                         'TramosNoJustificados': tramos_no_justificada,
    #                         'NotificacionDiaCompleto': notificacion_dia_completo,
    #                         'NotificacionTramos': notificacion_tramos,
    #                     }
    #                 )
    #
    #                 # Si el registro ya existía, actualizamos los campos necesarios
    #                 if not created:
    #                     obj.DiaCompletoJustificada = dia_completo_justificada_prof + dia_completo_justificada_tutor
    #                     obj.DiaCompletoNoJustificada = dia_completo_no_justificada
    #                     obj.TramosJustificados = tramos_justificados_prof + tramos_justificados_tutor
    #                     obj.TramosNoJustificados = tramos_no_justificada
    #                     obj.NotificacionDiaCompleto = notificacion_dia_completo
    #                     obj.NotificacionTramos = notificacion_tramos
    #                     obj.save()
    #
    #         return redirect(f'/absentismo/{alum_id}/protocolo')
    #     else:
    #         print(form.errors)
    # else:
    #     form = CargaInformeFaltasSeneca(
    #         initial={'Protocolo': protocolo}
    #     )
    #
    # titulo = "Carga de faltas desde informe de Séneca"
    #
    # context = {'form': form, 'titulo': titulo, 'protocolo': protocolo}
    # return render(request, 'cargainformefaltasseneca.html', context)


@login_required(login_url='/')
@user_passes_test(group_check_je, login_url='/')
def resumen_faltas_periodos(request, proto_id):
    protocolo = get_object_or_404(ProtocoloAbs, pk=proto_id)
    resumen = []
    curso_id = request.POST.get('curso_academico') or (
        protocolo.curso_academico.id if protocolo.curso_academico else None)

    form = ResumenFaltasForm(request.POST or None, curso_id=curso_id)

    if request.method == "POST" and form.is_valid():
        periodos_sel = form.cleaned_data['periodos']

        for p in periodos_sel:
            faltas = protocolo.faltas_injustificadas_periodo(p)
            dias_nj = faltas['dias']
            tramos_nj = faltas['tramos']

            # Cálculo de horas: 6 por cada día completo + tramos sueltos
            horas_faltadas = (dias_nj * 6) + tramos_nj
            # Horas totales del periodo: días lectivos del periodo * 6
            horas_totales_periodo = p.dias_lectivos * 6

            porcentaje = 0
            if horas_totales_periodo > 0:
                porcentaje = (horas_faltadas / horas_totales_periodo) * 100

            resumen.append({
                'periodo': p.descripcion or str(p),
                'rango': f"{p.inicio.strftime('%d/%m')} al {p.fin.strftime('%d/%m')}",
                'dias_nj': dias_nj,
                'tramos_nj': tramos_nj,
                'total_horas': horas_faltadas,
                'porcentaje': round(porcentaje, 2)
            })

    context = {
        'protocolo': protocolo,
        'form': form,
        'resumen': resumen,
        'titulo': f"Resumen de Faltas: {protocolo.alumno}"
    }
    return render(request, 'resumen_faltas.html', context)

# ─────────────────────────────────────────────────────────────
# Helpers: construir el dict "initial" desde el modelo guardado
# ─────────────────────────────────────────────────────────────

def _initial_fm(informe):
    """Convierte InformeFM → dict con los valores para precargar la plantilla."""
    return {
        'asignacion_tutores':            informe.asignacion_tutores or '1P_2M',
        'hermanos_centro':               informe.hermanos_centro,
        'hermanos_centro_numero':        informe.hermanos_centro_nro or '',
        'hermanos_absentistas':          informe.hermanos_absentistas,
        'hermanos_absentistas_numero':   informe.hermanos_absentistas_nro or '',
        'hermanos_nombres':              informe.hermanos_absentistas_nombres,
        'otros_convivientes':            informe.otros_convivientes,
        'informe_actuaciones':           informe.informe_actuaciones,
        'valoracion_educativa':          informe.valoracion_educativa,
        'comparecencia_menor':           informe.comparecencia_menor,
        'llamadas_citaciones':           informe.llamadas_citaciones,
        'comparecencia_tutores_legales': informe.comparecencia_tutores_legales,
    }


def _initial_ssc(informe):
    """Convierte InformeSSC → dict con los valores para precargar la plantilla."""
    ant = ''
    if informe.ant_primera_vez:
        ant = 'PRIMERA'
    elif informe.ant_reiteradas:
        ant = 'REITERADA'

    return {
        'dirigido_a':            informe.dirigido_a,
        'fecha_derivacion':      informe.fecha_derivacion.strftime('%Y-%m-%d') if informe.fecha_derivacion else '',
        # Psicopedagógica
        'psi_des':               informe.psi_des,
        'psi_dia':               informe.psi_dia,
        'psi_dis':               informe.psi_dis,
        'psi_tdah':              informe.psi_tdah,
        'psi_aaccii':            informe.psi_aaccii,
        'psi_otros':             informe.psi_otros,
        # Servicios del centro (los 10)
        'serv_aula_matinal':     informe.serv_aula_matinal,
        'serv_atal':             informe.serv_atal,
        'serv_comedor':          informe.serv_comedor,
        'serv_acompanamiento':   informe.serv_acompanamiento,
        'serv_parcep':           informe.serv_parcep,
        'serv_deporte':          informe.serv_deporte,
        'serv_actividades_ayto': informe.serv_actividades_ayto,
        'serv_pale':             informe.serv_pale,
        'serv_pali':             informe.serv_pali,
        'serv_otras_act':        informe.serv_otras_act,
        'serv_otros':            informe.serv_otros,
        # Antecedentes
        'hermanos_nombres':      informe.hermanos_nombres,
        'hermanos_centros':      informe.hermanos_centros,
        'antecedentes_tipo':     ant,
        'ant_curso_inicio':      str(informe.ant_curso_inicio) if informe.ant_curso_inicio else '',
        # Dificultades
        'dif_iguales':           informe.dif_iguales,
        'dif_profesorado':       informe.dif_profesorado,
        'dif_disruptivo':        informe.dif_disruptivo,
        'dif_salud_mental':      informe.dif_salud_mental,
        # Medidas acordadas
        'med_compromisos':       informe.med_compromisos,
        'med_aula_convivencia':  informe.med_aula_convivencia,
        'med_talleres':          informe.med_talleres,
        'med_mediacion':         informe.med_mediacion,
        'med_observaciones':     informe.med_observaciones,
        # Familiar
        'fam_relaciones':        informe.fam_relaciones,
        'fam_economicas':        informe.fam_economicas,
        'fam_educativas':        informe.fam_educativas,
        'fam_riesgo':            informe.fam_riesgo,
        'fam_observaciones':     informe.fam_observaciones,
        # Actuaciones
        'act_tutor':             informe.act_tutor,
        'act_eoe':               informe.act_eoe,
        'act_equipo_dir':        informe.act_equipo_dir,
        'act_motivos_familia':   informe.act_motivos_familia,
        # Individuales
        'ind_refuerzo':          informe.ind_refuerzo,
        'ind_tutorial':          informe.ind_tutorial,
        'ind_eoe':               informe.ind_eoe,
        'ind_observaciones':     informe.ind_observaciones,
        # Otra info
        'otra_info':             informe.otra_info,
    }


# ─────────────────────────────────────────────────────────────
# Helpers: guardar POST → modelo
# ─────────────────────────────────────────────────────────────

def _guardar_fm(informe, post):
    informe.asignacion_tutores           = post.get('asignacion_tutores', '1P_2M')
    informe.hermanos_centro              = post.get('hermanos_centro', '')
    informe.hermanos_centro_nro          = int(post.get('hermanos_centro_numero') or 0)
    informe.hermanos_absentistas         = post.get('hermanos_absentistas', '')
    informe.hermanos_absentistas_nro     = int(post.get('hermanos_absentistas_numero') or 0)
    informe.hermanos_absentistas_nombres = post.get('hermanos_nombres', '')
    informe.otros_convivientes           = post.get('otros_convivientes', '')
    informe.informe_actuaciones          = post.get('informe_actuaciones', '')
    informe.valoracion_educativa         = post.get('valoracion_educativa', '')
    informe.comparecencia_menor          = post.get('comparecencia_menor', '')
    informe.llamadas_citaciones          = post.get('llamadas_citaciones', '')
    informe.comparecencia_tutores_legales = post.get('comparecencia_tutores_legales', '')
    informe.save()


def _guardar_ssc(informe, post):
    informe.dirigido_a             = post.get('dirigido_a', '')
    informe.fecha_derivacion       = post.get('fecha_derivacion') or None
    # Psicopedagógica
    informe.psi_des                = bool(post.get('psi_des'))
    informe.psi_dia                = bool(post.get('psi_dia'))
    informe.psi_dis                = bool(post.get('psi_dis'))
    informe.psi_tdah               = bool(post.get('psi_tdah'))
    informe.psi_aaccii             = bool(post.get('psi_aaccii'))
    informe.psi_otros              = post.get('psi_otros', '')
    # Servicios
    informe.serv_aula_matinal      = bool(post.get('serv_aula_matinal'))
    informe.serv_atal              = bool(post.get('serv_atal'))
    informe.serv_comedor           = bool(post.get('serv_comedor'))
    informe.serv_acompanamiento    = bool(post.get('serv_acompanamiento'))
    informe.serv_parcep            = bool(post.get('serv_parcep'))
    informe.serv_deporte           = bool(post.get('serv_deporte'))
    informe.serv_actividades_ayto  = bool(post.get('serv_actividades_ayto'))
    informe.serv_pale              = bool(post.get('serv_pale'))
    informe.serv_pali              = bool(post.get('serv_pali'))
    informe.serv_otras_act         = bool(post.get('serv_otras_act'))
    informe.serv_otros             = post.get('serv_otros', '')
    # Antecedentes
    informe.hermanos_nombres       = post.get('hermanos_nombres', '')
    informe.hermanos_centros       = post.get('hermanos_centros', '')
    ant = post.get('antecedentes_tipo', '')
    informe.ant_primera_vez        = (ant == 'PRIMERA')
    informe.ant_reiteradas         = (ant == 'REITERADA')
    # Dificultades
    informe.dif_iguales            = bool(post.get('dif_iguales'))
    informe.dif_profesorado        = bool(post.get('dif_profesorado'))
    informe.dif_disruptivo         = bool(post.get('dif_disruptivo'))
    informe.dif_salud_mental       = bool(post.get('dif_salud_mental'))
    # Medidas
    informe.med_compromisos        = bool(post.get('med_compromisos'))
    informe.med_aula_convivencia   = bool(post.get('med_aula_convivencia'))
    informe.med_talleres           = bool(post.get('med_talleres'))
    informe.med_mediacion          = bool(post.get('med_mediacion'))
    informe.med_observaciones      = post.get('med_observaciones', '')
    # Familiar
    informe.fam_relaciones         = bool(post.get('fam_relaciones'))
    informe.fam_economicas         = bool(post.get('fam_economicas'))
    informe.fam_educativas         = bool(post.get('fam_educativas'))
    informe.fam_riesgo             = bool(post.get('fam_riesgo'))
    informe.fam_observaciones      = post.get('fam_observaciones', '')
    # Actuaciones
    informe.act_tutor              = post.get('act_tutor', '')
    informe.act_eoe                = post.get('act_eoe', '')
    informe.act_equipo_dir         = post.get('act_equipo_dir', '')
    informe.act_motivos_familia    = post.get('act_motivos_familia', '')
    # Individuales
    informe.ind_refuerzo           = bool(post.get('ind_refuerzo'))
    informe.ind_tutorial           = bool(post.get('ind_tutorial'))
    informe.ind_eoe                = bool(post.get('ind_eoe'))
    informe.ind_observaciones      = post.get('ind_observaciones', '')
    # Otra info
    informe.otra_info              = post.get('otra_info', '')
    informe.save()


# ─────────────────────────────────────────────────────────────
# ANEXO I  —  Informe Fiscalía de Menores
# ─────────────────────────────────────────────────────────────


@login_required(login_url='/')
@user_passes_test(group_check_je, login_url='/')
def editar_informe_fm(request, protocolo_id):
    protocolo = get_object_or_404(ProtocoloAbs, pk=protocolo_id)
    informe, _ = InformeFM.objects.get_or_create(protocolo=protocolo)

    if request.method == 'POST':
        _guardar_fm(informe, request.POST)

        if request.POST.get('accion') == 'guardar_pdf':
            campos   = campos_informe_FM(protocolo, request.POST)
            adjuntos = informe.adjuntos.all()
            nombre   = f"informe_fiscalia_{protocolo.id}.pdf"
            return cumplimentar_pdf_form(
                PLANTILLA_FM, campos, nombre, descarga=True,
                adjuntos=adjuntos,
                titulo_informe=f"Informe para Fiscalía de Menores · {protocolo.alumno.Nombre}",
            )

        return redirect('editar_informe_fm', protocolo_id=protocolo_id)

    return render(request, 'informe_fm.html', {
        'protocolo':          protocolo,
        'informe':            informe,
        'initial':            _initial_fm(informe),
        'adjuntos':           informe.adjuntos.all(),
        'asignacion_choices': ASIGNACION_CHOICES,
        'hermanos_choices':   HERMANOS_CHOICES,
    })

@login_required(login_url='/')
@user_passes_test(group_check_je, login_url='/')
def descargar_pdf_fm(request, protocolo_id):
    protocolo = get_object_or_404(ProtocoloAbs, pk=protocolo_id)
    informe   = get_object_or_404(InformeFM, protocolo=protocolo)
    campos    = campos_informe_FM(protocolo, _initial_fm(informe))
    adjuntos  = informe.adjuntos.all()
    nombre    = f"informe_fiscalia_{protocolo.id}.pdf"
    return cumplimentar_pdf_form(
        PLANTILLA_FM, campos, nombre, descarga=True,
        adjuntos=adjuntos,
        titulo_informe=f"Informe para Fiscalía de Menores · {protocolo.alumno.Nombre}",
    )

# ── Adjuntos FM ──────────────────────────────────────────────
@login_required(login_url='/')
@user_passes_test(group_check_je, login_url='/')
@require_POST
def subir_adjunto_fm(request, protocolo_id):
    """Sube un adjunto vía AJAX y devuelve JSON con los datos del nuevo registro."""
    protocolo = get_object_or_404(ProtocoloAbs, pk=protocolo_id)
    informe, _ = InformeFM.objects.get_or_create(protocolo=protocolo)

    archivo     = request.FILES.get('archivo')
    descripcion = request.POST.get('descripcion', '').strip()

    if not archivo or not descripcion:
        return JsonResponse({'ok': False, 'error': 'Archivo y descripción son obligatorios.'}, status=400)
    if not archivo.name.lower().endswith('.pdf'):
        return JsonResponse({'ok': False, 'error': 'Solo se permiten archivos PDF.'}, status=400)

    adj = AdjuntoInformeFM.objects.create(
        informe=informe,
        descripcion=descripcion,
        archivo=archivo,
        orden=informe.adjuntos.count(),
    )
    return JsonResponse({
        'ok':          True,
        'id':          adj.pk,
        'descripcion': adj.descripcion,
        'filename':    adj.filename(),
        'url':         adj.archivo.url,
    })


@login_required(login_url='/')
@user_passes_test(group_check_je, login_url='/')
@require_POST
def eliminar_adjunto_fm(request, adjunto_id):
    """Elimina un adjunto FM vía AJAX."""
    adj = get_object_or_404(AdjuntoInformeFM, pk=adjunto_id)
    # Verificar que el usuario tiene acceso al protocolo
    protocolo = adj.informe.protocolo
    # Borrar fichero físico
    ruta = adj.archivo.path
    adj.delete()
    if os.path.isfile(ruta):
        os.remove(ruta)
    return JsonResponse({'ok': True})


@login_required(login_url='/')
@user_passes_test(group_check_je, login_url='/')
@require_POST
def actualizar_descripcion_adjunto_fm(request, adjunto_id):
    """Edita la descripción de un adjunto FM vía AJAX."""
    adj         = get_object_or_404(AdjuntoInformeFM, pk=adjunto_id)
    descripcion = request.POST.get('descripcion', '').strip()
    if not descripcion:
        return JsonResponse({'ok': False, 'error': 'La descripción no puede estar vacía.'}, status=400)
    adj.descripcion = descripcion
    adj.save()
    return JsonResponse({'ok': True, 'descripcion': adj.descripcion})

# ─────────────────────────────────────────────────────────────
# PROTOCOLO DE DERIVACIÓN  —  SS.CC. / Mesa Técnica
# ─────────────────────────────────────────────────────────────
@login_required(login_url='/')
@user_passes_test(group_check_je, login_url='/')
def editar_informe_ssc(request, protocolo_id):
    protocolo = get_object_or_404(ProtocoloAbs, pk=protocolo_id)
    informe, _ = InformeSSC.objects.get_or_create(protocolo=protocolo)

    if request.method == 'POST':
        _guardar_ssc(informe, request.POST)

        if request.POST.get('accion') == 'guardar_pdf':
            campos   = campos_informe_SSC(protocolo, request.POST)
            adjuntos = informe.adjuntos.all()
            nombre   = f"protocolo_derivacion_{protocolo.id}.pdf"
            return cumplimentar_pdf_form(
                PLANTILLA_SSC, campos, nombre, descarga=True,
                adjuntos=adjuntos,
                titulo_informe=f"Protocolo de Derivación SS.CC. · {protocolo.alumno.Nombre}",
            )

        return redirect('editar_informe_ssc', protocolo_id=protocolo_id)

    return render(request, 'informe_ssc.html', {
        'protocolo':           protocolo,
        'informe':             informe,
        'initial':             _initial_ssc(informe),
        'adjuntos':            informe.adjuntos.all(),
        'dirigido_choices':    DIRIGIDO_CHOICES,
        'psico_choices':       PSICO_CHOICES,
        'servicios_choices':   SERVICIOS_CHOICES,
        'dificultades_choices':DIFICULTADES_CHOICES,
        'medidas_choices':     MEDIDAS_CHOICES,
        'familiar_choices':    FAMILIAR_CHOICES,
        'individuales_choices':INDIVIDUALES_CHOICES,
    })

@login_required(login_url='/')
@user_passes_test(group_check_je, login_url='/')
def descargar_pdf_ssc(request, protocolo_id):
    protocolo = get_object_or_404(ProtocoloAbs, pk=protocolo_id)
    informe   = get_object_or_404(InformeSSC, protocolo=protocolo)
    campos    = campos_informe_SSC(protocolo, _initial_ssc(informe))
    adjuntos  = informe.adjuntos.all()
    nombre    = f"protocolo_derivacion_{protocolo.id}.pdf"
    return cumplimentar_pdf_form(
        PLANTILLA_SSC, campos, nombre, descarga=True,
        adjuntos=adjuntos,
        titulo_informe=f"Protocolo de Derivación SS.CC. · {protocolo.alumno.Nombre}",
    )


# ── Adjuntos SSC ─────────────────────────────────────────────

@login_required(login_url='/')
@user_passes_test(group_check_je, login_url='/')
@require_POST
def subir_adjunto_ssc(request, protocolo_id):
    protocolo = get_object_or_404(ProtocoloAbs, pk=protocolo_id)
    informe, _ = InformeSSC.objects.get_or_create(protocolo=protocolo)

    archivo     = request.FILES.get('archivo')
    descripcion = request.POST.get('descripcion', '').strip()

    if not archivo or not descripcion:
        return JsonResponse({'ok': False, 'error': 'Archivo y descripción son obligatorios.'}, status=400)
    if not archivo.name.lower().endswith('.pdf'):
        return JsonResponse({'ok': False, 'error': 'Solo se permiten archivos PDF.'}, status=400)

    adj = AdjuntoInformeSSC.objects.create(
        informe=informe,
        descripcion=descripcion,
        archivo=archivo,
        orden=informe.adjuntos.count(),
    )
    return JsonResponse({
        'ok':          True,
        'id':          adj.pk,
        'descripcion': adj.descripcion,
        'filename':    adj.filename(),
        'url':         adj.archivo.url,
    })


@login_required(login_url='/')
@user_passes_test(group_check_je, login_url='/')
@require_POST
def eliminar_adjunto_ssc(request, adjunto_id):
    adj  = get_object_or_404(AdjuntoInformeSSC, pk=adjunto_id)
    ruta = adj.archivo.path
    adj.delete()
    if os.path.isfile(ruta):
        os.remove(ruta)
    return JsonResponse({'ok': True})


@login_required(login_url='/')
@user_passes_test(group_check_je, login_url='/')
@require_POST
def actualizar_descripcion_adjunto_ssc(request, adjunto_id):
    adj = get_object_or_404(AdjuntoInformeSSC, pk=adjunto_id)
    descripcion = request.POST.get('descripcion', '').strip()
    if not descripcion:
        return JsonResponse({'ok': False, 'error': 'La descripción no puede estar vacía.'}, status=400)
    adj.descripcion = descripcion
    adj.save()
    return JsonResponse({'ok': True, 'descripcion': adj.descripcion})


@login_required(login_url='/')
@user_passes_test(group_check_je, login_url='/')
def calendario_asistencia(request, protocolo_id):
    protocolo  = get_object_or_404(ProtocoloAbs, pk=protocolo_id)
    alumno     = protocolo.alumno
    hoy        = date.today()

    # Calendario lectivo del curso
    cal_lectivo = CalendariosLectivos.objects.filter(
        curso_academico=protocolo.curso_academico
    ).prefetch_related('periodos_lectivos__festivos').first()

    if not cal_lectivo:
        return render(request, 'calendario_asistencia.html', {
            'protocolo': protocolo,
            'alumno':    alumno,
            'filas':     [],
            'totales':   {},
        })

    # Construir sets de días lectivos y festivos
    dias_lectivos_set = set()
    festivos_set      = set()

    for periodo in cal_lectivo.periodos_lectivos.all():
        d = periodo.inicio
        while d <= periodo.fin:
            if d.weekday() < 5:
                dias_lectivos_set.add(d)
            d += timedelta(days=1)
        for festivo in periodo.festivos.all():
            festivos_set.add(festivo.fecha)
            dias_lectivos_set.discard(festivo.fecha)

    # Faltas del protocolo indexadas por fecha
    faltas_qs   = FaltasProtocolo.objects.filter(Protocolo=protocolo)
    faltas_dict = {f.Fecha: f for f in faltas_qs}

    # Rango de meses: Sep del año_inicio → Jun del año_fin del curso académico actual
    curso_academico_actual = get_current_academic_year()
    fecha_inicio = date(curso_academico_actual.año_inicio, 9, 1)
    fecha_fin    = date(curso_academico_actual.año_fin,    6, 30)

    # Construir estructura de meses
    meses_nombres = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                     'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    dias_semana   = ['L', 'M', 'X', 'J', 'V', 'S', 'D']

    meses = []
    anio_actual = fecha_inicio.year
    mes_actual  = fecha_inicio.month

    while (anio_actual, mes_actual) <= (fecha_fin.year, fecha_fin.month):
        cal_mes  = calendar.monthcalendar(anio_actual, mes_actual)
        semanas  = []
        # Resumen en TRAMOS horarios (1 día = 6 tramos)
        resumen  = {'tr_lectivos': 0, 'tr_ok': 0, 'tr_j': 0, 'tr_nj': 0}

        for semana in cal_mes:
            dias_semana_data = []
            for num_dia in semana:
                if num_dia == 0:
                    dias_semana_data.append(None)
                    continue

                fecha = date(anio_actual, mes_actual, num_dia)

                # Días fuera del rango del curso: celda vacía neutra
                if fecha < fecha_inicio or fecha > fecha_fin:
                    dias_semana_data.append({
                        'num': num_dia,
                        'tipo': 'fuera-rango',
                        'gradiente': '', 'tooltip': '',
                        'tramos_nj': 0, 'tramos_j': 0, 'tramos_ok': 0,
                    })
                    continue

                info = _datos_dia(fecha, faltas_dict, dias_lectivos_set, festivos_set, hoy)

                # Solo los días lectivos pasados computan en el resumen
                if info['tipo'] == 'lectivo':
                    resumen['tr_lectivos'] += TRAMOS_DIA
                    resumen['tr_ok']  += info['tramos_ok']
                    resumen['tr_j']   += info['tramos_j']
                    resumen['tr_nj']  += info['tramos_nj']
                # tipo 'futuro' → no computa

                dias_semana_data.append({'num': num_dia, 'fecha': fecha, **info})

            semanas.append(dias_semana_data)

        meses.append({
            'nombre':      meses_nombres[mes_actual],
            'anio':        anio_actual,
            'semanas':     semanas,
            'dias_semana': dias_semana,
            'resumen':     resumen,
        })

        mes_actual += 1
        if mes_actual > 12:
            mes_actual  = 1
            anio_actual += 1

    # Totales globales en tramos
    tr_lect = sum(m['resumen']['tr_lectivos'] for m in meses)
    tr_ok   = sum(m['resumen']['tr_ok']       for m in meses)
    tr_j    = sum(m['resumen']['tr_j']        for m in meses)
    tr_nj   = sum(m['resumen']['tr_nj']       for m in meses)

    totales = {
        'tr_lectivos': tr_lect,
        'tr_ok':  tr_ok,
        'tr_j':   tr_j,
        'tr_nj':  tr_nj,
        'pct_ok': round(tr_ok / tr_lect * 100) if tr_lect else 0,
        'pct_j':  round(tr_j  / tr_lect * 100) if tr_lect else 0,
        'pct_nj': round(tr_nj / tr_lect * 100) if tr_lect else 0,
        'barra':  _gradiente(tr_nj, tr_j, tr_ok),
    }

    filas = [meses[i:i+3] for i in range(0, len(meses), 3)]

    return render(request, 'calendario_asistencia.html', {
        'protocolo': protocolo,
        'alumno':    alumno,
        'filas':     filas,
        'totales':   totales,
    })

@login_required(login_url='/')
@user_passes_test(group_check_je, login_url='/')
def descargar_pdf_calendario(request, protocolo_id):
    """
    Genera el PDF del calendario de asistencia (WeasyPrint).
    12 meses completos Sep→Ago, una sola página A4 vertical (4 filas × 3 cols).
    Cada día lectivo muestra un rectángulo con 6 franjas de color proporcionales:
        rojo    → tramos NJ  (arriba)
        amarillo→ tramos J   (medio)
        verde   → asistencia (abajo)
    """
    protocolo = get_object_or_404(ProtocoloAbs, pk=protocolo_id)
    alumno    = protocolo.alumno

    curso_academico_actual = get_current_academic_year()
    fecha_inicio = date(curso_academico_actual.año_inicio, 9,  1)
    fecha_fin    = date(curso_academico_actual.año_fin,    8, 31)

    # ── Calendario lectivo ────────────────────────────────────────────
    cal_lectivo = CalendariosLectivos.objects.filter(
        curso_academico=protocolo.curso_academico
    ).prefetch_related('periodos_lectivos__festivos').first()

    dias_lectivos_set = set()
    festivos_set      = set()

    if cal_lectivo:
        for periodo in cal_lectivo.periodos_lectivos.all():
            d = periodo.inicio
            while d <= periodo.fin:
                if d.weekday() < 5:
                    dias_lectivos_set.add(d)
                d += timedelta(days=1)
            for festivo in periodo.festivos.all():
                festivos_set.add(festivo.fecha)
                dias_lectivos_set.discard(festivo.fecha)

    # ── Faltas ────────────────────────────────────────────────────────
    faltas_dict = {
        f.Fecha: f
        for f in FaltasProtocolo.objects.filter(Protocolo=protocolo)
    }

    # ── 12 meses ─────────────────────────────────────────────────────
    hoy = date.today()
    MESES_NOMBRES = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                     'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    DIAS_SEMANA   = ['L', 'M', 'X', 'J', 'V', 'S', 'D']

    meses = []
    anio_actual = fecha_inicio.year
    mes_actual  = fecha_inicio.month

    while (anio_actual, mes_actual) <= (fecha_fin.year, fecha_fin.month):
        semanas = []
        # Resumen en TRAMOS horarios
        res = {'tr_lectivos': 0, 'tr_ok': 0, 'tr_j': 0, 'tr_nj': 0}

        for semana in calendar.monthcalendar(anio_actual, mes_actual):
            fila = []
            for num_dia in semana:
                if num_dia == 0:
                    fila.append(None)
                    continue
                fecha = date(anio_actual, mes_actual, num_dia)
                info  = _datos_dia(fecha, faltas_dict, dias_lectivos_set, festivos_set, hoy)
                if info['tipo'] == 'lectivo':
                    res['tr_lectivos'] += TRAMOS_DIA
                    res['tr_ok']  += info['tramos_ok']
                    res['tr_j']   += info['tramos_j']
                    res['tr_nj']  += info['tramos_nj']
                # tipo 'futuro' → no se acumula en ningún contador
                fila.append({'num': num_dia, **info})
            semanas.append(fila)

        meses.append({
            'nombre': MESES_NOMBRES[mes_actual], 'anio': anio_actual,
            'semanas': semanas, 'dias_semana': DIAS_SEMANA, 'resumen': res,
        })
        mes_actual += 1
        if mes_actual > 12:
            mes_actual = 1; anio_actual += 1

    filas = [meses[i:i + 3] for i in range(0, len(meses), 3)]

    # ── Totales globales en tramos ────────────────────────────────────
    tr_lect = sum(m['resumen']['tr_lectivos'] for m in meses)
    tr_ok   = sum(m['resumen']['tr_ok']       for m in meses)
    tr_j    = sum(m['resumen']['tr_j']        for m in meses)
    tr_nj   = sum(m['resumen']['tr_nj']       for m in meses)

    totales = {
        'tr_lectivos': tr_lect,
        'tr_ok':  tr_ok,
        'tr_j':   tr_j,
        'tr_nj':  tr_nj,
        'pct_ok': round(tr_ok / tr_lect * 100) if tr_lect else 0,
        'pct_j':  round(tr_j  / tr_lect * 100) if tr_lect else 0,
        'pct_nj': round(tr_nj / tr_lect * 100) if tr_lect else 0,
        # gradiente de la barra de resumen proporcional
        'barra':  _gradiente(tr_nj, tr_j, tr_ok),
    }

    context = {
        'protocolo':              protocolo,
        'alumno':                 alumno,
        'curso_academico_actual': curso_academico_actual,
        'filas':                  filas,
        'totales':                totales,
        'fecha_generacion':       hoy,
    }

    html_string = render_to_string('calendario_asistencia_pdf.html', context)
    font_config = FontConfiguration()
    pdf_bytes   = HTML(string=html_string).write_pdf(font_config=font_config)

    nombre = (
        f"calendario_{alumno.Nombre.replace(' ', '_').replace(',', '')}"
        f"_protocolo_{protocolo.pk}.pdf"
    )
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{nombre}"'
    return response