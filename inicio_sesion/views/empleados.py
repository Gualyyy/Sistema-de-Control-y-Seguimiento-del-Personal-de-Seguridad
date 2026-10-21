from django.db.models import Q
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.hashers import check_password, make_password
from django.views.decorators.cache import never_cache
from inicio_sesion.views.autenticacion import crear_token_panel

from inicio_sesion.models import usuarios, credenciales, contacto, nacimiento, residencia, turnos_laborales, bitacora
from inicio_sesion.models import personal_limpieza, supervisores_encargados, despachadores, vigilantes

import os
from django.conf import settings
from datetime import datetime

from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Spacer,
    KeepTogether
)

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter

# GESTIÓN DE EMPLEADOS Y USUARIOS ENCARGADO ADMINISTRATIVO

# VALIDACIÓN DE CAMPOS CRÍTICOS

def validar_nombre_usuario(request):
    if request.method == "POST":
        nombre_usuario = request.POST.get("nombre_usuario", "").strip()
        id_usuario = request.POST.get("id_usuario", "").strip()

        consulta = credenciales.objects.filter(nombre_usuario=nombre_usuario)

        # Si es actualización, excluir las credenciales del usuario actual
        if id_usuario:
            consulta = consulta.exclude(id_usuario=id_usuario)

        existe = consulta.exists()

        return JsonResponse({
            "existe": existe
        })

    return JsonResponse({
        "existe": False
    })

def validar_contrasenia(request):
    if request.method == "POST":
        contrasenia = request.POST.get("clave", "")
        id_usuario = request.POST.get("id_usuario", "").strip()

        cuentas = credenciales.objects.only("id_credenciales", "clave", "id_usuario")

        if id_usuario:
            cuentas = cuentas.exclude(id_usuario=id_usuario)

        existe = any(
            check_password(contrasenia, cuenta.clave)
            for cuenta in cuentas

        )

        return JsonResponse({
            "existe": existe
        })

    return JsonResponse({
        "existe": False
    })
    
def validar_ci(request):
    if request.method == "POST":
        nacionalidad = request.POST.get("nacionalidad", "").strip()
        cedula = request.POST.get("cedula", "").strip()
        id_usuario = request.POST.get("id_usuario", "").strip()

        cedula_completa = f"{nacionalidad}-{cedula}"

        consulta = usuarios.objects.filter(
            cedula_identidad=cedula_completa
        )

        # Solo excluir al usuario cuando se está actualizando
        if id_usuario:
            consulta = consulta.exclude(
                id_usuario=id_usuario
            )

        existe = consulta.exists()

        return JsonResponse({
            "existe": existe
        })

    return JsonResponse({
        "existe": False
    })

def validar_email(request):
    if request.method == "POST":
        correo = request.POST.get("correo", "").strip().lower()
        dominio = request.POST.get("dominio", "").strip().lower()
        id_usuario = request.POST.get("id_usuario", "").strip()

        email = f"{correo}{dominio}"

        consulta = contacto.objects.filter(
            Q(correo_principal__iexact=email) |
            Q(correo_secundario__iexact=email)
        )

        if id_usuario:
            contacto_usuario = contacto.objects.filter(
                id_usuario=id_usuario
            ).first()

            if contacto_usuario:
                mismo_usuario = (
                    contacto_usuario.correo_principal.lower() == email or
                    contacto_usuario.correo_secundario.lower() == email
                )

                if mismo_usuario:
                    return JsonResponse({
                        "existe": True
                    })

            consulta = consulta.exclude(
                id_usuario=id_usuario
            )

        existe = consulta.exists()

        return JsonResponse({
            "existe": existe
        })

    return JsonResponse({
        "existe": False
    })

def validar_telefono(request):
    if request.method == "POST":
        prefijo = request.POST.get("prefijo", "").strip()
        numeros = request.POST.get("numeros", "").strip()
        id_usuario = request.POST.get("id_usuario", "").strip()

        telefono = f"{prefijo}-{numeros}"

        consulta = contacto.objects.filter(
            Q(telefono_principal__iexact=telefono) |
            Q(telefono_secundario__iexact=telefono)
        )

        if id_usuario:
            contacto_usuario = contacto.objects.filter(id_usuario=id_usuario).first()

            if contacto_usuario:
                mismo_usuario = (
                    contacto_usuario.telefono_principal == telefono or
                    contacto_usuario.telefono_secundario == telefono
                )

                if mismo_usuario:
                    return JsonResponse({ "existe": True })

            consulta = consulta.exclude(id_usuario=id_usuario)

        existe = consulta.exists()

        return JsonResponse({
            "existe": existe
        })

    return JsonResponse({
        "existe": False
    })

# SUPERVISORES ENCARGADOS

def supervisores_registrados(request):
    supervisores = []

    registros = supervisores_encargados.objects.filter(
        vigencia=True
    ).select_related(
        "id_usuario",
        "id_turno",
        "id_usuario__credenciales"
    )

    for supervisor in registros:

        credenciales = getattr(
            supervisor.id_usuario,
            "credenciales",
            None
        )

        supervisores.append({
            "id_usuario": supervisor.id_usuario.id_usuario,
            "id_supervisor": supervisor.id_supervisor,
            "cedula": supervisor.id_usuario.cedula_identidad,
            "nombres": supervisor.id_usuario.nombres,
            "apellidos": supervisor.id_usuario.apellidos,
            "genero": supervisor.id_usuario.genero,
            "estado_civil": supervisor.id_usuario.estado_civil,
            "turno": (
                supervisor.id_turno.nombre
                if supervisor.id_turno
                else "Sin turno asignado"
            ),
            "vigencia": supervisor.vigencia,

            "tiene_credenciales": credenciales is not None,
            "bloqueado": (
                credenciales.bloqueado
                if credenciales
                else False
            )
        })

    if not supervisores:
        return JsonResponse({
            "estado": "vacio",
            "supervisores": []
        })

    return JsonResponse({
        "estado": "exito",
        "supervisores": supervisores
    })

def credenciales_supervisor(request):
    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "descripcion": "Método de solicitud no permitido.",
            "tipo_mensaje": "error"
        })

    id_usuario = request.POST.get("id_usuario")
    nombre_usuario = request.POST.get("nombre_usuario", "").strip()
    contrasenia = request.POST.get("contrasenia", "")

    if not id_usuario:
        return JsonResponse({
            "estado": "fallo",
            "descripcion": "Selecciona un supervisor registrado.",
            "tipo_mensaje": "advertencia"
        })

    if not nombre_usuario:
        return JsonResponse({
            "estado": "fallo",
            "descripcion": "Ingresa el nombre de usuario.",
            "tipo_mensaje": "advertencia"
        })

    if not contrasenia:
        return JsonResponse({
            "estado": "fallo",
            "descripcion": "Ingresa la contraseña.",
            "tipo_mensaje": "advertencia"
        })

    try:
        usuario = usuarios.objects.get(id_usuario=id_usuario)
    except usuarios.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "descripcion": "El supervisor no se encuentra registrado.",
            "tipo_mensaje": "error"
        })

    if hasattr(usuario, "credenciales"):
        return JsonResponse({
            "estado": "fallo",
            "descripcion": "Este supervisor ya tiene credenciales registradas.",
            "tipo_mensaje": "advertencia"
        })

    if credenciales.objects.filter(nombre_usuario=nombre_usuario).exists():
        return JsonResponse({
            "estado": "fallo",
            "descripcion": "El nombre de usuario ya está registrado. Elige otro.",
            "tipo_mensaje": "advertencia"
        })

    credenciales.objects.create(
        nombre_usuario=nombre_usuario,
        clave=make_password(contrasenia),
        id_usuario=usuario
    )

    return JsonResponse({
        "estado": "exito",
        "descripcion": "Las credenciales se registraron correctamente.",
        "tipo_mensaje": "exito"
    })

def actualizar_credenciales_supervisor(request):
    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "descripcion": "Método de solicitud no permitido.",
            "tipo_mensaje": "error"
        })

    id_usuario = request.POST.get("id_usuario")
    nombre_usuario = request.POST.get("nombre_usuario", "").strip()
    contrasenia = request.POST.get("contrasenia", "")

    if not id_usuario:
        return JsonResponse({
            "estado": "fallo",
            "descripcion": "Selecciona un supervisor registrado.",
            "tipo_mensaje": "advertencia"
        })

    if not nombre_usuario:
        return JsonResponse({
            "estado": "fallo",
            "descripcion": "Ingresa el nombre de usuario.",
            "tipo_mensaje": "advertencia"
        })

    if not contrasenia:
        return JsonResponse({
            "estado": "fallo",
            "descripcion": "Ingresa la contraseña.",
            "tipo_mensaje": "advertencia"
        })
    try:
        usuario = usuarios.objects.get(id_usuario=id_usuario)
    except usuarios.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "descripcion": "El supervisor no se encuentra registrado o está inactivo.",
            "tipo_mensaje": "error"
        })
    
    try:
        credenciales_supervisor = credenciales.objects.get(
            id_usuario=usuario
        )
    except credenciales.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "descripcion": "Este supervisor todavía no tiene credenciales registradas.",
            "tipo_mensaje": "advertencia"
        })

    if credenciales.objects.filter(
        nombre_usuario=nombre_usuario
    ).exclude(
        id_usuario=usuario
    ).exists():
        return JsonResponse({
            "estado": "fallo",
            "descripcion": "El nombre de usuario ya está registrado. Elige otro.",
            "tipo_mensaje": "advertencia"
        })

    credenciales_supervisor.nombre_usuario = nombre_usuario
    credenciales_supervisor.clave = make_password(contrasenia)
    credenciales_supervisor.save()

    return JsonResponse({
        "estado": "exito",
        "descripcion": "Las credenciales se actualizaron correctamente.",
        "tipo_mensaje": "exito"
    })

def bloquear_supervisor(request):
    id_usuario = request.POST.get("id_usuario", "").strip()
    estado = request.POST.get("bloqueado", "").strip()

    if not id_usuario:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "descripcion": "No se recibió el usuario del supervisor.",
            "icon": "error"
        })

    # OBTENER USUARIO DEL SUPERVISOR
    try:
        usuario = usuarios.objects.get(id_usuario=id_usuario)
    except usuarios.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "descripcion": "El supervisor no se encuentra registrado.",
            "icon": "error"
        })

    # OBTENER CREDENCIALES
    try:
        credencial = credenciales.objects.get(id_usuario=usuario)
    except credenciales.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sin credenciales",
            "descripcion": "Este supervisor no tiene credenciales registradas.",
            "icon": "warning"
        })

    # CAMBIAR ESTADO
    credencial.bloqueado = estado == "true"
    credencial.save()

    # USUARIO QUE REALIZA LA ACCIÓN
    try:
        usuario_accion = usuarios.objects.get(cedula_identidad=request.session.get("cedula_identidad"))
    except usuarios.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "descripcion": "No se pudo identificar al usuario que realiza la acción.",
            "icon": "error"
        })

    # REGISTRAR EN BITÁCORA
    if credencial.bloqueado:
        accion = (
            f"Se bloqueó al supervisor "
            f"{usuario.nombres} {usuario.apellidos}."
        )
    else:
        accion = (
            f"Se desbloqueó al supervisor "
            f"{usuario.nombres} {usuario.apellidos}."
        )

    bitacora.objects.create(
        id_usuario=usuario_accion,
        accion=accion
    )

    return JsonResponse({
        "estado": "exito",
        "title": "Éxito",
        "descripcion": (
            "El supervisor ha sido bloqueado."
            if credencial.bloqueado
            else
            "El supervisor ha sido desbloqueado."
        ),
        "icon": "success"
    })

def supervisores_generales(request):
    return render(request, "Modulos/Supervisor Encargado/gestionar_supervisores.html")

# COMPLETAR REGISTRO EMPLEADOS Y ADMINISTRADOR

def buscar_datos_pre_registrado(request):
    cedula_identidad = request.session.get("cedula_identidad")
    if not cedula_identidad:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "descripcion": "No existe una cédula registrada en la sesión.",
            "icon": "error"
        })

    try:
        usuario = usuarios.objects.get(cedula_identidad=cedula_identidad)
    except usuarios.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "descripcion": "No existe una cédula registrada en la sesión.",
            "icon": "error"
        })

    try:
        info_contacto = contacto.objects.get(id_usuario=usuario)

        telefono = info_contacto.telefono_principal
        correo_electronico = info_contacto.correo_principal
    except contacto.DoesNotExist:
        telefono = None
        correo_electronico = None

    return JsonResponse({
        "estado": "exito",
        "usuario": {
            "nombre": usuario.nombres,
            "apellido": usuario.apellidos,
            "cedula_identidad": usuario.cedula_identidad,
            "genero": usuario.genero,
            "estado_civil": usuario.estado_civil
        },
        "contacto": {
            "telefono_principal": telefono,
            "correo_principal": correo_electronico,
        }
    })

@never_cache
def completar_registro(request):
    if not request.session.get("usuario"):
        if request.method == "POST":
            return JsonResponse({
                "estado": "fallo",
                "title": "Sesión expirada",
                "descripcion": "Inicie sesión para continuar.",
                "icon": "warning"
            }, status=401)

        return redirect("inicio_sesion")

    if request.method == "POST":
        prefijo_principal = request.POST.get("prefijo_principal")
        numero_principal = request.POST.get("numero_principal")

        correo_principal = request.POST.get("correo_principal")
        dominio_principal = request.POST.get("dominio_principal")

        correo_secundaria = request.POST.get("correo_secundaria")
        dominio_secundaria = request.POST.get("dominio_secundaria")
        
        pais_nacimiento = request.POST.get("pais_nacimiento")
        
        estado_nacimiento = request.POST.get("estado_nacimiento")
        estado_nacimiento_nvzla = request.POST.get("estado_nacimiento_nvzla")
        
        municipio_nacimiento = request.POST.get("municipio_nacimiento")
        municipio_nacimiento_nvzla = request.POST.get("municipio_nacimiento_nvzla")
        
        parroquia_nacimiento = request.POST.get("parroquia_nacimiento")
        parroquia_nacimiento_nvzla = request.POST.get("parroquia_nacimiento_nvzla")
        
        direccion_nacimiento = request.POST.get("direccion_nacimiento")
        fecha_nacimiento = request.POST.get("fecha_nacimiento")
        
        condicion_residencia = request.POST.get("condicion_residencia")
        municipio_residencia = request.POST.get("municipio_residencia")
        parroquia_residencia = request.POST.get("parroquia_residencia")
        direccion_residencia = request.POST.get("direccion_residencia")

        if (estado_nacimiento and municipio_nacimiento and parroquia_nacimiento):
            estado = estado_nacimiento
            municipio = municipio_nacimiento
            parroquia = parroquia_nacimiento
        else:
            estado = estado_nacimiento_nvzla
            municipio = municipio_nacimiento_nvzla
            parroquia = parroquia_nacimiento_nvzla

        campos = [
            (pais_nacimiento, "País de Nacimiento", "Por favor, seleccione su país de nacimiento."),
            
            (direccion_nacimiento, "Dirección de Nacimiento", "Por favor, ingrese su dirección de nacimiento."),
            (fecha_nacimiento, "Fecha de Nacimiento", "Por favor, ingrese su fecha de nacimiento."),
            (condicion_residencia, "Condición de Residencia", "Por favor, seleccione su condición de residencia."),
            (municipio_residencia, "Municipio de Residencia", "Por favor, seleccione su municipio de residenica."),
            (parroquia_residencia, "Parroquia de Residencia", "Por favor, seleccione su parroquia de residencia."),
            (direccion_residencia, "Dirección de Residencia", "Por favor, ingrese su dirección de residencia."),
        ]

        for valor, campo, mensaje in campos:
            if not valor:
                return JsonResponse({
                    "title": campo,
                    "descripcion": mensaje,
                    "icon": "warning"
                })

        prefijo_secundaria = request.POST.get("prefijo_secundaria")
        numero_secundaria = request.POST.get("numero_secundaria")

        # TELÉFONO SECUNDARIO
        if not prefijo_secundaria and not numero_secundaria:
            telefono_secundario = "N/A"

        elif not prefijo_secundaria:
            return JsonResponse({
                "title": "Prefijo vacío",
                "descripcion": "Por favor, selecciona el prefijo telefónico.",
                "icon": "warning"
            })

        elif not numero_secundaria:
            return JsonResponse({
                "title": "Número vacío",
                "descripcion": "Por favor, ingresa el número telefónico.",
                "icon": "warning"
            })

        else:
            telefono_secundario = prefijo_secundaria + "-" + numero_secundaria

        # CORREO ELECTRONICO (ALTERNATIVO)
        if not dominio_secundaria and not correo_secundaria:
            correo_secundario = "N/A"

        elif not dominio_secundaria:
            return JsonResponse({
                "title": "Prefijo vacío",
                "descripcion": "Por favor, selecciona el dominio del Correo Electronico.",
                "icon": "warning"
            })

        elif not correo_secundaria:
            return JsonResponse({
                "title": "Número vacío",
                "descripcion": "Por favor, ingresa el nombre del Correo Electronico.",
                "icon": "warning"
            })

        else:
            correo_secundario = correo_secundaria + dominio_secundaria

        try:
            with transaction.atomic():
                usuario = usuarios.objects.get(cedula_identidad= request.session.get("cedula_identidad"))
                
                info_contacto, creado = contacto.objects.get_or_create(id_usuario=usuario)
        
                if not info_contacto.telefono_principal:
                    info_contacto.telefono_principal = (prefijo_principal + "-" + numero_principal)
        
                if not info_contacto.correo_principal:
                    info_contacto.correo_principal = (correo_principal + dominio_principal)
        
                info_contacto.telefono_secundario = telefono_secundario
                info_contacto.correo_secundario = correo_secundario
                info_contacto.save()
        
                nacimiento.objects.create(pais=pais_nacimiento, estado=estado, municipio=municipio, parroquia=parroquia, direccion=direccion_nacimiento, fecha_nacimiento=fecha_nacimiento, id_usuario=usuario)
        
                residencia.objects.create(condicion_residencia=condicion_residencia, municipio=municipio_residencia, parroquia=parroquia_residencia, direccion=direccion_residencia, id_usuario=usuario)
        
                info_usuario = usuarios.objects.get(cedula_identidad=request.session.get("cedula_identidad"))
                accion = f"Completar el registro del empleado {info_usuario.nombres} {info_usuario.apellidos} {info_usuario.cedula_identidad}"
        
                bitacora.objects.create(
                    id_usuario=info_usuario,
                    accion=accion
                )
        
                token = crear_token_panel()
                request.session["panel_token"] = token
                request.session["completar_registro"] = True
                request.session.save()
        
                return JsonResponse({
                    "estado": "exito",
                    "title": "Exito",
                    "descripcion": "Se registro exitosamente el empelado.",
                    "icon": "success",
                    "url": reverse("panel_usuario_token", kwargs={"token": token})
                })
        except Exception:
            return JsonResponse({
                "estado": "fallo",
                "title": "Error",
                "descripcion": "Ocurrio un error al momento de completar el registro.",
                "icon": "error"
            })

    return render(request, "inicio_sesion/completar_datos_usuario.html")

# REGISTRO EMPLEADOS POR PARTE DEL ADMINISTRADOR

def turnos_registrados(request):
    turnos_lista = turnos_laborales.objects.all()

    datos = [
        {
            "id_turno": turno.id_turno,
            "nombre": turno.nombre
        }
        for turno in turnos_lista
    ]

    return JsonResponse(datos, safe=False)

def perfiles_disponibles(request):
    if request.method == "POST":
        id_turno = request.POST.get("turno")

        if not id_turno:
            return JsonResponse({
                "estado": "fallo",
                "perfiles": []
            })

        perfiles = []

        # Supervisor Encargado
        supervisor_existe = supervisores_encargados.objects.filter(
            id_turno=id_turno,
            vigencia=True
        ).exists()

        if not supervisor_existe:
            perfiles.append({
                "perfil": "Supervisor Encargado"
            })

        # Personal de Limpieza
        limpieza_existe = personal_limpieza.objects.filter(
            id_turno=id_turno,
            vigencia=True
        ).exists()

        if not limpieza_existe:
            perfiles.append({
                "perfil": "Personal de Limpieza"
            })

        # Despachador
        despachador_existe = despachadores.objects.filter(
            id_turno=id_turno,
            vigencia=True
        ).exists()

        if not despachador_existe:
            perfiles.append({
                "perfil": "Despachador"
            })

        # Vigilante
        vigilante_existe = vigilantes.objects.filter(
            id_turno=id_turno,
            vigencia=True
        ).exists()

        if not vigilante_existe:
            perfiles.append({
                "perfil": "Vigilante"
            })

        return JsonResponse({
            "estado": "exito",
            "perfiles": perfiles
        })

def registro_usuarios(request):
    if request.method == "POST":
        nombres = request.POST.get("nombres")
        apellidos = request.POST.get("apellidos")
        nacionalidad = request.POST.get("nacionalidad")
        cedula = request.POST.get("cedula_identidad")
        genero = request.POST.get("genero")
        estado_civil = request.POST.get("estado_civil")

        prefijo_principal = request.POST.get("prefijo_principal")
        numero_principal = request.POST.get("numero_principal")
        prefijo_secundaria = request.POST.get("prefijo_secundaria")
        numero_secundaria = request.POST.get("numero_secundaria")

        correo_principal = request.POST.get("correo_principal")
        dominio_principal = request.POST.get("dominio_principal")
        correo_secundaria = request.POST.get("correo_secundaria")
        dominio_secundaria = request.POST.get("dominio_secundaria")

        pais_nacimiento = request.POST.get("pais_nacimiento")

        if pais_nacimiento == "Venezuela":
            estado = request.POST.get("estado_nacimiento")
            municipio = request.POST.get("municipio_nacimiento")
            parroquia = request.POST.get("parroquia_nacimiento")
        else:
            estado = request.POST.get("estado_novzla")
            municipio = request.POST.get("municipio_nacimiento_nvzla")
            parroquia = request.POST.get("parroquia_novzla")

        direccion_nacimiento = request.POST.get("direccion_nacimiento")
        fecha_nacimiento = request.POST.get("fecha_nacimiento")
        
        condicion_residencia = request.POST.get("condicion_residencia")
        municipio_residencia = request.POST.get("municipio_residencia")
        parroquia_residencia = request.POST.get("parroquia_residencia")
        direccion_residencia = request.POST.get("direccion_residencia")

        turno = request.POST.get("turno_laboral")

        perfil = request.POST.get("perfil")

        campos = [
            # DATOS PERSONALES
            (nombres, "nombre", "Por favor, ingrese su nombre."),
            (apellidos, "apellidos", "Por favor, ingrese sus apellidos."),
            (nacionalidad, "nacionalidad", "Por favor, ingrese su nacionalidad."),
            (cedula, "cédula de identidad", "Por favor, ingrese su cédula de identidad."),
            (genero, "género", "Por favor, ingrese su género."),
            (estado_civil, "estado civil", "Por favor, ingrese su estado civil."),

            # TELÉFONO PRINCIPAL
            (prefijo_principal, "prefijo principal", "Por favor, seleccione un prefijo telefónico."),
            (numero_principal, "número principal", "Por favor, ingrese el número telefónico principal."),

            # CORREO PRINCIPAL
            (correo_principal, "correo principal", "Por favor, ingrese el correo electrónico principal."),
            (dominio_principal, "dominio principal", "Por favor, seleccione el dominio del correo electrónico principal."),

            # NACIMIENTO
            (pais_nacimiento, "país de nacimiento", "Por favor, seleccione el país de nacimiento."),
            (estado, "estado de nacimiento", "Por favor, seleccione el estado de nacimiento."),
            (municipio, "municipio de nacimiento", "Por favor, seleccione el municipio de nacimiento."),
            (parroquia, "parroquia de nacimiento", "Por favor, seleccione la parroquia de nacimiento."),
            (direccion_nacimiento, "dirección de nacimiento", "Por favor, ingrese la dirección de nacimiento."),
            (fecha_nacimiento, "fecha de nacimiento", "Por favor, ingrese la fecha de nacimiento."),

            # RESIDENCIA
            (condicion_residencia, "condición de residencia", "Por favor, seleccione la condición de residencia."),
            (municipio_residencia, "municipio de residencia", "Por favor, seleccione el municipio de residencia."),
            (parroquia_residencia, "parroquia de residencia", "Por favor, selecciona la parroquia de residencia."),
            (direccion_residencia, "dirección de residencia", "Por favor, ingrese la dirección de residencia."),

            # DATOS LABORALES
            (turno, "turno","Por favor, seleccione un turno."),

            # PERFILES
            (perfil, "perfil", "Por favor, seleccione un perfil laboral."),
        ]

        for valor, campo, mensaje in campos:
            if not valor:
                return JsonResponse({
                    "estado": "fallo",
                    "title": campo,
                    "descripcion": mensaje,
                    "icon": "warning"
                })

        if not dominio_secundaria and not correo_secundaria:
            correo_alternativo = "N/A"

        elif not dominio_secundaria:
            return JsonResponse({
                "title": "Prefijo vacío",
                "descripcion": "Por favor, selecciona el dominio del Correo Electronico.",
                "icon": "warning"
            })
        elif not correo_secundaria:
            return JsonResponse({
                "title": "Número vacío",
                "descripcion": "Por favor, ingresa el nombre del Correo Electronico.",
                "icon": "warning"
            })
        else:
            correo_alternativo = correo_secundaria + dominio_secundaria

        if not prefijo_secundaria and not numero_secundaria:
            telefono_secundario = "N/A"

        elif not prefijo_secundaria:
            return JsonResponse({
                "estado": "fallo",
                "title": "Prefijo vacío",
                "descripcion": "Por favor, selecciona el prefijo telefónico.",
                "icon": "warning"
            })
        elif not numero_secundaria:
            return JsonResponse({
                "estado": "fallo",
                "title": "Número vacío",
                "descripcion": "Por favor, ingresa el número telefónico.",
                "icon": "warning"
            })
        else:
            telefono_secundario = prefijo_secundaria + "-" + numero_secundaria

        cedula_identidad = nacionalidad + "-" + cedula

        telefono_princiapl = prefijo_principal + "-" + numero_principal

        correo_electronico = correo_principal + dominio_principal

        print(perfil)

        try:
            with transaction.atomic():
                turno_obj = turnos_laborales.objects.get(id_turno=turno)

                # CREAR USUARIO
                usuario = usuarios.objects.create(
                    nombres=nombres,
                    apellidos=apellidos,
                    cedula_identidad=cedula_identidad,
                    genero=genero,
                    estado_civil=estado_civil
                )

                contacto.objects.create(
                    telefono_principal=telefono_princiapl,
                    telefono_secundario=telefono_secundario,
                    correo_principal=correo_electronico,
                    correo_secundario=correo_alternativo,
                    id_usuario=usuario
                )

                nacimiento.objects.create(
                    pais=pais_nacimiento,
                    estado=estado,
                    municipio=municipio,
                    parroquia=parroquia,
                    direccion=direccion_nacimiento,
                    fecha_nacimiento=fecha_nacimiento,
                    id_usuario=usuario
                )

                residencia.objects.create(
                    condicion_residencia=condicion_residencia,
                    municipio=municipio_residencia,
                    parroquia=parroquia_residencia,
                    direccion=direccion_residencia,
                    id_usuario=usuario
                )

                if perfil == "Supervisor Encargado":
                    supervisores_encargados.objects.create(
                        id_usuario=usuario,
                        id_turno=turno_obj,
                        vigencia=True
                    )

                elif perfil == "Personal de Limpieza":
                    personal_limpieza.objects.create(
                        id_usuario=usuario,
                        id_turno=turno_obj,
                        vigencia=True
                    )

                elif perfil == "Despachador":
                    despachadores.objects.create(
                        id_usuario=usuario,
                        id_turno=turno_obj,
                        vigencia=True
                    )

                elif perfil == "Vigilante":
                    vigilantes.objects.create(
                        id_usuario=usuario,
                        id_turno=turno_obj,
                        vigencia=True
                    )

            # BITÁCORA
            info_usuario = usuarios.objects.get(
                cedula_identidad=request.session.get(
                    "cedula_identidad"
                )
            )

            accion = (
                f"Registró un nuevo usuario "
                f"{nombres} {apellidos} {cedula_identidad}"
            )

            bitacora.objects.create(
                id_usuario=info_usuario,
                accion=accion
            )

            return JsonResponse({
                "estado": "exito",
                "title": "Éxito",
                "descripcion": (
                    "Se registraron los datos del empleado "
                    "exitosamente."
                ),
                "icon": "success"
            })

        except Exception as e:
            return JsonResponse({
                "estado": "fallo",
                "title": "Error",
                "descripcion": f"Ocurrio un error: {e}.",
                "icon": "error"
            })

    return render(request, "Modulos/Empleados/Administrador/registro_empleados.html")

# ACTUALIZAR DATOS DEL EMPLEADO EL ADMINISTRADOR

def buscar_datos_usuario(request):
    if request.method == "POST":
        nacionalidad = request.POST.get("nacionalidad")
        cedula = request.POST.get("cedula")

        if not nacionalidad:
            return JsonResponse({
                "estado": "fallo",
                "title": "Vacío",
                "descripcion": "Por favor, seleccione la nacionalidad.",
                "icon": "warning"
            })

        if not cedula:
            return JsonResponse({
                "estado": "fallo",
                "title": "Vacío",
                "descripcion": "Por favor, ingrese su número de cédula.",
                "icon": "warning"
            })

        cedula_identidad = f"{nacionalidad}-{cedula}"

        try:
            usuario = usuarios.objects.select_related(
                "credenciales",
                "supervisor__id_turno",
                "personal_limpieza__id_turno",
                "despachador__id_turno",
                "vigilante__id_turno"
            ).get(
                cedula_identidad=cedula_identidad
            )

            try:
                info_nacimiento = nacimiento.objects.get(
                    id_usuario=usuario
                )
            except nacimiento.DoesNotExist:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Registro incompleto",
                    "descripcion": "El usuario todavía no ha completado sus datos personales. Debe esperar a que complete su registro.",
                    "icon": "warning"
                })

            info_contacto = contacto.objects.get(
                id_usuario=usuario
            )

            info_residencia = residencia.objects.get(
                id_usuario=usuario
            )

            # PERFIL LABORAL Y TURNO
            perfil_laboral = "N/A"
            turno_laboral = "N/A"

            if hasattr(usuario, "supervisor") and usuario.supervisor.vigencia:
                perfil_laboral = "Supervisor Encargado"
                turno_laboral = str(usuario.supervisor.id_turno)

            elif hasattr(usuario, "personal_limpieza") and usuario.personal_limpieza.vigencia:
                perfil_laboral = "Personal de Limpieza"
                turno_laboral = str(usuario.personal_limpieza.id_turno)

            elif hasattr(usuario, "despachador") and usuario.despachador.vigencia:
                perfil_laboral = "Despachador"
                turno_laboral = str(usuario.despachador.id_turno)

            elif hasattr(usuario, "vigilante") and usuario.vigilante.vigencia:
                perfil_laboral = "Vigilante"
                turno_laboral = str(usuario.vigilante.id_turno)

            return JsonResponse({
                "estado": "exito",

                "usuario": {
                    "id": usuario.id_usuario,
                    "nombres": usuario.nombres,
                    "apellidos": usuario.apellidos,
                    "cedula_identidad": usuario.cedula_identidad,
                    "genero": usuario.genero,
                    "estado_civil": usuario.estado_civil,
                },

                "laboral": {
                    "perfil": perfil_laboral,
                    "turno": turno_laboral,
                },

                "contacto": {
                    "telefono_principal": info_contacto.telefono_principal,
                    "telefono_secundario": info_contacto.telefono_secundario,
                    "correo_principal": info_contacto.correo_principal,
                    "correo_secundario": info_contacto.correo_secundario,
                },

                "nacimiento": {
                    "pais": info_nacimiento.pais,
                    "estado": info_nacimiento.estado,
                    "municipio": info_nacimiento.municipio,
                    "parroquia": info_nacimiento.parroquia,
                    "direccion": info_nacimiento.direccion,
                    "fecha_nacimiento": info_nacimiento.fecha_nacimiento,
                },

                "residencia": {
                    "condicion_residencia": info_residencia.condicion_residencia,
                    "municipio": info_residencia.municipio,
                    "parroquia": info_residencia.parroquia,
                    "direccion": info_residencia.direccion,
                },
            })

        except usuarios.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "title": "No encontrado",
                "descripcion": "No existe un usuario con esa cédula.",
                "icon": "error"
            })

        except Exception as e:
            return JsonResponse({
                "estado": "fallo",
                "title": "Error",
                "descripcion": str(e),
                "icon": "error"
            })

def actualizacion_datos_usuarios(request):
    if request.method == "POST":
        usuario_id = request.POST.get("usuario_id")
        nombre_usuario = request.POST.get("nombre_usuario")
        apellido_usuario = request.POST.get("apellido_usuario")
        nacionalidad_usuario = request.POST.get("nacionalidad_usuario")
        cedula_usuario = request.POST.get("cedula_usuario")
        genero_usuario = request.POST.get("genero_usuario")
        estado_civil_usuario = request.POST.get("estado_civil_usuario")

        prefijo_principal = request.POST.get("prefijo_principal")
        numero_principal = request.POST.get("numero_principal")
        prefijo_secundaria = request.POST.get("prefijo_secundaria")
        numero_secundaria = request.POST.get("numero_secundaria")
        
        correo_principal = request.POST.get("email_principal")
        dominio_principal = request.POST.get("dominio_principal")
        correo_secundaria = request.POST.get("email_secundaria")
        dominio_secundaria = request.POST.get("dominio_secundaria")
        
        actualizar_pais_nacimiento = request.POST.get("actualizar_pais_nacimiento")
        
        actualizar_estado_nacimiento = request.POST.get("actualizar_estado_nacimiento")
        actualizar_estado_nacimiento_nvzla = request.POST.get("actualizar_estado_nacimiento_nvzla")
        
        actualizar_municipio_nacimiento = request.POST.get("actualizar_municipio_nacimiento")
        actualizar_municipio_nacimiento_nvzla = request.POST.get("actualizar_municipio_nacimiento_nvzla")
        
        actualizar_parroquia_nacimiento = request.POST.get("actualizar_parroquia_nacimiento")
        actualizar_parroquia_nacimiento_nvzla = request.POST.get("actualizar_parroquia_nacimiento_nvzla")
        
        actualizar_direccion_nacimiento = request.POST.get("actualizar_direccion_nacimiento")
        actualizar_fecha_nacimiento = request.POST.get("actualizar_fecha_nacimiento")
        
        actualizar_condicion_residencia = request.POST.get("actualizar_condicion_residencia")
        actualizar_municipio_residencia = request.POST.get("actualizar_municipio_residencia")
        actualizar_parroquia_residencia = request.POST.get("actualizar_parroquia_residencia")
        actualizar_direccion_residencia = request.POST.get("actualizar_direccion_residencia")

        campos = [
            (nombre_usuario, "Nombre", "Por favor, ingrese el nombre del empleado."),
            (apellido_usuario, "Apellido", "Por favor, ingrese el apellido del empleado."),
            (nacionalidad_usuario, "Nacionalidad", "Por favor, seleccione la nacionalidad."),
            (cedula_usuario, "Cédula", "Por favor, ingrese la cédula de identidad."),
            (genero_usuario, "Género", "Por favor, seleccione el género."),
            (estado_civil_usuario, "Estado Civil", "Por favor, seleccione el estado civil."),

            (prefijo_principal, "Prefijo Principal", "Por favor, seleccione el prefijo del teléfono principal."),
            (numero_principal, "Teléfono Principal", "Por favor, ingrese el número del teléfono principal."),
            
            (correo_principal, "Correo Principal", "Por favor, ingrese el usuario del correo principal."),
            (dominio_principal, "Dominio Principal", "Por favor, seleccione el dominio del correo principal."),
            
            (actualizar_direccion_nacimiento, "Dirección de Nacimiento", "Por favor, ingrese la dirección de nacimiento."),
            (actualizar_fecha_nacimiento, "Fecha de Nacimiento", "Por favor, seleccione la fecha de nacimiento."),

            (actualizar_condicion_residencia, "Condición de Residencia", "Por favor, seleccione la condición de residencia."),
            (actualizar_municipio_residencia, "Municipio de Residencia", "Por favor, seleccione el municipio de residencia."),
            (actualizar_parroquia_residencia, "Parroquia de Residencia", "Por favor, seleccione la parroquia de residencia."),
            (actualizar_direccion_residencia, "Dirección de Residencia", "Por favor, ingrese la dirección de residencia.")
        ]

        for valor, campo, mensaje in campos:
            if not valor:
                return JsonResponse({
                    "estado": "fallo",
                    "title": campo,
                    "descripcion": mensaje,
                    "icon": "warning"
                })

        if not prefijo_secundaria and not numero_secundaria:
            telefono_secundario = "N/A"

        elif prefijo_secundaria and not numero_secundaria:
            return JsonResponse({
                "estado": "fallo",
                "title": "Vacío",
                "descripcion": "Debe ingresar el número telefónico secundario.",
                "icon": "warning"
            })

        elif not prefijo_secundaria and numero_secundaria:
            return JsonResponse({
                "estado": "fallo",
                "title": "Vacío",
                "descripcion": "Debe seleccionar el prefijo telefónico secundario.",
                "icon": "warning"
            })

        elif prefijo_secundaria and numero_secundaria:
            telefono_secundario = prefijo_secundaria + "-" + numero_secundaria


        if not dominio_secundaria and not correo_secundaria:
            correo_secundario = "N/A"

        elif not dominio_secundaria:
            return JsonResponse({
                "title": "Prefijo vacío",
                "descripcion": "Por favor, selecciona el dominio del Correo Electronico.",
                "icon": "warning"
            })

        elif not correo_secundaria:
            return JsonResponse({
                "title": "Número vacío",
                "descripcion": "Por favor, ingresa el nombre del Correo Electronico.",
                "icon": "warning"
            })

        else:
            correo_secundario = correo_secundaria+dominio_secundaria

        if actualizar_pais_nacimiento == "Venezuela":
            estado = actualizar_estado_nacimiento
            municipio = actualizar_municipio_nacimiento
            parroquia = actualizar_parroquia_nacimiento
        else:
            estado = actualizar_estado_nacimiento_nvzla
            municipio = actualizar_municipio_nacimiento_nvzla
            parroquia = actualizar_parroquia_nacimiento_nvzla

        cedula_identidad = nacionalidad_usuario + "-" + cedula_usuario
        telefono_principal = prefijo_principal + "-" + numero_principal
        correo_principal = correo_principal + dominio_principal

        try:
            with transaction.atomic():
                usuario = usuarios.objects.get(id_usuario=usuario_id)
                info_contacto = contacto.objects.get(id_usuario=usuario)

                if cedula_identidad != usuario.cedula_identidad:
                    if usuarios.objects.filter(cedula_identidad=cedula_identidad).exclude(id_usuario=usuario_id).exists():

                        return JsonResponse({
                            "estado": "fallo",
                            "title": "Cédula existente",
                            "descripcion": "Ya existe otro usuario con esa cédula.",
                            "icon": "warning"
                        })

                if telefono_principal != info_contacto.telefono_principal:
                    if contacto.objects.filter(telefono_principal=telefono_principal).exclude(id_usuario=usuario_id).exists():
                        return JsonResponse({
                            "estado": "fallo",
                            "title": "Teléfono Principal existente",
                            "descripcion": "Ya existe otro usuario con ese número telefónico.",
                            "icon": "warning"
                        })

                if correo_principal != info_contacto.correo_principal:
                    if contacto.objects.filter(correo_principal=correo_principal).exclude(id_usuario=usuario_id).exists():
                        return JsonResponse({
                            "estado": "fallo",
                            "title": "Correo existente",
                            "descripcion": "Ya existe otro usuario con ese correo.",
                            "icon": "warning"
                        })

                if correo_secundario != info_contacto.correo_secundario:
                    if contacto.objects.filter(correo_secundario=correo_secundario).exclude(id_usuario=usuario_id).exists():
                        return JsonResponse({
                            "estado": "fallo",
                            "title": "Correo existente",
                            "descripcion": "Ya existe otro usuario con ese correo.",
                            "icon": "warning"
                        })

                # ACTUALIZAR DATOS DEL USUARIO
                usuario.nombres = nombre_usuario
                usuario.apellidos = apellido_usuario
                usuario.cedula_identidad = cedula_identidad
                usuario.genero = genero_usuario
                usuario.estado_civil = estado_civil_usuario
                usuario.save()

                # ACTUALIZAR CONTACTO
                info_contacto.telefono_principal = telefono_principal
                info_contacto.telefono_secundario = telefono_secundario
                info_contacto.correo_principal = correo_principal
                info_contacto.correo_secundario = correo_secundario
                info_contacto.save()

                # ACTUALIZAR NACIMIENTO
                info_nacimiento = nacimiento.objects.get(id_usuario=usuario)
                info_nacimiento.pais = actualizar_pais_nacimiento
                info_nacimiento.estado = estado
                info_nacimiento.municipio = municipio
                info_nacimiento.parroquia = parroquia
                info_nacimiento.direccion = actualizar_direccion_nacimiento
                info_nacimiento.fecha_nacimiento = actualizar_fecha_nacimiento
                info_nacimiento.save()

                # ACTUALIZAR RESIDENCIA
                info_residencia = residencia.objects.get(id_usuario=usuario)

                info_residencia.condicion_residencia = (
                    actualizar_condicion_residencia
                )
                info_residencia.municipio = (
                    actualizar_municipio_residencia
                )
                info_residencia.parroquia = (
                    actualizar_parroquia_residencia
                )
                info_residencia.direccion = (
                    actualizar_direccion_residencia
                )
                info_residencia.save()

                # USUARIO QUE REALIZA LA ACCIÓN
                info_usuario = usuarios.objects.get(
                    cedula_identidad=request.session.get(
                        "cedula_identidad"
                    )
                )

                accion = (
                    f"Actualización del registro "
                    f"{nombre_usuario} "
                    f"{apellido_usuario} "
                    f"{cedula_identidad}"
                )

                bitacora.objects.create(
                    id_usuario=info_usuario,
                    accion=accion
                )

                return JsonResponse({
                    "estado": "exito",
                    "title": "Éxito",
                    "descripcion": "Se registró exitosamente el empleado.",
                    "icon": "success"
                })
        except Exception:
            return JsonResponse({
                "estado": "fallo",
                "title": "Error",
                "descripcion": "Ocrrio al momento de actualizar los datos de empleado.",
                "icon": "error"
            })

    return render(request, "Modulos/Empleados/Administrador/actualizar_datos_empleado.html")

# VISUALIZAR EN LA TABLA LOS EMPLEADOS REGISTRADOS

def visualizacion_datos_usuarios(request):
    if request.method == "POST":
        nacionalidad = request.POST.get("nacionalidad", "").strip()
        cedula = request.POST.get("cedula", "").strip()
        perfil = request.POST.get("perfil", "").strip()

        datos = []

        # SUPERVISORES ENCARGADOS
        if not perfil or perfil == "Supervisor Encargado":
            supervisores = (
                supervisores_encargados.objects
                .select_related("id_usuario", "id_turno")
                .filter(vigencia=True)
            )

            for empleado in supervisores:
                usuario = empleado.id_usuario

                if nacionalidad and cedula:
                    if usuario.cedula_identidad != f"{nacionalidad}-{cedula}":
                        continue

                datos.append({
                    "id": usuario.id_usuario,
                    "nombres": usuario.nombres,
                    "apellidos": usuario.apellidos,
                    "cedula": usuario.cedula_identidad,
                    "genero": usuario.genero,
                    "estado_civil": usuario.estado_civil,
                    "perfil": "Supervisor Encargado",
                    "turno": empleado.id_turno.nombre
                })

        # PERSONAL DE LIMPIEZA
        if not perfil or perfil == "Personal de Limpieza":
            empleados = (
                personal_limpieza.objects
                .select_related("id_usuario", "id_turno")
                .filter(vigencia=True)
            )

            for empleado in empleados:
                usuario = empleado.id_usuario

                if nacionalidad and cedula:
                    if usuario.cedula_identidad != f"{nacionalidad}-{cedula}":
                        continue

                datos.append({
                    "id": usuario.id_usuario,
                    "nombres": usuario.nombres,
                    "apellidos": usuario.apellidos,
                    "cedula": usuario.cedula_identidad,
                    "genero": usuario.genero,
                    "estado_civil": usuario.estado_civil,
                    "perfil": "Personal de Limpieza",
                    "turno": empleado.id_turno.nombre
                })

        # DESPACHADORES
        if not perfil or perfil == "Despachador":
            empleados = (
                despachadores.objects
                .select_related("id_usuario", "id_turno")
                .filter(vigencia=True)
            )

            for empleado in empleados:

                usuario = empleado.id_usuario

                if nacionalidad and cedula:
                    if usuario.cedula_identidad != f"{nacionalidad}-{cedula}":
                        continue

                datos.append({
                    "id": usuario.id_usuario,
                    "nombres": usuario.nombres,
                    "apellidos": usuario.apellidos,
                    "cedula": usuario.cedula_identidad,
                    "genero": usuario.genero,
                    "estado_civil": usuario.estado_civil,
                    "perfil": "Despachador",
                    "turno": empleado.id_turno.nombre
                })

        # VIGILANTES
        if not perfil or perfil == "Vigilante":
            empleados = (
                vigilantes.objects
                .select_related("id_usuario", "id_turno")
                .filter(vigencia=True)
            )

            for empleado in empleados:

                usuario = empleado.id_usuario

                if nacionalidad and cedula:
                    if usuario.cedula_identidad != f"{nacionalidad}-{cedula}":
                        continue

                datos.append({
                    "id": usuario.id_usuario,
                    "nombres": usuario.nombres,
                    "apellidos": usuario.apellidos,
                    "cedula": usuario.cedula_identidad,
                    "genero": usuario.genero,
                    "estado_civil": usuario.estado_civil,
                    "perfil": "Vigilante",
                    "turno": empleado.id_turno.nombre
                })

        return JsonResponse(datos, safe=False)

    return JsonResponse([], safe=False)

def visualizar_empleados(request):
    return render(request, "Modulos/Empleados/Administrador/visualizar_empleados.html")

# REPORTE DE TODOS LOS EMPLEADOS REGISTRADOS

def lista_empleados_pdf(request):
    perfil_empleado = request.POST.get("perfil", "").strip()

    datos = []
    modelos_perfiles = (
        ("Supervisor Encargado", supervisores_encargados),
        ("Personal de Limpieza", personal_limpieza),
        ("Despachador", despachadores),
        ("Vigilante", vigilantes),
    )

    for nombre_perfil, modelo_perfil in modelos_perfiles:
        if perfil_empleado and perfil_empleado != nombre_perfil:
            continue

        empleados = (
            modelo_perfil.objects
            .filter(vigencia=True)
            .select_related("id_usuario")
        )

        for empleado in empleados:
            usuario = empleado.id_usuario
            datos.append({
                "nombres": usuario.nombres,
                "apellidos": usuario.apellidos,
                "cedula": usuario.cedula_identidad,
                "perfil": nombre_perfil,
                "turno": (
                    "Turno Completo"
                    if nombre_perfil == "Encargado Administrativo"
                    else empleado.id_turno.nombre
                )
            })

    # RESPUESTA PDF
    response = HttpResponse(content_type="application/pdf")

    response["Content-Disposition"] = ('inline; filename="lista_empleados.pdf"')

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

    # DATOS TABLA
    datos_tabla = [
        # ENCABEZADO PRINCIPAL
        ["LISTA DE EMPLEADOS", "", "", "", "", ""],

        # ENCABEZADO DE COLUMNAS
        ["N.º", "Nombres", "Apellidos", "C.I", "Perfil", "Turno Laboral"],
    ]

    # NÚMERO DE REGISTRO DINÁMICO
    for numero, dato in enumerate(datos, start=1):
        datos_tabla.append([
            numero,
            dato["nombres"],
            dato["apellidos"],
            dato["cedula"],
            dato["perfil"],
            dato["turno"]
        ])

    # TABLA
    tabla = Table(
        datos_tabla,
        colWidths=[35, 85, 85, 70, 125, 120],
        repeatRows=2
    )
    
    tabla.setStyle(TableStyle([
        # ENCABEZADO PRINCIPAL

        # UNIR LAS 6 COLUMNAS
        ("SPAN", (0, 0), (-1, 0)),

        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#00445F")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 14),

        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),

        # ENCABEZADO DE COLUMNAS
        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#00445F")),
        ("TEXTCOLOR", (0, 1), (-1, 1), colors.white),
        ("FONTNAME", (0, 1), (-1, 1), "Times-Bold"),
        ("FONTSIZE", (0, 1), (-1, 1), 10),

        ("ALIGN", (0, 1), (-1, 1), "CENTER"),
        ("VALIGN", (0, 1), (-1, 1), "MIDDLE"),

        # CONTENIDO
        ("FONTNAME", (0, 2), (-1, -1), "Times-Roman"),
        ("FONTSIZE", (0, 2), (-1, -1), 10),

        ("TEXTCOLOR", (0, 2), (-1, -1), colors.black),

        ("ALIGN", (0, 2), (-1, -1), "CENTER"),
        ("VALIGN", (0, 2), (-1, -1), "MIDDLE"),

        # BORDES
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),

        # ESPACIADO
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))

    # ELEMENTOS
    elementos = [
        tabla
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

# REPORTE DE TODOS LOS DATOS DEL EMEPLEADO SELECCIONADO

def datos_empleados_pdf(request):
    # OBTENER ID DEL USUARIO
    id_usuario = request.POST.get("id_usuario", "").strip()

    # BUSCAR USUARIO
    usuario = usuarios.objects.get(id_usuario=id_usuario)

    # INFORMACIÓN DE CONTACTO
    try:
        info_contacto = contacto.objects.get(id_usuario=usuario)
    except contacto.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "descripcion": "El empleado no tiene información de contacto registrada.",
            "icon": "error"
        })

    # INFORMACIÓN DE NACIMIENTO
    try:
        info_nacimiento = nacimiento.objects.get(id_usuario=usuario)
    except nacimiento.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "descripcion": "El empleado no tiene información de nacimiento registrada.",
            "icon": "error"
        })

    # INFORMACIÓN DE RESIDENCIA
    try:
        info_residencia = residencia.objects.get(id_usuario=usuario)
    except residencia.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "descripcion": "El empleado no tiene información de residencia registrada.",
            "icon": "error"
        })

    # RESPUESTA PDF
    response = HttpResponse(content_type="application/pdf")

    response["Content-Disposition"] = (f'inline; filename="empleado_{usuario.id_usuario}.pdf"')

    # DOCUMENTO
    documento = SimpleDocTemplate(
        response,
        pagesize=letter,
        rightMargin=30,
        leftMargin=30,
        topMargin=130,
        bottomMargin=30
    )

    # ESTILOS
    estilos = getSampleStyleSheet()

    estilo_titulo = estilos["Heading2"]
    estilo_titulo.fontName = "Times-Bold"
    estilo_titulo.fontSize = 14
    estilo_titulo.alignment = TA_CENTER
    estilo_titulo.textColor = colors.black
    estilo_titulo.leading = 18

    def crear_tabla(titulo, datos):
        datos_tabla = [
            [titulo, ""]
        ]

        datos_tabla.extend(datos)

        tabla = Table(
            datos_tabla,
            colWidths=[110, 380],
            splitByRow=1
        )

        tabla.setStyle(TableStyle([

            # ENCABEZADO
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#00445F")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 13),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),

            # UNIR LAS DOS COLUMNAS DEL ENCABEZADO
            ("SPAN", (0, 0), (-1, 0)),

            # CAMPOS
            ("BACKGROUND", (0, 1), (0, -1), colors.HexColor("#00445F")),
            ("TEXTCOLOR", (0, 1), (0, -1), colors.white),
            ("FONTNAME", (0, 1), (0, -1), "Times-Bold"),
            ("FONTSIZE", (0, 1), (0, -1), 10),

            # VALORES
            ("FONTNAME", (1, 1), (1, -1), "Times-Roman"),
            ("TEXTCOLOR", (1, 1), (1, -1), colors.black),
            ("FONTSIZE", (1, 1), (1, -1), 11),

            # GENERAL
            ("ALIGN", (0, 1), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))

        return tabla

    # DATOS BÁSICOS
    datos_basicos = [
        ["Nombres:", usuario.nombres],
        ["Apellidos:", usuario.apellidos],
        ["Cédula de Identidad:", usuario.cedula_identidad],
        ["Género:", usuario.genero],
        ["Estado civil:", usuario.estado_civil],
    ]

    # CONTACTO
    datos_contacto = [
        ["Teléfono Principal:", info_contacto.telefono_principal],
        ["Teléfono Secundario:", info_contacto.telefono_secundario],
        ["Correo Principal:", info_contacto.correo_principal],
        ["Correo Secundario:", info_contacto.correo_secundario],
    ]

    # NACIMIENTO
    datos_nacimiento = [
        ["País:", info_nacimiento.pais],
        ["Estado:", info_nacimiento.estado],
        ["Municipio:", info_nacimiento.municipio],
        ["Parroquia:", info_nacimiento.parroquia],
        ["Dirección:", info_nacimiento.direccion],
        ["Fecha:", info_nacimiento.fecha_nacimiento],
    ]

    # RESIDENCIA
    datos_residencia = [
        ["Condición:", info_residencia.condicion_residencia],
        ["Municipio:", info_residencia.municipio],
        ["Parroquia:", info_residencia.parroquia],
        ["Dirección:", info_residencia.direccion],
    ]

    # CREAR TABLAS
    tabla_basicos = crear_tabla(
        "DATOS BÁSICOS",
        datos_basicos
    )

    tabla_contacto = crear_tabla(
        "CONTACTO",
        datos_contacto
    )

    tabla_nacimiento = crear_tabla(
        "DATOS DE NACIMIENTO",
        datos_nacimiento
    )

    tabla_residencia = crear_tabla(
        "DATOS DE RESIDENCIA",
        datos_residencia
    )

    # ELEMENTOS DEL PDF
    elementos = []

    elementos.append(
        KeepTogether([
            tabla_basicos,
            Spacer(1, 15)
        ])
    )

    elementos.append(
        KeepTogether([
            tabla_contacto,
            Spacer(1, 15)
        ])
    )

    elementos.append(
        KeepTogether([
            tabla_nacimiento,
            Spacer(1, 15)
        ])
    )

    elementos.append(
        KeepTogether([
            tabla_residencia
        ])
    )

    # LOGO
    ruta_logo = os.path.join(
        settings.BASE_DIR,
        "static",
        "Imagenes",
        "logo_hielo_caipe.png"
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
