from django.shortcuts import render, redirect, get_object_or_404

from centro.utils import get_current_academic_year, get_previous_academic_years
from convivencia.forms import AmonestacionForm, SancionForm, FechasForm, AmonestacionProfeForm, ResumenForm
from centro.models import Alumnos, Profesores, Niveles, CursoAcademico
from centro.views import group_check_je, group_check_prof
from convivencia.models import Amonestaciones, Sanciones, TiposAmonestaciones
from centro.models import Cursos
from django.contrib.auth.decorators import login_required, user_passes_test
import time, calendar
from datetime import datetime, date
from operator import itemgetter
from django.db.models import Count
from django.template.loader import get_template
from django.shortcuts import render
from django.template import Context
from django.core.mail import send_mail


# Create your views here.


# Curro Jul 24: Modifico para que solo pueda usarse por JE
@login_required(login_url='/')
@user_passes_test(group_check_je, login_url='/')
def parte(request, tipo, alum_id):
    alum = Alumnos.objects.get(pk=alum_id)
    # if request.user.username[:5]=="tutor" and alum.Unidad.Abe!=request.user.username[5:]:
    #	return redirect("/")
    if request.method == 'POST':
        if tipo == "amonestacion":
            form = AmonestacionForm(request.POST)
            titulo = "Amonestaciones"
        elif tipo == "sancion":
            form = SancionForm(request.POST)
            titulo = "Sanciones"
        else:
            return redirect("/")

        if form.is_valid():
            form.save()

            if tipo == "amonestacion":
                amon = form.instance
                destinatarios = [amon.Profesor, amon.IdAlumno.Unidad.Tutor]

                template = get_template("correo_amonestacion.html")
                contenido = template.render({'amon': amon})

                # Comunica la amonestación a la familia
                correo_familia = amon.IdAlumno.email
                if correo_familia:
                    template = get_template("correo_amonestacion.html")
                    contenido = template.render({'amon': amon})

            # send_mail(
            #	'Nueva amonestación',
            #	contenido,
            #	'41011038.jestudios.edu@juntadeandalucia.es',
            #	(correo_familia,),
            #	fail_silently=False
            # )

            if tipo == "sancion":
                sanc = form.instance
                destinatarios = list(sanc.IdAlumno.Unidad.EquipoEducativo.all())
                destinatarios.append(sanc.IdAlumno.Unidad.Tutor)
                template = get_template("correo_sancion.html")
                contenido = template.render({'sanc': sanc})

            correos = []
            for prof in destinatarios:
                correo = Profesores.objects.get(id=prof.id).Email
                if correo != "":
                    correos.append(correo)
            # send_mail(
            #    new_correo.Asunto,
            #    new_correo.Contenido,
            #    '41011038.jestudios.edu@juntadeandalucia.es',
            #    correos,
            #    fail_silently=False,
            #   )
            return redirect('/centro/alumnos')
    else:
        if tipo == "amonestacion":
            form = AmonestacionForm({'IdAlumno': alum.id, 'Fecha': time.strftime("%d/%m/%Y"), 'Hora': 1, 'Profesor': 1})

            titulo = "Amonestaciones"
        elif tipo == "sancion":
            form = SancionForm(
                {'IdAlumno': alum.id, 'Fecha': time.strftime("%d/%m/%Y"), 'Fecha_fin': time.strftime("%d/%m/%Y"),
                 'Profesor': 1})
            titulo = "Sanciones"
        else:
            return redirect("/")
    context = {'alum': alum, 'form': form, 'titulo': titulo, 'tipo': tipo, 'menu_convivencia': True}
    return render(request, 'parte.html', context)


@login_required(login_url='/')
@user_passes_test(group_check_prof, login_url='/')
def historial(request, alum_id, prof):
    horas = ["1ª hora", "2ª hora", "3ª hora", "Recreo", "4ª hora", "5ª hora", "6ª hora"]
    alum = Alumnos.objects.get(pk=alum_id)

    if request.user.username[:5] == "tutor" and alum.Unidad.Abe != request.user.username[5:]:
        return redirect("/")

    curso_academico_actual = get_current_academic_year()

    # Filtrar las amonestaciones y sanciones del curso académico actual
    amon_actual = Amonestaciones.objects.filter(IdAlumno_id=alum_id, curso_academico=curso_academico_actual).order_by(
        'Fecha')
    sanc_actual = Sanciones.objects.filter(IdAlumno_id=alum_id, curso_academico=curso_academico_actual).order_by(
        'Fecha')

    historial_actual = list(amon_actual) + list(sanc_actual)
    historial_actual = sorted(historial_actual, key=lambda x: x.Fecha, reverse=False)

    tipo_actual = ["Amonestación" if isinstance(h, Amonestaciones) else "Sanción" for h in historial_actual]
    hist_actual = zip(historial_actual, tipo_actual, range(1, len(historial_actual) + 1))

    # Filtrar las amonestaciones y sanciones de cursos anteriores
    cursos_anteriores = get_previous_academic_years()
    historial_anteriores = {}

    for curso in cursos_anteriores:
        amon_anteriores = Amonestaciones.objects.filter(IdAlumno_id=alum_id, curso_academico=curso).order_by('Fecha')
        sanc_anteriores = Sanciones.objects.filter(IdAlumno_id=alum_id, curso_academico=curso).order_by('Fecha')

        historial_curso = list(amon_anteriores) + list(sanc_anteriores)
        historial_curso = sorted(historial_curso, key=lambda x: x.Fecha, reverse=False)

        tipo_anteriores = ["Amonestación" if isinstance(h, Amonestaciones) else "Sanción" for h in historial_curso]
        hist_anteriores = list(zip(historial_curso, tipo_anteriores, range(1, len(historial_curso) + 1)))

        if hist_anteriores:
            historial_anteriores[curso] = hist_anteriores

    prof = True if prof == "" else False

    context = {
        'prof': prof,
        'alum': alum,
        'historial_actual': hist_actual,
        'historial_anteriores': historial_anteriores,
        'menu_convivencia': True,
        'horas': horas
    }
    return render(request, 'historial.html', context)


@login_required(login_url='/')
@user_passes_test(group_check_je, login_url='/')
def resumen_hoy(request, tipo):
    hoy = datetime.now()
    return resumen(request, tipo, str(hoy.month), str(hoy.year))


@login_required(login_url='/')
@user_passes_test(group_check_je, login_url='/')
def resumen(request, tipo=None, fecha=None):
    if request.method == 'POST':
        tipo = request.POST.get('tipo')
        fecha = request.POST.get('fecha')
        form = ResumenForm(request.POST)
        if form.is_valid():
            # Procesar los datos del formulario aquí si es necesario
            pass
    else:
        # Valores predeterminados para GET
        tipo = tipo if tipo else 'amonestacion'
        hoy = datetime.now()
        # Formatear la fecha
        fecha_formateada = hoy.strftime('%d-%m-%Y')
        # Redirigir a POST con valores predeterminados solo si es GET
        if not fecha:
            return redirect('resumen_con_parametros', tipo=tipo, fecha=fecha_formateada)

        form = ResumenForm(initial={'tipo': tipo, 'fecha': hoy})

    context = {'form': form, 'tipo': tipo, 'fecha': fecha}
    return render(request, 'resumen.html', context)

    '''

    c = calendar.HTMLCalendar(calendar.MONDAY)
    calhtml=c.formatmonth(int(ano),int(mes))

    if tipo=="amonestacion":
        datos=Amonestaciones.objects.filter(Fecha__year=ano).filter(Fecha__month=mes)
        titulo="Resumen de amonestaciones"
    if tipo=="sancion":
        datos=Sanciones.objects.filter(Fecha__year=ano).filter(Fecha__month=mes)
        titulo="Resumen de sanciones"
    
    ult_dia=calendar.monthrange(int(ano),int(mes))[1]
    dic_fechas=datos.values("Fecha")
    fechas=[]
    for f in dic_fechas:
        fechas.append(f["Fecha"])

    for dia in range(1,int(ult_dia)+1):
        fecha=datetime(int(ano),int(mes),dia)
        if fecha.date() in fechas:
            calhtml=calhtml.replace(">"+str(dia)+"<",'><a href="/convivencia/show/%s/%s/%s/%s"><strong>%s</strong></a><'%(tipo,mes,ano,dia,dia))
    calhtml=calhtml.replace('class="month"','class="table-condensed table-bordered table-striped"')
    
    
    mes_actual=datetime(int(ano),int(mes),1)
    mes_ant=AddMonths(mes_actual,-1)
    mes_prox=AddMonths(mes_actual,1)

    context={'calhtml':calhtml,'fechas':[mes_actual,mes_ant,mes_prox],'titulo':titulo,'tipo':tipo,'menu_resumen':True}
    return render(request, 'resumen.html',context)
    '''


def AddMonths(d, x):
    newmonth = (((d.month - 1) + x) % 12) + 1
    newyear = int(d.year + (((d.month - 1) + x) / 12))
    return datetime(newyear, newmonth, d.day)


@login_required(login_url='/')
@user_passes_test(group_check_je, login_url='/')
def show(request, tipo=None, mes=None, ano=None, dia=None):
    if request.method == 'POST':
        fecha = request.POST.get('fecha')
        tipo = request.POST.get('tipo')
        dia, mes, ano = fecha.split('/')
        return redirect('show', tipo=tipo, mes=mes, ano=ano, dia=dia)

    if tipo is None or mes is None or ano is None or dia is None:
        # Establecer valores predeterminados
        tipo = tipo if tipo else 'amonestacion'
        hoy = datetime.now()
        mes = mes if mes else hoy.month
        ano = ano if ano else hoy.year
        dia = dia if dia else hoy.day
        return redirect('show', tipo=tipo, mes=mes, ano=ano, dia=dia)

    fecha = datetime(int(ano), int(mes), int(dia))

    if tipo == "amonestacion":
        datos = Amonestaciones.objects.filter(Fecha=fecha)
        titulo = "Resumen de amonestaciones"
    if tipo == "sancion":
        datos = Sanciones.objects.filter(Fecha=fecha)
        titulo = "Resumen de sanciones"

    form = ResumenForm(initial={'fecha': fecha, 'tipo': tipo})

    datos = zip(range(1, len(datos) + 1), datos, ContarFaltas(datos.values("IdAlumno")))
    context = {
        'form': form,
        'datos': datos,
        'tipo': tipo,
        'mes': mes,
        'ano': ano,
        'dia': dia,
        'titulo': titulo,
        f'menu_{tipo}': True,
        'menu_convivencia': True,

    }
    context[tipo] = True
    return render(request, 'show.html', context)


@login_required(login_url='/')
@user_passes_test(group_check_je, login_url='/')
def estadisticas(request):
    # Obtener todos los cursos académicos
    cursos_academicos = CursoAcademico.objects.order_by('nombre')

    # Determinar el curso académico seleccionado
    curso_academico_id = request.GET.get('curso_academico')
    if curso_academico_id:
        curso_seleccionado = get_object_or_404(CursoAcademico, id=curso_academico_id)
    else:
        curso_seleccionado = get_current_academic_year()

    # Por defecto, mostrar el curso académico actual si no se selecciona uno
    if not curso_seleccionado:
        curso_seleccionado = get_current_academic_year()

    if request.method == "POST":

        # f1=datetime(int(request.POST.get('Fecha1_year')),int(request.POST.get('Fecha1_month')),int(request.POST.get('Fecha1_day')))
        # f2=datetime(int(request.POST.get('Fecha2_year')),int(request.POST.get('Fecha2_month')),int(request.POST.get('Fecha2_day')))
        f1 = datetime.strptime(request.POST.get('Fecha1'), '%d/%m/%Y')
        f2 = datetime.strptime(request.POST.get('Fecha2'), '%d/%m/%Y')

        a3t = Amonestaciones.objects.filter(Fecha__gte=f1, Fecha__lte=f2, curso_academico=curso_seleccionado).count()
        al3t = Amonestaciones.objects.filter(Fecha__gte=f1, Fecha__lte=f2, curso_academico=curso_seleccionado,
                                             Tipo__TipoFalta="L").count()
        ag3t = Amonestaciones.objects.filter(Fecha__gte=f1, Fecha__lte=f2, curso_academico=curso_seleccionado,
                                             Tipo__TipoFalta="G").count()
        s3t = Sanciones.objects.filter(Fecha__gte=f1, Fecha__lte=f2, curso_academico=curso_seleccionado).count()
        sne3t = Sanciones.objects.filter(Fecha__gte=f1, Fecha__lte=f2, curso_academico=curso_seleccionado,
                                         NoExpulsion=True).count()

        datos1t = a3t, al3t, ag3t, s3t, sne3t
        datos2t = a3t, al3t, ag3t, s3t, sne3t
        datos3t = a3t, al3t, ag3t, s3t, sne3t

        form = FechasForm(request.POST, curso_academico=curso_seleccionado)
        fechas = [f1, f2]
        total = ()

        tipos = []
        for i in TiposAmonestaciones.objects.all():
            tipos.append((i.TipoAmonestacion,
                          Amonestaciones.objects.filter(Fecha__gte=f1, Fecha__lte=f2,
                                                        curso_academico=curso_seleccionado,
                                                        Tipo=i).count(),
                          i.TipoFalta
                          ))
        filtro = True
    else:
        # Valores por defecto
        year1 = curso_seleccionado.año_inicio
        fi1 = datetime(year1, 9, 1)
        ff1 = datetime(year1, 12, 31)
        fi2 = datetime(year1 + 1, 1, 1)
        ff2 = datetime(year1 + 1, 3, 31)
        fi3 = datetime(year1 + 1, 4, 1)
        ff3 = datetime(year1 + 1, 6, 30)

        # Numeros 1er trimestre

        a1t = Amonestaciones.objects.filter(Fecha__gte=fi1, Fecha__lte=ff1,
                                            curso_academico=curso_seleccionado).count()
        al1t = Amonestaciones.objects.filter(Fecha__gte=fi1, Fecha__lte=ff1, curso_academico=curso_seleccionado,
                                             Tipo__TipoFalta="L").count()
        ag1t = Amonestaciones.objects.filter(Fecha__gte=fi1, Fecha__lte=ff1, curso_academico=curso_seleccionado,
                                             Tipo__TipoFalta="G").count()
        s1t = Sanciones.objects.filter(Fecha__gte=fi1, Fecha__lte=ff1, curso_academico=curso_seleccionado).count()
        sne1t = Sanciones.objects.filter(Fecha__gte=fi1, Fecha__lte=ff1, curso_academico=curso_seleccionado,
                                         NoExpulsion=True).count()

        datos1t = a1t, al1t, ag1t, s1t, sne1t

        # Numeros 2do trimestre

        a2t = Amonestaciones.objects.filter(Fecha__gte=fi2, Fecha__lte=ff2,
                                            curso_academico=curso_seleccionado).count()
        al2t = Amonestaciones.objects.filter(Fecha__gte=fi2, Fecha__lte=ff2, curso_academico=curso_seleccionado,
                                             Tipo__TipoFalta="L").count()
        ag2t = Amonestaciones.objects.filter(Fecha__gte=fi2, Fecha__lte=ff2, curso_academico=curso_seleccionado,
                                             Tipo__TipoFalta="G").count()
        s2t = Sanciones.objects.filter(Fecha__gte=fi2, Fecha__lte=ff2, curso_academico=curso_seleccionado).count()
        sne2t = Sanciones.objects.filter(Fecha__gte=fi2, Fecha__lte=ff2, curso_academico=curso_seleccionado,
                                         NoExpulsion=True).count()

        datos2t = a2t, al2t, ag2t, s2t, sne2t

        # Numeros 3er trimestre

        a3t = Amonestaciones.objects.filter(Fecha__gte=fi3, Fecha__lte=ff3,
                                            curso_academico=curso_seleccionado).count()
        al3t = Amonestaciones.objects.filter(Fecha__gte=fi3, Fecha__lte=ff3, curso_academico=curso_seleccionado,
                                             Tipo__TipoFalta="L").count()
        ag3t = Amonestaciones.objects.filter(Fecha__gte=fi3, Fecha__lte=ff3, curso_academico=curso_seleccionado,
                                             Tipo__TipoFalta="G").count()
        s3t = Sanciones.objects.filter(Fecha__gte=fi3, Fecha__lte=ff3, curso_academico=curso_seleccionado).count()
        sne3t = Sanciones.objects.filter(Fecha__gte=fi3, Fecha__lte=ff3, curso_academico=curso_seleccionado,
                                         NoExpulsion=True).count()

        datos3t = a3t, al3t, ag3t, s3t, sne3t

        form = FechasForm(curso_academico=curso_seleccionado)
        fechas = [fi1, ff3]
        total = Amonestaciones.objects.filter(curso_academico=curso_seleccionado).count(), Sanciones.objects.filter(
            curso_academico=curso_seleccionado).count(), Sanciones.objects.filter(
            curso_academico=curso_seleccionado, NoExpulsion=True).count()
        filtro = False

        # Tipos de amonestaciones
        tipos = []
        for i in TiposAmonestaciones.objects.all():
            tipos.append((
                i.TipoAmonestacion,
                Amonestaciones.objects.filter(Fecha__gte=fi1, Fecha__lte=ff1, curso_academico=curso_seleccionado,
                                              Tipo=i).count(),
                Amonestaciones.objects.filter(Fecha__gte=fi2, Fecha__lte=ff2, curso_academico=curso_seleccionado,
                                              Tipo=i).count(),
                Amonestaciones.objects.filter(Fecha__gte=fi3, Fecha__lte=ff3, curso_academico=curso_seleccionado,
                                              Tipo=i).count(),
                i.TipoFalta
            ))

    context = {'filtro': filtro, 'curso_seleccionado': curso_seleccionado,
               'cursos_academicos': cursos_academicos, 'tipos': tipos, 'total': total, 'form': form, 'datos1t': datos1t,
               'datos2t': datos2t,
               'datos3t': datos3t, 'fechas': fechas, 'menu_estadistica': True}

    return render(request, 'estadisticas.html', context)


@login_required(login_url='/')
@user_passes_test(group_check_je, login_url='/')
def estadisticas2(request, curso):
    if request.method == "POST":

        pass
    else:
        year1 = int(curso) - 1
        fi1 = datetime(year1, 9, 1)
        ff1 = datetime(year1, 12, 31)
        fi2 = datetime(year1 + 1, 1, 1)
        ff2 = datetime(year1 + 1, 3, 31)
        fi3 = datetime(year1 + 1, 4, 1)
        ff3 = datetime(year1 + 1, 6, 30)

        a1t = Amonestaciones.objects.using('db%s' % curso).filter(Fecha__gte=fi1).filter(Fecha__lte=ff1).count()
        a2t = Amonestaciones.objects.using('db%s' % curso).filter(Fecha__gte=fi2).filter(Fecha__lte=ff2).count()
        a3t = Amonestaciones.objects.using('db%s' % curso).filter(Fecha__gte=fi3).filter(Fecha__lte=ff3).count()
        s1t = Sanciones.objects.using('db%s' % curso).filter(Fecha__gte=fi1).filter(Fecha__lte=ff1).count()
        s2t = Sanciones.objects.using('db%s' % curso).filter(Fecha__gte=fi2).filter(Fecha__lte=ff2).count()
        s3t = Sanciones.objects.using('db%s' % curso).filter(Fecha__gte=fi3).filter(Fecha__lte=ff3).count()
        datos = a1t, s1t, a2t, s2t, a3t, s3t
        form = FechasForm()
        fechas = [fi1, ff3]
        total = Amonestaciones.objects.using('db%s' % curso).count(), Sanciones.objects.using('db%s' % curso).count()
        filtro = False

        # Tipos de amonestaciones
        tipos = []
        for i in TiposAmonestaciones.objects.using('db%s' % curso).all():
            tipos.append((i.TipoAmonestacion,
                          Amonestaciones.objects.using('db%s' % curso).filter(Fecha__gte=fi1).filter(
                              Fecha__lte=ff1).filter(Tipo=i).count(),
                          Amonestaciones.objects.using('db%s' % curso).filter(Fecha__gte=fi2).filter(
                              Fecha__lte=ff2).filter(Tipo=i).count(),
                          Amonestaciones.objects.using('db%s' % curso).filter(Fecha__gte=fi3).filter(
                              Fecha__lte=ff3).filter(Tipo=i).count(),
                          ))

    context = {'curso': str(int(curso) - 1) + "/" + curso, 'filtro': filtro, 'tipos': tipos, 'total': total,
               'form': form, 'datos': datos, 'fechas': fechas, 'menu_estadistica': True}
    return render(request, 'estadisticas2.html', context)


@login_required(login_url='/')
@user_passes_test(group_check_je, login_url='/')
def horas(request):
    # Obtener todos los cursos académicos
    cursos_academicos = CursoAcademico.objects.order_by('nombre')

    # Determinar el curso académico seleccionado
    curso_academico_id = request.GET.get('curso_academico')
    if curso_academico_id:
        curso_seleccionado = get_object_or_404(CursoAcademico, id=curso_academico_id)
    else:
        curso_seleccionado = get_current_academic_year()

    # Por defecto, mostrar el curso académico actual si no se selecciona uno
    if not curso_seleccionado:
        curso_seleccionado = get_current_academic_year()

    if request.method == "POST":
        f1 = datetime.strptime(request.POST.get('Fecha1'), '%d/%m/%Y')
        f2 = datetime.strptime(request.POST.get('Fecha2'), '%d/%m/%Y')

    lista = []
    horas = ["[1ª] Primera", "[2ª] Segunda", "[3ª] Tercera", "Recreo", "[4ª] Cuarta", "[5ª] Quinta", "[6ª] Sexta"]
    for i in range(1, 8):
        if request.method == "POST":
            lista.append(Amonestaciones.objects.filter(Hora=i, Fecha__gte=f1, Fecha__lte=f2,
                                                       curso_academico=curso_seleccionado).count())
        else:
            lista.append(Amonestaciones.objects.filter(Hora=i, curso_academico=curso_seleccionado).count())
    form = FechasForm(request.POST, curso_academico=curso_seleccionado) if request.method == "POST" else FechasForm(
        curso_academico=curso_seleccionado)
    horas.append("TOTAL")
    if request.method == "POST":
        lista.append(
            Amonestaciones.objects.filter(Fecha__gte=f1, Fecha__lte=f2, curso_academico=curso_seleccionado).count())
    else:
        lista.append(Amonestaciones.objects.filter(curso_academico=curso_seleccionado).count())

    context = {'form': form, 'horas': zip(horas, lista), 'curso_seleccionado': curso_seleccionado,
               'cursos_academicos': cursos_academicos, 'totales': lista, 'menu_estadistica': True}
    return render(request, 'horas.html', context)


@login_required(login_url='/')
@user_passes_test(group_check_je, login_url='/')
def profesores(request):
    # Obtener todos los cursos académicos
    cursos_academicos = CursoAcademico.objects.order_by('nombre')

    # Determinar el curso académico seleccionado
    curso_academico_id = request.GET.get('curso_academico')
    if curso_academico_id:
        curso_seleccionado = get_object_or_404(CursoAcademico, id=curso_academico_id)
    else:
        curso_seleccionado = get_current_academic_year()

    # Por defecto, mostrar el curso académico actual si no se selecciona uno
    if not curso_seleccionado:
        curso_seleccionado = get_current_academic_year()

    if request.method == "POST":
        f1 = datetime.strptime(request.POST.get('Fecha1'), '%d/%m/%Y')
        f2 = datetime.strptime(request.POST.get('Fecha2'), '%d/%m/%Y')
    lista = []
    if request.method == "POST":
        listAmon = Amonestaciones.objects.values('Profesor').filter(Fecha__gte=f1, Fecha__lte=f2,
                                                                    curso_academico=curso_seleccionado).annotate(
            Count('Profesor'))
    else:
        listAmon = Amonestaciones.objects.values('Profesor').filter(curso_academico=curso_seleccionado).annotate(
            Count('Profesor'))
    newlist = sorted(listAmon, key=itemgetter('Profesor__count'), reverse=True)
    suma = 0
    for l in newlist:
        l["Profesor"] = Profesores.objects.get(id=l["Profesor"]).Apellidos + ", " + Profesores.objects.get(
            id=l["Profesor"]).Nombre
        suma += l["Profesor__count"]
    form = FechasForm(request.POST, curso_academico=curso_seleccionado) if request.method == "POST" else FechasForm(
        curso_academico=curso_seleccionado)
    context = {"form": form, "lista": newlist, 'menu_estadistica': True, "suma": suma,
               'curso_seleccionado': curso_seleccionado,
               'cursos_academicos': cursos_academicos}
    return render(request, 'lprofesores.html', context)


@login_required(login_url='/')
@user_passes_test(group_check_je, login_url='/')
def grupos(request):
    cursos_queryset = Cursos.objects.order_by('Curso')
    cursos_nombres = []

    # Obtener todos los cursos académicos
    cursos_academicos = CursoAcademico.objects.order_by('nombre')

    # Determinar el curso académico seleccionado
    curso_academico_id = request.GET.get('curso_academico')
    if curso_academico_id:
        curso_seleccionado = get_object_or_404(CursoAcademico, id=curso_academico_id)
    else:
        curso_seleccionado = get_current_academic_year()

    # Por defecto, mostrar el curso académico actual si no se selecciona uno
    if not curso_seleccionado:
        curso_seleccionado = get_current_academic_year()

    if request.method == "POST":
        f1 = datetime.strptime(request.POST.get('Fecha1'), '%d/%m/%Y')
        f2 = datetime.strptime(request.POST.get('Fecha2'), '%d/%m/%Y')

    # Total
    total = []
    if request.method == "POST":
        total.append(
            Amonestaciones.objects.filter(Fecha__gte=f1, Fecha__lte=f2, curso_academico=curso_seleccionado).count())
        total.append(Sanciones.objects.filter(Fecha__gte=f1, Fecha__lte=f2, curso_academico=curso_seleccionado).count())
    else:
        total.append(Amonestaciones.objects.filter(curso_academico=curso_seleccionado).count())
        total.append(Sanciones.objects.filter(curso_academico=curso_seleccionado).count())

    lista = []

    for curso in cursos_queryset:

        if request.method == "POST":
            datos = [Amonestaciones.objects.filter(IdAlumno__in=Alumnos.objects.filter(Unidad=curso)).filter(
                Fecha__gte=f1, Fecha__lte=f2, curso_academico=curso_seleccionado).count(),
                     Sanciones.objects.filter(IdAlumno__in=Alumnos.objects.filter(Unidad=curso)).filter(
                         Fecha__gte=f1, Fecha__lte=f2, curso_academico=curso_seleccionado).count()]
        else:
            datos = [Amonestaciones.objects.filter(IdAlumno__in=Alumnos.objects.filter(Unidad=curso),
                                                   curso_academico=curso_seleccionado).count(),
                     Sanciones.objects.filter(IdAlumno__in=Alumnos.objects.filter(Unidad=curso),
                                              curso_academico=curso_seleccionado).count()]
        if total[0] > 0:
            datos.append(round(datos[0] * 100 / total[0], 2))
        else:
            datos.append(0)  # Si total[0] es 0, asigna 0 para evitar división por cero

        if total[1] > 0:
            datos.append(round(datos[1] * 100 / total[1], 2))
        else:
            datos.append(0)  # Si total[1] es 0, asigna 0 para evitar división por cero
        lista.append(datos)

        cursos_nombres.append({
            'nombre': curso.Curso,
            'amonestaciones': datos[0],
            'sanciones': datos[1]
        })

    form = FechasForm(request.POST, curso_academico=curso_seleccionado) if request.method == "POST" else FechasForm(
        curso_academico=curso_seleccionado)

    cursos = zip(cursos_queryset, lista)
    cursos = sorted(cursos, key=lambda x: x[1][0], reverse=True)
    context = {'form': form, 'cursos': cursos, 'menu_estadistica': True, 'total': total,
               'cursos_nombres': cursos_nombres, 'curso_seleccionado': curso_seleccionado,
               'cursos_academicos': cursos_academicos}
    return render(request, 'grupos.html', context)


@login_required(login_url='/')
@user_passes_test(group_check_je, login_url='/')
def niveles(request):
    niveles_queryset = Niveles.objects.order_by('Nombre')
    niveles_nombres = []

    # Obtener todos los cursos académicos
    cursos_academicos = CursoAcademico.objects.order_by('nombre')

    # Determinar el curso académico seleccionado
    curso_academico_id = request.GET.get('curso_academico')
    if curso_academico_id:
        curso_seleccionado = get_object_or_404(CursoAcademico, id=curso_academico_id)
    else:
        curso_seleccionado = get_current_academic_year()

    # Por defecto, mostrar el curso académico actual si no se selecciona uno
    if not curso_seleccionado:
        curso_seleccionado = get_current_academic_year()

    if request.method == "POST":
        f1 = datetime.strptime(request.POST.get('Fecha1'), '%d/%m/%Y')
        f2 = datetime.strptime(request.POST.get('Fecha2'), '%d/%m/%Y')

    # Total
    total = []
    if request.method == "POST":
        total.append(
            Amonestaciones.objects.filter(Fecha__gte=f1, Fecha__lte=f2, curso_academico=curso_seleccionado).count())
        total.append(Sanciones.objects.filter(Fecha__gte=f1, Fecha__lte=f2, curso_academico=curso_seleccionado).count())
    else:
        total.append(Amonestaciones.objects.filter(curso_academico=curso_seleccionado).count())
        total.append(Sanciones.objects.filter(curso_academico=curso_seleccionado).count())

    lista = []

    for nivel in niveles_queryset:

        if request.method == "POST":
            datos = [Amonestaciones.objects.filter(IdAlumno__Unidad__Nivel=nivel).filter(Fecha__gte=f1,
                                                                                         Fecha__lte=f2,
                                                                                         curso_academico=curso_seleccionado).count(),
                     Sanciones.objects.filter(IdAlumno__Unidad__Nivel=nivel).filter(Fecha__gte=f1).filter(
                         Fecha__lte=f2).filter(Fecha__gte=f1, Fecha__lte=f2,
                                               curso_academico=curso_seleccionado).count()]
        else:
            datos = [Amonestaciones.objects.filter(IdAlumno__Unidad__Nivel=nivel,
                                                   curso_academico=curso_seleccionado).count(),
                     Sanciones.objects.filter(IdAlumno__Unidad__Nivel=nivel,
                                              curso_academico=curso_seleccionado).count()]

        if total[0] > 0:
            datos.append(round(datos[0] * 100 / total[0], 2))
        else:
            datos.append(0)  # Si total[0] es 0, asigna 0 para evitar división por cero

        if total[1] > 0:
            datos.append(round(datos[1] * 100 / total[1], 2))
        else:
            datos.append(0)  # Si total[1] es 0, asigna 0 para evitar división por cero

        lista.append(datos)

        niveles_nombres.append({
            'nombre': nivel.Abr,
            'amonestaciones': datos[0],
            'sanciones': datos[1]
        })

    form = FechasForm(request.POST, curso_academico=curso_seleccionado) if request.method == "POST" else FechasForm(
        curso_academico=curso_seleccionado)

    niveles = zip(niveles_queryset, lista)
    niveles = sorted(niveles, key=lambda x: x[1][0], reverse=True)
    context = {'form': form, 'niveles': niveles, 'menu_estadistica': True, 'total': total,
               'curso_seleccionado': curso_seleccionado,
               'cursos_academicos': cursos_academicos, 'niveles_nombres': niveles_nombres}
    return render(request, 'niveles.html', context)


@login_required(login_url='/')
@user_passes_test(group_check_je, login_url='/')
def alumnos(request):
    # Obtener todos los cursos académicos
    cursos_academicos = CursoAcademico.objects.order_by('nombre')

    # Determinar el curso académico seleccionado
    curso_academico_id = request.GET.get('curso_academico')
    if curso_academico_id:
        curso_seleccionado = get_object_or_404(CursoAcademico, id=curso_academico_id)
    else:
        curso_seleccionado = get_current_academic_year()

    # Por defecto, mostrar el curso académico actual si no se selecciona uno
    if not curso_seleccionado:
        curso_seleccionado = get_current_academic_year()

    if request.method == "POST":
        f1 = datetime.strptime(request.POST.get('Fecha1'), '%d/%m/%Y')
        f2 = datetime.strptime(request.POST.get('Fecha2'), '%d/%m/%Y')

    # Total
    total = []
    if request.method == "POST":
        total.append(
            Amonestaciones.objects.filter(Fecha__gte=f1, Fecha__lte=f2, curso_academico=curso_seleccionado).count())
        total.append(Sanciones.objects.filter(Fecha__gte=f1, Fecha__lte=f2, curso_academico=curso_seleccionado).count())
    else:
        total.append(Amonestaciones.objects.filter(curso_academico=curso_seleccionado).count())
        total.append(Sanciones.objects.filter(curso_academico=curso_seleccionado).count())

    if request.method == "POST":
        listAmon = Amonestaciones.objects.values('IdAlumno').filter(Fecha__gte=f1, Fecha__lte=f2,
                                                                    curso_academico=curso_seleccionado).annotate(
            Count('IdAlumno'))
        listSan = Sanciones.objects.values('IdAlumno').filter(Fecha__gte=f1, Fecha__lte=f2,
                                                              curso_academico=curso_seleccionado).annotate(
            Count('IdAlumno'))
    else:
        listAmon = Amonestaciones.objects.values('IdAlumno').filter(curso_academico=curso_seleccionado).annotate(
            Count('IdAlumno'))
        listSan = Sanciones.objects.values('IdAlumno').filter(curso_academico=curso_seleccionado).annotate(
            Count('IdAlumno'))
    newlist = sorted(listAmon, key=itemgetter('IdAlumno__count'), reverse=True)
    for l in newlist:
        try:
            l["Sanciones"] = listSan.get(IdAlumno=l["IdAlumno"]).get("IdAlumno__count")
        except:
            l["Sanciones"] = 0
        l["Porcentajes"] = []
        try:
            l["Porcentajes"].append(round(l["IdAlumno__count"] * 100 / total[0], 2))
        except:
            l["Porcentajes"].append(0)
        try:
            l["Porcentajes"].append(round(l["Sanciones"] * 100 / total[1], 2))
        except:
            l["Porcentajes"].append(0)

        try:
            alumno = Alumnos.objects.get(id=l["IdAlumno"])
            unidad = alumno.Unidad
            if unidad:
                l["IdAlumno"] = alumno.Nombre + " (" + unidad.Curso + ")"
            else:
                l["IdAlumno"] = alumno.Nombre + " (Sin Unidad asignada)"
        except Alumnos.DoesNotExist:
            l["IdAlumno"] = "Alumno no encontrado"

    form = FechasForm(request.POST, curso_academico=curso_seleccionado) if request.method == "POST" else FechasForm(
        curso_academico=curso_seleccionado)
    context = {"form": form, "lista": newlist, 'menu_estadistica': True, "suma": total,
               'curso_seleccionado': curso_seleccionado,
               'cursos_academicos': cursos_academicos}
    return render(request, 'lalumnos.html', context)


def ContarFaltas(lista_id):
    contar = []
    for alum in lista_id:
        am = str(len(Amonestaciones.objects.filter(IdAlumno_id=list(alum.values())[0])))
        sa = str(len(Sanciones.objects.filter(IdAlumno_id=list(alum.values())[0])))

        contar.append(am + "/" + sa)
    return contar


# Curro Jul 24: Anado view para que un profesor pueda poner un parte
@login_required(login_url='/')
@user_passes_test(group_check_prof, login_url='/')
def parteprofe(request, tipo, alum_id):
    alum = Alumnos.objects.get(pk=alum_id)
    profesor = request.user.profesor

    if request.method == 'POST':
        if tipo == "amonestacion":
            form = AmonestacionProfeForm(request.POST)
            titulo = "Amonestaciones"
        else:
            return redirect("/")

        if form.is_valid():
            form.save()

            if tipo == "amonestacion":
                amon = form.instance
                destinatarios = [amon.Profesor, amon.IdAlumno.Unidad.Tutor]

                template = get_template("correo_amonestacion.html")
                contenido = template.render({'amon': amon})

                # Comunica la amonestación a la familia
                correo_familia = amon.IdAlumno.email
                if correo_familia:
                    template = get_template("correo_amonestacion.html")
                    contenido = template.render({'amon': amon})

            # send_mail(
            #	'Nueva amonestación',
            #	contenido,
            #	'41011038.jestudios.edu@juntadeandalucia.es',
            #	(correo_familia,),
            #	fail_silently=False
            # )

            return redirect('/centro/misalumnos')
    else:
        if tipo == "amonestacion":
            form = AmonestacionProfeForm(
                {'IdAlumno': alum.id, 'Fecha': time.strftime("%d/%m/%Y"), 'Hora': 1, 'Profesor': profesor.id,
                 'ComunicadoFamilia': False})

            titulo = "Amonestaciones"
        else:
            return redirect("/")
        error = False
    context = {'alum': alum, 'form': form, 'titulo': titulo, 'tipo': tipo, 'menu_convivencia': True,
               'profesor': profesor}
    return render(request, 'parteprofe.html', context)


@login_required(login_url='/')
@user_passes_test(group_check_je, login_url='/')
def aulaconvivencia(request):
    horas = ["1ª hora", "2ª hora", "3ª hora", "Recreo", "4ª hora", "5ª hora", "6ª hora"]

    curso_academico_actual = get_current_academic_year()

    amonestaciones = Amonestaciones.objects.filter(curso_academico=curso_academico_actual, DerivadoConvivencia=True)

    context = {
        'amonestaciones': amonestaciones,
        'num_resultados': amonestaciones.count(),
        'menu_convivencia': True,
        'horas': horas,
    }

    return render(request, 'aulaconvivencia.html', context)

@login_required(login_url='/')
@user_passes_test(group_check_je, login_url='/')
def alumnadosancionable(request):
    horas = ["1ª hora", "2ª hora", "3ª hora", "Recreo", "4ª hora", "5ª hora", "6ª hora"]

    curso_academico_actual = get_current_academic_year()

    amonestaciones = Amonestaciones.objects.filter(curso_academico=curso_academico_actual, DerivadoConvivencia=True)

    context = {
        'amonestaciones': amonestaciones,
        'num_resultados': amonestaciones.count(),
        'menu_convivencia': True,
        'horas': horas,
    }

    return render(request, 'aulaconvivencia.html', context)