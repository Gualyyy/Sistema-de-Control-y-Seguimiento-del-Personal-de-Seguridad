from django.db import transaction
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models.functions import TruncDate

from inicio_sesion.models import usuarios, turnos_laborales, bitacora, supervisores_encargados, personal_limpieza, despachadores, vigilantes, atencion_cliente, propietarios, encargados_administrativos

# PERFILES REGISTRADOS

def perfiles_disponibles(request):
    turno_seleccionado = request.POST.get("turno")

    datos = [
        {
            "id_perfil": "SUPERVISOR_ENCARGADO",
            "perfil": "Supervisor Encargado"
        },
        {
            "id_perfil": "PERSONAL_LIMPIEZA",
            "perfil": "Personal de Limpieza"
        },
        {
            "id_perfil": "DESPACHADOR",
            "perfil": "Despachador"
        },
        {
            "id_perfil": "VIGILANTE",
            "perfil": "Vigilante"
        },
        {
            "id_perfil": "ATENCION_CLIENTE",
            "perfil": "Atención al Cliente"
        }
    ]

    if turno_seleccionado:
        try:
            turno_id = int(turno_seleccionado)
        except (TypeError, ValueError):
            turno_id = None

        if turno_id:
            supervisor_ocupado = (
                supervisores_encargados.objects
                .filter(
                    id_turno_id=turno_id,
                    vigencia=True
                )
                .exists()
            )

            if supervisor_ocupado:
                datos = [
                    perfil
                    for perfil in datos
                    if perfil["id_perfil"] != "SUPERVISOR_ENCARGADO"
                ]

    return JsonResponse({
        "perfiles": datos
    })

# BUSCAR DATOS PERFILES 

def buscar_datos_asignacion(request):
    nacionalidad = request.POST.get("nacionalidad", "").strip()
    cedula = request.POST.get("cedula", "").strip()

    if not nacionalidad or not cedula:
        return JsonResponse({
            "estado": "fallo",
            "title": "Vacío",
            "descripcion": "Debe ingresar la nacionalidad y la cédula.",
            "icon": "warning"
        })

    cedula_completa = f"{nacionalidad}-{cedula}"

    try:
        usuario = usuarios.objects.get(
            cedula_identidad=cedula_completa
        )
    except usuarios.DoesNotExist:
        return JsonResponse({
            "estado": "no_existe",
            "title": "Error",
            "descripcion": (
                "No se encontró ningún empleado con esa cédula."
            ),
            "icon": "warning"
        })

        # IMPEDIR BÚSQUEDA DE PROPIETARIO Y ENCARGADO ADMINISTRATIVO
    es_directiva = propietarios.objects.filter(
        id_usuario=usuario
    ).exists()

    es_encargado = encargados_administrativos.objects.filter(
        id_usuario=usuario
    ).exists()

    if es_directiva or es_encargado:
        return JsonResponse({
            "estado": "fallo",
            "codigo": "PERFIL_NO_PERMITIDO",
            "title": "Búsqueda no permitida",
            "descripcion": (
                "No se puede realizar la búsqueda de este usuario "
                "porque tiene el perfil de Propietario o "
                "Encargado Administrativo."
            ),
            "icon": "warning"
        })

    turnos = list(turnos_laborales.objects.all())
    perfiles_datos = []

    # ATENCIÓN AL CLIENTE
    atencion = (
        atencion_cliente.objects
        .filter(id_usuario=usuario)
        .first()
    )

    if atencion:
        perfiles_datos.append({
            "id_perfil_usuario": atencion.id_atencion_cliente,
            "id_perfil": "ATENCION_CLIENTE",
            "perfil": "Atención al Cliente",
            "id_turno": None,
            "turno": "Turno Completo",
            "vigencia": atencion.vigencia,
            "turnos": []
        })

    # SUPERVISOR ENCARGADO
    supervisor = (
        supervisores_encargados.objects
        .filter(id_usuario=usuario)
        .select_related("id_turno")
        .first()
    )

    if supervisor:
        opciones_turnos = []

        if not supervisor.vigencia:
            opciones_turnos = [
                {
                    "id_turno": turno.id_turno,
                    "nombre": turno.nombre
                }
                for turno in turnos
            ]
        else:
            for turno in turnos:
                if turno.id_turno == supervisor.id_turno_id:
                    opciones_turnos.append({
                        "id_turno": turno.id_turno,
                        "nombre": turno.nombre
                    })
                    continue

                supervisor_ocupado = (
                    supervisores_encargados.objects
                    .filter(
                        id_turno=turno,
                        vigencia=True
                    )
                    .exclude(
                        id_supervisor=supervisor.id_supervisor
                    )
                    .exists()
                )

                if not supervisor_ocupado:
                    opciones_turnos.append({
                        "id_turno": turno.id_turno,
                        "nombre": turno.nombre
                    })

        perfiles_datos.append({
            "id_perfil_usuario": supervisor.id_supervisor,
            "id_perfil": "SUPERVISOR_ENCARGADO",
            "perfil": "Supervisor Encargado",
            "id_turno": supervisor.id_turno_id,
            "turno": supervisor.id_turno.nombre,
            "vigencia": supervisor.vigencia,
            "turnos": opciones_turnos
        })

    # PERSONAL DE LIMPIEZA
    limpieza = (
        personal_limpieza.objects
        .filter(id_usuario=usuario)
        .select_related("id_turno")
        .first()
    )

    if limpieza:
        opciones_turnos = [
            {
                "id_turno": turno.id_turno,
                "nombre": turno.nombre
            }
            for turno in turnos
        ]

        perfiles_datos.append({
            "id_perfil_usuario": limpieza.id_personal,
            "id_perfil": "PERSONAL_LIMPIEZA",
            "perfil": "Personal de Limpieza",
            "id_turno": limpieza.id_turno_id,
            "turno": limpieza.id_turno.nombre,
            "vigencia": limpieza.vigencia,
            "turnos": opciones_turnos
        })

    # DESPACHADOR
    despachador = (
        despachadores.objects
        .filter(id_usuario=usuario)
        .select_related("id_turno")
        .first()
    )

    if despachador:
        opciones_turnos = [
            {
                "id_turno": turno.id_turno,
                "nombre": turno.nombre
            }
            for turno in turnos
        ]

        perfiles_datos.append({
            "id_perfil_usuario": despachador.id_despachador,
            "id_perfil": "DESPACHADOR",
            "perfil": "Despachador",
            "id_turno": despachador.id_turno_id,
            "turno": despachador.id_turno.nombre,
            "vigencia": despachador.vigencia,
            "turnos": opciones_turnos
        })

    # VIGILANTE
    vigilante = (
        vigilantes.objects
        .filter(id_usuario=usuario)
        .select_related("id_turno")
        .first()
    )

    if vigilante:
        opciones_turnos = [
            {
                "id_turno": turno.id_turno,
                "nombre": turno.nombre
            }
            for turno in turnos
        ]

        perfiles_datos.append({
            "id_perfil_usuario": vigilante.id_vigilante,
            "id_perfil": "VIGILANTE",
            "perfil": "Vigilante",
            "id_turno": vigilante.id_turno_id,
            "turno": vigilante.id_turno.nombre,
            "vigencia": vigilante.vigencia,
            "turnos": opciones_turnos
        })

    # INFORMACIÓN DEL USUARIO
    datos_usuario = {
        "id_usuario": usuario.id_usuario,
        "nombres": usuario.nombres,
        "apellidos": usuario.apellidos,
        "cedula_identidad": usuario.cedula_identidad,
        "genero": usuario.genero,
        "estado_civil": usuario.estado_civil
    }

    request.session["id_empleado"] = usuario.id_usuario

    # RESPUESTA
    respuesta = {
        "estado": "exito",
        "success": True,
        "usuario": datos_usuario,
        "perfiles": perfiles_datos
    }

    if not perfiles_datos:
        respuesta["codigo"] = "SIN_PERFIL"

    return JsonResponse(respuesta)

# PERFILES NO ASIGNADOS

def perfiles_usuario_no_registrados(request):
    turno_seleccionado = request.POST.get("turno")
    id_empleado = request.session.get("id_empleado")

    if not id_empleado:
        return JsonResponse({
            "estado": "fallo",
            "mensaje": "No se ha seleccionado ningún empleado.",
            "perfiles": []
        })

    try:
        turno_id = int(turno_seleccionado) if turno_seleccionado else None
    except (TypeError, ValueError):
        turno_id = None

    atencion = atencion_cliente.objects.filter(
        id_usuario_id=id_empleado
    ).first()

    supervisor = supervisores_encargados.objects.filter(
        id_usuario_id=id_empleado
    ).first()

    supervisor_ocupado = False

    if turno_id is not None:
        supervisor_ocupado = (
            supervisores_encargados.objects
            .filter(
                id_turno_id=turno_id,
                vigencia=True
            )
            .exclude(id_usuario_id=id_empleado)
            .exists()
        )

    perfiles = [
        {
            "id_perfil": "ATENCION_CLIENTE",
            "perfil": "Atención al Cliente",
            "asignado": atencion is not None,
            "vigencia": atencion.vigencia if atencion else False,
            "ocupado": (
                atencion_cliente.objects
                .filter(vigencia=True)
                .exclude(id_usuario_id=id_empleado)
                .exists()
            )
        },
        {
            "id_perfil": "SUPERVISOR_ENCARGADO",
            "perfil": "Supervisor Encargado",
            "asignado": supervisor is not None,
            "vigencia": supervisor.vigencia if supervisor else False,
            "turno_ocupado": supervisor_ocupado
        },
        {
            "id_perfil": "DESPACHADOR",
            "perfil": "Despachador",
            "asignado": despachadores.objects.filter(
                id_usuario_id=id_empleado
            ).exists()
        },
        {
            "id_perfil": "PERSONAL_LIMPIEZA",
            "perfil": "Personal de Limpieza",
            "asignado": personal_limpieza.objects.filter(
                id_usuario_id=id_empleado
            ).exists()
        },
        {
            "id_perfil": "VIGILANTE",
            "perfil": "Vigilante",
            "asignado": vigilantes.objects.filter(
                id_usuario_id=id_empleado
            ).exists()
        }
    ]

    return JsonResponse({
        "estado": "exito",
        "perfiles": perfiles
    })

# REGISTRAR NUEVAS PERFILES ASIGNADOS

def registrar_nueva_asignacion(request):
    if request.method == "POST":
        id_empleado = request.session.get("id_empleado")

        if not id_empleado:
            return JsonResponse({
                "estado": "error",
                "icon": "warning",
                "title": "Empleado no seleccionado",
                "descripcion": "No se ha seleccionado ningún empleado."
            })

        id_perfil = request.POST.get("perfil")

        perfiles_validos = {
            "SUPERVISOR_ENCARGADO": "Supervisor Encargado",
            "PERSONAL_LIMPIEZA": "Personal de Limpieza",
            "DESPACHADOR": "Despachador",
            "VIGILANTE": "Vigilante",
            "ATENCION_CLIENTE": "Atención al Cliente"
        }

        perfiles_con_turno = {
            "SUPERVISOR_ENCARGADO",
            "PERSONAL_LIMPIEZA",
            "DESPACHADOR",
            "VIGILANTE"
        }

        if not id_perfil or id_perfil not in perfiles_validos:
            return JsonResponse({
                "estado": "error",
                "icon": "error",
                "title": "Perfil no válido",
                "descripcion": "El perfil seleccionado no es válido."
            })

        id_turno = None
        turno = None

        if id_perfil in perfiles_con_turno:
            id_turno = request.POST.get("turnos_registro")

            if not id_turno:
                return JsonResponse({
                    "estado": "error",
                    "icon": "warning",
                    "title": "Turno no seleccionado",
                    "descripcion": (
                        "Debe seleccionar un turno laboral "
                        "para el perfil seleccionado."
                    )
                })

        try:
            usuario = usuarios.objects.get(
                id_usuario=id_empleado
            )
        except usuarios.DoesNotExist:
            return JsonResponse({
                "estado": "error",
                "icon": "error",
                "title": "Usuario no encontrado",
                "descripcion": "El usuario seleccionado no existe."
            })

        if id_perfil in perfiles_con_turno:
            try:
                turno = turnos_laborales.objects.get(
                    id_turno=id_turno
                )
            except (
                turnos_laborales.DoesNotExist,
                ValueError,
                TypeError
            ):
                return JsonResponse({
                    "estado": "error",
                    "icon": "error",
                    "title": "Turno no encontrado",
                    "descripcion": "El turno seleccionado no existe."
                })

        try:
            with transaction.atomic():
                usuario_accion = usuarios.objects.get(
                    cedula_identidad=request.session.get(
                        "cedula_identidad"
                    )
                )

                nombre_perfil = perfiles_validos[id_perfil]

                modelos_perfiles = {
                    "SUPERVISOR_ENCARGADO": supervisores_encargados,
                    "PERSONAL_LIMPIEZA": personal_limpieza,
                    "DESPACHADOR": despachadores,
                    "VIGILANTE": vigilantes,
                    "ATENCION_CLIENTE": atencion_cliente,
                }

                if modelos_perfiles[id_perfil].objects.filter(
                    id_usuario=usuario
                ).exists():
                    return JsonResponse({
                        "estado": "error",
                        "icon": "warning",
                        "title": "Perfil ya registrado",
                        "descripcion": (
                            "Este empleado ya tiene registrado ese perfil. "
                            "Habilítelo desde la gestión de perfiles."
                        )
                    })

                perfiles_activos = (
                    supervisores_encargados.objects.filter(
                        id_usuario=usuario,
                        vigencia=True
                    ).exists()
                    or personal_limpieza.objects.filter(
                        id_usuario=usuario,
                        vigencia=True
                    ).exists()
                    or despachadores.objects.filter(
                        id_usuario=usuario,
                        vigencia=True
                    ).exists()
                    or vigilantes.objects.filter(
                        id_usuario=usuario,
                        vigencia=True
                    ).exists()
                    or atencion_cliente.objects.filter(
                        id_usuario=usuario,
                        vigencia=True
                    ).exists()
                )

                if perfiles_activos:
                    return JsonResponse({
                        "estado": "error",
                        "icon": "warning",
                        "title": "Perfil activo",
                        "descripcion": (
                            "El empleado ya tiene un perfil laboral "
                            "activo. Debe inhabilitar el perfil actual "
                            "antes de asignar uno nuevo."
                        )
                    })

                # SUPERVISOR ENCARGADO
                if id_perfil == "SUPERVISOR_ENCARGADO":

                    supervisor_existente = (
                        supervisores_encargados.objects
                        .select_for_update()
                        .filter(id_usuario=usuario)
                        .first()
                    )

                    if supervisor_existente:
                        if supervisor_existente.vigencia:
                            return JsonResponse({
                                "estado": "error",
                                "icon": "warning",
                                "title": "Perfil ya asignado",
                                "descripcion": (
                                    "El empleado ya tiene asignado "
                                    "el perfil Supervisor Encargado."
                                )
                            })

                        supervisor_ocupado = (
                            supervisores_encargados.objects
                            .filter(
                                id_turno=turno,
                                vigencia=True
                            )
                            .exclude(
                                id_supervisor=(
                                    supervisor_existente.id_supervisor
                                )
                            )
                            .exists()
                        )

                        if supervisor_ocupado:
                            return JsonResponse({
                                "estado": "error",
                                "icon": "warning",
                                "title": "Turno ocupado",
                                "descripcion": (
                                    "El turno seleccionado ya tiene "
                                    "un Supervisor Encargado activo."
                                )
                            })

                        supervisor_existente.id_turno = turno
                        supervisor_existente.vigencia = True

                        supervisor_existente.save(
                            update_fields=[
                                "id_turno",
                                "vigencia"
                            ]
                        )

                    else:
                        supervisor_ocupado = (
                            supervisores_encargados.objects
                            .filter(
                                id_turno=turno,
                                vigencia=True
                            )
                            .exists()
                        )

                        if supervisor_ocupado:
                            return JsonResponse({
                                "estado": "error",
                                "icon": "warning",
                                "title": "Turno ocupado",
                                "descripcion": (
                                    "El turno seleccionado ya tiene "
                                    "un Supervisor Encargado activo."
                                )
                            })

                        supervisores_encargados.objects.create(
                            id_usuario=usuario,
                            id_turno=turno,
                            vigencia=True
                        )

                # PERSONAL DE LIMPIEZA
                elif id_perfil == "PERSONAL_LIMPIEZA":

                    limpieza_existente = (
                        personal_limpieza.objects
                        .select_for_update()
                        .filter(id_usuario=usuario)
                        .first()
                    )

                    if limpieza_existente:
                        if limpieza_existente.vigencia:
                            return JsonResponse({
                                "estado": "error",
                                "icon": "warning",
                                "title": "Perfil ya asignado",
                                "descripcion": (
                                    "El empleado ya tiene asignado "
                                    "el perfil Personal de Limpieza."
                                )
                            })

                        limpieza_existente.id_turno = turno
                        limpieza_existente.vigencia = True

                        limpieza_existente.save(
                            update_fields=[
                                "id_turno",
                                "vigencia"
                            ]
                        )

                    else:
                        personal_limpieza.objects.create(
                            id_usuario=usuario,
                            id_turno=turno,
                            vigencia=True
                        )

                # DESPACHADOR
                elif id_perfil == "DESPACHADOR":

                    despachador_existente = (
                        despachadores.objects
                        .select_for_update()
                        .filter(id_usuario=usuario)
                        .first()
                    )

                    if despachador_existente:
                        if despachador_existente.vigencia:
                            return JsonResponse({
                                "estado": "error",
                                "icon": "warning",
                                "title": "Perfil ya asignado",
                                "descripcion": (
                                    "El empleado ya tiene asignado "
                                    "el perfil Despachador."
                                )
                            })

                        despachador_existente.id_turno = turno
                        despachador_existente.vigencia = True

                        despachador_existente.save(
                            update_fields=[
                                "id_turno",
                                "vigencia"
                            ]
                        )

                    else:
                        despachadores.objects.create(
                            id_usuario=usuario,
                            id_turno=turno,
                            vigencia=True
                        )

                # VIGILANTE
                elif id_perfil == "VIGILANTE":

                    vigilante_existente = (
                        vigilantes.objects
                        .select_for_update()
                        .filter(id_usuario=usuario)
                        .first()
                    )

                    if vigilante_existente:
                        if vigilante_existente.vigencia:
                            return JsonResponse({
                                "estado": "error",
                                "icon": "warning",
                                "title": "Perfil ya asignado",
                                "descripcion": (
                                    "El empleado ya tiene asignado "
                                    "el perfil Vigilante."
                                )
                            })

                        vigilante_existente.id_turno = turno
                        vigilante_existente.vigencia = True

                        vigilante_existente.save(
                            update_fields=[
                                "id_turno",
                                "vigencia"
                            ]
                        )

                    else:
                        vigilantes.objects.create(
                            id_usuario=usuario,
                            id_turno=turno,
                            vigencia=True
                        )

                # ATENCIÓN AL CLIENTE
                elif id_perfil == "ATENCION_CLIENTE":

                    atencion_ocupada = (
                        atencion_cliente.objects
                        .filter(vigencia=True)
                        .exclude(id_usuario=usuario)
                        .exists()
                    )

                    if atencion_ocupada:
                        return JsonResponse({
                            "estado": "error",
                            "icon": "warning",
                            "title": "Perfil ocupado",
                            "descripcion": (
                                "Ya existe otro empleado activo "
                                "en Atención al Cliente."
                            )
                        })

                    atencion_existente = (
                        atencion_cliente.objects
                        .select_for_update()
                        .filter(id_usuario=usuario)
                        .first()
                    )

                    if atencion_existente:
                        if atencion_existente.vigencia:
                            return JsonResponse({
                                "estado": "error",
                                "icon": "warning",
                                "title": "Perfil ya asignado",
                                "descripcion": (
                                    "El empleado ya tiene asignado "
                                    "el perfil Atención al Cliente."
                                )
                            })

                        atencion_existente.vigencia = True

                        atencion_existente.save(
                            update_fields=["vigencia"]
                        )

                    else:
                        atencion_cliente.objects.create(
                            id_usuario=usuario,
                            vigencia=True
                        )

                nombre_turno = (
                    turno.nombre
                    if turno
                    else "Turno Completo"
                )

                bitacora.objects.create(
                    id_usuario=usuario_accion,
                    nombre_modulo="Asignación de perfiles y turnos",
                    cargo_usuario=request.session.get("perfil", "No especificado"),
                    accion=(
                        f"Se asignó el perfil {nombre_perfil} "
                        f"al empleado {usuario.nombres} "
                        f"{usuario.apellidos} "
                        f"en el turno {nombre_turno}."
                    )
                )

            return JsonResponse({
                "estado": "exito",
                "icon": "success",
                "title": "Éxito",
                "descripcion": (
                    f"El perfil {nombre_perfil} "
                    "se registró exitosamente."
                )
            })

        except usuarios.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Usuario no encontrado",
                "descripcion": (
                    "No se encontró el usuario que registra "
                    "la asignación."
                )
            })

        except Exception as e:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Error",
                "descripcion": (
                    "Ocurrió un error al registrar "
                    f"la asignación {e}."
                )
            })

# CONOCER LA CANTIDAD DE PERFILES ASIGNADO AL EMEPLEADO

def cantidad_perfiles_asignado(request):
    id_empleado = request.session.get("id_empleado")

    if not id_empleado:
        return JsonResponse({
            "estado": "fallo",
            "icon": "error",
            "title": "Error",
            "descripcion": "No se ha seleccionado ningún empleado."
        })

    # TOTAL DE PERFILES LABORALES
    cantidad_perfiles = 5

    perfiles_asignados = {
        "SUPERVISOR_ENCARGADO": supervisores_encargados.objects.filter(
            id_usuario_id=id_empleado
        ).exists(),
        "PERSONAL_LIMPIEZA": personal_limpieza.objects.filter(
            id_usuario_id=id_empleado
        ).exists(),
        "DESPACHADOR": despachadores.objects.filter(
            id_usuario_id=id_empleado
        ).exists(),
        "VIGILANTE": vigilantes.objects.filter(
            id_usuario_id=id_empleado
        ).exists(),
        "ATENCION_CLIENTE": atencion_cliente.objects.filter(
            id_usuario_id=id_empleado
        ).exists(),
    }
    cantidad_asignados = sum(perfiles_asignados.values())
    atencion_ocupada = (
        atencion_cliente.objects
        .filter(vigencia=True)
        .exclude(id_usuario_id=id_empleado)
        .exists()
    )
    solo_falta_atencion_ocupada = (
        cantidad_asignados == cantidad_perfiles - 1
        and not perfiles_asignados["ATENCION_CLIENTE"]
        and atencion_ocupada
    )

    if cantidad_asignados >= cantidad_perfiles or solo_falta_atencion_ocupada:
        todos_asignados = cantidad_asignados >= cantidad_perfiles
        return JsonResponse({
            "estado": "fallo",
            "todos_asignados": todos_asignados,
            "atencion_ocupada": atencion_ocupada,
            "icon": "error",
            "title": (
                "Perfiles completos"
                if todos_asignados
                else "Sin perfiles disponibles"
            ),
            "descripcion": (
                "El empleado ya tiene todos los perfiles laborales "
                "asignados."
                if todos_asignados
                else "El único perfil que le falta es Atención al Cliente, "
                "pero ya está ocupado por otro empleado."
            ),
        })

    return JsonResponse({
        "estado": "exito",
        "todos_asignados": False,
        "atencion_ocupada": atencion_ocupada,
    })

# CARGA LOS PERFILES ASIGNADOS O MODIFICADOS

def cargar_perfiles_asignados(request):
    id_empleado = request.session.get("id_empleado")

    if not id_empleado:
        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Empleado no seleccionado",
            "descripcion": "No se ha seleccionado ningún empleado.",
            "perfiles": []
        })

    turnos = list(turnos_laborales.objects.all())
    datos = []

    # SUPERVISOR ENCARGADO
    supervisor = (
        supervisores_encargados.objects
        .filter(id_usuario_id=id_empleado)
        .select_related("id_turno")
        .first()
    )

    if supervisor:
        opciones_turnos = []

        if not supervisor.vigencia:
            opciones_turnos = [
                {
                    "id_turno": turno.id_turno,
                    "nombre": turno.nombre
                }
                for turno in turnos
            ]

        else:
            for turno in turnos:

                # El turno actual siempre puede mantenerse
                if (
                    supervisor.id_turno
                    and turno.id_turno == supervisor.id_turno_id
                ):
                    opciones_turnos.append({
                        "id_turno": turno.id_turno,
                        "nombre": turno.nombre
                    })
                    continue

                # Verificar si otro supervisor ocupa el turno
                supervisor_ocupado = (
                    supervisores_encargados.objects
                    .filter(
                        id_turno_id=turno.id_turno,
                        vigencia=True
                    )
                    .exclude(
                        id_supervisor=supervisor.id_supervisor
                    )
                    .exists()
                )

                if not supervisor_ocupado:
                    opciones_turnos.append({
                        "id_turno": turno.id_turno,
                        "nombre": turno.nombre
                    })

        datos.append({
            "id_registro": supervisor.id_supervisor,
            "id_perfil": "SUPERVISOR_ENCARGADO",
            "perfil": "Supervisor Encargado",
            "id_turno": (
                supervisor.id_turno.id_turno
                if supervisor.id_turno
                else None
            ),
            "turno": (
                supervisor.id_turno.nombre
                if supervisor.id_turno
                else "Sin turno asignado"
            ),
            "vigencia": supervisor.vigencia,
            "turnos": opciones_turnos
        })

    # PERSONAL DE LIMPIEZA
    limpieza = (
        personal_limpieza.objects
        .filter(id_usuario_id=id_empleado)
        .select_related("id_turno")
        .first()
    )

    if limpieza:
        opciones_turnos = [
            {
                "id_turno": turno.id_turno,
                "nombre": turno.nombre
            }
            for turno in turnos
        ]

        datos.append({
            "id_registro": limpieza.id_personal,
            "id_perfil": "PERSONAL_LIMPIEZA",
            "perfil": "Personal de Limpieza",
            "id_turno": (
                limpieza.id_turno.id_turno
                if limpieza.id_turno
                else None
            ),
            "turno": (
                limpieza.id_turno.nombre
                if limpieza.id_turno
                else "Sin turno asignado"
            ),
            "vigencia": limpieza.vigencia,
            "turnos": opciones_turnos
        })

    # DESPACHADOR
    despachador = (
        despachadores.objects
        .filter(id_usuario_id=id_empleado)
        .select_related("id_turno")
        .first()
    )

    if despachador:
        opciones_turnos = [
            {
                "id_turno": turno.id_turno,
                "nombre": turno.nombre
            }
            for turno in turnos
        ]

        datos.append({
            "id_registro": despachador.id_despachador,
            "id_perfil": "DESPACHADOR",
            "perfil": "Despachador",
            "id_turno": (
                despachador.id_turno.id_turno
                if despachador.id_turno
                else None
            ),
            "turno": (
                despachador.id_turno.nombre
                if despachador.id_turno
                else "Sin turno asignado"
            ),
            "vigencia": despachador.vigencia,
            "turnos": opciones_turnos
        })

    # VIGILANTE
    vigilante = (
        vigilantes.objects
        .filter(id_usuario_id=id_empleado)
        .select_related("id_turno")
        .first()
    )

    if vigilante:
        opciones_turnos = [
            {
                "id_turno": turno.id_turno,
                "nombre": turno.nombre
            }
            for turno in turnos
        ]

        datos.append({
            "id_registro": vigilante.id_vigilante,
            "id_perfil": "VIGILANTE",
            "perfil": "Vigilante",
            "id_turno": (
                vigilante.id_turno.id_turno
                if vigilante.id_turno
                else None
            ),
            "turno": (
                vigilante.id_turno.nombre
                if vigilante.id_turno
                else "Sin turno asignado"
            ),
            "vigencia": vigilante.vigencia,
            "turnos": opciones_turnos
        })

    # ATENCIÓN AL CLIENTE
    atencion = (
        atencion_cliente.objects
        .filter(id_usuario_id=id_empleado)
        .first()
    )

    if atencion:
        datos.append({
            "id_registro": atencion.id_atencion_cliente,
            "id_perfil": "ATENCION_CLIENTE",
            "perfil": "Atención al Cliente",
            "id_turno": None,
            "turno": "Turno Completo",
            "vigencia": atencion.vigencia,
            "turnos": []
        })

    return JsonResponse({
        "estado": "exito",
        "perfiles": datos
    })

#  DETALLES PERFILES ASIGNADO

def buscar_datos_perfil(request):
    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Método no permitido",
            "descripcion": "La solicitud realizada no es válida."
        })

    id_perfil = request.POST.get("id_perfil")
    id_perfil_usuario = request.POST.get("id_perfil_usuario")

    if not id_perfil or not id_perfil_usuario:
        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Datos incompletos",
            "descripcion": "No se recibió toda la información del perfil seleccionado."
        })

    if id_perfil == "ATENCION_CLIENTE":
        try:
            info_perfil = (
                atencion_cliente.objects
                .select_related("id_usuario")
                .get(id_atencion_cliente=id_perfil_usuario)
            )

        except atencion_cliente.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Perfil no disponible",
                "descripcion": "El personal de Atención al Cliente seleccionado no existe."
            })

        return JsonResponse({
            "estado": "exito",
            "id_registro": info_perfil.id_atencion_cliente,
            "id_perfil": id_perfil,
            "id_turno": None,
            "turno": "Turno Completo",
            "vigencia": info_perfil.vigencia
        })

    elif id_perfil == "SUPERVISOR_ENCARGADO":
        try:
            info_perfil = (
                supervisores_encargados.objects
                .select_related("id_usuario", "id_turno")
                .get(id_supervisor=id_perfil_usuario)
            )

        except supervisores_encargados.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Perfil no disponible",
                "descripcion": "El Supervisor Encargado seleccionado no existe."
            })

    elif id_perfil == "PERSONAL_LIMPIEZA":
        try:
            info_perfil = (
                personal_limpieza.objects
                .select_related("id_usuario", "id_turno")
                .get(id_personal=id_perfil_usuario)
            )

        except personal_limpieza.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Perfil no disponible",
                "descripcion": "El Personal de Limpieza seleccionado no existe."
            })

    elif id_perfil == "DESPACHADOR":
        try:
            info_perfil = (
                despachadores.objects
                .select_related("id_usuario", "id_turno")
                .get(id_despachador=id_perfil_usuario)
            )

        except despachadores.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Perfil no disponible",
                "descripcion": "El Despachador seleccionado no existe."
            })

    elif id_perfil == "VIGILANTE":
        try:
            info_perfil = (
                vigilantes.objects
                .select_related("id_usuario", "id_turno")
                .get(id_vigilante=id_perfil_usuario)
            )

        except vigilantes.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Perfil no disponible",
                "descripcion": "El Vigilante seleccionado no existe."
            })

    else:
        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Perfil inválido",
            "descripcion": "El tipo de personal seleccionado no es válido."
        })

    return JsonResponse({
        "estado": "exito",
        "id_registro": id_perfil_usuario,
        "id_perfil": id_perfil,
        "id_turno": (
            info_perfil.id_turno.id_turno
            if info_perfil.id_turno
            else None
        ),
        "turno": (
            info_perfil.id_turno.nombre
            if info_perfil.id_turno
            else "Turno Completo"
        ),
        "vigencia": info_perfil.vigencia
    })

# ACTUALIZAR PERFILES ASIGNADOS

def actualizar_vigencia_perfil(request):
    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Método no permitido",
            "descripcion": "La solicitud realizada no es válida."
        }, status=405)

    id_registro = request.POST.get("id_perfil_asignado")
    id_perfil = request.POST.get("id_perfil")
    turno = request.POST.get("actualizar_turno")
    vigencia = request.POST.get("vigencia")

    if not id_registro or not id_perfil:
        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Dato faltante",
            "descripcion": "No se recibió el personal seleccionado."
        })

    if vigencia not in ["DESIGNACION", "REASIGNAR"]:
        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Acción no válida",
            "descripcion": "La acción solicitada no es válida."
        })

    perfiles_con_turno = [
        "SUPERVISOR_ENCARGADO",
        "PERSONAL_LIMPIEZA",
        "DESPACHADOR",
        "VIGILANTE"
    ]

    if id_perfil in perfiles_con_turno and not turno:
        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Turno no seleccionado",
            "descripcion": "Debe seleccionar un turno."
        })

    try:
        id_registro = int(id_registro)

        if id_perfil in perfiles_con_turno:
            id_turno = int(turno)
        else:
            id_turno = None

    except (TypeError, ValueError):
        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Datos inválidos",
            "descripcion": "El registro o turno seleccionado no es válido."
        })

    try:
        with transaction.atomic():

            # SUPERVISOR ENCARGADO
            if id_perfil == "SUPERVISOR_ENCARGADO":
                try:
                    info_perfil = (
                        supervisores_encargados.objects
                        .select_related("id_usuario", "id_turno")
                        .select_for_update()
                        .get(id_supervisor=id_registro)
                    )
                except supervisores_encargados.DoesNotExist:
                    return JsonResponse({
                        "estado": "fallo",
                        "icon": "warning",
                        "title": "Perfil no disponible",
                        "descripcion": (
                            "El Supervisor Encargado seleccionado no existe."
                        )
                    })

                modelo = "supervisor"

            # PERSONAL DE LIMPIEZA
            elif id_perfil == "PERSONAL_LIMPIEZA":
                try:
                    info_perfil = (
                        personal_limpieza.objects
                        .select_related("id_usuario", "id_turno")
                        .select_for_update()
                        .get(id_personal=id_registro)
                    )
                except personal_limpieza.DoesNotExist:
                    return JsonResponse({
                        "estado": "fallo",
                        "icon": "warning",
                        "title": "Perfil no disponible",
                        "descripcion": (
                            "El Personal de Limpieza seleccionado no existe."
                        )
                    })

                modelo = "limpieza"

            # DESPACHADOR
            elif id_perfil == "DESPACHADOR":
                try:
                    info_perfil = (
                        despachadores.objects
                        .select_related("id_usuario", "id_turno")
                        .select_for_update()
                        .get(id_despachador=id_registro)
                    )
                except despachadores.DoesNotExist:
                    return JsonResponse({
                        "estado": "fallo",
                        "icon": "warning",
                        "title": "Perfil no disponible",
                        "descripcion": (
                            "El Despachador seleccionado no existe."
                        )
                    })

                modelo = "despachador"

            # VIGILANTE
            elif id_perfil == "VIGILANTE":
                try:
                    info_perfil = (
                        vigilantes.objects
                        .select_related("id_usuario", "id_turno")
                        .select_for_update()
                        .get(id_vigilante=id_registro)
                    )
                except vigilantes.DoesNotExist:
                    return JsonResponse({
                        "estado": "fallo",
                        "icon": "warning",
                        "title": "Perfil no disponible",
                        "descripcion": "El Vigilante seleccionado no existe."
                    })

                modelo = "vigilante"

            # ATENCIÓN AL CLIENTE
            elif id_perfil == "ATENCION_CLIENTE":
                try:
                    info_perfil = (
                        atencion_cliente.objects
                        .select_related("id_usuario")
                        .select_for_update()
                        .get(id_atencion_cliente=id_registro)
                    )
                except atencion_cliente.DoesNotExist:
                    return JsonResponse({
                        "estado": "fallo",
                        "icon": "warning",
                        "title": "Perfil no disponible",
                        "descripcion": (
                            "El personal de Atención al Cliente "
                            "seleccionado no existe."
                        )
                    })

                modelo = "atencion_cliente"

            else:
                return JsonResponse({
                    "estado": "fallo",
                    "icon": "warning",
                    "title": "Perfil inválido",
                    "descripcion": (
                        "El tipo de personal seleccionado no es válido."
                    )
                })

            # VALIDAR TURNO
            turno_nuevo = None

            if id_perfil in perfiles_con_turno:
                try:
                    turno_nuevo = turnos_laborales.objects.get(
                        id_turno=id_turno
                    )
                except turnos_laborales.DoesNotExist:
                    return JsonResponse({
                        "estado": "fallo",
                        "icon": "warning",
                        "title": "Turno no disponible",
                        "descripcion": "El turno seleccionado no existe."
                    })

            # IDENTIFICAR USUARIO QUE REALIZA LA ACCIÓN
            try:
                usuario_accion = usuarios.objects.get(
                    cedula_identidad=request.session.get(
                        "cedula_identidad"
                    )
                )
            except usuarios.DoesNotExist:
                return JsonResponse({
                    "estado": "fallo",
                    "icon": "error",
                    "title": "Usuario no disponible",
                    "descripcion": (
                        "No se pudo identificar al usuario que realiza "
                        "la acción."
                    )
                })

            usuario_afectado = info_perfil.id_usuario

            nombres_perfiles = {
                "SUPERVISOR_ENCARGADO": "Supervisor Encargado",
                "PERSONAL_LIMPIEZA": "Personal de Limpieza",
                "DESPACHADOR": "Despachador",
                "VIGILANTE": "Vigilante",
                "ATENCION_CLIENTE": "Atención al Cliente"
            }

            nombre_perfil = nombres_perfiles[id_perfil]

            # SOLO UNA ATENCIÓN AL CLIENTE ACTIVA EN TODA LA EMPRESA
            if (
                id_perfil == "ATENCION_CLIENTE"
                and vigencia == "REASIGNAR"
            ):
                atencion_activa = (
                    atencion_cliente.objects
                    .filter(vigencia=True)
                    .exclude(
                        id_atencion_cliente=info_perfil.id_atencion_cliente
                    )
                    .exists()
                )

                if atencion_activa:
                    return JsonResponse({
                        "estado": "fallo",
                        "icon": "warning",
                        "title": "Perfil ocupado",
                        "descripcion": (
                            "Ya existe un empleado con el perfil "
                            "de Atención al Cliente activo. Debe "
                            "deshabilitar ese perfil antes de habilitar otro."
                        )
                    })

            # VALIDAR QUE EL EMPLEADO NO TENGA OTRO PERFIL ACTIVO
            if vigencia == "REASIGNAR":

                supervisores_activos = (
                    supervisores_encargados.objects
                    .select_for_update()
                    .filter(
                        id_usuario=usuario_afectado,
                        vigencia=True
                    )
                )

                limpiezas_activas = (
                    personal_limpieza.objects
                    .select_for_update()
                    .filter(
                        id_usuario=usuario_afectado,
                        vigencia=True
                    )
                )

                despachadores_activos = (
                    despachadores.objects
                    .select_for_update()
                    .filter(
                        id_usuario=usuario_afectado,
                        vigencia=True
                    )
                )

                vigilantes_activos = (
                    vigilantes.objects
                    .select_for_update()
                    .filter(
                        id_usuario=usuario_afectado,
                        vigencia=True
                    )
                )

                atenciones_activas = (
                    atencion_cliente.objects
                    .select_for_update()
                    .filter(
                        id_usuario=usuario_afectado,
                        vigencia=True
                    )
                )

                perfil_activo = None

                if supervisores_activos.exclude(
                    id_supervisor=id_registro
                ).exists() or (
                    modelo != "supervisor"
                    and supervisores_activos.exists()
                ):
                    perfil_activo = "Supervisor Encargado"

                elif limpiezas_activas.exclude(
                    id_personal=id_registro
                ).exists() or (
                    modelo != "limpieza"
                    and limpiezas_activas.exists()
                ):
                    perfil_activo = "Personal de Limpieza"

                elif despachadores_activos.exclude(
                    id_despachador=id_registro
                ).exists() or (
                    modelo != "despachador"
                    and despachadores_activos.exists()
                ):
                    perfil_activo = "Despachador"

                elif vigilantes_activos.exclude(
                    id_vigilante=id_registro
                ).exists() or (
                    modelo != "vigilante"
                    and vigilantes_activos.exists()
                ):
                    perfil_activo = "Vigilante"

                elif atenciones_activas.exclude(
                    id_atencion_cliente=id_registro
                ).exists() or (
                    modelo != "atencion_cliente"
                    and atenciones_activas.exists()
                ):
                    perfil_activo = "Atención al Cliente"

                if perfil_activo:
                    return JsonResponse({
                        "estado": "fallo",
                        "icon": "warning",
                        "title": "Perfil activo",
                        "descripcion": (
                            f"El empleado ya tiene el perfil "
                            f"{perfil_activo} activo. Debe deshabilitarlo "
                            "antes de activar otro perfil."
                        )
                    })

            # VALIDAR DISPONIBILIDAD DEL TURNO DEL SUPERVISOR
            if (
                modelo == "supervisor"
                and vigencia == "REASIGNAR"
            ):
                supervisor_ocupado = (
                    supervisores_encargados.objects
                    .select_for_update()
                    .filter(
                        id_turno=turno_nuevo,
                        vigencia=True
                    )
                    .exclude(
                        id_supervisor=info_perfil.id_supervisor
                    )
                    .exists()
                )

                if supervisor_ocupado:
                    return JsonResponse({
                        "estado": "fallo",
                        "icon": "warning",
                        "title": "Turno ocupado",
                        "descripcion": (
                            "El turno seleccionado ya tiene un "
                            "Supervisor Encargado vigente."
                        )
                    })

            # ACTUALIZAR VIGENCIA Y TURNO
            nueva_vigencia = vigencia == "REASIGNAR"
            info_perfil.vigencia = nueva_vigencia

            campos_actualizados = ["vigencia"]

            if id_perfil in perfiles_con_turno:
                info_perfil.id_turno = turno_nuevo
                campos_actualizados.append("id_turno")

            info_perfil.save(update_fields=campos_actualizados)

            # GENERAR DESCRIPCIÓN
            nombres_completos = (
                f"{usuario_afectado.nombres} "
                f"{usuario_afectado.apellidos}"
            )

            if nueva_vigencia:
                if turno_nuevo:
                    descripcion = (
                        f"Se habilitó el perfil {nombre_perfil} "
                        f"para el empleado {nombres_completos} "
                        f"en el turno {turno_nuevo.nombre}."
                    )
                else:
                    descripcion = (
                        f"Se habilitó el perfil {nombre_perfil} "
                        f"para el empleado {nombres_completos}."
                    )
            else:
                descripcion = (
                    f"Se deshabilitó el perfil {nombre_perfil} "
                    f"del empleado {nombres_completos}."
                )

            # REGISTRAR EN BITÁCORA
            bitacora.objects.create(
                id_usuario=usuario_accion,
                nombre_modulo="Gestión de perfiles de empleado",
                cargo_usuario=request.session.get("perfil", "No especificado"),
                accion=descripcion
            )

            return JsonResponse({
                "estado": "exito",
                "icon": "success",
                "title": "Éxito",
                "descripcion": descripcion
            })

    except Exception as e:
        return JsonResponse({
            "estado": "fallo",
            "icon": "error",
            "title": "Error",
            "descripcion": (
                "Ocurrió un error al actualizar la vigencia del perfil."
                f" Error: {e}"
            )
        })

def gestionar_perfiles_empleado(request):
    return render(request, "Modulos/Perfiles/gestionar_perfiles_empleado.html")
