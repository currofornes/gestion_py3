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

	class Meta:
		verbose_name="Amonestación"
		verbose_name_plural="Amonestaciones"


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