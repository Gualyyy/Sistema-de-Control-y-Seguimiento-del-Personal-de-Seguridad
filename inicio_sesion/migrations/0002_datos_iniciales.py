from django.db import migrations

PERFIL = (
    ("Administrador(a)", "Administrador(a)"),
    ("Supervisor Encargado", "Supervisor Encargado"),
    ("Personal de Limpieza", "Personal de Limpieza"),
    ("Despachador", "Despachador"),
    ("Vigilante", "Vigilante"),
)

TURNO_LABORAL = [
    ("Diurno", "Diurno"),
    ("Nocturno", "Nocturno"),
]

CATEGORIA_EQUIPO = [
    ("Uniforme", "Uniforme"),
    ("Herramientas", "Herramientas"),
    ("Productos de Limpieza", "Productos de Limpieza"),
]

def crear_datos(apps, schema_editor):
    Perfil = apps.get_model("inicio_sesion", "perfiles")
    Turno = apps.get_model("inicio_sesion", "turnos_laborales")
    Categoria = apps.get_model("inicio_sesion", "categoria_equipo")

    for perfil, _ in PERFIL:
        Perfil.objects.get_or_create(perfil=perfil)

    for turno, _ in TURNO_LABORAL:
        Turno.objects.get_or_create(nombre=turno)

    for categoria, _ in CATEGORIA_EQUIPO:
        Categoria.objects.get_or_create(nombre=categoria)

def eliminar_datos(apps, schema_editor):
    Perfil = apps.get_model("inicio_sesion", "perfiles")
    Turno = apps.get_model("inicio_sesion", "turnos_laborales")
    Categoria = apps.get_model("inicio_sesion", "categoria_equipó")

    Perfil.objects.filter(
        perfil__in=[perfil for perfil, _ in PERFIL]
    ).delete()

    Turno.objects.filter(
        nombre__in=[turno for turno, _ in TURNO_LABORAL]
    ).delete()

    Categoria.objects.filter(
        nombre__in=[categoria for categoria, _ in CATEGORIA_EQUIPO]
    ).delete()

class Migration(migrations.Migration):
    dependencies = [
        ("inicio_sesion", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            crear_datos,
            eliminar_datos
        ),
    ]