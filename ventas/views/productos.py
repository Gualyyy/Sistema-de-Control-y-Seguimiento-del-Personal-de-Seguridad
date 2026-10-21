from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.db import transaction, IntegrityError, DatabaseError
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.files.images import get_image_dimensions
from django.utils.text import get_valid_filename

from ventas.models import categoria_producto, unidad_medida, producto, existencia_inventario, tipo_movimiento, movimiento_inventario, precio_volumen
from inicio_sesion.models import bitacora, usuarios

import os
import re
from decimal import Decimal, InvalidOperation

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
from reportlab.lib.pagesizes import letter
from xml.sax.saxutils import escape

# Create your views here.

#

def categorias_productos(request):
    categorias = categoria_producto.objects.order_by("nombre")

    datos = [
        {
            "id_categoria": categoria.id_categoria,
            "nombre": categoria.nombre
        }
        for categoria in categorias
    ]

    return JsonResponse(datos, safe=False)

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

#

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

#

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

#

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

    codigo = request.POST.get("id_codigo")
    nombre_producto = request.POST.get("nombre_producto", "").strip()
    precio_base_str = request.POST.get("precio_base", "").strip()
    costo_base_str = request.POST.get("costo_base", "").strip()
    imagen_producto = request.FILES.get("imagen_producto")
    categoria = request.POST.get("categoria_producto", "").strip()
    unidad = request.POST.get("unidad_producto", "").strip()

    print(codigo)

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
                    f"{get_valid_filename(registro.codigo)}."
                    f"{extension}"
                )

                imagen_producto.seek(0)

                registro.imagen.save(
                    nombre_archivo,
                    imagen_producto,
                    save=False
                )

            registro.save()

            if (
                imagen_producto
                and imagen_anterior
                and imagen_anterior != registro.imagen.name
            ):
                transaction.on_commit(
                    lambda: registro.imagen.storage.delete(imagen_anterior)
                )

            bitacora.objects.create(
                id_usuario=obj_usuario,
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

#

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

#

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

        if cantidad_nueva_decimal < 0:
            return JsonResponse({
                "estado": "fallo",
                "title": "Cantidad inválida",
                "descripcion": "La cantidad no puede ser negativa.",
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

    obj_usuario = usuarios.objects.get(cedula_identidad=request.session.get("cedula_identidad"))

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

            if cantidad_actual == cantidad_nueva:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Sin cambios",
                    "descripcion": "La nueva cantidad coincide con la existencia actual.",
                    "icon": "info"
                })

            diferencia = abs(cantidad_nueva - cantidad_actual)

            if cantidad_nueva > cantidad_actual:
                nombre_tipo = "Ajuste de inventario - Entrada"
                direccion_esperada = tipo_movimiento.Direccion.ENTRADA
            else:
                nombre_tipo = "Ajuste de inventario - Salida"
                direccion_esperada = tipo_movimiento.Direccion.SALIDA

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
                Decimal(diferencia) * costo_unitario
            ).quantize(Decimal("0.01"))

            movimiento_inventario.objects.create(
                id_producto=producto_obj,
                id_tipo_movimiento=tipo,
                cantidad=Decimal(diferencia),
                costo_unitario=costo_unitario,
                valor_total=valor_total,
                motivo=motivo
            )

            existencia.cantidad_actual = cantidad_nueva
            existencia.save(
                update_fields=["cantidad_actual", "fecha_actualizacion"]
            )

            bitacora.objects.create(
                id_usuario=obj_usuario,
                accion=(
                    f"Actualizó la existencia del producto {producto_obj.nombre}, "
                    f"con código {producto_obj.codigo}. "
                    f"Cantidad anterior: {cantidad_actual}. "
                    f"Cantidad nueva: {cantidad_nueva}. "
                    f"Diferencia: {cantidad_nueva - cantidad_actual}. "
                    f"Motivo: {motivo}."
                )
            )

        return JsonResponse({
            "estado": "exito",
            "title": "Existencia actualizada",
            "descripcion": (
                f"La existencia de {producto_obj.nombre} se actualizó "
                f"de {cantidad_actual} a {cantidad_nueva}."
            ),
            "icon": "success",
            "cantidad_actual": cantidad_nueva
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

# 

def registrar_precio_volumen(request):
    if request.method != "POST":
        return render(request, "Productos/precio_volumen.html")

    producto_registrado = request.POST.get("producto_registrado", "").strip()
    cantidad_minima = request.POST.get("cantidad_minima", "").strip()
    cantidad_maxima = request.POST.get("cantidad_maxima", "").strip()
    precio_unitario = request.POST.get("precio_unitario", "").strip()

    campos = [
        (producto_registrado, "Producto Registrado", "Por favor, debe seleccionar un producto registrado."),
        (cantidad_minima, "Cantidad Mínima", "Por favor, debe ingresar la cantidad mínima."),
        (cantidad_maxima, "Cantidad Máxima", "Por favor, debe ingresar la cantidad máxima."),
        (precio_unitario, "Precio Unitario", "Por favor, debe ingresar el precio unitario."),
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

    # Validar el formato del precio
    if not re.fullmatch(r"\d{1,10}(?:\.\d{1,2})?", precio_unitario):
        return JsonResponse({
            "estado": "fallo",
            "title": "Precio inválido",
            "descripcion": "El precio debe ser numérico, con un máximo de 10 enteros y 2 decimales.",
            "icon": "warning"
        })

    precio_unitario = Decimal(precio_unitario)

    if not precio_unitario.is_finite() or precio_unitario <= 0:
        return JsonResponse({
            "estado": "fallo",
            "title": "Precio inválido",
            "descripcion": "El precio unitario debe ser mayor que cero.",
            "icon": "warning"
        })
    
    try:
        with transaction.atomic():
            # Comprobar que el producto exista y esté activo
            producto_registrado = producto.objects.get(
                id_producto=int(producto_registrado),
                activo=True
            )

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
                    "descripcion": "Ya existe un precio por volumen activo para ese producto y ese rango de cantidades.",
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

            # Registrar el precio por volumen
            precio_volumen.objects.create(
                id_producto=producto_registrado,
                cantidad_minima=cantidad_minima,
                cantidad_maxima=cantidad_maxima,
                precio_unitario=precio_unitario,
                activo=True
            )

        return JsonResponse({
            "estado": "exito",
            "title": "Registro exitoso",
            "descripcion": "El precio por volumen se registró correctamente.",
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
            "precio_unitario": str(precio.precio_unitario),
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
                "precio_unitario": str(ultimo_registro.precio_unitario),
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


