from django.shortcuts import render
from django.http import JsonResponse
from django.db import transaction

from django.core.exceptions import ValidationError
from django.utils.dateparse import parse_date
from django.utils import timezone
from decimal import Decimal, InvalidOperation

from inicio_sesion.models import categoria_gasto, gasto, usuarios, bitacora

# GESTIONAR GASTOS

# CATEGORIA DEL GASTO

def categorias_gastos(request):
    categorias = categoria_gasto.objects.order_by("nombre")

    datos = [
        {
            "id_categoria_gasto": categoria.id_categoria_gasto,
            "nombre": categoria.nombre,
            "descripcion": categoria.descripcion,
            "activo": categoria.activo
        }
        for categoria in categorias
    ]

    return JsonResponse(datos, safe=False)

# REGISTRAR GASTOS

def registrar_gastos(request):
    if request.method != "POST":
        return render(request, "Modulos/Gastos/registrar_gastos.html")

    categoria_gastos = request.POST.get("categoria_gastos", "").strip()
    descripcion = request.POST.get("descripcion", "").strip()
    monto_gasto = request.POST.get("monto_gasto", "").strip()
    fecha_gasto = request.POST.get("fecha_gasto", "").strip()
    es_recurrente = request.POST.get("es_recurrente", "").strip()
    frecuencia = request.POST.get("frecuencia", "").strip()
    referencia = request.POST.get("referencia", "").strip()
    observacion = request.POST.get("observacion", "").strip()

    campos_obligatorios = [
        (categoria_gastos, "Categoría de Gasto", "Por favor, debe seleccionar la categoría del gasto."),
        (descripcion, "Descripción", "Por favor, debe ingresar la descripción del gasto."),
        (monto_gasto, "Monto del Gasto", "Por favor, debe ingresar el monto del gasto."),
        (fecha_gasto, "Fecha del Gasto", "Por favor, debe seleccionar la fecha del gasto."),
        (es_recurrente, "Recurrente", "Por favor, debe seleccionar si el gasto es recurrente.")
    ]

    for valor, campo, mensaje in campos_obligatorios:
        if not valor:
            return JsonResponse({
                "estado": "fallo",
                "title": campo,
                "descripcion": mensaje,
                "icon": "warning"
            })

    try:
        monto = Decimal(monto_gasto)

        if not monto.is_finite() or monto <= 0:
            raise InvalidOperation

    except (InvalidOperation, ValueError):
        return JsonResponse({
            "estado": "fallo",
            "title": "Monto del Gasto",
            "descripcion": "El monto debe ser un número válido mayor que cero.",
            "icon": "warning"
        })

    fecha = parse_date(fecha_gasto)

    if not fecha:
        return JsonResponse({
            "estado": "fallo",
            "title": "Fecha del Gasto",
            "descripcion": "La fecha ingresada no es válida.",
            "icon": "warning"
        })

    if es_recurrente.lower() in ["true", "1", "on", "si", "sí"]:
        recurrente = True
    elif es_recurrente.lower() in ["false", "0", "no"]:
        recurrente = False
    else:
        return JsonResponse({
            "estado": "fallo",
            "title": "Recurrente",
            "descripcion": "La opción de recurrencia seleccionada no es válida.",
            "icon": "warning"
        })

    if recurrente:
        frecuencias_validas = [
            gasto.Frecuencia.SEMANAL,
            gasto.Frecuencia.MENSUAL,
            gasto.Frecuencia.ANUAL
        ]

        if frecuencia not in frecuencias_validas:
            return JsonResponse({
                "estado": "fallo",
                "title": "Frecuencia",
                "descripcion": "Debe seleccionar una frecuencia válida para el gasto recurrente.",
                "icon": "warning"
            })
    else:
        frecuencia = gasto.Frecuencia.UNICO

    try:
        with transaction.atomic():
            obj_categoria = categoria_gasto.objects.get(
                id_categoria_gasto=categoria_gastos,
                activo=True
            )

            nuevo_gasto = gasto(
                id_categoria_gasto=obj_categoria,
                descripcion=descripcion,
                monto=monto,
                fecha_gasto=fecha,
                es_recurrente=recurrente,
                frecuencia=frecuencia,
                referencia=referencia,
                observacion=observacion
            )

            nuevo_gasto.full_clean()
            nuevo_gasto.save()

            # USUARIO QUE REALIZA LA ACCIÓN
            info_usuario = usuarios.objects.get(
                cedula_identidad=request.session.get(
                    "cedula_identidad"
                )
            )

            accion = (
                f"Registro del gasto ID {nuevo_gasto.id_gasto}: "
                f"{nuevo_gasto.descripcion}"
            )

            bitacora.objects.create(
                id_usuario=info_usuario,
                nombre_modulo="Registro de gastos",
                cargo_usuario=request.session.get("perfil", "No especificado"),
                accion=accion
            )

        return JsonResponse({
            "estado": "exito",
            "title": "Gasto registrado",
            "descripcion": "El gasto se ha registrado correctamente.",
            "icon": "success"
        })

    except categoria_gasto.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Categoría de Gasto",
            "descripcion": "La categoría seleccionada no existe o está inactiva.",
            "icon": "warning"
        })

    except ValidationError as e:
        return JsonResponse({
            "estado": "fallo",
            "title": "Datos inválidos",
            "descripcion": "Verifique los datos ingresados. " + str(e),
            "icon": "warning"
        })

    except Exception:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "descripcion": "Ocurrió un error al momento de registrar el gasto. Inténtelo nuevamente.",
            "icon": "error"
        })

# GESTIÓN DE GASTOS

def gestion_gastos(request):
    return render(request, "Modulos/Gastos/gestionar_gastos.html")

# OBTENER GASTOS REGISTRADOS

def visualizar_gastos(request):
    categoria = request.POST.get("categoria_gasto", "").strip()

    gastos = gasto.objects.select_related(
        "id_categoria_gasto"
    ).order_by("-fecha_gasto", "-id_gasto")

    if categoria and categoria.isdigit():
        gastos = gastos.filter(
            id_categoria_gasto_id=int(categoria)
        )

    datos = [
        {
            "id_gasto": gasto_obj.id_gasto,
            "id_categoria_gasto": gasto_obj.id_categoria_gasto.id_categoria_gasto,
            "categoria": gasto_obj.id_categoria_gasto.nombre,
            "descripcion": gasto_obj.descripcion,
            "monto": str(gasto_obj.monto),
            "fecha_gasto": gasto_obj.fecha_gasto.strftime("%d/%m/%Y"),
            "es_recurrente": gasto_obj.es_recurrente,
            "frecuencia": gasto_obj.get_frecuencia_display(),
            "referencia": gasto_obj.referencia or "N/A",
            "estado": gasto_obj.get_estado_display(),
            "observacion": gasto_obj.observacion or "N/A"
        }
        for gasto_obj in gastos
    ]

    return JsonResponse({
        "estado": "exito",
        "gastos": datos,
        "total": len(datos)
    })

# BUSCAR GASTOS

def buscar_gasto(request):
    id_gasto = request.POST.get("id_gasto", "").strip()

    if not id_gasto or not id_gasto.isdigit():
        return JsonResponse({
            "estado": "fallo",
            "title": "Gasto",
            "descripcion": "El identificador del gasto no es válido.",
            "icon": "warning"
        })

    try:
        gasto_obj = gasto.objects.select_related(
            "id_categoria_gasto"
        ).get(id_gasto=int(id_gasto))

        datos = {
            "id_gasto": gasto_obj.id_gasto,
            "id_categoria_gasto": gasto_obj.id_categoria_gasto.id_categoria_gasto,
            "categoria": gasto_obj.id_categoria_gasto.nombre,
            "descripcion": gasto_obj.descripcion,
            "monto": str(gasto_obj.monto),
            "fecha_gasto": gasto_obj.fecha_gasto.strftime("%Y-%m-%d"),
            "es_recurrente": gasto_obj.es_recurrente,
            "frecuencia": gasto_obj.frecuencia,
            "referencia": gasto_obj.referencia or "",
            "estado": gasto_obj.estado,
            "observacion": gasto_obj.observacion or ""
        }

        return JsonResponse({
            "estado": "exito",
            "gasto": datos
        })

    except gasto.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Gasto",
            "descripcion": "No se encontró el gasto solicitado.",
            "icon": "warning"
        })

# ACTUALIZAR DATOS DE GASTOS

def actualizar_datos_gasto(request):
    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "title": "Método no permitido",
            "descripcion": "La actualización debe enviarse mediante POST.",
            "icon": "warning"
        }, status=405)

    if request.method == "POST":
        id_gasto = request.POST.get("id_gasto", "").strip()

        categoria_gastos = request.POST.get("categoria_gastos", "").strip()
        descripcion = request.POST.get("descripcion", "").strip()
        monto_gasto = request.POST.get("monto_gasto", "").strip()
        fecha_gasto = request.POST.get("fecha_gasto", "").strip()
        es_recurrente = request.POST.get("es_recurrente", "").strip()
        frecuencia = request.POST.get("frecuencia", "").strip()
        referencia = request.POST.get("referencia", "").strip()
        observacion = request.POST.get("observacion", "").strip()

        if not id_gasto or not id_gasto.isdigit():
            return JsonResponse({
                "estado": "fallo",
                "title": "Gasto",
                "descripcion": "El identificador del gasto no es válido.",
                "icon": "warning"
            })

        if not categoria_gastos.isdigit():
            return JsonResponse({
                "estado": "fallo",
                "title": "Categoría de Gasto",
                "descripcion": "Debe seleccionar una categoría válida.",
                "icon": "warning"
            })

        campos_obligatorios = [
            (categoria_gastos, "Categoría de Gasto", "Por favor, debe seleccionar la categoría del gasto."),
            (descripcion, "Descripción", "Por favor, debe ingresar la descripción del gasto."),
            (monto_gasto, "Monto del Gasto", "Por favor, debe ingresar el monto del gasto."),
            (fecha_gasto, "Fecha del Gasto", "Por favor, debe seleccionar la fecha del gasto."),
            (es_recurrente, "Recurrente", "Por favor, debe seleccionar si el gasto es recurrente.")
        ]

        for valor, campo, mensaje in campos_obligatorios:
            if not valor:
                return JsonResponse({
                    "estado": "fallo",
                    "title": campo,
                    "descripcion": mensaje,
                    "icon": "warning"
                })

        if len(descripcion) > 200:
            return JsonResponse({
                "estado": "fallo",
                "title": "Descripción",
                "descripcion": "La descripción no puede superar los 200 caracteres.",
                "icon": "warning"
            })

        if len(referencia) > 100:
            return JsonResponse({
                "estado": "fallo",
                "title": "Documento o referencia",
                "descripcion": "El documento o referencia no puede superar los 100 caracteres.",
                "icon": "warning"
            })

        if len(observacion) > 250:
            return JsonResponse({
                "estado": "fallo",
                "title": "Observaciones",
                "descripcion": "Las observaciones no pueden superar los 250 caracteres.",
                "icon": "warning"
            })

        try:
            monto = Decimal(monto_gasto)

            if (
                not monto.is_finite()
                or monto <= 0
                or monto > Decimal("999.99")
            ):
                raise InvalidOperation

            if monto.as_tuple().exponent < -2:
                raise InvalidOperation

        except (InvalidOperation, ValueError):
            return JsonResponse({
                "estado": "fallo",
                "title": "Monto del Gasto",
                "descripcion": "El monto debe ser mayor que cero, no superar 999.99 y tener máximo dos decimales.",
                "icon": "warning"
            })

        fecha = parse_date(fecha_gasto)

        if not fecha:
            return JsonResponse({
                "estado": "fallo",
                "title": "Fecha del Gasto",
                "descripcion": "La fecha ingresada no es válida.",
                "icon": "warning"
            })

        if fecha > timezone.localdate():
            return JsonResponse({
                "estado": "fallo",
                "title": "Fecha del Gasto",
                "descripcion": "La fecha del gasto no puede ser futura.",
                "icon": "warning"
            })

        if es_recurrente.lower() in ["true", "1", "on", "si", "sí"]:
            recurrente = True
        elif es_recurrente.lower() in ["false", "0", "no"]:
            recurrente = False
        else:
            return JsonResponse({
                "estado": "fallo",
                "title": "Recurrente",
                "descripcion": "La opción de recurrencia seleccionada no es válida.",
                "icon": "warning"
            })

        if recurrente:
            frecuencias_validas = [
                gasto.Frecuencia.SEMANAL,
                gasto.Frecuencia.MENSUAL,
                gasto.Frecuencia.ANUAL
            ]

            if frecuencia not in frecuencias_validas:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Frecuencia",
                    "descripcion": "Debe seleccionar una frecuencia válida para el gasto recurrente.",
                    "icon": "warning"
                })
        else:
            frecuencia = gasto.Frecuencia.UNICO

        try:
            with transaction.atomic():

                gasto_obj = gasto.objects.select_for_update().get(
                    id_gasto=int(id_gasto)
                )

                obj_categoria = categoria_gasto.objects.get(
                    id_categoria_gasto=categoria_gastos,
                    activo=True
                )

                gasto_obj.id_categoria_gasto = obj_categoria
                gasto_obj.descripcion = descripcion
                gasto_obj.monto = monto
                gasto_obj.fecha_gasto = fecha
                gasto_obj.es_recurrente = recurrente
                gasto_obj.frecuencia = frecuencia
                gasto_obj.referencia = referencia
                gasto_obj.observacion = observacion

                gasto_obj.full_clean()
                gasto_obj.save()

                # USUARIO QUE REALIZA LA ACCIÓN
                info_usuario = usuarios.objects.get(
                    cedula_identidad=request.session.get(
                        "cedula_identidad"
                    )
                )
    
                accion = (
                    f"Actualización del gasto ID {gasto_obj.id_gasto}: "
                    f"{gasto_obj.descripcion}"
                )
    
                bitacora.objects.create(
                    id_usuario=info_usuario,
                    nombre_modulo="Actualización de gastos",
                    cargo_usuario=request.session.get("perfil", "No especificado"),
                    accion=accion
                )

            return JsonResponse({
                "estado": "exito",
                "title": "Gasto actualizado",
                "descripcion": "Los datos del gasto se han actualizado correctamente.",
                "icon": "success"
            })

        except gasto.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "title": "Gasto",
                "descripcion": "No se encontró el gasto que desea actualizar.",
                "icon": "warning"
            })

        except categoria_gasto.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "title": "Categoría de Gasto",
                "descripcion": "La categoría seleccionada no existe o está inactiva.",
                "icon": "warning"
            })

        except ValidationError as e:
            return JsonResponse({
                "estado": "fallo",
                "title": "Datos inválidos",
                "descripcion": "Verifique los datos ingresados. " + str(e),
                "icon": "warning"
            })

        except Exception:
            return JsonResponse({
                "estado": "fallo",
                "title": "Error",
                "descripcion": "Ocurrió un error al momento de actualizar el gasto. Inténtelo nuevamente.",
                "icon": "error"
            })
        