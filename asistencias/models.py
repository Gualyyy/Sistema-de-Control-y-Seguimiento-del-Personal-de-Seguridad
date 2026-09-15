from django.db import models

from inicio_sesion.models import usuarios, perfiles, turnos_laborales

# Create your models here.
class horario_establecido(models.Model):
    id_horario = models.AutoField(primary_key=True)
    id_perfil = models.ForeignKey(perfiles, on_delete=models.PROTECT, related_name="horarios")
    id_turno = models.ForeignKey(turnos_laborales, on_delete=models.PROTECT, related_name="horarios")
    hora_entrada = models.TimeField()
    hora_salida = models.TimeField()
    tolerancia = models.PositiveIntegerField(default=10)
    activo = models.BooleanField(default=True)

    @property
    def es_nocturno(self):
        return self.hora_salida < self.hora_entrada

    def __str__(self):
        return (
            f"{self.id_perfil.perfil} - "
            f"{self.id_turno.nombre} - "
            f"{self.hora_entrada} / "
            f"{self.hora_salida}"
        )
    
class asistencia(models.Model):
    id_asistencia = models.AutoField(primary_key=True)
    id_usuario = models.ForeignKey(usuarios, on_delete=models.PROTECT, related_name="asistencias")
    id_horario = models.ForeignKey(horario_establecido, on_delete=models.PROTECT, related_name="asistencias")

    fecha = models.DateField()

    hora_entrada = models.TimeField(blank=True, null=True)
    hora_salida = models.TimeField(blank=True, null=True)

    estado = models.CharField(
        max_length=20,
        choices=[
            ('Presente', 'Presente'),
            ('Ausente', 'Ausente'),
            ('Permiso', 'Permiso'),
            ('Reposo', 'Reposo'),
            ('Retardo', 'Retardo'),
        ]
    )
    observacion = models.TextField(blank=True, null=True)

    def __str__(self):
        return (
            f"{self.id_usuario.nombres} "
            f"{self.id_usuario.apellidos} - "
            f"{self.fecha}"
        )
