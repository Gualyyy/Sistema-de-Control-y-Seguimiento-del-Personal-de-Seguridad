from django.shortcuts import render
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.db.models import Sum, F
from django.conf import settings

from inicio_sesion.models import usuarios, bitacora
from asignaciones.models import categoria_equipo, equipos, historial_inventario_equipo, entrega_equipos

import os
from datetime import datetime

from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
)

from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter

# GESTIÓN DE EQUIPOS

# CARTEGORIAS REGISTRADAS

def categoria_registrados(request):
    categorias_lista = categoria_equipo.objects.all()

    datos = [
        {
            "id_categoria": categoria.id_categoria,
            "nombre": categoria.nombre
        }
        for categoria in categorias_lista
    ]

    return JsonResponse(datos, safe=False)

# REGISTRAR EQUIPOS

def registros_equipos(request):
    if request.method != "POST":
        return render(request, "Equipos/registro_equipos.html")

    nombre = (request.POST.get("nombre") or "").strip()
    codigo = (request.POST.get("codigo") or "").strip()
    cantidad_total = request.POST.get("cantidad_total")
    id_categoria = request.POST.get("categoria_equipo")

    campos = [
        (nombre, "Por favor, debe ingresar el nombre del equipo."),
        (codigo, "Por favor, debe ingresar el código del equipo."),
        (cantidad_total, "Por favor, debe ingresar la cantidad total del equipo."),
        (id_categoria, "Por favor, debe seleccionar una categoría."),
    ]

    for valor, mensaje in campos:
        if not valor:
            return JsonResponse({
                "estado": "fallo",
                "title": "Campo vacío",
                "descripcion": mensaje,
                "icon": "warning"
            })

    if request.POST.get("observacion"):
        observacion = request.POST.get("observacion")
    else:
        observacion = "N/A"

    try:
        cantidad_total = int(cantidad_total)

        if cantidad_total <= 0:
            return JsonResponse({
                "estado": "fallo",
                "title": "Cantidad inválida",
                "descripcion": "La cantidad inicial debe ser mayor que cero.",
                "icon": "warning"
            })

    except (ValueError, TypeError):
        return JsonResponse({
            "estado": "fallo",
            "title": "Cantidad inválida",
            "descripcion": "Debe ingresar una cantidad entera válida.",
            "icon": "warning"
        })

    if equipos.objects.filter(codigo=codigo).exists():
        return JsonResponse({
            "estado": "fallo",
            "title": "Código existente",
            "descripcion": "El código ingresado ya está registrado.",
            "icon": "warning"
        })

    try:
        categoria = categoria_equipo.objects.get(pk=id_categoria)
    except (categoria_equipo.DoesNotExist, ValueError, TypeError):
        return JsonResponse({
            "estado": "fallo",
            "title": "Categoría inválida",
            "descripcion": "La categoría seleccionada no existe.",
            "icon": "error"
        })

    try:
        with transaction.atomic():
            info_usuario = usuarios.objects.get(cedula_identidad=request.session.get("cedula_identidad"))

            equipo = equipos.objects.create(
                nombre=nombre,
                codigo=codigo,
                observacion=observacion,
                cantidad_disponible=cantidad_total,
                id_categoria=categoria
            )

            historial_inventario_equipo.objects.create(
                id_equipo=equipo,
                tipo_movimiento="REGISTRO",
                cantidad_anterior=0,
                cantidad_movimiento=cantidad_total,
                cantidad_nueva=cantidad_total,
                activo_anterior=None,
                activo_nuevo=True,
                observacion=(
                    f"Registro inicial del equipo {nombre} "
                    f"con código {codigo}. "
                    f"Cantidad incorporada: {cantidad_total}. "
                    f"Categoría: {categoria.nombre}."
                )
            )

            bitacora.objects.create(
                id_usuario=info_usuario,
                accion=(
                    f"Registro del equipo {nombre} ({codigo}), "
                    f"cantidad inicial: {cantidad_total}, "
                    f"categoría: {categoria.nombre}."
                )
            )

        return JsonResponse({
            "estado": "exito",
            "title": "Registro exitoso",
            "descripcion": (
                "El equipo fue registrado correctamente "
                "y su movimiento inicial fue guardado en el historial."
            ),
            "icon": "success"
        })

    except usuarios.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Usuario no encontrado",
            "descripcion": "No se encontró el usuario que realiza el registro.",
            "icon": "error"
        })

    except Exception:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "descripcion": (
                "Ocurrió un error al registrar el equipo. "
                "No se guardaron los cambios."
            ),
            "icon": "error"
        })
    
# BUSCAR LOS DATOS DEL EQUIPOS

def buscar_equipos(request):
    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "title": "Solicitud inválida",
            "descripcion": "Método de solicitud no permitido.",
            "icon": "warning"
        }, status=405)

    codigo = (request.POST.get("codigo_equipo") or "").strip()
    if not codigo:
        return JsonResponse({
            "estado": "fallo",
            "title": "Campo vacío",
            "descripcion": "No se recibió el código del equipo.",
            "icon": "warning"
        })

    try:
        equipo = equipos.objects.select_related("id_categoria").get(codigo=codigo)

        entregas = equipo.entregas_supervisores.aggregate(
            cantidad_entregada=Sum("cantidad_entregada"),
            cantidad_disponible=Sum("cantidad_disponible")
        )

        return JsonResponse({
            "estado": "exito",
            "equipo": {
                "id_equipo": equipo.id_equipo,
                "nombre": equipo.nombre,
                "codigo": equipo.codigo,
                "observacion": equipo.observacion,
                "cantidad_disponible": equipo.cantidad_disponible,
                "cantidad_entregada": (
                    entregas["cantidad_entregada"] or 0
                ),
                "cantidad_disponible_supervisores": (
                    entregas["cantidad_disponible"] or 0
                ),
                "id_categoria": equipo.id_categoria.id_categoria,
                "categoria": equipo.id_categoria.nombre,
                "activo": equipo.activo,
                "fecha_registro": equipo.fecha_registro.strftime("%d/%m/%Y %H:%M"),
            }
        })

    except equipos.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "No encontrado",
            "descripcion": "El equipo no existe.",
            "icon": "error"
        })
    except Exception:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "descripcion": "Ocurrió un error al consultar el equipo.",
            "icon": "error"
        })

# ACTUALIZAR LOS DATOS DEL EQUIPO

def actualizacion_equipos(request):
    if request.method != "POST":
        return render(request, "Equipos/actualizar_equipo.html")

    equipo_id = request.POST.get("equipo_id")
    nombre = (request.POST.get("nombre") or "").strip()
    observacion = (request.POST.get("observacion") or "").strip()
    cantidad_disponible = request.POST.get("cantidad_disponible")
    categoria = request.POST.get("categoria_equipo")

    campos = [
        (equipo_id, "Equipo", "No se recibió el identificador del equipo."),
        (nombre, "Nombre del Equipo", "Por favor, ingrese el nombre del equipo."),
        (cantidad_disponible, "Cantidad Disponible", "Por favor, ingrese la cantidad disponible de equipo."),
        (categoria, "Categoría de Equipo", "Por favor, seleccione la categoría de equipo."),
    ]

    for valor, campo, mensaje in campos:
        if not valor:
            return JsonResponse({
                "estado": "fallo",
                "title": campo,
                "descripcion": mensaje,
                "icon": "warning"
            })

    try:
        nueva_cantidad_disponible = int(cantidad_disponible)

        if nueva_cantidad_disponible <= 0:
            return JsonResponse({
                "estado": "fallo",
                "title": "Cantidad Total",
                "descripcion": "La cantidad total debe ser un número entero mayor que 0.",
                "icon": "warning"
            })

        with transaction.atomic():
            info_equipo = (
                equipos.objects
                .select_for_update()
                .get(id_equipo=equipo_id)
            )

            info_categoria = categoria_equipo.objects.get(pk=categoria)

            nombre_existente = (
                equipos.objects
                .filter(nombre__iexact=nombre)
                .exclude(id_equipo=info_equipo.id_equipo)
                .exists()
            )

            if nombre_existente:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Nombre del Equipo",
                    "descripcion": (
                        "Ingrese otro nombre para el equipo, "
                        "ya existe uno registrado con ese nombre."
                    ),
                    "icon": "error"
                })

            # Cantidad disponible en el inventario principal antes del cambio.
            cantidad_anterior = info_equipo.cantidad_disponible
            activo_anterior = info_equipo.activo

            # Cantidad total entregada a los supervisores.
            cantidad_entregada = (
                entrega_equipos.objects
                .filter(id_equipo=info_equipo)
                .aggregate(
                    total=Sum("cantidad_entregada")
                )["total"] or 0
            )

            if nueva_cantidad_disponible < cantidad_entregada:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Cantidad no válida",
                    "descripcion": (
                        f"La cantidad total no puede ser menor a "
                        f"{cantidad_entregada} "
                        f"{'unidad' if cantidad_entregada == 1 else 'unidades'} "
                        "entregadas a los supervisores."
                    ),
                    "icon": "warning"
                })

            # Calcular las unidades que quedan en el inventario principal.
            nueva_cantidad_disponible = nueva_cantidad_disponible - cantidad_entregada

            info_equipo.nombre = nombre
            info_equipo.observacion = observacion
            info_equipo.cantidad_disponible = nueva_cantidad_disponible
            info_equipo.id_categoria = info_categoria

            info_equipo.save()

            # Registrar el movimiento en el historial de inventario.
            historial_inventario_equipo.objects.create(
                id_equipo=info_equipo,
                tipo_movimiento="CORRECCION",
                cantidad_anterior=cantidad_anterior,
                cantidad_movimiento=(
                    nueva_cantidad_disponible - cantidad_anterior
                ),
                cantidad_nueva=nueva_cantidad_disponible,
                activo_anterior=activo_anterior,
                activo_nuevo=info_equipo.activo,
                observacion=(
                    f"Actualización del equipo '{nombre}'. "
                    f"Cantidad disponible anterior: {cantidad_anterior}. "
                    f"Cantidad disponible nueva: "
                    f"{nueva_cantidad_disponible}. "
                    f"Cantidad entregada a supervisores: "
                    f"{cantidad_entregada}. "
                    f"Motivo: {observacion or 'Sin observación adicional.'}"
                )
            )

            info_usuario = usuarios.objects.get(cedula_identidad=request.session.get("cedula_identidad"))

            accion = (
                f"Actualización del equipo: {nombre}; "
                f"cantidad disponible: {nueva_cantidad_disponible}; "
                f"categoría: {info_categoria.nombre}."
            )

            bitacora.objects.create(
                id_usuario=info_usuario,
                accion=accion
            )

            return JsonResponse({
                "estado": "exito",
                "title": "Éxito",
                "descripcion": "El equipo fue actualizado correctamente.",
                "icon": "success"
            })

    except (ValueError, TypeError):
        return JsonResponse({
            "estado": "fallo",
            "title": "Cantidad Total",
            "descripcion": "La cantidad total debe ser un número entero válido.",
            "icon": "warning"
        })

    except categoria_equipo.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Categoría",
            "descripcion": "La categoría de equipo no existe.",
            "icon": "error"
        })

    except equipos.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Equipo",
            "descripcion": "El equipo no existe.",
            "icon": "error"
        })

    except usuarios.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Usuario",
            "descripcion": "No se encontró el usuario de la sesión actual.",
            "icon": "error"
        })

    except Exception as e:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "descripcion": f"Ocurrió un error al momento de actualizar el equipo {e}.",
            "icon": "error"
        })

# VISUALIZAR TODOS LOS EQUIPOS REGISTRADOS 

def visualizacion_equipos(request):
    if request.method != "POST":
        return render(request, "Equipos/visualizar_equipos.html")

    codigo = (request.POST.get("codigo") or "").strip()
    categoria = (request.POST.get("categoria") or "").strip()

    lista_equipos = equipos.objects.select_related(
        "id_categoria"
    ).order_by("nombre")

    if codigo:
        lista_equipos = lista_equipos.filter(codigo__icontains=codigo)

    if categoria.isdigit():
        lista_equipos = lista_equipos.filter(id_categoria__id_categoria=int(categoria))

    datos = []

    for equipo in lista_equipos:
        datos.append({
            "id_equipo": equipo.id_equipo,
            "nombre": equipo.nombre,
            "codigo": equipo.codigo,
            "categoria": equipo.id_categoria.nombre,
            "cantidad_disponible": equipo.cantidad_disponible,
            "observacion": equipo.observacion or "",
            "fecha_registro": equipo.fecha_registro.strftime("%d/%m/%Y %H:%M"),
            "activo": equipo.activo,
        })

    return JsonResponse(datos, safe=False)

# REPORTE DE TODOS LOS EQUIPOS

def lista_equipos_pdf(request):
    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "title": "Solicitud inválida",
            "descripcion": "Método de solicitud no permitido.",
            "icon": "warning"
        }, status=405)

    categoria = (request.POST.get("categoria") or "").strip()

    lista_equipos = equipos.objects.select_related(
        "id_categoria"
    ).order_by("nombre")

    if categoria.isdigit():
        lista_equipos = lista_equipos.filter(
            id_categoria__id_categoria=int(categoria)
        )

    # Verificar que existan equipos antes de generar el PDF.
    if not lista_equipos.exists():
        return JsonResponse({
            "estado": "fallo",
            "title": "Sin equipos registrados",
            "descripcion": (
                "No existen equipos registrados para generar el reporte."
            ),
            "icon": "warning"
        })

    # RESPUESTA PDF
    response = HttpResponse(content_type="application/pdf")

    response["Content-Disposition"] = (
        'inline; filename="lista_equipos.pdf"'
    )

    # DOCUMENTO
    documento = SimpleDocTemplate(
        response,
        pagesize=letter,
        rightMargin=30,
        leftMargin=30,
        topMargin=135,
        bottomMargin=35
    )

    # ESTILOS
    estilos = getSampleStyleSheet()

    estilo_encabezado = ParagraphStyle(
        "EncabezadoEquipos",
        parent=estilos["Normal"],
        fontName="Times-Bold",
        fontSize=12,
        leading=12,
        alignment=TA_CENTER,
        textColor=colors.white
    )

    estilo_celda = ParagraphStyle(
        "CeldaEquipos",
        parent=estilos["Normal"],
        fontName="Times-Roman",
        fontSize=12,
        leading=12,
        alignment=TA_CENTER,
        textColor=colors.black
    )

    # LOGO
    ruta_logo = os.path.join(
        settings.BASE_DIR,
        "static",
        "Imagenes",
        "logo_hielo_caipe.png"
    )

    # DATOS DE LA TABLA
    datos_tabla = [
        [
            Paragraph("Lista de Equipos", estilo_encabezado),
            "",
            "",
            "",
            "",
        ],
        [
            Paragraph("N.º", estilo_encabezado),
            Paragraph("Nombre", estilo_encabezado),
            Paragraph("Código", estilo_encabezado),
            Paragraph("Categoría", estilo_encabezado),
            Paragraph("Disponible", estilo_encabezado),
        ]
    ]

    for numero, equipo in enumerate(lista_equipos, start=1):
        nombre = equipo.nombre or "No especificado"
        codigo = equipo.codigo or "No especificado"

        categoria_nombre = (
            equipo.id_categoria.nombre
            if equipo.id_categoria
            else "No especificada"
        )

        datos_tabla.append([
            Paragraph(str(numero), estilo_celda),
            Paragraph(str(nombre), estilo_celda),
            Paragraph(str(codigo), estilo_celda),
            Paragraph(str(categoria_nombre), estilo_celda),
            Paragraph(str(equipo.cantidad_disponible), estilo_celda),
        ])

    # TABLA
    tabla = Table(
        datos_tabla,
        colWidths=[
            40,
            140,
            100,
            160,
            95,
        ],
        repeatRows=2,
        hAlign="CENTER"
    )

    tabla.setStyle(TableStyle([
        ("SPAN", (0, 0), (-1, 0)),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#00445F")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),

        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#00445F")),
        ("TEXTCOLOR", (0, 1), (-1, 1), colors.white),
        ("FONTNAME", (0, 1), (-1, 1), "Times-Bold"),

        ("FONTNAME", (0, 2), (-1, -1), "Times-Roman"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),

        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#00445F")),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#58A5C4")),

        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))

    # ELEMENTOS
    elementos = [
        tabla,
    ]

    # GENERAR PDF
    documento.build(
        elementos,
        onFirstPage=lambda canvas, documento:
            encabezado_lista_pdf(
                canvas,
                documento,
                ruta_logo
            ),
        onLaterPages=lambda canvas, documento:
            encabezado_lista_pdf(
                canvas,
                documento,
                ruta_logo
            )
    )

    return response

def encabezado_lista_pdf(canvas, documento, ruta_logo):
    canvas.saveState()

    # LOGO
    x_logo = 30
    y_logo = letter[1] - 150

    ancho_logo = 160
    alto_logo = 160

    canvas.drawImage(
        ruta_logo,
        x_logo,
        y_logo,
        width=ancho_logo,
        height=alto_logo,
        preserveAspectRatio=True,
        mask="auto"
    )

    # TITULO EMPRESA
    x_titulo = 185
    y_titulo = letter[1] - 70

    canvas.setFont("Times-Bold", 18)
    canvas.setFillColor(colors.HexColor("#00445F"))

    canvas.drawString(
        x_titulo,
        y_titulo,
        "EMPRESA HIELO CAIPE C.A"
    )

    # FECHA EN ESPAÑOL
    meses = [
        "Enero",
        "Febrero",
        "Marzo",
        "Abril",
        "Mayo",
        "Junio",
        "Julio",
        "Agosto",
        "Septiembre",
        "Octubre",
        "Noviembre",
        "Diciembre"
    ]

    fecha = datetime.now()

    fecha_actual = (
        f"{fecha.day} de "
        f"{meses[fecha.month - 1]} de "
        f"{fecha.year}"
    )

    # FECHA
    x_fecha = 210
    y_fecha = letter[1] - 120

    canvas.setFont("Times-Bold", 11)
    canvas.setFillColor(colors.HexColor("#072F3F"))

    canvas.drawString(
        x_fecha,
        y_fecha,
        f"Fecha Generado {fecha_actual}"
    )

    canvas.restoreState()

# REPORTE DE TODOS LOS DATOS DEL EQUIPO

def datos_equipos_pdf(request):
    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "title": "Solicitud inválida",
            "descripcion": "Método de solicitud no permitido.",
            "icon": "warning"
        }, status=405)

    id_equipo = (request.POST.get("id_equipo") or "").strip()

    if not id_equipo:
        return JsonResponse({
            "estado": "fallo",
            "title": "Equipo no seleccionado",
            "descripcion": "Debe seleccionar un equipo para generar el reporte.",
            "icon": "warning"
        }, status=400)

    try:
        equipo = equipos.objects.select_related(
            "id_categoria"
        ).get(id_equipo=id_equipo)

    except (equipos.DoesNotExist, ValueError, TypeError):
        return JsonResponse({
            "estado": "fallo",
            "title": "Equipo no encontrado",
            "descripcion": "El equipo seleccionado no existe o no se pudo encontrar.",
            "icon": "warning"
        }, status=404)

    response = HttpResponse(content_type="application/pdf")

    response["Content-Disposition"] = (
        f'inline; filename="equipo_{equipo.id_equipo}.pdf"'
    )

    documento = SimpleDocTemplate(
        response,
        pagesize=letter,
        rightMargin=45,
        leftMargin=45,
        topMargin=120,
        bottomMargin=40
    )

    estilos = getSampleStyleSheet()

    estilo_encabezado = ParagraphStyle(
        "EncabezadoEquipo",
        parent=estilos["Normal"],
        fontName="Times-Bold",
        fontSize=12,
        leading=12,
        alignment=TA_CENTER,
        textColor=colors.white
    )

    estilo_campo = ParagraphStyle(
        "CampoEquipo",
        parent=estilos["Normal"],
        fontName="Times-Bold",
        fontSize=12,
        leading=12,
        textColor=colors.white
    )

    estilo_valor = ParagraphStyle(
        "ValorEquipo",
        parent=estilos["Normal"],
        fontName="Times-Roman",
        fontSize=12,
        leading=14,
        textColor=colors.black,
        wordWrap="CJK"
    )

    nombre = equipo.nombre or "No especificado"
    codigo = equipo.codigo or "No especificado"
    observacion = equipo.observacion or "Sin observaciones"
    cantidad_disponible = equipo.cantidad_disponible

    categoria = (
        equipo.id_categoria.nombre
        if equipo.id_categoria
        else "No especificada"
    )

    fecha_registro = (
        equipo.fecha_registro.strftime("%d/%m/%Y %H:%M")
        if equipo.fecha_registro
        else "No registrada"
    )

    datos_equipo = [
        [
            Paragraph("Datos del Equipo", estilo_encabezado),
            ""
        ],
        [
            Paragraph("Nombre", estilo_campo),
            Paragraph(str(nombre), estilo_valor)
        ],
        [
            Paragraph("Código", estilo_campo),
            Paragraph(str(codigo), estilo_valor)
        ],
        [
            Paragraph("Categoría", estilo_campo),
            Paragraph(str(categoria), estilo_valor)
        ],
        [
            Paragraph("Fecha de Registro", estilo_campo),
            Paragraph(str(fecha_registro), estilo_valor)
        ],
        [
            Paragraph("Cantidad Disponible", estilo_campo),
            Paragraph(str(cantidad_disponible), estilo_valor)
        ],
        [
            Paragraph("Observación", estilo_campo),
            Paragraph(str(observacion), estilo_valor)
        ],
    ]

    tabla_equipo = Table(
        datos_equipo,
        colWidths=[145, 350],
        hAlign="CENTER"
    )

    tabla_equipo.setStyle(TableStyle([
        ("SPAN", (0, 0), (-1, 0)),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#00445F")),
        ("BACKGROUND", (0, 1), (0, -1), colors.HexColor("#00445F")),
        ("BACKGROUND", (1, 1), (1, -1), colors.white),

        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("TEXTCOLOR", (0, 1), (0, -1), colors.white),
        ("TEXTCOLOR", (1, 1), (1, -1), colors.black),

        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#00445F")),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#58A5C4")),

        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("ALIGN", (0, 1), (-1, -1), "LEFT"),

        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10)
    ]))

    ruta_logo = os.path.join(
        settings.BASE_DIR,
        "static",
        "Imagenes",
        "logo_hielo_caipe.png"
    )

    elementos = [
        Spacer(1, 10),
        tabla_equipo
    ]

    documento.build(
        elementos,
        onFirstPage=lambda canvas, documento:
            encabezado_datos_pdf(
                canvas,
                documento,
                ruta_logo
            ),
        onLaterPages=lambda canvas, documento:
            encabezado_datos_pdf(
                canvas,
                documento,
                ruta_logo
            )
    )

    return response

def encabezado_datos_pdf(canvas, documento, ruta_logo):
    canvas.saveState()

    # LOGO
    x_logo = 30
    y_logo = letter[1] - 150

    ancho_logo = 160
    alto_logo = 160

    canvas.drawImage(
        ruta_logo,
        x_logo,
        y_logo,
        width=ancho_logo,
        height=alto_logo,
        preserveAspectRatio=True,
        mask="auto"
    )

    # TITULO EMPRESA
    x_titulo = 185
    y_titulo = letter[1] - 70

    canvas.setFont("Times-Bold", 18)
    canvas.setFillColor(colors.HexColor("#00445F"))

    canvas.drawString(
        x_titulo,
        y_titulo,
        "EMPRESA HIELO CAIPE C.A"
    )

    # FECHA EN ESPAÑOL
    meses = [
        "Enero",
        "Febrero",
        "Marzo",
        "Abril",
        "Mayo",
        "Junio",
        "Julio",
        "Agosto",
        "Septiembre",
        "Octubre",
        "Noviembre",
        "Diciembre"
    ]

    fecha = datetime.now()

    fecha_actual = (
        f"{fecha.day} de "
        f"{meses[fecha.month - 1]} de "
        f"{fecha.year}"
    )

    # FECHA
    x_fecha = 210
    y_fecha = letter[1] - 120

    canvas.setFont("Times-Bold", 11)
    canvas.setFillColor(colors.HexColor("#072F3F"))

    canvas.drawString(
        x_fecha,
        y_fecha,
        f"Fecha Generado {fecha_actual}"
    )

    canvas.restoreState()

