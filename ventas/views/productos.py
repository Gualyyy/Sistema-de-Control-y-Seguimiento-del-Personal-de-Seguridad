from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.db import transaction, IntegrityError, DatabaseError
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.files.images import get_image_dimensions
from django.utils.text import get_valid_filename
from django.db.models import Q

from ventas.models import categoria_producto, unidad_medida, producto, existencia_inventario, tipo_movimiento, movimiento_inventario, precio_volumen
from inicio_sesion.models import bitacora, usuarios

import os
import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.conf import settings
from datetime import datetime

from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Image
)

from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from xml.sax.saxutils import escape

# Create your views here.

# GESTION DE CATEGORIAS DE PRODUCTOS

def buscar_categoria(request):
    if request.method == "POST":
        id_categoria = request.POST.get("id_categoria")

        if not id_categoria:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Dato requerido",
                "descripcion": "No se recibió el identificador de la categoría."
            })

        try:
            categoria = categoria_producto.objects.get(id_categoria=id_categoria)

            return JsonResponse({
                "estado": "exito",
                "id_categoria": categoria.id_categoria,
                "nombre": categoria.nombre,
                "activo": categoria.activo
            })

        except categoria_producto.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Categoría no encontrada",
                "descripcion": "La categoría solicitada no existe."
            })

def gestionar_categorias(request):
    return render(request, "Productos/gestionar_categorias.html")

def registrar_categorias(request):
    if request.method == "POST":
        nombre_categoria = request.POST.get("nombre_categoria", "").strip()

        if not nombre_categoria:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Campo obligatorio",
                "descripcion": "Debe ingresar el nombre de la categoría."
            })

        if len(nombre_categoria) > 50:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Nombre demasiado largo",
                "descripcion": "El nombre de la categoría no puede superar los 50 caracteres."
            })

        if categoria_producto.objects.filter(nombre__iexact=nombre_categoria).exists():
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Categoría existente",
                "descripcion": "Ya existe una categoría con ese nombre."
            })

        try:
            categoria_producto.objects.create(
                nombre=nombre_categoria,
                activo=True
            )

            return JsonResponse({
                "estado": "exito",
                "icon": "success",
                "title": "Categoría registrada",
                "descripcion": "La categoría se registró correctamente."
            })

        except IntegrityError:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Error al registrar",
                "descripcion": "No fue posible registrar la categoría."
            })

def actualizar_categoria(request):
    if request.method == "POST":
        id_categoria = request.POST.get("id_categoria", "").strip()
        nombre_categoria = request.POST.get("nuevo_nombre", "").strip()

        if not id_categoria or not id_categoria.isdigit():
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Categoría no válida",
                "descripcion": "No se recibió un identificador de categoría válido."
            })

        if not nombre_categoria:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Campo obligatorio",
                "descripcion": "Debe ingresar el nombre de la categoría."
            })

        if len(nombre_categoria) > 50:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Nombre demasiado largo",
                "descripcion": "El nombre de la categoría no puede superar los 50 caracteres."
            })

        try:
            categoria = categoria_producto.objects.get(
                id_categoria=id_categoria
            )

            # Verificar que no exista otra categoría con el mismo nombre.
            if categoria_producto.objects.filter(
                nombre__iexact=nombre_categoria
            ).exclude(
                id_categoria=id_categoria
            ).exists():
                return JsonResponse({
                    "estado": "fallo",
                    "icon": "warning",
                    "title": "Categoría existente",
                    "descripcion": "Ya existe otra categoría con ese nombre."
                })

            categoria.nombre = nombre_categoria
            categoria.save(update_fields=["nombre"])

            return JsonResponse({
                "estado": "exito",
                "icon": "success",
                "title": "Categoría actualizada",
                "descripcion": "La categoría se actualizó correctamente."
            })

        except categoria_producto.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Categoría no encontrada",
                "descripcion": "La categoría que intenta actualizar no existe."
            })

        except IntegrityError:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Error al actualizar",
                "descripcion": "No fue posible actualizar la categoría."
            })

def categorias_productos(request):
    categorias = categoria_producto.objects.order_by("nombre")

    datos = [
        {
            "id_categoria": categoria.id_categoria,
            "nombre": categoria.nombre,
            "activo": categoria.activo
        }
        for categoria in categorias
    ]

    return JsonResponse(datos, safe=False)

def estado_categoria(request):
    if request.method == "POST":
        id_categoria = request.POST.get("id_categoria", "").strip()
        estado = request.POST.get("estado", "").strip()

        if not id_categoria or not id_categoria.isdigit():
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Categoría no válida",
                "descripcion": "No se recibió un identificador de categoría válido."
            })

        if estado not in ["true", "false"]:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Estado no válido",
                "descripcion": "El estado proporcionado no es válido."
            })

        try:
            categoria = categoria_producto.objects.get(id_categoria=id_categoria)

            nuevo_estado = estado == "true"

            if categoria.activo == nuevo_estado:
                return JsonResponse({
                    "estado": "fallo",
                    "icon": "info",
                    "title": "Sin cambios",
                    "descripcion": "La categoría ya se encuentra en ese estado."
                })

            categoria.activo = nuevo_estado
            categoria.save(update_fields=["activo"])

            return JsonResponse({
                "estado": "exito",
                "icon": "success",
                "title": "Estado actualizado",
                "descripcion": (
                    "La categoría se activó correctamente."
                    if nuevo_estado else
                    "La categoría se desactivó correctamente."
                )
            })

        except categoria_producto.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Categoría no encontrada",
                "descripcion": "La categoría que intenta modificar no existe."
            })

# ACTUALIZAR ESTADO PRODUCTO

def estado_producto(request):
    codigo = request.POST.get("codigo", "").strip()

    if not codigo:
        return JsonResponse({
            "estado": "fallo",
            "titulo": "Producto no válido",
            "icon": "warning",
            "descripcion": "El código del producto no es válido."
        })

    try:
        with transaction.atomic():
            producto_obj = producto.objects.select_for_update().get(
                codigo=codigo
            )

            producto_obj.activo = not producto_obj.activo
            producto_obj.save(update_fields=["activo"])

        return JsonResponse({
            "estado": "exito",
            "titulo": "Estado actualizado",
            "icon": "success",
            "descripcion": (
                "El producto ha sido activado correctamente."
                if producto_obj.activo
                else "El producto ha sido desactivado correctamente."
            ),
            "activo": producto_obj.activo,
            "id_producto": producto_obj.id_producto
        })

    except producto.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "titulo": "Producto no encontrado",
            "icon": "warning",
            "descripcion": "El producto solicitado no existe."
        })

    except Exception:
        return JsonResponse({
            "estado": "fallo",
            "titulo": "Error del sistema",
            "icon": "error",
            "descripcion": "No se pudo actualizar el estado del producto."
        })

# VALORES PREVIAMENTE ALMACENADO

def unidades_medida(request):
    unidades = unidad_medida.objects.order_by("nombre")

    datos = [
        {
            "id_unidad": unidad.id_unidad,
            "nombre": unidad.nombre,
            "abreviatura": unidad.abreviatura,
            "permite_decimales": unidad.permite_decimales
        }
        for unidad in unidades
    ]

    return JsonResponse(datos, safe=False)

# REGISTRO DE PRODUCTOS

def registrar_productos(request):
    if request.method != "POST":
        return render(request, "Productos/registrar_productos.html")

    nombre_producto = request.POST.get("nombre_producto", "").strip()
    codigo_producto = request.POST.get("codigo_producto", "").strip()
    precio_base_str = request.POST.get("precio_base", "").strip()
    costo_base_str = request.POST.get("costo_base", "").strip()
    imagen_producto = request.FILES.get("imagen_producto")
    categoria = request.POST.get("categoria_producto", "").strip()
    unidad = request.POST.get("unidad_producto", "").strip()

    campos = [
        (nombre_producto, "Nombre del producto", "Por favor, ingresa el nombre del producto."),
        (codigo_producto, "Código del producto", "Por favor, ingresa el código del producto."),
        (precio_base_str, "Precio base", "Por favor, ingresa el precio base en USD."),
        (costo_base_str, "Costo base", "Por favor, ingresa el costo base en USD."),
        (imagen_producto, "Imagen del producto", "Por favor, selecciona una imagen del producto."),
        (categoria, "Categoría del producto", "Por favor, selecciona una categoría."),
        (unidad, "Unidad de medida", "Por favor, selecciona una unidad de medida."),
    ]

    for valor, campo, mensaje in campos:
        if not valor:
            return JsonResponse({
                "estado": "fallo",
                "title": campo,
                "descripcion": mensaje,
                "icon": "warning"
            })

    if len(nombre_producto) > 100:
        return JsonResponse({
            "estado": "fallo",
            "title": "Nombre del producto",
            "descripcion": "El nombre no puede superar los 100 caracteres.",
            "icon": "warning"
        })

    if len(codigo_producto) > 50:
        return JsonResponse({
            "estado": "fallo",
            "title": "Código del producto",
            "descripcion": "El código no puede superar los 50 caracteres.",
            "icon": "warning"
        })

    if producto.objects.filter(codigo__iexact=codigo_producto).exists():
        return JsonResponse({
            "estado": "fallo",
            "title": "Código duplicado",
            "descripcion": "Ya existe un producto registrado con ese código.",
            "icon": "warning"
        })

    patron_precio = r"^\d{1,3}(?:\.\d{1,2})?$"

    for valor, campo in [
        (precio_base_str, "Precio base"),
        (costo_base_str, "Costo base"),
    ]:
        if not re.fullmatch(patron_precio, valor):
            return JsonResponse({
                "estado": "fallo",
                "title": campo,
                "descripcion": (
                    "Ingresa un importe válido de hasta "
                    "3 dígitos enteros y 2 decimales, "
                    "utilizando el punto como separador."
                ),
                "icon": "warning"
            })

    try:
        precio_base = Decimal(precio_base_str)
        costo_base = Decimal(costo_base_str)
    except InvalidOperation:
        return JsonResponse({
            "estado": "fallo",
            "title": "Importes inválidos",
            "descripcion": "El precio y el costo deben ser valores numéricos.",
            "icon": "warning"
        })

    if precio_base <= 0:
        return JsonResponse({
            "estado": "fallo",
            "title": "Precio base",
            "descripcion": "El precio base debe ser mayor que cero.",
            "icon": "warning"
        })

    if costo_base < 0:
        return JsonResponse({
            "estado": "fallo",
            "title": "Costo base",
            "descripcion": "El costo base no puede ser negativo.",
            "icon": "warning"
        })

    if imagen_producto.size > 5 * 1024 * 1024:
        return JsonResponse({
            "estado": "fallo",
            "title": "Imagen demasiado grande",
            "descripcion": "La imagen no puede superar los 5 MB.",
            "icon": "warning"
        })

    try:
        dimensiones = get_image_dimensions(imagen_producto)

        if not dimensiones:
            raise ValidationError("Imagen inválida.")

        imagen_producto.seek(0)

    except (ValidationError, OSError, ValueError):
        return JsonResponse({
            "estado": "fallo",
            "title": "Imagen inválida",
            "descripcion": "Selecciona una imagen válida en formato PNG, JPG o JPEG.",
            "icon": "warning"
        })

    extension = imagen_producto.name.rsplit(".", 1)[-1].lower()

    if extension not in ("jpg", "jpeg", "png"):
        return JsonResponse({
            "estado": "fallo",
            "title": "Formato de imagen",
            "descripcion": "Solo se permiten imágenes JPG, JPEG o PNG.",
            "icon": "warning"
        })

    try:
        categoria_obj = categoria_producto.objects.get(
            id_categoria=categoria,
            activo=True
        )
    except (categoria_producto.DoesNotExist, ValueError, TypeError):
        return JsonResponse({
            "estado": "fallo",
            "title": "Categoría inválida",
            "descripcion": (
                "La categoría seleccionada no existe "
                "o se encuentra inactiva."
            ),
            "icon": "warning"
        })

    try:
        unidad_obj = unidad_medida.objects.get(
            id_unidad=unidad,
            activo=True
        )
    except (unidad_medida.DoesNotExist, ValueError, TypeError):
        return JsonResponse({
            "estado": "fallo",
            "title": "Unidad de medida inválida",
            "descripcion": (
                "La unidad seleccionada no existe "
                "o se encuentra inactiva."
            ),
            "icon": "warning"
        })

    try:
        with transaction.atomic():
            obj_usuario = usuarios.objects.get(
                cedula_identidad=request.session.get(
                    "cedula_identidad"
                )
            )

            tipo_movimiento.objects.get_or_create(
                nombre="Ajuste de inventario - Entrada",
                defaults={
                    "direccion": tipo_movimiento.Direccion.ENTRADA,
                    "es_perdida": False,
                    "activo": True
                }
            )

            tipo_movimiento.objects.get_or_create(
                nombre="Ajuste de inventario - Salida",
                defaults={
                    "direccion": tipo_movimiento.Direccion.SALIDA,
                    "es_perdida": False,
                    "activo": True
                }
            )

            obj_producto = producto.objects.create(
                nombre=nombre_producto,
                codigo=codigo_producto,
                precio_base=precio_base,
                costo_base=costo_base,
                imagen="",
                id_categoria=categoria_obj,
                id_unidad=unidad_obj
            )

            nombre_archivo = (
                f"{get_valid_filename(obj_producto.codigo)}."
                f"{extension}"
            )

            imagen_producto.seek(0)

            obj_producto.imagen.save(
                nombre_archivo,
                imagen_producto,
                save=False
            )

            obj_producto.save(update_fields=["imagen"])

            existencia_inventario.objects.create(
                id_producto=obj_producto,
                cantidad_actual=0
            )

            bitacora.objects.create(
                id_usuario=obj_usuario,
                nombre_modulo="Gestión de productos",
                cargo_usuario=request.session.get("perfil", "No especificado"),
                accion=(
                    f"Registró el producto {obj_producto.nombre}, "
                    f"con código {obj_producto.codigo}."
                )
            )

        return JsonResponse({
            "estado": "exito",
            "title": "Producto registrado",
            "descripcion": (
                "El producto se registró correctamente "
                "con una existencia inicial de cero."
            ),
            "icon": "success"
        })

    except usuarios.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sesión inválida",
            "descripcion": (
                "No se pudo identificar al usuario. "
                "Inicia sesión nuevamente."
            ),
            "icon": "warning"
        })

    except IntegrityError:
        return JsonResponse({
            "estado": "fallo",
            "title": "Registro duplicado",
            "descripcion": (
                "No se pudo registrar el producto porque "
                "el código ya existe o se incumple una "
                "restricción de la base de datos."
            ),
            "icon": "warning"
        })

    except Exception:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error del servidor",
            "descripcion": (
                "Ocurrió un error al registrar el producto. "
                "Inténtalo nuevamente."
            ),
            "icon": "error"
        })

# MOVIMIENTO DE INVENTARIO

def formatear_cantidad(cantidad, abreviatura):
    cantidad = Decimal(str(cantidad))

    if abreviatura.lower() == "kg":
        return str(cantidad.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

    return str(int(cantidad))

def movimiento_producto(request):
    if request.method != "POST":
        return render(request, "Productos/movimiento_inventario.html")

    categoria = request.POST.get("categoria", "").strip()
    unidad = request.POST.get("unidad", "").strip()

    movimientos = movimiento_inventario.objects.select_related(
        "id_producto",
        "id_producto__id_categoria",
        "id_producto__id_unidad",
        "id_tipo_movimiento",
        "id_venta"
    ).order_by("-fecha_movimiento")

    if categoria:
        movimientos = movimientos.filter(
            id_producto__id_categoria_id=categoria
        )

    if unidad:
        movimientos = movimientos.filter(
            id_producto__id_unidad_id=unidad
        )

    datos_movimientos = []

    for registro in movimientos:
        datos_movimientos.append({
            "id_movimiento": registro.id_movimiento,
            "id_producto": registro.id_producto_id,
            "nombre_producto": registro.id_producto.nombre,
            "codigo_producto": registro.id_producto.codigo,
            "id_categoria": registro.id_producto.id_categoria_id,
            "categoria": registro.id_producto.id_categoria.nombre,
            "id_unidad": registro.id_producto.id_unidad_id,
            "unidad": registro.id_producto.id_unidad.nombre,
            "abreviatura": registro.id_producto.id_unidad.abreviatura,
            "id_venta": registro.id_venta_id,
            "id_tipo_movimiento": registro.id_tipo_movimiento_id,
            "tipo_movimiento": registro.id_tipo_movimiento.nombre,
            "cantidad": formatear_cantidad(
                registro.cantidad,
                registro.id_producto.id_unidad.abreviatura
            ),
            "costo_unitario": str(registro.costo_unitario),
            "valor_total": str(registro.valor_total),
            "fecha_movimiento": (
                registro.fecha_movimiento.strftime("%d/%m/%Y %H:%M:%S")
                if registro.fecha_movimiento
                else ""
            ),
            "motivo": registro.motivo,
            "reverso_de": registro.reverso_de_id
        })

    return JsonResponse({
        "estado": "exito",
        "movimientos": datos_movimientos
    })

def lista_inventario_pdf(request):
    id_categoria = request.POST.get("id_categoria", "").strip()
    id_unidad = request.POST.get("id_unidad", "").strip()

    movimientos = movimiento_inventario.objects.select_related(
        "id_producto",
        "id_producto__id_categoria",
        "id_producto__id_unidad",
        "id_tipo_movimiento",
        "id_venta",
        "reverso_de"
    ).all()

    if id_categoria:
        movimientos = movimientos.filter(
            id_producto__id_categoria_id=id_categoria
        )

    if id_unidad:
        movimientos = movimientos.filter(
            id_producto__id_unidad_id=id_unidad
        )

    movimientos = movimientos.order_by("-fecha_movimiento", "-id_movimiento")

    if not movimientos.exists():
        return JsonResponse({
            "title": "Movimientos no registrados",
            "descripcion": (
                "No hay movimientos de inventario para generar "
                "el reporte PDF con los filtros seleccionados."
            ),
            "icon": "warning"
        })

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        'inline; filename="lista_inventario.pdf"'
    )

    documento = SimpleDocTemplate(
        response,
        pagesize=landscape(letter),
        rightMargin=30,
        leftMargin=30,
        topMargin=100,
        bottomMargin=30
    )

    ruta_logo = os.path.join(
        settings.BASE_DIR,
        "static",
        "Imagenes",
        "logo_hielo_caipe.png"
    )

    if id_categoria and id_unidad:
        titulo = "MOVIMIENTOS DE INVENTARIO POR CATEGORÍA Y UNIDAD"
    elif id_categoria:
        titulo = "MOVIMIENTOS DE INVENTARIO POR CATEGORÍA"
    elif id_unidad:
        titulo = "MOVIMIENTOS DE INVENTARIO POR UNIDAD DE MEDIDA"
    else:
        titulo = "LISTA DE MOVIMIENTOS DE INVENTARIO"

    estilo_titulo = ParagraphStyle(
        "TituloInventario",
        fontName="Times-Bold",
        fontSize=12,
        leading=15,
        alignment=TA_CENTER,
        textColor=colors.white
    )

    estilo_encabezado = ParagraphStyle(
        "EncabezadoInventario",
        fontName="Times-Bold",
        fontSize=8,
        leading=10,
        alignment=TA_CENTER,
        textColor=colors.white
    )

    estilo_celda = ParagraphStyle(
        "CeldaInventario",
        fontName="Times-Roman",
        fontSize=8,
        leading=10,
        alignment=TA_CENTER,
        wordWrap="CJK"
    )

    datos_tabla = [
        [
            Paragraph(escape(titulo), estilo_titulo),
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            ""
        ],
        [
            Paragraph("ID", estilo_encabezado),
            Paragraph("PRODUCTO", estilo_encabezado),
            Paragraph("CÓDIGO", estilo_encabezado),
            Paragraph("TIPO DE MOVIMIENTO", estilo_encabezado),
            Paragraph("CANTIDAD", estilo_encabezado),
            Paragraph("COSTO UNITARIO", estilo_encabezado),
            Paragraph("VALOR TOTAL", estilo_encabezado),
            Paragraph("FECHA Y HORA", estilo_encabezado),
            Paragraph("MOTIVO", estilo_encabezado),
            Paragraph("REVERSO DE", estilo_encabezado)
        ]
    ]

    for registro in movimientos:
        fecha_movimiento = (
            timezone.localtime(
                registro.fecha_movimiento
            ).strftime("%d/%m/%Y %H:%M:%S")
            if registro.fecha_movimiento
            else "No registrada"
        )

        nombre_producto = (
            registro.id_producto.nombre or "No registrado"
        )

        codigo_producto = (
            registro.id_producto.codigo or "No registrado"
        )

        abreviatura = (
            registro.id_producto.id_unidad.abreviatura
            if registro.id_producto.id_unidad
            else ""
        )

        cantidad = f"{registro.cantidad} {abreviatura}".strip()

        tipo_movimiento = (
            registro.id_tipo_movimiento.nombre or "No registrado"
        )

        motivo = registro.motivo or "No registrado"

        reverso_de = (
            str(registro.reverso_de_id)
            if registro.reverso_de_id
            else "No aplica"
        )

        datos_tabla.append([
            str(registro.id_movimiento),
            Paragraph(escape(str(nombre_producto)), estilo_celda),
            Paragraph(escape(str(codigo_producto)), estilo_celda),
            Paragraph(escape(str(tipo_movimiento)), estilo_celda),
            Paragraph(escape(str(cantidad)), estilo_celda),
            Paragraph(
                escape(f"{registro.costo_unitario} $"),
                estilo_celda
            ),
            Paragraph(
                escape(f"{registro.valor_total} $"),
                estilo_celda
            ),
            Paragraph(escape(fecha_movimiento), estilo_celda),
            Paragraph(escape(str(motivo)), estilo_celda),
            Paragraph(escape(reverso_de), estilo_celda)
        ])

    tabla = Table(
        datos_tabla,
        colWidths=[32, 105, 65, 80, 58, 68, 65, 95, 95, 49],
        repeatRows=2
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
        ("ALIGN", (0, 1), (-1, 1), "CENTER"),
        ("VALIGN", (0, 1), (-1, 1), "MIDDLE"),

        ("FONTNAME", (0, 2), (-1, -1), "Times-Roman"),
        ("FONTSIZE", (0, 2), (-1, -1), 8),
        ("TEXTCOLOR", (0, 2), (-1, -1), colors.black),
        ("ALIGN", (0, 2), (-1, -1), "CENTER"),
        ("VALIGN", (0, 2), (-1, -1), "MIDDLE"),

        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),

        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))

    elementos = [tabla]

    documento.build(
        elementos,
        onFirstPage=lambda canvas, documento:
            encabezado_inventario_pdf(
                canvas,
                documento,
                ruta_logo
            ),
        onLaterPages=lambda canvas, documento:
            encabezado_inventario_pdf(
                canvas,
                documento,
                ruta_logo
            )
    )

    return response

def encabezado_inventario_pdf(canvas, documento, ruta_logo):
    canvas.saveState()

    ancho_pagina, alto_pagina = landscape(letter)

    if os.path.exists(ruta_logo):
        canvas.drawImage(
            ruta_logo,
            50,
            alto_pagina - 135,
            width=165,
            height=165,
            preserveAspectRatio=True,
            mask="auto"
        )

    canvas.setFont("Times-Bold", 17)
    canvas.setFillColor(
        colors.HexColor("#00445F")
    )

    canvas.drawString(
        270,
        alto_pagina - 65,
        "EMPRESA HIELO CAIPE C.A"
    )

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

    canvas.setFont("Times-Bold", 11)
    canvas.setFillColor(
        colors.HexColor("#072F3F")
    )

    canvas.drawString(
        280,
        alto_pagina - 95,
        f"Fecha de generación: {fecha_actual}"
    )

    canvas.setStrokeColor(
        colors.HexColor("#00445F")
    )
    canvas.setLineWidth(1)

    canvas.line(
        30,
        alto_pagina - 150,
        ancho_pagina - 30,
        alto_pagina - 150
    )

    canvas.restoreState()

# VISUALIZAR LOS PRODUCTOS ALMACENADOS

def visualizar_productos(request):
    return render(request, "Productos/visualizar_productos.html")

def productos_registrados(request):
    unidad = request.POST.get("unidad", "").strip()
    categoria = request.POST.get("categoria", "").strip()

    productos = producto.objects.select_related(
        "id_categoria",
        "id_unidad"
    ).all()

    if unidad:
        productos = productos.filter(
            id_unidad_id=unidad
        )

    if categoria:
        productos = productos.filter(
            id_categoria_id=categoria
        )

    productos = productos.order_by("nombre")

    datos_productos = []

    for registro in productos:
        datos_productos.append({
            "id_producto": registro.id_producto,
            "nombre": registro.nombre,
            "codigo": registro.codigo,
            "precio_base": str(registro.precio_base),
            "costo_base": str(registro.costo_base),
            "imagen": registro.imagen.url if registro.imagen else "",
            "activo": registro.activo,
            "fecha_registro": (
                registro.fecha_registro.strftime("%d/%m/%Y %H:%M:%S")
                if registro.fecha_registro
                else ""
            ),
            "id_categoria": registro.id_categoria_id,
            "categoria": registro.id_categoria.nombre,
            "id_unidad": registro.id_unidad_id,
            "unidad": registro.id_unidad.nombre,
            "abreviatura": registro.id_unidad.abreviatura
        })

    return JsonResponse({
        "estado": "exito",
        "productos": datos_productos
    })

def detalle_producto_registrado(request):
    if request.method == "POST":
        codigo = request.POST.get("codigo", "").strip()
        if not codigo:
            return JsonResponse({
                "estado": "fallo",
                "title": "Código del producto",
                "descripcion": "Debes proporcionar el código del producto.",
                "icon": "warning"
            })

        try:
            registro = producto.objects.select_related(
                "id_categoria",
                "id_unidad"
            ).get(codigo__iexact=codigo)

        except producto.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "title": "Producto no encontrado",
                "descripcion": "No existe un producto registrado con ese código.",
                "icon": "warning"
            })

        datos_producto = {
            "id_producto": registro.id_producto,
            "nombre": registro.nombre,
            "codigo": registro.codigo,
            "precio_base": str(registro.precio_base),
            "costo_base": str(registro.costo_base),
            "imagen": registro.imagen.url if registro.imagen else "",
            "activo": registro.activo,
            "fecha_registro": (
                registro.fecha_registro.strftime("%d/%m/%Y %H:%M:%S")
                if registro.fecha_registro
                else ""
            ),
            "id_categoria": registro.id_categoria_id,
            "categoria": registro.id_categoria.nombre,
            "id_unidad": registro.id_unidad_id,
            "unidad": registro.id_unidad.nombre,
            "abreviatura": registro.id_unidad.abreviatura,
            "permite_decimales": registro.id_unidad.permite_decimales
        }

        return JsonResponse({
            "estado": "exito",
            "producto": datos_producto
        })

# BUSCAR Y ACTUALIZAR LOS DATOS DEL PRODUCTO

def buscar_datos_producto(request):
    codigo = request.POST.get("codigo_producto", "").strip()

    if not codigo:
        return JsonResponse({
            "estado": "fallo",
            "title": "Código del producto",
            "descripcion": "Debes proporcionar el código del producto.",
            "icon": "warning"
        })

    try:
        registro = (
            producto.objects
            .select_related(
                "id_categoria",
                "id_unidad"
            )
            .get(codigo__iexact=codigo)
        )
    except producto.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Producto no encontrado",
            "descripcion": "No existe un producto registrado con ese código.",
            "icon": "warning"
        })
    
    datos_producto = {
        "id_producto": registro.id_producto,
        "nombre": registro.nombre,
        "codigo": registro.codigo,
        "precio_base": str(registro.precio_base),
        "costo_base": str(registro.costo_base),
        "imagen": registro.imagen.url if registro.imagen else "",
        "activo": registro.activo,
        "fecha_registro": (
            registro.fecha_registro.strftime("%d/%m/%Y %H:%M:%S")
            if registro.fecha_registro
            else ""
        ),
        "id_categoria": registro.id_categoria_id,
        "categoria": registro.id_categoria.nombre,
        "id_unidad": registro.id_unidad_id,
        "unidad": registro.id_unidad.nombre,
        "abreviatura": registro.id_unidad.abreviatura,
        "permite_decimales": registro.id_unidad.permite_decimales
    }

    return JsonResponse({
        "estado": "exito",
        "title": "Éxito",
        "descripcion": "Se encontraron los datos del producto.",
        "icon": "success",
        "producto": datos_producto
    })

def actualizar_producto(request):
    if request.method != "POST":
        return render(request, "Productos/actualizar_producto.html")

    codigo = request.POST.get("id_codigo", "").strip()
    nombre_producto = request.POST.get("nombre_producto", "").strip()
    precio_base_str = request.POST.get("precio_base", "").strip()
    costo_base_str = request.POST.get("costo_base", "").strip()
    imagen_producto = request.FILES.get("imagen_producto")
    categoria = request.POST.get("categoria_producto", "").strip()
    unidad = request.POST.get("unidad_producto", "").strip()

    try:
        registro = producto.objects.get(codigo=codigo)

    except producto.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Producto no encontrado",
            "descripcion": "No existe un producto con el código indicado.",
            "icon": "warning"
        })

    campos = [
        (nombre_producto, "Nombre del producto", "Ingresa el nombre del producto."),
        (precio_base_str, "Precio base", "Ingresa el precio base en USD."),
        (costo_base_str, "Costo base", "Ingresa el costo base en USD."),
        (categoria, "Categoría del producto", "Selecciona una categoría."),
        (unidad, "Unidad de medida", "Selecciona una unidad de medida.")
    ]

    for valor, campo, mensaje in campos:
        if not valor:
            return JsonResponse({
                "estado": "fallo",
                "title": campo,
                "descripcion": mensaje,
                "icon": "warning"
            })

    if len(nombre_producto) > 100:
        return JsonResponse({
            "estado": "fallo",
            "title": "Nombre del producto",
            "descripcion": "El nombre no puede superar los 100 caracteres.",
            "icon": "warning"
        })

    patron_precio = r"^\d{1,3}(?:\.\d{1,2})?$"

    for valor, campo in [
        (precio_base_str, "Precio base"),
        (costo_base_str, "Costo base")
    ]:
        if not re.fullmatch(patron_precio, valor):
            return JsonResponse({
                "estado": "fallo",
                "title": campo,
                "descripcion": (
                    "Ingresa un importe válido de hasta "
                    "3 dígitos enteros y 2 decimales, "
                    "utilizando el punto como separador."
                ),
                "icon": "warning"
            })

    try:
        precio_base = Decimal(precio_base_str)
        costo_base = Decimal(costo_base_str)

    except InvalidOperation:
        return JsonResponse({
            "estado": "fallo",
            "title": "Importes inválidos",
            "descripcion": "El precio y el costo deben ser valores numéricos.",
            "icon": "warning"
        })

    if precio_base <= 0:
        return JsonResponse({
            "estado": "fallo",
            "title": "Precio base",
            "descripcion": "El precio base debe ser mayor que cero.",
            "icon": "warning"
        })

    if costo_base < 0:
        return JsonResponse({
            "estado": "fallo",
            "title": "Costo base",
            "descripcion": "El costo base no puede ser negativo.",
            "icon": "warning"
        })

    if costo_base >= precio_base:
        return JsonResponse({
            "estado": "fallo",
            "title": "Costo base inválido",
            "descripcion": "El costo base debe ser menor que el precio base.",
            "icon": "warning"
        })

    extension = None

    if imagen_producto:
        if imagen_producto.size > 5 * 1024 * 1024:
            return JsonResponse({
                "estado": "fallo",
                "title": "Imagen demasiado grande",
                "descripcion": "La imagen no puede superar los 5 MB.",
                "icon": "warning"
            })

        extension = imagen_producto.name.rsplit(".", 1)[-1].lower()

        if extension not in ("jpg", "jpeg", "png"):
            return JsonResponse({
                "estado": "fallo",
                "title": "Formato de imagen",
                "descripcion": "Solo se permiten imágenes JPG, JPEG o PNG.",
                "icon": "warning"
            })

        try:
            dimensiones = get_image_dimensions(imagen_producto)

            if not dimensiones:
                raise ValidationError("Imagen inválida.")

            imagen_producto.seek(0)

        except (ValidationError, OSError, ValueError):
            return JsonResponse({
                "estado": "fallo",
                "title": "Imagen inválida",
                "descripcion": "Selecciona una imagen válida en formato PNG, JPG o JPEG.",
                "icon": "warning"
            })

    try:
        categoria_obj = categoria_producto.objects.get(
            id_categoria=categoria,
            activo=True
        )

    except (categoria_producto.DoesNotExist, ValueError, TypeError):
        return JsonResponse({
            "estado": "fallo",
            "title": "Categoría inválida",
            "descripcion": "La categoría seleccionada no existe o está inactiva.",
            "icon": "warning"
        })

    try:
        unidad_obj = unidad_medida.objects.get(
            id_unidad=unidad,
            activo=True
        )

    except (unidad_medida.DoesNotExist, ValueError, TypeError):
        return JsonResponse({
            "estado": "fallo",
            "title": "Unidad de medida inválida",
            "descripcion": "La unidad seleccionada no existe o está inactiva.",
            "icon": "warning"
        })

    try:
        obj_usuario = usuarios.objects.get(
            cedula_identidad=request.session.get("cedula_identidad")
        )

        with transaction.atomic():

            imagen_anterior = registro.imagen.name if registro.imagen else None

            registro.nombre = nombre_producto
            registro.precio_base = precio_base
            registro.costo_base = costo_base
            registro.id_categoria = categoria_obj
            registro.id_unidad = unidad_obj

            if imagen_producto:
                nombre_archivo = (
                    f"{get_valid_filename(registro.codigo)}.{extension}"
                )

                ruta_imagen = f"productos/{nombre_archivo}"

                imagen_producto.seek(0)

                almacenamiento = registro.imagen.storage

                imagen_temporal = f"productos/temporal_{nombre_archivo}"

                with almacenamiento.open(imagen_temporal, "wb") as archivo:
                    for fragmento in imagen_producto.chunks():
                        archivo.write(fragmento)

                almacenamiento.delete(ruta_imagen)

                almacenamiento.save = almacenamiento.save

                with almacenamiento.open(imagen_temporal, "rb") as archivo:
                    contenido = archivo.read()

                almacenamiento.delete(imagen_temporal)

                with almacenamiento.open(ruta_imagen, "wb") as archivo:
                    archivo.write(contenido)

                registro.imagen.name = ruta_imagen

            registro.save()

            if (
                imagen_producto
                and imagen_anterior
                and imagen_anterior != registro.imagen.name
            ):
                transaction.on_commit(
                    lambda: almacenamiento.delete(imagen_anterior)
                )

            bitacora.objects.create(
                id_usuario=obj_usuario,
                nombre_modulo="Gestión de productos",
                cargo_usuario=request.session.get("perfil", "No especificado"),
                accion=(
                    f"Actualizó el producto {registro.nombre}, "
                    f"con código {registro.codigo}."
                )
            )

        return JsonResponse({
            "estado": "exito",
            "title": "Producto actualizado",
            "descripcion": "Los datos del producto se actualizaron correctamente.",
            "icon": "success"
        })

    except usuarios.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sesión inválida",
            "descripcion": "No se pudo identificar al usuario. Inicia sesión nuevamente.",
            "icon": "warning"
        })

    except IntegrityError:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error de integridad",
            "descripcion": "No se pudo actualizar el producto por un conflicto con los datos registrados.",
            "icon": "warning"
        })

    except Exception:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error del servidor",
            "descripcion": "Ocurrió un error al actualizar el producto. Inténtalo nuevamente.",
            "icon": "error"
        })

# REPORTES TODOS Y POR INDIVIDUAL

def lista_productos_pdf(request):
    id_categoria = request.POST.get("id_categoria", "").strip()
    id_unidad = request.POST.get("id_unidad", "").strip()

    productos = producto.objects.filter(activo=True)

    if id_categoria:
        productos = productos.filter(
            id_categoria_id=id_categoria
        )

    if id_unidad:
        productos = productos.filter(
            id_unidad_id=id_unidad
        )

    productos = productos.order_by("id_producto")

    # VALIDAR PRODUCTOS REGISTRADOS
    if not productos.exists():
        return JsonResponse({
            "title": "Productos no registrados",
            "descripcion": (
                "No hay productos registrados para generar "
                "el reporte PDF con los filtros seleccionados."
            ),
            "icon": "warning"
        })

    # RESPUESTA PDF
    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        'inline; filename="lista_productos.pdf"'
    )

    # DOCUMENTO
    documento = SimpleDocTemplate(
        response,
        pagesize=letter,
        rightMargin=30,
        leftMargin=30,
        topMargin=130,
        bottomMargin=30
    )

    # LOGO
    ruta_logo = os.path.join(
        settings.BASE_DIR,
        "static",
        "Imagenes",
        "logo_hielo_caipe.png"
    )

    # TÍTULO SEGÚN LOS FILTROS
    if id_categoria and id_unidad:
        titulo = "LISTA DE PRODUCTOS POR CATEGORÍA Y UNIDAD"
    elif id_categoria:
        titulo = "LISTA DE PRODUCTOS POR CATEGORÍA"
    elif id_unidad:
        titulo = "LISTA DE PRODUCTOS POR UNIDAD DE MEDIDA"
    else:
        titulo = "LISTA DE PRODUCTOS REGISTRADOS"

    # ESTILOS
    estilo_titulo = ParagraphStyle(
        "TituloProductos",
        fontName="Times-Bold",
        fontSize=12,
        leading=15,
        alignment=TA_CENTER,
        textColor=colors.white
    )

    estilo_celda = ParagraphStyle(
        "CeldaProducto",
        fontName="Times-Roman",
        fontSize=9,
        leading=11,
        alignment=TA_CENTER,
        wordWrap="CJK"
    )

    # DATOS TABLA
    datos_tabla = [
        # ENCABEZADO PRINCIPAL
        [
            Paragraph(
                escape(titulo),
                estilo_titulo
            ),
            "",
            "",
            ""
        ],

        # ENCABEZADO DE COLUMNAS
        [
            "ID",
            "Producto",
            "Código",
            "Fecha y Hora"
        ],
    ]

    # REGISTROS
    for numero, registro in enumerate(productos, start=1):
        fecha_registro = (
            timezone.localtime(
                registro.fecha_registro
            ).strftime("%d/%m/%Y %H:%M:%S")
            if registro.fecha_registro
            else "No registrada"
        )

        datos_tabla.append([
            str(numero),
            Paragraph(
                escape(str(registro.nombre or "No registrado")),
                estilo_celda
            ),
            Paragraph(
                escape(str(registro.codigo or "No registrado")),
                estilo_celda
            ),
            Paragraph(
                escape(fecha_registro),
                estilo_celda
            )
        ])

    # TABLA
    tabla = Table(
        datos_tabla,
        colWidths=[40, 190, 110, 200],
        repeatRows=2
    )

    tabla.setStyle(TableStyle([
        # ENCABEZADO PRINCIPAL
        ("SPAN", (0, 0), (-1, 0)),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#00445F")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),

        # ENCABEZADO DE COLUMNAS
        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#00445F")),
        ("TEXTCOLOR", (0, 1), (-1, 1), colors.white),
        ("FONTNAME", (0, 1), (-1, 1), "Times-Bold"),
        ("FONTSIZE", (0, 1), (-1, 1), 9),
        ("ALIGN", (0, 1), (-1, 1), "CENTER"),
        ("VALIGN", (0, 1), (-1, 1), "MIDDLE"),

        # CONTENIDO
        ("FONTNAME", (0, 2), (-1, -1), "Times-Roman"),
        ("FONTSIZE", (0, 2), (-1, -1), 9),
        ("TEXTCOLOR", (0, 2), (-1, -1), colors.black),
        ("ALIGN", (0, 2), (-1, -1), "CENTER"),
        ("VALIGN", (0, 2), (-1, -1), "MIDDLE"),

        # BORDES
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),

        # ESPACIADO
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))

    # ELEMENTOS
    elementos = [tabla]

    # GENERAR PDF
    documento.build(
        elementos,
        onFirstPage=lambda canvas, documento:
            encabezado_productos_pdf(
                canvas,
                documento,
                ruta_logo
            ),
        onLaterPages=lambda canvas, documento:
            encabezado_productos_pdf(
                canvas,
                documento,
                ruta_logo
            )
    )

    return response

def encabezado_productos_pdf(canvas, documento, ruta_logo):
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

def lista_detalle_producto_pdf(request):
    id_producto = request.POST.get("id_producto", "").strip()

    if not id_producto:
        return JsonResponse({
            "title": "Producto no seleccionado",
            "descripcion": "Debe seleccionar un producto para generar el reporte PDF.",
            "icon": "warning"
        }, status=400)

    try:
        registro = (
            producto.objects
            .select_related("id_categoria", "id_unidad")
            .get(id_producto=id_producto)
        )

    except (producto.DoesNotExist, ValueError, TypeError):
        return JsonResponse({
            "title": "Producto no encontrado",
            "descripcion": "El producto solicitado no existe o no está registrado.",
            "icon": "warning"
        }, status=404)

    # IMAGEN DEL PRODUCTO
    imagen_producto = None

    if registro.imagen:
        try:
            ruta_imagen = registro.imagen.path

            if os.path.isfile(ruta_imagen):
                imagen_producto = Image(
                    ruta_imagen,
                    width=120,
                    height=100,
                    kind="proportional"
                )
        except (ValueError, OSError):
            imagen_producto = None

    if imagen_producto is None:
        imagen_producto = Paragraph(
            "Imagen no disponible",
            ParagraphStyle(
                "ImagenNoDisponible",
                fontName="Times-Italic",
                fontSize=9,
                alignment=TA_CENTER,
                textColor=colors.grey
            )
        )

    # FECHA DE REGISTRO
    fecha_registro = (
        timezone.localtime(
            registro.fecha_registro
        ).strftime("%d/%m/%Y %H:%M:%S")
        if registro.fecha_registro
        else "No registrada"
    )

    # CATEGORÍA
    categoria = (
        str(registro.id_categoria)
        if registro.id_categoria
        else "No registrada"
    )

    # UNIDAD DE MEDIDA
    unidad = (
        str(registro.id_unidad)
        if registro.id_unidad
        else "No registrada"
    )

    # RESPUESTA PDF
    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        f'inline; filename="detalle_producto_{registro.codigo}.pdf"'
    )

    # DOCUMENTO
    documento = SimpleDocTemplate(
        response,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=130,
        bottomMargin=40
    )

    # LOGO
    ruta_logo = os.path.join(
        settings.BASE_DIR,
        "static",
        "Imagenes",
        "logo_hielo_caipe.png"
    )

    # ESTILOS
    estilo_etiqueta = ParagraphStyle(
        "EtiquetaProducto",
        fontName="Times-Bold",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#00445F")
    )

    estilo_valor = ParagraphStyle(
        "ValorProducto",
        fontName="Times-Roman",
        fontSize=10,
        leading=14,
        textColor=colors.black,
        wordWrap="CJK"
    )

    estilo_titulo = ParagraphStyle(
        "TituloProducto",
        fontName="Times-Bold",
        fontSize=14,
        leading=18,
        alignment=TA_CENTER,
        textColor=colors.white
    )

    # DATOS DEL PRODUCTO
    datos_tabla = [
        [
            Paragraph(
                "DETALLE DEL PRODUCTO",
                estilo_titulo
            ),
            ""
        ],
        [
            Paragraph("Imagen del Producto:", estilo_etiqueta),
            imagen_producto
        ],
        [
            Paragraph("Nombre del Producto:", estilo_etiqueta),
            Paragraph(
                escape(str(registro.nombre or "No registrado")),
                estilo_valor
            )
        ],
        [
            Paragraph("Código:", estilo_etiqueta),
            Paragraph(
                escape(str(registro.codigo or "No registrado")),
                estilo_valor
            )
        ],
        [
            Paragraph("Precio Base:", estilo_etiqueta),
            Paragraph(
                escape(str(registro.precio_base)+"$"),
                estilo_valor
            )
        ],
        [
            Paragraph("Costo Base:", estilo_etiqueta),
            Paragraph(
                escape(str(registro.costo_base)+"$"),
                estilo_valor
            )
        ],
        [
            Paragraph("Categoría:", estilo_etiqueta),
            Paragraph(escape(categoria), estilo_valor)
        ],
        [
            Paragraph("Unidad de Medida:", estilo_etiqueta),
            Paragraph(escape(unidad), estilo_valor)
        ],
        [
            Paragraph("Fecha y Hora del Registro:", estilo_etiqueta),
            Paragraph(escape(fecha_registro), estilo_valor)
        ],
    ]

    # TABLA
    tabla = Table(
        datos_tabla,
        colWidths=[190, 320],
        repeatRows=1
    )

    tabla.setStyle(TableStyle([
        # ENCABEZADO
        ("SPAN", (0, 0), (-1, 0)),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#00445F")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),

        # CONTENIDO
        ("BACKGROUND", (0, 1), (0, -1), colors.HexColor("#F0F5F7")),
        ("ALIGN", (0, 1), (0, -1), "LEFT"),
        ("ALIGN", (1, 1), (1, -1), "LEFT"),

        # IMAGEN CENTRADA
        ("ALIGN", (1, 1), (1, 1), "CENTER"),
        ("VALIGN", (1, 1), (1, 1), "MIDDLE"),

        # BORDES
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),

        # ESPACIADO
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))

    # ELEMENTOS
    elementos = [tabla]

    # GENERAR PDF
    documento.build(
        elementos,
        onFirstPage=lambda canvas, documento:
            encabezado_detalle_producto_pdf(
                canvas,
                documento,
                ruta_logo
            ),
        onLaterPages=lambda canvas, documento:
            encabezado_detalle_producto_pdf(
                canvas,
                documento,
                ruta_logo
            )
    )

    return response

def encabezado_detalle_producto_pdf(canvas, documento, ruta_logo):
    canvas.saveState()

    # LOGO
    x_logo = 30
    y_logo = letter[1] - 135

    ancho_logo = 140
    alto_logo = 140

    canvas.drawImage(ruta_logo, x_logo, y_logo, width=ancho_logo, height=alto_logo, preserveAspectRatio=True, mask="auto")

    # TITULO EMPRESA
    x_titulo = 185
    y_titulo = letter[1] - 70

    canvas.setFont("Times-Bold", 18)
    canvas.setFillColor(colors.HexColor("#00445F"))
    canvas.drawString(x_titulo, y_titulo, "EMPRESA HIELO CAIPE C.A")

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

# ACTUALIZAR LA EXISTENCIA DEL PRODUCTO

def actualizar_existencia(request):
    if request.method != "POST":
        return render(request, "Productos/existencia_producto.html")

    id_producto_existencia = request.POST.get("id_producto_existencia", "").strip()
    nueva_cantidad = request.POST.get("nueva_cantidad", "").strip()
    motivo = request.POST.get("motivo", "").strip()

    campos = [
        (id_producto_existencia, "Identificador de Producto", "Por favor, debe estar asignado el identificador del producto."),
        (nueva_cantidad, "Nueva Cantidad", "Por favor, debe ingresar la nueva cantidad del producto."),
        (motivo, "Motivo del Ajuste", "Por favor, debe ingresar el motivo del ajuste."),
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
        id_producto_existencia = int(id_producto_existencia)

        cantidad_nueva_decimal = Decimal(nueva_cantidad)

        if not cantidad_nueva_decimal.is_finite():
            raise InvalidOperation

        if cantidad_nueva_decimal <= 0:
            return JsonResponse({
                "estado": "fallo",
                "title": "Cantidad inválida",
                "descripcion": "La cantidad debe ser mayor que cero.",
                "icon": "warning"
            })

        if cantidad_nueva_decimal != cantidad_nueva_decimal.to_integral_value():
            return JsonResponse({
                "estado": "fallo",
                "title": "Cantidad inválida",
                "descripcion": "La cantidad debe ser un número entero.",
                "icon": "warning"
            })

        cantidad_nueva = int(cantidad_nueva_decimal)

    except (ValueError, InvalidOperation, TypeError):
        return JsonResponse({
            "estado": "fallo",
            "title": "Datos inválidos",
            "descripcion": "Verifique el identificador y la cantidad ingresada.",
            "icon": "warning"
        })

    obj_usuario = usuarios.objects.get(
        cedula_identidad=request.session.get("cedula_identidad")
    )

    try:
        with transaction.atomic():
            try:
                producto_obj = producto.objects.get(
                    id_producto=id_producto_existencia,
                    activo=True
                )
            except producto.DoesNotExist:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Producto no disponible",
                    "descripcion": "El producto no existe o está inactivo.",
                    "icon": "warning"
                })

            existencia, creada = existencia_inventario.objects.get_or_create(
                id_producto=producto_obj,
                defaults={"cantidad_actual": 0}
            )

            existencia = existencia_inventario.objects.select_for_update().get(
                pk=existencia.pk
            )

            cantidad_actual = existencia.cantidad_actual

            # SUMAR LA NUEVA CANTIDAD A LA EXISTENCIA ANTERIOR
            cantidad_total = cantidad_actual + cantidad_nueva

            nombre_tipo = "Ajuste de inventario - Entrada"
            direccion_esperada = tipo_movimiento.Direccion.ENTRADA

            tipo = tipo_movimiento.objects.filter(
                nombre=nombre_tipo,
                direccion=direccion_esperada,
                activo=True
            ).first()

            if tipo is None:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Tipo de movimiento no configurado",
                    "descripcion": (
                        f"Debe registrar y activar el tipo de movimiento "
                        f"'{nombre_tipo}' antes de actualizar la existencia."
                    ),
                    "icon": "warning"
                })

            costo_unitario = producto_obj.costo_base

            valor_total = (
                Decimal(cantidad_nueva) * costo_unitario
            ).quantize(Decimal("0.01"))

            movimiento_inventario.objects.create(
                id_producto=producto_obj,
                id_tipo_movimiento=tipo,
                cantidad=Decimal(cantidad_nueva),
                costo_unitario=costo_unitario,
                valor_total=valor_total,
                motivo=motivo
            )

            # ACTUALIZAR EXISTENCIA ACUMULANDO LAS UNIDADES
            existencia.cantidad_actual = cantidad_total
            existencia.save(
                update_fields=["cantidad_actual", "fecha_actualizacion"]
            )

            bitacora.objects.create(
                id_usuario=obj_usuario,
                nombre_modulo="Control de inventario de productos",
                cargo_usuario=request.session.get("perfil", "No especificado"),
                accion=(
                    f"Actualizó la existencia del producto {producto_obj.nombre}, "
                    f"con código {producto_obj.codigo}. "
                    f"Cantidad anterior: {cantidad_actual}. "
                    f"Cantidad agregada: {cantidad_nueva}. "
                    f"Existencia final: {cantidad_total}. "
                    f"Motivo: {motivo}."
                )
            )

        return JsonResponse({
            "estado": "exito",
            "title": "Existencia actualizada",
            "descripcion": (
                f"Se agregaron {cantidad_nueva} unidades de {producto_obj.nombre}. "
                f"Existencia anterior: {cantidad_actual}. "
                f"Existencia actual: {cantidad_total}."
            ),
            "icon": "success",
            "cantidad_actual": cantidad_total
        })

    except existencia_inventario.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error de existencia",
            "descripcion": "No se pudo obtener la existencia del producto.",
            "icon": "error"
        })

def productos_registrados_venta(request):
    productos = (
        producto.objects
        .filter(activo=True)
        .select_related("id_categoria", "id_unidad")
        .order_by("nombre")
    )

    datos_productos = []

    for p in productos:
        datos_productos.append({
            "id_producto": p.id_producto,
            "nombre": p.nombre,
            "codigo": p.codigo,
            "precio_base": str(p.precio_base),
            "costo_base": str(p.costo_base),
            "categoria": p.id_categoria.nombre,
            "unidad": p.id_unidad.nombre,
            "abreviatura": p.id_unidad.abreviatura,
            "permite_decimales": p.id_unidad.permite_decimales,
            "imagen": p.imagen.url if p.imagen else "",
        })

    return JsonResponse({
        "estado": "exito",
        "productos": datos_productos
    })

def datos_producto_existencia(request):
    codigo = request.POST.get("codigo_producto", "").strip()

    if not codigo:
        return JsonResponse({
            "producto": []
        })

    try:
        registro = (
            producto.objects
            .select_related(
                "id_categoria",
                "id_unidad",
                "existencia"
            )
            .get(codigo__iexact=codigo)
        )

    except producto.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Producto no encontrado",
            "descripcion": "No existe un producto registrado con ese código.",
            "icon": "warning",
            "producto": []
        })

    cantidad_actual = (
        registro.existencia.cantidad_actual
        if hasattr(registro, "existencia")
        else 0
    )

    datos_producto = {
        "id_producto": registro.id_producto,
        "nombre": registro.nombre,
        "codigo": registro.codigo,
        "precio_base": str(registro.precio_base),
        "costo_base": str(registro.costo_base),
        "imagen": registro.imagen.url if registro.imagen else "",
        "activo": registro.activo,
        "fecha_registro": (
            registro.fecha_registro.strftime("%d/%m/%Y %H:%M:%S")
            if registro.fecha_registro
            else ""
        ),
        "id_categoria": registro.id_categoria_id,
        "categoria": registro.id_categoria.nombre,
        "id_unidad": registro.id_unidad_id,
        "unidad": registro.id_unidad.nombre,
        "abreviatura": registro.id_unidad.abreviatura,
        "permite_decimales": registro.id_unidad.permite_decimales,
        "cantidad_actual": cantidad_actual
    }

    return JsonResponse({
        "producto": datos_producto
    })

# PRECIO POR CANTIDAD

def registrar_precio_volumen(request):
    if request.method != "POST":
        return render(request, "Productos/precio_volumen.html")

    producto_registrado = request.POST.get("producto_registrado", "").strip()
    cantidad_minima = request.POST.get("cantidad_minima", "").strip()
    cantidad_maxima = request.POST.get("cantidad_maxima", "").strip()
    porcentaje_descuento = request.POST.get("porcentaje_descuento", "").strip()

    campos = [
        (producto_registrado, "Producto Registrado", "Por favor, debe seleccionar un producto registrado."),
        (cantidad_minima, "Cantidad Mínima", "Por favor, debe ingresar la cantidad mínima."),
        (cantidad_maxima, "Cantidad Máxima", "Por favor, debe ingresar la cantidad máxima."),
        (porcentaje_descuento, "Descuento por volumen", "Por favor, debe ingresar el porcentaje de descuento."),
    ]

    for valor, campo, mensaje in campos:
        if not valor:
            return JsonResponse({
                "estado": "fallo",
                "title": campo,
                "descripcion": mensaje,
                "icon": "warning"
            })

    # Validar el identificador del producto
    if not producto_registrado.isdigit():
        return JsonResponse({
            "estado": "fallo",
            "title": "Producto inválido",
            "descripcion": "El producto seleccionado no es válido.",
            "icon": "warning"
        })

    # Validar que las cantidades sean números enteros positivos
    if not cantidad_minima.isdigit() or not cantidad_maxima.isdigit():
        return JsonResponse({
            "estado": "fallo",
            "title": "Cantidades inválidas",
            "descripcion": "Las cantidades mínima y máxima deben ser números enteros.",
            "icon": "warning"
        })

    cantidad_minima = int(cantidad_minima)
    cantidad_maxima = int(cantidad_maxima)

    if cantidad_minima <= 0 or cantidad_maxima <= 0:
        return JsonResponse({
            "estado": "fallo",
            "title": "Cantidades inválidas",
            "descripcion": "Las cantidades deben ser mayores que cero.",
            "icon": "warning"
        })

    if cantidad_minima >= cantidad_maxima:
        return JsonResponse({
            "estado": "fallo",
            "title": "Rango de cantidades",
            "descripcion": "La cantidad mínima debe ser menor que la cantidad máxima.",
            "icon": "warning"
        })

    if not re.fullmatch(r"\d{1,3}(?:\.\d{1,2})?", porcentaje_descuento):
        return JsonResponse({
            "estado": "fallo",
            "title": "Descuento inválido",
            "descripcion": "El descuento debe ser numérico, con un máximo de 3 enteros y 2 decimales.",
            "icon": "warning"
        })

    porcentaje_descuento = Decimal(porcentaje_descuento)

    if (
        not porcentaje_descuento.is_finite()
        or porcentaje_descuento <= 0
        or porcentaje_descuento > 100
    ):
        return JsonResponse({
            "estado": "fallo",
            "title": "Descuento inválido",
            "descripcion": "El porcentaje de descuento debe ser mayor que 0 y no superar el 100%.",
            "icon": "warning"
        })
    
    try:
        with transaction.atomic():
            # Comprobar que el producto exista y esté activo
            producto_registrado = producto.objects.get(
                id_producto=int(producto_registrado),
                activo=True
            )

            ultimo_registro = precio_volumen.objects.filter(
                id_producto=producto_registrado,
                activo=True
            ).order_by("-id_precio_volumen").first()

            if (
                ultimo_registro
                and porcentaje_descuento <= ultimo_registro.porcentaje_descuento
            ):
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Descuento inválido",
                    "descripcion": (
                        "El porcentaje de descuento debe ser mayor que el "
                        "último descuento registrado para este producto."
                    ),
                    "icon": "warning"
                })

            # Comprobar si ya existe exactamente el mismo registro activo
            duplicado = precio_volumen.objects.filter(
                id_producto=producto_registrado,
                cantidad_minima=cantidad_minima,
                cantidad_maxima=cantidad_maxima,
                activo=True
            ).exists()

            if duplicado:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Registro duplicado",
                    "descripcion": "Ya existe un descuento por volumen activo para ese producto y ese rango de cantidades.",
                    "icon": "warning"
                })

            # Comprobar si el nuevo rango se solapa con otro rango activo
            rango_solapado = precio_volumen.objects.filter(
                id_producto=producto_registrado,
                activo=True,
                cantidad_minima__lte=cantidad_maxima,
                cantidad_maxima__gte=cantidad_minima
            ).exists()

            if rango_solapado:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Rango de cantidades ocupado",
                    "descripcion": "El rango de cantidades se solapa con otro rango activo de este producto. Seleccione cantidades diferentes.",
                    "icon": "warning"
                })

            # Registrar el descuento por volumen
            precio_volumen.objects.create(
                id_producto=producto_registrado,
                cantidad_minima=cantidad_minima,
                cantidad_maxima=cantidad_maxima,
                porcentaje_descuento=porcentaje_descuento,
                activo=True
            )

        return JsonResponse({
            "estado": "exito",
            "title": "Registro exitoso",
            "descripcion": "El descuento por volumen se registró correctamente.",
            "icon": "success"
        })

    except producto.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Producto no encontrado",
            "descripcion": "El producto seleccionado no existe o está inactivo.",
            "icon": "warning"
        })

    except (InvalidOperation, ValueError, OverflowError):
        return JsonResponse({
            "estado": "fallo",
            "title": "Datos inválidos",
            "descripcion": "Verifique los valores ingresados e intente nuevamente.",
            "icon": "warning"
        })

    except DatabaseError:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error de base de datos",
            "descripcion": "No fue posible registrar el precio por volumen. Intente nuevamente.",
            "icon": "error"
        })

    except Exception:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error inesperado",
            "descripcion": "Ocurrió un error al registrar el precio por volumen.",
            "icon": "error"
        })

def precios_volumna_producto(request):
    id_producto = request.POST.get("id_producto")

    if not id_producto:
        return JsonResponse({
            "estado": "error",
            "precios": []
        })

    precios = precio_volumen.objects.filter(
        id_producto_id=id_producto
    ).select_related("id_producto").order_by("cantidad_minima")

    datos = [
        {
            "id_precio_volumen": precio.id_precio_volumen,
            "id_producto": precio.id_producto_id,
            "producto": precio.id_producto.nombre,
            "cantidad_minima": precio.cantidad_minima,
            "cantidad_maxima": precio.cantidad_maxima,
            "porcentaje_descuento": str(precio.porcentaje_descuento),
            "activo": precio.activo,
            "fecha_registro": precio.fecha_registro.strftime("%d/%m/%Y %H:%M")
        }
        for precio in precios
    ]

    return JsonResponse({
        "estado": "ok" if datos else "vacio",
        "precios": datos
    })

def ultimo_registro_volumen_producto(request):
    id_producto = request.POST.get("id_producto", "").strip()

    if not id_producto or not id_producto.isdigit():
        return JsonResponse({
            "estado": "fallo",
            "title": "Producto inválido",
            "descripcion": "El producto seleccionado no es válido.",
            "icon": "warning",
            "precios": []
        })

    try:
        ultimo_registro = precio_volumen.objects.filter(
            id_producto_id=int(id_producto),
            activo=True
        ).order_by("-id_precio_volumen").first()

        if not ultimo_registro:
            return JsonResponse({
                "estado": "vacio",
                "title": "Sin registros",
                "descripcion": "El producto no tiene precios por volumen registrados.",
                "icon": "info",
                "precios": []
            })

        return JsonResponse({
            "estado": "ok",
            "precios": {
                "id_precio_volumen": ultimo_registro.id_precio_volumen,
                "id_producto": ultimo_registro.id_producto_id,
                "cantidad_minima": ultimo_registro.cantidad_minima,
                "cantidad_maxima": ultimo_registro.cantidad_maxima,
                "porcentaje_descuento": str(ultimo_registro.porcentaje_descuento),
                "activo": ultimo_registro.activo
            }
        })

    except DatabaseError:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error de base de datos",
            "descripcion": "No fue posible consultar el último precio por volumen.",
            "icon": "error",
            "precios": []
        })

    except Exception:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error inesperado",
            "descripcion": "Ocurrió un error al consultar el último registro.",
            "icon": "error",
            "precios": []
        })

# PRODUCTO CON EXISTENCIA SUFICIENTE PARA REALIZAR COMPRAS

def productos_exhibicion(request):
    nombre_producto = request.POST.get("producto", "").strip()

    productos = producto.objects.select_related(
        "id_categoria",
        "id_unidad",
        "existencia"
    ).filter(
        activo=True,
        existencia__cantidad_actual__gt=0
    )

    # BUSCAR PRODUCTOS POR NOMBRE O CÓDIGO
    if nombre_producto:
        productos = productos.filter(
            Q(nombre__icontains=nombre_producto) |
            Q(codigo__icontains=nombre_producto)
        )

    productos = productos.order_by("nombre")

    datos_productos = []

    for registro in productos:

        datos_productos.append({
            "id_producto": registro.id_producto,
            "nombre": registro.nombre,
            "codigo": registro.codigo,
            "precio_base": str(registro.precio_base),
            "costo_base": str(registro.costo_base),
            "imagen": (
                registro.imagen.url
                if registro.imagen
                else ""
            ),
            "activo": registro.activo,
            "fecha_registro": (
                registro.fecha_registro.strftime(
                    "%d/%m/%Y %H:%M:%S"
                )
                if registro.fecha_registro
                else ""
            ),
            "id_categoria": registro.id_categoria_id,
            "categoria": registro.id_categoria.nombre,
            "id_unidad": registro.id_unidad_id,
            "unidad": registro.id_unidad.nombre,
            "abreviatura": registro.id_unidad.abreviatura,
            "cantidad_actual": registro.existencia.cantidad_actual
        })

    return JsonResponse({
        "estado": "exito",
        "productos": datos_productos
    })
