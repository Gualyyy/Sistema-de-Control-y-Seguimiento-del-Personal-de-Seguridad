from django.db import migrations

TIPOS_INCIDENCIA = (
    ("Daño", "Daño"),
    ("Accidente", "Accidente"),
    ("Mantenimiento", "Mantenimiento"),
    ("Falla de Hardware", "Falla de Hardware"),
    ("Falla de Software", "Falla de Software"),
    ("Conectividad", "Conectividad"),
    ("Seguridad", "Seguridad"),
    ("Robo", "Robo"),
)

def crear_datos(apps, schema_editor):
    TipoIncidencia = apps.get_model("incidencias", "tipo_incidencia")

    for tipo, _ in TIPOS_INCIDENCIA:
        TipoIncidencia.objects.get_or_create(nombre=tipo)

def eliminar_datos(apps, schema_editor):
    TipoIncidencia = apps.get_model("incidencias", "tipo_incidencia")

    TipoIncidencia.objects.filter(
        nombre__in=[tipo for tipo, _ in TIPOS_INCIDENCIA]
    ).delete()

class Migration(migrations.Migration):
    dependencies = [
        ("incidencias", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            crear_datos,
            eliminar_datos
        ),
    ]