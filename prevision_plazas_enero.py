# Este código para poder usar ORM de django
import os
import django
from django.db.models import Q

# Especifica la configuración de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion.settings')

# Inicializa Django
django.setup()

from centro.utils import get_current_academic_year
from analres.models import IndicadoresAlumnado

curso_academico_actual = get_current_academic_year()
repetidores = {}
promocionan = {}
repetidores["1º ESO"] = IndicadoresAlumnado.objects.filter(
    Q(curso_academico=curso_academico_actual) &
    Q(Convocatoria='1EV') &
    Q(Alumno__info_adicional__Repetidor=False) &
    Q(Alumno__info_adicional__Nivel__Abr="1º ESO") &
    Q(Alumno__info_adicional__curso_academico=curso_academico_actual) &
    Q(EstimacionPromocion=False)).count()

print(f'1º ESO: rep:{repetidores["1º ESO"]} -> {repetidores["1º ESO"]} plazas')

promocionan["1º ESO"] = IndicadoresAlumnado.objects.filter(
    Q(curso_academico=curso_academico_actual) &
    Q(Convocatoria='1EV') &
    Q(Alumno__info_adicional__Nivel__Abr="1º ESO") &
    Q(Alumno__info_adicional__curso_academico=curso_academico_actual) &
    (
        Q(EstimacionPromocion=True) | (
            Q(EstimacionPromocion=False) &
            Q(Alumno__info_adicional__Repetidor=True)
        )
    )
).count()
repetidores["2º ESO"] = IndicadoresAlumnado.objects.filter(
    Q(curso_academico=curso_academico_actual) &
    Q(Convocatoria='1EV') &
    Q(Alumno__info_adicional__Repetidor=False) &
    Q(Alumno__info_adicional__Nivel__Abr="2º ESO") &
    Q(Alumno__info_adicional__curso_academico=curso_academico_actual) &
    Q(EstimacionPromocion=False)).count()
print(f'2º ESO: prom: {promocionan["1º ESO"]}, rep: {repetidores["2º ESO"]} -> {promocionan["1º ESO"] + repetidores["2º ESO"]} plazas')

promocionan["2º ESO"] = IndicadoresAlumnado.objects.filter(
    Q(curso_academico=curso_academico_actual) &
    Q(Convocatoria='1EV') &
    Q(Alumno__info_adicional__Nivel__Abr="2º ESO") &
    Q(Alumno__info_adicional__curso_academico=curso_academico_actual) &
    (
        Q(EstimacionPromocion=True) | (
            Q(EstimacionPromocion=False) &
            Q(Alumno__info_adicional__Repetidor=True)
        )
    )
).count()
repetidores["3º ESO"] = IndicadoresAlumnado.objects.filter(
    Q(curso_academico=curso_academico_actual) &
    Q(Convocatoria='1EV') &
    Q(Alumno__info_adicional__Repetidor=False) &
    Q(Alumno__info_adicional__Nivel__Abr="3º ESO") &
    Q(Alumno__info_adicional__curso_academico=curso_academico_actual) &
    Q(EstimacionPromocion=False)).count()

rep_3_16 = IndicadoresAlumnado.objects.filter(
    Q(curso_academico=curso_academico_actual) &
    Q(Convocatoria='1EV') &
    Q(Alumno__info_adicional__Repetidor=False) &
    Q(Alumno__info_adicional__Nivel__Abr="3º ESO") &
    Q(Alumno__info_adicional__Edad__gte=16) &
    Q(Alumno__info_adicional__curso_academico=curso_academico_actual) &
    Q(EstimacionPromocion=False)).count()
print(f'3º ESO: prom: {promocionan["2º ESO"]}, rep: {repetidores["3º ESO"]} ({rep_3_16}) -> {promocionan["2º ESO"] + repetidores["3º ESO"]} plazas')

promocionan["3º ESO"] = IndicadoresAlumnado.objects.filter(
    Q(curso_academico=curso_academico_actual) &
    Q(Convocatoria='1EV') &
    Q(Alumno__info_adicional__Nivel__Abr="3º ESO") &
    Q(Alumno__info_adicional__curso_academico=curso_academico_actual) &
    (
        Q(EstimacionPromocion=True) | (
            Q(EstimacionPromocion=False) &
            Q(Alumno__info_adicional__Repetidor=True)
        )
    )
).count()
repetidores["4º ESO"] = IndicadoresAlumnado.objects.filter(
    Q(curso_academico=curso_academico_actual) &
    Q(Convocatoria='1EV') &
    Q(Alumno__info_adicional__Repetidor=False) &
    Q(Alumno__info_adicional__Nivel__Abr="4º ESO") &
    Q(Alumno__info_adicional__curso_academico=curso_academico_actual) &
    Q(EstimacionPromocion=False)).count()
print(f'4º ESO: prom: {promocionan["3º ESO"]}, rep: {repetidores["4º ESO"]} -> {promocionan["3º ESO"] + repetidores["4º ESO"]} plazas')

promocionan["4º ESO ACAD CyT"] = IndicadoresAlumnado.objects.filter(
    Q(curso_academico=curso_academico_actual) &
    Q(Convocatoria='1EV') &
    Q(Alumno__info_adicional__Nivel__Abr="4º ESO") &
    Q(Modalidad="ACAD CyT") &
    Q(Alumno__info_adicional__curso_academico=curso_academico_actual) &
    (
        Q(EstimacionPromocion=True) | (
            Q(EstimacionPromocion=False) &
            Q(Alumno__info_adicional__Repetidor=True)
        )
    )
).count()
repetidores["1º BTO CyT"] = IndicadoresAlumnado.objects.filter(
    Q(curso_academico=curso_academico_actual) &
    Q(Convocatoria='1EV') &
    Q(Alumno__info_adicional__Repetidor=False) &
    Q(Alumno__info_adicional__Nivel__Abr="1º BTO CyT") &
    Q(Alumno__info_adicional__curso_academico=curso_academico_actual) &
    Q(EstimacionPromocion=False)).count()
print(f'1º BTO CyT: prom: {promocionan["4º ESO ACAD CyT"]}, rep: {repetidores["1º BTO CyT"]} -> {promocionan["4º ESO ACAD CyT"] + repetidores["1º BTO CyT"]} plazas')

promocionan["4º ESO ACAD HyCS"] = IndicadoresAlumnado.objects.filter(
    Q(curso_academico=curso_academico_actual) &
    Q(Convocatoria='1EV') &
    Q(Alumno__info_adicional__Nivel__Abr="4º ESO") &
    Q(Modalidad="ACAD HyCS") &
    Q(Alumno__info_adicional__curso_academico=curso_academico_actual) &
    (
        Q(EstimacionPromocion=True) | (
            Q(EstimacionPromocion=False) &
            Q(Alumno__info_adicional__Repetidor=True)
        )
    )
).count()
repetidores["1º BTO HyCS"] = IndicadoresAlumnado.objects.filter(
    Q(curso_academico=curso_academico_actual) &
    Q(Convocatoria='1EV') &
    Q(Alumno__info_adicional__Repetidor=False) &
    Q(Alumno__info_adicional__Nivel__Abr="1º BTO HyCS") &
    Q(Alumno__info_adicional__curso_academico=curso_academico_actual) &
    Q(EstimacionPromocion=False)).count()
print(f'1º BTO HyCS: prom: {promocionan["4º ESO ACAD HyCS"]}, rep: {repetidores["1º BTO HyCS"]} -> {promocionan["4º ESO ACAD HyCS"] + repetidores["1º BTO HyCS"]} plazas')

promocionan["1º BTO CyT"] = IndicadoresAlumnado.objects.filter(
    Q(curso_academico=curso_academico_actual) &
    Q(Convocatoria='1EV') &
    Q(Alumno__info_adicional__Nivel__Abr="1º BTO CyT") &
    Q(Alumno__info_adicional__curso_academico=curso_academico_actual) &
    Q(EstimacionPromocion=True)
).count()
repetidores["2º BTO CyT"] = IndicadoresAlumnado.objects.filter(
    Q(curso_academico=curso_academico_actual) &
    Q(Convocatoria='1EV') &
    Q(Alumno__info_adicional__Repetidor=False) &
    Q(Alumno__info_adicional__Nivel__Abr="2º BTO CyT") &
    Q(Alumno__info_adicional__curso_academico=curso_academico_actual) &
    Q(EstimacionPromocion=False)).count()
print(f'2º BTO HyCS: prom: {promocionan["1º BTO CyT"]}, rep: {repetidores["2º BTO CyT"]} -> {promocionan["1º BTO CyT"] + repetidores["2º BTO CyT"]} plazas')

promocionan["1º BTO HyCS"] = IndicadoresAlumnado.objects.filter(
    Q(curso_academico=curso_academico_actual) &
    Q(Convocatoria='1EV') &
    Q(Alumno__info_adicional__Nivel__Abr="1º BTO HyCS") &
    Q(Alumno__info_adicional__curso_academico=curso_academico_actual) &
    Q(EstimacionPromocion=True)
).count()
repetidores["2º BTO HyCS"] = IndicadoresAlumnado.objects.filter(
    Q(curso_academico=curso_academico_actual) &
    Q(Convocatoria='1EV') &
    Q(Alumno__info_adicional__Repetidor=False) &
    Q(Alumno__info_adicional__Nivel__Abr="2º BTO HyCS") &
    Q(Alumno__info_adicional__curso_academico=curso_academico_actual) &
    Q(EstimacionPromocion=False)).count()
print(f'2º BTO HyCS: prom: {promocionan["1º BTO HyCS"]}, rep: {repetidores["2º BTO HyCS"]} -> {promocionan["1º BTO HyCS"] + repetidores["2º BTO HyCS"]} plazas')
