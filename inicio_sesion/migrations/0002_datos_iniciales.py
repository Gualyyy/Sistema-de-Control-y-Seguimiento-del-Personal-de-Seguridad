from django.db import migrations

TURNO_LABORAL = [
    ("Diurno", "Diurno"),
    ("Nocturno", "Nocturno"),
]

CATEGORIAS_GASTOS = [
    {
        "nombre": "Materia prima",
        "descripcion": "Compra de materiales e insumos necesarios para la producción de hielo.",
    },
    {
        "nombre": "Servicios básicos",
        "descripcion": "Pagos de electricidad, agua, telefonía e internet.",
    },
    {
        "nombre": "Mantenimiento",
        "descripcion": "Reparación y mantenimiento de equipos, maquinarias e instalaciones.",
    },
    {
        "nombre": "Transporte",
        "descripcion": "Gastos relacionados con el traslado y distribución de productos.",
    },
    {
        "nombre": "Combustible",
        "descripcion": "Compra de combustible para vehículos y equipos de la empresa.",
    },
    {
        "nombre": "Nómina",
        "descripcion": "Pagos de salarios y otros gastos relacionados con el personal.",
    },
    {
        "nombre": "Alquileres",
        "descripcion": "Pagos por alquiler de espacios, locales o equipos.",
    },
    {
        "nombre": "Impuestos y tasas",
        "descripcion": "Pagos de impuestos, tasas y obligaciones fiscales.",
    },
    {
        "nombre": "Materiales de oficina",
        "descripcion": "Compra de papelería y suministros administrativos.",
    },
    {
        "nombre": "Otros gastos",
        "descripcion": "Gastos que no corresponden a las demás categorías registradas.",
    },
]

def crear_datos(apps, schema_editor):
    Turno = apps.get_model("inicio_sesion", "turnos_laborales")
    CategoriaGasto = apps.get_model("inicio_sesion", "categoria_gasto")

    for turno, _ in TURNO_LABORAL:
        Turno.objects.get_or_create(
            nombre=turno
        )

    for datos in CATEGORIAS_GASTOS:
        CategoriaGasto.objects.get_or_create(
            nombre=datos["nombre"],
            defaults={
                "descripcion": datos["descripcion"],
                "activo": True,
            },
        )

def eliminar_datos(apps, schema_editor):
    Turno = apps.get_model("inicio_sesion", "turnos_laborales")
    CategoriaGasto = apps.get_model("inicio_sesion", "categoria_gasto")

    Turno.objects.filter(
        nombre__in=[turno for turno, _ in TURNO_LABORAL]
    ).delete()

    CategoriaGasto.objects.filter(
        nombre__in=[datos["nombre"] for datos in CATEGORIAS_GASTOS]
    ).delete()

class Migration(migrations.Migration):
    dependencies = [
        ("inicio_sesion", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            crear_datos,
            eliminar_datos,
        ),
    ]