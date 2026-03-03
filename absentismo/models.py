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
import os

from django.db import models

from centro.models import Alumnos, Profesores, CursoAcademico


# Create your models here.
class TiposActuaciones(models.Model):
    TipoActuacion = models.CharField(max_length=60)


    def __str__(self):
        return self.TipoActuacion

    class Meta:
        verbose_name = "Tipo Actuación"
        verbose_name_plural = "Tipos de Actuación"

class ProtocoloAbs(models.Model):
    alumno = models.ForeignKey(Alumnos, related_name='protocolos', on_delete=models.CASCADE)
    tutor = models.ForeignKey(Profesores, related_name='tutor', on_delete=models.CASCADE)
    fecha_apertura = models.DateField()
    fecha_cierre = models.DateField(blank=True, null=True)
    abierto = models.BooleanField(default=False)

    curso_academico = models.ForeignKey(CursoAcademico, on_delete=models.SET_NULL, null=True, blank=True)


    def __str__(self):
        return f"Protocolo absentismo para {self.alumno.Nombre}, abierto por {self.tutor}"

    class Meta:
        verbose_name="Protocolo Absentismo"
        verbose_name_plural="Protocolos Absentismo"

    def faltas_injustificadas_periodo(self, periodo):
        CI = 0
        TNJ = 0
        for falta in self.faltas.all():
            if periodo.inicio <= falta.Fecha <= periodo.fin:
                CI += falta.DiaCompletoNoJustificada
                TNJ += falta.TramosNoJustificados
        return {
            'dias': CI,
            'tramos': TNJ,
            'total tramos': CI * 6 + TNJ,
            'porcentaje': round(100 * (CI * 6 + TNJ) / (periodo.dias_lectivos * 6), 2)}

    def hay_faltas(self, periodo):
        return self.faltas.filter(
            Fecha__range=(periodo.inicio, periodo.fin)
        ).exists()


class Actuaciones(models.Model):
    medios = (
        ('1', 'Teléfono'),
        ('2', 'PASEN'),
        ('3', 'Correo ordinario'),
        ('4', 'Correo certificado'),
        ('5', 'Otros'),
    )
    Protocolo = models.ForeignKey(ProtocoloAbs,  related_name='actuaciones', on_delete=models.CASCADE)
    Fecha = models.DateField()
    Tipo = models.ForeignKey(TiposActuaciones, related_name='Tipo_de', blank=True, null=True, on_delete=models.SET_NULL)
    Comentario = models.TextField(blank=True)
    Notificada = models.BooleanField(default=False)
    Medio = models.CharField(max_length=1, choices=medios,blank=True, null=True)
    Telefono = models.TextField(blank=True, null=True)
    curso_academico = models.ForeignKey(CursoAcademico, on_delete=models.SET_NULL, null=True, blank=True)


    def __unicode__(self):
        return self.Protocolo

    class Meta:
        verbose_name = "Actuación"
        verbose_name_plural = "Actuaciones"


class FaltasProtocolo(models.Model):
    Protocolo = models.ForeignKey(ProtocoloAbs, related_name='faltas', on_delete=models.CASCADE)
    Fecha = models.DateField()
    DiaCompletoJustificada = models.PositiveSmallIntegerField(blank=True, null=True)
    DiaCompletoNoJustificada = models.PositiveSmallIntegerField(blank=True, null=True)
    TramosJustificados = models.PositiveSmallIntegerField(blank=True, null=True)
    TramosNoJustificados = models.PositiveSmallIntegerField(blank=True, null=True)
    NotificacionDiaCompleto = models.PositiveSmallIntegerField(blank=True, null=True)
    NotificacionTramos = models.PositiveSmallIntegerField(blank=True, null=True)

    def __str__(self):
        return f'Faltas del protocolo {self.Protocolo} en {self.Fecha}'

    class Meta:
        verbose_name = "Faltas de asistencia de un protocolo"
        verbose_name_plural = "Faltas de asistencia de los protocolos"


class InformeFM(models.Model):
    protocolo = models.OneToOneField('ProtocoloAbs', on_delete=models.CASCADE,
                                     related_name='informe_fiscalia')
    fecha_inicio = models.DateField(null=True, blank=True)

    # ASIGNACIÓN DE TUTORES (nuevo)
    ASIGNACION_CHOICES = [
        ('1P_2M',   'Tutor 1 → Padre / Tutor 2 → Madre'),
        ('1M_2P',   'Tutor 1 → Madre / Tutor 2 → Padre'),
        ('SOLO_1P', 'Solo Tutor 1, figura paterna'),
        ('SOLO_1M', 'Solo Tutor 1, figura materna'),
        ('SOLO_2P', 'Solo Tutor 2, figura paterna'),
        ('SOLO_2M', 'Solo Tutor 2, figura materna'),
    ]
    asignacion_tutores = models.CharField(
        max_length=10,
        blank=True,
        default='1P_2M',
        verbose_name='Asignación de tutores',
        choices=ASIGNACION_CHOICES,
    )

    # DATOS DE IDENTIFICACIÓN DE EL/LA MENOR
    representante_nombre = models.CharField(max_length=255, blank=True)
    representante_parentesco = models.CharField(max_length=255, blank=True)
    representante_DNI = models.CharField(max_length=9, blank=True)

    # DATOS FAMILIARES
    CHOICES_HERMANOS = [('SI', 'Sí'), ('NO', 'No'), ('NS', 'No se conoce')]
    hermanos_centro = models.TextField(max_length=2, choices=CHOICES_HERMANOS, blank=True)
    hermanos_centro_nro = models.PositiveSmallIntegerField(default=0)
    hermanos_absentistas = models.TextField(max_length=2, choices=CHOICES_HERMANOS, blank=True)
    hermanos_absentistas_nro = models.PositiveSmallIntegerField(default=0)
    hermanos_absentistas_nombres = models.TextField(blank=True)
    otros_convivientes = models.TextField(blank=True)

    # Textos del informe
    informe_actuaciones = models.TextField(blank=True)
    valoracion_educativa = models.TextField(blank=True)
    comparecencia_menor = models.TextField(blank=True)
    llamadas_citaciones = models.TextField(blank=True)
    comparecencia_tutores_legales = models.TextField(blank=True)

    # Metadatos
    finalizado = models.BooleanField(default=False)
    ultima_modificacion = models.DateTimeField(auto_now=True)


class InformeSSC(models.Model):
    protocolo = models.OneToOneField('ProtocoloAbs', on_delete=models.CASCADE,
                                     related_name='informe_sscc')

    DIRIGIDO_CHOICES = [
        ('SS_CC',        'Servicios Sociales Comunitarios'),
        ('MESA_TECNICA', 'Mesa Técnica'),
        ('FISCALIA',     'Fiscalía de Menores'),
    ]
    dirigido_a = models.CharField(max_length=12, choices=DIRIGIDO_CHOICES, blank=True)
    fecha_derivacion = models.DateField(null=True, blank=True)

    # Sección 4 — Información psicopedagógica
    psi_des    = models.BooleanField(default=False, verbose_name='DES – Desfavorecido Socialmente')
    psi_dia    = models.BooleanField(default=False, verbose_name='DIA – Dificultades de Aprendizaje')
    psi_dis    = models.BooleanField(default=False, verbose_name='DIS – Diversidad Funcional')
    psi_tdah   = models.BooleanField(default=False, verbose_name='TDAH')
    psi_aaccii = models.BooleanField(default=False, verbose_name='AACCII – Altas Capacidades')
    psi_otros  = models.CharField(max_length=255, blank=True)

    # Sección 5 — Servicios del centro (los 10 del formulario)
    serv_aula_matinal     = models.BooleanField(default=False, verbose_name='Aula Matinal')
    serv_atal             = models.BooleanField(default=False, verbose_name='ATAL')
    serv_comedor          = models.BooleanField(default=False, verbose_name='Comedor Escolar')
    serv_acompanamiento   = models.BooleanField(default=False, verbose_name='Programa de Acompañamiento')
    serv_parcep           = models.BooleanField(default=False, verbose_name='PARCEP / PARCES')
    serv_deporte          = models.BooleanField(default=False, verbose_name='Deporte en la Escuela')
    serv_actividades_ayto = models.BooleanField(default=False, verbose_name='Actividades Ayuntamiento / ESFL')
    serv_pale             = models.BooleanField(default=False, verbose_name='PALE')
    serv_pali             = models.BooleanField(default=False, verbose_name='PALI')
    serv_otras_act        = models.BooleanField(default=False, verbose_name='Otras Act. Complementarias')
    serv_otros            = models.CharField(max_length=255, blank=True)

    # Sección 6 — Antecedentes
    hermanos_nombres  = models.TextField(blank=True)
    hermanos_centros  = models.TextField(blank=True)
    ant_primera_vez   = models.BooleanField(default=False)
    ant_reiteradas    = models.BooleanField(default=False)
    ant_curso_inicio = models.ForeignKey(
        'centro.CursoAcademico', on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='informes_ssc_inicio'
    )

    # Sección 7 — Dificultades psicosociales
    dif_iguales     = models.BooleanField(default=False)
    dif_profesorado = models.BooleanField(default=False)
    dif_disruptivo  = models.BooleanField(default=False)
    dif_salud_mental= models.BooleanField(default=False)

    # Sección 7 — Medidas acordadas
    med_compromisos      = models.BooleanField(default=False)
    med_aula_convivencia = models.BooleanField(default=False)
    med_talleres         = models.BooleanField(default=False)
    med_mediacion        = models.BooleanField(default=False)
    med_observaciones    = models.TextField(blank=True)

    # Sección 8 — Ámbito familiar
    fam_relaciones   = models.BooleanField(default=False)
    fam_economicas   = models.BooleanField(default=False)
    fam_educativas   = models.BooleanField(default=False)
    fam_riesgo       = models.BooleanField(default=False)
    fam_observaciones= models.TextField(blank=True)

    # Sección 9 — Actuaciones del centro
    act_tutor           = models.TextField(blank=True)
    act_eoe             = models.TextField(blank=True)
    act_equipo_dir      = models.TextField(blank=True)
    act_motivos_familia = models.TextField(blank=True)

    # Sección 9 — Actuaciones individuales
    ind_refuerzo      = models.BooleanField(default=False)
    ind_tutorial      = models.BooleanField(default=False)
    ind_eoe           = models.BooleanField(default=False)
    ind_observaciones = models.TextField(blank=True)

    # Sección 10 — Otra información
    otra_info = models.TextField(blank=True)

    # Metadatos
    finalizado          = models.BooleanField(default=False)
    ultima_modificacion = models.DateTimeField(auto_now=True)

def _ruta_adjunto_fm(instance, filename):
    """Guarda en  media/absentismo/adjuntos/fm/<protocolo_id>/<filename>"""
    return os.path.join(
        'absentismo', 'adjuntos', 'fm',
        str(instance.informe.protocolo.pk),
        filename,
    )


def _ruta_adjunto_ssc(instance, filename):
    """Guarda en  media/absentismo/adjuntos/ssc/<protocolo_id>/<filename>"""
    return os.path.join(
        'absentismo', 'adjuntos', 'ssc',
        str(instance.informe.protocolo.pk),
        filename,
    )


class AdjuntoInformeFM(models.Model):
    informe     = models.ForeignKey(
        'InformeFM',
        on_delete=models.CASCADE,
        related_name='adjuntos',
        verbose_name='Informe FM',
    )
    descripcion = models.CharField(max_length=255, verbose_name='Descripción')
    archivo     = models.FileField(upload_to=_ruta_adjunto_fm, verbose_name='Archivo PDF')
    orden       = models.PositiveSmallIntegerField(default=0, verbose_name='Orden')
    subido_en   = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Adjunto informe FM'
        verbose_name_plural = 'Adjuntos informe FM'
        ordering            = ['orden', 'subido_en']

    def __str__(self):
        return f'{self.descripcion} ({self.informe})'

    def filename(self):
        return os.path.basename(self.archivo.name)


class AdjuntoInformeSSC(models.Model):
    informe     = models.ForeignKey(
        'InformeSSC',
        on_delete=models.CASCADE,
        related_name='adjuntos',
        verbose_name='Informe SSC',
    )
    descripcion = models.CharField(max_length=255, verbose_name='Descripción')
    archivo     = models.FileField(upload_to=_ruta_adjunto_ssc, verbose_name='Archivo PDF')
    orden       = models.PositiveSmallIntegerField(default=0, verbose_name='Orden')
    subido_en   = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Adjunto informe SSC'
        verbose_name_plural = 'Adjuntos informe SSC'
        ordering            = ['orden', 'subido_en']

    def __str__(self):
        return f'{self.descripcion} ({self.informe})'

    def filename(self):
        return os.path.basename(self.archivo.name)