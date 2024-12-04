from django.contrib.auth.models import User
from django.db import models

from gestion import settings


# Create your models here.

class CursoAcademico(models.Model):
    nombre = models.CharField(max_length=100)
    año_inicio = models.IntegerField(null=True,blank=True)
    año_fin = models.IntegerField(null=True,blank=True)

    def __str__(self):
        return f"{self.nombre} ({self.año_inicio}-{self.año_fin})"


class Aulas(models.Model):
    Aula = models.CharField(max_length=30)
    AulaHorarios = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return self.Aula

    class Meta:
        verbose_name = "Aula"
        verbose_name_plural = "Aulas"


class Departamentos(models.Model):
    Abr = models.CharField(max_length=4)
    Nombre = models.CharField(max_length=30)

    def __str__(self):
        return self.Nombre

    class Meta:
        verbose_name = "Departamento"
        verbose_name_plural = "Departamentos"


class Areas(models.Model):
    Nombre = models.CharField(max_length=30)
    Departamentos = models.ManyToManyField(Departamentos, blank=True)

    def __str__(self):
        return self.Nombre

    class Meta:
        verbose_name = "Área"
        verbose_name_plural = "Áreas"


class Profesores(models.Model):
    # Curro Jul 24: Anado user para vincular Profesor con user de la web
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='profesor')
    Nombre = models.CharField(max_length=20)
    Apellidos = models.CharField(max_length=30)
    DNI = models.CharField(max_length=10, blank=True)
    Telefono = models.CharField(max_length=9, blank=True)
    Movil = models.CharField(max_length=9, blank=True)
    Email = models.EmailField()
    Departamento = models.ForeignKey(Departamentos, blank=True, null=True, on_delete=models.SET_NULL)
    Baja = models.BooleanField(default=False)
    password_changed = models.BooleanField(default=False)  # Nuevo campo
    NombreHorarios = models.CharField(max_length=200, blank=True, null=True)
    SustitutoDe = models.ForeignKey('self',on_delete=models.SET_NULL,null=True,blank=True,related_name='sustitutos',verbose_name="Sustituto de")


    # Curro Jul 24: Anado la coma entre los apellidos y el nombre
    def __str__(self):
        return self.Apellidos + ", " + self.Nombre

    class Meta:
        verbose_name = "Profesor"
        verbose_name_plural = "Profesores"
        ordering = ("Apellidos",)

    @property
    def nombre_completo(self):
        return self.Apellidos + ", " + self.Nombre


class Niveles(models.Model):
    Nombre = models.CharField(max_length=255)
    Abr = models.CharField(max_length=50)

    def __str__(self):
        return self.Abr

    class Meta:
        verbose_name = "Nivel"
        verbose_name_plural = "Niveles"


class Cursos(models.Model):
    Curso = models.CharField(max_length=30)
    Tutor = models.ForeignKey(Profesores, related_name='Tutor_de', blank=True, null=True, on_delete=models.SET_NULL)
    EquipoEducativo = models.ManyToManyField(Profesores, verbose_name="Equipo Educativo", blank=True)
    Abe = models.CharField(max_length=10, blank=True, null=True)
    Nivel = models.ForeignKey(Niveles, related_name='Nivel', blank=True, null=True, on_delete=models.SET_NULL)
    Aula = models.ForeignKey(Aulas, related_name='Curso', blank=True, null=True, on_delete=models.SET_NULL)
    CursoHorarios = models.CharField(max_length=100, blank=True, null=True)
    Dificultad = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return self.Curso

    def __lt__(self, other):
        # Comparar los cursos según su 'id' o el campo que prefieras para la ordenación
        if isinstance(other, Cursos):
            return self.id < other.id
        return NotImplemented

    class Meta:
        verbose_name = "Curso"
        verbose_name_plural = "Cursos"
        ordering = ['id']


class Alumnos(models.Model):
    Nombre = models.CharField(max_length=50)
    NIE = models.CharField(max_length=20, blank=True, null=True)
    DNI = models.CharField(max_length=10, blank=True, null=True)
    Direccion = models.CharField(max_length=60)
    CodPostal = models.CharField(max_length=5, verbose_name="Código postal")
    Localidad = models.CharField(max_length=30)
    Fecha_nacimiento = models.DateField('Fecha de nacimiento')
    Provincia = models.CharField(max_length=30)
    Unidad = models.ForeignKey(Cursos, blank=True, null=True, on_delete=models.SET_NULL)
    Ap1tutor = models.CharField(max_length=20, verbose_name="Apellido 1 Tutor")
    Ap2tutor = models.CharField(max_length=20, verbose_name="Apellido 2 Tutor")
    Nomtutor = models.CharField(max_length=20, verbose_name="Nombre tutor")
    Telefono1 = models.CharField(max_length=12, blank=True)
    Telefono2 = models.CharField(max_length=12, blank=True)
    email = models.EmailField(max_length=70, blank=True)
    Obs = models.TextField(blank=True, verbose_name="Observaciones")
    PDC = models.BooleanField(default=False)
    NEAE = models.BooleanField(default=False)

    def __str__(self):
        dni = self.DNI if self.DNI else "Sin DNI"
        return dni + " - " + self.Nombre

    @property
    def amonestaciones_leves_vigentes(self):
        return [am for am in self.amonestaciones_set.order_by("Fecha").all() if am.gravedad == "Leve" and am.vigente]

    @property
    def amonestaciones_graves_vigentes(self):
        return [am for am in self.amonestaciones_set.order_by("Fecha").all() if am.gravedad == "Grave" and am.vigente]

    @property
    def leves(self):
        return len(self.amonestaciones_leves_vigentes)

    @property
    def graves(self):
        return len(self.amonestaciones_graves_vigentes)

    @property
    def sancionable(self):
        return self.peso_amonestaciones >= 6

    @property
    def peso_amonestaciones(self):
        return self.leves + 2 * self.graves

    @property
    def ultima_sancion(self ):
        return self.sanciones_set.order_by("Fecha").last()

    class Meta:
        verbose_name = "Alumno"
        verbose_name_plural = "Alumnos"
