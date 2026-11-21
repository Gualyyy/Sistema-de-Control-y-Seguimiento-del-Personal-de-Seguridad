from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from django.utils.dateparse import parse_date

from django.db.models import (
    Sum,
    F,
    DecimalField,
    ExpressionWrapper,
    Count
)

from django.db.models.functions import (
    TruncDate,
    TruncMonth,
    TruncYear,
    TruncWeek
)

from datetime import timedelta
from decimal import Decimal

from ventas.models import venta, detalle_venta

def ganancias_ventas(request):
    return render(request, "Compras/Atencion_Clientes/ganancias_ventas.html")

def respuesta_metodo_no_permitido():
    return JsonResponse({
        "estado": "fallo",
        "title": "Método no permitido",
        "icon": "warning",
        "descripcion": "La solicitud debe realizarse mediante POST."
    }, status=405)

def visualizar_ganancias(request):

    if request.method != "POST":
        return respuesta_metodo_no_permitido()

    try:
        hoy = timezone.localdate()

        fecha_desde = (
            parse_date(request.POST.get("desde", ""))
            or hoy.replace(day=1)
        )

        fecha_hasta = (
            parse_date(request.POST.get("hasta", ""))
            or hoy
        )

        if fecha_desde > fecha_hasta:
            fecha_desde, fecha_hasta = fecha_hasta, fecha_desde

        cero = Decimal("0.00")

        campo_monetario = DecimalField(
            max_digits=14,
            decimal_places=2
        )

        expresion_ingresos = ExpressionWrapper(
            F("subtotal") - F("descuento"),
            output_field=campo_monetario
        )

        # VENTAS CONFIRMADAS
        ventas_confirmadas = venta.objects.filter(
            estado=venta.Estado.CONFIRMADA,
            fecha_venta__date__range=(fecha_desde, fecha_hasta)
        )

        # INGRESOS NETOS
        ingresos_neto = ventas_confirmadas.aggregate(
            total=Sum(expresion_ingresos)
        )["total"] or cero

        # DETALLES DE LAS VENTAS
        detalles = detalle_venta.objects.filter(
            id_venta__in=ventas_confirmadas
        )

        # COSTO HISTÓRICO DE MERCANCÍA VENDIDA
        costo_mercancia = detalles.aggregate(
            total=Sum("costo_total")
        )["total"] or cero

        # GANANCIA DE LAS VENTAS
        ganancia = ingresos_neto - costo_mercancia

        # CANTIDAD DE VENTAS
        cantidad_ventas = ventas_confirmadas.count()

        # CANTIDAD DE PRODUCTOS VENDIDOS
        cantidad_productos = detalles.aggregate(
            total=Sum("cantidad")
        )["total"] or cero

        # INGRESOS AGRUPADOS POR DÍA
        ingresos_diarios = (
            ventas_confirmadas
            .annotate(dia=TruncDate("fecha_venta"))
            .values("dia")
            .annotate(total=Sum(expresion_ingresos))
            .order_by("dia")
        )

        # COSTOS AGRUPADOS POR DÍA
        costos_diarios = (
            detalles
            .annotate(dia=TruncDate("id_venta__fecha_venta"))
            .values("dia")
            .annotate(total=Sum("costo_total"))
            .order_by("dia")
        )

        # INICIALIZAR TODOS LOS DÍAS
        datos_diarios = {}

        fecha_actual = fecha_desde

        while fecha_actual <= fecha_hasta:

            datos_diarios[fecha_actual] = {
                "fecha": fecha_actual.strftime("%d/%m/%Y"),
                "ingresos": cero,
                "costos": cero,
                "ganancia": cero
            }

            fecha_actual += timedelta(days=1)

        # INCORPORAR INGRESOS
        for registro in ingresos_diarios:

            dia = registro["dia"]

            if dia in datos_diarios:
                datos_diarios[dia]["ingresos"] = (
                    registro["total"] or cero
                )

        # INCORPORAR COSTOS
        for registro in costos_diarios:

            dia = registro["dia"]

            if dia in datos_diarios:
                datos_diarios[dia]["costos"] = (
                    registro["total"] or cero
                )

        # CALCULAR GANANCIA DIARIA
        for datos in datos_diarios.values():

            datos["ganancia"] = (
                datos["ingresos"] - datos["costos"]
            )

        # PREPARAR DATOS PARA LA GRÁFICA
        estadistica_grafica = [
            {
                **datos,
                "ingresos": float(datos["ingresos"]),
                "costos": float(datos["costos"]),
                "ganancia": float(datos["ganancia"])
            }
            for datos in datos_diarios.values()
        ]

        return JsonResponse({
            "estado": "exito",
            "datos": {
                "fecha_desde": fecha_desde.strftime("%Y-%m-%d"),
                "fecha_hasta": fecha_hasta.strftime("%Y-%m-%d"),

                "ingresos_neto": float(ingresos_neto),
                "costo_mercancia": float(costo_mercancia),
                "ganancia": float(ganancia),

                "cantidad_ventas": cantidad_ventas,
                "cantidad_productos": float(cantidad_productos),

                "estadistica_grafica": estadistica_grafica
            }
        })

    except Exception:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error al consultar las ganancias",
            "icon": "error",
            "descripcion": (
                "Ocurrió un error al generar la estadística. "
                "Inténtalo nuevamente."
            )
        }, status=500)

def ganancia_producto(request):

    if request.method != "POST":
        return respuesta_metodo_no_permitido()

    try:
        hoy = timezone.localdate()

        fecha_desde = (
            parse_date(request.POST.get("desde", ""))
            or hoy.replace(day=1)
        )

        fecha_hasta = (
            parse_date(request.POST.get("hasta", ""))
            or hoy
        )

        if fecha_desde > fecha_hasta:
            fecha_desde, fecha_hasta = fecha_hasta, fecha_desde

        cero = Decimal("0.00")

        campo_monetario = DecimalField(
            max_digits=14,
            decimal_places=2
        )

        # INGRESOS NETOS POR DETALLE
        expresion_ingresos = ExpressionWrapper(
            F("subtotal") - F("descuento"),
            output_field=campo_monetario
        )

        # VENTAS CONFIRMADAS DEL PERÍODO
        ventas_confirmadas = venta.objects.filter(
            estado=venta.Estado.CONFIRMADA,
            fecha_venta__date__range=(fecha_desde, fecha_hasta)
        )

        # AGRUPAR DETALLES POR PRODUCTO
        productos = (
            detalle_venta.objects
            .filter(id_venta__in=ventas_confirmadas)
            .values(
                "id_producto",
                "id_producto__nombre",
                "id_producto__codigo",
                "id_producto__id_categoria__nombre",
                "id_producto__id_unidad__abreviatura"
            )
            .annotate(
                cantidad_vendida=Sum("cantidad"),
                ingresos=Sum(expresion_ingresos),
                costo_total=Sum("costo_total")
            )
            .order_by("-costo_total")
        )

        # CONSTRUIR ESTADÍSTICAS
        estadistica = []

        total_ingresos = cero
        total_costos = cero
        total_ganancias = cero
        total_cantidad = cero

        for producto in productos:

            ingresos = producto["ingresos"] or cero
            costo = producto["costo_total"] or cero

            ganancia = ingresos - costo

            cantidad = producto["cantidad_vendida"] or cero

            # MARGEN DE RENTABILIDAD
            margen = (
                (ganancia / ingresos) * Decimal("100")
                if ingresos > cero
                else cero
            )

            estadistica.append({
                "id_producto": producto["id_producto"],
                "nombre": producto["id_producto__nombre"],
                "codigo": producto["id_producto__codigo"],
                "categoria": producto["id_producto__id_categoria__nombre"],
                "unidad": producto["id_producto__id_unidad__abreviatura"],

                "cantidad_vendida": float(cantidad),
                "ingresos": float(ingresos),
                "costo_total": float(costo),
                "ganancia": float(ganancia),
                "margen": float(
                    margen.quantize(Decimal("0.01"))
                )
            })

            total_ingresos += ingresos
            total_costos += costo
            total_ganancias += ganancia
            total_cantidad += cantidad

        # MARGEN GENERAL
        margen_general = (
            (total_ganancias / total_ingresos) * Decimal("100")
            if total_ingresos > cero
            else cero
        )

        return JsonResponse({
            "estado": "exito",
            "datos": {
                "fecha_desde": fecha_desde.strftime("%Y-%m-%d"),
                "fecha_hasta": fecha_hasta.strftime("%Y-%m-%d"),

                "total_productos": len(estadistica),
                "cantidad_vendida": float(total_cantidad),

                "total_ingresos": float(total_ingresos),
                "total_costos": float(total_costos),
                "total_ganancias": float(total_ganancias),

                "margen_general": float(
                    margen_general.quantize(Decimal("0.01"))
                ),

                "productos": estadistica
            }
        })

    except Exception:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error al consultar las ganancias",
            "icon": "error",
            "descripcion": (
                "Ocurrió un error al calcular la ganancia por producto. "
                "Inténtalo nuevamente."
            )
        }, status=500)

def ventas_periodo(request):

    if request.method != "POST":
        return respuesta_metodo_no_permitido()

    try:
        hoy = timezone.localdate()

        fecha_desde = (
            parse_date(request.POST.get("desde", ""))
            or hoy.replace(day=1)
        )

        fecha_hasta = (
            parse_date(request.POST.get("hasta", ""))
            or hoy
        )

        if fecha_desde > fecha_hasta:
            fecha_desde, fecha_hasta = fecha_hasta, fecha_desde

        cero = Decimal("0.00")

        campo_monetario = DecimalField(
            max_digits=14,
            decimal_places=2
        )

        # INGRESOS NETOS
        expresion_ingresos = ExpressionWrapper(
            F("subtotal") - F("descuento"),
            output_field=campo_monetario
        )

        # VENTAS CONFIRMADAS
        ventas_confirmadas = venta.objects.filter(
            estado=venta.Estado.CONFIRMADA,
            fecha_venta__date__range=(fecha_desde, fecha_hasta)
        )

        # RESUMEN GENERAL
        resumen = ventas_confirmadas.aggregate(
            total_ventas=Count("id_venta"),
            total_ingresos=Sum(expresion_ingresos)
        )

        total_ventas = resumen["total_ventas"] or 0
        total_ingresos = resumen["total_ingresos"] or cero

        # PRODUCTOS VENDIDOS
        detalles = detalle_venta.objects.filter(
            id_venta__in=ventas_confirmadas
        )

        cantidad_productos = detalles.aggregate(
            total=Sum("cantidad")
        )["total"] or cero

        # PROMEDIO DE VENTA
        promedio_venta = (
            total_ingresos / total_ventas
            if total_ventas > 0
            else cero
        )

        # VENTAS AGRUPADAS POR DÍA
        ventas_diarias = (
            ventas_confirmadas
            .annotate(dia=TruncDate("fecha_venta"))
            .values("dia")
            .annotate(
                cantidad_ventas=Count("id_venta"),
                ingresos=Sum(expresion_ingresos)
            )
            .order_by("dia")
        )

        # PRODUCTOS VENDIDOS AGRUPADOS POR DÍA
        productos_diarios = (
            detalles
            .annotate(dia=TruncDate("id_venta__fecha_venta"))
            .values("dia")
            .annotate(
                cantidad_productos=Sum("cantidad")
            )
            .order_by("dia")
        )

        # INICIALIZAR TODOS LOS DÍAS
        datos_diarios = {}

        fecha_actual = fecha_desde

        while fecha_actual <= fecha_hasta:

            datos_diarios[fecha_actual] = {
                "fecha": fecha_actual.strftime("%d/%m/%Y"),
                "cantidad_ventas": 0,
                "ingresos": cero,
                "cantidad_productos": cero
            }

            fecha_actual += timedelta(days=1)

        # INCORPORAR VENTAS
        for registro in ventas_diarias:

            dia = registro["dia"]

            if dia in datos_diarios:

                datos_diarios[dia]["cantidad_ventas"] = (
                    registro["cantidad_ventas"]
                )

                datos_diarios[dia]["ingresos"] = (
                    registro["ingresos"] or cero
                )

        # INCORPORAR PRODUCTOS
        for registro in productos_diarios:

            dia = registro["dia"]

            if dia in datos_diarios:

                datos_diarios[dia]["cantidad_productos"] = (
                    registro["cantidad_productos"] or cero
                )

        # PREPARAR DATOS PARA LA GRÁFICA
        estadistica_grafica = [
            {
                **datos,
                "ingresos": float(datos["ingresos"]),
                "cantidad_productos": float(
                    datos["cantidad_productos"]
                )
            }
            for datos in datos_diarios.values()
        ]

        # DÍA CON MAYORES INGRESOS
        mejor_dia = max(
            estadistica_grafica,
            key=lambda x: x["ingresos"],
            default=None
        )

        if mejor_dia and mejor_dia["ingresos"] == 0:
            mejor_dia = None

        return JsonResponse({
            "estado": "exito",
            "datos": {
                "fecha_desde": fecha_desde.strftime("%Y-%m-%d"),
                "fecha_hasta": fecha_hasta.strftime("%Y-%m-%d"),

                "total_ventas": total_ventas,
                "total_ingresos": float(total_ingresos),
                "cantidad_productos": float(cantidad_productos),

                "promedio_venta": float(
                    promedio_venta.quantize(Decimal("0.01"))
                ),

                "mejor_dia": mejor_dia,

                "estadistica_grafica": estadistica_grafica
            }
        })

    except Exception:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error al consultar las ventas",
            "icon": "error",
            "descripcion": (
                "Ocurrió un error al generar la estadística de ventas. "
                "Inténtalo nuevamente."
            )
        }, status=500)

def ganancia_periodo(request):

    if request.method != "POST":
        return respuesta_metodo_no_permitido()

    periodo = request.POST.get("periodo", "mensual").lower()

    try:
        hoy = timezone.localdate()

        cero = Decimal("0.00")

        campo_monetario = DecimalField(
            max_digits=14,
            decimal_places=2
        )

        expresion_ingresos = ExpressionWrapper(
            F("subtotal") - F("descuento"),
            output_field=campo_monetario
        )

        # CONFIGURAR EL PERÍODO
        if periodo == "diario":

            fecha_inicio = hoy - timedelta(days=6)
            truncacion = TruncDate

        elif periodo == "semanal":

            fecha_inicio = hoy - timedelta(weeks=7)
            truncacion = TruncWeek

        elif periodo == "mensual":

            fecha_inicio = hoy.replace(day=1) - timedelta(days=365)
            truncacion = TruncMonth

        elif periodo == "anual":

            fecha_inicio = hoy.replace(
                month=1,
                day=1
            ) - timedelta(days=365 * 4)

            truncacion = TruncYear

        else:

            return JsonResponse({
                "estado": "fallo",
                "title": "Período inválido",
                "icon": "warning",
                "descripcion": "El período seleccionado no es válido."
            }, status=400)

        fecha_fin = hoy

        # INGRESOS AGRUPADOS POR PERÍODO
        ventas = (
            venta.objects
            .filter(
                estado=venta.Estado.CONFIRMADA,
                fecha_venta__date__gte=fecha_inicio,
                fecha_venta__date__lte=fecha_fin
            )
            .annotate(
                periodo=truncacion("fecha_venta")
            )
            .values("periodo")
            .annotate(
                ingresos=Sum(expresion_ingresos),
                cantidad_ventas=Count("id_venta")
            )
            .order_by("periodo")
        )

        # COSTOS HISTÓRICOS AGRUPADOS POR PERÍODO
        costos = (
            detalle_venta.objects
            .filter(
                id_venta__estado=venta.Estado.CONFIRMADA,
                id_venta__fecha_venta__date__gte=fecha_inicio,
                id_venta__fecha_venta__date__lte=fecha_fin
            )
            .annotate(
                periodo=truncacion("id_venta__fecha_venta")
            )
            .values("periodo")
            .annotate(
                costo_ventas=Sum("costo_total")
            )
            .order_by("periodo")
        )

        # UNIFICAR RESULTADOS
        resultados = {}

        for registro in ventas:

            fecha = registro["periodo"]

            resultados[fecha] = {
                "ingresos": registro["ingresos"] or cero,
                "costo_ventas": cero,
                "cantidad_ventas": registro["cantidad_ventas"]
            }

        for registro in costos:

            fecha = registro["periodo"]

            if fecha not in resultados:

                resultados[fecha] = {
                    "ingresos": cero,
                    "costo_ventas": cero,
                    "cantidad_ventas": 0
                }

            resultados[fecha]["costo_ventas"] = (
                registro["costo_ventas"] or cero
            )

        # CALCULAR GANANCIAS POR PERÍODO
        datos = []

        for fecha in sorted(resultados):

            registro = resultados[fecha]

            ingresos = registro["ingresos"]
            costo = registro["costo_ventas"]

            ganancia = ingresos - costo

            datos.append({
                "fecha": fecha.strftime("%Y-%m-%d"),

                "ingresos": float(ingresos),
                "costo_ventas": float(costo),
                "ganancia": float(ganancia),

                "cantidad_ventas": registro["cantidad_ventas"]
            })

        return JsonResponse({
            "estado": "exito",
            "periodo": periodo,
            "datos": datos
        })

    except Exception:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error al consultar las ganancias",
            "icon": "error",
            "descripcion": (
                "Ocurrió un error al generar las ganancias por período. "
                "Inténtalo nuevamente."
            )
        }, status=500)
