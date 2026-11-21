document.addEventListener("DOMContentLoaded", () => {

    const formulario_busqueda = document.getElementById("formulario_busqueda");
    const formulario_registrar = document.getElementById("formulario_registrar");
    const formulario_actualizar = document.getElementById("formulario_actualizar");

    const select_nacionalidad = document.getElementById("nacionalidad");
    const input_cedula_identidad = document.getElementById("cedula_identidad");
    const contenedor_perfiles = document.getElementById("contenedor_perfiles_registrados");

    const input_nombres_empleado = document.getElementById("nombres_empleado");
    const input_apellidos_empleado = document.getElementById("apellidos_empleado");

    const select_turnos_registro = document.getElementById("turnos_registro");
    const input_perfil_registrar = document.getElementById("perfil_registrar");

    const select_turno_actualizar = document.getElementById("actualizar_turno");
    const input_perfil_asignado = document.getElementById("id_perfil_asignado");

    const btn_asignar_perfil = document.getElementById("asignar_perfil");
    const dialogo_asignacion = document.getElementById("dialogo_registro");
    const btn_cerrar_registro = document.getElementById("btn_cerrar_registro");

    const dialogo_gestion = document.getElementById("dialogo_gestion");
    const btn_cerrar_gestion = document.getElementById("btn_cerrar_gestion");
    const input_habilitar_perfil = document.getElementById("habilitar_perfil");
    const input_deshabilitar_perfil = document.getElementById("deshabilitar_perfil");

    const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;

    configurarCedula(input_cedula_identidad, select_nacionalidad);

    let turno = "";

    function limpiarDatosEmpleado() {
        input_perfil_registrar.value = "";
        input_nombres_empleado.value = "";
        input_apellidos_empleado.value = "";
        contenedor_perfiles.innerHTML = "";
        btn_asignar_perfil.disabled = true;
    }

    async function actualizarDisponibilidadAsignacion() {
        btn_asignar_perfil.disabled = true;

        try {
            const respuesta = await fetch("/cantidad_perfiles_asignado/");
            const resultado = await respuesta.json();

            if (!respuesta.ok) {
                throw new Error(
                    resultado.descripcion ||
                    "No se pudo consultar la disponibilidad de perfiles."
                );
            }

            btn_asignar_perfil.disabled = resultado.estado !== "exito";
        } catch (error) {
            console.error(error);
            btn_asignar_perfil.disabled = true;
        }
    }

    // MUESTRA LOS PERFILES ASIGANDOS DEL EMPLEADO

    formulario_busqueda.addEventListener("submit", async (e) => {
        e.preventDefault();

        const formulario = new FormData(formulario_busqueda);
        limpiarDatosEmpleado();

        try {
            const respuesta = await fetch("/buscar_datos_asignacion/", {
                method: "POST",
                body: formulario
            });
            const resultado = await respuesta.json();

            formulario_busqueda.reset();

            if (!respuesta.ok || resultado.estado !== "exito") {
                await Swal.fire({
                    title: resultado.title || "No se pudo completar la búsqueda",
                    text: resultado.descripcion || "No se pudieron consultar los datos del empleado.",
                    icon: resultado.icon || (respuesta.ok ? "warning" : "error")
                });
                return;
            }

            if (!resultado.usuario || !resultado.usuario.id_usuario) {
                throw new Error("La respuesta no contiene los datos del empleado.");
            }

            await Swal.fire({
                title: "Éxito",
                text: "Datos del empleado encontrado exitosamente",
                icon: "success"
            });

            input_perfil_registrar.value = resultado.usuario.id_usuario;
            input_nombres_empleado.value = resultado.usuario.nombres;
            input_apellidos_empleado.value = resultado.usuario.apellidos;

            contenedor_perfiles.innerHTML = "";
            await actualizarDisponibilidadAsignacion();

            if (resultado.codigo === "SIN_PERFIL") {
                contenedor_perfiles.innerHTML = "";

            } else {
                resultado.perfiles.forEach((perfil) => {
                    const tarjeta = document.createElement("div");

                    tarjeta.classList.add("tarjeta_perfil_registrado");

                    tarjeta.dataset.idPerfilUsuario = perfil.id_perfil_usuario;
                    tarjeta.dataset.vigencia = perfil.vigencia;
                    tarjeta.dataset.id_perfil = perfil.id_perfil;

                    const estado = perfil.vigencia ? "Activo" : "Inactivo";

                    const clase_estado = perfil.vigencia
                        ? "perfil_habilitado"
                        : "perfil_deshabilitado";

                    const icono_estado = perfil.vigencia
                        ? "fa-circle-check"
                        : "fa-circle-xmark";

                    tarjeta.innerHTML = `
                        <div class="informacion_perfil_registrado">
                            <h4>${perfil.perfil}</h4>
                            <span>${perfil.turno}</span>

                            <div class="estado_perfil_registrado ${clase_estado}">
                                <i class="fa-solid ${icono_estado}"></i>
                                <span>${estado}</span>
                            </div>
                        </div>

                        <div class="acciones_perfil_registrado">
                            <button type="button" class="btn_gestionar_perfil">
                                <i class="fa-solid fa-gear"></i>
                                Gestionar
                            </button>
                        </div>
                    `;

                    contenedor_perfiles.appendChild(tarjeta);
                });

            }
        } catch (error) {
            console.error(error);
            await Swal.fire({
                title: "Error",
                text: "Ocurrió un error al buscar el empleado. Inténtelo nuevamente.",
                icon: "error"
            });
        }
    });

    // AL MOMENTO DE REFRESCAR LA PÁGINA DEBE MOSTRAR LOS PERFILES ASIGNADOS O MODIFICADOS

    async function perfiles_asignados() {
        try {
            const formulario = new FormData();
            formulario.append("id_empleado", input_perfil_registrar.value);

            const respuesta = await fetch("/cargar_perfiles_asignados/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector(
                        "[name=csrfmiddlewaretoken]"
                    ).value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            if (resultado.estado === "fallo") {
                btn_asignar_perfil.disabled = true;

                await Swal.fire({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon
                });

                return;
            }

            contenedor_perfiles.innerHTML = "";

            resultado.perfiles.forEach((perfil) => {
                const tarjeta = document.createElement("div");

                tarjeta.classList.add("tarjeta_perfil_registrado");

                tarjeta.dataset.idPerfilUsuario = perfil.id_registro;
                tarjeta.dataset.vigencia = perfil.vigencia;
                tarjeta.dataset.id_perfil = perfil.id_perfil;

                const estado = perfil.vigencia
                    ? "Habilitado"
                    : "Deshabilitado";

                const clase_estado = perfil.vigencia
                    ? "perfil_habilitado"
                    : "perfil_deshabilitado";

                const icono_estado = perfil.vigencia
                    ? "fa-circle-check"
                    : "fa-circle-xmark";

                tarjeta.innerHTML = `
                    <div class="informacion_perfil_registrado">
                        <h4>${perfil.perfil}</h4>
                        <span>${perfil.turno}</span>

                        <div class="estado_perfil_registrado ${clase_estado}">
                            <i class="fa-solid ${icono_estado}"></i>
                            <span>${estado}</span>
                        </div>
                    </div>

                    <div class="acciones_perfil_registrado">
                        <button type="button" class="btn_gestionar_perfil">
                            <i class="fa-solid fa-gear"></i>
                            Gestionar
                        </button>
                    </div>
                `;

                contenedor_perfiles.appendChild(tarjeta);
            });

            await actualizarDisponibilidadAsignacion();

        } catch (error) {
            console.error(error);
            btn_asignar_perfil.disabled = true;
        }
    }

    // REGISTRAR NUEVO PERFILES

    btn_asignar_perfil.addEventListener("click", async () => {
        try {
            const respuesta = await fetch("/cantidad_perfiles_asignado/");
            const resultado = await respuesta.json();
            console.log(resultado);

            if (resultado.estado == "fallo") {
                await Swal.fire({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon
                });
                return;
            }

            dialogo_asignacion.showModal();
            turno = "";
            select_turnos_registro.value = "";
            select_turnos_registro.required = false;

            Object.values(perfiles_registro).forEach(input => {
                input.checked = false;
                input.disabled = true;

                const indicador = input
                    .closest(".campo_perfil")
                    ?.querySelector(".perfil_disponible");

                if (indicador) {
                    indicador.textContent = "";
                }
            });

            await consultar_perfiles_registro();
        } catch (error) {
            console.log(error);
        }
    });

    // TURNOS LABORALES

    async function turnos_registrados() {
        try {
            const respuesta = await fetch("/turnos_registrados/");
            const resultado = await respuesta.json();
            console.log(resultado);

            select_turnos_registro.innerHTML = "<option value='' selected>Todos los turno</option>";

            resultado.forEach(turno => {
                const option_registrar = document.createElement("option");
                option_registrar.value = turno.id_turno;
                option_registrar.textContent = turno.nombre;
                select_turnos_registro.append(option_registrar);

                const option_actualizar = document.createElement("option");
                option_actualizar.value = turno.id_turno;
                option_actualizar.textContent = turno.nombre;
                select_turno_actualizar.append(option_actualizar);
            });
        } catch (error) {
            console.error(error);
        }
    }
    turnos_registrados();

    // PERFILES DISPONIBLES NO TODOS HAY ALGUNOS QUE ESTÁN DISPONIBLES

    const perfiles_registro = {
        ATENCION_CLIENTE: document.getElementById("atencion_cliente"),
        SUPERVISOR_ENCARGADO: document.getElementById("supervisor_encargado"),
        DESPACHADOR: document.getElementById("despachador"),
        PERSONAL_LIMPIEZA: document.getElementById("obrero"),
        VIGILANTE: document.getElementById("vigilante")
    };

    Object.values(perfiles_registro).forEach(input => {
        input.addEventListener("change", () => {
            select_turnos_registro.required =
                input.checked && input.value !== "ATENCION_CLIENTE";
        });
    });

    // PERFILES QUE NO TIENE ASIGNADO

    select_turnos_registro.addEventListener("change", async (E) => {
        turno = select_turnos_registro.value;

        await consultar_perfiles_registro();
    });

    async function consultar_perfiles_registro() {
        mostrar_mensaje_dialogo(
            "contenedor_mensajes_registrar",
            "Consultando los perfiles disponibles...",
            "informacion"
        );

        try {
            const formulario = new FormData();
            formulario.append("turno", turno);
            formulario.append("id_empleado", input_perfil_registrar.value);

            const respuesta = await fetch("/perfiles_usuario_no_registrados/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector(
                        "[name=csrfmiddlewaretoken]"
                    ).value
                },
                body: formulario
            });

            const resultado = await respuesta.json();

            if (!respuesta.ok || resultado.estado !== "exito") {
                await mostrar_mensaje_temporal(
                    "contenedor_mensajes_registrar",
                    resultado.mensaje || "No se pudieron consultar los perfiles.",
                    "error",
                    10
                );
                return;
            }

            resultado.perfiles.forEach(perfil => {
                const input = perfiles_registro[perfil.id_perfil];

                if (!input) return;

                const indicador = input
                    .closest(".campo_perfil")
                    ?.querySelector(".perfil_disponible");

                const asignado = perfil.asignado === true;
                const vigente = perfil.vigencia === true;

                const turnoOcupado =
                    perfil.id_perfil === "SUPERVISOR_ENCARGADO" &&
                    perfil.turno_ocupado === true;
                const atencionOcupada =
                    perfil.id_perfil === "ATENCION_CLIENTE" &&
                    perfil.ocupado === true;

                const requiereTurno =
                    perfil.id_perfil !== "ATENCION_CLIENTE";

                const perfilInactivo = asignado && !vigente;

                input.disabled =
                    asignado ||
                    atencionOcupada ||
                    turnoOcupado ||
                    (requiereTurno && !turno);

                if (indicador) {
                    if (asignado && vigente) {
                        indicador.textContent = "Ya registrado y activo";
                    } else if (perfilInactivo) {
                        indicador.textContent =
                            "Registrado inactivo; habilítelo desde gestión";
                    } else if (atencionOcupada) {
                        indicador.textContent = "Ocupado por otro empleado";
                    } else if (turnoOcupado) {
                        indicador.textContent = "Turno ocupado";
                    } else if (requiereTurno && !turno) {
                        indicador.textContent = "Seleccione un turno";
                    } else {
                        indicador.textContent = "Disponible";
                    }
                }
            });

            ocultar_mensaje_dialogo("contenedor_mensajes_registrar");

        } catch (error) {
            console.error(error);

            await mostrar_mensaje_temporal(
                "contenedor_mensajes_registrar",
                "Ocurrió un error al consultar los perfiles. Intente nuevamente.",
                "error",
                10
            );
        }
    }

    // REGISTRAR NUEVO PERFIL

    formulario_registrar.addEventListener("submit", async (e) => {
        e.preventDefault();

        if (!formulario_registrar.reportValidity()) {
            return;
        }

        const boton_submit = formulario_registrar.querySelector(
            'button[type="submit"]'
        );

        if (boton_submit.disabled) {
            return;
        }

        boton_submit.disabled = true;

        try {
            const formulario = new FormData(formulario_registrar);

            mostrar_mensaje_dialogo(
                "contenedor_mensajes_registrar",
                "Procesando la asignación del perfil...",
                "informacion"
            );

            const respuesta = await fetch("/registrar_nueva_asignacion/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector(
                        "[name=csrfmiddlewaretoken]"
                    ).value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            const tipos_mensaje = {
                success: "exito",
                warning: "advertencia",
                error: "error",
                info: "informacion"
            };

            const tipo_mensaje = tipos_mensaje[resultado.icon] || "error";

            if (!respuesta.ok || resultado.estado !== "exito") {
                await mostrar_mensaje_temporal(
                    "contenedor_mensajes_registrar",
                    resultado.descripcion ||
                    "No se pudo completar la asignación.",
                    tipo_mensaje,
                    10
                );

                return;
            }

            await mostrar_mensaje_temporal(
                "contenedor_mensajes_registrar",
                resultado.descripcion || "Perfil registrado exitosamente.",
                tipo_mensaje,
                10
            );

            dialogo_asignacion.close();

            await perfiles_asignados();
            formulario_busqueda.reset();

        } catch (error) {
            console.error(error);

            await mostrar_mensaje_temporal(
                "contenedor_mensajes_registrar",
                "Ocurrió un error al comunicarse con el servidor.",
                "error",
                10
            );

        } finally {
            boton_submit.disabled = false;
        }
    });

    // CERRAR EL DIALOGO PARA REGISTRAR EL NUEVO PERFIL

    btn_cerrar_registro.addEventListener("click", () => {
        dialogo_asignacion.close();
    });

    // ACTUALIZAR PERFIL

    contenedor_perfiles.addEventListener("click", async (e) => {
        const boton = e.target.closest(".btn_gestionar_perfil");
        if (!boton) return;

        const tarjeta = boton.closest(".tarjeta_perfil_registrado");
        if (!tarjeta) return;

        const id_perfil_usuario = tarjeta.dataset.idPerfilUsuario;
        const id_perfil = tarjeta.dataset.id_perfil;

        try {
            const formulario = new FormData();
            formulario.append("id_perfil_usuario", id_perfil_usuario);
            formulario.append("id_perfil", id_perfil);

            mostrar_mensaje_dialogo(
                "contenedor_mensajes_gestionar",
                "Consultando los datos del perfil...",
                "informacion"
            );

            const respuesta = await fetch("/buscar_datos_perfil/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken
                },
                body: formulario
            });

            const resultado = await respuesta.json();

            if (resultado.estado !== "exito") {
                const tipos_mensaje = {
                    success: "exito",
                    warning: "advertencia",
                    error: "error",
                    info: "informacion"
                };

                const tipo_mensaje = tipos_mensaje[resultado.icon] || "error";

                await mostrar_mensaje_temporal(
                    "contenedor_mensajes_gestionar",
                    resultado.descripcion || "No se pudieron consultar los datos del perfil.",
                    tipo_mensaje,
                    10
                );

                return;
            }

            input_perfil_asignado.value = resultado.id_registro;
            input_perfil_asignado.dataset.id_perfil = resultado.id_perfil;

            const option = document.createElement("option");
            option.value = resultado.id_turno ?? "";
            option.textContent = resultado.turno;
            option.selected = true;
            option.hidden = true;

            select_turno_actualizar.append(option);

            select_turno_actualizar.disabled = resultado.id_perfil === "ATENCION_CLIENTE";

            input_habilitar_perfil.checked = resultado.vigencia;
            input_deshabilitar_perfil.checked = !resultado.vigencia;

            ocultar_mensaje_dialogo("contenedor_mensajes_gestionar");

            dialogo_gestion.showModal();

        } catch (error) {
            console.error(error);

            await mostrar_mensaje_temporal(
                "contenedor_mensajes_gestionar",
                "Ocurrió un error al consultar los datos del perfil. Intente nuevamente.",
                "error",
                10
            );
        }
    });

    // GUARDAR LOS CAMBIOS REALIZADOS

    formulario_actualizar.addEventListener("submit", async (e) => {
        e.preventDefault();

        if (!formulario_actualizar.reportValidity()) {
            return;
        }

        const boton_submit = formulario_actualizar.querySelector(
            'button[type="submit"]'
        );

        if (boton_submit.disabled) {
            return;
        }

        boton_submit.disabled = true;

        try {
            const formulario = new FormData(formulario_actualizar);
            formulario.append("id_perfil", input_perfil_asignado.dataset.id_perfil);

            mostrar_mensaje_dialogo(
                "contenedor_mensajes_gestionar",
                "Actualizando el estado del perfil...",
                "informacion"
            );

            const respuesta = await fetch("/actualizar_vigencia_perfil/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            const tipos_mensaje = {
                success: "exito",
                warning: "advertencia",
                error: "error",
                info: "informacion"
            };

            const tipo_mensaje = tipos_mensaje[resultado.icon] || "error";

            if (resultado.estado !== "exito") {
                await mostrar_mensaje_temporal(
                    "contenedor_mensajes_gestionar",
                    resultado.descripcion ||
                    "No se pudo actualizar el estado del perfil.",
                    tipo_mensaje,
                    10
                );

                return;
            }

            await mostrar_mensaje_temporal(
                "contenedor_mensajes_gestionar",
                resultado.descripcion ||
                "El perfil se actualizó exitosamente.",
                tipo_mensaje,
                10
            );

            dialogo_gestion.close();

            await perfiles_asignados();

        } catch (error) {
            console.error(error);

            await mostrar_mensaje_temporal(
                "contenedor_mensajes_gestionar",
                "Ocurrió un error al comunicarse con el servidor. Intente nuevamente.",
                "error",
                10
            );

        } finally {
            boton_submit.disabled = false;
        }
    });

    // CERRAR DIALOGO

    btn_cerrar_gestion.addEventListener("click", () => {
        dialogo_gestion.close();
    });

    // FUNCIONES NOTIFICACIONES

    function mostrar_mensaje_dialogo(id_contenedor, mensaje, tipo = "informacion") {
        const contenedor = document.getElementById(id_contenedor);

        if (!contenedor) return;

        contenedor.className = `contenedor_mensajes ${tipo}`;
        contenedor.replaceChildren();

        const reloj = document.createElement("i");
        reloj.className = "fa-solid fa-hourglass-half reloj_procesamiento";
        reloj.setAttribute("aria-hidden", "true");

        const texto = document.createElement("span");
        texto.textContent = mensaje;

        contenedor.append(reloj, texto);
        contenedor.hidden = false;
    }

    function mostrar_mensaje_temporal(id_contenedor, mensaje, tipo = "exito", segundos = 4) {
        return new Promise((resolve) => {
            const contenedor = document.getElementById(id_contenedor);

            if (!contenedor) {
                resolve();
                return;
            }

            contenedor.className = `contenedor_mensajes ${tipo}`;
            contenedor.replaceChildren();

            const reloj = document.createElement("i");
            reloj.className = "fa-solid fa-hourglass-half reloj_procesamiento";
            reloj.setAttribute("aria-hidden", "true");

            const texto = document.createElement("span");
            texto.textContent = mensaje;

            const contador = document.createElement("span");
            contador.className = "contador_notificacion";
            contador.setAttribute("aria-live", "off");

            contenedor.append(reloj, texto, contador);
            contenedor.hidden = false;

            let restante = segundos;
            contador.textContent = ` ${restante} s`;

            const intervalo = setInterval(() => {
                restante--;

                if (restante <= 0) {
                    clearInterval(intervalo);
                    ocultar_mensaje_dialogo(id_contenedor);
                    resolve();
                    return;
                }

                contador.textContent = ` ${restante} s`;
            }, 1000);
        });
    }

    function ocultar_mensaje_dialogo(id_contenedor) {
        const contenedor = document.getElementById(id_contenedor);

        if (!contenedor) return;

        contenedor.hidden = true;
        contenedor.replaceChildren();
    }
});