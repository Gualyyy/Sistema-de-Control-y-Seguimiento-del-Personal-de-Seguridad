from django.db import models

from inicio_sesion.models import perfil_usuario

# Create your models here.
class tipo_incidencia(models.Model):
    id_tipo = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nombre

class incidencia(models.Model):
    id_incidencia = models.AutoField(primary_key=True)
    id_perfil_usuario = models.ForeignKey(perfil_usuario, on_delete=models.PROTECT)
    id_tipo = models.ForeignKey(tipo_incidencia, on_delete=models.PROTECT)
    fecha_hora = models.DateTimeField(blank=True, null=True)
    titulo = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    estado = models.CharField(
        max_length=15,
        choices=[
            ("Pendiente", "Pendiente"),
            ("Modificada", "Modificada"),
            ("Aceptada", "Aceptada"),
            ("En proceso", "En proceso"),
            ("Resuelta", "Resuelta"),
        ],
        default="Pendiente"
    )
    solucion = models.TextField(blank=True, null=True)
    fecha_resolucion = models.DateTimeField(blank=True, null=True)
    id_usuario_acepta = models.ForeignKey(perfil_usuario, on_delete=models.PROTECT, related_name="incidencias_aceptadas", blank=True, null=True)

    def __str__(self):
        return (
            f"{self.id_perfil_usuario.id_usuario.nombres} "
            f"{self.id_perfil_usuario.id_usuario.apellidos} - "
            f"{self.titulo}"
        )

class solucion_incidencia(models.Model):
    id_solucion = models.AutoField(primary_key=True)
    id_incidencia = models.ForeignKey(incidencia, on_delete=models.PROTECT, related_name="soluciones")
    id_perfil_usuario = models.ForeignKey(perfil_usuario, on_delete=models.PROTECT, related_name="soluciones_incidencias")
    estado = models.CharField(
        max_length=15,
        choices=[
            ("Pendiente", "Pendiente"),
            ("Modificada", "Modificada"),
            ("Aceptada", "Aceptada"),
            ("En proceso", "En proceso"),
            ("Resuelta", "Resuelta"),
        ]
    )
    descripcion = models.TextField()
    fecha_hora = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (
            f"{self.id_incidencia.titulo} - "
            f"{self.id_perfil_usuario.id_usuario.nombres} "
            f"{self.id_perfil_usuario.id_usuario.apellidos}"
        )