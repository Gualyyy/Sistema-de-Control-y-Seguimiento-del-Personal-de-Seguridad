from django.shortcuts import render
from django.http import JsonResponse
from django.db import IntegrityError, transaction

from ventas.models import metodo_pago, cuenta_destino_pago
from inicio_sesion.models import bitacora, usuarios

# MÉTODOS REGISTRADOS

def metodos_registrados(request):
    metodos = metodo_pago.objects.all().order_by("nombre")

    datos = [
        {
            "id_metodo": metodo.id_metodo_pago,
            "nombre": metodo.nombre,
            "activo": metodo.activo
        }
        for metodo in metodos
    ]

    return JsonResponse({
        "estado": "exito",
        "metodos": datos,
        "total": len(datos)
    })

# VALIDAR EL CAMPOS CRITICOS

def validar_numero_cuenta(request):
    numero_cuenta = request.POST.get("numero_cuenta", "").strip()
    id_cuenta = request.POST.get("id_cuenta", "").strip()

    if not numero_cuenta:
        return JsonResponse({
            "existe": False
        })

    consulta = cuenta_destino_pago.objects.filter(numero_cuenta=numero_cuenta)

    if id_cuenta and id_cuenta.isdigit():
        consulta = consulta.exclude(id_cuenta_destino=id_cuenta)

    existe = consulta.exists()

    return JsonResponse({
        "existe": existe
    })

# REGISTRAR CUENTAS BANCARIAS

def registrar_cuentas(request):
    if request.method != "POST":
        return render(request, "Cuentas_Bancarias/registrar_cuentas.html")

    bancos = request.POST.get("bancos", "").strip()
    metodos_pagos = request.POST.get("metodos_pagos", "").strip()
    nacionalidad = request.POST.get("nacionalidad", "").strip()
    num_cedula = request.POST.get("cedula_identidad", "").strip()

    prefijo = request.POST.get("prefijo", "").strip()
    num_telefono = request.POST.get("num_telefono", "").strip()

    numeros_cuenta = request.POST.get("numeros_cuenta", "").strip()
    tipo_cuenta = request.POST.get("tipo_cuenta", "").strip()

    campos = [
        (bancos, "Banco", "Por favor, debe seleccionar el banco."),
        (metodos_pagos, "Método de Pago", "Por favor, debe seleccionar el método de pago."),
        (nacionalidad, "Nacionalidad", "Por favor, debe seleccionar la nacionalidad."),
        (num_cedula, "Números de Identidad", "Por favor, debe ingresar los números de identidad."),
        (prefijo, "Prefijo", "Por favor, debe seleccionar el prefijo telefónico."),
        (num_telefono, "Número Telefónico", "Por favor, debe ingresar el número telefónico."),
    ]

    for valor, campo, mensaje in campos:
        if not valor:
            return JsonResponse({
                "estado": "fallo",
                "title": campo,
                "descripcion": mensaje,
                "icon": "warning"
            })
    
    documento_identidad = nacionalidad + "-" + num_cedula
    telefono = prefijo + "-" + num_telefono

    metodo = metodo_pago.objects.get(id_metodo_pago=metodos_pagos)

    nombre_metodo = metodo.nombre.strip().casefold()
    es_pago_movil = nombre_metodo in ("pago móvil", "pago movil")

    if es_pago_movil:
        numeros_cuenta = "N/A"
        tipo_cuenta = "N/A"

        consulta = cuenta_destino_pago.objects.filter(
            id_metodo_pago=metodo,
            banco=bancos,
            documento=documento_identidad,
            telefono=telefono,
            activo=True
        )
        if consulta.exists():
            return JsonResponse({
                "estado": "fallo",
                "title": "Pago Móvil Registrado",
                "descripcion": (
                    "Ya existe un Pago Móvil registrado con el mismo banco, "
                    "número telefónico y documento de identidad. "
                    "Verifique los datos ingresados."
                ),
                "icon": "warning"
            })

    if nombre_metodo in ("transferencia bancaria", "transferencia bancaria"):
        consulta = cuenta_destino_pago.objects.filter(
            id_metodo_pago=metodo,
            banco=bancos,
            documento=documento_identidad,
            numero_cuenta=numeros_cuenta,
            tipo_cuenta=tipo_cuenta,
            activo=True
        )
        if consulta.exists():
            return JsonResponse({
                "estado": "fallo",
                "title": "Transferencia Bancaria Registrada",
                "descripcion": (
                    "Ya existe una transferencia bancaria registrada con "
                    "el mismo banco, documento de identidad, número de "
                    "cuenta y tipo de cuenta. Verifique los datos ingresados."
                ),
                "icon": "warning"
            })
           
    if not es_pago_movil and numeros_cuenta and cuenta_destino_pago.objects.filter(
        numero_cuenta=numeros_cuenta,
        activo=True
    ).exists():
        return JsonResponse({
            "estado": "fallo",
            "title": "Cuenta Registrada",
            "descripcion": (
                "Este número de cuenta ya se encuentra registrado. "
                "Por favor, ingrese otro número de cuenta."
            ),
            "icon": "warning"
        })     
    
    try:
        with transaction.atomic():
            obj_usuario = usuarios.objects.get(cedula_identidad=request.session.get("cedula_identidad"))
    
            cuenta_destino_pago.objects.create(
                id_metodo_pago=metodo,
                banco=bancos,
                documento=documento_identidad,
                telefono=telefono,
                numero_cuenta=numeros_cuenta,
                tipo_cuenta=tipo_cuenta,
                activo=True
            )

            bitacora.objects.create(
                id_usuario=obj_usuario,
                nombre_modulo="Métodos de pago y cuentas de destino",
                cargo_usuario=request.session.get("perfil", "No especificado"),
                accion=(
                    f"Registró una cuenta de destino para el método de pago "
                    f"{metodo.nombre}, banco {bancos}, "
                    f"asociada al documento {obj_usuario.cedula_identidad}."
                )
            )

        return JsonResponse({
            "estado": "exito",
            "title": "Cuenta Registrada",
            "descripcion": "La cuenta se registró correctamente.",
            "icon": "success"
        })

    except metodo_pago.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Método de Pago",
            "descripcion": "El método de pago seleccionado no existe.",
            "icon": "warning"
        })

    except IntegrityError as e:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error de Registro",
            "descripcion": f"No fue posible registrar la cuenta. Verifique que los datos no estén duplicados. {e}",
            "icon": "warning"
        })

# PERMITE ACTUALIZAR Y INHABILITAR O HABILITAR

def gestionar_cuentas(request):
    return render(request, "Cuentas_Bancarias/gestionar_cuentas.html")

def visualizar_cuentas(request):
    metodo = request.POST.get("metodo", "").strip()

    cuentas = cuenta_destino_pago.objects.select_related("id_metodo_pago").order_by("-fecha_registro")

    if metodo and metodo.isdigit():
        cuentas = cuentas.filter(
            id_metodo_pago_id=int(metodo)
        )

    datos = [
        {
            "id_cuenta_destino": cuenta.id_cuenta_destino,
            "id_metodo": cuenta.id_metodo_pago.id_metodo_pago,
            "metodo_pago": cuenta.id_metodo_pago.nombre,
            "banco": cuenta.banco,
            "documento": cuenta.documento,
            "telefono": cuenta.telefono or "N/A",
            "numero_cuenta": cuenta.numero_cuenta or "N/A",
            "tipo_cuenta": cuenta.get_tipo_cuenta_display() or "N/A",
            "activo": cuenta.activo,
            "fecha_registro": cuenta.fecha_registro.strftime(
                "%d/%m/%Y %H:%M"
            )
        }
        for cuenta in cuentas
    ]

    return JsonResponse({
        "estado": "exito",
        "cuentas": datos,
        "total": len(datos)
    })

def actualizar_cuentas(request):
    id_cuenta = request.POST.get("id_cuenta", "").strip()
    bancos = request.POST.get("bancos", "").strip()
    metodos_pagos = request.POST.get("metodos_pagos", "").strip()
    nacionalidad = request.POST.get("nacionalidad", "").strip()
    num_cedula = request.POST.get("cedula_identidad", "").strip()
    prefijo = request.POST.get("prefijo", "").strip()
    num_telefono = request.POST.get("num_telefono", "").strip()
    numeros_cuenta = request.POST.get("numeros_cuenta", "").strip()
    tipo_cuenta = request.POST.get("tipo_cuenta", "").strip()

    try:
        cuenta = cuenta_destino_pago.objects.get(
            id_cuenta_destino=id_cuenta
        )

        metodo = metodo_pago.objects.get(
            id_metodo_pago=metodos_pagos
        )

        es_pago_movil = metodo.nombre.strip().casefold() == "pago móvil"

        if numeros_cuenta and not es_pago_movil:
            numero_existente = cuenta_destino_pago.objects.filter(
                numero_cuenta=numeros_cuenta,
                activo=True
            ).exclude(
                id_cuenta_destino=id_cuenta
            ).exists()

            if numero_existente:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Cuenta Registrada",
                    "descripcion": (
                        "Este número de cuenta ya se encuentra registrado. "
                        "Por favor, ingrese otro número de cuenta."
                    ),
                    "icon": "warning"
                })

        if es_pago_movil:
            numero_cuenta_registro = "N/A"
            tipo_cuenta_registro = "N/A"
        else:
            numero_cuenta_registro = numeros_cuenta
            tipo_cuenta_registro = tipo_cuenta

        with transaction.atomic():
            cuenta.id_metodo_pago = metodo
            cuenta.banco = bancos
            cuenta.documento = f"{nacionalidad}-{num_cedula}"
            cuenta.telefono = f"{prefijo}-{num_telefono}"
            cuenta.numero_cuenta = numero_cuenta_registro
            cuenta.tipo_cuenta = tipo_cuenta_registro

            cuenta.save(update_fields=[
                "id_metodo_pago",
                "banco",
                "documento",
                "telefono",
                "numero_cuenta",
                "tipo_cuenta"
            ])

        return JsonResponse({
            "estado": "exito",
            "title": "Cuenta actualizada",
            "descripcion": "La cuenta de destino se actualizó correctamente.",
            "icon": "success"
        })

    except cuenta_destino_pago.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Cuenta no encontrada",
            "descripcion": "La cuenta que intenta actualizar no existe.",
            "icon": "warning"
        })

    except metodo_pago.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Método de pago no encontrado",
            "descripcion": "El método de pago seleccionado no existe.",
            "icon": "warning"
        })

    except IntegrityError:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error de actualización",
            "descripcion": "No fue posible actualizar la cuenta de destino.",
            "icon": "warning"
        })
    
# BUSCAR DATOS DE CUENTA

def buscar_cuentas(request):
    id_cuenta = request.POST.get("id_cuenta", "").strip()

    if not id_cuenta or not id_cuenta.isdigit():
        return JsonResponse({
            "estado": "fallo",
            "title": "Cuenta inválida",
            "descripcion": "La cuenta de destino seleccionada no es válida.",
            "icon": "warning"
        })

    cuenta = cuenta_destino_pago.objects.select_related(
        "id_metodo_pago"
    ).filter(
        id_cuenta_destino=id_cuenta
    ).first()

    if not cuenta:
        return JsonResponse({
            "estado": "fallo",
            "title": "Cuenta no encontrada",
            "descripcion": "La cuenta de destino que intenta consultar no existe.",
            "icon": "warning"
        })

    datos = {
        "id_cuenta_destino": cuenta.id_cuenta_destino,
        "id_metodo": cuenta.id_metodo_pago.id_metodo_pago,
        "metodo_pago": cuenta.id_metodo_pago.nombre,
        "banco": cuenta.banco,
        "documento": cuenta.documento,
        "telefono": cuenta.telefono or "N/A",
        "numero_cuenta": cuenta.numero_cuenta or "N/A",
        "tipo_cuenta": cuenta.tipo_cuenta or "N/A",
        "tipos_cuenta_valor": cuenta.get_tipo_cuenta_display(),
        "activo": cuenta.activo,
        "fecha_registro": cuenta.fecha_registro.strftime("%d/%m/%Y %H:%M")
    }

    return JsonResponse({
        "estado": "exito",
        "cuenta": datos
    })

# CAMBIAR INHABILITAR O HABILITAR

def estado_cuenta(request):
    id_cuenta = request.POST.get("id_cuenta", "").strip()

    if not id_cuenta or not id_cuenta.isdigit():
        return JsonResponse({
            "estado": "fallo",
            "title": "Cuenta inválida",
            "descripcion": "La cuenta de destino seleccionada no es válida.",
            "icon": "warning"
        })

    cuenta = cuenta_destino_pago.objects.filter(
        id_cuenta_destino=id_cuenta
    ).first()

    if not cuenta:
        return JsonResponse({
            "estado": "fallo",
            "title": "Cuenta no encontrada",
            "descripcion": "La cuenta de destino que intenta modificar no existe.",
            "icon": "warning"
        })

    try:
        with transaction.atomic():
            cuenta.activo = not cuenta.activo
            cuenta.save(update_fields=["activo"])

        return JsonResponse({
            "estado": "exito",
            "title": "Estado actualizado",
            "descripcion": (
                "La cuenta de destino se activó correctamente."
                if cuenta.activo
                else "La cuenta de destino se desactivó correctamente."
            ),
            "icon": "success",
            "activo": cuenta.activo
        })

    except IntegrityError:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error al actualizar",
            "descripcion": "No fue posible modificar el estado de la cuenta de destino.",
            "icon": "warning"
        })