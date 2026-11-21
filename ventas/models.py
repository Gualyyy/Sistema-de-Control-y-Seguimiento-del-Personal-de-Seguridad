
from django.db import models
from django.db.models import Q

from inicio_sesion.models import cliente

# Create your models here.

class categoria_producto(models.Model):
    id_categoria = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50, unique=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

class unidad_medida(models.Model):
    id_unidad = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50, unique=True)
    abreviatura = models.CharField(max_length=10, unique=True)
    permite_decimales = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} {self.abreviatura}"

class producto(models.Model):
    id_producto = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=50, unique=True)
    precio_base = models.DecimalField(max_digits=12, decimal_places=2)
    costo_base = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    imagen = models.ImageField(upload_to="productos/", blank=True, null=True)
    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    id_categoria = models.ForeignKey(categoria_producto, on_delete=models.PROTECT, related_name="productos")
    id_unidad = models.ForeignKey(unidad_medida, on_delete=models.PROTECT, related_name="productos")

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(precio_base__gte=0),
                name="producto_precio_no_negativo"
            ),
            models.CheckConstraint(
                condition=Q(costo_base__gte=0),
                name="producto_costo_no_negativo"
            )
        ]

    def __str__(self):
        return f"{self.nombre} {self.codigo}"

class precio_volumen(models.Model):
    id_precio_volumen = models.AutoField(primary_key=True)
    id_producto = models.ForeignKey(producto, on_delete=models.PROTECT, related_name="precios_volumen", null=True, blank=True)
    cantidad_minima = models.PositiveIntegerField(null=True, blank=True)
    cantidad_maxima = models.PositiveIntegerField(null=True, blank=True)
    porcentaje_descuento = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(porcentaje_descuento__gte=0, porcentaje_descuento__lte=100),
                name="precio_volumen_descuento_porcentaje_valido"
            )
        ]

    def __str__(self):
        return f"{self.id_producto.nombre} - {self.porcentaje_descuento}%"

class existencia_inventario(models.Model):
    id_existencia = models.AutoField(primary_key=True)
    id_producto = models.OneToOneField(producto, on_delete=models.PROTECT, related_name="existencia", blank=True, null=True)
    cantidad_actual = models.DecimalField(max_digits=12, decimal_places=0, default=0, blank=True, null=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.id_producto.nombre}: {self.cantidad_actual}"

class tipo_movimiento(models.Model):
    class Direccion(models.TextChoices):
        ENTRADA = "ENTRADA", "Entrada"
        SALIDA = "SALIDA", "Salida"

    id_tipo_movimiento = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50, unique=True)
    direccion = models.CharField(max_length=10, choices=Direccion.choices)
    es_perdida = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

class venta(models.Model):
    class Estado(models.TextChoices):
        BORRADOR = "BORRADOR", "Borrador"
        PENDIENTE_CONFIRMACION = "PENDIENTE_CONFIRMACION", "Pendiente de confirmación"
        CONFIRMADA = "CONFIRMADA", "Confirmada"
        RECHAZADA = "RECHAZADA", "Rechazada"
        ANULADA = "ANULADA", "Anulada"

    class MotivoRechazo(models.TextChoices):
        COMPROBANTE_INVALIDO = "COMPROBANTE_INVALIDO", "Comprobante de pago inválido o ilegible."
        PAGO_NO_VERIFICADO = "PAGO_NO_VERIFICADO", "Pago no recibido o no verificado."
        MONTO_INCORRECTO = "MONTO_INCORRECTO", "El monto del pago no coincide con el total de la venta."
        COMPROBANTE_DUPLICADO = "COMPROBANTE_DUPLICADO", "Comprobante de pago duplicado."
        DATOS_INCORRECTOS = "DATOS_INCORRECTOS", "Datos del pago incorrectos."
        CUENTA_INCORRECTA = "CUENTA_INCORRECTA", "El pago fue realizado a una cuenta bancaria incorrecta."

    id_venta = models.AutoField(primary_key=True)
    comprobante = models.CharField(max_length=30, unique=True)
    id_cliente = models.ForeignKey(cliente, on_delete=models.PROTECT, related_name="ventas")
    fecha_venta = models.DateTimeField(auto_now_add=True)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    descuento = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    impuesto = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tasa_cambio = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    estado = models.CharField(max_length=25, choices=Estado.choices, default=Estado.BORRADOR)
    observacion = models.TextField(blank=True)
    motivo_rechazo = models.CharField(
        max_length=30,
        choices=MotivoRechazo.choices,
        blank=True,
        default="",
    )
    inventario_descontado = models.BooleanField(default=False)

    def __str__(self):
        return self.comprobante

class movimiento_inventario(models.Model):
    id_movimiento = models.AutoField(primary_key=True)
    id_producto = models.ForeignKey(producto, on_delete=models.PROTECT, related_name="movimientos_inventario")
    id_venta = models.ForeignKey(venta, on_delete=models.PROTECT, related_name="movimientos_inventario", null=True, blank=True)
    id_tipo_movimiento = models.ForeignKey(tipo_movimiento, on_delete=models.PROTECT, related_name="movimientos")
    cantidad = models.DecimalField(max_digits=12, decimal_places=3)

    # Costo unitario histórico al registrar el movimiento.
    costo_unitario = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Valor histórico del inventario afectado.
    valor_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    fecha_movimiento = models.DateTimeField(auto_now_add=True)
    motivo = models.TextField(blank=True)

    # Referencia a un movimiento original, si se revierte.
    reverso_de = models.ForeignKey("self", on_delete=models.PROTECT, related_name="reversiones", null=True, blank=True)

    def __str__(self):
        return (
            f"{self.id_tipo_movimiento.nombre} - "
            f"{self.id_producto.nombre} - {self.cantidad}"
        )

class detalle_venta(models.Model):
    id_detalle = models.AutoField(primary_key=True)
    id_venta = models.ForeignKey(venta, on_delete=models.PROTECT, related_name="detalles")
    id_producto = models.ForeignKey(producto, on_delete=models.PROTECT, related_name="detalles_venta")
    cantidad = models.DecimalField(max_digits=12, decimal_places=3)

    precio_unidad = models.DecimalField(max_digits=12, decimal_places=2)
    descuento = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2)

    # Copia histórica del costo por unidad al vender.
    costo_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    costo_total = models.DecimalField(max_digits=14, decimal_places=2)

    def __str__(self):
        return f"{self.id_venta.comprobante} - {self.id_producto.nombre}"

class metodo_pago(models.Model):
    id_metodo_pago = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50, unique=True,null=True, blank=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

class cuenta_destino_pago(models.Model):
    class TipoCuenta(models.TextChoices):
        CORRIENTE = "CORRIENTE", "Corriente"
        AHORRO = "AHORRO", "Ahorro"

    id_cuenta_destino = models.AutoField(primary_key=True)
    id_metodo_pago = models.ForeignKey(metodo_pago, on_delete=models.PROTECT, related_name="cuentas_destino")
    banco = models.CharField(max_length=100)
    documento = models.CharField(max_length=20)
    telefono = models.CharField(max_length=20, blank=True)
    numero_cuenta = models.CharField(max_length=30, blank=True)
    tipo_cuenta = models.CharField(max_length=15, choices=TipoCuenta.choices, blank=True)
    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.banco} - {self.id_metodo_pago.nombre}"

class pago(models.Model):
    class Estado(models.TextChoices):
        REGISTRADO = "REGISTRADO", "Registrado"
        ANULADO = "ANULADO", "Anulado"

    id_pago = models.AutoField(primary_key=True)
    id_venta = models.ForeignKey(venta, on_delete=models.PROTECT, related_name="pagos")
    id_cuenta_destino = models.ForeignKey(cuenta_destino_pago, on_delete=models.PROTECT, related_name="pagos", null=True, blank=True)
    id_metodo_pago = models.ForeignKey(metodo_pago, on_delete=models.PROTECT, related_name="pagos")
    monto = models.DecimalField(max_digits=14, decimal_places=2)
    fecha_pago = models.DateTimeField(auto_now_add=True)
    referencia = models.CharField(max_length=100, blank=True)
    capture_pago = models.FileField(upload_to="captures_pago/", blank=True, null=True)
    telefono_origen = models.CharField(max_length=15, blank=True)
    fecha_pago_bancario = models.DateField(null=True, blank=True)
    banco_origen = models.CharField(max_length=100, blank=True)
    estado = models.CharField(max_length=15, choices=Estado.choices, default=Estado.REGISTRADO)

    def __str__(self):
        return f"Pago {self.id_pago} - {self.monto}"
