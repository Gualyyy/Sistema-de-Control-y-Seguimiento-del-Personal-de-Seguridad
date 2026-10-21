document.addEventListener("DOMContentLoaded", () => {

    const contenedor_supervisor_diurno = document.getElementById("contenedor_supervisor_diurno");
    const contenedor_supervisor_nocturno = document.getElementById("contenedor_supervisor_nocturno");

    const lista_supervisores_diurnos = document.getElementById("lista_supervisores_diurnos");
    const lista_supervisores_nocturnos = document.getElementById("lista_supervisores_nocturnos");

    const formulario_registrar = document.getElementById("formulario_registrar");
    const input_supervisor_registrar = document.getElementById("supervisor_registrar");

    const input_nombre_usuario_registrar = document.getElementById("nombre_usuario_registrar");
    const contenedor_mensaje_nombre_registrar = document.getElementById("contenedor_mensaje_nombre_registrar");
    const input_clave_registrar = document.getElementById("clave_registrar");
    const contenedor_mensaje_password_registrar = document.getElementById("contenedor_mensaje_password_registrar");

    const dialogo_registrar = document.getElementById("dialogo_registrar");
    const btn_cerrar_registrar = document.getElementById("btn_cerrar_registrar");

    const formulario_actualizar = document.getElementById("formulario_actualizar");
    const input_supervisor_actualizar = document.getElementById("supervisor_actualizar");

    const input_nombre_usuario_actualizar = document.getElementById("nombre_usuario_actualizar");
    const contenedor_mensaje_nombre_actualizar = document.getElementById("contenedor_mensaje_nombre_actualizar");
    const input_clave_actualizar = document.getElementById("clave_actualizar");
    const contenedor_mensaje_password_actualizar = document.getElementById("contenedor_mensaje_password_actualizar");

    const dialogo_actualizar = document.getElementById("dialogo_actualizar");
    const btn_cerrar_actualizar = document.getElementById("btn_cerrar_actualizar");

    configurarContrasenia(formulario_registrar.querySelector(".password_contenedor"));
    configurarContrasenia(formulario_actualizar.querySelector(".password_contenedor"));

    function obtener_csrf_token() {
        const nombre = "csrftoken=";
        const cookies = document.cookie.split(";");

        for (let cookie of cookies) {
            cookie = cookie.trim();

            if (cookie.startsWith(nombre)) {
                return decodeURIComponent(cookie.substring(nombre.length));
            }
        }
        return null;
    }

    // VALIDACIONES

    let controlador_nombre_usuario_registrar = null;
    let controlador_nombre_usuario_actualizar = null;

    async function validar_nombre_usuario(input, msg, tipo) {
        const valor = input.value.trim();

        // Seleccionar controlador según el formulario
        let controlador_actual;

        if (tipo === "registrar") {
            controlador_actual = controlador_nombre_usuario_registrar;
        } else {
            controlador_actual = controlador_nombre_usuario_actualizar;
        }

        // Cancelar petición anterior del mismo campo
        if (controlador_actual) {
            controlador_actual.abort();
        }

        // CAMPO VACÍO
        if (!valor) {
            msg.textContent = "";
            msg.classList.remove("exito", "error", "espera");
            input.setCustomValidity("Debe ingresar un nombre de usuario.");
            input.classList.remove("is-valid", "is-invalid");
            return false;
        }

        // ESTADO: VERIFICANDO
        msg.textContent = "Verificando nombre de usuario...";
        msg.classList.add("espera");
        msg.classList.remove("exito", "error");

        input.classList.remove("is-valid", "is-invalid");
        input.setCustomValidity("Espere mientras se verifica el nombre de usuario.");

        // Crear controlador
        const controlador = new AbortController();

        if (tipo === "registrar") {
            controlador_nombre_usuario_registrar = controlador;
        } else {
            controlador_nombre_usuario_actualizar = controlador;
        }

        try {
            const formulario = new FormData();
            formulario.append("nombre_usuario", valor);

            // Si es registrar, enviar el usuario actual
            if (tipo === "registrar") {
                formulario.append("id_usuario", input_supervisor_registrar.value);
            }

            // Si es actualización, enviar el usuario actual
            if (tipo === "actualizar") {
                formulario.append("id_usuario", input_supervisor_actualizar.value);
            }

            const respuesta = await fetch("/validar_nombre_usuario/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": obtener_csrf_token()
                },
                body: formulario,
                signal: controlador.signal
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            // Comprobar que el valor no haya cambiado
            if (input.value.trim() !== valor) {
                return false;
            }

            // NOMBRE YA EXISTE
            if (resultado.existe) {
                input.setCustomValidity("Este nombre de usuario ya está registrado.");
                input.classList.add("is-invalid");
                input.classList.remove("is-valid");

                msg.textContent = "Este nombre de usuario ya está registrado.";
                msg.classList.add("error");
                msg.classList.remove("exito", "espera");
                return false;
            }

            // NOMBRE DISPONIBLE
            input.setCustomValidity("");
            input.classList.add("is-valid");
            input.classList.remove("is-invalid");

            msg.textContent = "El nombre de usuario está disponible.";
            msg.classList.add("exito");
            msg.classList.remove("error", "espera");
            return true;

        } catch (error) {
            if (error.name === "AbortError") {
                return false;
            }

            input.setCustomValidity("No se pudo verificar el nombre de usuario.");

            msg.textContent = "No se pudo verificar el nombre de usuario.";
            msg.classList.add("error");
            msg.classList.remove("exito", "espera");

            console.error(error);
            return false;
        }
    }

    input_nombre_usuario_registrar.addEventListener("input", async () => {
        await validar_nombre_usuario(input_nombre_usuario_registrar, contenedor_mensaje_nombre_registrar, "registrar");
    });

    input_nombre_usuario_actualizar.addEventListener("input", async () => {
        await validar_nombre_usuario(input_nombre_usuario_actualizar, contenedor_mensaje_nombre_actualizar, "actualizar");
    });

    let controlador_contrasenia_registrar = null;
    let controlador_contrasenia_actualizar = null;

    async function validar_contrasenia(input, msg, tipo) {
        const valor = input.value.trim();

        // Seleccionar controlador según el formulario
        let controlador_actual;

        if (tipo === "registrar") {
            controlador_actual = controlador_contrasenia_registrar;
        } else {
            controlador_actual = controlador_contrasenia_actualizar;
        }

        // Cancelar petición anterior del mismo campo
        if (controlador_actual) {
            controlador_actual.abort();
        }

        // Campo vacío
        if (!valor) {
            msg.textContent = "";
            msg.classList.remove("exito", "error", "espera");
            input.setCustomValidity("Debe ingresar una contraseña.");
            input.classList.remove("is-valid", "is-invalid");
            return false;
        }

        // Mientras se verifica
        msg.textContent = "Verificando contraseña...";
        msg.classList.add("espera");
        msg.classList.remove("exito", "error");
        input.classList.remove("is-valid", "is-invalid");
        input.setCustomValidity("Espere mientras se verifica la contraseña.");

        // Crear controlador
        const controlador = new AbortController();

        if (tipo === "registrar") {
            controlador_contrasenia_registrar = controlador;
        } else {
            controlador_contrasenia_actualizar = controlador;
        }

        try {
            const formulario = new FormData();
            formulario.append("clave", valor);

            // Si es registrar, enviar el usuario actual
            if (tipo === "registrar") {
                formulario.append("id_usuario", input_supervisor_registrar.value);
            }

            // Si es actualización, enviar el usuario actual
            if (tipo === "actualizar") {
                formulario.append("id_usuario", input_supervisor_actualizar.value);
            }

            const respuesta = await fetch("/validar_contrasenia/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": obtener_csrf_token()
                },
                body: formulario,
                signal: controlador.signal
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            // Comprobar que la contraseña no haya cambiado
            if (input.value.trim() !== valor) {
                return false;
            }

            // CONTRASEÑA YA EXISTE
            if (resultado.existe) {
                input.setCustomValidity("Esta contraseña ya está registrada.");
                input.classList.add("is-invalid");
                input.classList.remove("is-valid");

                msg.textContent = "Esta contraseña ya está registrada.";
                msg.classList.add("error");
                msg.classList.remove("exito", "espera");
                return false;
            }

            // CONTRASEÑA DISPONIBLE
            input.setCustomValidity("");
            input.classList.add("is-valid");
            input.classList.remove("is-invalid");

            msg.textContent = "La contraseña está disponible.";
            msg.classList.add("exito");
            msg.classList.remove("error", "espera");
            return true;

        } catch (error) {
            if (error.name === "AbortError") {
                return false;
            }

            input.setCustomValidity("No se pudo verificar la contraseña.");
            msg.textContent = "No se pudo verificar la contraseña.";
            msg.classList.add("error");
            msg.classList.remove("exito", "espera");

            console.error(error);
            return false;
        }
    }

    input_clave_registrar.addEventListener("input", async () => {
        await validar_contrasenia(input_clave_registrar, contenedor_mensaje_password_registrar, "registrar");
    });

    input_clave_actualizar.addEventListener("input", async () => {
        await validar_contrasenia(input_clave_actualizar, contenedor_mensaje_password_actualizar, "actualizar");
    });

    // SUPERVISORES REGISTRADOS

    async function supervisores_registrados() {
        try {
            const respuesta = await fetch("/supervisores_registrados/");
            const resultado = await respuesta.json();
            console.log(resultado);

            const supervisores = resultado.supervisores || [];

            const diurnos = supervisores.filter(
                supervisor => supervisor.turno === "Diurno"
            );

            const nocturnos = supervisores.filter(
                supervisor => supervisor.turno === "Nocturno"
            );

            rellenar_supervisor(
                contenedor_supervisor_diurno,
                lista_supervisores_diurnos,
                diurnos
            );

            rellenar_supervisor(
                contenedor_supervisor_nocturno,
                lista_supervisores_nocturnos,
                nocturnos
            );

        } catch (error) {
            console.error(error);
        }
    }
    supervisores_registrados();

    function rellenar_supervisor(contenedor, lista, supervisores) {
        const mensaje = contenedor.querySelector(".supervisor_no_registrado");
        const tarjetas = lista.querySelectorAll("[data-supervisor-card]");

        const supervisor = supervisores[0];
        if (!supervisor) {
            if (mensaje) {
                mensaje.hidden = false;
            }

            tarjetas.forEach(tarjeta => {
                tarjeta.hidden = true;
            });
            return;
        }

        if (mensaje) {
            mensaje.hidden = true;
        }

        const tarjeta = tarjetas[0];
        tarjeta.hidden = false;

        const iniciales = (supervisor.nombres?.charAt(0) || "") + (supervisor.apellidos?.charAt(0) || "");

        tarjeta.querySelector('[data-campo="iniciales"]').textContent = iniciales.toUpperCase();
        tarjeta.querySelector('[data-campo="nombre_completo"]').textContent = `${supervisor.nombres || ""} ${supervisor.apellidos || ""}`.trim();

        const estado = tarjeta.querySelector('[data-campo="estado"]');
        estado.textContent = supervisor.bloqueado ? "Supervisor Bloqueado" : "Encargado Activo";

        estado.classList.toggle("estado_bloqueado", supervisor.bloqueado);
        estado.classList.toggle("estado_activo", !supervisor.bloqueado);

        const boton_actualizar = tarjeta.querySelector(".btn_actualizar_supervisor");
        if (boton_actualizar) {
            boton_actualizar.dataset.id = supervisor.id_usuario;
        }

        const boton_bloqueo = tarjeta.querySelector(".btn_bloquear, .btn_desbloquear");
        if (boton_bloqueo) {
            boton_bloqueo.dataset.id = supervisor.id_usuario;
            boton_bloqueo.dataset.bloqueado = String(!supervisor.bloqueado);

            if (supervisor.bloqueado) {
                boton_bloqueo.classList.remove("btn_bloquear");
                boton_bloqueo.classList.add("btn_desbloquear");
                boton_bloqueo.textContent = "Desbloquear";
            } else {
                boton_bloqueo.classList.remove("btn_desbloquear");
                boton_bloqueo.classList.add("btn_bloquear");
                boton_bloqueo.textContent = "Bloquear";
            }
        }

        const boton_credenciales = tarjeta.querySelector(".btn_credenciales, .btn_credenciales_registradas");
        if (boton_credenciales) {
            boton_credenciales.dataset.id = supervisor.id_usuario;

            if (supervisor.tiene_credenciales) {
                boton_credenciales.classList.remove("btn_credenciales");
                boton_credenciales.classList.add("btn_credenciales_registradas");
                boton_credenciales.textContent = "Credenciales registradas";
            } else {
                boton_credenciales.classList.remove("btn_credenciales_registradas");
                boton_credenciales.classList.add("btn_credenciales");
                boton_credenciales.textContent = "Registrar credenciales";
            }
        }
    }

    // ACTIVAR LOS DIALOGOS

    document.addEventListener("click", async (e) => {

        // BLOQUEAR / DESBLOQUEAR
        const boton_bloqueo = e.target.closest(".btn_bloquear, .btn_desbloquear");

        if (boton_bloqueo) {
            const id_supervisor = boton_bloqueo.dataset.id;

            if (!id_supervisor) {
                await Swal.fire({
                    title: "Supervisor no registrado",
                    text: "No se puede realizar esta acción porque el supervisor no está registrado.",
                    icon: "warning"
                });
                return;
            }

            const bloqueado = boton_bloqueo.dataset.bloqueado === "true";

            await bloquear_supervisor(id_supervisor, bloqueado);
            return;
        }

        // ACTUALIZAR SUPERVISOR
        const boton_actualizar = e.target.closest(".btn_actualizar_supervisor");

        if (boton_actualizar) {
            const id_supervisor = boton_actualizar.dataset.id;

            if (!id_supervisor) {
                await Swal.fire({
                    title: "Supervisor no registrado",
                    text: "No se puede realizar esta acción porque el supervisor no está registrado.",
                    icon: "warning"
                });
                return;
            }

            input_supervisor_actualizar.value = id_supervisor;
            dialogo_actualizar.showModal();
            return;
        }

        // REGISTRAR CREDENCIALES
        const boton_credenciales = e.target.closest(".btn_credenciales");

        if (boton_credenciales) {
            const id_supervisor = boton_credenciales.dataset.id;

            if (!id_supervisor) {
                await Swal.fire({
                    title: "Supervisor no registrado",
                    text: "No se puede realizar esta acción porque el supervisor no está registrado.",
                    icon: "warning"
                });
                return;
            }

            input_supervisor_registrar.value = id_supervisor;
            dialogo_registrar.showModal();
            return;
        }
    });

    // MODULOS

    async function bloquear_supervisor(id_supervisor, bloqueado) {
        try {
            const formulario = new FormData();
            formulario.append("id_usuario", id_supervisor);
            formulario.append("bloqueado", bloqueado);

            const respuesta = await fetch("/bloquear_supervisor/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": obtener_csrf_token()
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            await Swal.fire({
                title: resultado.title,
                text: resultado.descripcion,
                icon: resultado.icon
            });

            await supervisores_registrados();
        } catch (error) {
            console.error(error);
        }
    }

    function limpiar_validacion_credenciales() {
        const campos = [
            {
                input: input_nombre_usuario_registrar,
                mensaje: contenedor_mensaje_nombre_registrar
            },
            {
                input: input_clave_registrar,
                mensaje: contenedor_mensaje_password_registrar
            },
            {
                input: input_nombre_usuario_actualizar,
                mensaje: contenedor_mensaje_nombre_actualizar
            },
            {
                input: input_clave_actualizar,
                mensaje: contenedor_mensaje_password_actualizar
            }
        ];

        campos.forEach(({ input, mensaje }) => {
            if (mensaje) {
                mensaje.textContent = "";
                mensaje.classList.remove("exito", "error", "espera");
            }

            if (input) {
                input.classList.remove("is-valid", "is-invalid");
                input.setCustomValidity("");
            }
        });
    }

    formulario_registrar.addEventListener("submit", async (e) => {
        e.preventDefault();

        const boton = formulario_registrar.querySelector('button[type="submit"]');

        if (boton.disabled) return;

        boton.disabled = true;

        try {
            const formulario = new FormData(formulario_registrar);

            mostrar_mensaje_dialogo(
                "contenedor_mensajes_registrar",
                "Procesando el registro...",
                "informacion"
            );

            const respuesta = await fetch("/credenciales_supervisor/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": obtener_csrf_token()
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            await mostrar_mensaje_temporal(
                "contenedor_mensajes_registrar",
                resultado.descripcion,
                resultado.tipo_mensaje,
                4
            );

            ocultar_mensaje_dialogo("contenedor_mensajes_registrar");

            dialogo_registrar.close();

            await supervisores_registrados();

            limpiar_validacion_credenciales();
            formulario_registrar.reset();
        } catch (error) {
            console.error(error);

            ocultar_mensaje_dialogo("contenedor_mensajes_registrar");
        } finally {
            boton.disabled = false;
        }
    });

    formulario_actualizar.addEventListener("submit", async (e) => {
        e.preventDefault();

        const boton = formulario_actualizar.querySelector('button[type="submit"]');

        if (boton.disabled) return;

        boton.disabled = true;

        try {
            const formulario = new FormData(formulario_actualizar);

            mostrar_mensaje_dialogo(
                "contenedor_mensajes_actualizar",
                "Procesando la actualización...",
                "informacion"
            );

            const respuesta = await fetch("/actualizar_credenciales_supervisor/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": obtener_csrf_token()
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            await mostrar_mensaje_temporal(
                "contenedor_mensajes_actualizar",
                resultado.descripcion,
                resultado.tipo_mensaje,
                4
            );

            ocultar_mensaje_dialogo("contenedor_mensajes_actualizar");

            dialogo_actualizar.close();

            await supervisores_registrados();

            limpiar_validacion_credenciales();
            formulario_actualizar.reset();
        } catch (error) {
            console.error(error);

            ocultar_mensaje_dialogo("contenedor_mensajes_actualizar");
        } finally {
            boton.disabled = false;
        }
    });

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

    function limpiar_formulario(formulario) {
        formulario.reset();

        // Limpiar inputs con validación
        formulario.querySelectorAll("input, select, textarea").forEach(campo => {
            campo.setCustomValidity("");
            campo.classList.remove(
                "is-valid",
                "is-invalid"
            );
        });

        // Limpiar mensajes
        formulario.querySelectorAll(".mensaje-feedback").forEach(mensaje => {
            mensaje.textContent = "";

            mensaje.classList.remove(
                "exito",
                "error",
                "espera"
            );
        });
    }

    // CERRAR DIALOGOS

    btn_cerrar_registrar.addEventListener("click", () => {
        limpiar_formulario(formulario_registrar);

        dialogo_registrar.close();
    });

    btn_cerrar_actualizar.addEventListener("click", () => {
        limpiar_formulario(formulario_actualizar);

        dialogo_actualizar.close();
    });

});