document.addEventListener("DOMContentLoaded", () => {

    const formulario_registrar = document.getElementById("formulario_registrar");
    const formulario_busqueda = document.getElementById("formulario_busqueda");

    const select_nacionalidad = document.getElementById("nacionalidad");
    const input_cedula_identidad = document.getElementById("cedula_identidad");

    const input_id_usuario = document.getElementById("id_usuario");
    const input_nombre_usuario = document.getElementById("nombre_usuario");
    const input_clave = document.getElementById("clave");

    const contenedor_formulario_credenciales = document.querySelector(".seccion_registro_credenciales");
    const contenedor_formulario_busqueda = document.querySelector(".seccion_busqueda_empleado");

    const contenedor_mensaje_user = document.getElementById("contenedor_mensaje_user");
    const contenedor_mensaje_password = document.getElementById("contenedor_mensaje_password");

    const campo_contrasenia = formulario_registrar.querySelector(".password_contenedor");

    const indicadores = document.querySelectorAll(".indicador_password");

    const btn_registrar = document.getElementById("btn_registrar");

    const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;

    contenedor_formulario_credenciales.hidden = true;
    contenedor_formulario_busqueda.hidden = false;

    configurarCedula(input_cedula_identidad, select_nacionalidad);
    configurarContrasenia(campo_contrasenia);

    let nombre_usuario_valido = false;

    function actualizar_estado_registro() {
        if (btn_registrar) {
            btn_registrar.disabled = !(
                nombre_usuario_valido &&
                contrasenia_valida
            );
        }
    }
    actualizar_estado_registro();

    let solicitud_usuario = 0;

    async function validar_nombre_usuario(input, msg) {
        const nombre_usuario = input.value.trim();
        const id_solicitud = ++solicitud_usuario;

        nombre_usuario_valido = false;
        actualizar_estado_registro();

        if (!nombre_usuario) {
            msg.textContent = "";
            msg.classList.remove("exito", "error");

            input.setCustomValidity("");
            input.classList.remove("is-valid", "is-invalid");
            return;
        }

        msg.textContent = "Verificando nombre de usuario...";
        msg.classList.remove("exito", "error");

        input.setCustomValidity("");
        input.classList.remove("is-valid", "is-invalid");

        try {
            const formulario = new FormData();
            formulario.append("nombre_usuario", nombre_usuario);

            const respuesta = await fetch("/validar_nombre_usuario/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken
                },
                body: formulario,
                credentials: "same-origin"
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            if (id_solicitud !== solicitud_usuario || input.value.trim() !== nombre_usuario) {
                return;
            }

            if (resultado.existe === true) {
                input.setCustomValidity(
                    "Este nombre de usuario ya está registrado."
                );

                input.classList.add("is-invalid");
                input.classList.remove("is-valid");

                msg.textContent = "Este nombre de usuario ya está registrado.";
                msg.classList.add("error");
                msg.classList.remove("exito");

                return;
            }

            nombre_usuario_valido = true;

            input.setCustomValidity("");
            input.classList.add("is-valid");
            input.classList.remove("is-invalid");

            msg.textContent = "Nombre de usuario disponible.";
            msg.classList.add("exito");
            msg.classList.remove("error");

            actualizar_estado_registro();

        } catch (error) {
            if (id_solicitud !== solicitud_usuario || input.value.trim() !== nombre_usuario) {
                return;
            }

            console.error(error);

            nombre_usuario_valido = false;
            actualizar_estado_registro();

            input.setCustomValidity(
                "No se pudo verificar el nombre de usuario."
            );

            input.classList.add("is-invalid");
            input.classList.remove("is-valid");

            msg.textContent = "No se pudo verificar el nombre de usuario. Intente nuevamente.";

            msg.classList.add("error");
            msg.classList.remove("exito");
        }
    }

    input_nombre_usuario.addEventListener("input", () => {
        nombre_usuario_valido = false;
        actualizar_estado_registro();

        // Impedir espacios en blanco
        if (/\s/.test(input_nombre_usuario.value)) {
            // Invalidar cualquier solicitud anterior
            ++solicitud_usuario;

            input_nombre_usuario.setCustomValidity(
                "El nombre de usuario no debe contener espacios."
            );

            input_nombre_usuario.classList.add("is-invalid");
            input_nombre_usuario.classList.remove("is-valid");

            contenedor_mensaje_user.textContent =
                "El nombre de usuario no debe contener espacios.";

            contenedor_mensaje_user.classList.add("error");
            contenedor_mensaje_user.classList.remove("exito");

            return;
        }

        // Limpiar el estado de validación anterior
        input_nombre_usuario.setCustomValidity("");

        validar_nombre_usuario(
            input_nombre_usuario,
            contenedor_mensaje_user
        );
    });

    let temporizador_password;
    let solicitud_password = 0;
    let contrasenia_valida = false;

    async function validar_contrasenia() {
        const contrasenia = input_clave.value;
        const id_solicitud = ++solicitud_password;

        contrasenia_valida = false;
        actualizar_estado_registro();

        if (/\s/.test(contrasenia)) {
            contrasenia_valida = false;
            actualizar_estado_registro();

            input_clave.setCustomValidity(
                "La contraseña no debe contener espacios en blanco."
            );

            input_clave.classList.add("is-invalid");
            input_clave.classList.remove("is-valid");

            contenedor_mensaje_password.textContent = "La contraseña no debe contener espacios en blanco.";

            contenedor_mensaje_password.classList.add("error");
            contenedor_mensaje_password.classList.remove("exito");

            return;
        }

        if (!contrasenia.trim()) {
            contenedor_mensaje_password.textContent = "";
            contenedor_mensaje_password.classList.remove("exito", "error");
            input_clave.setCustomValidity("");
            input_clave.classList.remove("is-valid", "is-invalid");
            return;
        }

        contenedor_mensaje_password.textContent = "Validando contraseña...";
        contenedor_mensaje_password.classList.remove("exito", "error");
        input_clave.setCustomValidity("");
        input_clave.classList.remove("is-valid", "is-invalid");

        try {
            const formulario = new FormData();
            formulario.append("clave", contrasenia);

            const respuesta_existencia = await fetch("/validar_contrasenia/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken
                },
                body: formulario
            });
            const resultado_existencia = await respuesta_existencia.json();
            console.log(respuesta_existencia);

            if (id_solicitud !== solicitud_password || input_clave.value !== contrasenia) {
                return;
            }

            const formulario_patron = new FormData();
            formulario_patron.append("clave", contrasenia);

            const respuesta_patron = await fetch("/validar_patron_contrasenia/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken
                },
                body: formulario_patron
            });
            const resultado_patron = await respuesta_patron.json();

            if (id_solicitud !== solicitud_password || input_clave.value !== contrasenia) {
                return;
            }

            indicadores.forEach(indicador => {
                const regla = indicador.dataset.regla;
                const icono = indicador.querySelector("i");
                const cumplido = resultado_patron.validaciones[regla] === true;

                indicador.classList.toggle("cumplido", cumplido);

                if (icono) {
                    icono.classList.toggle("fa-circle-check", cumplido);
                    icono.classList.toggle("fa-circle-xmark", !cumplido);
                }
            });

            const contraseña_existente = resultado_existencia.existe === true;

            const patron_valido = resultado_patron.valida === true;

            contrasenia_valida = !contraseña_existente && patron_valido;

            if (contraseña_existente) {
                contenedor_mensaje_password.textContent = "Esta contraseña ya está registrada para otra cuenta.";
            } else if (!patron_valido) {
                contenedor_mensaje_password.textContent = "La contraseña no cumple todas las reglas de seguridad.";
            } else {
                contenedor_mensaje_password.textContent = "La contraseña está disponible y cumple las reglas de seguridad.";
            }

            contenedor_mensaje_password.classList.toggle("exito", contrasenia_valida);

            contenedor_mensaje_password.classList.toggle("error", !contrasenia_valida);

            input_clave.setCustomValidity(
                contrasenia_valida
                    ? ""
                    : contraseña_existente
                        ? "Esta contraseña ya está registrada para otra cuenta."
                        : "La contraseña no cumple las reglas de seguridad."
            );

            input_clave.classList.toggle("is-valid", contrasenia_valida);
            input_clave.classList.toggle("is-invalid", !contrasenia_valida);

            actualizar_estado_registro();
        } catch (error) {
            if (id_solicitud !== solicitud_password || input_clave.value !== contrasenia) {
                return;
            }

            console.error(error);

            contrasenia_valida = false;
            actualizar_estado_registro();

            input_clave.setCustomValidity("No se pudo completar la validación de la contraseña.");

            input_clave.classList.add("is-invalid");
            input_clave.classList.remove("is-valid");

            contenedor_mensaje_password.textContent = "No se pudo comprobar la contraseña. Inténtelo nuevamente.";

            contenedor_mensaje_password.classList.add("error");
            contenedor_mensaje_password.classList.remove("exito");
        }
    }

    input_clave.addEventListener("input", () => {
        clearTimeout(temporizador_password);
        solicitud_password++;

        contrasenia_valida = false;
        actualizar_estado_registro();

        input_clave.setCustomValidity("");
        input_clave.classList.remove("is-valid", "is-invalid");

        const contrasenia = input_clave.value;

        // Campo vacío
        if (!contrasenia) {
            contenedor_mensaje_password.textContent = "";
            contenedor_mensaje_password.classList.remove("exito", "error");

            indicadores.forEach(indicador => {
                indicador.classList.remove("cumplido");

                const icono = indicador.querySelector("i");

                if (icono) {
                    icono.classList.remove("fa-circle-check");
                    icono.classList.add("fa-circle-xmark");
                }
            });

            return;
        }

        // Impedir espacios en blanco
        if (/\s/.test(contrasenia)) {
            contenedor_mensaje_password.textContent = "La contraseña no debe contener espacios en blanco.";

            contenedor_mensaje_password.classList.add("error");
            contenedor_mensaje_password.classList.remove("exito");

            input_clave.setCustomValidity(
                "La contraseña no debe contener espacios en blanco."
            );

            input_clave.classList.add("is-invalid");

            indicadores.forEach(indicador => {
                indicador.classList.remove("cumplido");

                const icono = indicador.querySelector("i");

                if (icono) {
                    icono.classList.remove("fa-circle-check");
                    icono.classList.add("fa-circle-xmark");
                }
            });

            return;
        }

        // Continuar con la validación existente
        contenedor_mensaje_password.textContent = "Esperando para validar...";

        contenedor_mensaje_password.classList.remove("exito", "error");

        temporizador_password = setTimeout(() => {
            validar_contrasenia();
        }, 700);
    });

    formulario_busqueda.addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
            const formulario = new FormData(formulario_busqueda);

            const respuesta = await fetch("/empleado_sin_credenciales/", {
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

            if (resultado.estado == true) {
                input_id_usuario.value = resultado.id_usuario;

                contenedor_formulario_credenciales.hidden = false;
                contenedor_formulario_busqueda.hidden = true;

                formulario_busqueda.reset();
            }
        } catch (error) {
            console.error(error);
        }
    });

    let datos_empleado = {
        nombres: "",
        apellidos: "",
        cedula: "",
        telefono: "",
        nacimiento: ""
    };

    function normalizar(texto) {
        return String(texto || "")
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "")
            .toLowerCase()
            .replace(/\s+/g, "");
    }

    function solo_digitos(texto) {
        return String(texto || "").replace(/\D/g, "");
    }

    function contiene_dato(clave, dato) {
        const valor_clave = normalizar(clave);
        const valor_dato = normalizar(dato);

        return valor_dato.length >= 3 && valor_clave.includes(valor_dato);
    }

    function contiene_fecha(clave, fecha) {
        const valor_clave = solo_digitos(clave);
        const valor_fecha = solo_digitos(fecha);

        if (valor_fecha.length < 6) {
            return false;
        }

        const variantes = [valor_fecha];

        if (valor_fecha.length >= 8) {
            variantes.push(valor_fecha.slice(0, 8));
            variantes.push(valor_fecha.slice(2, 8));
        }

        return variantes.some(
            variante => variante.length >= 6 && valor_clave.includes(variante)
        );
    }

    function validar_clave(clave) {
        const letras = /[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]/.test(clave);
        const numero = /\d/.test(clave);
        const especial = /[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9]/.test(clave);
        const repetidos = !/(.)\1\1/.test(clave);

        const cedula = solo_digitos(datos_empleado.cedula);
        const telefono = solo_digitos(datos_empleado.telefono);

        return {
            longitud: clave.length >= 8 && clave.length <= 15,
            alfabetico: letras,
            especial: especial,
            numero: numero,
            repetidos: repetidos,
            nacimiento: !contiene_fecha(clave, datos_empleado.nacimiento),
            telefono: !(
                telefono.length >= 7 &&
                solo_digitos(clave).includes(telefono)
            ),
            cedula: !(
                cedula.length >= 6 &&
                solo_digitos(clave).includes(cedula)
            ),
            nombre: !contiene_dato(clave, datos_empleado.nombres),
            apellido: !contiene_dato(clave, datos_empleado.apellidos)
        };
    }


    function actualizar_indicadores() {
        const clave = input_clave.value;

        if (!clave) {
            reiniciar_indicadores_password();
            return;
        }

        const reglas = validar_clave(clave);

        indicadores.forEach(indicador => {
            const regla = indicador.dataset.regla;
            const icono = indicador.querySelector("i");

            if (!(regla in reglas) || !icono) {
                return;
            }

            const cumplido = reglas[regla];

            indicador.classList.toggle("cumplido", cumplido);

            icono.classList.toggle("fa-circle-check", cumplido);
            icono.classList.toggle("fa-circle-xmark", !cumplido);
            icono.classList.remove("fa-circle");
        });
    }

    window.actualizar_datos_empleado_password = function (datos) {
        datos_empleado = {
            nombres: datos.nombres || "",
            apellidos: datos.apellidos || "",
            cedula: datos.cedula || "",
            telefono: datos.telefono || "",
            nacimiento: datos.nacimiento || ""
        };

        actualizar_indicadores();
    };

    function reiniciar_indicadores_password() {
        input_clave.value = "";

        indicadores.forEach(indicador => {
            const icono = indicador.querySelector("i");

            indicador.classList.remove("cumplido");

            if (icono) {
                icono.classList.remove(
                    "fa-circle-check",
                    "fa-circle-xmark"
                );

                icono.classList.add("fa-circle");
            }
        });

        datos_empleado = {
            nombres: "",
            apellidos: "",
            cedula: "",
            telefono: "",
            nacimiento: ""
        };
    }

    input_clave.addEventListener("input", actualizar_indicadores);

    actualizar_indicadores();

    formulario_registrar.addEventListener("submit", async (e) => {
        e.preventDefault();

        // Mostrar mensaje de carga
        Swal.fire({
            title: "Registrando credenciales...",
            text: "Por favor, espere mientras se procesa la solicitud.",
            icon: "info",
            allowOutsideClick: false,
            allowEscapeKey: false,
            showConfirmButton: false,
            didOpen: () => {
                Swal.showLoading();
            }
        });

        try {
            const formulario = new FormData(formulario_registrar);

            const respuesta = await fetch("/registrar_credenciales/", {
                method: "POST",
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            // Mostrar el resultado del registro
            await Swal.fire({
                title: resultado.title,
                text: resultado.descripcion,
                icon: resultado.icon
            });

            // No reiniciar si el registro no fue exitoso
            if (resultado.estado !== "exito") {
                return;
            }

            formulario_registrar.reset();

            reiniciar_indicadores_password();

            contenedor_formulario_credenciales.hidden = true;
            contenedor_formulario_busqueda.hidden = false;

            contenedor_mensaje_user.textContent = "";
            contenedor_mensaje_password.textContent = "";
        } catch (error) {
            console.error(error);
        }
    });

});