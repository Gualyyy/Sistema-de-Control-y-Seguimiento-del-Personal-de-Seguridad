document.addEventListener("DOMContentLoaded", () => {

    const formulario_registro = document.getElementById("formulario_registrar");

    const input_nombres_usuario = document.getElementById("nombres_usuario");
    const input_apellidos_usuario = document.getElementById("apellidos_usuario");

    const input_cedula_identidad = document.getElementById("cedula_identidad");
    const select_nacionalidad = document.getElementById("nacionalidad");
    const contenedor_mensaje_ci = document.getElementById("contenedor_mensaje_ci");

    const select_prefijo_principal = document.getElementById("prefijo_principal");
    const input_num_telefono_principal = document.getElementById("num_telefono_principal");
    const contenedor_mensaje_telefono_principal = document.getElementById("contenedor_mensaje_telefono_principal");

    const select_prefijo_secundario = document.getElementById("prefijo_secundario");
    const input_num_telefono_secundario = document.getElementById("num_telefono_secundario");
    const contenedor_mensaje_telefono_secundario = document.getElementById("contenedor_mensaje_telefono_secundario");

    const input_correo_principal = document.getElementById("correo_principal");
    const select_dominio_principal = document.getElementById("dominio_principal");
    const contenedor_mensaje_correo_principal = document.getElementById("contenedor_mensaje_correo_principal");

    const input_correo_secundario = document.getElementById("correo_secundario");
    const select_dominio_secundaria = document.getElementById("dominio_secundaria");
    const contenedor_mensaje_correo_secundario = document.getElementById("contenedor_mensaje_correo_secundario");

    const select_turno_laboral = document.getElementById("turno_laboral");

    const input_encargado_administrativo = document.getElementById("encargado_administrativo");
    const input_atencion_cliente = document.getElementById("atencion_cliente");
    const input_supervisor_encargado = document.getElementById("supervisor_encargado");
    const input_despachador = document.getElementById("despachador");
    const input_vigilante = document.getElementById("vigilante");
    const input_personal_limpieza = document.getElementById("personal_limpieza");
    const contenedor_texto_mensaje_turno = document.getElementById("contenedor_texto_mensaje_turno");

    const textarea_direccion_nacimiento = document.getElementById("direccion_nacimiento");
    const contador_nacimiento = document.getElementById("contador_nacimiento");

    const textarea_direccion_domicilioo = document.getElementById("direccion_domicilio");
    const contador_residencia = document.getElementById("contador_residencia");

    configurarCorreo(input_correo_principal, select_dominio_principal);
    configurarCorreo(input_correo_secundario, select_dominio_secundaria);
    configurarTelefono(input_num_telefono_principal, select_prefijo_principal);
    configurarTelefono(input_num_telefono_secundario, select_prefijo_secundario);
    configurarCedula(input_cedula_identidad, select_nacionalidad);

    textarea_direccion_nacimiento.addEventListener("input", () => {
        textarea_direccion_nacimiento.value = textarea_direccion_nacimiento.value.replace(
            /[^a-zA-ZáéíóúÁÉÍÓÚñÑ0-9\s.,:;()\-]/g,
            ""
        );

        contador_nacimiento.textContent = textarea_direccion_nacimiento.value.length;
    });

    textarea_direccion_domicilioo.addEventListener("input", () => {
        textarea_direccion_domicilioo.value = textarea_direccion_domicilioo.value.replace(
            /[^a-zA-ZáéíóúÁÉÍÓÚñÑ0-9\s.,:;()\-]/g,
            ""
        );

        contador_residencia.textContent = textarea_direccion_domicilioo.value.length;
    });

    function soloTexto(input) {
        input.value = input.value.replace(/[^a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]/g, '');
    }

    input_nombres_usuario.addEventListener("input", function () {
        soloTexto(this);
    });

    input_apellidos_usuario.addEventListener("input", function () {
        soloTexto(this);
    });

    async function validar_ci(nacionalidad, cedula, msg) {
        if (!nacionalidad.value || !cedula.value.trim()) {
            msg.textContent = "";
            msg.classList.remove("exito", "error");

            cedula.setCustomValidity("");
            cedula.classList.remove("is-valid", "is-invalid");
            delete cedula.dataset.validando;

            return;
        }

        try {
            cedula.dataset.validando = "true";

            const formulario = new FormData();
            formulario.append("nacionalidad", nacionalidad.value);
            formulario.append("cedula", cedula.value);

            const respuesta = await fetch("/validar_ci/", {
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

            if (resultado.existe) {
                cedula.setCustomValidity(
                    "Ya se encuentra la cédula de identidad registrada."
                );

                cedula.classList.add("is-invalid");
                cedula.classList.remove("is-valid");

                msg.textContent = "Ya se encuentra la cédula de identidad registrada.";
                msg.classList.add("error");
                msg.classList.remove("exito");

            } else {
                cedula.setCustomValidity("");

                cedula.classList.add("is-valid");
                cedula.classList.remove("is-invalid");

                msg.textContent = "Cédula de Identidad disponible.";
                msg.classList.add("exito");
                msg.classList.remove("error");
            }

        } catch (error) {
            console.error("Error al validar la cédula:", error);

        } finally {
            delete cedula.dataset.validando;
        }
    }

    input_cedula_identidad.addEventListener("input", async () => {
        const nacionalidad = select_nacionalidad.value;
        const cedula = input_cedula_identidad.value.trim();

        // Sin nacionalidad o cédula vacía
        if (!nacionalidad || !cedula) {
            contenedor_mensaje_ci.textContent = "";
            contenedor_mensaje_ci.classList.remove("exito", "error"); // Limpia estilos de caja

            input_cedula_identidad.setCustomValidity("");
            input_cedula_identidad.classList.remove("is-valid", "is-invalid");
            return;
        }

        let longitudMinima;
        let longitudMaxima;

        switch (nacionalidad) {
            case "V":
                longitudMinima = 7;
                longitudMaxima = 8;
                break;
            case "E":
                longitudMinima = 8;
                longitudMaxima = 10;
                break;
            default:
                return;
        }

        // Todavía no tiene la longitud mínima o supera la máxima
        if (cedula.length < longitudMinima || cedula.length > longitudMaxima) {
            contenedor_mensaje_ci.textContent = "";
            contenedor_mensaje_ci.classList.remove("exito", "error"); // Limpia estilos de caja

            input_cedula_identidad.setCustomValidity(`La cédula debe tener entre ${longitudMinima} y ${longitudMaxima} números.`);
            input_cedula_identidad.classList.remove("is-valid");
            input_cedula_identidad.classList.add("is-invalid");
            return;
        }

        // Longitud correcta → consultar al servidor
        await validar_ci(select_nacionalidad, input_cedula_identidad, contenedor_mensaje_ci);
    });

    select_nacionalidad.addEventListener("change", async () => {
        await validar_ci(select_nacionalidad, input_cedula_identidad, contenedor_mensaje_ci);
    });

    let controlador_telefono_principal = null;
    let controlador_telefono_secundario = null;

    async function validar_telefono(prefijo, numero, msg, otro_prefijo, otro_numero, tipo) {
        const valorPrefijo = prefijo.value.trim();
        const valorNumero = numero.value.trim();

        // Cancelar petición anterior
        if (tipo === "principal") {
            if (controlador_telefono_principal) {
                controlador_telefono_principal.abort();
            }
        } else {
            if (controlador_telefono_secundario) {
                controlador_telefono_secundario.abort();
            }
        }

        // Prefijo o número vacío
        if (!valorPrefijo || !valorNumero) {
            msg.textContent = "";
            msg.classList.remove("exito", "error");

            numero.setCustomValidity("");
            numero.classList.remove("is-valid", "is-invalid");

            delete numero.dataset.validando;
            return;
        }

        // COMPROBAR SI PRINCIPAL Y SECUNDARIO SON IGUALES
        const otroPrefijo = otro_prefijo.value.trim();
        const otroNumero = otro_numero.value.trim();

        if (
            otroPrefijo &&
            otroNumero &&
            valorPrefijo === otroPrefijo &&
            valorNumero === otroNumero
        ) {
            numero.setCustomValidity(
                "El teléfono principal y secundario no pueden ser iguales."
            );

            numero.classList.add("is-invalid");
            numero.classList.remove("is-valid");

            msg.textContent = "El teléfono principal y secundario no pueden ser iguales.";
            msg.classList.add("error");
            msg.classList.remove("exito");

            delete numero.dataset.validando;
            return;
        }

        // CREAR CONTROLADOR
        const controlador = new AbortController();

        if (tipo === "principal") {
            controlador_telefono_principal = controlador;
        } else {
            controlador_telefono_secundario = controlador;
        }

        try {
            numero.dataset.validando = "true";

            const formulario = new FormData();
            formulario.append("prefijo", valorPrefijo);
            formulario.append("numeros", valorNumero);

            const respuesta = await fetch("/validar_telefono/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector(
                        "[name=csrfmiddlewaretoken]"
                    ).value
                },
                body: formulario,
                signal: controlador.signal
            });

            const resultado = await respuesta.json();
            console.log(resultado);

            // Comprobar que la petición sigue siendo la actual
            if (
                (tipo === "principal" &&
                    controlador_telefono_principal !== controlador) ||
                (tipo === "secundario" &&
                    controlador_telefono_secundario !== controlador)
            ) {
                return;
            }

            // Comprobar que los valores siguen siendo los mismos
            if (
                prefijo.value.trim() !== valorPrefijo ||
                numero.value.trim() !== valorNumero
            ) {
                return;
            }

            // TELÉFONO YA EXISTE
            if (resultado.existe) {
                numero.setCustomValidity(
                    "Ya existe un usuario con este número telefónico."
                );

                numero.classList.add("is-invalid");
                numero.classList.remove("is-valid");

                msg.textContent = "Ya existe un usuario con este número telefónico.";
                msg.classList.add("error");
                msg.classList.remove("exito");

            } else {
                numero.setCustomValidity("");

                numero.classList.add("is-valid");
                numero.classList.remove("is-invalid");

                msg.textContent = "El número telefónico está disponible.";
                msg.classList.add("exito");
                msg.classList.remove("error");
            }

        } catch (error) {
            if (error.name === "AbortError") {
                return;
            }

            console.error(error);

        } finally {
            if (
                (tipo === "principal" &&
                    controlador_telefono_principal === controlador) ||
                (tipo === "secundario" &&
                    controlador_telefono_secundario === controlador)
            ) {
                delete numero.dataset.validando;
            }
        }
    }

    // TELÉFONO PRINCIPAL
    input_num_telefono_principal.addEventListener("input", async () => {
        await validar_telefono(
            select_prefijo_principal,
            input_num_telefono_principal,
            contenedor_mensaje_telefono_principal,

            select_prefijo_secundario,
            input_num_telefono_secundario,

            "principal"
        );
    });

    select_prefijo_principal.addEventListener("change", async () => {
        await validar_telefono(
            select_prefijo_principal,
            input_num_telefono_principal,
            contenedor_mensaje_telefono_principal,

            select_prefijo_secundario,
            input_num_telefono_secundario,

            "principal"
        );
    });

    // TELÉFONO SECUNDARIO
    input_num_telefono_secundario.addEventListener("input", async () => {
        await validar_telefono(
            select_prefijo_secundario,
            input_num_telefono_secundario,
            contenedor_mensaje_telefono_secundario,

            select_prefijo_principal,
            input_num_telefono_principal,

            "secundario"
        );
    });

    select_prefijo_secundario.addEventListener("change", async () => {
        await validar_telefono(
            select_prefijo_secundario,
            input_num_telefono_secundario,
            contenedor_mensaje_telefono_secundario,

            select_prefijo_principal,
            input_num_telefono_principal,

            "secundario"
        );
    });

    let controlador_correo_principal = null;
    let controlador_correo_secundario = null;

    async function validar_correo(correo, dominio, msg, otro_correo, otro_dominio, tipo) {
        const valorCorreo = correo.value.trim().toLowerCase();
        const valorDominio = dominio.value.trim().toLowerCase();

        // CANCELAR PETICIÓN ANTERIOR DEL MISMO CORREO
        if (tipo === "principal") {
            if (controlador_correo_principal) {
                controlador_correo_principal.abort();
            }
        } else {
            if (controlador_correo_secundario) {
                controlador_correo_secundario.abort();
            }
        }

        // CORREO O DOMINIO VACÍO
        if (!valorDominio || !valorCorreo) {
            msg.textContent = "";
            msg.classList.remove("exito", "error");

            correo.setCustomValidity("");
            correo.classList.remove("is-valid", "is-invalid");

            delete correo.dataset.validando;
            return;
        }

        // COMPROBAR SI PRINCIPAL Y SECUNDARIO SON IGUALES
        const otroValorCorreo = otro_correo.value.trim().toLowerCase();
        const otroValorDominio = otro_dominio.value.trim().toLowerCase();

        if (
            otroValorCorreo &&
            otroValorDominio &&
            valorCorreo === otroValorCorreo &&
            valorDominio === otroValorDominio
        ) {
            correo.setCustomValidity(
                "El correo electrónico principal y secundario no pueden ser iguales."
            );

            correo.classList.add("is-invalid");
            correo.classList.remove("is-valid");

            msg.textContent = "El correo electrónico principal y secundario no pueden ser iguales.";
            msg.classList.add("error");
            msg.classList.remove("exito");

            delete correo.dataset.validando;
            return;
        }

        // CREAR CONTROLADOR
        const controlador = new AbortController();

        if (tipo === "principal") {
            controlador_correo_principal = controlador;
        } else {
            controlador_correo_secundario = controlador;
        }

        try {
            correo.dataset.validando = "true";

            const formulario = new FormData();
            formulario.append("correo", valorCorreo);
            formulario.append("dominio", valorDominio);

            const respuesta = await fetch("/validar_email/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector(
                        "[name=csrfmiddlewaretoken]"
                    ).value
                },
                body: formulario,
                signal: controlador.signal
            });

            const resultado = await respuesta.json();
            console.log(resultado);

            // COMPROBAR QUE LA PETICIÓN SIGUE SIENDO LA ACTUAL
            if (
                (tipo === "principal" &&
                    controlador_correo_principal !== controlador) ||
                (tipo === "secundario" &&
                    controlador_correo_secundario !== controlador)
            ) {
                return;
            }

            // COMPROBAR QUE LOS VALORES NO CAMBIARON
            if (
                correo.value.trim().toLowerCase() !== valorCorreo ||
                dominio.value.trim().toLowerCase() !== valorDominio
            ) {
                return;
            }

            // CORREO YA EXISTE
            if (resultado.existe) {
                correo.setCustomValidity(
                    "Ya existe un usuario con este correo electrónico."
                );

                correo.classList.add("is-invalid");
                correo.classList.remove("is-valid");

                msg.textContent = "Ya existe un usuario con este correo electrónico.";
                msg.classList.add("error");
                msg.classList.remove("exito");

            } else {
                correo.setCustomValidity("");

                correo.classList.add("is-valid");
                correo.classList.remove("is-invalid");

                msg.textContent = "El correo electrónico está disponible.";
                msg.classList.add("exito");
                msg.classList.remove("error");
            }

        } catch (error) {
            if (error.name === "AbortError") {
                return;
            }

            console.error(error);

        } finally {
            if (
                (tipo === "principal" &&
                    controlador_correo_principal === controlador) ||
                (tipo === "secundario" &&
                    controlador_correo_secundario === controlador)
            ) {
                delete correo.dataset.validando;
            }
        }
    }

    // CORREO PRINCIPAL
    input_correo_principal.addEventListener("input", async () => {
        await validar_correo(
            input_correo_principal,
            select_dominio_principal,
            contenedor_mensaje_correo_principal,

            input_correo_secundario,
            select_dominio_secundaria,

            "principal"
        );
    });

    select_dominio_principal.addEventListener("change", async () => {
        await validar_correo(
            input_correo_principal,
            select_dominio_principal,
            contenedor_mensaje_correo_principal,

            input_correo_secundario,
            select_dominio_secundaria,

            "principal"
        );
    });

    // CORREO SECUNDARIO
    input_correo_secundario.addEventListener("input", async () => {
        await validar_correo(
            input_correo_secundario,
            select_dominio_secundaria,
            contenedor_mensaje_correo_secundario,

            input_correo_principal,
            select_dominio_principal,

            "secundario"
        );
    });

    select_dominio_secundaria.addEventListener("change", async () => {
        await validar_correo(
            input_correo_secundario,
            select_dominio_secundaria,
            contenedor_mensaje_correo_secundario,

            input_correo_principal,
            select_dominio_principal,

            "secundario"
        );
    });

    async function turnos_registrados() {
        try {
            const respuesta = await fetch("/turnos_registrados/");
            const resultado = await respuesta.json();
            console.log(resultado);

            select_turno_laboral.innerHTML = '<option value="Turno Completo" selected> Todos los Turnos Laborales</option>';

            resultado.forEach(turno => {
                const option = document.createElement("option");
                option.value = turno.id_turno;
                option.textContent = turno.nombre;
                select_turno_laboral.append(option);
            });

            await Promise.all([
                perfiles_sin_turno_registrados(),
                perfiles_registrados(select_turno_laboral.value)
            ]);
        } catch (error) {
            console.error(error);
        }
    }
    turnos_registrados();

    select_turno_laboral.addEventListener("change", async () => {
        await perfiles_registrados(select_turno_laboral.value);
    });

    // PERFILES QUE NO REQUIEREN TURNO
    async function perfiles_sin_turno_registrados() {
        try {
            const respuesta = await fetch("/perfiles_sin_turno_registrados/");
            const resultado = await respuesta.json();
            console.log(resultado);

            // Encargado Administrativo
            actualizar_estado_perfil(input_encargado_administrativo, resultado.encargado_administrativo_registrado);

            // Atención al Cliente
            actualizar_estado_perfil(input_atencion_cliente, resultado.atencion_cliente_registrada);
        } catch (error) {
            console.error(error);

            [
                input_encargado_administrativo,
                input_atencion_cliente
            ].forEach(input => {
                if (input) {
                    input.disabled = true;
                    input.checked = false;
                }
            });
        }
    }


    // PERFILES QUE REQUIEREN TURNO
    async function perfiles_registrados(turnoId) {
        if (turnoId === "Turno Completo") {
            contenedor_texto_mensaje_turno.textContent = "Seleccione un perfil disponible para el turno completo.";

            [
                input_supervisor_encargado,
                input_despachador,
                input_vigilante,
                input_personal_limpieza
            ].forEach(input => {
                if (input) {
                    input.disabled = true;
                    input.checked = false;
                }
            });

            [
                input_supervisor_encargado,
                input_despachador,
                input_vigilante,
                input_personal_limpieza
            ].forEach(input => {
                const span = input?.parentElement.querySelector(".estado_perfil");

                if (span) {
                    span.textContent = "";
                }
            });

            return;
        }

        if (!turnoId) {
            desactivarPerfilesConTurno("Seleccione un turno para mostrar los perfiles disponibles.");
            return;
        }

        try {
            const formulario = new FormData();
            formulario.append("turno", turnoId);

            const respuesta = await fetch("/perfiles_disponibles_registro/", {
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

            if (resultado.estado !== "exito") {
                desactivarPerfilesConTurno(resultado.descripcion);
                return;
            }

            contenedor_texto_mensaje_turno.textContent = "Seleccione un perfil para el turno laboral seleccionado.";

            // Supervisor Encargado
            actualizar_estado_perfil(
                input_supervisor_encargado,
                resultado.supervisor_encargado_registrado
            );

            // Perfiles múltiples
            [
                input_despachador,
                input_vigilante,
                input_personal_limpieza
            ].forEach(input => {
                if (input) {
                    input.disabled = false;
                    input.checked = false;

                    const span = input.parentElement.querySelector(".estado_perfil");

                    if (span) {
                        span.textContent = "";
                    }
                }
            });

        } catch (error) {
            console.error(error);
            desactivarPerfilesConTurno("Error de conexión al consultar los perfiles.");
        }
    }

    // ACTUALIZAR ESTADO DE UN PERFIL
    function actualizar_estado_perfil(input, registrado) {
        if (!input) {
            return;
        }

        input.disabled = registrado;
        input.checked = false;

        const span = input.parentElement.querySelector(".estado_perfil");

        if (span) {
            span.textContent = registrado ? "(Ya registrado)" : "";
        }
    }

    // DESACTIVAR PERFILES QUE REQUIEREN TURNO
    function desactivarPerfilesConTurno(mensaje) {
        contenedor_texto_mensaje_turno.textContent = mensaje;

        [
            input_supervisor_encargado,
            input_despachador,
            input_vigilante,
            input_personal_limpieza
        ].forEach(input => {

            if (input) {
                input.disabled = true;
                input.checked = false;

                const span = input.parentElement.querySelector(".estado_perfil");

                if (span) {
                    span.textContent = "";
                }
            }
        });
    }

    const navegacion = configurarDesplazamientoPasos(formulario_registro);

    formulario_registro.addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
            const formulario = new FormData(formulario_registro);

            const respuesta = await fetch("/registro_usuarios/", {
                method: "POST",
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            await Swal.fire({
                title: resultado.title,
                text: resultado.descripcion,
                icon: resultado.icon
            });

            if (resultado.estado != "exito") return;

            formulario_registro.reset();
            navegacion.reiniciar();


            contenedor_mensaje_ci.innerHTML = "";
            contenedor_mensaje_correo_principal.innerHTML = "";
            contenedor_mensaje_correo_secundario.innerHTML = "";
            contenedor_mensaje_telefono_principal.innerHTML = "";
            contenedor_mensaje_telefono_secundario.innerHTML = "";

            turno = "";
            select_turno_laboral.selectedIndex = 0;

            await Promise.all([
                perfiles_sin_turno_registrados(),
                perfiles_registrados(select_turno_laboral.value)
            ]);
        } catch (error) {
            console.error(error);
        }
    });
});