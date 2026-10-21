from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.conf import settings

from inicio_sesion.models import usuarios,  bitacora, encargados_administrativos, supervisores_encargados

from asignaciones.models import asignacion_equipo, categoria_equipo, equipos, historial_entrega_equipo, entrega_equipos

import os
from datetime import datetime
from django.utils import timezone

from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
)

from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter

# EQUIPO RECIBIDO SUPERVISOR ENCARGADO

def categoria_equipo_recibido(request):
    cedula_supervisor = request.session.get("cedula_identidad")

    if not cedula_supervisor:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sesión no válida",
            "icon": "warning",
            "descripcion": "No se pudo identificar al supervisor encargado."
        }, status=401)

    supervisor = supervisores_encargados.objects.filter(
        id_usuario__cedula_identidad=cedula_supervisor,
        vigencia=True
    ).first()

    if not supervisor:
        return JsonResponse({
            "estado": "fallo",
            "title": "Supervisor no encontrado",
            "icon": "warning",
            "descripcion": "No se encontró un supervisor encargado activo."
        }, status=403)

    categorias = (
        categoria_equipo.objects
        .filter(
            equipos__entregas_supervisores__supervisor_encargado=supervisor
        )
        .distinct()
        .order_by("nombre")
    )

    datos = [
        {
            "id_categoria": categoria.id_categoria,
            "nombre": categoria.nombre
        }
        for categoria in categorias
    ]

    if not datos:
        return JsonResponse({
            "estado": "vacio",
            "title": "Sin categorías",
            "icon": "info",
            "descripcion": (
                "No hay categorías de equipos entregados a su usuario."
            ),
            "categorias": []
        })

    return JsonResponse({
        "estado": "exito",
        "title": "Categorías encontradas",
        "icon": "success",
        "descripcion": "Las categorías se cargaron correctamente.",
        "categorias": datos
    })

def visualizar_equipos_supervisor(request):
    if request.method != "POST":
        return render(
            request,
            "Entrega_Equipos/Supervisor/visualizar_recibido.html"
        )

    cedula_supervisor = request.session.get("cedula_identidad")

    if not cedula_supervisor:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sesión no válida",
            "icon": "warning",
            "descripcion": "No se pudo identificar al supervisor encargado."
        }, status=401)

    supervisor = supervisores_encargados.objects.filter(
        id_usuario__cedula_identidad=cedula_supervisor,
        vigencia=True
    ).first()

    if not supervisor:
        return JsonResponse({
            "estado": "fallo",
            "title": "Supervisor no encontrado",
            "icon": "warning",
            "descripcion": "No se encontró un supervisor encargado activo."
        }, status=403)

    entregas = (
        entrega_equipos.objects
        .filter(supervisor_encargado=supervisor)
        .select_related(
            "supervisor_encargado__id_turno",
            "supervisor_encargado__id_usuario",
            "id_equipo",
            "id_equipo__id_categoria"
        )
        .order_by("-fecha_entrega")
    )

    datos = [
        {
            "id_entrega": entrega.id_entrega,
            "equipo": entrega.id_equipo.nombre,
            "codigo": entrega.id_equipo.codigo,
            "categoria": entrega.id_equipo.id_categoria.nombre,
            "turno": entrega.supervisor_encargado.id_turno.nombre,
            "cantidad_entregada": entrega.cantidad_entregada,
            "cantidad_disponible": entrega.cantidad_disponible,
            "fecha_entrega": (
                timezone.localtime(
                    entrega.fecha_entrega
                ).strftime("%d/%m/%Y %H:%M")
                if entrega.fecha_entrega else ""
            ),
            "observacion": entrega.observacion,
            "estado": entrega.get_estado_display(),
            "motivo_incidencia": entrega.get_motivo_incidencia_display()
        }
        for entrega in entregas
    ]

    if not datos:
        return JsonResponse({
            "estado": "vacio",
            "title": "Sin equipos entregados",
            "icon": "info",
            "descripcion": "No hay equipos entregados a su usuario.",
            "equipos": []
        })

    return JsonResponse({
        "estado": "exito",
        "title": "Equipos recibidos",
        "icon": "success",
        "descripcion": "Los equipos recibidos se consultaron correctamente.",
        "equipos": datos
    })

def datos_equipo_recibido(request):
    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "title": "Solicitud inválida",
            "icon": "warning",
            "descripcion": "La solicitud debe realizarse mediante POST."
        }, status=405)

    id_recibido = request.POST.get("id_recibido", "").strip()
    cedula_supervisor = request.session.get("cedula_identidad")

    if not cedula_supervisor:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sesión no válida",
            "icon": "warning",
            "descripcion": "No se pudo identificar al supervisor encargado."
        }, status=401)

    if not id_recibido or not id_recibido.isdigit():
        return JsonResponse({
            "estado": "fallo",
            "title": "Identificador inválido",
            "icon": "warning",
            "descripcion": "Debe indicar una entrega válida."
        })

    supervisor = supervisores_encargados.objects.filter(
        id_usuario__cedula_identidad=cedula_supervisor,
        vigencia=True
    ).first()

    if not supervisor:
        return JsonResponse({
            "estado": "fallo",
            "title": "Supervisor no encontrado",
            "icon": "warning",
            "descripcion": "No se encontró un supervisor encargado activo."
        }, status=403)

    entrega = (
        entrega_equipos.objects
        .filter(
            id_entrega=int(id_recibido),
            supervisor_encargado=supervisor
        )
        .select_related(
            "supervisor_encargado__id_usuario",
            "supervisor_encargado__id_turno",
            "id_equipo__id_categoria"
        )
        .first()
    )

    if not entrega:
        return JsonResponse({
            "estado": "vacio",
            "title": "Entrega no encontrada",
            "icon": "warning",
            "descripcion": "No se encontró la entrega del equipo seleccionado."
        }, status=404)

    equipo = entrega.id_equipo
    categoria = equipo.id_categoria

    datos = {
        "id_categoria": categoria.id_categoria,
        "categoria": categoria.nombre,

        "id_equipo": equipo.id_equipo,
        "nombre_equipo": equipo.nombre,
        "codigo_equipo": equipo.codigo,

        "id_entrega": entrega.id_entrega,
        "cantidad_entregada": entrega.cantidad_entregada,
        "cantidad_disponible_entrega": entrega.cantidad_disponible,

        "fecha_entrega": (
            timezone.localtime(
                entrega.fecha_entrega
            ).strftime("%d/%m/%Y %H:%M")
            if entrega.fecha_entrega else ""
        ),

        "observacion_entrega": entrega.observacion,
        "estado": entrega.estado,
        "estado_display": entrega.get_estado_display(),
        "motivo_incidencia": entrega.motivo_incidencia,
        "motivo_incidencia_display": (
            entrega.get_motivo_incidencia_display()
        ),
        "turno": entrega.supervisor_encargado.id_turno.nombre
    }

    return JsonResponse({
        "estado": "exito",
        "title": "Detalle del equipo",
        "icon": "success",
        "equipo": datos
    })

def lista_equipos_recibido_pdf(request):
    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "title": "Solicitud inválida",
            "icon": "warning",
            "descripcion": "La solicitud debe realizarse mediante POST."
        }, status=405)

    categoria = request.POST.get("categoria", "").strip()
    cedula_supervisor = request.session.get("cedula_identidad")

    if not cedula_supervisor:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sesión no válida",
            "icon": "warning",
            "descripcion": "No se pudo identificar al supervisor encargado."
        }, status=401)

    supervisor = supervisores_encargados.objects.filter(
        id_usuario__cedula_identidad=cedula_supervisor,
        vigencia=True
    ).first()

    if not supervisor:
        return JsonResponse({
            "estado": "fallo",
            "title": "Supervisor no encontrado",
            "icon": "warning",
            "descripcion": "No se encontró un supervisor encargado activo."
        }, status=403)

    entregas = (
        entrega_equipos.objects
        .filter(supervisor_encargado=supervisor)
        .select_related(
            "id_equipo",
            "id_equipo__id_categoria"
        )
    )

    if categoria:
        if not categoria.isdigit():
            return JsonResponse({
                "estado": "fallo",
                "title": "Categoría inválida",
                "icon": "warning",
                "descripcion": "La categoría seleccionada no es válida."
            })

        entregas = entregas.filter(
            id_equipo__id_categoria_id=int(categoria)
        )

    entregas = entregas.order_by("-fecha_entrega")

    # Validar antes de crear la respuesta PDF.
    if not entregas.exists():
        return JsonResponse({
            "estado": "vacio",
            "title": "Sin equipos recibidos",
            "descripcion": (
                "No se encontraron equipos recibidos "
                "con los filtros seleccionados. No se generó el PDF."
            ),
            "icon": "warning"
        })

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        'inline; filename="equipos_recibidos.pdf"'
    )

    documento = SimpleDocTemplate(
        response,
        pagesize=letter,
        rightMargin=30,
        leftMargin=30,
        topMargin=140,
        bottomMargin=35
    )

    estilos = getSampleStyleSheet()

    estilo_titulo = ParagraphStyle(
        "TituloEquiposRecibidos",
        parent=estilos["Normal"],
        fontName="Times-Bold",
        fontSize=13,
        leading=16,
        alignment=TA_CENTER,
        textColor=colors.white
    )

    estilo_encabezado = ParagraphStyle(
        "EncabezadoColumnasEquiposRecibidos",
        parent=estilos["Normal"],
        fontName="Times-Bold",
        fontSize=8,
        leading=10,
        alignment=TA_CENTER,
        textColor=colors.white
    )

    estilo_celda = ParagraphStyle(
        "CeldaEquiposRecibidos",
        parent=estilos["Normal"],
        fontName="Times-Roman",
        fontSize=8,
        leading=10,
        alignment=TA_CENTER,
        textColor=colors.black,
        wordWrap="CJK"
    )

    def texto_seguro(valor, predeterminado="No especificado"):
        valor = str(valor).strip() if valor is not None else ""
        return escape(valor) if valor else predeterminado

    datos_tabla = [
        [
            Paragraph("EQUIPOS RECIBIDOS", estilo_titulo),
            "", "", "", "", ""
        ],
        [
            Paragraph("N.º", estilo_encabezado),
            Paragraph("Equipo", estilo_encabezado),
            Paragraph("Código", estilo_encabezado),
            Paragraph("Cantidad entregada", estilo_encabezado),
            Paragraph("Cantidad disponible", estilo_encabezado),
            Paragraph("Fecha de entrega", estilo_encabezado)
        ]
    ]

    for numero, entrega in enumerate(entregas, start=1):
        equipo = entrega.id_equipo

        datos_tabla.append([
            Paragraph(str(numero), estilo_celda),
            Paragraph(texto_seguro(equipo.nombre), estilo_celda),
            Paragraph(texto_seguro(equipo.codigo), estilo_celda),
            Paragraph(str(entrega.cantidad_entregada), estilo_celda),
            Paragraph(str(entrega.cantidad_disponible), estilo_celda),
            Paragraph(
                timezone.localtime(entrega.fecha_entrega).strftime(
                    "%d/%m/%Y %H:%M"
                ) if entrega.fecha_entrega else "No especificada",
                estilo_celda
            )
        ])

    tabla = Table(
        datos_tabla,
        colWidths=[35, 115, 90, 100, 105, 95],
        repeatRows=2,
        hAlign="CENTER"
    )

    tabla.setStyle(TableStyle([
        ("SPAN", (0, 0), (-1, 0)),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#00445F")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 13),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),

        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#00445F")),
        ("TEXTCOLOR", (0, 1), (-1, 1), colors.white),
        ("FONTNAME", (0, 1), (-1, 1), "Times-Bold"),
        ("FONTSIZE", (0, 1), (-1, 1), 8),
        ("ALIGN", (0, 1), (-1, 1), "CENTER"),

        ("BACKGROUND", (0, 2), (-1, -1), colors.white),
        ("TEXTCOLOR", (0, 2), (-1, -1), colors.black),
        ("FONTNAME", (0, 2), (-1, -1), "Times-Roman"),
        ("FONTSIZE", (0, 2), (-1, -1), 8),
        ("ALIGN", (0, 2), (-1, -1), "CENTER"),

        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#00445F")),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#58A5C4")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
    ]))

    ruta_logo = os.path.join(
        settings.BASE_DIR,
        "static",
        "Imagenes",
        "logo_hielo_caipe.png"
    )

    documento.build(
        [tabla],
        onFirstPage=lambda canvas, doc:
            encabezado_lista_equipos_recibido_pdf(
                canvas, doc, ruta_logo
            ),
        onLaterPages=lambda canvas, doc:
            encabezado_lista_equipos_recibido_pdf(
                canvas, doc, ruta_logo
            )
    )

    return response

def encabezado_lista_equipos_recibido_pdf(canvas, documento, ruta_logo):
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
    x_titulo = 178
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

def datos_equipo_recibido_pdf(request):
    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "title": "Método no permitido",
            "descripcion": "La solicitud debe realizarse mediante POST.",
            "icon": "warning"
        }, status=405)

    id_entrega = request.POST.get("id_entrega", "").strip()
    cedula_supervisor = request.session.get("cedula_identidad")

    if not cedula_supervisor:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sesión no válida",
            "descripcion": "No se pudo identificar al supervisor encargado.",
            "icon": "warning"
        }, status=401)

    if not id_entrega:
        return JsonResponse({
            "estado": "vacio",
            "title": "Entrega no seleccionada",
            "descripcion": "Debe seleccionar una entrega para generar el reporte.",
            "icon": "warning"
        }, status=400)

    if not id_entrega.isdigit() or int(id_entrega) <= 0:
        return JsonResponse({
            "estado": "fallo",
            "title": "Identificador inválido",
            "descripcion": "El identificador de la entrega no es válido.",
            "icon": "warning"
        }, status=400)

    supervisor_autenticado = supervisores_encargados.objects.filter(
        id_usuario__cedula_identidad=cedula_supervisor,
        vigencia=True
    ).first()

    if not supervisor_autenticado:
        return JsonResponse({
            "estado": "fallo",
            "title": "Supervisor no encontrado",
            "descripcion": "No se encontró un supervisor encargado activo.",
            "icon": "warning"
        }, status=403)

    entrega = (
        entrega_equipos.objects
        .select_related(
            "supervisor_encargado",
            "id_equipo",
            "id_equipo__id_categoria"
        )
        .filter(
            id_entrega=int(id_entrega),
            supervisor_encargado=supervisor_autenticado
        )
        .first()
    )

    if not entrega:
        return JsonResponse({
            "estado": "vacio",
            "title": "Entrega no encontrada",
            "descripcion": (
                "La entrega seleccionada no existe "
                "o no pertenece al supervisor autenticado."
            ),
            "icon": "warning"
        }, status=404)

    equipo = entrega.id_equipo
    categoria = equipo.id_categoria

    estilos = getSampleStyleSheet()

    estilo_encabezado = ParagraphStyle(
        "EncabezadoEquipoRecibido",
        parent=estilos["Normal"],
        fontName="Times-Bold",
        fontSize=12,
        leading=14,
        alignment=TA_CENTER,
        textColor=colors.white
    )

    estilo_campo = ParagraphStyle(
        "CampoEquipoRecibido",
        parent=estilos["Normal"],
        fontName="Times-Bold",
        fontSize=10,
        leading=13,
        textColor=colors.white
    )

    estilo_valor = ParagraphStyle(
        "ValorEquipoRecibido",
        parent=estilos["Normal"],
        fontName="Times-Roman",
        fontSize=10,
        leading=13,
        textColor=colors.black,
        wordWrap="CJK"
    )

    def texto_seguro(valor, predeterminado="No especificado"):
        valor = str(valor).strip() if valor is not None else ""
        return escape(valor) if valor else predeterminado

    fecha_entrega = (
        timezone.localtime(entrega.fecha_entrega).strftime("%d/%m/%Y %H:%M")
        if entrega.fecha_entrega
        else "No especificada"
    )

    datos_entrega = [
        [
            Paragraph("Datos del Equipo Recibido", estilo_encabezado),
            ""
        ],
        [
            Paragraph("Equipo", estilo_campo),
            Paragraph(texto_seguro(equipo.nombre), estilo_valor)
        ],
        [
            Paragraph("Categoría", estilo_campo),
            Paragraph(
                texto_seguro(categoria.nombre if categoria else None),
                estilo_valor
            )
        ],
        [
            Paragraph("Código", estilo_campo),
            Paragraph(texto_seguro(equipo.codigo), estilo_valor)
        ],
        [
            Paragraph("Cantidad entregada", estilo_campo),
            Paragraph(str(entrega.cantidad_entregada), estilo_valor)
        ],
        [
            Paragraph("Cantidad disponible", estilo_campo),
            Paragraph(str(entrega.cantidad_disponible), estilo_valor)
        ],
        [
            Paragraph("Estado", estilo_campo),
            Paragraph(texto_seguro(entrega.get_estado_display()), estilo_valor)
        ],
        [
            Paragraph("Motivo de incidencia", estilo_campo),
            Paragraph(
                texto_seguro(entrega.get_motivo_incidencia_display()),
                estilo_valor
            )
        ],
        [
            Paragraph("Fecha de entrega", estilo_campo),
            Paragraph(fecha_entrega, estilo_valor)
        ],
        [
            Paragraph("Observación", estilo_campo),
            Paragraph(
                texto_seguro(entrega.observacion, "Sin observaciones"),
                estilo_valor
            )
        ]
    ]

    tabla_entrega = Table(
        datos_entrega,
        colWidths=[175, 320],
        hAlign="CENTER"
    )

    tabla_entrega.setStyle(TableStyle([
        ("SPAN", (0, 0), (-1, 0)),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#00445F")),
        ("BACKGROUND", (0, 1), (0, -1), colors.HexColor("#00445F")),
        ("BACKGROUND", (1, 1), (1, -1), colors.white),

        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("TEXTCOLOR", (0, 1), (0, -1), colors.white),
        ("TEXTCOLOR", (1, 1), (1, -1), colors.black),

        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#00445F")),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#58A5C4")),

        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 1), (-1, -1), "LEFT"),

        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))

    ruta_logo = os.path.join(
        settings.BASE_DIR,
        "static",
        "Imagenes",
        "logo_hielo_caipe.png"
    )

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'inline; filename="equipo_recibido_{entrega.id_entrega}.pdf"'
    )

    documento = SimpleDocTemplate(
        response,
        pagesize=letter,
        rightMargin=45,
        leftMargin=45,
        topMargin=100,
        bottomMargin=40
    )

    elementos = [
        Spacer(1, 25),
        tabla_entrega,
        Spacer(1, 25)
    ]

    documento.build(
        elementos,
        onFirstPage=lambda canvas, doc:
            encabezado_datos_recibido_pdf(canvas, doc, ruta_logo),
        onLaterPages=lambda canvas, doc:
            encabezado_datos_recibido_pdf(canvas, doc, ruta_logo)
    )

    return response

def encabezado_datos_recibido_pdf(canvas, documento, ruta_logo):
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
