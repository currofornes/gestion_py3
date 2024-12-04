from datetime import datetime, date
from django.db import models

# Create your models here.
from centro.models import Alumnos, Profesores, CursoAcademico


# Register your models here.

class TiposAmonestaciones(models.Model):
	TipoAmonestacion = models.CharField(max_length=60)
	TipoFalta = models.CharField(max_length=1, default='L')

	def __str__(self):
		return "("+self.TipoFalta+") "+self.TipoAmonestacion

	class Meta:
		verbose_name="Tipo Amonestación"
		verbose_name_plural="Tipos de Amonestaciones"

class Amonestaciones(models.Model):
	hora = (
		('1','Primera (1ª)'),
		('2','Segunda (2ª)'),
		('3','Tercera (3ª)'),
		('4','Recreo (REC)'),
		('5','Cuarta (4ª)'),
		('6','Quinta (5ª)'),
		('7','Sexta (6ª)'),

	)

	medios = (
		('1', 'Teléfono'),
		('2', 'PASEN'),
		('3', 'Otro'),
	)

	IdAlumno = models.ForeignKey(Alumnos,null=True,on_delete=models.SET_NULL)
	Fecha = models.DateField()
	Hora = models.CharField(max_length=1,choices=hora,default='1')
	Profesor = models.ForeignKey(Profesores, null=True, on_delete=models.SET_NULL)
	Tipo = models.ForeignKey(TiposAmonestaciones, related_name='Tipo_de', blank=True, null=True,
							 on_delete=models.SET_NULL)
	Comentario=models.TextField(blank=True)
	Enviado = models.BooleanField(default=False,verbose_name="Enviar por correo electrónico")

	DerivadoConvivencia = models.BooleanField(default=False, verbose_name="Derivado a Aula de Convivencia")

	ComunicadoFamilia = models.BooleanField(default=False, verbose_name="Comunicado a la familia")
	FamiliarComunicado = models.TextField(blank=True, null=True)
	FechaComunicado = models.DateField(blank=True, null=True)
	HoraComunicado = models.TimeField(blank=True, null=True)
	Medio = models.CharField(max_length=1, choices=medios,blank=True, null=True)
	TelefonoComunicado = models.TextField(blank=True, null=True)
	ObservacionComunicado = models.TextField(blank=True, null=True)

	curso_academico = models.ForeignKey(CursoAcademico, on_delete=models.SET_NULL, null=True, blank=True)

	def __str__(self):
		return self.IdAlumno.Nombre

	@property
	def caducada(self):
		hoy = datetime.now().date()  # Obtener la fecha de hoy

		diferencia = hoy - self.Fecha


		if self.gravedad == "Leve":
			return diferencia.days > 30
		elif self.gravedad == "Grave":
			return diferencia.days > 60
		else:
			return False

	@property
	def sancionada(self):
		ultima_sancion = Sanciones.objects.filter(IdAlumno=self.IdAlumno).order_by("Fecha").last()
		if ultima_sancion:
			return self.Fecha <= ultima_sancion.Fecha
		else:
			return False

	@property
	def gravedad(self):
		if self.Tipo and self.Tipo.TipoFalta:
			if self.Tipo.TipoFalta == "L":
				return "Leve"
			elif self.Tipo.TipoFalta == "G":
				return "Grave"
		return "Desconocida"  # Valor por defecto si Tipo o TipoFalta es None

	@property
	def vigente(self):
		return (not self.caducada) and (not self.sancionada)

	class Meta:
		verbose_name="Amonestación"
		verbose_name_plural="Amonestaciones"
		unique_together = ('IdAlumno', 'Fecha', 'Hora', 'Profesor', 'Tipo', 'Comentario', 'DerivadoConvivencia', 'FamiliarComunicado', 'FechaComunicado', 'HoraComunicado', 'Medio', 'TelefonoComunicado', 'ObservacionComunicado', 'curso_academico')


class Sanciones(models.Model):
	
	IdAlumno = models.ForeignKey(Alumnos,null=True,on_delete=models.SET_NULL)
	Fecha = models.DateField()
	Fecha_fin = models.DateField(verbose_name="Fecha finalización")
	Sancion=models.CharField(max_length=100,blank=True)
	Comentario=models.TextField(blank=True)
	NoExpulsion = models.BooleanField(default=False,verbose_name="Medidas de flexibilización a la expulsión")

	curso_academico = models.ForeignKey(CursoAcademico, on_delete=models.SET_NULL, null=True, blank=True)

	def __str__(self):
		return self.IdAlumno.Nombre 

	class Meta:
		verbose_name="Sanción"
		verbose_name_plural="Sanciones"
		unique_together = ('IdAlumno', 'Fecha', 'Fecha_fin', 'Sancion', 'Comentario', 'curso_academico')


class PropuestasSancion(models.Model):
	curso_academico = models.ForeignKey(CursoAcademico, on_delete=models.SET_NULL, null=True, blank=True)

	alumno = models.ForeignKey(Alumnos,null=True,on_delete=models.SET_NULL)
	entrada = models.DateField()
	salida = models.DateField(blank=True, null=True)
	motivo_salida = models.TextField(blank=True, null=True)
	ultima_amonestacion = models.ForeignKey(Amonestaciones,null=True,on_delete=models.SET_NULL)
	ignorar = models.BooleanField(default=False)


	def __str__(self):
		return f"Propuesta de sanción de {self.alumno} ({self.alumno.leves} leves, {self.alumno.graves} graves - peso: {self.alumno.peso_amonestaciones}"

	class Meta:
		verbose_name = "Propuesta de alumnado sancionable"
		verbose_name_plural = "Propuestas de alumnado sancionable"