import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone

from centro.models import (
    Cursos, MateriaImpartida, LibroTexto, MatriculaMateria, EstadoLibro,
    RevisionLibro, RevisionLibroAlumno, MomentoRevisionLibros
)
from centro.utils import get_current_academic_year


class Command(BaseCommand):
    help = "Genera revisiones de libros aleatorias para cada curso con libro asignado"

    def handle(self, *args, **options):
        curso_actual = get_current_academic_year()
        momentos = list(MomentoRevisionLibros.objects.all())
        estados = list(EstadoLibro.objects.all())

        if not momentos or not estados:
            self.stdout.write(self.style.ERROR("❌ Faltan momentos o estados. Aborta."))
            return

        total = 0
        for curso in Cursos.objects.all():
            materias_impartidas = MateriaImpartida.objects.filter(curso=curso)

            for mi in materias_impartidas:
                materia = mi.materia
                profesor = mi.profesor
                libro_qs = LibroTexto.objects.filter(materia=materia, nivel=curso.Nivel)

                if not libro_qs.exists():
                    continue  # Saltar si no hay libro asignado

                if profesor.Baja:
                    continue

                libro = libro_qs.first()
                momento = random.choice(momentos)
                fecha = timezone.now() - timedelta(days=random.randint(0, 30))

                revision = RevisionLibro.objects.create(
                    profesor=profesor,
                    materia=materia,
                    libro=libro,
                    momento=momento,
                    curso=curso,
                    curso_academico=curso_actual,
                    fecha=fecha
                )

                # Buscar alumnado matriculado en esa materia en ese curso
                alumnos = MatriculaMateria.objects.filter(
                    materia_impartida=mi
                ).values_list('alumno', flat=True).distinct()

                for alumno_id in alumnos:
                    estado = random.choice(estados)
                    RevisionLibroAlumno.objects.create(
                        revision=revision,
                        alumno_id=alumno_id,
                        estado=estado,
                        observaciones=random.choice(["", "Portada rota", "Sin forro", "Muy buen estado"])
                    )

                total += 1
                self.stdout.write(f"📝 Revisión generada para {curso} - {materia} ({len(alumnos)} alumnos)")

        self.stdout.write(self.style.SUCCESS(f"\n✅ {total} revisiones generadas."))
