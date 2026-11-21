from django.shortcuts import render
from django.http import JsonResponse
from django.db import transaction
from django.db.models.functions import TruncDate
from django.db.models import Q, Prefetch
from decimal import Decimal
from collections import defaultdict
from django.db.models import Sum
from pathlib import Path

import json
import uuid
import logging
from io import BytesIO
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
from django.utils import timezone
from django.utils.dateparse import parse_date

from inicio_sesion.models import bitacora, cliente, contacto, usuarios
from ventas.models import cuenta_destino_pago, detalle_venta, existencia_inventario, metodo_pago, pago, producto, venta, precio_volumen, tipo_movimiento, movimiento_inventario

from xml.sax.saxutils import escape

logger = logging.getLogger(__name__)

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer
)

# Create your views here.

# REGISTRAR COMPRA POR PARTE DEL CLIENTE

def productos_disponible_venta(request):
    nombre_producto = request.POST.get("nombre_producto", "").strip()
    categoria = request.POST.get("categoria", "").strip()

    filtros = Q(
        activo=True,
        existencia__cantidad_actual__gt=0
    )

    if nombre_producto:
        filtros &= Q(nombre__icontains=nombre_producto)

    if categoria:
        filtros &= Q(id_categoria__id_categoria=categoria)

    productos = producto.objects.filter(filtros).select_related(
        "id_categoria",
        "id_unidad",
        "existencia"
    ).order_by("nombre")

    datos = [
        {
            "id_producto": p.id_producto,
            "nombre": p.nombre,
            "codigo": p.codigo,
            "precio_base": str(p.precio_base),
            "imagen": p.imagen.url if p.imagen else None,
            "categoria": p.id_categoria.nombre,
            "unidad": p.id_unidad.nombre,
            "abreviatura": p.id_unidad.abreviatura,
            "existencia": p.existencia.cantidad_actual
        }
        for p in productos
    ]

    return JsonResponse({
        "estado": "exito",
        "productos": datos
    })

def precio_volumen_producto(request):
    id_producto = request.POST.get("id_producto")

    if not id_producto:
        return JsonResponse({
            "estado": "fallo",
            "title": "Producto requerido",
            "icon": "warning",
            "descripcion": "No se recibió el identificador del producto."
        })

    try:
        id_producto = int(id_producto)

        precios = precio_volumen.objects.filter(
            id_producto_id=id_producto,
            activo=True
        ).order_by("cantidad_minima")

        datos = [
            {
                "id_precio_volumen": precio.id_precio_volumen,
                "cantidad_minima": precio.cantidad_minima,
                "cantidad_maxima": precio.cantidad_maxima,
                "porcentaje_descuento": float(precio.porcentaje_descuento)
            }
            for precio in precios
        ]

        return JsonResponse({
            "estado": "exito",
            "precios": datos
        })

    except (ValueError, TypeError):
        return JsonResponse({
            "estado": "fallo",
            "title": "Identificador inválido",
            "icon": "warning",
            "descripcion": "El identificador del producto no es válido."
        })

    except Exception:
        logger.exception(
            "Error al obtener descuentos por volumen para el producto %s.",
            id_producto
        )
        return JsonResponse({
            "estado": "fallo",
            "title": "Error del servidor",
            "icon": "error",
            "descripcion": "No fue posible obtener los precios por volumen."
        }, status=500)

# ENVIAR AL CORREO FACTURA Y PDF

def enviar_correo_compra(destinatario, contexto, comprobante, pdf):
    try:
        contenido_html = render_to_string(
            "Email/compra_espara.html",
            contexto
        )

        contenido_texto = strip_tags(contenido_html)

        lineas_limpias = [
            linea.strip()
            for linea in contenido_texto.splitlines()
            if linea.strip()
        ]

        texto_plano_final = "\n".join(lineas_limpias)

        correo = EmailMultiAlternatives(
            subject=f"Comprobante de compra - {comprobante}",
            body=texto_plano_final,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[destinatario]
        )

        correo.attach_alternative(
            contenido_html,
            "text/html"
        )

        # Adjuntar factura PDF
        correo.attach(
            f"factura_{comprobante}.pdf",
            pdf,
            "application/pdf"
        )

        correo.send()

        return True

    except Exception:
        logger.exception(
            "Error al renderizar o enviar el correo de compra pendiente. "
            "Comprobante: %s",
            comprobante
        )

        return False

def enviar_correo_compra_con_factura(destinatario, contexto, comprobante, id_venta):
    try:
        venta_actual = venta.objects.select_related(
            "id_cliente__id_usuario",
            "id_cliente__id_usuario__contacto"
        ).prefetch_related(
            "detalles__id_producto__id_unidad",
            "pagos__id_metodo_pago",
            "pagos__id_cuenta_destino"
        ).get(
            id_venta=id_venta,
            estado=venta.Estado.PENDIENTE_CONFIRMACION
        )

        pdf = generar_factura_compra(venta_actual)

        return enviar_correo_compra(
            destinatario,
            contexto,
            comprobante,
            pdf
        )

    except Exception:
        logger.exception(
            "Error al generar o enviar la factura de compra. "
            "Comprobante: %s",
            comprobante
        )
        return False

def registrar_compra_cliente(request):
    if request.method != "POST":
        return render(request, "Compras/Clientes/registrar_compra.html")

    cedula = request.session.get("cedula_identidad")

    if not cedula:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sesión inválida",
            "descripcion": "Inicia sesión nuevamente para registrar la compra.",
            "icon": "warning"
        }, status=401)

    try:
        usuario_actual = usuarios.objects.select_related(
            "contacto"
        ).get(
            cedula_identidad=cedula
        )

        cliente_actual = cliente.objects.get(
            id_usuario=usuario_actual
        )

        contacto = usuario_actual.contacto

    except (usuarios.DoesNotExist, cliente.DoesNotExist):
        return JsonResponse({
            "estado": "fallo",
            "title": "Cliente no encontrado",
            "descripcion": "No se pudo identificar al cliente que realiza la compra.",
            "icon": "warning"
        }, status=404)

    except AttributeError:
        return JsonResponse({
            "estado": "fallo",
            "title": "Datos de contacto",
            "descripcion": "No se encontró la información de contacto del cliente.",
            "icon": "warning"
        }, status=400)

    productos_str = request.POST.get("productos", "").strip()

    if not productos_str:
        return JsonResponse({
            "estado": "fallo",
            "title": "Carrito vacío",
            "descripcion": "Agrega productos antes de registrar la compra.",
            "icon": "warning"
        })

    try:
        productos_solicitados = json.loads(productos_str)

        if not isinstance(productos_solicitados, list) or not productos_solicitados:
            raise ValueError

        cantidades_por_producto = {}

        for item in productos_solicitados:
            id_producto = int(item["id_producto"])
            cantidad = Decimal(str(item["cantidad"]))

            if id_producto <= 0 or not cantidad.is_finite() or cantidad <= 0:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Cantidad inválida",
                    "descripcion": "Verifica que los productos y sus cantidades sean válidos.",
                    "icon": "warning"
                })

            cantidades_por_producto[id_producto] = (
                cantidades_por_producto.get(id_producto, Decimal("0")) + cantidad
            )

    except (ValueError, TypeError, KeyError, InvalidOperation, ArithmeticError):
        return JsonResponse({
            "estado": "fallo",
            "title": "Productos inválidos",
            "descripcion": "Verifica los productos y las cantidades del carrito.",
            "icon": "warning"
        })

    tasa_cambio_str = request.POST.get("tasa_cambio", "").strip()

    try:
        tasa_cambio = Decimal(tasa_cambio_str)

        if not tasa_cambio.is_finite() or tasa_cambio <= 0:
            raise ValueError

    except (ValueError, TypeError, InvalidOperation):
        return JsonResponse({
            "estado": "fallo",
            "title": "Tasa de cambio inválida",
            "descripcion": "No se recibió una tasa de cambio válida.",
            "icon": "warning"
        })

    id_metodo = request.POST.get("id_metodo", "").strip()
    id_cuenta = request.POST.get("id_cuenta", "").strip()
    referencia = request.POST.get("referencia", "").strip()
    capture_pago = request.FILES.get("capture_pago")
    telefono_origen = request.POST.get("telefono_origen", "").strip()
    fecha_pago_bancario = request.POST.get("fecha_pago_bancario")
    banco_origen = request.POST.get("banco_origen", "").strip()

    campos = [
        (id_metodo, "Método de pago", "Selecciona un método de pago."),
        (id_cuenta, "Cuenta de destino", "Selecciona una cuenta de destino."),
        (capture_pago, "Capture de pago", "Adjunta el capture del pago.")
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
        with transaction.atomic():

            metodo = metodo_pago.objects.get(
                id_metodo_pago=id_metodo,
                activo=True
            )

            cuenta = cuenta_destino_pago.objects.get(
                id_cuenta_destino=id_cuenta,
                id_metodo_pago=metodo,
                activo=True
            )

            total_subtotal = Decimal("0.00")
            total_subtotal_usd = Decimal("0.00")
            descuento_total = Decimal("0.00")
            descuento_total_usd = Decimal("0.00")

            articulos = []

            for id_producto, cantidad in cantidades_por_producto.items():

                producto_actual = producto.objects.select_for_update().get(
                    id_producto=id_producto,
                    activo=True
                )

                existencia = existencia_inventario.objects.select_for_update().get(
                    id_producto=producto_actual
                )

                if existencia.cantidad_actual < cantidad:
                    return JsonResponse({
                        "estado": "fallo",
                        "title": "Existencia insuficiente",
                        "descripcion": (
                            f"No hay suficientes unidades de "
                            f"{producto_actual.nombre}."
                        ),
                        "icon": "warning"
                    })

                precio_volumen_actual = precio_volumen.objects.filter(
                    id_producto=producto_actual,
                    activo=True,
                    cantidad_minima__lte=cantidad
                ).filter(
                    Q(cantidad_maxima__isnull=True) |
                    Q(cantidad_maxima__gte=cantidad)
                ).order_by(
                    "-cantidad_minima"
                ).first()

                precio_unitario_usd = producto_actual.precio_base.quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP
                )

                porcentaje_descuento = (
                    precio_volumen_actual.porcentaje_descuento
                    if precio_volumen_actual
                    else Decimal("0.00")
                )

                subtotal_bruto_usd = (
                    precio_unitario_usd * cantidad
                ).quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP
                )

                descuento_articulo_usd = (
                    subtotal_bruto_usd * porcentaje_descuento / Decimal("100")
                ).quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP
                )

                subtotal_articulo_usd = (
                    subtotal_bruto_usd - descuento_articulo_usd
                ).quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP
                )

                precio_unitario = (
                    precio_unitario_usd * tasa_cambio
                ).quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP
                )

                subtotal_bruto = (
                    subtotal_bruto_usd * tasa_cambio
                ).quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP
                )

                descuento_articulo = (
                    descuento_articulo_usd * tasa_cambio
                ).quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP
                )

                subtotal_articulo = (
                    subtotal_bruto - descuento_articulo
                ).quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP
                )

                total_subtotal += subtotal_bruto
                total_subtotal_usd += subtotal_bruto_usd
                descuento_total += descuento_articulo
                descuento_total_usd += descuento_articulo_usd

                articulos.append({
                    "producto": producto_actual,
                    "cantidad": cantidad,
                    "precio_unitario": precio_unitario,
                    "precio_unitario_usd": precio_unitario_usd,
                    "porcentaje_descuento": porcentaje_descuento,
                    "descuento": descuento_articulo,
                    "descuento_usd": descuento_articulo_usd,
                    "subtotal": subtotal_articulo,
                    "subtotal_usd": subtotal_articulo_usd
                })

            total_subtotal = total_subtotal.quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP
            )

            total_subtotal_usd = total_subtotal_usd.quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP
            )

            descuento = descuento_total.quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP
            )
            descuento_usd = descuento_total_usd.quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP
            )

            impuesto = (
                (total_subtotal - descuento) * Decimal("0.16")
            ).quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP
            )

            total = (
                total_subtotal - descuento + impuesto
            ).quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP
            )

            impuesto_usd = (
                impuesto / tasa_cambio
            ).quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP
            )

            total_usd = (
                total / tasa_cambio
            ).quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP
            )

            venta_actual = venta.objects.create(
                comprobante=f"COMP-{uuid.uuid4().hex[:12].upper()}",
                id_cliente=cliente_actual,
                subtotal=total_subtotal,
                descuento=descuento,
                impuesto=impuesto,
                total=total,
                tasa_cambio=tasa_cambio,
                estado=venta.Estado.PENDIENTE_CONFIRMACION,
                observacion="Pendiente de revisión por Atención al Cliente.",
                inventario_descontado=False,
            )

            for articulo in articulos:
                producto_actual = articulo["producto"]
                cantidad = articulo["cantidad"]

                costo_unitario = producto_actual.costo_base.quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP
                )

                costo_total = (
                    costo_unitario * cantidad
                ).quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP
                )

                detalle_venta.objects.create(
                    id_venta=venta_actual,
                    id_producto=producto_actual,
                    cantidad=cantidad,
                    precio_unidad=articulo["precio_unitario"],
                    descuento=articulo["descuento"],
                    subtotal=articulo["subtotal"],
                    costo_unitario=costo_unitario,
                    costo_total=costo_total
                )

            pago.objects.create(
                id_venta=venta_actual,
                id_cuenta_destino=cuenta,
                id_metodo_pago=metodo,
                monto=total,
                referencia=referencia,
                capture_pago=capture_pago,
                telefono_origen=telefono_origen,
                fecha_pago_bancario=fecha_pago_bancario,
                banco_origen=banco_origen
            )

            bitacora.objects.create(
                id_usuario=usuario_actual,
                nombre_modulo="Gestión de compras",
                cargo_usuario=request.session.get("perfil", "No especificado"),
                accion=(
                    f"Registró la compra {venta_actual.comprobante}, "
                    "pendiente de revisión por Atención al Cliente."
                )
            )

            contexto = {
                "cliente": cliente_actual,
                "usuario": usuario_actual,
                "correo": contacto.correo_principal,
                "comprobante": venta_actual.comprobante,
                "fecha_compra": venta_actual.fecha_venta,
                "articulos": articulos,
                "subtotal": total_subtotal,
                "subtotal_usd": total_subtotal_usd,
                "descuento": descuento,
                "descuento_usd": descuento_usd,
                "impuesto": impuesto,
                "impuesto_usd": impuesto_usd,
                "total": total,
                "total_usd": total_usd,
                "tasa_cambio": tasa_cambio,
                "metodo_pago": metodo.nombre,
                "estado": venta_actual.estado
            }

            correo_seleccionado = contacto.correo_principal

            if correo_seleccionado:
                transaction.on_commit(
                    lambda correo=correo_seleccionado,
                        datos=contexto,
                        comprobante=venta_actual.comprobante,
                        id_venta=venta_actual.id_venta:
                        enviar_correo_compra_con_factura(
                            correo,
                            datos,
                            comprobante,
                            id_venta
                        )
                )

        return JsonResponse({
            "estado": "exito",
            "title": "Compra registrada",
            "descripcion": (
                f"La compra {venta_actual.comprobante} se registró "
                "y quedó pendiente de revisión por Atención al Cliente."
            ),
            "comprobante": venta_actual.comprobante,
            "tasa_cambio": str(venta_actual.tasa_cambio),
            "icon": "success"
        })

    except (metodo_pago.DoesNotExist, cuenta_destino_pago.DoesNotExist):
        return JsonResponse({
            "estado": "fallo",
            "title": "Método de pago no disponible",
            "descripcion": "Verifica el método de pago y la cuenta seleccionada.",
            "icon": "warning"
        })

    except (producto.DoesNotExist, existencia_inventario.DoesNotExist):
        return JsonResponse({
            "estado": "fallo",
            "title": "Producto no disponible",
            "descripcion": "Uno de los productos ya no está disponible.",
            "icon": "warning"
        })

    except Exception as e:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error del servidor",
            "descripcion": f"Ocurrió un error al registrar la compra. Inténtalo nuevamente {e}.",
            "icon": "error"
        })

# VISUALIZAR HISTORIAL COMPRA POR PARTE DEL CLIENTE

def fechas_compras_cliente(request):
    cedula = request.session.get("cedula_identidad")
    if not cedula:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sesión no válida",
            "descripcion": "Debe iniciar sesión para consultar sus compras.",
            "icon": "warning"
        }, status=401)

    try:
        cliente_actual = cliente.objects.get(id_usuario__cedula_identidad=cedula)

    except cliente.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Cliente no encontrado",
            "descripcion": "No se encontró el registro del cliente.",
            "icon": "warning"
        }, status=404)

    fechas = venta.objects.filter(
        id_cliente=cliente_actual
    ).exclude(
        estado=venta.Estado.BORRADOR
    ).annotate(
        fecha=TruncDate("fecha_venta")
    ).values_list(
        "fecha",
        flat=True
    ).distinct().order_by("-fecha")

    return JsonResponse({
        "estado": "exito",
        "fechas": [
            fecha.isoformat()
            for fecha in fechas
        ]
    })

def estado_compra_cliente(request):
    cedula = request.session.get("cedula_identidad")

    if not cedula:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sesión no válida",
            "descripcion": "Debe iniciar sesión para consultar sus compras.",
            "icon": "warning"
        }, status=401)

    try:
        cliente_actual = cliente.objects.get(
            id_usuario__cedula_identidad=cedula
        )

    except cliente.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Cliente no encontrado",
            "descripcion": "No se encontró el registro del cliente.",
            "icon": "warning"
        }, status=404)

    estados = venta.objects.filter(
        id_cliente=cliente_actual
    ).exclude(
        estado=venta.Estado.BORRADOR
    ).values_list(
        "estado",
        flat=True
    ).distinct().order_by("estado")

    return JsonResponse({
        "estado": "exito",
        "estados": [
            {
                "valor": estado,
                "nombre": venta.Estado(estado).label
            }
            for estado in estados
        ]
    })

def historial_compra_cliente(request):
    if request.method != "POST":
        return render(
            request,
            "Compras/Clientes/visualizar_compras.html"
        )

    # VALIDAR CLIENTE
    cedula = request.session.get("cedula_identidad")

    if not cedula:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sesión no válida",
            "descripcion": "Debe iniciar sesión para consultar sus compras.",
            "icon": "warning"
        }, status=401)

    try:
        cliente_actual = cliente.objects.select_related(
            "id_usuario"
        ).get(
            id_usuario__cedula_identidad=cedula
        )

    except cliente.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Cliente no encontrado",
            "descripcion": "No se encontró el registro del cliente.",
            "icon": "warning"
        }, status=404)

    # IDENTIFICAR OPERACIÓN
    accion = request.POST.get("accion", "historial")

    # CONSULTA BASE
    compras = venta.objects.filter(
        id_cliente=cliente_actual
    ).exclude(
        estado=venta.Estado.BORRADOR
    ).prefetch_related(
        Prefetch(
            "detalles",
            queryset=detalle_venta.objects.select_related(
                "id_producto__id_unidad"
            )
        )
    ).order_by("-fecha_venta")

    # --------------------------------------------------
    # HISTORIAL DE COMPRAS
    # --------------------------------------------------

    if accion == "historial":

        fecha_compra = request.POST.get("fecha_compra")
        estado = request.POST.get("estado")

        # FILTRAR POR FECHA ESPECÍFICA
        if fecha_compra:

            fecha_compra = parse_date(fecha_compra)

            if not fecha_compra:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Fecha incorrecta",
                    "descripcion": "La fecha seleccionada no es válida.",
                    "icon": "warning"
                }, status=400)

            compras = compras.filter(
                fecha_venta__date=fecha_compra
            )

        # FILTRAR POR ESTADO
        estados_validos = [
            opcion[0]
            for opcion in venta.Estado.choices
            if opcion[0] != venta.Estado.BORRADOR
        ]

        if estado:
            if estado not in estados_validos:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Estado incorrecto",
                    "descripcion": "El estado seleccionado no es válido.",
                    "icon": "warning"
                }, status=400)

            compras = compras.filter(
                estado=estado
            )

        # CONSTRUIR RESULTADOS
        resultados = []

        for compra in compras:

            productos = []

            for detalle in compra.detalles.all():

                productos.append({
                    "id_detalle": detalle.id_detalle,
                    "nombre": detalle.id_producto.nombre,
                    "codigo": detalle.id_producto.codigo,
                    "cantidad": str(detalle.cantidad),
                    "unidad": detalle.id_producto.id_unidad.abreviatura,
                    "precio_unidad": str(detalle.precio_unidad),
                    "descuento": str(detalle.descuento),
                    "subtotal": str(detalle.subtotal)
                })

            fecha = timezone.localtime(
                compra.fecha_venta
            )

            resultados.append({
                "id_venta": compra.id_venta,
                "comprobante": compra.comprobante,
                "fecha": fecha.strftime("%d/%m/%Y"),
                "hora": fecha.strftime("%I:%M %p"),
                "estado": compra.estado,
                "estado_display": compra.get_estado_display(),
                "subtotal": str(compra.subtotal),
                "descuento": str(compra.descuento),
                "impuesto": str(compra.impuesto),
                "total": str(compra.total),
                "tasa_cambio": (
                    str(compra.tasa_cambio)
                    if compra.tasa_cambio is not None
                    else None
                ),
                "productos": productos
            })

        return JsonResponse({
            "estado": "exito",
            "compras": resultados,
            "total_compras": len(resultados)
        })

    # --------------------------------------------------
    # DETALLE DE COMPRA
    # --------------------------------------------------

    elif accion == "detalle":

        id_venta = request.POST.get("id_venta")

        if not id_venta:
            return JsonResponse({
                "estado": "fallo",
                "title": "Compra requerida",
                "descripcion": "No se recibió el identificador de la compra.",
                "icon": "warning"
            }, status=400)

        try:
            compra = compras.select_related(
                "id_cliente__id_usuario"
            ).prefetch_related(
                Prefetch(
                    "detalles",
                    queryset=detalle_venta.objects.select_related(
                        "id_producto__id_unidad",
                        "id_producto__id_categoria"
                    )
                ),
                Prefetch(
                    "pagos",
                    queryset=pago.objects.select_related(
                        "id_metodo_pago",
                        "id_cuenta_destino",
                        "id_cuenta_destino__id_metodo_pago"
                    ).order_by("id_pago")
                )
            ).get(
                id_venta=id_venta
            )

        except (venta.DoesNotExist, ValueError):
            return JsonResponse({
                "estado": "fallo",
                "title": "Compra no encontrada",
                "descripcion": "La compra solicitada no existe o no está disponible para este cliente.",
                "icon": "warning"
            }, status=404)

        # INFORMACIÓN GENERAL
        fecha_compra = timezone.localtime(
            compra.fecha_venta
        )

        informacion_general = {
            "id_venta": compra.id_venta,
            "comprobante": compra.comprobante,
            "fecha": fecha_compra.strftime("%d/%m/%Y"),
            "hora": fecha_compra.strftime("%I:%M %p"),
            "estado": compra.estado,
            "estado_display": compra.get_estado_display(),
            "observacion": compra.observacion,
            "subtotal": str(compra.subtotal),
            "descuento": str(compra.descuento),
            "impuesto": str(compra.impuesto),
            "total": str(compra.total),
            "tasa_cambio": (
                str(compra.tasa_cambio)
                if compra.tasa_cambio is not None
                else None
            )
        }

        # INFORMACIÓN DE PRODUCTOS
        productos = []

        for detalle in compra.detalles.all():

            productos.append({
                "id_detalle": detalle.id_detalle,
                "id_producto": detalle.id_producto_id,
                "nombre": detalle.id_producto.nombre,
                "codigo": detalle.id_producto.codigo,
                "categoria": detalle.id_producto.id_categoria.nombre,
                "unidad": detalle.id_producto.id_unidad.abreviatura,
                "cantidad": str(detalle.cantidad),
                "precio_unidad": str(detalle.precio_unidad),
                "descuento": str(detalle.descuento),
                "subtotal": str(detalle.subtotal)
            })

        # INFORMACIÓN DE PAGOS
        pagos = []

        for registro in compra.pagos.all():

            cuenta = registro.id_cuenta_destino

            pagos.append({
                "id_pago": registro.id_pago,
                "metodo_pago": registro.id_metodo_pago.nombre,
                "monto": str(registro.monto),
                "estado": registro.estado,
                "referencia": registro.referencia,

                "fecha_pago": timezone.localtime(
                    registro.fecha_pago
                ).strftime("%d/%m/%Y %I:%M %p"),

                "fecha_pago_bancario": (
                    registro.fecha_pago_bancario.strftime("%d/%m/%Y")
                    if registro.fecha_pago_bancario
                    else None
                ),

                "banco_origen": registro.banco_origen,
                "telefono_origen": registro.telefono_origen,

                "capture_pago": (
                    request.build_absolute_uri(
                        registro.capture_pago.url
                    )
                    if registro.capture_pago
                    else None
                ),

                "cuenta_destino": (
                    {
                        "banco": cuenta.banco,
                        "documento": cuenta.documento,
                        "telefono": cuenta.telefono,
                        "numero_cuenta": cuenta.numero_cuenta,
                        "tipo_cuenta": cuenta.get_tipo_cuenta_display(),
                        "metodo_pago": cuenta.id_metodo_pago.nombre
                    }
                    if cuenta
                    else None
                )
            })

        return JsonResponse({
            "estado": "exito",
            "compra": informacion_general,
            "productos": productos,
            "pagos": pagos
        })

def datos_factura_cliente(request):
    if request.method == "POST":
        id_venta = request.POST.get("id_venta", "").strip()
        
        if not id_venta.isdigit() or int(id_venta) <= 0:
            return JsonResponse({
                "estado": "fallo",
                "title": "Compra inválida",
                "descripcion": "No se recibió un identificador de compra válido.",
                "icon": "warning"
            }, status=400)
    
        cedula = request.session.get("cedula_identidad")
        
        if not cedula:
            return JsonResponse({
                "estado": "fallo",
                "title": "Sesión inválida",
                "descripcion": "Inicia sesión nuevamente para consultar la factura.",
                "icon": "warning"
            }, status=401)
        
        try:
    
            cliente_actual = cliente.objects.select_related(
                "id_usuario",
                "id_usuario__contacto"
            ).get(
                id_usuario__cedula_identidad=cedula
            )
    
        except cliente.DoesNotExist:
    
            return JsonResponse({
                "estado": "fallo",
                "title": "Cliente no encontrado",
                "descripcion": "No se encontró el registro del cliente.",
                "icon": "warning"
            }, status=404)
    
        try:
    
            venta_actual = venta.objects.select_related(
                "id_cliente",
                "id_cliente__id_usuario",
                "id_cliente__id_usuario__contacto"
            ).prefetch_related(
                Prefetch(
                    "detalles",
                    queryset=detalle_venta.objects.select_related(
                        "id_producto",
                        "id_producto__id_unidad",
                        "id_producto__id_categoria"
                    )
                ),
                Prefetch(
                    "pagos",
                    queryset=pago.objects.select_related(
                        "id_metodo_pago",
                        "id_cuenta_destino",
                        "id_cuenta_destino__id_metodo_pago"
                    ).order_by("-fecha_pago")
                )
            ).get(
                id_venta=int(id_venta),
                id_cliente=cliente_actual
            )
    
        except venta.DoesNotExist:
    
            return JsonResponse({
                "estado": "fallo",
                "title": "Compra no encontrada",
                "descripcion": "No se encontró la compra solicitada.",
                "icon": "warning"
            }, status=404)
    
        usuario_actual = cliente_actual.id_usuario
        contacto = getattr(usuario_actual, "contacto", None)
    
        # ==========================================
        # DATOS DE LOS PRODUCTOS
        # ==========================================
    
        articulos = []
    
        for detalle in venta_actual.detalles.all():
    
            articulos.append({
                "id_detalle": detalle.id_detalle,
                "nombre": detalle.id_producto.nombre,
                "codigo": detalle.id_producto.codigo,
                "categoria": detalle.id_producto.id_categoria.nombre,
                "unidad": detalle.id_producto.id_unidad.abreviatura,
                "cantidad": str(detalle.cantidad),
                "precio_unitario": str(detalle.precio_unidad),
                "descuento": str(detalle.descuento),
                "subtotal": str(detalle.subtotal),
                "costo_unitario": str(detalle.costo_unitario),
                "costo_total": str(detalle.costo_total)
            })
    
        # ==========================================
        # INFORMACIÓN DEL PAGO
        # ==========================================
    
        pagos = []
    
        for pago_actual in venta_actual.pagos.all():
    
            cuenta = pago_actual.id_cuenta_destino
    
            pagos.append({
                "id_pago": pago_actual.id_pago,
                "metodo_pago": pago_actual.id_metodo_pago.nombre,
                "monto": str(pago_actual.monto),
                "referencia": pago_actual.referencia,
                "fecha_pago": timezone.localtime(
                    pago_actual.fecha_pago
                ).strftime("%d/%m/%Y"),
                "hora_pago": timezone.localtime(
                    pago_actual.fecha_pago
                ).strftime("%I:%M %p"),
                "estado": pago_actual.estado,
                "telefono_origen": pago_actual.telefono_origen,
                "fecha_pago_bancario": (
                    pago_actual.fecha_pago_bancario.strftime("%d/%m/%Y")
                    if pago_actual.fecha_pago_bancario else ""
                ),
                "banco_origen": pago_actual.banco_origen,
    
                "cuenta_destino": {
                    "banco": cuenta.banco,
                    "documento": cuenta.documento,
                    "telefono": cuenta.telefono,
                    "numero_cuenta": cuenta.numero_cuenta,
                    "tipo_cuenta": cuenta.get_tipo_cuenta_display()
                } if cuenta else None,
    
                "capture_pago": (
                    request.build_absolute_uri(pago_actual.capture_pago.url)
                    if pago_actual.capture_pago else ""
                )
            })
    
        # ==========================================
        # EQUIVALENTES EN USD
        # ==========================================
    
        tasa_cambio = venta_actual.tasa_cambio or Decimal("0.00")
    
        def convertir_usd(valor):
    
            if tasa_cambio <= 0:
                return "0.00"
    
            return str(
                (valor / tasa_cambio).quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP
                )
            )
    
        # ==========================================
        # DATOS GENERALES DE LA FACTURA
        # ==========================================
    
        datos_factura = {
    
            "id_venta": venta_actual.id_venta,
            "comprobante": venta_actual.comprobante,
    
            "fecha": timezone.localtime(
                venta_actual.fecha_venta
            ).strftime("%d/%m/%Y"),
    
            "hora": timezone.localtime(
                venta_actual.fecha_venta
            ).strftime("%I:%M %p"),
    
            "estado": venta_actual.estado,
            "estado_display": venta_actual.get_estado_display(),
    
            "motivo_rechazo": venta_actual.get_motivo_rechazo_display(),
    
            "observacion": venta_actual.observacion,
    
            # CLIENTE
            "cliente": {
                "nombre": (
                    usuario_actual.nombre_razon_social
                    if usuario_actual.tipo_usuario == "EMPRESA"
                    else usuario_actual.nombres
                ),
                "apellido": (
                    ""
                    if usuario_actual.tipo_usuario == "EMPRESA"
                    else usuario_actual.apellidos
                ),
                "cedula": usuario_actual.cedula_identidad,
                "correo": (
                    contacto.correo_principal if contacto else ""
                )
            },
    
            # PRODUCTOS
            "productos": articulos,
    
            # RESUMEN ECONÓMICO
            "resumen": {
                "subtotal": str(venta_actual.subtotal),
                "descuento": str(venta_actual.descuento),
                "impuesto": str(venta_actual.impuesto),
                "total": str(venta_actual.total),
    
                "subtotal_usd": convertir_usd(venta_actual.subtotal),
                "descuento_usd": convertir_usd(venta_actual.descuento),
                "impuesto_usd": convertir_usd(venta_actual.impuesto),
                "total_usd": convertir_usd(venta_actual.total),
    
                "tasa_cambio": str(tasa_cambio)
            },
    
            # PAGOS
            "pagos": pagos
        }
    
        return JsonResponse({
            "estado": "exito",
            "factura": datos_factura
        })

# VERIFICAR Y VISUALIZAR COMPRA PARA ACEPTAR O RECHAZAR COMPRA

def verificar_compras_clientes(request):
    return render(request, "Compras/Atencion_Clientes/verificar_ventas.html")

def obtener_venta_verificar(request):
    metodo_pago = request.POST.get("metodo_pago", "").strip()

    try:
        ventas = venta.objects.exclude(estado=venta.Estado.BORRADOR)

        if metodo_pago:
            if not metodo_pago.isdigit():
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Método de pago inválido",
                    "descripcion": "El método de pago seleccionado no es válido.",
                    "icon": "warning"
                })

            ventas = ventas.filter(
                pagos__id_metodo_pago_id=int(metodo_pago)
            ).distinct()

        ventas = ventas.order_by("-fecha_venta")

        datos_ventas = []

        for registro in ventas:
            datos_ventas.append({
                "id_venta": registro.id_venta,
                "comprobante": registro.comprobante,
                "fecha_venta": (
                    registro.fecha_venta.strftime("%d/%m/%Y %I:%M %p")
                    if registro.fecha_venta
                    else "No disponible"
                ),
                "estado": registro.estado,
                "estado_display": registro.get_estado_display()
            })

        return JsonResponse({
            "estado": "exito",
            "ventas": datos_ventas
        })

    except Exception:
        logger.exception(
            "Error al consultar las ventas para verificar. Método de pago: %s",
            metodo_pago
        )

        return JsonResponse({
            "estado": "fallo",
            "title": "Error al consultar las ventas",
            "descripcion": "No fue posible obtener los registros de ventas.",
            "icon": "error"
        }, status=500)

def detalle_venta_verificar(request):
    id_venta = request.POST.get("id_venta", "").strip()

    if not id_venta or not id_venta.isdigit():
        return JsonResponse({
            "estado": "fallo",
            "title": "Venta inválida",
            "descripcion": "El identificador de la venta no es válido.",
            "icon": "warning"
        })

    try:
        registro = venta.objects.select_related(
            "id_cliente",
            "id_cliente__id_usuario",
            "id_cliente__id_usuario__contacto"
        ).prefetch_related(
            Prefetch(
                "detalles",
                queryset=detalle_venta.objects.select_related(
                    "id_producto",
                    "id_producto__id_unidad"
                )
            ),
            Prefetch(
                "pagos",
                queryset=pago.objects.select_related(
                    "id_metodo_pago",
                    "id_cuenta_destino"
                )
            )
        ).get(id_venta=int(id_venta))

        # INFORMACIÓN GENERAL DE LA VENTA
        informacion_general = {
            "id_venta": registro.id_venta,
            "comprobante": registro.comprobante,
            "fecha_venta": registro.fecha_venta.strftime(
                "%d/%m/%Y %I:%M %p"
            ),
            "tasa_cambio": (
                str(registro.tasa_cambio)
                if registro.tasa_cambio is not None
                else None
            ),
            "estado": registro.estado,
            "estado_display": registro.get_estado_display(),
            "observacion": registro.observacion or ""
        }

        # INFORMACIÓN DEL CLIENTE
        usuario_registro = registro.id_cliente.id_usuario

        try:
            contacto_registro = usuario_registro.contacto
        except contacto.DoesNotExist:
            contacto_registro = None

        informacion_cliente = {
            "id_cliente": (
                usuario_registro.id_usuario
            ),
            "nombre": (
                usuario_registro.nombre_razon_social
                if usuario_registro.tipo_usuario == "EMPRESA"
                else f"{usuario_registro.nombres} {usuario_registro.apellidos}".strip()
            ),
            "documento": usuario_registro.cedula_identidad,
            "telefono": (
                contacto_registro.telefono_principal
                if contacto_registro else ""
            ),
            "correo": (
                contacto_registro.correo_principal
                if contacto_registro else ""
            )
        }

        # PRODUCTOS DE LA VENTA
        productos = []

        for detalle in registro.detalles.all():
            unidad = detalle.id_producto.id_unidad

            cantidad = (
                str(detalle.cantidad)
                if unidad.permite_decimales
                else str(int(detalle.cantidad))
            )

            productos.append({
                "id_detalle": detalle.id_detalle,
                "id_producto": detalle.id_producto_id,
                "producto": detalle.id_producto.nombre,
                "cantidad": cantidad,
                "unidad_medida": unidad.nombre,
                "abreviatura": unidad.abreviatura,
                "permite_decimales": unidad.permite_decimales,
                "precio_unidad": str(
                    (detalle.precio_unidad / registro.tasa_cambio).quantize(
                        Decimal("0.01"),
                        rounding=ROUND_HALF_UP
                    )
                    if registro.tasa_cambio
                    else detalle.precio_unidad
                ),
                "descuento": str(
                    (detalle.descuento / registro.tasa_cambio).quantize(
                        Decimal("0.01"),
                        rounding=ROUND_HALF_UP
                    )
                    if registro.tasa_cambio
                    else detalle.descuento
                ),
                "subtotal": str(
                    (detalle.subtotal / registro.tasa_cambio).quantize(
                        Decimal("0.01"),
                        rounding=ROUND_HALF_UP
                    )
                    if registro.tasa_cambio
                    else detalle.subtotal
                ),
                "precio_unidad_ves": (
                    str(detalle.precio_unidad)
                    if registro.tasa_cambio is not None
                    else None
                ),
                "descuento_ves": (
                    str(detalle.descuento)
                    if registro.tasa_cambio is not None
                    else None
                ),
                "subtotal_ves": (
                    str(detalle.subtotal)
                    if registro.tasa_cambio is not None
                    else None
                )
            })

        # PAGO DE LA VENTA
        registro_pago = registro.pagos.first()

        informacion_pago = None
        cuenta_destino = None
        total_pagado = Decimal("0.00")

        if registro_pago:

            if registro_pago.estado == pago.Estado.REGISTRADO:
                total_pagado = registro_pago.monto

            informacion_pago = {
                "id_pago": registro_pago.id_pago,
                "metodo_pago": registro_pago.id_metodo_pago.nombre,
                "monto": str(
                    (registro_pago.monto / registro.tasa_cambio).quantize(
                        Decimal("0.01"),
                        rounding=ROUND_HALF_UP
                    )
                    if registro.tasa_cambio
                    else registro_pago.monto
                ),
                "monto_ves": (
                    str(registro_pago.monto)
                    if registro.tasa_cambio is not None
                    else None
                ),
                "capture_pago": (
                    registro_pago.capture_pago.url
                    if registro_pago.capture_pago
                    else ""
                ),
                "referencia": registro_pago.referencia or "",
                "banco_origen": registro_pago.banco_origen or "",
                "telefono_origen": registro_pago.telefono_origen or "",
                "fecha_pago_bancario": (
                    registro_pago.fecha_pago_bancario.strftime("%d/%m/%Y")
                    if registro_pago.fecha_pago_bancario else ""
                ),
                "fecha_pago": registro_pago.fecha_pago.strftime(
                    "%d/%m/%Y %I:%M %p"
                ),
                "estado": registro_pago.estado,
                "estado_display": registro_pago.get_estado_display()
            }

            # CUENTA DESTINO
            cuenta = registro_pago.id_cuenta_destino

            if cuenta:
                cuenta_destino = {
                    "banco": cuenta.banco,
                    "documento": cuenta.documento,
                    "telefono": cuenta.telefono,
                    "numero_cuenta": cuenta.numero_cuenta,
                    "tipo_cuenta": cuenta.tipo_cuenta,
                    "tipo_cuenta_display": cuenta.get_tipo_cuenta_display()
                }

        # RESUMEN FINANCIERO
        monto_pendiente = registro.total - total_pagado

        resumen = {
            "subtotal": str(
                (registro.subtotal / registro.tasa_cambio).quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP
                )
                if registro.tasa_cambio
                else registro.subtotal
            ),
            "descuento": str(
                (registro.descuento / registro.tasa_cambio).quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP
                )
                if registro.tasa_cambio
                else registro.descuento
            ),
            "impuesto": str(
                (registro.impuesto / registro.tasa_cambio).quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP
                )
                if registro.tasa_cambio
                else registro.impuesto
            ),
            "total": str(
                (registro.total / registro.tasa_cambio).quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP
                )
                if registro.tasa_cambio
                else registro.total
            ),
            "total_pagado": str(
                (total_pagado / registro.tasa_cambio).quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP
                )
                if registro.tasa_cambio
                else total_pagado
            ),
            "monto_pendiente": str(
                (max(monto_pendiente, Decimal("0.00")) / registro.tasa_cambio).quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP
                )
                if registro.tasa_cambio
                else max(monto_pendiente, Decimal("0.00"))
            ),
            "excedente": str(
                (max(-monto_pendiente, Decimal("0.00")) / registro.tasa_cambio).quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP
                )
                if registro.tasa_cambio
                else max(-monto_pendiente, Decimal("0.00"))
            ),
            "subtotal_ves": (
                str(registro.subtotal)
                if registro.tasa_cambio is not None
                else None
            ),
            "descuento_ves": (
                str(registro.descuento)
                if registro.tasa_cambio is not None
                else None
            ),
            "impuesto_ves": (
                str(registro.impuesto)
                if registro.tasa_cambio is not None
                else None
            ),
            "total_ves": (
                str(registro.total)
                if registro.tasa_cambio is not None
                else None
            ),
            "total_pagado_ves": (
                str(total_pagado)
                if registro.tasa_cambio is not None
                else None
            ),
            "monto_pendiente_ves": (
                str(max(monto_pendiente, Decimal("0.00")))
                if registro.tasa_cambio is not None
                else None
            ),
            "excedente_ves": (
                str(max(-monto_pendiente, Decimal("0.00")))
                if registro.tasa_cambio is not None
                else None
            ),
        }

        # RESPUESTA COMPLETA
        return JsonResponse({
            "estado": "exito",
            "venta": informacion_general,
            "cliente": informacion_cliente,
            "productos": productos,
            "pago": informacion_pago,
            "cuenta_destino": cuenta_destino,
            "resumen": resumen
        })

    except venta.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Venta no encontrada",
            "descripcion": "La venta solicitada no existe.",
            "icon": "warning"
        })

    except Exception as error:
        print(f"Error al consultar el detalle de la venta: {error}")

        return JsonResponse({
            "estado": "fallo",
            "title": "Error al consultar la venta",
            "descripcion": "No fue posible obtener los detalles de la venta.",
            "icon": "error"
        })

# COMPROBAR EL ESTADO LA COMPRA

def estado_compra_venta(request):
    id_venta = request.POST.get("id_venta")

    if not id_venta:
        return JsonResponse({
            "estado": "fallo",
            "title": "Venta no identificada",
            "icon": "warning",
            "descripcion": "No se recibió el identificador de la venta."
        }, status=400)

    try:
        venta_actual = venta.objects.only(
            "id_venta",
            "estado"
        ).get(id_venta=id_venta)

        puede_procesar = (
            venta_actual.estado == venta.Estado.PENDIENTE_CONFIRMACION
        )

        return JsonResponse({
            "estado": "exito",
            "puede_procesar": puede_procesar,
            "estado_venta": venta_actual.estado,
            "inhabilitar_botones": not puede_procesar,
            "descripcion": (
                "La venta está pendiente de confirmación."
                if puede_procesar
                else "La venta ya no está pendiente de confirmación."
            )
        })

    except venta.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Venta no encontrada",
            "icon": "warning",
            "descripcion": "La venta solicitada no existe.",
            "inhabilitar_botones": True
        }, status=404)

# ACCIÓN ACEPTAR LA COMPRA

def enviar_correo_compra_confirmada(destinatario, contexto, comprobante, pdf):
    try:
        contenido_html = render_to_string(
            "Email/compra_aprobada.html",
            contexto
        )

        contenido_texto = strip_tags(contenido_html)

        lineas_limpias = [
            linea.strip()
            for linea in contenido_texto.splitlines()
            if linea.strip()
        ]

        texto_plano_final = "\n".join(lineas_limpias)

        correo = EmailMultiAlternatives(
            subject=f"Compra confirmada - {comprobante}",
            body=texto_plano_final,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[destinatario]
        )

        correo.attach_alternative(
            contenido_html,
            "text/html"
        )

        correo.attach(
            f"factura_{comprobante}.pdf",
            pdf,
            "application/pdf"
        )

        correo.send()

        return True

    except Exception:
        logger.exception(
            "Error al renderizar o enviar el correo de compra confirmada. "
            "Comprobante: %s",
            comprobante
        )
        return False

def enviar_correo_compra_confirmada_con_factura(destinatario, contexto, comprobante, id_venta):
    try:
        venta_actual = venta.objects.select_related(
            "id_cliente__id_usuario",
            "id_cliente__id_usuario__contacto"
        ).prefetch_related(
            "detalles__id_producto__id_unidad",
            "pagos__id_metodo_pago",
            "pagos__id_cuenta_destino"
        ).get(
            id_venta=id_venta,
            estado=venta.Estado.CONFIRMADA
        )

        pdf = generar_factura_compra(venta_actual)

        return enviar_correo_compra_confirmada(
            destinatario=destinatario,
            contexto=contexto,
            comprobante=comprobante,
            pdf=pdf
        )

    except Exception:
        logger.exception(
            "Error al generar o enviar la factura de compra confirmada. "
            "Comprobante: %s",
            comprobante
        )

        return False

def aceptar_venta(request):
    id_venta = request.POST.get("id_venta")

    if not id_venta:
        return JsonResponse({
            "estado": "fallo",
            "title": "Venta no identificada",
            "icon": "warning",
            "descripcion": "No se recibió el identificador de la venta.",
            "inhabilitar_botones": True
        }, status=400)

    try:
        correo_principal = None
        usuario_cliente = None
        detalles = []
        venta_actual = None

        with transaction.atomic():

            venta_actual = venta.objects.select_for_update().get(
                id_venta=id_venta
            )

            # VALIDAR QUE LA VENTA SIGA PENDIENTE

            if venta_actual.estado != venta.Estado.PENDIENTE_CONFIRMACION:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Venta no disponible",
                    "icon": "warning",
                    "descripcion": (
                        "Esta venta ya fue procesada o dejó de estar "
                        "pendiente de confirmación. No es posible "
                        "realizar nuevamente esta acción."
                    ),
                    "estado_venta": venta_actual.estado,
                    "inhabilitar_botones": True
                }, status=400)

            cliente_actual = cliente.objects.select_related(
                "id_usuario"
            ).get(
                id_cliente=venta_actual.id_cliente_id
            )

            usuario_cliente = cliente_actual.id_usuario

            contacto_cliente = contacto.objects.filter(
                id_usuario=usuario_cliente
            ).first()

            if not contacto_cliente:
                raise ValueError(
                    "El cliente no tiene un registro de contacto. "
                    "No es posible enviar la notificación de confirmación."
                )

            correo_principal = contacto_cliente.correo_principal

            if not correo_principal:
                raise ValueError(
                    "El cliente no tiene un correo electrónico principal registrado."
                )

            detalles = list(
                detalle_venta.objects.select_related(
                    "id_producto",
                    "id_producto__id_unidad"
                ).filter(
                    id_venta=venta_actual
                ).order_by("id_producto_id")
            )

            if not detalles:
                raise ValueError(
                    "No se puede confirmar una venta sin productos."
                )

            pagos = pago.objects.filter(
                id_venta=venta_actual,
                estado=pago.Estado.REGISTRADO
            )

            monto_pagado = pagos.aggregate(
                total=Sum("monto")
            )["total"] or Decimal("0.00")

            if monto_pagado <= 0:
                raise ValueError(
                    "La venta no tiene pagos registrados válidos."
                )

            cantidades = defaultdict(
                lambda: Decimal("0.000")
            )

            productos = {}

            for detalle in detalles:

                producto_actual = detalle.id_producto

                if detalle.cantidad <= 0:
                    raise ValueError(
                        f"La cantidad del producto "
                        f"{producto_actual.nombre} no es válida."
                    )

                if producto_actual.id_unidad.permite_decimales is False:

                    if detalle.cantidad != detalle.cantidad.to_integral_value():
                        raise ValueError(
                            f"El producto {producto_actual.nombre} "
                            "no permite cantidades decimales."
                        )

                cantidades[detalle.id_producto_id] += detalle.cantidad

                productos[detalle.id_producto_id] = producto_actual

            existencias = list(
                existencia_inventario.objects.select_for_update().filter(
                    id_producto_id__in=list(cantidades.keys())
                ).order_by("id_producto_id")
            )

            existencias_por_producto = {
                existencia.id_producto_id: existencia
                for existencia in existencias
            }

            for id_producto, cantidad in cantidades.items():

                existencia = existencias_por_producto.get(id_producto)

                producto_actual = productos[id_producto]

                if existencia is None:
                    raise ValueError(
                        f"El producto {producto_actual.nombre} "
                        "no tiene existencias registradas."
                    )

                if not venta_actual.inventario_descontado:
                    if existencia.cantidad_actual < cantidad:
                        raise ValueError(
                            f"No hay suficientes existencias de "
                            f"{producto_actual.nombre} para confirmar la venta."
                        )

                    existencia.cantidad_actual -= cantidad
                    existencia.save(
                        update_fields=[
                            "cantidad_actual",
                            "fecha_actualizacion",
                        ]
                    )

            tipo_salida, _ = tipo_movimiento.objects.get_or_create(
                nombre="Venta",
                defaults={
                    "direccion": tipo_movimiento.Direccion.SALIDA,
                    "es_perdida": False,
                    "activo": True,
                },
            )

            if (
                tipo_salida.direccion != tipo_movimiento.Direccion.SALIDA
                or tipo_salida.es_perdida
                or not tipo_salida.activo
            ):
                raise tipo_movimiento.DoesNotExist

            movimientos = [
                movimiento_inventario(
                    id_producto=detalle.id_producto,
                    id_venta=venta_actual,
                    id_tipo_movimiento=tipo_salida,
                    cantidad=detalle.cantidad,
                    costo_unitario=detalle.costo_unitario,
                    valor_total=detalle.costo_total,
                    motivo=(
                        f"Salida de inventario por venta "
                        f"{venta_actual.comprobante}"
                    )
                )
                for detalle in detalles
            ]

            movimiento_inventario.objects.bulk_create(
                movimientos
            )

            venta_actual.estado = venta.Estado.CONFIRMADA
            venta_actual.inventario_descontado = True

            venta_actual.save(
                update_fields=["estado", "inventario_descontado"]
            )

        # ENVÍO DEL CORREO CON FACTURA PDF DESPUÉS DEL COMMIT

        try:

            tasa = Decimal(str(venta_actual.tasa_cambio))

            if not tasa.is_finite() or tasa <= 0:
                raise ValueError(
                    "La tasa de cambio registrada no es válida."
                )

            articulos_correo = [
                {
                    "producto": detalle.id_producto,
                    "cantidad": detalle.cantidad,
                    "precio_unitario": detalle.precio_unidad,
                    "precio_unitario_usd": (
                        detalle.precio_unidad / tasa
                    ).quantize(
                        Decimal("0.01"),
                        rounding=ROUND_HALF_UP
                    ),
                    "subtotal": detalle.subtotal,
                    "subtotal_usd": (
                        detalle.subtotal / tasa
                    ).quantize(
                        Decimal("0.01"),
                        rounding=ROUND_HALF_UP
                    )
                }
                for detalle in detalles
            ]

            contexto_correo = {
                "usuario": usuario_cliente,
                "comprobante": venta_actual.comprobante,
                "fecha_compra": venta_actual.fecha_venta,
                "tasa_cambio": tasa,
                "articulos": articulos_correo,
                "subtotal": venta_actual.subtotal,
                "subtotal_usd": (
                    venta_actual.subtotal / tasa
                ).quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP
                ),
                "descuento": venta_actual.descuento,
                "descuento_usd": (
                    venta_actual.descuento / tasa
                ).quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP
                ),
                "impuesto": venta_actual.impuesto,
                "impuesto_usd": (
                    venta_actual.impuesto / tasa
                ).quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP
                ),
                "total": venta_actual.total,
                "total_usd": (
                    venta_actual.total / tasa
                ).quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP
                )
            }

            correo_enviado = enviar_correo_compra_confirmada_con_factura(
                destinatario=correo_principal,
                contexto=contexto_correo,
                comprobante=venta_actual.comprobante,
                id_venta=venta_actual.id_venta
            )

        except Exception:
            logger.exception(
                "Error al preparar o enviar el correo de confirmación "
                "de la venta %s.",
                id_venta
            )

            correo_enviado = False

        if correo_enviado:

            return JsonResponse({
                "estado": "exito",
                "title": "Venta confirmada",
                "icon": "success",
                "inhabilitar_botones": True,
                "estado_venta": venta.Estado.CONFIRMADA,
                "descripcion": (
                    "La venta fue confirmada correctamente. "
                    "Se registraron los movimientos de salida "
                    "del inventario y se envió la factura confirmada "
                    "en formato PDF al correo principal del cliente."
                )
            })

        return JsonResponse({
            "estado": "exito",
            "title": "Venta confirmada con advertencia",
            "icon": "warning",
            "inhabilitar_botones": True,
            "estado_venta": venta.Estado.CONFIRMADA,
            "descripcion": (
                "La venta fue confirmada correctamente y se "
                "registraron los movimientos de salida del inventario. "
                "Sin embargo, no fue posible enviar el correo con "
                "la factura PDF al cliente. Verifique el servicio "
                "de correo electrónico."
            )
        })

    except venta.DoesNotExist:

        return JsonResponse({
            "estado": "fallo",
            "title": "Venta no encontrada",
            "icon": "warning",
            "descripcion": "La venta solicitada no existe.",
            "inhabilitar_botones": True
        }, status=404)

    except cliente.DoesNotExist:

        return JsonResponse({
            "estado": "fallo",
            "title": "Cliente no encontrado",
            "icon": "warning",
            "descripcion": (
                "No se encontró el cliente asociado a la venta."
            )
        }, status=404)

    except tipo_movimiento.DoesNotExist:

        return JsonResponse({
            "estado": "fallo",
            "title": "Movimiento no configurado",
            "icon": "warning",
            "descripcion": (
                "No existe un tipo de movimiento de salida activo "
                "denominado Venta. Verifique la configuración "
                "de los tipos de movimiento."
            )
        }, status=400)

    except ValueError as error:

        return JsonResponse({
            "estado": "fallo",
            "title": "No se pudo confirmar la venta",
            "icon": "warning",
            "descripcion": str(error)
        }, status=400)

    except Exception as error:

        logger.exception(
            "Error al confirmar la venta %s.",
            id_venta
        )

        return JsonResponse({
            "estado": "fallo",
            "title": "Error al confirmar la venta",
            "icon": "error",
            "descripcion": (
                "Ocurrió un error inesperado al procesar la "
                "confirmación de la venta. La operación fue "
                "revertida y no se aplicaron cambios. "
                f"{error}"
            )
        }, status=500)

# ACCIÓN RECHAZAR LA COMPRA

def enviar_correo_compra_rechazada(destinatario, contexto, comprobante):
    try:
        contenido_html = render_to_string(
            "Email/compra_rechazada.html",
            contexto
        )

        contenido_texto = strip_tags(contenido_html)

        lineas_limpias = [
            linea.strip()
            for linea in contenido_texto.splitlines()
            if linea.strip()
        ]

        texto_plano_final = "\n".join(lineas_limpias)

        correo = EmailMultiAlternatives(
            subject=f"Compra rechazada - {comprobante}",
            body=texto_plano_final,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[destinatario]
        )

        correo.attach_alternative(
            contenido_html,
            "text/html"
        )

        return bool(correo.send())

    except Exception:
        logger.exception(
            "Error al renderizar o enviar el correo de compra rechazada. "
            "Comprobante: %s",
            comprobante
        )

        return False

def rechazar_venta(request):
    id_venta = request.POST.get("id_venta")
    motivo_rechazo = request.POST.get("motivo_rechazo")

    if not id_venta:
        return JsonResponse({
            "estado": "fallo",
            "title": "Venta no identificada",
            "icon": "warning",
            "descripcion": "No se recibió el identificador de la venta.",
            "inhabilitar_botones": True
        }, status=400)

    if not motivo_rechazo:
        return JsonResponse({
            "estado": "fallo",
            "title": "Motivo no seleccionado",
            "icon": "warning",
            "descripcion": "Debe seleccionar el motivo del rechazo."
        }, status=400)

    if motivo_rechazo not in venta.MotivoRechazo.values:
        return JsonResponse({
            "estado": "fallo",
            "title": "Motivo no válido",
            "icon": "warning",
            "descripcion": "El motivo seleccionado no es válido."
        }, status=400)

    try:
        id_venta = int(id_venta)
    except (TypeError, ValueError):
        return JsonResponse({
            "estado": "fallo",
            "title": "Venta no identificada",
            "icon": "warning",
            "descripcion": "El identificador de la venta no es válido.",
            "inhabilitar_botones": True
        }, status=400)

    try:
        correo_principal = None
        usuario_cliente = None
        detalles = []
        venta_actual = None

        with transaction.atomic():

            venta_actual = venta.objects.select_for_update().get(
                id_venta=id_venta
            )

            # VALIDAR QUE LA VENTA SIGA PENDIENTE

            if venta_actual.estado != venta.Estado.PENDIENTE_CONFIRMACION:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Venta no disponible",
                    "icon": "warning",
                    "descripcion": (
                        "Esta venta ya fue procesada o dejó de estar "
                        "pendiente de confirmación."
                    ),
                    "estado_venta": venta_actual.estado,
                    "inhabilitar_botones": True
                }, status=400)

            # OBTENER DATOS DEL CLIENTE

            cliente_actual = cliente.objects.select_related(
                "id_usuario"
            ).filter(
                id_cliente=venta_actual.id_cliente_id
            ).first()

            if cliente_actual:
                usuario_cliente = cliente_actual.id_usuario

                contacto_cliente = contacto.objects.filter(
                    id_usuario=usuario_cliente
                ).first()

                if contacto_cliente:
                    correo_principal = contacto_cliente.correo_principal

            # OBTENER LOS DETALLES DE LA VENTA

            detalles = list(
                detalle_venta.objects.select_related(
                    "id_producto",
                    "id_producto__id_unidad"
                ).filter(
                    id_venta=venta_actual
                ).order_by("id_producto_id")
            )

            if not detalles:
                raise ValueError(
                    "No se puede rechazar la venta porque no tiene "
                    "productos registrados."
                )

            venta_actual.motivo_rechazo = motivo_rechazo
            motivo_descriptivo = venta_actual.get_motivo_rechazo_display()

            if venta_actual.inventario_descontado:
                cantidades = defaultdict(
                    lambda: Decimal("0.000")
                )
                productos = {}

                for detalle in detalles:
                    cantidades[detalle.id_producto_id] += detalle.cantidad
                    productos[detalle.id_producto_id] = detalle.id_producto

                existencias = list(
                    existencia_inventario.objects.select_for_update().filter(
                        id_producto_id__in=list(cantidades.keys())
                    ).order_by("id_producto_id")
                )
                existencias_por_producto = {
                    existencia.id_producto_id: existencia
                    for existencia in existencias
                }

                for id_producto, cantidad in cantidades.items():
                    existencia = existencias_por_producto.get(id_producto)
                    if existencia is None:
                        raise ValueError(
                            f"El producto {productos[id_producto].nombre} "
                            "no tiene existencias registradas."
                        )

                    existencia.cantidad_actual += cantidad
                    existencia.save(
                        update_fields=[
                            "cantidad_actual",
                            "fecha_actualizacion",
                        ]
                    )

                tipo_entrada, _ = tipo_movimiento.objects.get_or_create(
                    nombre="Devolución",
                    defaults={
                        "direccion": tipo_movimiento.Direccion.ENTRADA,
                        "es_perdida": False,
                        "activo": True,
                    },
                )

                if (
                    tipo_entrada.direccion != tipo_movimiento.Direccion.ENTRADA
                    or tipo_entrada.es_perdida
                    or not tipo_entrada.activo
                ):
                    raise tipo_movimiento.DoesNotExist

                movimiento_inventario.objects.bulk_create([
                    movimiento_inventario(
                        id_producto=detalle.id_producto,
                        id_venta=venta_actual,
                        id_tipo_movimiento=tipo_entrada,
                        cantidad=detalle.cantidad,
                        costo_unitario=detalle.costo_unitario,
                        valor_total=detalle.costo_total,
                        motivo=(
                            f"Devolución al inventario por rechazo "
                            f"de la venta {venta_actual.comprobante}. "
                            f"Motivo: {motivo_descriptivo}"
                        )
                    )
                    for detalle in detalles
                ])

            venta_actual.estado = venta.Estado.RECHAZADA
            venta_actual.inventario_descontado = False

            venta_actual.save(
                update_fields=[
                    "estado",
                    "motivo_rechazo",
                    "inventario_descontado",
                ]
            )

        # ENVÍO DEL CORREO DESPUÉS DEL COMMIT

        correo_enviado = False

        if correo_principal and usuario_cliente:

            try:
                tasa = Decimal(str(venta_actual.tasa_cambio))

                if not tasa.is_finite() or tasa <= 0:
                    raise ValueError(
                        "La tasa de cambio registrada no es válida."
                    )

                articulos_correo = [
                    {
                        "producto": detalle.id_producto,
                        "cantidad": detalle.cantidad,
                        "precio_unitario": detalle.precio_unidad,
                        "precio_unitario_usd": (
                            detalle.precio_unidad / tasa
                        ).quantize(
                            Decimal("0.01"),
                            rounding=ROUND_HALF_UP
                        ),
                        "subtotal": detalle.subtotal,
                        "subtotal_usd": (
                            detalle.subtotal / tasa
                        ).quantize(
                            Decimal("0.01"),
                            rounding=ROUND_HALF_UP
                        )
                    }
                    for detalle in detalles
                ]

                contexto_correo = {
                    "usuario": usuario_cliente,
                    "comprobante": venta_actual.comprobante,
                    "fecha_compra": venta_actual.fecha_venta,
                    "tasa_cambio": tasa,
                    "motivo_rechazo": motivo_descriptivo,
                    "articulos": articulos_correo,
                    "subtotal": venta_actual.subtotal,
                    "subtotal_usd": (
                        venta_actual.subtotal / tasa
                    ).quantize(
                        Decimal("0.01"),
                        rounding=ROUND_HALF_UP
                    ),
                    "descuento": venta_actual.descuento,
                    "descuento_usd": (
                        venta_actual.descuento / tasa
                    ).quantize(
                        Decimal("0.01"),
                        rounding=ROUND_HALF_UP
                    ),
                    "impuesto": venta_actual.impuesto,
                    "impuesto_usd": (
                        venta_actual.impuesto / tasa
                    ).quantize(
                        Decimal("0.01"),
                        rounding=ROUND_HALF_UP
                    ),
                    "total": venta_actual.total,
                    "total_usd": (
                        venta_actual.total / tasa
                    ).quantize(
                        Decimal("0.01"),
                        rounding=ROUND_HALF_UP
                    )
                }

                correo_enviado = enviar_correo_compra_rechazada(
                    destinatario=correo_principal,
                    contexto=contexto_correo,
                    comprobante=venta_actual.comprobante
                )

            except Exception:
                logger.exception(
                    "Error al preparar o enviar el correo de rechazo "
                    "de la venta %s.",
                    id_venta
                )

                correo_enviado = False

        if correo_enviado:

            return JsonResponse({
                "estado": "exito",
                "title": "Venta rechazada",
                "icon": "success",
                "descripcion": (
                    "La venta fue rechazada correctamente. "
                    "Se registraron los movimientos de entrada "
                    "y los productos fueron devueltos al inventario. "
                    "También se envió la notificación de rechazo "
                    "al correo principal del cliente."
                ),
                "estado_venta": venta_actual.estado,
                "inhabilitar_botones": True
            })

        return JsonResponse({
            "estado": "exito",
            "title": "Venta rechazada con advertencia",
            "icon": "warning",
            "descripcion": (
                "La venta fue rechazada correctamente y se "
                "registraron los movimientos de entrada. "
                "Sin embargo, no fue posible enviar la notificación "
                "al correo del cliente. Verifique que tenga un "
                "correo principal registrado y que el servicio "
                "de correo electrónico esté funcionando."
            ),
            "estado_venta": venta_actual.estado,
            "inhabilitar_botones": True
        })

    except venta.DoesNotExist:

        return JsonResponse({
            "estado": "fallo",
            "title": "Venta no encontrada",
            "icon": "warning",
            "descripcion": "No se encontró la venta indicada.",
            "inhabilitar_botones": True
        }, status=404)

    except tipo_movimiento.DoesNotExist:

        return JsonResponse({
            "estado": "fallo",
            "title": "Movimiento no configurado",
            "icon": "warning",
            "descripcion": (
                "No existe un tipo de movimiento de entrada activo "
                "denominado Devolución. Verifique la configuración "
                "de los tipos de movimiento."
            )
        }, status=400)

    except ValueError as error:

        return JsonResponse({
            "estado": "fallo",
            "title": "No se pudo rechazar la venta",
            "icon": "warning",
            "descripcion": str(error)
        }, status=400)

    except Exception:

        logger.exception(
            "Error al rechazar la venta %s.",
            id_venta
        )

        return JsonResponse({
            "estado": "fallo",
            "title": "Error al rechazar la venta",
            "icon": "error",
            "descripcion": (
                "Ocurrió un error inesperado al procesar el rechazo. "
                "La operación fue revertida y no se aplicaron cambios."
            )
        }, status=500)

# FACTURA EN PDF

def generar_factura_compra(venta_actual):
    buffer = BytesIO()

    try:
        documento = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=15 * mm,
            leftMargin=15 * mm,
            topMargin=28 * mm,
            bottomMargin=18 * mm
        )

        # ---------------------------------------------------------
        # COLORES
        # ---------------------------------------------------------

        azul_principal = colors.HexColor("#102F4E")
        azul_borde = colors.HexColor("#DCE6EC")
        gris_fondo = colors.HexColor("#F3F7F9")
        gris_texto = colors.HexColor("#52606D")
        verde = colors.HexColor("#15803D")
        verde_fondo = colors.HexColor("#DCFCE7")
        naranja = colors.HexColor("#D97706")
        naranja_fondo = colors.HexColor("#FEF3C7")

        # ---------------------------------------------------------
        # ESTADO DEL DOCUMENTO
        # ---------------------------------------------------------

        estado_actual = str(venta_actual.estado)

        if estado_actual == "CONFIRMADA":
            titulo_documento = "FACTURA DE COMPRA"
            texto_estado = "CONFIRMADA"
            color_estado = verde
            fondo_estado = verde_fondo

            mensaje_confirmacion = (
                "<b>COMPRA CONFIRMADA:</b> Hielo Caipe C.A. ha verificado "
                "y aprobado el pago correspondiente. La compra ha sido "
                "confirmada satisfactoriamente."
            )

        elif estado_actual == "PENDIENTE_CONFIRMACION":
            titulo_documento = "COMPROBANTE DE PREVENTA"
            texto_estado = "PENDIENTE DE CONFIRMACIÓN"
            color_estado = naranja
            fondo_estado = naranja_fondo

            mensaje_confirmacion = (
                "<b>COMPRA PENDIENTE:</b> El pago y la compra se encuentran "
                "pendientes de verificación por parte de Hielo Caipe C.A."
            )

        else:
            raise ValueError(
                f"No se puede generar el documento para el estado: {estado_actual}"
            )

        # ---------------------------------------------------------
        # FUNCIONES AUXILIARES
        # ---------------------------------------------------------

        def texto(valor, predeterminado="N/A"):
            if valor is None or str(valor).strip() == "":
                valor = predeterminado

            return escape(str(valor))

        def dato_cuenta(valor):
            if valor is None or str(valor).strip().upper() in ("", "N/A"):
                return texto("No registrado")

            return texto(valor)

        def decimal_seguro(valor):
            try:
                return Decimal(str(valor or 0))
            except (InvalidOperation, TypeError, ValueError):
                return Decimal("0")

        def formato_moneda(valor):
            valor = decimal_seguro(valor)
            return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        def formato_cantidad(valor, permite_decimales):
            cantidad = decimal_seguro(valor)

            if not permite_decimales:
                return f"{cantidad:,.0f}".replace(",", ".")

            cantidad_formateada = f"{cantidad:,.3f}".rstrip("0").rstrip(".")
            return cantidad_formateada.replace(",", "X").replace(".", ",").replace("X", ".")

        def moneda_usd(valor):
            valor = decimal_seguro(valor)
            return f"$ {formato_moneda(valor)}"

        def parrafo(valor, estilo):
            return Paragraph(str(valor), estilo)

        def obtener_atributo(objeto, *atributos, predeterminado="N/A"):
            for atributo in atributos:
                valor = getattr(objeto, atributo, None)

                if valor is not None and str(valor).strip():
                    return valor

            return predeterminado

        # ---------------------------------------------------------
        # ESTILOS
        # ---------------------------------------------------------

        estilos = getSampleStyleSheet()

        estilo_normal = ParagraphStyle(
            "EstiloNormalFactura",
            parent=estilos["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=gris_texto,
            alignment=TA_LEFT
        )

        estilo_centrado = ParagraphStyle(
            "EstiloCentradoFactura",
            parent=estilo_normal,
            alignment=TA_CENTER
        )

        estilo_izquierdo = ParagraphStyle(
            "EstiloIzquierdoFactura",
            parent=estilo_normal,
            alignment=TA_LEFT
        )
        
        estilo_derecha = ParagraphStyle(
            "EstiloDerechaFactura",
            parent=estilo_normal,
            alignment=TA_RIGHT
        )

        estilo_negrita = ParagraphStyle(
            "EstiloNegritaFactura",
            parent=estilo_normal,
            fontName="Helvetica-Bold",
            textColor=azul_principal
        )

        estilo_encabezado = ParagraphStyle(
            "EstiloEncabezadoFactura",
            parent=estilo_normal,
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=colors.white,
            alignment=TA_CENTER
        )

        estilo_titulo = ParagraphStyle(
            "EstiloTituloFactura",
            parent=estilo_normal,
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=azul_principal,
            alignment=TA_CENTER
        )

        estilo_subtitulo = ParagraphStyle(
            "EstiloSubtituloFactura",
            parent=estilo_normal,
            fontSize=8,
            leading=11,
            alignment=TA_CENTER
        )

        estilo_seccion = ParagraphStyle(
            "EstiloSeccionFactura",
            parent=estilo_normal,
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            textColor=azul_principal
        )

        # ---------------------------------------------------------
        # INFORMACIÓN DEL CLIENTE
        # ---------------------------------------------------------

        cliente = venta_actual.id_cliente
        usuario_actual = cliente.id_usuario

        contacto = getattr(usuario_actual, "contacto", None)

        nombre_cliente = (
            obtener_atributo(usuario_actual, "nombre_razon_social")
            if obtener_atributo(usuario_actual, "tipo_usuario") == "EMPRESA"
            else (
                f"{obtener_atributo(usuario_actual, 'nombres')} "
                f"{obtener_atributo(usuario_actual, 'apellidos')}"
            ).strip()
        )

        identificacion = (
            f"{obtener_atributo(usuario_actual, 'cedula_identidad')}"
        )

        correo_cliente = obtener_atributo(
            contacto,
            "correo_principal"
        )

        # ---------------------------------------------------------
        # INFORMACIÓN GENERAL DE LA VENTA
        # ---------------------------------------------------------

        fecha_venta = venta_actual.fecha_venta

        if fecha_venta:
            if timezone.is_aware(fecha_venta):
                fecha_venta = timezone.localtime(fecha_venta)

            fecha_formateada = fecha_venta.strftime("%d/%m/%Y %I:%M %p")
        else:
            fecha_formateada = "N/A"

        numero_comprobante = texto(venta_actual.comprobante)

        contenido = []

        contenido.append(parrafo(titulo_documento, estilo_titulo))
        contenido.append(
            parrafo(
                "Hielo Caipe C.A. | Rif: J-0012902-5 | Barinas, Venezuela",
                estilo_subtitulo
            )
        )
        contenido.append(Spacer(1, 8))

        # ---------------------------------------------------------
        # TABLA GENERAL
        # ---------------------------------------------------------

        filas_generales = [
            [
                parrafo(
                    f"<b>Comprobante:</b> {numero_comprobante}",
                    estilo_normal
                ),
                parrafo(
                    f"<b>Fecha:</b> {texto(fecha_formateada)}",
                    estilo_normal
                )
            ],
            [
                parrafo(
                    f"<b>Cliente:</b> {texto(nombre_cliente)}",
                    estilo_normal
                ),
                parrafo(
                    f"<b>Identificación:</b> {texto(identificacion)}",
                    estilo_normal
                )
            ],
            [
                parrafo(
                    f"<b>Correo:</b> {texto(correo_cliente)}",
                    estilo_normal
                ),
                parrafo(
                    f"<b>Estado:</b> {texto(texto_estado)}",
                    estilo_normal
                )
            ]
        ]

        tabla_general = Table(
            filas_generales,
            colWidths=[92.5 * mm, 92.5 * mm],
            hAlign="LEFT"
        )

        tabla_general.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, azul_borde),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6)
        ]))

        contenido.append(tabla_general)
        contenido.append(Spacer(1, 12))

        # ---------------------------------------------------------
        # DETALLE DE PRODUCTOS
        # ---------------------------------------------------------

        contenido.append(
            parrafo("DETALLE DE PRODUCTOS", estilo_seccion)
        )
        contenido.append(Spacer(1, 5))

        filas_productos = [[
            parrafo("Producto", estilo_encabezado),
            parrafo("Código", estilo_encabezado),
            parrafo("Cant.", estilo_encabezado),
            parrafo("Unid.", estilo_encabezado),
            parrafo("Precio Unit.", estilo_encabezado),
            parrafo("Desc.", estilo_encabezado),
            parrafo("Subtotal", estilo_encabezado)
        ]]

        detalles = venta_actual.detalles.select_related(
            "id_producto__id_unidad"
        ).all()

        for detalle in detalles:
            producto = detalle.id_producto
            unidad = producto.id_unidad

            nombre_producto = obtener_atributo(
                producto,
                "nombre"
            )

            codigo_producto = obtener_atributo(
                producto,
                "codigo"
            )

            cantidad = formato_cantidad(
                detalle.cantidad,
                unidad.permite_decimales
            )

            nombre_unidad = obtener_atributo(
                unidad,
                "abreviatura",
                "nombre_unidad",
                "unidad"
            )

            precio_unitario = decimal_seguro(detalle.precio_unidad)
            descuento = decimal_seguro(detalle.descuento)
            subtotal_producto = decimal_seguro(detalle.subtotal)

            filas_productos.append([
                parrafo(texto(nombre_producto), estilo_normal),
                parrafo(texto(codigo_producto), estilo_centrado),
                parrafo(cantidad, estilo_centrado),
                parrafo(texto(nombre_unidad), estilo_centrado),
                parrafo(formato_moneda(precio_unitario), estilo_izquierdo),
                parrafo(formato_moneda(descuento), estilo_izquierdo),
                parrafo(formato_moneda(subtotal_producto), estilo_izquierdo)
            ])

        tabla_productos = Table(
            filas_productos,
            colWidths=[
                45 * mm,
                22 * mm,
                16 * mm,
                14 * mm,
                30 * mm,
                26 * mm,
                32 * mm
            ],
            repeatRows=1,
            hAlign="LEFT"
        )

        tabla_productos.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), azul_principal),
            ("GRID", (0, 0), (-1, -1), 0.5, azul_borde),
            ("ALIGN", (0, 0), (0, -1), "LEFT"),
            ("ALIGN", (1, 0), (1, -1), "CENTER"),
            ("ALIGN", (2, 0), (2, -1), "RIGHT"),
            ("ALIGN", (3, 0), (3, -1), "CENTER"),
            ("ALIGN", (4, 0), (-1, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
                colors.white,
                gris_fondo
            ])
        ]))

        contenido.append(tabla_productos)
        contenido.append(Spacer(1, 12))

        # ---------------------------------------------------------
        # RESUMEN DE LA COMPRA
        # ---------------------------------------------------------

        subtotal = decimal_seguro(venta_actual.subtotal)
        descuento_total = decimal_seguro(venta_actual.descuento)
        impuesto = decimal_seguro(venta_actual.impuesto)
        total = decimal_seguro(venta_actual.total)

        tasa_cambio = decimal_seguro(
            obtener_atributo(
                venta_actual,
                "tasa_cambio",
                predeterminado=0
            )
        )

        filas_resumen = [
            [
                parrafo("Subtotal:", estilo_normal),
                parrafo(
                    f"Bs. {formato_moneda(subtotal)}",
                    estilo_derecha
                )
            ],
            [
                parrafo("Descuento:", estilo_normal),
                parrafo(
                    f"Bs. {formato_moneda(descuento_total)}",
                    estilo_derecha
                )
            ],
            [
                parrafo("Impuesto (IVA):", estilo_normal),
                parrafo(
                    f"Bs. {formato_moneda(impuesto)}",
                    estilo_derecha
                )
            ],
            [
                parrafo("TOTAL:", estilo_negrita),
                parrafo(
                    f"Bs. {formato_moneda(total)}",
                    estilo_derecha
                )
            ]
        ]

        if tasa_cambio > 0:
            total_usd = total / tasa_cambio

            filas_resumen.extend([
                [
                    parrafo("Tasa de cambio:", estilo_normal),
                    parrafo(
                        f"Bs. {formato_moneda(tasa_cambio)} por USD",
                        estilo_derecha
                    )
                ],
                [
                    parrafo("Total en USD:", estilo_normal),
                    parrafo(
                        moneda_usd(total_usd),
                        estilo_derecha
                    )
                ]
            ])

        tabla_resumen = Table(
            filas_resumen,
            colWidths=[45 * mm, 45 * mm],
            hAlign="LEFT"
        )

        tabla_resumen.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, azul_borde),
            ("BACKGROUND", (0, 3), (-1, 3), gris_fondo),
            ("TEXTCOLOR", (0, 3), (-1, 3), azul_principal),
            ("FONTNAME", (0, 3), (-1, 3), "Helvetica-Bold"),
            ("ALIGN", (0, 0), (0, -1), "LEFT"),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5)
        ]))

        # ---------------------------------------------------------
        # INFORMACIÓN DEL PAGO
        # ---------------------------------------------------------

        filas_pagos = []

        pagos = venta_actual.pagos.select_related(
            "id_metodo_pago",
            "id_cuenta_destino"
        ).all()

        for pago in pagos:
            metodo = pago.id_metodo_pago
            nombre_metodo = obtener_atributo(
                metodo,
                "nombre",
                "metodo",
                "nombre_metodo"
            )
            es_pago_movil = str(nombre_metodo).strip().casefold() in (
                "pago móvil",
                "pago movil"
            )

            filas_pagos.extend([
                [
                    parrafo("<b>Método:</b>", estilo_normal),
                    parrafo(texto(nombre_metodo), estilo_derecha)
                ],
                [
                    parrafo("<b>Referencia:</b>", estilo_normal),
                    parrafo(texto(pago.referencia), estilo_derecha)
                ],
                [
                    parrafo("<b>Monto:</b>", estilo_normal),
                    parrafo(
                        f"Bs. {formato_moneda(pago.monto)}",
                        estilo_derecha
                    )
                ],
                [
                    parrafo("<b>Estado:</b>", estilo_normal),
                    parrafo(texto(pago.get_estado_display()), estilo_derecha)
                ]
            ])

            cuenta = pago.id_cuenta_destino

            if cuenta:
                banco = obtener_atributo(
                    cuenta,
                    "banco"
                )

                filas_pagos.extend([
                    [
                        parrafo("<b>Banco:</b>", estilo_normal),
                        parrafo(texto(banco), estilo_derecha)
                    ],
                    [
                        parrafo("<b>Documento:</b>", estilo_normal),
                        parrafo(dato_cuenta(cuenta.documento), estilo_derecha)
                    ]
                ])

                tipo_cuenta = str(
                    getattr(cuenta, "tipo_cuenta", "") or ""
                ).strip()
                tipos_cuenta = dict(
                    cuenta_destino_pago.TipoCuenta.choices
                )
                tipo_cuenta_display = tipos_cuenta.get(
                    tipo_cuenta.upper(),
                    tipo_cuenta
                )

                if es_pago_movil:
                    filas_pagos.extend([
                        [
                            parrafo("<b>N.º de Pago Móvil:</b>", estilo_normal),
                            parrafo(dato_cuenta(cuenta.telefono), estilo_derecha)
                        ],
                        [
                            parrafo("<b>Tipo de cuenta:</b>", estilo_normal),
                            parrafo("No aplica", estilo_derecha)
                        ]
                    ])
                else:
                    filas_pagos.extend([
                        [
                            parrafo("<b>Teléfono:</b>", estilo_normal),
                            parrafo(dato_cuenta(cuenta.telefono), estilo_derecha)
                        ],
                        [
                            parrafo("<b>N.º de cuenta:</b>", estilo_normal),
                            parrafo(dato_cuenta(cuenta.numero_cuenta), estilo_derecha)
                        ],
                        [
                            parrafo("<b>Tipo de cuenta:</b>", estilo_normal),
                            parrafo(dato_cuenta(tipo_cuenta_display), estilo_derecha)
                        ]
                    ])

        if not filas_pagos:
            filas_pagos.append([
                parrafo("<b>Estado:</b>", estilo_normal),
                parrafo("No se registraron pagos.", estilo_derecha)
            ])

        tabla_pagos = Table(
            filas_pagos,
            colWidths=[27 * mm, 63 * mm],
            hAlign="LEFT"
        )

        tabla_pagos.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, azul_borde),
            ("BACKGROUND", (0, 0), (0, -1), gris_fondo),
            ("ALIGN", (0, 0), (0, -1), "LEFT"),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4)
        ]))

        tabla_resumen_pagos = Table(
            [[
                [
                    parrafo("RESUMEN DE LA COMPRA", estilo_seccion),
                    Spacer(1, 5),
                    tabla_resumen
                ],
                [
                    parrafo("INFORMACIÓN DEL PAGO", estilo_seccion),
                    Spacer(1, 5),
                    tabla_pagos
                ]
            ]],
            colWidths=[92.5 * mm, 92.5 * mm],
            hAlign="LEFT"
        )
        tabla_resumen_pagos.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 1.25 * mm),
            ("RIGHTPADDING", (0, 0), (-1, -1), 1.25 * mm),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0)
        ]))

        contenido.append(tabla_resumen_pagos)
        contenido.append(Spacer(1, 12))
        contenido.append(Spacer(1, 12))

        # ---------------------------------------------------------
        # AVISO DEL ESTADO DE LA COMPRA
        # ---------------------------------------------------------

        tabla_aviso = Table(
            [[parrafo(mensaje_confirmacion, estilo_normal)]],
            colWidths=[185 * mm],
            hAlign="LEFT"
        )

        tabla_aviso.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), fondo_estado),
            ("BOX", (0, 0), (-1, -1), 0.7, color_estado),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8)
        ]))

        contenido.append(tabla_aviso)

        # ---------------------------------------------------------
        # ENCABEZADO Y PIE DE PÁGINA
        # ---------------------------------------------------------

        ruta_logo = (
            Path(settings.BASE_DIR)
            / "static"
            / "Imagenes"
            / "logo_hielo_caipe.png"
        )

        def encabezado_factura_pdf(canvas, documento_pdf):
            canvas.saveState()

            ancho_pagina, alto_pagina = letter

            # Logo
            if ruta_logo.exists():
                canvas.drawImage(
                    str(ruta_logo),
                    15 * mm,
                    alto_pagina - 24 * mm,
                    width=34 * mm,
                    height=17 * mm,
                    preserveAspectRatio=True,
                    mask="auto"
                )

            # Línea superior
            canvas.setStrokeColor(azul_borde)
            canvas.setLineWidth(0.7)
            canvas.line(
                15 * mm,
                alto_pagina - 25 * mm,
                ancho_pagina - 15 * mm,
                alto_pagina - 25 * mm
            )

            # Pie de página
            canvas.setStrokeColor(azul_borde)
            canvas.line(
                15 * mm,
                14 * mm,
                ancho_pagina - 15 * mm,
                14 * mm
            )

            canvas.setFont("Helvetica", 7)
            canvas.setFillColor(gris_texto)

            canvas.drawString(
                15 * mm,
                9 * mm,
                "Hielo Caipe C.A. — Gracias por su preferencia."
            )

            canvas.drawRightString(
                ancho_pagina - 15 * mm,
                9 * mm,
                f"Comprobante: {numero_comprobante} | Página {documento_pdf.page}"
            )

            canvas.restoreState()

        # ---------------------------------------------------------
        # GENERAR PDF
        # ---------------------------------------------------------

        documento.build(
            contenido,
            onFirstPage=encabezado_factura_pdf,
            onLaterPages=encabezado_factura_pdf
        )

        pdf_generado = buffer.getvalue()
        buffer.close()

        return pdf_generado

    except Exception:
        buffer.close()

        logger.exception(
            "Error al generar el documento PDF de la compra %s.",
            getattr(venta_actual, "comprobante", "SIN COMPROBANTE")
        )

        raise
