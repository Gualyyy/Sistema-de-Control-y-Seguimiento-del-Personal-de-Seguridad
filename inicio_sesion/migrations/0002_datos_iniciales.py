from django.db import migrations

TURNO_LABORAL = [
    ("Diurno", "Diurno"),
    ("Nocturno", "Nocturno"),
]

def crear_datos(apps, schema_editor):
    Turno = apps.get_model("inicio_sesion", "turnos_laborales")

    for turno, _ in TURNO_LABORAL:
        Turno.objects.get_or_create(nombre=turno)

def eliminar_datos(apps, schema_editor):
    Turno = apps.get_model("inicio_sesion", "turnos_laborales")

    Turno.objects.filter(
        nombre__in=[turno for turno, _ in TURNO_LABORAL]
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