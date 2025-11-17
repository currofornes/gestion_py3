from abc import ABC, abstractmethod
from collections import defaultdict
from itertools import product
import statistics
import matplotlib.pyplot as plt
import io
import base64

import numpy as np
from matplotlib.lines import lineStyles

from analres.models import Calificaciones, IndicadoresAlumnado
from centro.models import Niveles
from horarios.templatetags.horario_tags import get_item


def isdigit(s):
    try:
        float(s)
        return True
    except ValueError:
        try:
            int(s)
            return True
        except ValueError:
            return False


class Indicador(ABC):
    """
    Clase base para un indicador.
    Un indicador es el elemento de cálculo básico para las calificaciones de un alumno en un curso académico y una convocatoria.

    """
    def __init__(self):
        pass

    @abstractmethod
    def calcular(self, calificaciones, **kwargs):
        """
        Método abstracto que debe ser implementado en las clases hijas.
        Este método realizará el cálculo específico sobre las calificaciones obtenidas.
        """
        pass


class AbandonoEscolar(Indicador):
    """
    Este indicador calcula si un alumno ha abandonado. Sólo se va a aplicar a alumnado de ESO.
    Se entiende que un alumno ha abandonado si más del 80% de sus calificaciones son 1.
    Devuelve un valor lógico.
    """
    def calcular(self, calificaciones, **kwargs):
        abandonos = 0
        calificadas = 0

        for calificacion in calificaciones:
            if calificacion.Calificacion in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10']:
                calificadas += 1
                if int(calificacion.Calificacion) == 1:
                    abandonos += 1

        return (calificadas == 0) or (abandonos/calificadas >= 0.8)


class Nro_Suspensos(Indicador):
    """
    Este indicador devuelve el número de materias no superadas.
    """
    def calcular(self, calificaciones, **kwargs):
        suspensos = 0
        for calificacion in calificaciones:
            if isdigit(calificacion.Calificacion) and int(calificacion.Calificacion) < 5:
                suspensos += 1
        return suspensos


class EstimacionPromocion(Indicador):
    """
    Este indicador devuelve la estimación de promoción de un alumno basándose en sus calificaciones y en el nivel del alumnado.
    """

    def __init__(self):
        super().__init__()

    def calcular(self, calificaciones, **kwargs):
        nro_suspensos = Nro_Suspensos()
        nivel = kwargs['nivel']
        promo_ord = kwargs.get('promocion', None)
        if promo_ord is None:
            if 'ESO' in nivel.Abr or 'BTO' in nivel.Abr:
                return nro_suspensos.calcular(calificaciones) <= 4
            else:
                return nro_suspensos.calcular(calificaciones) == 0
        else:
            return promo_ord


class EficaciaTransito(Indicador):
    """
    Este indicador solo aplica a alumnado de 1º ESO.
    Devuelve True si tiene no más de 3 suspensos.
    """

    def __init__(self):
        super().__init__()

    def calcular(self, calificaciones, **kwargs):
        nro_suspensos = Nro_Suspensos()
        return nro_suspensos.calcular(calificaciones) <= 3


class EvaluacionPositivaTodo(Indicador):
    """
    Este indicador devuelve un valor lógico.
    El resultado es True si el alumno tiene todas las materias aprobadas.
    """
    def calcular(self, calificaciones, **kwargs):
        nro_suspensos = Nro_Suspensos()
        return nro_suspensos.calcular(calificaciones) == 0


class IdoneidadCursoEdad(Indicador):
    """
    Este indicador devuelve verdadero si la edad es adecuada al curso. Solo aplica a ESO.
    Curso   Edad
    1º ESO  12
    2º ESO  13
    3º ESO  14
    4º ESO  15
    """

    def __init__(self):
        super().__init__()

    def calcular(self, calificaciones, **kwargs):
        nivel = kwargs['nivel']
        edad = kwargs['edad']
        return (
            ((nivel.Nombre == '1º de E.S.O.') and (edad == 12)) or
            ((nivel.Nombre == '2º de E.S.O.') and (edad == 13)) or
            ((nivel.Nombre == '3º de E.S.O.') and (edad == 14)) or
            ((nivel.Nombre == '4º de E.S.O.') and (edad == 15))
        )


class Modalidad(Indicador):

    def calcular(self, calificaciones, **kwargs):
        nivel = kwargs['nivel']
        calif_dict = {calif.Materia: calif.Calificacion for calif in calificaciones}
        if nivel.Abr == "4º ESO":
            if ('MAP' in calif_dict and calif_dict['MAP']) or ('MAA' in calif_dict and calif_dict['MAA']):
                return "PROF"
            elif 'ACT' in calif_dict and calif_dict['ACT']:
                return "PDC"
            elif ('MAC' in calif_dict and calif_dict['MAC']) or ('MAB' in calif_dict and calif_dict['MAB']):
                if 'LAT' in calif_dict and calif_dict['LAT']:
                    return "ACAD HyCS"
                else:
                    return "ACAD CyT"
        if "BTO HyCS" in nivel.Abr:
            return "HyCS"
        if "BTO CyT" in nivel.Abr:
            return "CyT"

        return None


def calcular_indicador(curso_academico, convocatoria, niveles, modalidad=None, indicador=None, abandono_cuenta=False):
    if not abandono_cuenta:
        datos = IndicadoresAlumnado.objects.filter(
            curso_academico=curso_academico,
            Convocatoria=convocatoria,
            Alumno__info_adicional__curso_academico=curso_academico,
            Alumno__info_adicional__Nivel__in=niveles
        )
    else:
        datos = IndicadoresAlumnado.objects.filter(
            curso_academico=curso_academico,
            Convocatoria=convocatoria,
            AbandonoEscolar=False,
            Alumno__info_adicional__curso_academico=curso_academico,
            Alumno__info_adicional__Nivel__in=niveles
        )
    if modalidad:
        datos = datos.filter(Modalidad=modalidad)

    if indicador:
        datos = datos.exclude(**{indicador: None})
        total = datos.count()
        parte = datos.filter(**{indicador: True}).count()

        if total > 0:
            return 100 * parte / total
        else:
            return 0
    else:
        return None

class Serie(object):
    curso_academico = None
    nro_cursos = None
    convocatoria = None
    niveles = None
    modalidades = None
    indicador = None
    titulo = None
    abandono_cuenta = None

    resultados = None
    mu = None
    sigma = None

    def __init__(self, curso_academico, nro_cursos, convocatoria, niveles, abandono_cuenta=False, modalidades=None, indicador="", titulo=""):
        self.curso_academico = curso_academico
        self.nro_cursos = nro_cursos
        self.convocatoria = convocatoria
        self.niveles = niveles
        self.abandono_cuenta = abandono_cuenta
        self.modalidades = modalidades
        self.indicador = indicador
        self.titulo = titulo

        self.cursos = [self.curso_academico - i for i in range(nro_cursos - 1, -1, -1)]

        if self.modalidades:
            if self.abandono_cuenta:
                self.resultados = {curso: {modalidad: (0., 0.) for modalidad in self.modalidades} for curso in self.cursos}
                self.mu = {modalidad: (0., 0.) for modalidad in self.modalidades}
                self.sigma = {modalidad: (0., 0.) for modalidad in self.modalidades}
            else:
                self.resultados = {curso: {modalidad: 0. for modalidad in self.modalidades} for curso in self.cursos}
                self.mu = {modalidad: 0. for modalidad in self.modalidades}
                self.sigma = {modalidad: 0. for modalidad in self.modalidades}
        else:
            if self.abandono_cuenta:
                self.resultados = {curso: (0., 0.) for curso in self.cursos}
                self.mu = (0., 0.)
                self.sigma = (0., 0.)
            else:
                self.resultados = {curso: 0. for curso in self.cursos}
                self.mu = 0.
                self.sigma = 0.


    def calcular(self):
        if self.modalidades:
            for modalidad in self.modalidades:
                # No tengo en cuenta los abandonos porque no se van a usar con modalidades o itinerarios
                res = []
                for curso in self.cursos:
                    self.resultados[curso][modalidad] = calcular_indicador(
                        curso, self.convocatoria, self.niveles, modalidad, self.indicador
                    )
                    if self.resultados[curso][modalidad]:
                        res.append(self.resultados[curso][modalidad])
                self.mu[modalidad] = statistics.mean(res)
                self.sigma[modalidad] = statistics.stdev(res) if len(res) > 1 else 0
        else:
            res = []
            res_sin_abandono = []
            for curso in self.cursos:
                if self.abandono_cuenta:
                    resultados_sin_abandonos = calcular_indicador(
                        curso, self.convocatoria, self.niveles, indicador=self.indicador, abandono_cuenta=True
                    )
                resultados_totales = calcular_indicador(
                    curso, self.convocatoria, self.niveles, indicador=self.indicador, abandono_cuenta=False
                )
                if self.abandono_cuenta:
                    self.resultados[curso] = (resultados_sin_abandonos, resultados_totales)
                    res.append(resultados_totales)
                    res_sin_abandono.append(resultados_sin_abandonos)
                else:
                    self.resultados[curso] = resultados_totales
                    res.append(resultados_totales)

            if self.abandono_cuenta:
                self.mu = (statistics.mean(res_sin_abandono), statistics.mean(res))
                self.sigma = (
                    statistics.stdev(res_sin_abandono) if len(res_sin_abandono) > 1 else 0,
                    statistics.stdev(res) if len(res) > 1 else 0,
                )
            else:
                self.mu = statistics.mean(res)
                self.sigma = statistics.stdev(res) if len(res) > 1 else 0

    def grafica(self):
        cursos =[curso.nombre for curso in self.cursos]

        if self.modalidades:
            porcentajes = {mod: [] for mod in self.modalidades}
            for curso in self.cursos:
                for modalidad in self.modalidades:
                    if self.resultados[curso][modalidad]:
                        porcentajes[modalidad].append(self.resultados[curso][modalidad])
                    else:
                        porcentajes[modalidad].append(0)
        else:
            if self.abandono_cuenta:
                porcentajes_sin_abandono = [self.resultados[curso][0] for curso in self.cursos]
                porcentajes_total = [self.resultados[curso][1] for curso in self.cursos]
            else:
                porcentajes = [self.resultados[curso] if self.resultados[curso] else 0 for curso in self.cursos]

        fig, ax = plt.subplots(figsize=(8, 4), layout='constrained')

        if self.modalidades:
            bar_width = 0.3
            group_spacing = 0.1
            x = np.arange(len(cursos)) * (len(self.modalidades) * bar_width + group_spacing)

            paleta = ['skyblue', 'lightgreen', 'violet', 'orange']
            colors = {mod: paleta[i] for i, mod in enumerate(self.modalidades)}

            multiplier = 0
            for modalidad, valores in porcentajes.items():
                offset = bar_width * multiplier
                rects = ax.bar(x + offset, valores, bar_width, color=colors[modalidad], label=modalidad)
                # ax.bar_label(rects, padding=3)
                multiplier += 1
            for mod, media in self.mu.items():
                plt.axhline(y=media, color=colors[mod], linestyle='--', linewidth=1.5)

            ax.legend(loc='upper left', ncols=len(self.modalidades))
            ax.set_xticks(x + (len(self.modalidades) - 1) * bar_width / 2)
        else:
            if self.abandono_cuenta:
                bar_width = 0.3
                group_spacing = 0.1
                x = np.arange(len(cursos)) * (2 * bar_width + group_spacing)

                colors = {
                    'Sin abandono': 'skyblue',
                    'Total': 'orange',
                }

                multiplier = 0
                datos = {
                    'Sin abandono': porcentajes_sin_abandono,
                    'Total': porcentajes_total,
                }
                for modalidad, valores in datos.items():
                    offset = bar_width * multiplier
                    rects = ax.bar(x + offset, valores, bar_width, color=colors[modalidad], label=modalidad)
                    # ax.bar_label(rects, padding=3)
                    multiplier += 1
                mu_sin_abandono = self.mu[0]
                mu_total = self.mu[1]
                plt.axhline(y=mu_sin_abandono, color=colors['Sin abandono'], linestyle='--', linewidth=1.5)
                plt.axhline(y=mu_total, color=colors['Total'], linestyle='--', linewidth=1.5)

                ax.legend(loc='upper left', ncols=2)
                ax.set_xticks(x + bar_width / 2)

            else:
                bar_width = 0.4
                x = np.arange(len(cursos))

                bars = plt.bar(cursos, porcentajes, color='skyblue', edgecolor='black')
                plt.axhline(y=self.mu, color='red', linestyle='--', linewidth=1.5)
                ax.set_xticks(x)

        ax.set_xticklabels(cursos)

        ax.set_ylabel('Porcentaje (%)')
        ax.set_title(self.titulo)
        ax.set_ylim(0, 120)


        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        plt.close()
        buffer.seek(0)

        # Convertir la imagen a base64
        imagen_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        buffer.close()
        return imagen_base64


class SerieManual(object):
    categorias = None # list(str)
    valores = None # dict(str: float)
    titulo = None # str
    referencia = None # float

    def __init__(self, categorias, valores, referencia=None, titulo=None):
        self.categorias = categorias
        self.valores = valores
        self.referencia = referencia
        self.titulo = titulo

    def grafica(self):
        valores = [self.valores[categoria] for categoria in self.categorias]

        fig, ax = plt.subplots(figsize=(8, 4), layout='constrained')

        bar_width = 0.4
        x = np.arange(len(self.categorias))
        bars = plt.bar(self.categorias, valores, color='skyblue', edgecolor='black')
        if self.referencia:
            plt.axhline(y=self.referencia, color='red', linestyle='--', linewidth=1.5)
        ax.set_xticks(x)


        # ax.legend(loc='upper left', ncols=len(self.categorias))
        # ax.set_xticks(x + (len(self.categorias) - 1) * bar_width / 2)


        # ax.set_xticklabels(cursos)

        ax.set_ylabel('Porcentaje (%)')
        ax.set_title(self.titulo)
        ax.set_ylim(0, 120)

        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        plt.close()
        buffer.seek(0)

        # Convertir la imagen a base64
        imagen_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        buffer.close()
        return imagen_base64





