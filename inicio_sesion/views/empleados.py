from django.db.models import Q
from django.db import transaction, IntegrityError
from django.shortcuts import redirect, render
from django.urls import reverse
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.hashers import check_password
from django.views.decorators.cache import never_cache
from inicio_sesion.views.autenticacion import crear_token_panel

from inicio_sesion.models import usuarios, credenciales, contacto, nacimiento, residencia, turnos_laborales, bitacora
from inicio_sesion.models import personal_limpieza, supervisores_encargados, despachadores, vigilantes, propietarios, atencion_cliente, encargados_administrativos

# GESTIÓN DE EMPLEADOS Y USUARIOS ENCARGADO ADMINISTRATIVO

# VALIDACIÓN DE CAMPOS CRÍTICOS

def validar_nombre_usuario(request):
    nombre_usuario = request.POST.get("nombre_usuario", "").strip()
    id_usuario = request.POST.get("id_usuario", "").strip()

    consulta = credenciales.objects.filter(
        nombre_usuario__iexact=nombre_usuario
    )

    if id_usuario:
        consulta = consulta.exclude(id_usuario=id_usuario)

    existe = consulta.exists()

    return JsonResponse({
        "existe": existe,
    })

def validar_contrasenia(request):
    contrasenia = request.POST.get("clave", "")
    id_usuario = request.POST.get("id_usuario", "").strip()

    if not contrasenia:
        return JsonResponse({"existe": False})

    cuentas = credenciales.objects.only(
        "id_credenciales",
        "clave",
        "id_usuario"
    )

    if id_usuario:
        cuentas = cuentas.exclude(id_usuario=id_usuario)

    existe = any(
        check_password(contrasenia, cuenta.clave)
        for cuenta in cuentas.iterator()
    )

    return JsonResponse({"existe": existe})
    
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

        if not correo or not dominio:
            return JsonResponse({
                "existe": False
            })

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
                    (contacto_usuario.correo_principal or "").strip().lower() == email
                    or
                    (contacto_usuario.correo_secundario or "").strip().lower() == email
                )

                if mismo_usuario:
                    return JsonResponse({
                        "existe": False
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
            contacto_usuario = contacto.objects.filter(
                id_usuario=id_usuario
            ).first()

            if contacto_usuario:
                mismo_usuario = (
                    (contacto_usuario.telefono_principal or "").casefold() == telefono.casefold()
                    or
                    (contacto_usuario.telefono_secundario or "").casefold() == telefono.casefold()
                )

                if mismo_usuario:
                    return JsonResponse({"existe": False})

            consulta = consulta.exclude(id_usuario=id_usuario)

        existe = consulta.exists()

        return JsonResponse({
            "existe": existe
        })

    return JsonResponse({
        "existe": False
    })

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
        genero = request.POST.get("genero")
        estado_civil = request.POST.get("estado_civil")

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
        if not numero_secundaria:
            telefono_secundario = "N/A"
        else:
            telefono_secundario = prefijo_secundaria + "-" + numero_secundaria

        # CORREO ELECTRÓNICO (ALTERNATIVO)
        if not correo_secundaria:
            correo_secundario = "N/A"
        else:
            correo_secundario = correo_secundaria + dominio_secundaria

        try:
            with transaction.atomic():
                usuario = usuarios.objects.get(cedula_identidad=request.session.get("cedula_identidad"))

                genero_actual = (usuario.genero or "").strip()
                estado_civil_actual = (usuario.estado_civil or "").strip()

                if not genero_actual or genero_actual.upper() == "N/A":
                    if not genero or genero.strip().upper() == "N/A":
                        return JsonResponse({
                            "estado": "fallo",
                            "title": "Género requerido",
                            "descripcion": "Por favor, seleccione su género para continuar.",
                            "icon": "warning"
                        })

                    usuario.genero = genero.strip()

                if not estado_civil_actual or estado_civil_actual.upper() == "N/A":
                    if not estado_civil or estado_civil.strip().upper() == "N/A":
                        return JsonResponse({
                            "estado": "fallo",
                            "title": "Estado civil requerido",
                            "descripcion": "Por favor, seleccione su estado civil para continuar.",
                            "icon": "warning"
                        })

                    usuario.estado_civil = estado_civil.strip()

                usuario.save()

                info_contacto, creado = contacto.objects.get_or_create(id_usuario=usuario)
        
                if not info_contacto.telefono_principal:
                    info_contacto.telefono_principal = (prefijo_principal + "-" + numero_principal)
        
                if not info_contacto.correo_principal:
                    info_contacto.correo_principal = (correo_principal + dominio_principal)
        
                info_contacto.telefono_secundario = telefono_secundario
                info_contacto.correo_secundario = correo_secundario
                info_contacto.save()
        
                info_nacimiento, creado = nacimiento.objects.get_or_create(id_usuario=usuario)

                info_nacimiento.pais=pais_nacimiento,
                info_nacimiento.estado=estado
                info_nacimiento.municipio=municipio
                info_nacimiento.parroquia=parroquia
                info_nacimiento.direccion=direccion_nacimiento
                info_nacimiento.fecha_nacimiento=fecha_nacimiento
                info_nacimiento.save()
                
                info_residencia, creado = residencia.objects.get_or_create(id_usuario=usuario)

                info_residencia.condicion_residencia=condicion_residencia 
                info_residencia.municipio=municipio_residencia
                info_residencia.parroquia=parroquia_residencia 
                info_residencia.direccion=direccion_residencia
                info_residencia.save()
        
                info_usuario = usuarios.objects.get(cedula_identidad=request.session.get("cedula_identidad"))
                accion = f"Completar el registro del empleado {info_usuario.nombres} {info_usuario.apellidos} {info_usuario.cedula_identidad}"
        
                bitacora.objects.create(
                    id_usuario=info_usuario,
                    nombre_modulo="Completar registro de empleado",
                    cargo_usuario=request.session.get("perfil", "No especificado"),
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
        except Exception as e:
            return JsonResponse({
                "estado": "fallo",
                "title": "Error",
                "descripcion": f"Ocurrio un error al momento de completar el registro {e}.",
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

def perfiles_sin_turno_registrados(request):

    encargado_existe = encargados_administrativos.objects.filter(
        vigencia=True
    ).exists()

    atencion_existe = atencion_cliente.objects.filter(
        vigencia=True
    ).exists()

    return JsonResponse({
        "estado": "exito",
        "encargado_administrativo_registrado": encargado_existe,
        "atencion_cliente_registrada": atencion_existe
    })

def perfiles_disponibles_registro(request):
    id_turno = request.POST.get("turno")

    if not id_turno:
        return JsonResponse({
            "estado": "fallo",
            "descripcion": "Debe seleccionar un turno laboral."
        })

    try:
        turno = turnos_laborales.objects.get(id_turno=id_turno)

    except (turnos_laborales.DoesNotExist, ValueError, TypeError):
        return JsonResponse({
            "estado": "fallo",
            "descripcion": "El turno laboral seleccionado no es válido."
        })

    supervisor_existe = supervisores_encargados.objects.filter(
        id_turno=turno,
        vigencia=True
    ).exists()

    return JsonResponse({
        "estado": "exito",
        "supervisor_encargado_registrado": supervisor_existe
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
        
        turno = request.POST.get("turno_laboral")
        perfil = request.POST.get("perfil")

        campos = [
            (nombres, "nombre", "Por favor, ingrese su nombre."),
            (apellidos, "apellidos", "Por favor, ingrese sus apellidos."),
            (nacionalidad, "nacionalidad", "Por favor, ingrese su nacionalidad."),
            (cedula, "cédula de identidad", "Por favor, ingrese su cédula de identidad."),
            (genero, "género", "Por favor, ingrese su género."),
            (estado_civil, "estado civil", "Por favor, ingrese su estado civil."),

            (prefijo_principal, "prefijo principal", "Por favor, seleccione un prefijo telefónico."),
            (numero_principal, "número principal", "Por favor, ingrese el número telefónico principal."),

            (correo_principal, "correo principal", "Por favor, ingrese el correo electrónico principal."),
            (dominio_principal, "dominio principal", "Por favor, seleccione el dominio del correo electrónico principal."),

            (turno, "turno", "Por favor, seleccione un turno."),
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

        perfiles_validos = {
            "encargado_administrativo",
            "atencion_cliente",
            "supervisor_encargado",
            "despachador",
            "vigilante",
            "personal_limpieza",
        }

        if perfil not in perfiles_validos:
            return JsonResponse({
                "estado": "fallo",
                "title": "Perfil inválido",
                "descripcion": "El perfil seleccionado no es válido.",
                "icon": "warning"
            })

        perfiles_sin_turno = {
            "encargado_administrativo",
            "atencion_cliente",
        }

        perfiles_datos_completos = {
            "despachador",
            "vigilante",
            "personal_limpieza",
        }

        requiere_datos_adicionales = perfil in perfiles_datos_completos

        if not correo_secundaria:
            correo_alternativo = "N/A"
        else:
            correo_alternativo = correo_secundaria + dominio_secundaria

        if not numero_secundaria:
            telefono_secundario = "N/A"
        else:
            telefono_secundario = (
                prefijo_secundaria + "-" + numero_secundaria
            )

        cedula_identidad = nacionalidad + "-" + cedula
        telefono_principal = prefijo_principal + "-" + numero_principal
        correo_electronico = correo_principal + dominio_principal
        razon_social = nombres + " " + apellidos
        tipo_usuario = "NATURAL"

        # DATOS DE NACIMIENTO Y RESIDENCIA
        if requiere_datos_adicionales:

            pais_nacimiento = request.POST.get("pais_nacimiento")

            if pais_nacimiento != "Venezuela":
                estado_nacimiento = request.POST.get("estado_nacimiento_nvzla")
                municipio_nacimiento = request.POST.get("parroquia_nacimiento_nvzla")
                parroquia_nacimiento = request.POST.get("parroquia_nacimiento_nvzla")
            else:
                estado_nacimiento = request.POST.get("estado_nacimiento")
                municipio_nacimiento = request.POST.get("municipio_nacimiento")
                parroquia_nacimiento = request.POST.get("parroquia_nacimiento")

            direccion_nacimiento = request.POST.get("direccion_nacimiento")
            fecha_nacimiento = request.POST.get("fecha_nacimiento")

            condicion_residencia = request.POST.get("condicion_residencia")
            municipio_residencia = request.POST.get("municipio_residencia")
            parroquia_residencia = request.POST.get("parroquia_residencia")
            direccion_residencia = request.POST.get("direccion_residencia")

        else:
            pais_nacimiento = "N/A"
            estado_nacimiento = "N/A"
            municipio_nacimiento = "N/A"
            parroquia_nacimiento = "N/A"
            direccion_nacimiento = "N/A"
            fecha_nacimiento = "N/A"

            condicion_residencia = "N/A"
            municipio_residencia = "N/A"
            parroquia_residencia = "N/A"
            direccion_residencia = "N/A"

        if requiere_datos_adicionales:

            campos_adicionales = [
                (pais_nacimiento, "país de nacimiento", "Por favor, seleccione el país de nacimiento."),
                (estado_nacimiento, "estado de nacimiento", "Por favor, seleccione el estado de nacimiento."),
                (municipio_nacimiento, "municipio de nacimiento", "Por favor, seleccione el municipio de nacimiento."),
                (parroquia_nacimiento, "parroquia de nacimiento", "Por favor, seleccione la parroquia de nacimiento."),
                (direccion_nacimiento, "dirección de nacimiento", "Por favor, ingrese la dirección de nacimiento."),
                (fecha_nacimiento, "fecha de nacimiento", "Por favor, ingrese la fecha de nacimiento."),
                (condicion_residencia, "condición de residencia", "Por favor, seleccione la condición de residencia."),
                (municipio_residencia, "municipio de residencia", "Por favor, seleccione el municipio de residencia."),
                (parroquia_residencia, "parroquia de residencia", "Por favor, seleccione la parroquia de residencia."),
                (direccion_residencia, "dirección de residencia", "Por favor, ingrese la dirección de residencia."),
            ]

            for valor, campo, mensaje in campos_adicionales:
                if not valor:
                    return JsonResponse({
                        "estado": "fallo",
                        "title": campo,
                        "descripcion": mensaje,
                        "icon": "warning"
                    })
            
        try:
            with transaction.atomic():
                if perfil in perfiles_sin_turno:
                    if turno != "Turno Completo":
                        return JsonResponse({
                            "estado": "fallo",
                            "title": "Turno inválido",
                            "descripcion": (
                                "El perfil seleccionado no tiene un turno laboral."
                            ),
                            "icon": "warning"
                        })
                    turno_obj = None
                elif turno == "Turno Completo":
                    return JsonResponse({
                        "estado": "fallo",
                        "title": "Turno inválido",
                        "descripcion": (
                            "El perfil seleccionado requiere un turno laboral registrado."
                        ),
                        "icon": "warning"
                    })
                else:
                    try:
                        turno_obj = turnos_laborales.objects.get(id_turno=turno)
                    except (turnos_laborales.DoesNotExist, ValueError, TypeError):
                        return JsonResponse({
                            "estado": "fallo",
                            "title": "Turno inválido",
                            "descripcion": "El turno seleccionado no es válido.",
                            "icon": "warning"
                        })

                # Comprobar cédula duplicada.
                if usuarios.objects.filter(
                    cedula_identidad=cedula_identidad
                ).exists():
                    return JsonResponse({
                        "estado": "fallo",
                        "title": "Cédula registrada",
                        "descripcion": "Ya existe un usuario con esa cédula de identidad.",
                        "icon": "warning"
                    })

                # Validar los perfiles con límite de asignación.
                if (perfil == "propietarios" and propietarios.objects.exists()):
                    return JsonResponse({
                        "estado": "fallo",
                        "title": "Propietario no disponible",
                        "descripcion": "Ya existe un Propietario registrado.",
                        "icon": "warning"
                    })

                if request.session.get("perfil") == "Encargado Administrativo":
                    if (perfil == "encargado_administrativo"
                        and encargados_administrativos.objects.filter(
                            vigencia=True
                        ).exists()):
                        return JsonResponse({
                            "estado": "fallo",
                            "title": "Encargado Administrativo no disponible",
                            "descripcion": "Ya existe una asignación vigente de Encargado Administrativo.",
                            "icon": "warning"
                        })
                
                if (perfil == "atencion_cliente"
                    and atencion_cliente.objects.filter(
                        vigencia=True
                    ).exists()):
                    return JsonResponse({
                        "estado": "fallo",
                        "title": "Atención al Cliente no disponible",
                        "descripcion": "Ya existe una asignación vigente de Atención al Cliente.",
                        "icon": "warning"
                    })

                if (perfil == "supervisor_encargado"
                    and supervisores_encargados.objects.filter(
                        id_turno=turno_obj,
                        vigencia=True
                    ).exists()):
                    return JsonResponse({
                        "estado": "fallo",
                        "title": "Supervisor no disponible",
                        "icon": "warning",
                        "descripcion": (
                            f"Ya existe un Supervisor Encargado vigente "
                            f"para el turno {turno_obj.nombre}."
                        )
                    })

                # Crear usuario.
                usuario = usuarios.objects.create(
                    tipo_usuario=tipo_usuario,
                    nombre_razon_social=razon_social,
                    nombres=nombres,
                    apellidos=apellidos,
                    cedula_identidad=cedula_identidad,
                    genero=genero or "N/A",
                    estado_civil=estado_civil or "N/A"
                )

                contacto.objects.create(
                    telefono_principal=telefono_principal,
                    telefono_secundario=telefono_secundario,
                    correo_principal=correo_electronico,
                    correo_secundario=correo_alternativo,
                    id_usuario=usuario
                )

                nacimiento.objects.create(
                    pais=pais_nacimiento,
                    estado=estado_nacimiento,
                    municipio=municipio_nacimiento,
                    parroquia=parroquia_nacimiento,
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

                if perfil == "encargado_administrativo":
                    encargados_administrativos.objects.create(
                        id_usuario=usuario,
                        vigencia=True
                    )
                
                elif perfil == "atencion_cliente":
                    atencion_cliente.objects.create(
                        id_usuario=usuario,
                        vigencia=True
                    )

                elif perfil == "supervisor_encargado":
                    supervisores_encargados.objects.create(
                        id_usuario=usuario,
                        id_turno=turno_obj,
                        vigencia=True
                    )

                elif perfil == "personal_limpieza":
                    personal_limpieza.objects.create(
                        id_usuario=usuario,
                        id_turno=turno_obj,
                        vigencia=True
                    )

                elif perfil == "despachador":
                    despachadores.objects.create(
                        id_usuario=usuario,
                        id_turno=turno_obj,
                        vigencia=True
                    )

                elif perfil == "vigilante":
                    vigilantes.objects.create(
                        id_usuario=usuario,
                        id_turno=turno_obj,
                        vigencia=True
                    )

                # Registrar en bitácora dentro de la transacción.
                cedula_sesion = request.session.get("cedula_identidad")

                if not cedula_sesion:
                    return JsonResponse({
                        "estado": "fallo",
                        "title": "Error de Sesión",
                        "descripcion": "Debe de iniciar sesión.",
                        "icon": "error"
                    })

                info_usuario = usuarios.objects.get(
                    cedula_identidad=cedula_sesion
                )

                accion = (
                    f"Registró un nuevo usuario "
                    f"{nombres} {apellidos} {cedula_identidad}. "
                    f"Perfil asignado: {perfil}. "
                    f"Turno: {turno_obj.nombre if turno_obj else 'Turno Completo'}."
                )

                bitacora.objects.create(
                    id_usuario=info_usuario,
                    nombre_modulo="Registro de empleados",
                    cargo_usuario=request.session.get("perfil", "No especificado"),
                    accion=accion
                )

            return JsonResponse({
                "estado": "exito",
                "title": "Éxito",
                "descripcion": (
                    "Se registraron los datos del empleado "
                    "y se asignó su perfil correctamente."
                ),
                "icon": "success"
            })

        except IntegrityError:
            return JsonResponse({
                "estado": "fallo",
                "title": "Registro duplicado",
                "descripcion": (
                    "No se pudo completar el registro porque "
                    "uno de los datos ya está registrado."
                ),
                "icon": "warning"
            })

        except Exception as e:
            return JsonResponse({
                "estado": "fallo",
                "title": "Error",
                "descripcion": (
                    "Ocurrió un error al registrar el usuario. "
                    "Verifique los datos e intente nuevamente."
                    f"{e}"
                ),
                "icon": "error"
            })

    return render(request, "Modulos/Empleados/Administrador/registro_empleados.html")

# ACTUALIZAR DATOS DEL EMPLEADO EL ADMINISTRADOR

def buscar_datos_usuario(request):
    if request.method == "POST":
        nacionalidad = request.POST.get("nacionalidad", "").strip()
        cedula = request.POST.get("cedula", "").strip()

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

        usuario = usuarios.objects.select_related(
            "credenciales",
            "propietario",
            "atencion_cliente",
            "supervisor__id_turno",
            "personal_limpieza__id_turno",
            "despachador__id_turno",
            "vigilante__id_turno"
        ).get(
            cedula_identidad=cedula_identidad
        )

        # VALIDAR QUE NO SE MODIFIQUEN LOS DATOS PROPIOS
        perfil_sesion = request.session.get("perfil")

        if perfil_sesion in [
            "Propietario",
            "Encargado Administrativo"
        ]:

            usuario_sesion = usuarios.objects.filter(
                cedula_identidad=request.session.get("cedula_identidad")
            ).only("id_usuario").first()

            if not usuario_sesion:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Sesión no válida",
                    "descripcion": "No se pudo identificar al usuario que inició sesión.",
                    "icon": "error"
                })

            if usuario_sesion.id_usuario == usuario.id_usuario:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Acción no permitida",
                    "descripcion": "No puede modificar sus propios datos personales.",
                    "icon": "warning"
                })

        def datos_completos(instancia, campos):
            for campo in campos:
                valor = getattr(instancia, campo, None)

                if valor is None:
                    return False

                if isinstance(valor, str):
                    if not valor.strip() or valor.strip().casefold() == "n/a":
                        return False

            return True

        try:
            usuario = usuarios.objects.select_related(
                "credenciales",
                "propietario",
                "atencion_cliente",
                "supervisor__id_turno",
                "personal_limpieza__id_turno",
                "despachador__id_turno",
                "vigilante__id_turno"
            ).get(
                cedula_identidad=cedula_identidad
            )
        
            # DATOS DE NACIMIENTO
            try:
                info_nacimiento = nacimiento.objects.get(id_usuario=usuario)
            except nacimiento.DoesNotExist:
                info_nacimiento = None

            # DATOS DE CONTACTO
            info_contacto = contacto.objects.get(id_usuario=usuario)

            # DATOS DE RESIDENCIA
            try:
                info_residencia = residencia.objects.get(id_usuario=usuario)
            except residencia.DoesNotExist:
                info_residencia = None

            # ESTADO DE LOS DATOS DE NACIMIENTO
            campos_nacimiento = [
                "pais",
                "estado",
                "municipio",
                "parroquia",
                "direccion",
                "fecha_nacimiento"
            ]

            nacimiento_registrado = (
                info_nacimiento is not None
                and datos_completos(info_nacimiento, campos_nacimiento)
            )


            # ESTADO DE LOS DATOS DE RESIDENCIA
            campos_residencia = [
                "condicion_residencia",
                "municipio",
                "parroquia",
                "direccion"
            ]

            residencia_registrada = (
                info_residencia is not None
                and datos_completos(info_residencia, campos_residencia)
            )

            # PERFIL LABORAL Y TURNO
            perfil_laboral = "N/A"
            turno_laboral = "N/A"

            if hasattr(usuario, "propietario"):
                perfil_laboral = "Propietario"
                turno_laboral = "Turno Completo"

            elif (hasattr(usuario, "atencion_cliente") and usuario.atencion_cliente.vigencia):
                perfil_laboral = "Atención al Cliente"
                turno_laboral = "Turno Completo"

            elif (hasattr(usuario, "supervisor") and usuario.supervisor.vigencia):
                perfil_laboral = "Supervisor Encargado"
                turno_laboral = str(usuario.supervisor.id_turno)

            elif (hasattr(usuario, "personal_limpieza") and usuario.personal_limpieza.vigencia):
                perfil_laboral = "Personal de Limpieza"
                turno_laboral = str(usuario.personal_limpieza.id_turno)

            elif (hasattr(usuario, "despachador") and usuario.despachador.vigencia):
                perfil_laboral = "Despachador"
                turno_laboral = str(usuario.despachador.id_turno)

            elif (hasattr(usuario, "vigilante") and usuario.vigilante.vigencia):
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
                    "pais": info_nacimiento.pais if nacimiento_registrado else "No registrado",
                    "estado": info_nacimiento.estado if nacimiento_registrado else "No registrado",
                    "municipio": info_nacimiento.municipio if nacimiento_registrado else "No registrado",
                    "parroquia": info_nacimiento.parroquia if nacimiento_registrado else "No registrado",
                    "direccion": info_nacimiento.direccion if nacimiento_registrado else "No registrado",
                    "fecha_nacimiento": (
                       str(info_nacimiento.fecha_nacimiento)
                        if nacimiento_registrado else "No registrado"
                    ),
                },
                "residencia": {
                    "condicion_residencia": (
                        info_residencia.condicion_residencia
                        if residencia_registrada else "No registrado"
                    ),
                    "municipio": (
                        info_residencia.municipio
                        if residencia_registrada else "No registrado"
                    ),
                    "parroquia": (
                        info_residencia.parroquia
                        if residencia_registrada else "No registrado"
                    ),
                    "direccion": (
                        info_residencia.direccion
                        if residencia_registrada else "No registrado"
                    ),
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
                "descripcion": (
                    "Ocurrió un error al consultar los datos del empleado."
                    f" Error: {e}"
                ),
                "icon": "error"
            })

def actualizacion_datos_usuarios(request):
    if request.method != "POST":
        return render(request, "Modulos/Empleados/Administrador/actualizar_datos_empleado.html")
    
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
    ]

    for valor, campo, mensaje in campos:
        if not valor or not valor.strip():
            return JsonResponse({
                "estado": "fallo",
                "title": campo,
                "descripcion": mensaje,
                "icon": "warning"
            })
        
    # TELÉFONO SECUNDARIO
    if not numero_secundaria:
        telefono_secundario = "N/A"
    else:
        if not prefijo_secundaria:
            return JsonResponse({
                "estado": "fallo",
                "title": "Prefijo vacío",
                "descripcion": "Debe seleccionar el prefijo telefónico secundario.",
                "icon": "warning"
            })

        telefono_secundario = prefijo_secundaria + "-" + numero_secundaria

    # CORREO SECUNDARIO
    if not correo_secundaria:
        correo_secundario = "N/A"
    else:
        if not dominio_secundaria:
            return JsonResponse({
                "estado": "fallo",
                "title": "Dominio vacío",
                "descripcion": "Por favor, seleccione el dominio del correo electrónico.",
                "icon": "warning"
            })

        correo_secundario = correo_secundaria + dominio_secundaria
        
    def datos_completos(instancia, campos):
        for campo in campos:
            valor = getattr(instancia, campo, None)

            if valor is None:
                return False

            if isinstance(valor, str):
                if not valor.strip() or valor.strip().casefold() == "n/a":
                    return False

        return True

    usuario = usuarios.objects.get(id_usuario=usuario_id)

    # DATOS DE NACIMIENTO
    try:
        info_nacimiento = nacimiento.objects.get(id_usuario=usuario)
    except nacimiento.DoesNotExist:
        info_nacimiento = None

    campos_nacimiento = [
        "pais",
        "estado",
        "municipio",
        "parroquia",
        "direccion",
        "fecha_nacimiento"
    ]

    nacimiento_registrado = (
        info_nacimiento is not None
        and datos_completos(info_nacimiento, campos_nacimiento)
    )

    if nacimiento_registrado:

        campos_obligatorios = [
            (actualizar_pais_nacimiento, "País de Nacimiento", "Por favor, selecciona el país de nacimiento."),
            (actualizar_direccion_nacimiento, "Dirección de Nacimiento", "Por favor, ingresa la dirección de nacimiento."),
            (actualizar_fecha_nacimiento, "Fecha de Nacimiento", "Por favor, selecciona la fecha de nacimiento.")
        ]

        for valor, campo, mensaje in campos_obligatorios:
            if not valor or not valor.strip():
                return JsonResponse({
                    "estado": "fallo",
                    "title": campo,
                    "descripcion": mensaje,
                    "icon": "warning"
                })

        if actualizar_pais_nacimiento == "Venezuela":
            campos_ubicacion = [
                (actualizar_estado_nacimiento, "Estado de Nacimiento", "Por favor, selecciona el estado de nacimiento."),
                (actualizar_municipio_nacimiento, "Municipio de Nacimiento", "Por favor, selecciona el municipio de nacimiento."),
                (actualizar_parroquia_nacimiento, "Parroquia de Nacimiento", "Por favor, selecciona la parroquia de nacimiento.")
            ]

            for valor, campo, mensaje in campos_ubicacion:
                if not valor or not valor.strip():
                    return JsonResponse({
                        "estado": "fallo",
                        "title": campo,
                        "descripcion": mensaje,
                        "icon": "warning"
                    })

            pais = actualizar_pais_nacimiento
            estado = actualizar_estado_nacimiento
            municipio = actualizar_municipio_nacimiento
            parroquia = actualizar_parroquia_nacimiento

        else:
            campos_ubicacion = [
                (actualizar_estado_nacimiento_nvzla, "Estado de Nacimiento", "Por favor, completa el estado de nacimiento."),
                (actualizar_municipio_nacimiento_nvzla, "Municipio de Nacimiento", "Por favor, completa el municipio de nacimiento."),
                (actualizar_parroquia_nacimiento_nvzla, "Parroquia de Nacimiento", "Por favor, completa la parroquia de nacimiento.")
            ]

            for valor, campo, mensaje in campos_ubicacion:
                if not valor or not valor.strip():
                    return JsonResponse({
                        "estado": "fallo",
                        "title": campo,
                        "descripcion": mensaje,
                        "icon": "warning"
                    })

            pais = actualizar_pais_nacimiento
            estado = actualizar_estado_nacimiento_nvzla
            municipio = actualizar_municipio_nacimiento_nvzla
            parroquia = actualizar_parroquia_nacimiento_nvzla

        direccion = actualizar_direccion_nacimiento
        fecha_nacimiento = actualizar_fecha_nacimiento

    # DATOS DE RESIDENCIA
    try:
        info_residencia = residencia.objects.get(id_usuario=usuario)
    except residencia.DoesNotExist:
        info_residencia = None

    campos_residencia = [
        "condicion_residencia",
        "municipio",
        "parroquia",
        "direccion"
    ]

    residencia_registrada = (
        info_residencia is not None
        and datos_completos(info_residencia, campos_residencia)
    )

    if residencia_registrada:

        campos_obligatorios = [
            (actualizar_condicion_residencia, "Condición de Residencia", "Por favor, seleccione la condición de residencia."),
            (actualizar_municipio_residencia, "Municipio de Residencia", "Por favor, seleccione el municipio de residencia."),
            (actualizar_parroquia_residencia, "Parroquia de Residencia", "Por favor, seleccione la parroquia de residencia."),
            (actualizar_direccion_residencia, "Dirección de Residencia", "Por favor, ingrese la dirección de residencia.")
        ]

        for valor, campo, mensaje in campos_obligatorios:
            if not valor or not valor.strip():
                return JsonResponse({
                    "estado": "fallo",
                    "title": campo,
                    "descripcion": mensaje,
                    "icon": "warning"
                })

        condicion_residencia = actualizar_condicion_residencia
        municipio_residencia = actualizar_municipio_residencia
        parroquia_residencia = actualizar_parroquia_residencia
        direccion_residencia = actualizar_direccion_residencia

    cedula_identidad = nacionalidad_usuario + "-" + cedula_usuario
    telefono_principal = prefijo_principal + "-" + numero_principal
    correo_principal = correo_principal + dominio_principal

    try:
        with transaction.atomic():
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
            if nacimiento_registrado:
                info_nacimiento.pais = pais
                info_nacimiento.estado = estado
                info_nacimiento.municipio = municipio
                info_nacimiento.parroquia = parroquia
                info_nacimiento.direccion = direccion
                info_nacimiento.fecha_nacimiento = fecha_nacimiento
                info_nacimiento.save()

            # ACTUALIZAR RESIDENCIA
            if residencia_registrada:
                info_residencia.condicion_residencia = condicion_residencia
                info_residencia.municipio = municipio_residencia
                info_residencia.parroquia = parroquia_residencia
                info_residencia.direccion = direccion_residencia
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
                nombre_modulo="Actualización de datos del empleado",
                cargo_usuario=request.session.get("perfil", "No especificado"),
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

# VISUALIZAR EN LA TABLA LOS EMPLEADOS REGISTRADOS

def datos_empleado(request):
    nacionalidad = request.POST.get("nacionalidad", "").strip()
    cedula = request.POST.get("cedula", "").strip()

    if not nacionalidad or not cedula:
        return JsonResponse({
            "estado": "fallo",
            "title": "Datos incompletos",
            "descripcion": "Debe proporcionar la nacionalidad y el número de cédula.",
            "icon": "warning"
        })

    cedula_identidad = f"{nacionalidad}-{cedula}"

    def datos_completos(instancia, campos):

        if instancia is None:
            return False

        for campo in campos:
            valor = getattr(instancia, campo, None)

            if valor is None:
                return False

            if isinstance(valor, str):
                if not valor.strip() or valor.strip().casefold() == "n/a":
                    return False

        return True

    try:

        usuario = usuarios.objects.select_related(
            "credenciales",
            "propietario",
            "encargado_administrativo",
            "atencion_cliente",
            "supervisor__id_turno",
            "personal_limpieza__id_turno",
            "despachador__id_turno",
            "vigilante__id_turno"
        ).get(
            cedula_identidad=cedula_identidad
        )

        # DATOS DE NACIMIENTO
        info_nacimiento = nacimiento.objects.filter(
            id_usuario=usuario
        ).first()

        campos_nacimiento = [
            "pais",
            "estado",
            "municipio",
            "parroquia",
            "direccion",
            "fecha_nacimiento"
        ]

        nacimiento_registrado = datos_completos(
            info_nacimiento,
            campos_nacimiento
        )

        # DATOS DE CONTACTO
        info_contacto = contacto.objects.filter(
            id_usuario=usuario
        ).first()

        # DATOS DE RESIDENCIA
        info_residencia = residencia.objects.filter(
            id_usuario=usuario
        ).first()

        campos_residencia = [
            "condicion_residencia",
            "municipio",
            "parroquia",
            "direccion"
        ]

        residencia_registrada = datos_completos(
            info_residencia,
            campos_residencia
        )

        # PERFIL LABORAL Y TURNO
        perfil_laboral = "N/A"
        turno_laboral = "N/A"

        if hasattr(usuario, "propietario"):

            perfil_laboral = "Propietario"
            turno_laboral = "Turno Completo"

        elif (
            hasattr(usuario, "encargado_administrativo")
            and usuario.encargado_administrativo.vigencia
        ):

            perfil_laboral = "Encargado Administrativo"
            turno_laboral = "Turno Completo"

        elif (
            hasattr(usuario, "atencion_cliente")
            and usuario.atencion_cliente.vigencia
        ):

            perfil_laboral = "Atención al Cliente"
            turno_laboral = "Turno Completo"

        elif (
            hasattr(usuario, "supervisor")
            and usuario.supervisor.vigencia
        ):

            perfil_laboral = "Supervisor Encargado"
            turno_laboral = str(usuario.supervisor.id_turno)

        elif (
            hasattr(usuario, "personal_limpieza")
            and usuario.personal_limpieza.vigencia
        ):

            perfil_laboral = "Personal de Limpieza"
            turno_laboral = str(usuario.personal_limpieza.id_turno)

        elif (
            hasattr(usuario, "despachador")
            and usuario.despachador.vigencia
        ):

            perfil_laboral = "Despachador"
            turno_laboral = str(usuario.despachador.id_turno)

        elif (
            hasattr(usuario, "vigilante")
            and usuario.vigilante.vigencia
        ):

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
                "telefono_principal": (
                    info_contacto.telefono_principal
                    if info_contacto else "No registrado"
                ),
                "telefono_secundario": (
                    info_contacto.telefono_secundario
                    if info_contacto else "No registrado"
                ),
                "correo_principal": (
                    info_contacto.correo_principal
                    if info_contacto else "No registrado"
                ),
                "correo_secundario": (
                    info_contacto.correo_secundario
                    if info_contacto else "No registrado"
                ),
            },

            "nacimiento": {
                "pais": (
                    info_nacimiento.pais
                    if nacimiento_registrado else "No registrado"
                ),
                "estado": (
                    info_nacimiento.estado
                    if nacimiento_registrado else "No registrado"
                ),
                "municipio": (
                    info_nacimiento.municipio
                    if nacimiento_registrado else "No registrado"
                ),
                "parroquia": (
                    info_nacimiento.parroquia
                    if nacimiento_registrado else "No registrado"
                ),
                "direccion": (
                    info_nacimiento.direccion
                    if nacimiento_registrado else "No registrado"
                ),
                "fecha_nacimiento": (
                    str(info_nacimiento.fecha_nacimiento)
                    if nacimiento_registrado else "No registrado"
                ),
            },

            "residencia": {
                "condicion_residencia": (
                    info_residencia.condicion_residencia
                    if residencia_registrada else "No registrado"
                ),
                "municipio": (
                    info_residencia.municipio
                    if residencia_registrada else "No registrado"
                ),
                "parroquia": (
                    info_residencia.parroquia
                    if residencia_registrada else "No registrado"
                ),
                "direccion": (
                    info_residencia.direccion
                    if residencia_registrada else "No registrado"
                ),
            },
        })

    except usuarios.DoesNotExist:

        return JsonResponse({
            "estado": "fallo",
            "title": "No encontrado",
            "descripcion": "No existe un usuario con esa cédula.",
            "icon": "error"
        })

    except Exception:

        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "descripcion": "Ocurrió un error al consultar los datos del empleado.",
            "icon": "error"
        })

def visualizacion_datos_usuarios(request):
    if request.method == "POST":
        nacionalidad = request.POST.get("nacionalidad", "").strip()
        cedula = request.POST.get("cedula", "").strip()
        perfil = request.POST.get("perfil", "").strip()

        datos = []

        def coincide_cedula(usuario):
            if nacionalidad and cedula:
                return usuario.cedula_identidad == f"{nacionalidad}-{cedula}"
            return True

        # PROPIETARIO
        if not perfil or perfil == "Propietario":
            directivas = (
                propietarios.objects
                .select_related("id_usuario")
            )

            for empleado in directivas:
                usuario = empleado.id_usuario

                if not coincide_cedula(usuario):
                    continue

                datos.append({
                    "id": usuario.id_usuario,
                    "nombres": usuario.nombres,
                    "apellidos": usuario.apellidos,
                    "cedula": usuario.cedula_identidad,
                    "genero": usuario.genero,
                    "estado_civil": usuario.estado_civil,
                    "perfil": "Propietario",
                    "turno": "Turno Completo"
                })

        # ATENCIÓN AL CLIENTE
        if not perfil or perfil == "Atención al Cliente":
            empleados = (
                atencion_cliente.objects
                .select_related("id_usuario")
                .filter(vigencia=True)
            )

            for empleado in empleados:
                usuario = empleado.id_usuario

                if not coincide_cedula(usuario):
                    continue

                datos.append({
                    "id": usuario.id_usuario,
                    "nombres": usuario.nombres,
                    "apellidos": usuario.apellidos,
                    "cedula": usuario.cedula_identidad,
                    "genero": usuario.genero,
                    "estado_civil": usuario.estado_civil,
                    "perfil": "Atención al Cliente",
                    "turno": "Turno Completo"
                })

        # SUPERVISORES ENCARGADOS
        if not perfil or perfil == "Supervisor Encargado":
            supervisores = (
                supervisores_encargados.objects
                .select_related("id_usuario", "id_turno")
                .filter(vigencia=True)
            )

            for empleado in supervisores:
                usuario = empleado.id_usuario

                if not coincide_cedula(usuario):
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

                if not coincide_cedula(usuario):
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

                if not coincide_cedula(usuario):
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

                if not coincide_cedula(usuario):
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
