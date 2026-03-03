
from io import BytesIO
from pypdf import PdfReader, PdfWriter
from datetime import date
from weasyprint import HTML as WeasyHTML

from django.http import HttpResponse

from centro.models import CalendariosLectivos, InfoAlumnos

TRAMOS_DIA = 6  # Número de tramos lectivos por día

# ─────────────────────────────────────────────────────────────
# Generador de la página de índice de adjuntos
# ─────────────────────────────────────────────────────────────

def _generar_indice_adjuntos(adjuntos_info, titulo_informe=""):
    """
    Genera en memoria una página PDF con el índice de documentos adjuntos.

    :param adjuntos_info:   Lista de dicts con claves:
                              'numero'      → int  (posición 1-based)
                              'descripcion' → str
                              'paginas'     → int  (páginas del adjunto)
                              'pagina_ini'  → int  (nº de página en el PDF final)
    :param titulo_informe:  Texto opcional para la cabecera de la página.
    :returns:               bytes del PDF de una sola página.
    """
    from datetime import date as _date

    filas_html = ""
    for item in adjuntos_info:
        filas_html += f"""
        <tr>
          <td class="num">{item['numero']}</td>
          <td class="desc">{item['descripcion']}</td>
          <td class="pags">{item['paginas']}</td>
          <td class="inicio">{item['pagina_ini']}</td>
        </tr>"""

    hoy = _date.today().strftime("%d/%m/%Y")

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<style>
  @page {{
    size: A4 portrait;
    margin: 22mm 20mm 20mm 20mm;
    @bottom-right {{
      content: "{hoy}";
      font-family: 'DejaVu Sans Mono', monospace;
      font-size: 7pt;
      color: #aaa;
    }}
  }}

  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  body {{
    font-family: 'DejaVu Sans', sans-serif;
    font-size: 9pt;
    color: #111;
  }}

  /* ── Cabecera ── */
  .cab {{
    border-bottom: 2pt solid #111;
    padding-bottom: 8pt;
    margin-bottom: 18pt;
  }}
  .cab-titulo {{
    font-size: 7pt;
    font-family: 'DejaVu Sans Mono', monospace;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #555;
    margin-bottom: 4pt;
  }}
  .cab-h1 {{
    font-size: 16pt;
    font-weight: bold;
    letter-spacing: -0.02em;
    line-height: 1.1;
  }}
  .cab-sub {{
    font-family: 'DejaVu Sans Mono', monospace;
    font-size: 7.5pt;
    color: #444;
    margin-top: 4pt;
  }}

  /* ── Tabla de índice ── */
  table {{
    width: 100%;
    border-collapse: collapse;
    margin-top: 4pt;
  }}
  thead tr {{
    border-bottom: 1pt solid #111;
  }}
  thead th {{
    font-family: 'DejaVu Sans Mono', monospace;
    font-size: 7pt;
    font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    padding: 5pt 6pt 5pt 0;
    color: #222;
    text-align: left;
  }}
  thead th.num    {{ width: 30pt;  text-align: center; }}
  thead th.pags   {{ width: 42pt;  text-align: center; }}
  thead th.inicio {{ width: 52pt;  text-align: center; }}

  tbody tr {{
    border-bottom: 0.3pt solid #ddd;
  }}
  tbody tr:last-child {{
    border-bottom: 1pt solid #999;
  }}
  tbody td {{
    padding: 7pt 6pt 7pt 0;
    vertical-align: middle;
    font-size: 9pt;
  }}
  td.num {{
    font-family: 'DejaVu Sans Mono', monospace;
    font-size: 8pt;
    text-align: center;
    color: #888;
  }}
  td.desc {{
    line-height: 1.3;
  }}
  td.pags {{
    font-family: 'DejaVu Sans Mono', monospace;
    font-size: 8.5pt;
    text-align: center;
    font-weight: bold;
  }}
  td.inicio {{
    font-family: 'DejaVu Sans Mono', monospace;
    font-size: 8.5pt;
    text-align: center;
    color: #444;
  }}

  /* ── Nota al pie ── */
  .nota {{
    margin-top: 16pt;
    font-size: 7pt;
    color: #888;
    font-family: 'DejaVu Sans Mono', monospace;
    border-top: 0.3pt solid #ddd;
    padding-top: 6pt;
  }}
</style>
</head>
<body>

<div class="cab">
  <div class="cab-titulo">Documentación adjunta</div>
  <div class="cab-h1">Índice de documentos</div>
  {"<div class='cab-sub'>" + titulo_informe + "</div>" if titulo_informe else ""}
</div>

<table>
  <thead>
    <tr>
      <th class="num">Nº</th>
      <th class="desc">Descripción del documento</th>
      <th class="pags">Páginas</th>
      <th class="inicio">Pág. inicio</th>
    </tr>
  </thead>
  <tbody>
    {filas_html}
  </tbody>
</table>

<div class="nota">
  Los documentos adjuntos se presentan a continuación en el orden indicado.
  La numeración de página inicio hace referencia a la paginación del documento completo.
</div>

</body>
</html>"""

    pdf_bytes = WeasyHTML(string=html).write_pdf()
    return pdf_bytes

# ─────────────────────────────────────────────────────────────
# Función genérica de cumplimentación + fusión de adjuntos
# ─────────────────────────────────────────────────────────────

def cumplimentar_pdf_form(input_file, fields, output_file,
                           descarga=True, adjuntos=None,
                           titulo_informe=""):
    """
    Rellena los campos AcroForm de input_file, añade opcionalmente una página
    de índice y las páginas de los adjuntos guardados, y devuelve un
    HttpResponse con el PDF resultante.

    :param input_file:      Ruta al PDF plantilla.
    :param fields:          Dict {nombre_campo: valor}.
    :param output_file:     Nombre sugerido para la descarga.
    :param descarga:        True  → Content-Disposition: attachment
                            False → inline (abrir en el navegador)
    :param adjuntos:        QuerySet o lista de AdjuntoInformeFM / AdjuntoInformeSSC.
                            Si no está vacío se añade primero la página de índice
                            y luego las páginas de cada adjunto.
    :param titulo_informe:  Texto descriptivo para la cabecera del índice,
                            p. ej. "Informe para Fiscalía · Sara García López".
    """
    # 1. Rellenar el informe principal
    reader = PdfReader(input_file)
    writer = PdfWriter()
    writer.append(reader)

    for page in writer.pages:
        writer.update_page_form_field_values(page, fields, auto_regenerate=True)

    # 2. Procesar adjuntos (si los hay)
    if adjuntos:
        # 2a. Leer cada adjunto y contar sus páginas; descartar los corruptos
        adjuntos_validos = []
        for adjunto in adjuntos:
            try:
                reader_adj = PdfReader(adjunto.archivo.path)
                n_paginas  = len(reader_adj.pages)
                adjuntos_validos.append({
                    'adjunto':  adjunto,
                    'reader':   reader_adj,
                    'paginas':  n_paginas,
                })
            except Exception:
                pass  # Adjunto corrupto o huérfano: se omite

        if adjuntos_validos:
            # 2b. Calcular la página de inicio de cada adjunto en el PDF final.
            #     El informe principal ya está en writer; su longitud es la base.
            pagina_ini  = len(writer.pages) + 2  # +1 por la página de índice (1-based)
            adjuntos_info = []
            for i, item in enumerate(adjuntos_validos):
                adjuntos_info.append({
                    'numero':      i + 1,
                    'descripcion': item['adjunto'].descripcion,
                    'paginas':     item['paginas'],
                    'pagina_ini':  pagina_ini,
                })
                pagina_ini += item['paginas']

            # 2c. Generar la página de índice e insertarla
            indice_bytes  = _generar_indice_adjuntos(adjuntos_info, titulo_informe)
            indice_reader = PdfReader(BytesIO(indice_bytes))
            writer.append(indice_reader)

            # 2d. Añadir las páginas de cada adjunto
            for item in adjuntos_validos:
                writer.append(item['reader'])

    # 3. Escribir en buffer y devolver respuesta HTTP
    buffer = BytesIO()
    writer.write(buffer)
    buffer.seek(0)

    response = HttpResponse(buffer.read(), content_type='application/pdf')
    disposition = 'attachment' if descarga else 'inline'
    response['Content-Disposition'] = f'{disposition}; filename="{output_file}"'
    return response



# ─────────────────────────────────────────────────────────────
# ANEXO I · Informe para Fiscalía de Menores
# ─────────────────────────────────────────────────────────────

def campos_informe_FM(protocolo, form_data=None):
    alumno      = protocolo.alumno
    info_alumno = InfoAlumnos.objects.filter(
        Alumno=alumno,
        curso_academico=protocolo.curso_academico
    ).first()

    unidad       = alumno.Unidad.Curso if alumno.Unidad else ""
    tutor        = alumno.Unidad.Tutor if alumno.Unidad else None
    tutor_unidad = f'{tutor.Nombre} {tutor.Apellidos}' if tutor else ""

    edad  = int(round((date.today() - alumno.Fecha_nacimiento).days / 365.25, 0))
    hoy   = date.today()
    meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
             "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

    campos = {
        'alumno_nombre':          alumno.Nombre,
        'alumno_edad':            str(edad),
        'alumno_fechanacimiento': alumno.Fecha_nacimiento.strftime('%d/%m/%Y'),
        'alumno_domicilio':       info_alumno.Direccion if info_alumno and info_alumno.Direccion else '',
        'alumno_localidad':       info_alumno.Localidad if info_alumno and info_alumno.Localidad else '',
        'alumno_telefono':        info_alumno.Telefono  if info_alumno and info_alumno.Telefono  else '',
        'alumno_email':           info_alumno.Email     if info_alumno and info_alumno.Email      else '',
        'alumno_cuso':            unidad,
        'alumno_tutorcurso':      tutor_unidad,
        'fecha_inicio_protocolo': protocolo.fecha_apertura.strftime('%d/%m/%Y') if protocolo.fecha_apertura else '',
        'fecha_dia':              str(hoy.day),
        'fecha_mes':              meses[hoy.month - 1],
        'fecha_a#C3#B1o':         str(hoy.year),
    }

    if form_data:
        padre_nom = padre_dni = madre_nom = madre_dni = ""
        asignacion = form_data.get('asignacion_tutores', '')
        t1_nom = (info_alumno.NombreTutor1 or "") if info_alumno else ""
        t1_dni = (info_alumno.DniTutor1    or "") if info_alumno else ""
        t2_nom = (info_alumno.NombreTutor2 or "") if info_alumno else ""
        t2_dni = (info_alumno.DniTutor2    or "") if info_alumno else ""

        if asignacion == '1P_2M':
            padre_nom, padre_dni, madre_nom, madre_dni = t1_nom, t1_dni, t2_nom, t2_dni
        elif asignacion == '1M_2P':
            madre_nom, madre_dni, padre_nom, padre_dni = t1_nom, t1_dni, t2_nom, t2_dni
        elif asignacion == 'SOLO_1P':
            padre_nom, padre_dni = t1_nom, t1_dni
        elif asignacion == 'SOLO_1M':
            madre_nom, madre_dni = t1_nom, t1_dni
        elif asignacion == 'SOLO_2P':
            padre_nom, padre_dni = t2_nom, t2_dni
        elif asignacion == 'SOLO_2M':
            madre_nom, madre_dni = t2_nom, t2_dni

        campos.update({
            'alumno_nombrepadre': padre_nom,
            'alumno_dnipadre':    padre_dni,
            'alumno_nombremadre': madre_nom,
            'alumno_dnimadre':    madre_dni,
        })

        h_centro = form_data.get('hermanos_centro', '')
        campos['hermanos_centro_si']     = '/Yes' if h_centro == 'SI' else '/Off'
        campos['hermanos_centro_no']     = '/Yes' if h_centro == 'NO' else '/Off'
        campos['hermanos_centro_nosabe'] = '/Yes' if h_centro == 'NS' else '/Off'

        h_absent = form_data.get('hermanos_absentistas', '')
        campos['hermanos_absentistas_si']     = '/Yes' if h_absent == 'SI' else '/Off'
        campos['hermanos_absentistas_no']     = '/Yes' if h_absent == 'NO' else '/Off'
        campos['hermanos_absentistas_nosabe'] = '/Yes' if h_absent == 'NS' else '/Off'

        campos.update({
            'hermanos_centro_numero':        str(form_data.get('hermanos_centro_numero') or ''),
            'hermanos_absentistas_numero':   str(form_data.get('hermanos_absentistas_numero') or ''),
            'hermanos_nombres':              form_data.get('hermanos_nombres', ''),
            'otros_convivientes':            form_data.get('otros_convivientes', ''),
            'informe_actuaciones':           form_data.get('informe_actuaciones', ''),
            'valoracion_educativa':          form_data.get('valoracion_educativa', ''),
            'comparecencia_menor':           form_data.get('comparecencia_menor', ''),
            'llamadas_citaciones':           form_data.get('llamadas_citaciones', ''),
            'comparecencia_tutores_legales': form_data.get('comparecencia_tutores_legales', ''),
        })

    # Faltas por periodo
    calendario = CalendariosLectivos.objects.filter(
        curso_academico=protocolo.curso_academico
    ).first()
    if calendario:
        resumen = []
        for periodo in calendario.periodos_lectivos.all():
            if protocolo.hay_faltas(periodo):
                res = protocolo.faltas_injustificadas_periodo(periodo)
                resumen.append((periodo, res['tramos'], res['dias'],
                                res['total tramos'], res['porcentaje']))
        for i, datos in enumerate(resumen):
            idx = i + 1
            if idx <= 9:
                tramos_key = f'periodo{idx}_tramos' if idx != 9 else 'periodo8_tramos_2'
                campos.update({
                    f'periodo{idx}_nombre':     datos[0].nombre_corto(),
                    tramos_key:                 str(datos[1]),
                    f'periodo{idx}_dias':       str(datos[2]),
                    f'periodo{idx}_totalhoras': str(datos[3]),
                    f'periodo{idx}_porcentaje': f'{datos[4]} %',
                })

    return campos


# ─────────────────────────────────────────────────────────────
# PROTOCOLO DE DERIVACIÓN · SS.CC. / Mesa Técnica
# ─────────────────────────────────────────────────────────────

def campos_informe_SSC(protocolo, form_data=None):
    alumno      = protocolo.alumno
    info_alumno = InfoAlumnos.objects.filter(
        Alumno=alumno,
        curso_academico=protocolo.curso_academico
    ).first()
    hoy   = date.today()
    meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
             "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

    SI  = '/Yes'
    OFF = '/Off'
    cb  = lambda b: SI if b else OFF

    pdf = {
        '.Texto1':  'IES Gonzalo Nazareno',
        '.Texto 2': '41011038',
        '.Texto3':  'C/Las Botijas 10',
        '.Texto4':  'Dos Hermanas',
        '.Texto5':  'Sevilla',
        '.Texto6':  'Raúl Reina Molina',
        '.Texto7':  '670213187',
        '.Texto8':  'rreimol902@g.educaand.es',
    }

    tutor = alumno.Unidad.Tutor if alumno.Unidad else None
    pdf['.Texto10'] = alumno.Nombre
    pdf['.Texto11'] = alumno.Fecha_nacimiento.strftime('%d/%m/%Y')
    pdf['.Texto12'] = alumno.Unidad.Curso if alumno.Unidad else ""
    pdf['.Texto13'] = ""
    pdf['.Texto14'] = f'{tutor.Nombre} {tutor.Apellidos}' if tutor else ""
    pdf['.Texto15'] = (info_alumno.NombreTutor1 or "") if info_alumno else ""
    pdf['.Texto16'] = (info_alumno.DniTutor1    or "") if info_alumno else ""
    pdf['.Texto17'] = info_alumno.Telefono  if info_alumno and info_alumno.Telefono  else alumno.Telefono1
    pdf['.Texto18'] = info_alumno.Direccion if info_alumno and info_alumno.Direccion else alumno.Direccion
    pdf['.Texto19'] = info_alumno.Localidad if info_alumno and info_alumno.Localidad else alumno.Localidad
    pdf['.Texto20'] = ""
    pdf['.Texto21'] = (info_alumno.NombreTutor2 or "") if info_alumno else ""
    pdf['.Texto22'] = (info_alumno.DniTutor2    or "") if info_alumno else ""
    pdf['.Texto23'] = pdf['.Texto24'] = pdf['.Texto25'] = pdf['.Texto26'] = pdf['.Texto27'] = ""
    pdf['.Texto42'] = str(hoy.day)
    pdf['.Texto43'] = meses[hoy.month - 1]
    pdf['.Texto44'] = str(hoy.year)

    if not form_data:
        return pdf

    dest = form_data.get('dirigido_a', '')
    pdf['Casilla de verificación3'] = SI  if dest == 'SS_CC'        else OFF
    pdf['Casilla de verificación4'] = SI  if dest == 'MESA_TECNICA' else OFF
    pdf['Casilla de verificación5'] = SI  if dest == 'FISCALIA'     else OFF
    pdf['.Texto9'] = form_data.get('fecha_derivacion', '')

    pdf['Casilla de verificación6']  = cb(form_data.get('psi_des'))
    pdf['Casilla de verificación7']  = cb(form_data.get('psi_dia'))
    pdf['Casilla de verificación8']  = cb(form_data.get('psi_dis'))
    pdf['Casilla de verificación9']  = cb(form_data.get('psi_tdah'))
    pdf['Casilla de verificación10'] = cb(form_data.get('psi_aaccii'))
    pdf['Texto28']                   = form_data.get('psi_otros', '')

    for nombre_form, nombre_pdf in {
        'serv_aula_matinal':     'Casilla de verificación29',
        'serv_atal':             'Casilla de verificación30',
        'serv_comedor':          'Casilla de verificación31',
        'serv_acompanamiento':   'Casilla de verificación32',
        'serv_parcep':           'Casilla de verificación33',
        'serv_deporte':          'Casilla de verificación34',
        'serv_actividades_ayto': 'Casilla de verificación35',
        'serv_pale':             'Casilla de verificación36',
        'serv_pali':             'Casilla de verificación37',
        'serv_otras_act':        'Casilla de verificación38',
    }.items():
        pdf[nombre_pdf] = cb(form_data.get(nombre_form))
    pdf['.Texto29'] = form_data.get('serv_otros', '')

    pdf['.Texto30'] = form_data.get('hermanos_nombres', '')
    pdf['.Texto31'] = form_data.get('hermanos_centros', '')
    ant = form_data.get('antecedentes_tipo', '')
    pdf['Casilla de verificación12'] = SI if ant == 'PRIMERA'   else OFF
    pdf['Casilla de verificación13'] = SI if ant == 'REITERADA' else OFF
    pdf['.Texto32'] = form_data.get('ant_curso_inicio', '')

    pdf['Casilla de verificación14'] = cb(form_data.get('dif_iguales'))
    pdf['Casilla de verificación15'] = cb(form_data.get('dif_profesorado'))
    pdf['Casilla de verificación16'] = cb(form_data.get('dif_disruptivo'))
    pdf['Casilla de verificación17'] = cb(form_data.get('dif_salud_mental'))
    pdf['Casilla de verificación18'] = cb(form_data.get('med_compromisos'))
    pdf['Casilla de verificación19'] = cb(form_data.get('med_aula_convivencia'))
    pdf['Casilla de verificación20'] = cb(form_data.get('med_talleres'))
    pdf['Casilla de verificación21'] = cb(form_data.get('med_mediacion'))
    pdf['Texto33']                   = form_data.get('med_observaciones', '')
    pdf['Casilla de verificación22'] = cb(form_data.get('fam_relaciones'))
    pdf['Casilla de verificación23'] = cb(form_data.get('fam_economicas'))
    pdf['Casilla de verificación24'] = cb(form_data.get('fam_educativas'))
    pdf['Casilla de verificación25'] = cb(form_data.get('fam_riesgo'))
    pdf['Texto34']                   = form_data.get('fam_observaciones', '')
    pdf['.Texto36'] = form_data.get('act_tutor', '')
    pdf['.Texto37'] = form_data.get('act_eoe', '')
    pdf['.Texto38'] = form_data.get('act_equipo_dir', '')
    pdf['Texto35']  = form_data.get('act_motivos_familia', '')
    pdf['Casilla de verificación26'] = cb(form_data.get('ind_refuerzo'))
    pdf['Casilla de verificación27'] = cb(form_data.get('ind_tutorial'))
    pdf['Casilla de verificación28'] = cb(form_data.get('ind_eoe'))
    pdf['Texto39']                   = form_data.get('ind_observaciones', '')
    pdf['.Texto40'] = form_data.get('otra_info', '')

    return pdf

# ─────────────────────────────────────────────────────────────
# Funciones auxiliares para calendario de asistencia
# ─────────────────────────────────────────────────────────────
def _datos_dia(fecha, faltas_dict, dias_lectivos_set, festivos_set, hoy):
    """
    Devuelve un dict con la información de tramos para renderizar el día.

    Campos devueltos:
        tipo        → 'no-lectivo' | 'futuro' | 'lectivo'
        tramos_nj   → int  (0-6) tramos de falta no justificada
        tramos_j    → int  (0-6) tramos de falta justificada
        tramos_ok   → int  (0-6) tramos de asistencia
        gradiente   → str  valor CSS para la propiedad background
        tooltip     → str  descripción corta

    Los días con tipo 'futuro' son días lectivos posteriores a hoy:
    no se computan en tramos ni en porcentajes.
    """
    es_finde   = fecha.weekday() >= 5
    es_festivo = fecha in festivos_set
    en_periodo = fecha in dias_lectivos_set

    if es_finde or es_festivo or not en_periodo:
        etiqueta = ('Festivo'       if es_festivo else
                    'Fin de semana' if es_finde   else 'No lectivo')
        return {
            'tipo': 'no-lectivo', 'tramos_nj': 0,
            'tramos_j': 0, 'tramos_ok': 0,
            'gradiente': '', 'tooltip': etiqueta,
        }

    # Día lectivo en el futuro → se muestra pero no cuenta
    if fecha > hoy:
        return {
            'tipo': 'futuro', 'tramos_nj': 0,
            'tramos_j': 0, 'tramos_ok': 0,
            'gradiente': '', 'tooltip': 'Pendiente',
        }

    falta = faltas_dict.get(fecha)

    if not falta:
        return {
            'tipo': 'lectivo', 'tramos_nj': 0,
            'tramos_j': 0, 'tramos_ok': TRAMOS_DIA,
            'gradiente': _gradiente(0, 0, TRAMOS_DIA),
            'tooltip': 'Asistencia completa',
        }

    # Días completos → convertir a tramos
    nj = (falta.DiaCompletoNoJustificada or 0) * TRAMOS_DIA + (falta.TramosNoJustificados or 0)
    j  = (falta.DiaCompletoJustificada   or 0) * TRAMOS_DIA + (falta.TramosJustificados   or 0)

    # Limitar a TRAMOS_DIA en total
    nj = min(nj, TRAMOS_DIA)
    j  = min(j,  TRAMOS_DIA - nj)
    ok = max(TRAMOS_DIA - nj - j, 0)

    if nj == 0 and j == 0:
        # Registro vacío → asistencia completa
        return {
            'tipo': 'lectivo', 'tramos_nj': 0,
            'tramos_j': 0, 'tramos_ok': TRAMOS_DIA,
            'gradiente': _gradiente(0, 0, TRAMOS_DIA),
            'tooltip': 'Asistencia completa',
        }

    partes = []
    if nj: partes.append(f'{nj} NJ')
    if j:  partes.append(f'{j} J')
    if ok: partes.append(f'{ok} asist.')

    return {
        'tipo': 'lectivo', 'tramos_nj': nj,
        'tramos_j': j, 'tramos_ok': ok,
        'gradiente': _gradiente(nj, j, ok),
        'tooltip': ' | '.join(partes),
    }


def _gradiente(nj, j, ok):
    """
    Construye un linear-gradient de arriba a abajo:
      rojo    (NJ)  →  amarillo (J)  →  verde (OK)
    Cada franja es proporcional al número de tramos.
    """
    total = nj + j + ok
    if total == 0:
        return '#e8e8e4'

    def pct(n, acum):
        return round(n / total * 100, 2), round((n + acum) / total * 100, 2)

    paradas = []
    acum = 0

    if nj:
        ini, fin = pct(nj, acum)
        paradas += [f'#ef4444 {acum:.2f}%', f'#ef4444 {fin:.2f}%']
        acum += nj

    if j:
        ini, fin = pct(j, acum)
        paradas += [f'#facc15 {ini:.2f}%', f'#facc15 {fin:.2f}%']
        acum += j

    if ok:
        ini, _ = pct(ok, acum)
        paradas += [f'#22c55e {ini:.2f}%', '#22c55e 100%']

    return 'linear-gradient(to bottom, ' + ', '.join(paradas) + ')'

def _clasificar_dia(fecha, faltas_dict, dias_lectivos_set, festivos_set):
    """
    Devuelve un dict con la clasificación del día para la plantilla.

    Clases CSS devueltas:
      'no-lectivo'          — fin de semana o festivo
      'lectivo-completo'    — lectivo sin ninguna falta
      'falta-just-parcial'  — faltó < 50 % justificado
      'falta-just-total'    — faltó >= 50 % justificado
      'falta-injust-parcial'— faltó < 50 % injustificado
      'falta-injust-total'  — faltó >= 50 % injustificado
      'falta-mixta-parcial' — mezcla just+injust, total < 50 %
      'falta-mixta-total'   — mezcla just+injust, total >= 50 %
    """
    es_finde   = fecha.weekday() >= 5
    es_festivo = fecha in festivos_set
    en_periodo = fecha in dias_lectivos_set

    if es_finde or es_festivo or not en_periodo:
        return {
            'clase':      'no-lectivo',
            'tooltip':    'Festivo' if es_festivo else ('Fin de semana' if es_finde else 'No lectivo'),
            'tramos_j':   0,
            'tramos_nj':  0,
            'porcentaje': 0,
        }

    falta = faltas_dict.get(fecha)
    if not falta:
        return {
            'clase':      'lectivo-completo',
            'tooltip':    'Asistencia completa',
            'tramos_j':   0,
            'tramos_nj':  0,
            'porcentaje': 0,
        }

    # Calcular tramos totales faltados
    dia_completo_j  = falta.DiaCompletoJustificada   or 0
    dia_completo_nj = falta.DiaCompletoNoJustificada or 0
    tramos_j        = falta.TramosJustificados        or 0
    tramos_nj       = falta.TramosNoJustificados      or 0

    # Día completo cuenta como todos los tramos
    total_j  = (TRAMOS_DIA * dia_completo_j)  + tramos_j
    total_nj = (TRAMOS_DIA * dia_completo_nj) + tramos_nj
    total    = total_j + total_nj

    if total == 0:
        return {
            'clase':      'lectivo-completo',
            'tooltip':    'Asistencia completa',
            'tramos_j':   0,
            'tramos_nj':  0,
            'porcentaje': 0,
        }

    porcentaje = round((total / TRAMOS_DIA) * 100)
    mitad      = total >= (TRAMOS_DIA / 2)  # >= 50 %

    tiene_j  = total_j  > 0
    tiene_nj = total_nj > 0

    if tiene_j and tiene_nj:
        clase = 'falta-mixta-total'   if mitad else 'falta-mixta-parcial'
        desc  = 'justificadas y no justificadas'
    elif tiene_j:
        clase = 'falta-just-total'    if mitad else 'falta-just-parcial'
        desc  = 'justificadas'
    else:
        clase = 'falta-injust-total'  if mitad else 'falta-injust-parcial'
        desc  = 'no justificadas'

    tooltip = f'{total} tramo{"s" if total != 1 else ""} de falta {desc} ({porcentaje} %)'

    return {
        'clase':      clase,
        'tooltip':    tooltip,
        'tramos_j':   total_j,
        'tramos_nj':  total_nj,
        'porcentaje': porcentaje,
    }

def _leyenda():
    return [
        {'clase': 'lectivo-completo',   'etiqueta': 'Asistencia completa'},
        {'clase': 'no-lectivo',         'etiqueta': 'No lectivo / festivo'},
        {'clase': 'falta-just-parcial', 'etiqueta': 'Falta justificada < 50 %'},
        {'clase': 'falta-just-total',   'etiqueta': 'Falta justificada ≥ 50 %'},
        {'clase': 'falta-injust-parcial','etiqueta': 'Falta injustificada < 50 %'},
        {'clase': 'falta-injust-total', 'etiqueta': 'Falta injustificada ≥ 50 %'},
        {'clase': 'falta-mixta-parcial','etiqueta': 'Falta mixta < 50 %'},
        {'clase': 'falta-mixta-total',  'etiqueta': 'Falta mixta ≥ 50 %'},
    ]