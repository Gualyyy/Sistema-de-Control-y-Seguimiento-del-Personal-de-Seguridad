
from django.db import migrations

CATEGORIAS = [
    "Uniforme",
    "Herramientas",
    "Productos de Limpieza",
    "Comunicaciones",
    "Seguridad y Vigilancia",
    "Primeros Auxilios",
    "Identificación",
]

CATEGORIA_POR_PREFIJO = {
    "UNI": "Uniforme",
    "HER": "Herramientas",
    "LIM": "Productos de Limpieza",
    "COM": "Comunicaciones",
    "SEG": "Seguridad y Vigilancia",
    "PRI": "Primeros Auxilios",
    "IDE": "Identificación",
}

EQUIPOS = [
    # Uniforme
    ("UNI-001", "Camisa de vigilancia", 120, "Uniforme destinado al personal de vigilancia."),
    ("UNI-002", "Pantalón de vigilancia", 120, "Pantalón para el uniforme del personal de vigilancia."),
    ("UNI-003", "Botas de seguridad", 110, "Calzado de protección para el personal."),
    ("UNI-004", "Gorra de vigilancia", 15, "Gorra para identificación del personal de vigilancia."),
    ("UNI-005", "Cinturón táctico", 12, "Cinturón de dotación para el personal de vigilancia."),
    ("UNI-006", "Chaleco reflectante", 10, "Chaleco para mejorar la visibilidad del personal."),
    ("UNI-007", "Impermeable de vigilancia", 10, "Prenda impermeable para labores de vigilancia."),
    ("UNI-008", "Chaqueta de vigilancia", 10, "Chaqueta de dotación para el personal."),
    ("UNI-009", "Guantes de protección", 120, "Guantes para protección durante las labores asignadas."),
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
    ("LIM-006", "Bolsas para basura", 150, "Insumo para recolección de residuos."),
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
    ("UNI-016", "Mascarilla de protección", 150, "Protección respiratoria para tareas que lo requieran."),
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
    ("LIM-019", "Papel higiénico", 180, "Insumo para baños y áreas sanitarias."),
    ("LIM-020", "Toallas de papel", 120, "Insumo para secado e higiene de manos."),

    # Comunicaciones
    ("COM-001", "Radio portátil", 120, "Equipo de comunicación para coordinación del personal de vigilancia."),
    ("COM-002", "Batería para radio", 120, "Batería de repuesto compatible con los radios de la empresa."),
    ("COM-003", "Cargador para radio", 30, "Cargador individual para radios portátiles."),
    ("COM-004", "Auricular para radio", 100, "Accesorio de audio para comunicación discreta por radio."),
    ("COM-005", "Micrófono para radio", 50, "Micrófono externo compatible con radios portátiles."),
    ("COM-006", "Base múltiple de carga", 12, "Base para cargar varios radios durante el cambio de turno."),
    ("COM-007", "Teléfono corporativo", 25, "Teléfono asignado a supervisores para coordinación operativa."),
    ("COM-008", "Cargador de teléfono", 30, "Cargador de repuesto para teléfonos corporativos."),

    # Seguridad y Vigilancia
    ("SEG-001", "Detector de metales manual", 20, "Detector portátil para controles de acceso autorizados."),
    ("SEG-002", "Binoculares de vigilancia", 15, "Binoculares para observación desde puestos de vigilancia."),
    ("SEG-003", "Cámara corporal", 30, "Cámara portátil para registro de rondas según protocolo."),
    ("SEG-004", "Megáfono portátil", 12, "Equipo de comunicación sonora para emergencias y control de acceso."),
    ("SEG-005", "Cono de señalización", 100, "Elemento portátil para delimitar zonas durante una incidencia."),
    ("SEG-006", "Cinta de señalización", 100, "Cinta para delimitar temporalmente áreas restringidas."),
    ("SEG-007", "Espejo de inspección", 12, "Espejo manual para inspecciones visuales autorizadas."),
    ("SEG-008", "Silbato de seguridad", 100, "Accesorio de aviso sonoro para el personal de vigilancia."),

    # Primeros Auxilios
    ("PRI-001", "Botiquín portátil", 25, "Botiquín básico para puestos y vehículos de servicio."),
    ("PRI-002", "Venda de gasa", 120, "Insumo de primeros auxilios para cubrir lesiones menores."),
    ("PRI-003", "Gasa estéril", 120, "Material estéril para atención básica de primeros auxilios."),
    ("PRI-004", "Venda elástica", 80, "Venda de soporte para botiquines de los puestos de servicio."),
    ("PRI-005", "Guantes de nitrilo", 150, "Guantes desechables para atención básica y segura."),
    ("PRI-006", "Tijera de primeros auxilios", 25, "Tijera de punta roma para equipar botiquines."),
    ("PRI-007", "Compresa fría instantánea", 50, "Compresa de un solo uso para botiquines de servicio."),
    ("PRI-008", "Manta térmica de emergencia", 30, "Manta compacta para incluir en equipos de emergencia."),

    # Identificación
    ("IDE-001", "Credencial de identificación", 150, "Credencial para identificar al personal de la empresa."),
    ("IDE-002", "Porta credencial", 150, "Funda protectora para credenciales del personal."),
    ("IDE-003", "Cordón porta credencial", 150, "Cordón para portar la identificación durante el servicio."),
    ("IDE-004", "Placa identificativa", 100, "Placa con nombre para el uniforme del personal."),
    ("IDE-005", "Parche institucional", 120, "Parche identificativo para uniformes de vigilancia."),
    ("IDE-006", "Brazalete de supervisor", 30, "Brazalete visible para identificar al supervisor de turno."),
    ("IDE-007", "Etiqueta para casillero", 100, "Etiqueta para identificar casilleros de dotación."),
    ("IDE-008", "Tarjeta de visitante", 200, "Tarjeta temporal para control de visitantes en los puestos."),
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
        prefijo = codigo.split("-", 1)[0]
        categoria_nombre = CATEGORIA_POR_PREFIJO[prefijo]

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
