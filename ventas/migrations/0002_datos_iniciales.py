from django.db import migrations


def cargar_catalogos(apps, schema_editor):
    Categoria = apps.get_model("ventas", "categoria_producto")
    Unidad = apps.get_model("ventas", "unidad_medida")
    CategoriaGasto = apps.get_model("ventas", "categoria_gasto")
    MetodoPago = apps.get_model("ventas", "metodo_pago")

    categorias = [
        "Hielo en cubos",
        "Hielo triturado",
        "Hielo en bloques",
        "Hielo en escamas",
        "Hielo en tubos",
        "Hielo industrial",
        "Hielo para consumo humano",
        "Hielo para refrigeración",
    ]

    for nombre in categorias:
        Categoria.objects.get_or_create(
            nombre=nombre,
            defaults={"activo": True},
        )

    unidades = [
        {"nombre": "Unidad", "abreviatura": "und", "permite_decimales": False},
        {"nombre": "Bolsa", "abreviatura": "bol", "permite_decimales": False},
        {"nombre": "Kilogramo", "abreviatura": "kg", "permite_decimales": True},
        {"nombre": "Paquete", "abreviatura": "paq", "permite_decimales": False},
    ]

    for datos in unidades:
        Unidad.objects.get_or_create(
            nombre=datos["nombre"],
            defaults={
                "abreviatura": datos["abreviatura"],
                "permite_decimales": datos["permite_decimales"],
                "activo": True,
            },
        )

    categorias_gastos = [
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

    for datos in categorias_gastos:
        CategoriaGasto.objects.get_or_create(
            nombre=datos["nombre"],
            defaults={
                "descripcion": datos["descripcion"],
                "activo": True,
            },
        )

    metodos_pago = [
        "Efectivo",
        "Transferencia bancaria",
        "Pago móvil",
        "Tarjeta de débito",
        "Tarjeta de crédito",
    ]

    for nombre in metodos_pago:
        MetodoPago.objects.get_or_create(
            nombre=nombre,
            defaults={"activo": True},
        )


class Migration(migrations.Migration):

    dependencies = [
        ("ventas", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            cargar_catalogos,
            migrations.RunPython.noop,
        ),
    ]