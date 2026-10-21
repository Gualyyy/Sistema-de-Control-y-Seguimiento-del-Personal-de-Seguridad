
from django.db import migrations

CATEGORIAS = [
    "Uniforme",
    "Herramientas",
    "Productos de Limpieza",
]

EQUIPOS = [
    # Uniforme
    ("UNI-001", "Camisa de vigilancia", 20, "Uniforme destinado al personal de vigilancia."),
    ("UNI-002", "Pantalón de vigilancia", 20, "Pantalón para el uniforme del personal de vigilancia."),
    ("UNI-003", "Botas de seguridad", 15, "Calzado de protección para el personal."),
    ("UNI-004", "Gorra de vigilancia", 15, "Gorra para identificación del personal de vigilancia."),
    ("UNI-005", "Cinturón táctico", 12, "Cinturón de dotación para el personal de vigilancia."),
    ("UNI-006", "Chaleco reflectante", 10, "Chaleco para mejorar la visibilidad del personal."),
    ("UNI-007", "Impermeable de vigilancia", 10, "Prenda impermeable para labores de vigilancia."),
    ("UNI-008", "Chaqueta de vigilancia", 10, "Chaqueta de dotación para el personal."),
    ("UNI-009", "Guantes de protección", 20, "Guantes para protección durante las labores asignadas."),
    ("UNI-010", "Casco de seguridad", 10, "Casco para protección en áreas operativas."),

    # Herramientas
    ("HER-001", "Linterna recargable", 15, "Linterna para recorridos y vigilancia nocturna."),
    ("HER-002", "Juego de destornilladores", 5, "Herramientas para trabajos de mantenimiento."),
    ("HER-003", "Juego de llaves combinadas", 4, "Herramientas para mantenimiento general."),
    ("HER-004", "Alicate universal", 5, "Herramienta para trabajos de mantenimiento."),
    ("HER-005", "Martillo de carpintero", 3, "Herramienta para reparaciones generales."),
    ("HER-006", "Cinta métrica", 5, "Instrumento para mediciones en instalaciones."),
    ("HER-007", "Taladro eléctrico", 2, "Equipo eléctrico para trabajos de mantenimiento."),
    ("HER-008", "Extensión eléctrica", 5, "Extensión para alimentación eléctrica temporal."),
    ("HER-009", "Escalera de aluminio", 3, "Escalera para trabajos autorizados en altura."),
    ("HER-010", "Carretilla de carga", 3, "Equipo para traslado de materiales."),

    # Productos de Limpieza
    ("LIM-001", "Detergente líquido", 20, "Insumo para limpieza de superficies."),
    ("LIM-002", "Desinfectante de superficies", 20, "Insumo para desinfección de áreas comunes."),
    ("LIM-003", "Cloro de limpieza", 15, "Insumo para limpieza y desinfección."),
    ("LIM-004", "Desengrasante industrial", 10, "Insumo para eliminar grasa en áreas autorizadas."),
    ("LIM-005", "Jabón líquido para manos", 20, "Insumo de higiene para baños y lavamanos."),
    ("LIM-006", "Bolsas para basura", 30, "Insumo para recolección de residuos."),
    ("LIM-007", "Escoba industrial", 8, "Utensilio para limpieza de pisos."),
    ("LIM-008", "Recogedor de basura", 8, "Utensilio para recolección de residuos."),
    ("LIM-009", "Trapeador industrial", 8, "Utensilio para limpieza de pisos."),
    ("LIM-010", "Paños de limpieza", 20, "Paños reutilizables para limpieza de superficies."),

    # Uniforme - equipos adicionales
    ("UNI-011", "Chaleco de vigilancia", 10, "Chaleco de dotación para el personal de vigilancia."),
    ("UNI-012", "Camisa tipo polo", 15, "Camisa institucional para el personal operativo."),
    ("UNI-013", "Pantalón cargo", 12, "Pantalón para actividades operativas."),
    ("UNI-014", "Botas impermeables", 8, "Calzado impermeable para áreas húmedas."),
    ("UNI-015", "Gafas de seguridad", 12, "Protección ocular para actividades autorizadas."),
    ("UNI-016", "Mascarilla de protección", 30, "Protección respiratoria para tareas que lo requieran."),
    ("UNI-017", "Protector auditivo", 10, "Protección auditiva para áreas con ruido."),
    ("UNI-018", "Faja de soporte lumbar", 8, "Accesorio de apoyo para tareas autorizadas."),
    ("UNI-019", "Brazalete de identificación", 15, "Accesorio de identificación del personal."),
    ("UNI-020", "Poncho impermeable", 10, "Prenda impermeable para recorridos al aire libre."),

    # Herramientas - equipos adicionales
    ("HER-011", "Juego de alicates", 4, "Herramientas para trabajos de mantenimiento."),
    ("HER-012", "Llave ajustable", 5, "Herramienta para ajustes mecánicos."),
    ("HER-013", "Sierra manual", 3, "Herramienta para cortes en materiales compatibles."),
    ("HER-014", "Nivel de burbuja", 4, "Instrumento para verificar nivelación."),
    ("HER-015", "Pinza de presión", 4, "Herramienta para sujetar piezas."),
    ("HER-016", "Cúter industrial", 8, "Herramienta de corte para tareas autorizadas."),
    ("HER-017", "Juego de llaves Allen", 5, "Herramientas para ajustes de tornillería."),
    ("HER-018", "Multímetro digital", 3, "Instrumento para mediciones eléctricas por personal autorizado."),
    ("HER-019", "Carro de herramientas", 2, "Equipo para organizar y trasladar herramientas."),
    ("HER-020", "Hidrolavadora", 2, "Equipo para limpieza de superficies resistentes al agua."),

    # Productos de Limpieza - artículos adicionales
    ("LIM-011", "Limpiavidrios", 12, "Producto para limpieza de superficies de vidrio."),
    ("LIM-012", "Limpiador multiusos", 20, "Producto para limpieza general de superficies."),
    ("LIM-013", "Esponjas de limpieza", 25, "Accesorios para limpieza de superficies."),
    ("LIM-014", "Cepillo de cerdas duras", 10, "Utensilio para limpieza profunda."),
    ("LIM-015", "Cepillo para baños", 8, "Utensilio para limpieza de sanitarios."),
    ("LIM-016", "Cubeta de limpieza", 10, "Recipiente para labores de limpieza."),
    ("LIM-017", "Atomizador manual", 12, "Recipiente pulverizador para productos de limpieza."),
    ("LIM-018", "Dispensador de jabón", 6, "Dispensador para áreas sanitarias."),
    ("LIM-019", "Papel higiénico", 40, "Insumo para baños y áreas sanitarias."),
    ("LIM-020", "Toallas de papel", 30, "Insumo para secado e higiene de manos."),
]

def cargar_inventario(apps, schema_editor):
    Categoria = apps.get_model("asignaciones", "categoria_equipo")
    Equipo = apps.get_model("asignaciones", "equipos")
    Historial = apps.get_model("asignaciones", "historial_inventario_equipo")

    alias = schema_editor.connection.alias

    categorias = {}

    for nombre in CATEGORIAS:
        categoria, _ = Categoria.objects.using(alias).get_or_create(
            nombre=nombre
        )
        categorias[nombre] = categoria

    for codigo, nombre, cantidad, observacion in EQUIPOS:
        if codigo.startswith("UNI-"):
            categoria_nombre = "Uniforme"
        elif codigo.startswith("HER-"):
            categoria_nombre = "Herramientas"
        else:
            categoria_nombre = "Productos de Limpieza"

        equipo, creado = Equipo.objects.using(alias).get_or_create(
            codigo=codigo,
            defaults={
                "nombre": nombre,
                "observacion": observacion,
                "cantidad_disponible": cantidad,
                "activo": True,
                "id_categoria_id": categorias[categoria_nombre].pk,
            },
        )

        if creado:
            Historial.objects.using(alias).create(
                id_equipo_id=equipo.pk,
                tipo_movimiento="REGISTRO",
                cantidad_anterior=0,
                cantidad_movimiento=cantidad,
                cantidad_nueva=cantidad,
                activo_anterior=False,
                activo_nuevo=True,
                observacion="Registro inicial mediante migración de datos.",
            )


def revertir_inventario(apps, schema_editor):
    Equipo = apps.get_model("asignaciones", "equipos")
    Historial = apps.get_model("asignaciones", "historial_inventario_equipo")
    Categoria = apps.get_model("asignaciones", "categoria_equipo")

    alias = schema_editor.connection.alias
    codigos = [equipo[0] for equipo in EQUIPOS]

    equipos = Equipo.objects.using(alias).filter(codigo__in=codigos)
    ids = list(equipos.values_list("pk", flat=True))

    Historial.objects.using(alias).filter(id_equipo_id__in=ids).delete()
    equipos.delete()

    Categoria.objects.using(alias).filter(
        nombre__in=CATEGORIAS,
        equipos__isnull=True,
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("asignaciones", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            cargar_inventario,
            revertir_inventario,
        ),
    ]
