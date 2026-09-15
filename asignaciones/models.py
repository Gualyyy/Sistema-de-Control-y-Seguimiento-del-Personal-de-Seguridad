from django.db import models

from inicio_sesion.models import perfil_usuario, equipos, usuarios

# Create your models here.

class asignacion_equipo(models.Model):
    id_asignacion = models.AutoField(primary_key=True)
    id_perfil_usuario = models.ForeignKey(perfil_usuario, on_delete=models.PROTECT, related_name="asignaciones_equipo", blank=True, null=True)
    id_equipo = models.ForeignKey(equipos, on_delete=models.PROTECT, related_name="asignaciones")
    fecha_entrega = models.DateTimeField(auto_now_add=True)
    fecha_devolucion = models.DateTimeField(blank=True, null=True)
    observacion = models.TextField()
    cantidad_asignada = models.PositiveIntegerField(default=1)
    cantidad_devuelta = models.PositiveIntegerField(default=0)
    estado = models.CharField(max_length=15,
        choices=[
            ("Asignado", "Asignado"),
            ("Parcial", "Parcial"),
            ("Finalizado", "Finalizado"),
            ("Error_Humano", "Error Humano"),
        ],
        default="Asignado"
    )

    def __str__(self):
        return (
            f"{self.id_perfil_usuario.id_usuario.nombres} "
            f"{self.id_perfil_usuario.id_usuario.apellidos} - "
            f"{self.id_equipo.nombre}"
        )

class movimiento_equipo(models.Model):
    id_movimiento = models.AutoField(primary_key=True)
    id_asignacion = models.ForeignKey(asignacion_equipo, on_delete=models.PROTECT, related_name="movimientos")
    usuario_registro = models.ForeignKey(usuarios, on_delete=models.PROTECT, related_name="movimientos_registrados")
    cantidad = models.PositiveIntegerField()
    tipo = models.CharField(
        max_length=20,
        choices=[
            ("DEVOLUCION", "Devolución"),
            ("CORRECCION", "Corrección"),
        ]
    )
    estado = models.CharField(
        max_length=20,
        choices=[
            ("DEVUELTO", "Devuelto"),
            ("DAÑADO", "Dañado"),
            ("HURTADO", "Hurtado"),
            ("EXTRAVIADO", "Extraviado"),
            ("ERROR_HUMANO", "Error Humano"),
        ]
    )
    fecha = models.DateTimeField(auto_now_add=True)
