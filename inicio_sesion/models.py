from django.db import models
from django.utils import timezone

# Create your models here.

class usuarios(models.Model):
    id_usuario = models.AutoField(primary_key=True)
    tipo_usuario = models.CharField(
        max_length=15,
        choices=[
            ("NATURAL", "Persona Natural"),
            ("EMPRESA", "Empresa"),
        ]
    )
    nombre_razon_social = models.CharField(max_length=100)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    cedula_identidad = models.CharField(unique=True, max_length=15)
    genero = models.CharField(max_length=10, blank=True, null=True)
    estado_civil = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.nombres} {self.apellidos}"

class credenciales(models.Model):
    id_credenciales = models.AutoField(primary_key=True)
    nombre_usuario = models.CharField(max_length=120)
    clave = models.CharField(max_length=120)
    bloqueado = models.BooleanField(default=False)
    foto_perfil = models.ImageField(upload_to="fotos_perfil/", blank=True,  null=True)
    id_usuario = models.OneToOneField(usuarios, on_delete=models.PROTECT, related_name="credenciales")

class contacto(models.Model):
    id_contacto = models.AutoField(primary_key=True)
    telefono_principal = models.CharField(max_length=12)
    telefono_secundario = models.CharField(max_length=12, null=True, blank=True)
    correo_principal = models.EmailField(max_length=30)
    correo_secundario = models.EmailField(max_length=30, null=True, blank=True)
    id_usuario = models.OneToOneField(usuarios, on_delete=models.PROTECT, related_name="contacto")

    def __str__(self):
        return f"{self.id_usuario.nombres} {self.id_usuario.apellidos}"

class nacimiento(models.Model):
    id_nacimiento = models.AutoField(primary_key=True)
    pais = models.CharField(max_length=15)
    estado = models.CharField(max_length=50)
    municipio = models.CharField(max_length=50)
    parroquia = models.CharField(max_length=50)
    direccion = models.TextField()
    fecha_nacimiento = models.CharField(max_length=10)
    id_usuario = models.OneToOneField(usuarios, on_delete=models.PROTECT, related_name="nacimiento")

    def __str__(self):
        return f"{self.id_usuario.nombres} {self.id_usuario.apellidos}"
    
class residencia(models.Model):
    id_residencia = models.AutoField(primary_key=True)
    condicion_residencia = models.CharField(max_length=20)
    municipio = models.CharField(max_length=50)
    parroquia = models.CharField(max_length=50)
    direccion = models.TextField()
    id_usuario = models.OneToOneField(usuarios, on_delete=models.PROTECT, related_name="residencia")

    def __str__(self):
        return f"{self.id_usuario.nombres} {self.id_usuario.apellidos}"

class turnos_laborales(models.Model):
    id_turno = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=30, unique=True)

    def __str__(self):
            return self.nombre

class encargados_administrativos(models.Model):
    id_encargado = models.AutoField(primary_key=True)
    id_usuario = models.OneToOneField(usuarios, on_delete=models.PROTECT, related_name="encargado_administrativo")
    vigencia = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.id_usuario.nombres} {self.id_usuario.apellidos}"

class cliente(models.Model):
    id_cliente = models.AutoField(primary_key=True)
    id_usuario = models.OneToOneField(usuarios, on_delete=models.PROTECT, related_name="cliente")

    def __str__(self):
        return f"{self.id_usuario.nombres} {self.id_usuario.apellidos}"

class propietarios(models.Model):
    id_propietario = models.AutoField(primary_key=True)
    id_usuario = models.OneToOneField(usuarios, on_delete=models.PROTECT, related_name="propietario")

    def __str__(self):
        return f"{self.id_usuario.nombres} {self.id_usuario.apellidos}"

class atencion_cliente(models.Model):
    id_atencion_cliente = models.AutoField(primary_key=True)
    id_usuario = models.OneToOneField(usuarios, on_delete=models.PROTECT, related_name="atencion_cliente")
    vigencia = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.id_usuario.nombres} {self.id_usuario.apellidos}"

class supervisores_encargados(models.Model):
    id_supervisor = models.AutoField(primary_key=True)
    id_usuario = models.OneToOneField(usuarios, on_delete=models.PROTECT, related_name="supervisor")
    id_turno = models.ForeignKey(turnos_laborales, on_delete=models.PROTECT, related_name="supervisores")
    vigencia = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.id_usuario.nombres} {self.id_usuario.apellidos}"
    
class personal_limpieza(models.Model):
    id_personal = models.AutoField(primary_key=True)
    id_usuario = models.OneToOneField(usuarios, on_delete=models.PROTECT, related_name="personal_limpieza")
    id_turno = models.ForeignKey(turnos_laborales, on_delete=models.PROTECT, related_name="personal_limpieza")
    vigencia = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.id_usuario.nombres} {self.id_usuario.apellidos}"

class despachadores(models.Model):
    id_despachador = models.AutoField(primary_key=True)
    id_usuario = models.OneToOneField(usuarios, on_delete=models.PROTECT, related_name="despachador")
    id_turno = models.ForeignKey(turnos_laborales, on_delete=models.PROTECT, related_name="despachadores")
    vigencia = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.id_usuario.nombres} {self.id_usuario.apellidos}"
    
class vigilantes(models.Model):
    id_vigilante = models.AutoField(primary_key=True)
    id_usuario = models.OneToOneField(usuarios, on_delete=models.PROTECT, related_name="vigilante")
    id_turno = models.ForeignKey(turnos_laborales, on_delete=models.PROTECT, related_name="vigilantes")
    vigencia = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.id_usuario.nombres} {self.id_usuario.apellidos}"

# GASTOS DE LA EMPRESA

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

    def __str__(self):
        return f"{self.descripcion} - {self.monto}"

# SEGURIDAD DEL SISTEMA

class informacion_contacto(models.Model):
    id_contacto = models.AutoField(primary_key=True)
    direccion = models.TextField()
    telefono = models.CharField(max_length=15)
    correo_electronico = models.CharField(max_length=50)

class imagenes_publicitaria(models.Model):
    id_imagen = models.AutoField(primary_key=True)
    imagen = models.ImageField(upload_to="imagenes_publicitarias/", null=True, blank=True)
    titulo = models.CharField(max_length=150, null=True, blank=True)
    texto = models.TextField(null=True, blank=True)
    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Imagen del carrusel - {self.id_imagen}"

class bitacora(models.Model):
    id_bitacora = models.AutoField(primary_key=True)
    id_usuario = models.ForeignKey(usuarios, on_delete=models.PROTECT, related_name="bitacoras")
    fecha_hora = models.DateTimeField(auto_now_add=True)
    nombre_modulo = models.CharField(max_length=100, default="No especificado")
    cargo_usuario = models.CharField(max_length=80, default="No especificado")
    accion = models.TextField(max_length=100)

    def __str__(self):
        return (
            f"{self.id_usuario.nombres} "
            f"{self.id_usuario.apellidos} - "
            f"{self.accion}"
        )
    
class sesiones_usuario(models.Model):
    id_sesion = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(usuarios, on_delete=models.CASCADE, related_name="sesiones")
    session_key = models.CharField(max_length=50, unique=True)
    tab_id = models.CharField(max_length=100, null=True, blank=True)
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_fin = models.DateTimeField(null=True, blank=True)
    ultima_actividad = models.DateTimeField(default=timezone.now)
    activa = models.BooleanField(default=True)
    info_general = models.CharField(max_length=255)
    direccion_ip = models.GenericIPAddressField()

class sesiones_recuperacion(models.Model):
    tab_id = models.CharField(max_length=100, unique=True)
    session_key = models.CharField(max_length=50, unique=True)
    actualizado = models.DateTimeField(auto_now=True)

class intentos_inicio_sesion(models.Model):
    id_intento = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(usuarios, on_delete=models.SET_NULL, null=True, blank=True, related_name="intentos_inicio_sesion")
    nombre_usuario = models.CharField(max_length=50)
    direccion_ip = models.GenericIPAddressField()
    exitoso = models.BooleanField(default=False)
    fecha_hora = models.DateTimeField(auto_now_add=True)

class bloqueo_inicio_sesion(models.Model):
    id_bloqueo = models.AutoField(primary_key=True)
    usuario = models.OneToOneField(usuarios, on_delete=models.CASCADE, related_name="bloqueo_inicio_sesion")
    intentos = models.PositiveSmallIntegerField(default=0)
    bloqueado = models.BooleanField(default=False)
    bloqueado_hasta = models.DateTimeField(null=True, blank=True)
    ultima_direccion_ip = models.GenericIPAddressField(null=True, blank=True)
    ultimo_intento = models.DateTimeField(auto_now=True)

class autenticar_codigo(models.Model):
    id_codigo = models.AutoField(primary_key=True)
    cedula_identidad = models.CharField(max_length=12)
    token = models.CharField(max_length=255, null=True, blank=True)
    codigo = models.CharField(max_length=10)
    creado = models.DateTimeField(auto_now_add=True)
    intentos = models.PositiveIntegerField(default=0)
    numero_reenvios = models.PositiveIntegerField(default=0)
    bloqueado_hasta = models.DateTimeField(null=True, blank=True)
    activo = models.BooleanField(default=True)
    descripcion = models.CharField(max_length=100)
    fecha_expiracion = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.cedula_identidad