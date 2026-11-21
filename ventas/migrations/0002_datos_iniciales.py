
from django.db import migrations

def cargar_catalogos(apps, schema_editor):
    Categoria = apps.get_model("ventas", "categoria_producto")
    Unidad = apps.get_model("ventas", "unidad_medida")
    MetodoPago = apps.get_model("ventas", "metodo_pago")

    categorias = [
        "Hielo en cubos",
        "Hielo molido",
        "Hielo en bloques",
        "Hielo seco",
    ]

    for nombre in categorias:
        Categoria.objects.get_or_create(
            nombre=nombre,
            defaults={"activo": True},
        )

    unidades = [
        {"nombre": "Unidad", "abreviatura": "und", "permite_decimales": False},
        {"nombre": "Bolsa", "abreviatura": "bol", "permite_decimales": False},
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

    

    metodos_pago = [
        "Pago móvil",
        "Transferencia bancaria",
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
