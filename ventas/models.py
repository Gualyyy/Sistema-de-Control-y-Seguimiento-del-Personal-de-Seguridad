
from django.db import models
from django.db.models import Q

# Create your models here.

class cliente(models.Model):
    class TipoCliente(models.TextChoices):
        NATURAL = "NATURAL", "Persona natural"
        EMPRESA = "EMPRESA", "Empresa"

    id_cliente = models.AutoField(primary_key=True)
    nombre_razon_social = models.CharField(max_length=150)
    nombre_cliente = models.CharField(max_length=100, blank=True, default="")
    apellido_cliente = models.CharField(max_length=100, blank=True, default="")
    identificador = models.CharField(max_length=20, unique=True)
    tipo_cliente = models.CharField(max_length=20,choices=TipoCliente.choices)
    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre_razon_social} - {self.identificador}"

class contacto_cliente(models.Model):
    id_contacto = models.AutoField(primary_key=True)
    telefono = models.CharField(max_length=20)
    correo = models.EmailField(max_length=254)
    id_cliente = models.OneToOneField(cliente, on_delete=models.PROTECT, related_name="contacto")

    def __str__(self):
        return f"Contacto de {self.id_cliente}"

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
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.id_producto.nombre} - {self.precio_unitario}"

class existencia_inventario(models.Model):
    id_existencia = models.AutoField(primary_key=True)
    id_producto = models.OneToOneField(producto, on_delete=models.PROTECT, related_name="existencia")
    cantidad_actual = models.PositiveIntegerField(default=0)
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
        CONFIRMADA = "CONFIRMADA", "Confirmada"
        ANULADA = "ANULADA", "Anulada"

    id_venta = models.AutoField(primary_key=True)
    comprobante = models.CharField(max_length=30, unique=True)
    id_cliente = models.ForeignKey(cliente, on_delete=models.PROTECT, related_name="ventas")
    fecha_venta = models.DateTimeField(auto_now_add=True)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    descuento = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    impuesto = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    estado = models.CharField(max_length=15, choices=Estado.choices, default=Estado.BORRADOR)
    observacion = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(subtotal__gte=0),
                name="venta_subtotal_no_negativo"
            ),
            models.CheckConstraint(
                condition=Q(descuento__gte=0),
                name="venta_descuento_no_negativo"
            ),
            models.CheckConstraint(
                condition=Q(impuesto__gte=0),
                name="venta_impuesto_no_negativo"
            ),
            models.CheckConstraint(
                condition=Q(total__gte=0),
                name="venta_total_no_negativo"
            )
        ]

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

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(cantidad__gt=0),
                name="movimiento_cantidad_positiva"
            ),
            models.CheckConstraint(
                condition=Q(costo_unitario__gte=0),
                name="movimiento_costo_no_negativo"
            ),
            models.CheckConstraint(
                condition=Q(valor_total__gte=0),
                name="movimiento_valor_no_negativo"
            )
        ]

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
    nombre = models.CharField(max_length=50, unique=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

class pago(models.Model):
    class Estado(models.TextChoices):
        REGISTRADO = "REGISTRADO", "Registrado"
        ANULADO = "ANULADO", "Anulado"

    id_pago = models.AutoField(primary_key=True)
    id_venta = models.ForeignKey(venta, on_delete=models.PROTECT, related_name="pagos")
    id_metodo_pago = models.ForeignKey(metodo_pago, on_delete=models.PROTECT, related_name="pagos")
    monto = models.DecimalField(max_digits=14, decimal_places=2)
    fecha_pago = models.DateTimeField(auto_now_add=True)
    referencia = models.CharField(max_length=100, blank=True)
    estado = models.CharField(max_length=15, choices=Estado.choices, default=Estado.REGISTRADO)

    def __str__(self):
        return f"Pago {self.id_pago} - {self.monto}"

class categoria_gasto(models.Model):
    id_categoria_gasto = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=80, unique=True)
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

class gasto(models.Model):
    class Frecuencia(models.TextChoices):
        UNICO = "UNICO", "Único"
        SEMANAL = "SEMANAL", "Semanal"
        MENSUAL = "MENSUAL", "Mensual"
        ANUAL = "ANUAL", "Anual"

    class Estado(models.TextChoices):
        REGISTRADO = "REGISTRADO", "Registrado"
        ANULADO = "ANULADO", "Anulado"

    id_gasto = models.AutoField(primary_key=True)
    id_categoria_gasto = models.ForeignKey(categoria_gasto, on_delete=models.PROTECT, related_name="gastos")
    descripcion = models.CharField(max_length=200)
    monto = models.DecimalField(max_digits=14, decimal_places=2)
    fecha_gasto = models.DateField()
    es_recurrente = models.BooleanField(default=False)
    frecuencia = models.CharField(max_length=10, choices=Frecuencia.choices, default=Frecuencia.UNICO)
    referencia = models.CharField(max_length=100, blank=True)
    estado = models.CharField(max_length=15, choices=Estado.choices, default=Estado.REGISTRADO)
    observacion = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(monto__gt=0),
                name="gasto_monto_positivo"
            )
        ]

    def __str__(self):
        return f"{self.descripcion} - {self.monto}"
