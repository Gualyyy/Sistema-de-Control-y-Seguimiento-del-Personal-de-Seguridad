document.addEventListener("DOMContentLoaded", () => {

    const formulario_registro = document.getElementById("formulario_registrar");

    const input_cedula_identidad = document.getElementById("cedula_identidad");
    const select_nacionalidad = document.getElementById("nacionalidad");
    const contenedor_mensaje_ci = document.getElementById("contenedor_mensaje_ci");

    const input_nombre_usuario = document.getElementById("nombre_usuario");
    const contenedor_mensaje_usuario = document.getElementById("contenedor_mensaje_nombre_usuario");

    const input_clave = document.getElementById("clave");
    const contenedor_mensaje_password = document.getElementById("contenedor_mensaje_password");

    const select_prefijo_telefono = document.getElementById("prefijo_telefono");
    const input_numero_telefonico = document.getElementById("numero_telefonico");

    const input_correo = document.getElementById("correo");
    const select_dominio = document.getElementById("dominio");
    const contenedor_mensaje_correo = document.getElementById("contenedor_mensaje_correo");

    const input_nombres_usuario = document.getElementById("nombres_usuario");
    const input_apellidos_usuario = document.getElementById("apellidos_usuario");

    const barra_fortaleza = document.querySelector(".barra_fortaleza");
    const texto_fortaleza = document.querySelector(".texto_fortaleza");

    const select_turno_laboral = document.getElementById("turno_laboral");
    const contenedor_perfiles = document.getElementById("contenedor_perfiles");
    const contenedor_mensaje_turno = document.getElementById("contenedor_mensaje_turno");
    const contenedor_texto_mensaje_turno = document.getElementById("contenedor_texto_mensaje_turno");

    configurarCorreo(input_correo, select_dominio);
    configurarTelefono(input_numero_telefonico, select_prefijo_telefono);
    configurarCedula(input_cedula_identidad, select_nacionalidad);

    let turno = "";

    function evaluarContrasenia(contraseña) {
        let puntos = 0;

        if (contraseña.length >= 5) puntos++;
        if (contraseña.length >= 8) puntos++;
        if (/[a-z]/.test(contraseña)) puntos++;
        if (/[A-Z]/.test(contraseña)) puntos++;
        if (/[0-9]/.test(contraseña)) puntos++;
        if (/[^a-zA-Z0-9]/.test(contraseña)) puntos++;

        return puntos;
    }

    function actualizarFortalezaContrasenia() {
        const clave = input_clave.value;
        const puntos = evaluarContrasenia(clave);

        const contenedorFortaleza = document.querySelector(".fortaleza_contrasenia");

        contenedorFortaleza.classList.remove(
            "debil",
            "media",
            "fuerte",
            "sin_fortaleza"
        );

        if (!clave) {
            contenedorFortaleza.classList.add("sin_fortaleza");
            texto_fortaleza.textContent = "";
            input_clave.setCustomValidity("");
            return;
        }

        if (puntos <= 2) {
            contenedorFortaleza.classList.add("debil");
            texto_fortaleza.textContent = "Contraseña débil";
        } else if (puntos <= 4) {
            contenedorFortaleza.classList.add("media");
            texto_fortaleza.textContent = "Contraseña media";
        } else {
            contenedorFortaleza.classList.add("fuerte");
            texto_fortaleza.textContent = "Contraseña fuerte";
        }
    }

    input_clave.addEventListener("input", actualizarFortalezaContrasenia);

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
            return;
        }

        try {
            const formulario = new FormData();
            formulario.append("nacionalidad", nacionalidad.value);
            formulario.append("cedula", cedula.value);

            const respuesta = await fetch("/validar_ci/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            if (resultado.existe) {
                // Manejo del campo de texto
                cedula.setCustomValidity("Ya se encuentra la cédula de identidad registrada.");
                cedula.classList.add("is-invalid");
                cedula.classList.remove("is-valid");

                // Manejo del mensaje visual
                msg.textContent = "Ya se encuentra la cédula de identidad registrada.";
                msg.classList.add("error");
                msg.classList.remove("exito");
            } else {
                // Manejo del campo de texto
                cedula.setCustomValidity("");
                cedula.classList.add("is-valid");
                cedula.classList.remove("is-invalid");

                // Manejo del mensaje visual
                msg.textContent = "Cédula de Identidad disponible.";
                msg.classList.add("exito");
                msg.classList.remove("error");
            }
        } catch (error) {
            console.error("Error al validar la cédula:", error);
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

    let controlador_correo = null;

    async function validar_correo(correo, dominio, msg) {
        const valorCorreo = correo.value.trim();
        const valorDominio = dominio.value;

        if (controlador_correo) { // Cancelar petición anterior
            controlador_correo.abort();
        }

        if (!valorDominio || !valorCorreo) { // Correo o dominio vacío
            msg.textContent = "";
            msg.classList.remove("exito", "error");

            correo.setCustomValidity("");
            correo.classList.remove("is-valid", "is-invalid");
            return;
        }

        controlador_correo = new AbortController();

        try {
            const formulario = new FormData();
            formulario.append("correo", valorCorreo);
            formulario.append("dominio", valorDominio);

            const respuesta = await fetch("/validar_email/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario,
                signal: controlador_correo.signal
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            // Comprobar que correo y dominio siguen siendo los mismos
            if (correo.value.trim() !== valorCorreo || dominio.value !== valorDominio) {
                return;
            }

            if (resultado.existe) {
                correo.setCustomValidity("Ya existe un usuario con este correo electrónico.");
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
        }
    }

    input_correo.addEventListener("input", async () => {
        await validar_correo(input_correo, select_dominio, contenedor_mensaje_correo);
    });

    select_dominio.addEventListener("change", async () => {
        await validar_correo(input_correo, select_dominio, contenedor_mensaje_correo);
    });

    // Validar Nombre Usuario
    let controlador_nombre_usuario = null;

    async function validar_nombre_usuario() {
        const nombre_usuario = input_nombre_usuario.value.trim();
        if (controlador_nombre_usuario) { // Cancelar petición anterior
            controlador_nombre_usuario.abort();
        }

        // Campo vacío
        if (!nombre_usuario) {
            contenedor_mensaje_usuario.textContent = "";
            contenedor_mensaje_usuario.classList.remove("exito", "error");

            input_nombre_usuario.setCustomValidity("");
            input_nombre_usuario.classList.remove("is-valid", "is-invalid");
            return;
        }
        controlador_nombre_usuario = new AbortController();

        try {
            const formulario = new FormData();
            formulario.append("nombre_usuario", nombre_usuario);

            const respuesta = await fetch("/validar_nombre_usuario/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario,
                signal: controlador_nombre_usuario.signal
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            if (input_nombre_usuario.value.trim() !== nombre_usuario) {
                return;
            }

            if (resultado.existe) {
                input_nombre_usuario.setCustomValidity("Ya existe un nombre de usuario.");
                input_nombre_usuario.classList.add("is-invalid");
                input_nombre_usuario.classList.remove("is-valid");

                contenedor_mensaje_usuario.textContent = "Ya existe un nombre de usuario.";
                contenedor_mensaje_usuario.classList.add("error");
                contenedor_mensaje_usuario.classList.remove("exito");
            } else {
                input_nombre_usuario.setCustomValidity("");
                input_nombre_usuario.classList.add("is-valid");
                input_nombre_usuario.classList.remove("is-invalid");

                contenedor_mensaje_usuario.textContent = "El nombre de usuario está disponible.";
                contenedor_mensaje_usuario.classList.add("exito");
                contenedor_mensaje_usuario.classList.remove("error");
            }
        } catch (error) {
            if (error.name === "AbortError") {
                return;
            }
            console.error(error);
        }
    }

    input_nombre_usuario.addEventListener("input", validar_nombre_usuario);

    // Validar Contraseña
    let controlador_contrasenia = null;

    async function validar_contrasenia() {
        const clave = input_clave.value.trim();

        // Cancelar petición anterior
        if (controlador_contrasenia) {
            controlador_contrasenia.abort();
        }

        // Campo vacío
        if (!clave) {
            contenedor_mensaje_password.textContent = "";
            contenedor_mensaje_password.classList.remove("exito", "error");

            input_clave.setCustomValidity("");
            input_clave.classList.remove("is-valid", "is-invalid");
            return;
        }

        controlador_contrasenia = new AbortController();

        try {
            const formulario = new FormData();
            formulario.append("clave", input_clave.value);

            const respuesta = await fetch("/validar_contrasenia/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario,
                signal: controlador_contrasenia.signal
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            // El usuario cambió la contraseña mientras se esperaba la respuesta
            if (input_clave.value.trim() !== clave) {
                return;
            }

            if (resultado.existe) {
                input_clave.setCustomValidity("Ya se encuentra la contraseña registrada.");
                input_clave.classList.add("is-invalid");
                input_clave.classList.remove("is-valid");

                contenedor_mensaje_password.textContent = "Ya se encuentra la contraseña registrada.";
                contenedor_mensaje_password.classList.add("error");
                contenedor_mensaje_password.classList.remove("exito");
            } else {
                input_clave.setCustomValidity("");
                input_clave.classList.add("is-valid");
                input_clave.classList.remove("is-invalid");

                contenedor_mensaje_password.textContent = "Contraseña disponible.";
                contenedor_mensaje_password.classList.add("exito");
                contenedor_mensaje_password.classList.remove("error");
            }
        } catch (error) {
            if (error.name === "AbortError") {
                return;
            }
            console.error(error);
        }
    }

    input_clave.addEventListener("input", validar_contrasenia);

    async function turnos_registrados() {
        try {
            const respuesta = await fetch("/turnos_registrados/");
            const resultado = await respuesta.json();
            console.log(resultado);

            select_turno_laboral.innerHTML = "<option value='' selected>Seleccione un Turno</option>";

            resultado.forEach(turno => {
                const option = document.createElement("option");
                option.value = turno.id_turno;
                option.textContent = turno.nombre;
                select_turno_laboral.append(option);
            });
        } catch (error) {
            console.error(error);
        }
    }
    turnos_registrados();

    select_turno_laboral.addEventListener("change", async () => {
        turno = select_turno_laboral.value;

        await perfiles_registrados();
    });

    async function perfiles_registrados() {
        try {
            contenedor_perfiles.innerHTML = "";

            if (!turno) {
                contenedor_texto_mensaje_turno.textContent =
                    "Seleccione un turno para mostrar los perfiles disponibles.";

                contenedor_mensaje_turno.style.display = "block";

                return;
            }

            contenedor_mensaje_turno.style.display = "none";

            const formulario = new FormData();
            formulario.append("turno", turno);

            const respuesta = await fetch("/perfiles_disponibles/", {
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

            resultado.perfiles.forEach(perfil => {

                const div = document.createElement("div");
                div.classList.add("perfil-item");

                const input = document.createElement("input");

                if (perfil.perfil === "Supervisor Encargado") {
                    input.type = "radio";
                } else {
                    input.type = "checkbox";
                }

                input.name = "perfiles";
                input.value = perfil.id_perfil;
                input.id = `perfil_${perfil.id_perfil}`;

                const label = document.createElement("label");
                label.htmlFor = `perfil_${perfil.id_perfil}`;
                label.textContent = perfil.perfil;

                div.appendChild(input);
                div.appendChild(label);

                contenedor_perfiles.appendChild(div);
            });

        } catch (error) {
            console.error(error);
        }
    }
    perfiles_registrados();

    const navegacion = configurarFormularioPasos(formulario_registro);

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

            if (resultado.estado == "exito") {
                formulario_registro.reset();
                navegacion.reiniciar();

                select_nacionalidad.selectedIndex = 0;

                barra_fortaleza.innerHTML = ""
                texto_fortaleza.innerHTML = "";

                contenedor_mensaje_ci.innerHTML = "";
                contenedor_mensaje_correo.innerHTML = "";
                contenedor_mensaje_usuario.innerHTML = "";
                contenedor_mensaje_password.innerHTML = "";

                // REINICIAR PERFILES
                contenedor_perfiles.innerHTML = "";
                contenedor_texto_mensaje_turno.textContent = "Seleccione un turno para mostrar los perfiles disponibles.";
                contenedor_mensaje_turno.style.display = "block";
            }
        } catch (error) {
            console.error(error);
        }
    });
});