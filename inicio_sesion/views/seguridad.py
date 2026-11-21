from django.shortcuts import render
from django.http import JsonResponse
from inicio_sesion.models import bitacora, sesiones_usuario, intentos_inicio_sesion
from django.db.models.functions import TruncDate

# BITACORA DE ACCIÓN

def visualizar_bitacora(request):
    return render(request, "Modulos/Seguridad/visualizar_bitacora.html")

def bitacora_registradas(request):
    cedula = request.POST.get("cedula", "").strip()
    nacionalidad = request.POST.get("nacionalidad", "").strip()

    if cedula in ("undefined", "null"):
        cedula = ""

    if nacionalidad in ("undefined", "null"):
        nacionalidad = ""

    registros = (
        bitacora.objects
        .select_related("id_usuario")
        .order_by("-fecha_hora")
    )

    if cedula:
        if nacionalidad:
            cedula_identidad = f"{nacionalidad}-{cedula}"
            registros = registros.filter(
                id_usuario__cedula_identidad=cedula_identidad
            )

    datos = []

    for registro in registros:
        datos.append({
            "id": registro.id_bitacora,
            "usuario": (
                f"{registro.id_usuario.nombres} "
                f"{registro.id_usuario.apellidos}"
            ),
            "cedula": registro.id_usuario.cedula_identidad,
            "fecha": registro.fecha_hora.strftime("%d/%m/%Y %H:%M:%S"),
            "cargo_usuario": registro.cargo_usuario,
            "nombre_modulo": registro.nombre_modulo,
            "accion": registro.accion,
        })

    return JsonResponse(datos, safe=False)
    
#  INICIOS DE SESIÓN Y REPORTE

def visualizar_inicio_sesion(request):
    return render(request, "Modulos/Seguridad/visualizar_inicios_sesiones.html")

def fechas_inicios_sesiones(request):
    registros = (
        sesiones_usuario.objects
        .values_list("fecha_inicio", flat=True)
        .order_by("-fecha_inicio")
    )

    fechas = []

    for fecha in registros:
        fecha = fecha.date()

        if fecha not in fechas:
            fechas.append(fecha)

    return JsonResponse({
        "estado": "exito",
        "fechas": [
            fecha.strftime("%Y-%m-%d")
            for fecha in fechas
        ]
    })

def inicios_sesiones_registradas(request):
    fecha = request.POST.get("fecha", "").strip()

    registros = (
        sesiones_usuario.objects
        .select_related("usuario")
        .order_by("-fecha_inicio")
    )

    if fecha:
        registros = registros.filter(fecha_inicio__date=fecha)

    datos = []
    for registro in registros:
        user_agent = registro.info_general or ""

        if "OPR/" in user_agent:
            navegador = "Opera"
        elif "Edg/" in user_agent:
            navegador = "Microsoft Edge"
        elif "Chrome/" in user_agent:
            navegador = "Google Chrome"
        elif "Firefox/" in user_agent:
            navegador = "Mozilla Firefox"
        elif "Safari/" in user_agent:
            navegador = "Safari"
        else:
            navegador = "Desconocido"

        datos.append({
            "id": registro.id_sesion,
            "usuario": (
                registro.usuario.nombres + " " +
                registro.usuario.apellidos
            ),
            "cedula_identidad": registro.usuario.cedula_identidad,
            "fecha_inicio": registro.fecha_inicio.strftime(
                "%d/%m/%Y %H:%M:%S"
            ),
            "fecha_fin": (
                registro.fecha_fin.strftime("%d/%m/%Y %H:%M:%S")
                if registro.fecha_fin
                else "Sesión activa"
            ),
            "activa": registro.activa,
            "navegador": navegador,
            "direccion_ip": registro.direccion_ip,
        })

    return JsonResponse(datos, safe=False)
 
# INTENTO INICIÓN DE SESIÓN

def visualizar_intentos_sesion(request):
    return render(request, "Modulos/Seguridad/visualizar_intentos_sesion.html")

def fechas_intentos_registrados(request):
    fechas = (
        intentos_inicio_sesion.objects
        .annotate(fecha=TruncDate("fecha_hora"))
        .values_list("fecha", flat=True)
        .distinct()
        .order_by("-fecha")
    )

    return JsonResponse({
        "estado": "exito",
        "fechas": list(fechas)
    })

def intentos_registrados(request):
    fecha = request.POST.get("fecha")

    intentos = intentos_inicio_sesion.objects.select_related("usuario").order_by("-fecha_hora")

    if fecha:
        intentos = intentos.filter(fecha_hora__date=fecha)

    datos = []
    for intento in intentos:
        datos.append({
            "id_intento": intento.id_intento,
            "usuario": (
                f"{intento.usuario.nombres} "
                f"{intento.usuario.apellidos}"
                if intento.usuario
                else "Usuario no registrado"
            ),
            "nombre_usuario": (
                intento.nombre_usuario
                if intento.nombre_usuario
                else "Usuario no registrado"
            ),
            "direccion_ip": intento.direccion_ip,
            "exitoso": intento.exitoso,
            "fecha_hora": intento.fecha_hora.strftime(
                "%d/%m/%Y %H:%M:%S"
            )
        })

    return JsonResponse({
        "estado": "exito",
        "intentos": datos
    })
