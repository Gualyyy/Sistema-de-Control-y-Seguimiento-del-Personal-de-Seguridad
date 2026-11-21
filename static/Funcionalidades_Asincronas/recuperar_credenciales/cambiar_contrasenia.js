document.addEventListener("DOMContentLoaded", () => {

    const formulario_actualizar = document.getElementById("formulario_actualizar");
    const campo_contrasenia = formulario_actualizar.querySelector(".password_contenedor");
    const campo_contrasenia_confirmar = formulario_actualizar.querySelector(".password_contenedor_confirma");

    const input_clave = document.getElementById("clave");
    const input_clave_confirmar = document.getElementById("clave_confirmar");

    const indicadores = document.querySelectorAll(".indicador_password");

    const contenedor_mensaje_password = document.getElementById("contenedor_mensaje_password");

    const btn_actualizar = document.getElementById("btn_actualizar");

    const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;

    configurarContrasenia(campo_contrasenia);
    configurarContrasenia(campo_contrasenia_confirmar);

    function actualizar_estado_boton_password() {
        const claves_coinciden =
            input_clave.value.length > 0 &&
            input_clave_confirmar.value.length > 0 &&
            input_clave.value === input_clave_confirmar.value;

        const formulario_valido =
            input_clave.value.length > 0 &&
            input_clave_confirmar.value.length > 0 &&
            claves_coinciden &&
            contrasenia_valida;

        if (btn_actualizar) {
            btn_actualizar.disabled = !formulario_valido;
        }
    }

    let temporizador_password;
    let solicitud_password = 0;
    let contrasenia_valida = false;

    async function validar_contrasenia() {
        const contrasenia = input_clave.value;
        const id_solicitud = ++solicitud_password;

        contrasenia_valida = false;
        actualizar_estado_boton_password();

        if (!contrasenia) {
            contenedor_mensaje_password.textContent = "";
            contenedor_mensaje_password.classList.remove("exito", "error");
            input_clave.setCustomValidity("Debe ingresar una contraseña.");
            input_clave.classList.remove("is-valid");
            input_clave.classList.add("is-invalid");
            actualizar_estado_boton_password();
            return;
        }

        if (/\s/.test(contrasenia)) {
            contenedor_mensaje_password.textContent =
                "La contraseña no puede contener espacios en blanco.";

            contenedor_mensaje_password.classList.remove("exito");
            contenedor_mensaje_password.classList.add("error");

            input_clave.setCustomValidity(
                "La contraseña no puede contener espacios en blanco."
            );

            input_clave.classList.remove("is-valid");
            input_clave.classList.add("is-invalid");

            actualizar_estado_boton_password();
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

            if (!respuesta_existencia.ok) {
                throw new Error("No se pudo comprobar la contraseña.");
            }

            const resultado_existencia = await respuesta_existencia.json();

            if (
                id_solicitud !== solicitud_password ||
                input_clave.value !== contrasenia
            ) {
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

            if (!respuesta_patron.ok) {
                throw new Error("No se pudieron comprobar las reglas de seguridad.");
            }

            const resultado_patron = await respuesta_patron.json();

            if (
                id_solicitud !== solicitud_password ||
                input_clave.value !== contrasenia
            ) {
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

            actualizar_estado_boton_password();

            if (contraseña_existente) {
                contenedor_mensaje_password.textContent =
                    "Esta contraseña ya está registrada para otra cuenta.";
            } else if (!patron_valido) {
                contenedor_mensaje_password.textContent =
                    "La contraseña no cumple todas las reglas de seguridad.";
            } else {
                contenedor_mensaje_password.textContent =
                    "La contraseña está disponible y cumple las reglas de seguridad.";
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

        } catch (error) {
            if (
                id_solicitud !== solicitud_password ||
                input_clave.value !== contrasenia
            ) {
                return;
            }

            console.error(error);

            contrasenia_valida = false;

            input_clave.setCustomValidity(
                "No se pudo completar la validación de la contraseña."
            );

            input_clave.classList.add("is-invalid");
            input_clave.classList.remove("is-valid");

            contenedor_mensaje_password.textContent =
                "No se pudo comprobar la contraseña. Inténtelo nuevamente.";

            contenedor_mensaje_password.classList.add("error");
            contenedor_mensaje_password.classList.remove("exito");

            actualizar_estado_boton_password();
        }
    }

    input_clave.addEventListener("input", () => {
        clearTimeout(temporizador_password);
        solicitud_password++;

        contrasenia_valida = false;
        actualizar_estado_boton_password();

        input_clave.setCustomValidity("");
        input_clave.classList.remove("is-valid", "is-invalid");

        if (!input_clave.value) {
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

        if (/\s/.test(input_clave.value)) {
            contenedor_mensaje_password.textContent =
                "La contraseña no puede contener espacios en blanco.";

            contenedor_mensaje_password.classList.remove("exito");
            contenedor_mensaje_password.classList.add("error");

            input_clave.setCustomValidity(
                "La contraseña no puede contener espacios en blanco."
            );

            input_clave.classList.add("is-invalid");
            actualizar_estado_boton_password();
            return;
        }

        contenedor_mensaje_password.textContent = "Esperando para validar...";
        contenedor_mensaje_password.classList.remove("exito", "error");

        actualizar_coincidencia_claves();

        temporizador_password = setTimeout(() => {
            validar_contrasenia();
        }, 700);
    });

    input_clave_confirmar.addEventListener("input", () => {
        actualizar_coincidencia_claves();

        input_clave_confirmar.setCustomValidity("");

        if (!input_clave_confirmar.value) {
            return;
        }

        if (input_clave_confirmar.value !== input_clave.value) {
            input_clave_confirmar.setCustomValidity(
                "Las contraseñas no coinciden."
            );
        }

        actualizar_estado_boton_password();

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
            apellido: !contiene_dato(clave, datos_empleado.apellidos),

            // Comparar contraseña y confirmación
            coincide: Boolean(clave) &&
                clave === input_clave_confirmar.value
        };
    }

    function actualizar_coincidencia_claves() {
        const indicador = document.querySelector(
            '.pagina_cambiar_contrasenia [data-regla="coincide"]'
        );

        if (!indicador) {
            return;
        }

        const icono = indicador.querySelector("i");

        if (!icono) {
            return;
        }

        const clave = input_clave.value;
        const confirmar = input_clave_confirmar.value;

        // Si alguno está vacío, todavía no se ha validado
        const cumplido = Boolean(clave) &&
            Boolean(confirmar) &&
            clave === confirmar;

        indicador.classList.toggle("cumplido", cumplido);

        icono.classList.toggle("fa-circle-check", cumplido);
        icono.classList.toggle("fa-circle-xmark", !cumplido);
        icono.classList.remove("fa-circle");
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


    formulario_actualizar.addEventListener("submit", async (e) => {
        e.preventDefault();

        try {
            const formulario = new FormData(formulario_actualizar);

            const respuesta = await fetch("/cambiar_contrasenia/", {
                method: "POST",
                body: formulario
            });

            const resultado = await respuesta.json();

            await Swal.fire({
                title: resultado.title,
                text: resultado.descripcion,
                icon: resultado.icon
            });

            // No reiniciar si el registro no fue exitoso.
            if (resultado.estado == "exito") {
                if (window.Swal) {
                    window.Swal.close();
                }
                window.vigilanciaReemplazar(resultado.url);
                return;
            }

            formulario_actualizar.reset();
            reiniciar_indicadores_password();
            contenedor_mensaje_password.innerHTML = "";
        } catch (error) {
            console.error(error);
        }
    });

});