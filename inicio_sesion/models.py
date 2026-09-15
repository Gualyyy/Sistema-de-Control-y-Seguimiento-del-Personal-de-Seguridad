from django.db import models

# Create your models here.
class usuarios(models.Model):
    id_usuario = models.AutoField(primary_key=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    cedula_identidad = models.CharField(unique=True, max_length=11)
    genero = models.CharField(max_length=10)
    estado_civil = models.CharField(max_length=20)

    def __str__(self):
        return self.nombres + " " + self.apellidos

class credenciales(models.Model):
    id_credenciales = models.AutoField(primary_key=True)
    nombre_usuario = models.CharField(max_length=120)
    clave = models.CharField(max_length=120)
    bloqueado = models.BooleanField(default=False)
    id_usuario = models.OneToOneField(usuarios, on_delete=models.PROTECT)

class contacto(models.Model):
    id_contacto = models.AutoField(primary_key=True)
    telefono_principal = models.CharField(max_length=12)
    telefono_secundario = models.CharField(max_length=12, null=True, blank=True)
    correo_principal = models.EmailField(max_length=30)
    correo_secundario = models.EmailField(max_length=30, null=True, blank=True)
    id_usuario = models.OneToOneField(usuarios, on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.id_usuario.nombres} {self.id_usuario.apellidos}"

class nacimiento(models.Model):
    id_nacimiento = models.AutoField(primary_key=True)
    pais = models.CharField(max_length=15)
    estado = models.CharField(max_length=50)
    municipio = models.CharField(max_length=50)
    parroquia = models.CharField(max_length=50)
    direccion = models.TextField()
    fecha_nacimiento = models.DateField(max_length=10)
    id_usuario = models.OneToOneField(usuarios, on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.id_usuario.nombres} {self.id_usuario.apellidos}"
    
class residencia(models.Model):
    id_residencia = models.AutoField(primary_key=True)
    condicion_residencia = models.CharField(max_length=20)
    municipio = models.CharField(max_length=50)
    parroquia = models.CharField(max_length=50)
    direccion = models.TextField()
    id_usuario = models.OneToOneField(usuarios, on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.id_usuario.nombres} {self.id_usuario.apellidos}"

class perfiles(models.Model):
    id_perfil = models.AutoField(primary_key=True)
    perfil = models.CharField(max_length=30, unique=True)

    def __str__(self):
        return self.perfil

class turnos_laborales(models.Model):
    id_turno = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=30, unique=True)

    def __str__(self):
            return self.nombre
    
class perfil_usuario(models.Model):
    id_perfil_usuario = models.AutoField(primary_key=True)
    id_perfil = models.ForeignKey(perfiles, on_delete=models.PROTECT, related_name="usuarios")
    id_usuario = models.ForeignKey(usuarios, on_delete=models.PROTECT, related_name="perfiles")
    id_turno = models.ForeignKey(turnos_laborales, on_delete=models.PROTECT, related_name="perfiles_usuario", blank=True, null=True)
    vigencia = models.BooleanField(default=True)
    def __str__(self):
        return (
            f"{self.id_usuario.nombres} "
            f"{self.id_usuario.apellidos} "
            f"{self.id_perfil.perfil}"
        )

class historial_perfiles_usuario(models.Model):
    id_historial = models.AutoField(primary_key=True)
    id_usuario = models.ForeignKey(usuarios, on_delete=models.PROTECT, related_name="historial_perfiles")
    id_perfil = models.ForeignKey(perfiles, on_delete=models.PROTECT, related_name="historial_asignaciones")
    id_turno = models.ForeignKey(turnos_laborales, on_delete=models.PROTECT, related_name="historial_perfiles")
    accion = models.CharField(max_length=20, choices= [
        ("ASIGNACION", "Asignación"),
        ("DESIGNACION", "Designación"),
        ("REASIGNAR", "Reasignar"),
    ])
    fecha_accion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (
            f"{self.id_usuario.nombres} "
            f"{self.id_usuario.apellidos} - "
            f"{self.id_perfil.perfil}"
        )

class categoria_equipo(models.Model):
    id_categoria = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nombre

class equipos(models.Model):
    id_equipo = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=35)
    codigo = models.CharField(max_length=30, unique=True)
    observacion = models.TextField(blank=True, null=True)
    cantidad_total = models.PositiveIntegerField(default=0)
    cantidad_disponible = models.PositiveIntegerField(default=0)
    fecha_registro = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    id_categoria = models.ForeignKey(categoria_equipo, models.PROTECT)

    def __str__(self):
        return self.nombre

# SEGURIDAD DEL SISTEMA

class bitacora(models.Model):
    id_bitacora = models.AutoField(primary_key=True)
    id_usuario = models.ForeignKey(usuarios, on_delete=models.PROTECT, related_name="bitacoras")
    fecha_hora = models.DateTimeField(auto_now_add=True)
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
    activa = models.BooleanField(default=True)
    info_general = models.CharField(max_length=255)
    direccion_ip = models.GenericIPAddressField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["usuario"],
                condition=models.Q(activa=True),
                name="una_sola_sesion_activa_por_usuario"
            )
        ]

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
