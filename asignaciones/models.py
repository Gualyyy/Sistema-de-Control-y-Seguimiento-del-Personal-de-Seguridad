from django.db import models

from inicio_sesion.models import usuarios, supervisores_encargados

# Create your models here.

class categoria_equipo(models.Model):
    id_categoria = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nombre

class equipos(models.Model):
    id_equipo = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=35)
    codigo = models.CharField(max_length=30, unique=True)
    observacion = models.TextField()
    cantidad_disponible = models.PositiveIntegerField(default=0)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    id_categoria = models.ForeignKey(categoria_equipo, models.PROTECT, related_name="equipos")

    def __str__(self):
        return self.nombre

class historial_inventario_equipo(models.Model):
    id_historial = models.AutoField(primary_key=True)
    id_equipo = models.ForeignKey(equipos, on_delete=models.PROTECT, related_name="historial_inventario")
    tipo_movimiento = models.CharField(
        max_length=20,
        choices=[
            ("REGISTRO", "Registro inicial"),
            ("REPOSICION", "Reposición"),
            ("ENTREGA", "Entrega a supervisor"),
            ("CORRECCION", "Corrección de inventario"),
            ("BAJA", "Baja de inventario"),
        ]
    )

    cantidad_anterior = models.PositiveIntegerField()
    cantidad_movimiento = models.IntegerField(default=0)
    cantidad_nueva = models.PositiveIntegerField()
    
    activo_anterior = models.BooleanField(blank=True, null=True)
    activo_nuevo = models.BooleanField(blank=True, null=True)

    observacion = models.TextField(blank=True, default="")
    fecha_movimiento = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (
            f"{self.id_equipo.nombre} - "
            f"{self.get_tipo_movimiento_display()} - "
            f"{self.fecha_movimiento:%d/%m/%Y %H:%M}"
        )

class entrega_equipos(models.Model):
    id_entrega = models.AutoField(primary_key=True)
    supervisor_encargado = models.ForeignKey(supervisores_encargados, on_delete=models.PROTECT, related_name="equipos_recibidos_supervisor")
    id_equipo = models.ForeignKey(equipos, on_delete=models.PROTECT, related_name="entregas_supervisores")

    cantidad_entregada = models.PositiveIntegerField(default=1)
    cantidad_disponible = models.PositiveIntegerField(default=0)

    fecha_entrega = models.DateTimeField(auto_now_add=True)
    observacion = models.TextField(blank=True, default="")

    estado = models.CharField(
        max_length=20,
        choices=[
            ("ASIGNADO", "Asignado"),
            ("DAÑADO", "Dañado"),
            ("DETERIORADO", "Deteriorado"),
        ],
        default="ASIGNADO"
    )
    motivo_incidencia = models.CharField(
        max_length=20,
        choices=[
            ("NINGUNA", "Sin incidencia"),
            ("ERROR_HUMANO", "Error Humano"),
        ],
        default="NINGUNA"
    )

    def __str__(self):
        return (
            f"{self.supervisor_encargado.id_usuario.nombres} "
            f"{self.supervisor_encargado.id_usuario.apellidos} - "
            f"{self.id_equipo.nombre}"
        )

class historial_entrega_equipo(models.Model):
    id_historial = models.AutoField(primary_key=True)
    entrega_equipo = models.ForeignKey(entrega_equipos, on_delete=models.PROTECT, related_name="historial_actualizaciones")

    cantidad_entregada_anterior = models.PositiveIntegerField()
    cantidad_entregada_nueva = models.PositiveIntegerField()

    cantidad_disponible_anterior = models.PositiveIntegerField()
    cantidad_disponible_nueva = models.PositiveIntegerField()

    estado_anterior = models.CharField(max_length=20)
    estado_nuevo = models.CharField(max_length=20)

    motivo_incidencia_anterior = models.CharField(max_length=20)
    motivo_incidencia_nuevo = models.CharField(max_length=20)

    observacion_anterior = models.TextField(blank=True, default="")
    observacion_nueva = models.TextField(blank=True, default="")

    motivo_actualizacion = models.TextField()

    fecha_actualizacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (
            f"{self.id_historial} "
            f"{self.entrega_equipo.id_equipo.nombre}"
        )

class asignacion_equipo(models.Model):
    id_asignacion = models.AutoField(primary_key=True)
    id_entrega = models.ForeignKey(entrega_equipos, on_delete=models.PROTECT, related_name="asignaciones_personal")
    id_usuario = models.ForeignKey(usuarios, on_delete=models.PROTECT, related_name="asignaciones_equipo")
    fecha_entrega = models.DateTimeField(auto_now_add=True)
    fecha_devolucion = models.DateTimeField(blank=True, null=True)
    observacion = models.TextField(blank=True, default="")
    cantidad_asignada = models.PositiveIntegerField(default=1)
    cantidad_devuelta = models.PositiveIntegerField(default=0)
    estado = models.CharField(
        max_length=15,
        choices=[
            ("ASIGNADO", "Asignado"),
            ("PARCIAL", "Parcial"),
            ("FINALIZADO", "Finalizado"),
        ],
        default="ASIGNADO"
    )
    motivo_incidencia = models.CharField(
        max_length=20,
        choices=[
            ("NINGUNA", "Sin incidencia"),
            ("ERROR_HUMANO", "Error humano"),
        ],
        default="NINGUNA"
    )

    def __str__(self):
        return (
            f"{self.id_usuario.nombres} "
            f"{self.id_usuario.apellidos} "
            f"{self.id_entrega.id_equipo.nombre}"
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
            ("BUEN_ESTADO", "Buen estado"),
            ("DETERIORADO", "Deteriorado"),
            ("DAÑADO", "Dañado"),
        ]
    )
    motivo_incidencia = models.CharField(
        max_length=20,
        choices=[
            ("NINGUNA", "Sin incidencia"),
            ("ERROR_HUMANO", "Error humano"),
        ],
        default="NINGUNA"
    )
    observacion = models.TextField(blank=True, default="")
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (
            f"{self.id_movimiento} "
            f"{self.id_asignacion.id_usuario.nombres} "
            f"{self.id_asignacion.id_usuario.apellidos} "
            f"{self.id_asignacion.id_entrega.id_equipo.nombre}"
        )
