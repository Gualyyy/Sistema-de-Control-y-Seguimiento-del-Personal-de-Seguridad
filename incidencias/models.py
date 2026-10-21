from django.db import models

from inicio_sesion.models import supervisores_encargados, vigilantes, turnos_laborales

# Create your models here.

class tipo_incidencia(models.Model):
    id_tipo = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nombre
    
class incidencia(models.Model):
    id_incidencia = models.AutoField(primary_key=True)
    id_supervisor = models.ForeignKey(supervisores_encargados, on_delete=models.PROTECT, related_name="incidencias_registradas")
    id_turno = models.ForeignKey(turnos_laborales, on_delete=models.PROTECT, related_name="incidencias")
    id_tipo = models.ForeignKey(tipo_incidencia, on_delete=models.PROTECT, related_name="incidencias")
    fecha_hora = models.DateTimeField(auto_now_add=True)
    titulo = models.CharField(max_length=100)
    descripcion = models.TextField()
    solucion = models.TextField(blank=True, default="")
    fecha_cierre = models.DateTimeField(blank=True, null=True)
    varios_vigilantes = models.ManyToManyField(vigilantes, through="vigilante_incidencia", related_name="incidencias_atendidas", blank=True)

    def __str__(self):
        return f"{self.titulo} - {self.get_estado_display()}"

class vigilante_incidencia(models.Model):
    id_vigilante_incidencia = models.AutoField(primary_key=True)
    id_incidencia = models.ForeignKey(incidencia, on_delete=models.PROTECT, related_name="vigilantes_asignados")
    id_vigilante = models.ForeignKey(vigilantes, on_delete=models.PROTECT, related_name="asignaciones_incidencias")

    def __str__(self):
        return (
            f"{self.id_incidencia.titulo} - "
            f"{self.id_vigilante.id_usuario.nombres} "
            f"{self.id_vigilante.id_usuario.apellidos}"
        )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["id_incidencia", "id_vigilante"],
                name="uq_vigilante_incidencia"
            )
        ]