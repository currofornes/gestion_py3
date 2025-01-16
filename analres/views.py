from collections import defaultdict
from datetime import datetime, timedelta, date


from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.http import JsonResponse, HttpResponse
from django_weasyprint import WeasyTemplateResponseMixin
from django.views.generic import TemplateView

from centro.views import group_check_je
from centro.models import InfoAlumnos, Centros

from .forms import AnalisisResultados, AnalisisResultadosPorCentros1ESO
from centro.models import Niveles
from centro.utils import get_current_academic_year
from convivencia.models import Amonestaciones, Sanciones
from absentismo.models import ProtocoloAbs

from .indicadores import EstimacionPromocion, EficaciaTransito, EvaluacionPositivaTodo, IdoneidadCursoEdad, \
    AbandonoEscolar, Modalidad, Serie, SerieManual
from.models import Calificaciones, IndicadoresAlumnado


def calcular_resultados_analisis(curso_academico, convocatoria):
    # Obtener todos los niveles de una sola vez
    niveles_dict = {nivel.Abr: nivel for nivel in Niveles.objects.filter(
        Abr__in=[
            "1º ESO", "2º ESO", "3º ESO", "4º ESO",
            "1º BTO CyT", "1º BTO HyCS", "1º BTO", "2º BTO CyT", "2º BTO HyCS", "2º BTO",
            "1º SMR", "2º SMR", "1º ASIR", "2º ASIR"
        ]
    )}

    # Agrupación de niveles para facilitar cálculos
    ESO = [niveles_dict.get(f"{i}º ESO") for i in range(1, 5)]
    BTO_1 = [niveles_dict.get("1º BTO CyT"), niveles_dict.get("1º BTO HyCS")]
    BTO_2 = [niveles_dict.get("2º BTO CyT"), niveles_dict.get("2º BTO HyCS")]
    SMR = [niveles_dict.get("1º SMR"), niveles_dict.get("2º SMR")]
    ASIR = [niveles_dict.get("1º ASIR"), niveles_dict.get("2º ASIR")]

    BTO = [BTO_1, BTO_2]
    FP = []
    FP.extend(SMR)
    FP.extend(ASIR)
    niveles = []
    niveles.extend(ESO)
    niveles.extend(BTO)
    niveles.extend(FP)

    calculos = defaultdict(list)

    for nivel in FP:
        calculos[nivel.Nombre].append(
            {
                'Estimación de la promoción':
                    Serie(
                        curso_academico, 4, convocatoria, [nivel], indicador='EstimacionPromocion',
                        titulo='Estimación de la promoción'
                    )
            }
        )

    for nivel in ESO:
        calculos[nivel.Nombre].append(
            {
                'Estimación de la promoción':
                    Serie(
                        curso_academico, 4, convocatoria, [nivel], indicador='EstimacionPromocion',
                        abandono_cuenta=True,
                        titulo='Estimación de la promoción'
                    )
            }
        )
        if nivel.Nombre == "4º ESO":
            modalidades = ["PDC", "PROF", "ACAD HyCS", "ACAD CyT"]
            calculos['4º ESO'].append(
                {
                    'Estimación de la promoción (por itinerarios)':
                        Serie(
                            curso_academico, 4, convocatoria, [nivel], modalidades=modalidades,
                            indicador='EstimacionPromocion', titulo='Estimación de la promoción (por itinerarios)'
                        )
                }
            )
        if nivel.Nombre == '1º ESO':
            calculos['1º ESO'].append(
                {
                    'Eficacia del tránsito':
                        Serie(
                            curso_academico, 4, convocatoria, [nivel], indicador='EficaciaTransito',
                            abandono_cuenta=True,
                            titulo='Eficacia del tránsito'
                        )
                }
            )
        calculos[nivel.Nombre].append(
            {
                'Alumnado con eval. positiva en todas las materias':
                    Serie(
                        curso_academico, 4, convocatoria, [nivel], indicador='EvaluacionPositivaTodo',
                        abandono_cuenta=True,
                        titulo='Alumnado con eval. positiva en todas las materias'
                    )
            }
        )
        calculos[nivel.Nombre].append(
            {
                'Eficacia de la repetición':
                    Serie(
                        curso_academico, 4, convocatoria, [nivel], indicador='EficaciaRepeticion',
                        abandono_cuenta=True,
                        titulo='Eficacia de la repetición'
                    )
            }
        )

        calculos[nivel.Nombre].append(
            {
                'Idoneidad curso-edad':
                    Serie(
                        curso_academico, 4, convocatoria, [nivel], indicador='IdoneidadCursoEdad',
                        abandono_cuenta=True,
                        titulo='Idoneidad curso-edad'
                    )
            }
        )

        calculos[nivel.Nombre].append(
            {
                'Abandono escolar en ESO':
                    Serie(
                        curso_academico, 4, convocatoria, [nivel], indicador='AbandonoEscolar',
                        titulo='Abandono escolar en ESO'
                    )
            }
        )

    modalidades = ['CyT', 'HyCS']
    for i, nivel in enumerate(BTO):
        calculos[f'{i + 1}º BTO'].append(
            {
                'Estimación de la promoción':
                    Serie(
                        curso_academico, 4, convocatoria, nivel, indicador='EstimacionPromocion',
                        titulo='Estimación de la promoción'
                    )
            }
        )
        calculos[f'{i + 1}º BTO'].append(
            {
                'Estimación de la promoción (por modalidad)':
                    Serie(
                        curso_academico, 4, convocatoria, nivel, modalidades=modalidades,
                        indicador='EstimacionPromocion', titulo='Estimación de la promoción (por modalidad)'
                    )
            }
        )



    resultados = [[nivel, []] for nivel in calculos]

    for calc_nivel in resultados:
        nivel = calc_nivel[0]
        for calculo in calculos[nivel]:
            indicador, serie = list(calculo.items())[0]
            serie.calcular()
            if serie.modalidades:
                resultado = [
                    (curso, [(modalidad, serie.resultados[curso][modalidad]) for modalidad in serie.modalidades]) for
                    curso in serie.cursos]
                calc_nivel[1].append(
                    (
                        indicador,
                        resultado,
                        serie.modalidades,
                        serie.abandono_cuenta,
                        [serie.mu[modalidad] for modalidad in serie.modalidades],
                        [serie.sigma[modalidad] for modalidad in serie.modalidades],
                        # 'grafica'
                        serie.grafica()
                    )
                )
            else:
                resultado = [(curso, serie.resultados[curso]) for curso in serie.cursos]
                calc_nivel[1].append(
                    (
                        indicador,
                        resultado,
                        serie.modalidades,
                        serie.abandono_cuenta,
                        serie.mu,
                        serie.sigma,
                        # 'grafica'
                        serie.grafica()
                    )
                )
    return resultados
@login_required(login_url='/')
@user_passes_test(group_check_je, login_url='/')
def analisis(request):
    if request.method == 'POST':
        form = AnalisisResultados(request.POST, request.FILES)
        if form.is_valid():
            convocatoria = form.cleaned_data['Convocatoria']
            curso_academico_actual = get_current_academic_year()

            resultados = calcular_resultados_analisis(curso_academico_actual, convocatoria)

            context = {
                'form': form,
                'menu_analisis': True,
                'resultados': resultados,
                'descarga': f"/analres/analisis_pdf/?convocatoria={convocatoria}"
            }
        else:
            context = {'form': form, 'menu_analisis': True}
    else:
        form = AnalisisResultados()
        context = {'form': form, 'menu_analisis': True}

    return render(request, 'analisis.html', context)

def obtener_calificaciones(curso_academico, convocatoria):
    calificaciones = Calificaciones.objects.filter(
        curso_academico=curso_academico,
        Convocatoria=convocatoria
    ).all()

    # Crear un diccionario donde la clave es el alumno y el valor es una lista de sus calificaciones
    resultado = defaultdict(list)

    for calificacion in calificaciones:
        resultado[calificacion.Alumno].append(calificacion)

    return resultado

@login_required(login_url='/')
@user_passes_test(group_check_je, login_url='/')
def recalcular_indicadores(request):
    if request.method == 'POST':
        convocatoria = request.POST.get('Convocatoria')
        curso_academico_actual = get_current_academic_year()

        cursos = [curso_academico_actual - i for i in range(4)]
        estimacion_promocion = EstimacionPromocion()
        eficacia_transito = EficaciaTransito()
        eval_positiva_todo = EvaluacionPositivaTodo()
        idoneidad_curso_edad = IdoneidadCursoEdad()
        abandono_escolar = AbandonoEscolar()
        modalidad = Modalidad()

        for curso in cursos:
            # Cargar las calificaciones del alumnado
            calificaciones = obtener_calificaciones(curso, convocatoria)
            for alumno in calificaciones:
                info_alumno = InfoAlumnos.objects.filter(curso_academico=curso, Alumno=alumno).first()
                if not info_alumno:
                    print(f"No se encuentra info adicional de {alumno.Nombre} en {curso}.")
                    continue

                indicadores, _ = IndicadoresAlumnado.objects.get_or_create(
                    curso_academico=curso,
                    Alumno=alumno,
                    Convocatoria=convocatoria,
                    defaults={
                        'EstimacionPromocion': None,
                        'EficaciaTransito': None,
                        'EvaluacionPositivaTodo': None,
                        'EficaciaRepeticion': None,
                        'IdoneidadCursoEdad': None,
                        'AbandonoEscolar': None
                    }
                )
                indicadores.EstimacionPromocion = estimacion_promocion.calcular(calificaciones[alumno], nivel=info_alumno.Nivel)
                if info_alumno.Nivel.Abr == "1º ESO":
                    indicadores.EficaciaTransito = eficacia_transito.calcular(calificaciones[alumno])
                if "ESO" in info_alumno.Nivel.Abr:
                    indicadores.EvaluacionPositivaTodo = eval_positiva_todo.calcular(calificaciones[alumno])
                    if info_alumno.Repetidor:
                        indicadores.EficaciaRepeticion = indicadores.EstimacionPromocion
                    indicadores.IdoneidadCursoEdad = idoneidad_curso_edad.calcular(
                        calificaciones[alumno], nivel=info_alumno.Nivel, edad=info_alumno.Edad)
                    indicadores.AbandonoEscolar = abandono_escolar.calcular(calificaciones[alumno])
                if info_alumno.Nivel.Abr == "4º ESO" or "BTO" in info_alumno.Nivel.Abr:
                    mod = modalidad.calcular(calificaciones[alumno], nivel=info_alumno.Nivel)
                    indicadores.Modalidad = modalidad.calcular(calificaciones[alumno], nivel=info_alumno.Nivel)
                indicadores.save()



        return JsonResponse({'status': 'success'})

@method_decorator(login_required(login_url='/'), name='dispatch')
@method_decorator(user_passes_test(group_check_je, login_url='/'), name='dispatch')
class GenerarPDFView(WeasyTemplateResponseMixin, TemplateView):
    convocatorias = {
        'EVI': 'Evaluación inicial',
        '1EV': '1ª Evaluación',
        '2EV': '2ª Evaluacion',
        '3EV': '3ª Evaluacion',
        'FFP': 'Final FP',
        'Ord': 'Ordinaria',
        'Ext': 'Extraordinaria'
    }
    template_name = 'analisis_pdf.html'
    pdf_stylesheets = [
        # 'static/css/estilo_pdf.css',  # Define tu CSS para dar formato al PDF
        'static/css/bootstrap.min.css'
    ]
    pdf_attachment = False  # Cambiar a False si quieres visualizar el PDF en lugar de descargarlo

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        curso_academico_actual = get_current_academic_year()
        convocatoria = self.request.GET.get('convocatoria')
        resultados = calcular_resultados_analisis(curso_academico_actual, convocatoria)

        context['resultados'] = resultados
        context['curso_academico'] = curso_academico_actual.nombre
        context['convocatoria'] = self.convocatorias[convocatoria]
        return context


def calcular_domingo_de_ramos(anio):
    """
    Calcula la fecha del Domingo de Ramos para un año dado.
    El Domingo de Ramos es el domingo anterior al Domingo de Pascua.

    :param anio: Año en formato entero.
    :return: Fecha del Domingo de Ramos como un objeto datetime.date.
    """
    # Cálculo del Domingo de Pascua utilizando el algoritmo de computus
    a = anio % 19
    b = anio // 100
    c = anio % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mes = (h + l - 7 * m + 114) // 31
    dia = ((h + l - 7 * m + 114) % 31) + 1

    # Fecha del Domingo de Pascua
    domingo_pascua = date(anio, mes, dia)

    # Fecha del Domingo de Ramos (una semana antes)
    domingo_ramos = domingo_pascua - timedelta(days=7)
    return domingo_ramos


def calcular_amonestaciones_1_ESO_por_centro(curso_academico, convocatoria, centro):
    if convocatoria == "1EV":
        fecha_inicio = datetime.strptime(f'01/09/{curso_academico.año_inicio}', '%d/%m/%Y')
        fecha_fin = datetime.strptime(f'23/12/{curso_academico.año_inicio}', '%d/%m/%Y')
    elif convocatoria == "2EV":
        fecha_inicio = datetime.strptime(f'07/01/{curso_academico.año_fin}', '%d/%m/%Y')
        fecha_fin = calcular_domingo_de_ramos(curso_academico.año_fin)
    else:
        fecha_inicio = calcular_domingo_de_ramos(curso_academico.año_fin)
        fecha_fin = datetime.strptime(f'30/06/{curso_academico.año_fin}', '%d/%m/%Y')

    datos = Amonestaciones.objects.filter(
        curso_academico=curso_academico,
        Fecha__range=(fecha_inicio, fecha_fin),
        IdAlumno__info_adicional__Nivel__Abr="1º ESO",
        IdAlumno__info_adicional__curso_academico=curso_academico,
    )

    total = datos.count()
    parte = datos.filter(
        IdAlumno__info_adicional__CentroOrigen=centro
    ).count()

    if total > 0:
        return 100 * parte / total
    else:
        return 0

def calcular_sanciones_1_ESO_por_centro(curso_academico, convocatoria, centro):
    if convocatoria == "1EV":
        fecha_inicio = datetime.strptime(f'01/09/{curso_academico.año_inicio}', '%d/%m/%Y')
        fecha_fin = datetime.strptime(f'23/12/{curso_academico.año_inicio}', '%d/%m/%Y')
    elif convocatoria == "2EV":
        fecha_inicio = datetime.strptime(f'07/01/{curso_academico.año_fin}', '%d/%m/%Y')
        fecha_fin = calcular_domingo_de_ramos(curso_academico.año_fin)
    else:
        fecha_inicio = calcular_domingo_de_ramos(curso_academico.año_fin)
        fecha_fin = datetime.strptime(f'30/06/{curso_academico.año_fin}', '%d/%m/%Y')

    datos = Sanciones.objects.filter(
        curso_academico=curso_academico,
        Fecha__range=(fecha_inicio, fecha_fin),
        IdAlumno__info_adicional__Nivel__Abr="1º ESO",
        IdAlumno__info_adicional__curso_academico=curso_academico,
    )

    total = datos.count()
    parte = datos.filter(
        IdAlumno__info_adicional__CentroOrigen=centro
    ).count()

    if total > 0:
        return 100 * parte / total
    else:
        return 0

def calcular_absentismo_1_ESO_por_centro(curso_academico, convocatoria, centro):
    if convocatoria == "1EV":
        fecha_inicio = datetime.strptime(f'01/09/{curso_academico.año_inicio}', '%d/%m/%Y')
        fecha_fin = datetime.strptime(f'23/12/{curso_academico.año_inicio}', '%d/%m/%Y')
    elif convocatoria == "2EV":
        fecha_inicio = datetime.strptime(f'07/01/{curso_academico.año_fin}', '%d/%m/%Y')
        fecha_fin = calcular_domingo_de_ramos(curso_academico.año_fin)
    else:
        fecha_inicio = calcular_domingo_de_ramos(curso_academico.año_fin)
        fecha_fin = datetime.strptime(f'30/06/{curso_academico.año_fin}', '%d/%m/%Y')

    datos = ProtocoloAbs.objects.filter(
        curso_academico=curso_academico,
        abierto=True,
        alumno__info_adicional__Nivel__Abr="1º ESO",
        alumno__info_adicional__curso_academico=curso_academico,
        fecha_apertura__range=(fecha_inicio, fecha_fin),
    )


    total = datos.count()

    parte = datos.filter(
        alumno__info_adicional__CentroOrigen=centro
    ).count()

    print(centro.Nombre, parte, total)

    if total > 0:
        return 100 * parte / total
    else:
        return 0

def calcular_indicador_1_ESO_por_centro(curso_academico, convocatoria, indicador, centro=None):
    if centro:
        datos = IndicadoresAlumnado.objects.filter(
            curso_academico=curso_academico,
            Convocatoria=convocatoria,
            Alumno__info_adicional__curso_academico=curso_academico,
            Alumno__info_adicional__Nivel__Abr="1º ESO",
            Alumno__info_adicional__CentroOrigen=centro
        )
    else:
        datos = IndicadoresAlumnado.objects.filter(
            curso_academico=curso_academico,
            Convocatoria=convocatoria,
            Alumno__info_adicional__curso_academico=curso_academico,
            Alumno__info_adicional__Nivel__Abr="1º ESO",
        )

    datos.exclude(**{indicador: None})
    total = datos.count()
    parte = datos.filter(**{indicador: True}).count()

    if total > 0:
        return 100 * parte / total
    else:
        return 0

def calcular_resultados_analisis_1_ESO_por_centros(curso_academico, convocatoria, centros):
    ESO_1 = Niveles.objects.filter(Abr="1º ESO")
    indicadores = [
        'EstimacionPromocion',
        'EficaciaTransito',
        'EvaluacionPositivaTodo',
        'AbandonoEscolar',
    ]
    titulos = {
        'EstimacionPromocion': 'Estimación de la promoción',
        'EficaciaTransito': 'Eficacia del tránsito',
        'EvaluacionPositivaTodo': 'Evaluación positiva en todas las materias',
        'AbandonoEscolar': 'Abandono Escolar',
    }
    calculos = {
        indicador: {
            centro.Nombre: calcular_indicador_1_ESO_por_centro(
                curso_academico, convocatoria, indicador, centro
            ) for centro in centros
        } for indicador in indicadores
    }

    for indicador in indicadores:
        calculos[indicador]['IES Gonzalo Nazareno'] = calcular_indicador_1_ESO_por_centro(
            curso_academico, convocatoria, indicador
        )

    nombres_centro = [centro.Nombre for centro in centros]

    series = {
        indicador: SerieManual(
            nombres_centro, calculos[indicador], calculos[indicador]['IES Gonzalo Nazareno'], titulos[indicador]
        ) for indicador in indicadores
    }

    indicadores.append('Amonestaciones')
    titulos['Amonestaciones'] = 'Amonestaciones (%)'
    calculos['Amonestaciones'] = {
        centro.Nombre: calcular_amonestaciones_1_ESO_por_centro(curso_academico, convocatoria, centro)
        for centro in centros
    }

    series['Amonestaciones'] = SerieManual(
        nombres_centro, calculos['Amonestaciones'], None, titulos['Amonestaciones']
    )

    indicadores.append('Sanciones')
    titulos['Sanciones'] = 'Sanciones (%)'
    calculos['Sanciones'] = {
        centro.Nombre: calcular_sanciones_1_ESO_por_centro(curso_academico, convocatoria, centro)
        for centro in centros
    }

    series['Sanciones'] = SerieManual(
        nombres_centro, calculos['Sanciones'], None, titulos['Sanciones']
    )

    indicadores.append('Absentismo')
    titulos['Absentismo'] = 'Casos de absentismo %'
    calculos['Absentismo'] = {
        centro.Nombre: calcular_absentismo_1_ESO_por_centro(curso_academico, convocatoria, centro)
        for centro in centros
    }

    series['Absentismo'] = SerieManual(
        nombres_centro, calculos['Absentismo'], None, titulos['Absentismo']
    )

    resultados = [(titulos[indicador], list(series[indicador].valores.items()), series[indicador].grafica()) for indicador in indicadores]
    return resultados

@login_required(login_url='/')
@user_passes_test(group_check_je, login_url='/')
def analisis_por_centros_1_ESO(request):
    if request.method == 'POST':
        form = AnalisisResultadosPorCentros1ESO(request.POST)

        if form.is_valid():
            curso_academico_actual = get_current_academic_year()
            convocatoria = form.cleaned_data['Convocatoria']
            centros_id = form.cleaned_data['Centros']
            centros = [Centros.objects.get(id=i) for i in centros_id]
            resultados = calcular_resultados_analisis_1_ESO_por_centros(curso_academico_actual, convocatoria, centros)
            centros_ids = ",".join(centros_id)
            context = {
                'form': form,
                'resultados': resultados,
                'descarga': f"/analres/analisis_1ESO_pdf/?convocatoria={convocatoria}&centros={centros_ids}",
                'menu_analisis': True}
    else:
        form = AnalisisResultadosPorCentros1ESO()
        context = {'form': form, 'menu_analisis': True}

    return render(request, 'analisis_por_centros_1_ESO.html', context)

@method_decorator(login_required(login_url='/'), name='dispatch')
@method_decorator(user_passes_test(group_check_je, login_url='/'), name='dispatch')
class GenerarPDF1ESOView(WeasyTemplateResponseMixin, TemplateView):
    convocatorias = {
        '1EV': '1ª Evaluación',
        '2EV': '2ª Evaluacion',
        'Ord': 'Ordinaria',
    }
    template_name = 'analisis_1ESO_pdf.html'
    pdf_stylesheets = [
        # 'static/css/estilo_pdf.css',  # Define tu CSS para dar formato al PDF
        'static/css/bootstrap.min.css'
    ]
    pdf_attachment = False  # Cambiar a False si quieres visualizar el PDF en lugar de descargarlo

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        curso_academico_actual = get_current_academic_year()
        convocatoria = self.request.GET.get('convocatoria')
        centros_ids = self.request.GET.get('centros')
        centros_id = [int(i) for i in centros_ids.split(',')]
        centros = [Centros.objects.get(id=int(i)) for i in centros_id]
        resultados = calcular_resultados_analisis_1_ESO_por_centros(curso_academico_actual, convocatoria, centros)

        context['resultados'] = resultados
        context['curso_academico'] = curso_academico_actual.nombre
        context['convocatoria'] = self.convocatorias[convocatoria]
        return context
