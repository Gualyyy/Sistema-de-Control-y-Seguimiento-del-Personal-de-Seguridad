from django.shortcuts import render
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.db.models import Sum, F
from django.conf import settings

from inicio_sesion.models import usuarios, categoria_equipo, equipos, bitacora

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
    if request.method == "POST":
        nombre = request.POST.get("nombre")
        codigo = request.POST.get("codigo")
        cantidad_total = request.POST.get("cantidad_total")
        id_categoria = request.POST.get("categoria_equipo")

        if request.POST.get("observacion"):
            observacion = request.POST.get("observacion")
        else:
            observacion = "N/A"

        campos = [
            (nombre, "Nombre del Equipo", "Por favor, debe ingrese el nombre del equipo."),
            (cantidad_total, "Cantidad Total", "Por favor, debe ingrese la cantidad total del equipo."),
            (id_categoria, "Categoría", "Por favor, debe seleccionar una categoría.")
        ]

        for valor, _, mensaje in campos:
            if not valor:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Vacío",
                    "descripcion": mensaje,
                    "icon": "warning"
                })

        if equipos.objects.filter(codigo=codigo).exists():
            return JsonResponse({
                "estado": "fallo",
                "title": "Código existente",
                "descripcion": "El código generado ya existe.",
                "icon": "warning"
            })

        try:
            categoria = categoria_equipo.objects.get(pk=id_categoria)
        except categoria_equipo.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "title": "Error",
                "descripcion": "La categoría seleccionada no existe.",
                "icon": "error"
            })

        try:
            with transaction.atomic():
                
                equipos.objects.create(
                    nombre=nombre,
                    codigo=codigo,
                    observacion=observacion,
                    cantidad_total=cantidad_total,
                    cantidad_disponible=cantidad_total,
                    id_categoria=categoria
                )
        
                info_usuario = usuarios.objects.get(cedula_identidad=request.session.get("cedula_identidad"))
                accion = f"Registro del equipo {nombre} {codigo} {cantidad_total} {categoria.nombre}"
                
                bitacora.objects.create(
                    id_usuario=info_usuario,
                    accion=accion
                )
                return JsonResponse({
                    "estado": "exito",
                    "title": "Exito",
                    "descripcion": "El equipo fue registrado correctamente.",
                    "icon": "success"
                })
        except Exception as e:
            print("ERROR AL REGISTRAR EQUIPO:", e)
            return JsonResponse({
                "estado": "fallo",
                "title": "Error",
                "descripcion": "Ocurrio un error al momento de registrar al equipo.",
                "icon": "error"
            })

    return render(request, "Modulos/registro_equipos.html")

# BUSCAR LOS DATOS DEL EQUIPOS

def buscar_equipos(request):
    if request.method == "POST":
        codigo = request.POST.get("codigo_equipo")

        if not codigo:
            return JsonResponse({
                "estado": "fallo",
                "title": "Vacío",
                "descripcion": "No se recibió el identificador del equipo.",
                "icon": "warning"
            })

        try:
            equipo = equipos.objects.select_related(
                "id_categoria"
            ).get(codigo=codigo)

            cantidad_asignada = (
                equipo.asignaciones
                .filter(
                    estado__in=["Asignado", "Parcial"]
                )
                .aggregate(
                    total=Sum(
                        F("cantidad_asignada") -
                        F("cantidad_devuelta")
                    )
                )["total"] or 0
            )

            return JsonResponse({
                "estado": "exito",
                "equipo": {
                    "id_equipo": equipo.id_equipo,
                    "nombre": equipo.nombre,
                    "codigo": equipo.codigo,
                    "observacion": equipo.observacion,
                    "cantidad_total": equipo.cantidad_total,
                    "cantidad_disponible": equipo.cantidad_disponible,
                    "cantidad_asignada": cantidad_asignada,
                    "id_categoria": equipo.id_categoria.id_categoria,
                    "categoria": equipo.id_categoria.nombre,
                }
            })

        except equipos.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "title": "No encontrado",
                "descripcion": "El equipo no existe.",
                "icon": "error"
            })

        except Exception as e:
            return JsonResponse({
                "estado": "fallo",
                "title": "Error",
                "descripcion": str(e),
                "icon": "error"
            })
        
# ACTUALIZAR LOS DATOS DEL EQUIPO

def actualizacion_equipos(request):
    if request.method == "POST":
        equipo_id = request.POST.get("equipo_id")
        nombre = request.POST.get("nombre")
        observacion = request.POST.get("observacion")
        cantidad_total = request.POST.get("cantidad_total")
        categoria = request.POST.get("categoria_equipo")

        campos = [
            (nombre, "Nombre del Equipo", "Por favor, ingrese el nombre del equipo."),
            (cantidad_total, "Cantidad Total",  "Por favor, ingresar la cantidad total de equipo."),
            (categoria, "Categoria de Equipo", "Por favor, seleccione la categoria de equipo."),
        ]

        for valor, campo, mensaje in campos:
            if not valor:
                return JsonResponse({
                    "estado": "fallo",
                    "title": campo,
                    "descripcion": mensaje,
                    "icon": "warning"
                })

        nombre_existente = (
            equipos.objects
            .filter(nombre__iexact=nombre)
            .exclude(id_equipo=equipo_id)
            .exists()
        )

        if nombre_existente:
            return JsonResponse({
                "estado": "fallo",
                "title": "Error",
                "descripcion": (
                    "Ingrese otro nombre para el equipo, "
                    "ya se encuentra uno registrado."
                ),
                "icon": "error"
            })

        try:
            nueva_cantidad_total = int(cantidad_total)

            if nueva_cantidad_total <= 0:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Cantidad Total",
                    "descripcion": (
                        "La cantidad total debe ser un número entero "
                        "mayor a 0."
                    ),
                    "icon": "warning"
                })

            with transaction.atomic():
                info_categoria = categoria_equipo.objects.get(
                    pk=categoria
                )

                info_equipo = (
                    equipos.objects
                    .select_for_update()
                    .get(id_equipo=equipo_id)
                )

                cantidad_asignada = (
                    info_equipo.asignaciones
                    .filter(
                        estado__in=["Asignado", "Parcial"]
                    )
                    .aggregate(
                        total=Sum(
                            F("cantidad_asignada") -
                            F("cantidad_devuelta")
                        )
                    )["total"] or 0
                )

                if nueva_cantidad_total < cantidad_asignada:
                    return JsonResponse({
                        "estado": "fallo",
                        "title": "Cantidad no válida",
                        "descripcion": (
                            f"La cantidad total no puede ser menor a "
                            f"{cantidad_asignada} "
                            f"{'unidad' if cantidad_asignada == 1 else 'unidades'} "
                            "actualmente asignadas."
                        ),
                        "icon": "warning"
                    })

                nueva_cantidad_disponible = (
                    nueva_cantidad_total - cantidad_asignada
                )

                info_equipo.nombre = nombre
                info_equipo.observacion = observacion
                info_equipo.cantidad_total = nueva_cantidad_total
                info_equipo.cantidad_disponible = nueva_cantidad_disponible
                info_equipo.id_categoria = info_categoria

                info_equipo.save()

                info_usuario = usuarios.objects.get(
                    cedula_identidad=request.session.get(
                        "cedula_identidad"
                    )
                )

                accion = (
                    f"Actualización del equipo "
                    f"{nombre} {cantidad_total} "
                    f"{info_categoria.nombre}"
                )

                bitacora.objects.create(
                    id_usuario=info_usuario,
                    accion=accion
                )

                return JsonResponse({
                    "estado": "exito",
                    "title": "Exito",
                    "descripcion": (
                        "El equipo fue actualizado correctamente."
                    ),
                    "icon": "success"
                })

        except (ValueError, TypeError):
            return JsonResponse({
                "estado": "fallo",
                "title": "Cantidad Total",
                "descripcion": (
                    "La cantidad total debe ser un número entero válido."
                ),
                "icon": "warning"
            })

        except categoria_equipo.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "title": "Categoria",
                "descripcion": "La categoria de equipo no existe.",
                "icon": "error"
            })

        except equipos.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "title": "Equipo",
                "descripcion": "El equipo no existe.",
                "icon": "error"
            })

        except Exception:
            return JsonResponse({
                "estado": "fallo",
                "title": "Error",
                "descripcion": (
                    "Ocurrio un error al momento de actualizar el equipo."
                ),
                "icon": "error"
            })
        
    return render(request, "Modulos/actualizar_equipo.html")

# VISUALIZAR TODOS LOS EQUIPOS REGISTRADOS 

def visualizacion_equipos(request):
    if request.method == "POST":
        codigo = request.POST.get("codigo", "").strip()
        categoria = request.POST.get("categoria", "").strip()

        lista_equipos = equipos.objects.select_related("id_categoria")

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
                "cantidad_total": equipo.cantidad_total,
                "cantidad_disponible": equipo.cantidad_disponible,
                "observacion": equipo.observacion or "",
            })

        return JsonResponse(datos, safe=False)

    return render(request, "Modulos/visualizar_equipos.html")

# REPORTE DE TODOS LOS EQUIPOS

def lista_equipos_pdf(request):
    categoria = request.POST.get("categoria", "").strip()

    lista_equipos = equipos.objects.select_related("id_categoria")

    if categoria.isdigit():
        lista_equipos = lista_equipos.filter(
            id_categoria__id_categoria=int(categoria)
        )

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
        topMargin=100,
        bottomMargin=30
    )

    # ESTILOS
    estilos = getSampleStyleSheet()

    estilo_titulo = ParagraphStyle(
        "TituloEquipos",
        parent=estilos["Heading2"],
        fontName="Times-Bold",
        fontSize=14,
        leading=18,
        alignment=TA_CENTER,
        textColor=colors.black
    )

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

    # DATOS TABLA
    datos_tabla = [
        [
            Paragraph("Lista Equipos", estilo_encabezado),
            "",
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
            Paragraph("Cantidad Total", estilo_encabezado),
            Paragraph("Disponible", estilo_encabezado),
        ]
    ]

    # EQUIPOS
    for numero, equipo in enumerate(lista_equipos, start=1):

        nombre = equipo.nombre or "No especificado"
        codigo = equipo.codigo or "No especificado"

        if equipo.id_categoria:
            categoria_nombre = equipo.id_categoria.nombre
        else:
            categoria_nombre = "No especificada"

        cantidad_total = equipo.cantidad_total
        cantidad_disponible = equipo.cantidad_disponible

        datos_tabla.append([
            Paragraph(str(numero), estilo_celda),
            Paragraph(str(nombre), estilo_celda),
            Paragraph(str(codigo), estilo_celda),
            Paragraph(str(categoria_nombre), estilo_celda),
            Paragraph(str(cantidad_total), estilo_celda),
            Paragraph(str(cantidad_disponible), estilo_celda),
        ])

    # TABLA
    tabla = Table(
        datos_tabla,
        colWidths=[
            40,
            100,
            85,
            130,
            75,
            75
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
    elementos = []

    elementos.append(
        Paragraph(
            "",
            estilo_titulo
        )
    )

    elementos.append(
        Spacer(1, 15)
    )

    elementos.append(
        tabla
    )

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

def datos_equipos_pnf(request):
    if request.method == "POST":
        id_equipo = request.POST.get("id_equipo", "").strip()

        # BUSCAR EQUIPO
        equipo = equipos.objects.get(id_equipo=id_equipo)

        response = HttpResponse(content_type="application/pdf")

        response["Content-Disposition"] = (
            f'inline; filename="equipo_{equipo.id_equipo}.pdf"'
        )

        documento = SimpleDocTemplate(
            response,
            pagesize=letter,
            rightMargin=45,
            leftMargin=45,
            topMargin=100,
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
            textColor=colors.white,
        )

        estilo_campo = ParagraphStyle(
            "CampoEquipo",
            parent=estilos["Normal"],
            fontName="Times-Bold",
            fontSize=12,
            leading=12,
            textColor=colors.white,
        )

        estilo_valor = ParagraphStyle(
            "ValorEquipo",
            parent=estilos["Normal"],
            fontName="Times-Roman",
            fontSize=12,
            leading=12,
            textColor=colors.black,
        )

        estilo_observacion = ParagraphStyle(
            "ObservacionEquipo",
            parent=estilos["Normal"],
            fontName="Times-Roman",
            fontSize=12,
            leading=12,
            textColor=colors.black,
        )

        nombre = equipo.nombre or "No especificado"
        codigo = equipo.codigo or "No especificado"
        observacion = equipo.observacion or "Sin observaciones"
        cantidad_total = equipo.cantidad_total
        cantidad_disponible = equipo.cantidad_disponible

        if equipo.id_categoria:
            categoria = equipo.id_categoria.nombre
        else:
            categoria = "No especificada"

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
                Paragraph("Cantidad Total", estilo_campo),
                Paragraph(str(cantidad_total), estilo_valor)
            ],
            [
                Paragraph("Cantidad Disponible", estilo_campo),
                Paragraph(str(cantidad_disponible), estilo_valor)
            ],
            [
                Paragraph("Observación", estilo_campo),
                Paragraph(str(observacion), estilo_observacion)
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
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),

            ("BACKGROUND", (0, 1), (0, -1), colors.HexColor("#00445F")),
            ("BACKGROUND", (1, 1), (1, -1), colors.white),

            ("TEXTCOLOR", (0, 1), (0, -1), colors.white),
            ("TEXTCOLOR", (1, 1), (1, -1), colors.black),

            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#00445F")),
            ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#58A5C4")),

            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 1), (-1, -1), "LEFT"),

            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ]))

        # LOGO
        ruta_logo = os.path.join(
            settings.BASE_DIR,
            "static",
            "Imagenes",
            "logo_hielo_caipe.png"
        )

        # ELEMENTOS
        elementos = []

        elementos.append(
            Spacer(1, 25)
        )

        elementos.append(
            tabla_equipo
        )

        elementos.append(
            Spacer(1, 25)
        )

        # GENERAR PDF
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

