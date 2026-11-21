document.addEventListener("DOMContentLoaded", () => {

    const formulario_registrar = document.getElementById("formulario_registrar");

    const select_tipo_cliente = document.getElementById("tipo_cliente");
    const input_nombre_cliente = document.getElementById("nombre_cliente");
    const input_apellido_cliente = document.getElementById("apellido_cliente");
    const input_nombre_empresa = document.getElementById("nombre_empresa");

    const input_identificador = document.getElementById("identificador");
    const select_tipo_identificador = document.getElementById("tipo_identificador");

    const select_prefijo = document.getElementById("prefijo");
    const input_num_telefono = document.getElementById("num_telefono");

    const input_correo = document.getElementById("correo");
    const select_dominio = document.getElementById("dominio");

    const input_nombre_usuario = document.getElementById("nombre_usuario");
    const input_clave = document.getElementById("clave");

    const textarea_direccion = document.getElementById("direccion_domicilio");
    const contador_residencia = document.getElementById("contador_residencia");

    const contenedor_mensaje_identificador = document.getElementById("contenedor_mensaje_identificador");
    const contenedor_mensaje_telefono = document.getElementById("contenedor_mensaje_telefono");
    const contenedor_mensaje_correo = document.getElementById("contenedor_mensaje_correo");
    const contenedor_mensaje_user = document.getElementById("contenedor_mensaje_user");
    const contenedor_mensaje_password = document.getElementById("contenedor_mensaje_password");

    const campo_contrasenia = formulario_registrar.querySelector(".password_contenedor");
    const indicadores = document.querySelectorAll(".indicador_password");

    const btn_registrar = document.getElementById("btn_registrar");

    const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;

    const controles_individuo = document.getElementById("controles_individuo");
    const control_empresa = document.getElementById("control_empresa");

    configurarIdentificador(input_identificador, select_tipo_identificador, select_tipo_cliente);
    configurarContrasenia(campo_contrasenia);
    configurarCorreo(input_correo, select_dominio);
    configurarTelefono(input_num_telefono, select_prefijo);

    controles_individuo.hidden = true;
    control_empresa.hidden = true;

    // Configuración inicial
    function actualizar_controles_cliente() {
        const tipo_cliente = select_tipo_cliente.value;
        const es_natural = tipo_cliente === "NATURAL";
        const es_empresa = tipo_cliente === "EMPRESA";

        // Mostrar únicamente los controles correspondientes
        controles_individuo.hidden = !es_natural;
        control_empresa.hidden = !es_empresa;

        controles_individuo.classList.toggle("activo", es_natural);
        control_empresa.classList.toggle("activo", es_empresa);

        // Validaciones obligatorias
        input_nombre_cliente.required = es_natural;
        input_apellido_cliente.required = es_natural;
        input_nombre_empresa.required = es_empresa;

        // Deshabilitar campos que no corresponden al tipo seleccionado
        input_nombre_cliente.disabled = !es_natural;
        input_apellido_cliente.disabled = !es_natural;
        input_nombre_empresa.disabled = !es_empresa;

        // Limpiar campos del tipo anterior
        if (es_natural) {
            input_nombre_empresa.value = "";
        } else if (es_empresa) {
            input_nombre_cliente.value = "";
            input_apellido_cliente.value = "";
        }
    }

    // Detectar cambios
    select_tipo_cliente.addEventListener("change", actualizar_controles_cliente);

    // Aplicar configuración inicial
    actualizar_controles_cliente();

    function soloTexto(input) {
        input.value = input.value.replace(/[^a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]/g, '');
    }

    input_nombre_cliente.addEventListener("input", function () {
        soloTexto(this);
    });

    input_apellido_cliente.addEventListener("input", function () {
        soloTexto(this);
    });

    input_nombre_empresa.addEventListener("input", function () {
        soloTexto(this);
    });

    textarea_direccion.addEventListener("input", function () {
        soloTexto(textarea_direccion);
    });

    textarea_direccion.addEventListener("input", () => {
        textarea_direccion.value = textarea_direccion.value.replace(
            /[^a-zA-ZáéíóúÁÉÍÓÚñÑ0-9\s.,:;()\-]/g,
            ""
        );

        contador_residencia.textContent = textarea_direccion.value.length;
    });

    let controlador_identificador = null;

    async function validar_identificador() {
        const tipo = select_tipo_identificador.value.trim().toUpperCase();
        const valor = input_identificador.value.trim();

        if (controlador_identificador) {
            controlador_identificador.abort();
            controlador_identificador = null;
        }

        if (!tipo || !valor) {
            input_identificador.setCustomValidity("");
            input_identificador.classList.remove("is-valid", "is-invalid");
            contenedor_mensaje_identificador.textContent = "";
            contenedor_mensaje_identificador.classList.remove("exito", "error");
            return;
        }

        const controlador = new AbortController();
        controlador_identificador = controlador;

        try {
            const formulario = new FormData();
            formulario.append("tipo_identificador", tipo);
            formulario.append("identificador", valor);

            const respuesta = await fetch("/validar_identificador/", {
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

            if (input_identificador.value.trim() !== valor ||
                select_tipo_identificador.value.trim().toUpperCase() !== tipo) {
                return;
            }

            if (resultado.existe) {
                input_identificador.setCustomValidity(
                    "Este identificador ya se encuentra registrado."
                );

                input_identificador.classList.add("is-invalid");
                input_identificador.classList.remove("is-valid");

                contenedor_mensaje_identificador.textContent = "Este identificador ya se encuentra registrado.";
                contenedor_mensaje_identificador.classList.add("error");
                contenedor_mensaje_identificador.classList.remove("exito");

            } else {
                input_identificador.setCustomValidity("");

                input_identificador.classList.add("is-valid");
                input_identificador.classList.remove("is-invalid");

                contenedor_mensaje_identificador.textContent = "Identificador disponible.";
                contenedor_mensaje_identificador.classList.add("exito");
                contenedor_mensaje_identificador.classList.remove("error");
            }

        } catch (error) {
            if (error.name !== "AbortError") {
                console.error("Error al validar el identificador:", error);

                input_identificador.setCustomValidity(
                    "No se pudo validar el identificador. Inténtelo nuevamente."
                );
                input_identificador.classList.add("is-invalid");
                input_identificador.classList.remove("is-valid");

                contenedor_mensaje_identificador.textContent =
                    "No se pudo validar el identificador. Inténtelo nuevamente.";
                contenedor_mensaje_identificador.classList.add("error");
                contenedor_mensaje_identificador.classList.remove("exito");
            }
        } finally {
            if (controlador_identificador === controlador) {
                controlador_identificador = null;
            }
        }
    }

    input_identificador.addEventListener("input", validar_identificador);

    select_tipo_identificador.addEventListener("change", validar_identificador);

    select_tipo_cliente.addEventListener("change", () => {
        validar_identificador();
    });

    let controlador_telefono = null;

    async function validar_telefono(prefijo, numero, msg) {
        const valorPrefijo = prefijo.value.trim();
        const valorNumero = numero.value.trim();

        if (controlador_telefono) {
            controlador_telefono.abort();
            controlador_telefono = null;
        }

        if (!valorPrefijo || !valorNumero) {
            msg.textContent = "";
            msg.classList.remove("exito", "error");
            numero.setCustomValidity("");
            numero.classList.remove("is-valid", "is-invalid");
            return;
        }

        const controlador = new AbortController();
        controlador_telefono = controlador;

        try {
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

            if (prefijo.value.trim() !== valorPrefijo || numero.value.trim() !== valorNumero) {
                return;
            }

            if (resultado.existe) {
                numero.setCustomValidity("Este número telefónico ya está registrado.");
                numero.classList.add("is-invalid");
                numero.classList.remove("is-valid");

                msg.textContent = "Este número telefónico ya está registrado.";
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
            if (error.name !== "AbortError") {
                console.error(error);
            }
        } finally {
            if (controlador_telefono === controlador) {
                controlador_telefono = null;
            }
        }
    }

    input_num_telefono.addEventListener("input", () => {
        validar_telefono(select_prefijo, input_num_telefono, contenedor_mensaje_telefono);
    });

    select_prefijo.addEventListener("change", () => {
        validar_telefono(select_prefijo, input_num_telefono, contenedor_mensaje_telefono);
    });

    let controlador_correo = null;

    async function validar_correo(correo, dominio, msg) {
        const valorCorreo = correo.value.trim().toLowerCase();
        const valorDominio = dominio.value.trim().toLowerCase();

        if (controlador_correo) {
            controlador_correo.abort();
            controlador_correo = null;
        }

        if (!valorCorreo || !valorDominio) {
            msg.textContent = "";
            msg.classList.remove("exito", "error");
            correo.setCustomValidity("");
            correo.classList.remove("is-valid", "is-invalid");
            return;
        }

        const controlador = new AbortController();
        controlador_correo = controlador;

        try {
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

            if (correo.value.trim().toLowerCase() !== valorCorreo || dominio.value.trim().toLowerCase() !== valorDominio) {
                return;
            }

            if (resultado.existe) {
                correo.setCustomValidity("Este correo electrónico ya está registrado.");
                correo.classList.add("is-invalid");
                correo.classList.remove("is-valid");

                msg.textContent = "Este correo electrónico ya está registrado.";
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
            if (error.name !== "AbortError") {
                console.error(error);
            }
        } finally {
            if (controlador_correo === controlador) {
                controlador_correo = null;
            }
        }
    }

    input_correo.addEventListener("input", () => {
        validar_correo(input_correo, select_dominio, contenedor_mensaje_correo);
    });

    select_dominio.addEventListener("change", () => {
        validar_correo(input_correo, select_dominio, contenedor_mensaje_correo);
    });

    let solicitud_usuario = 0;

    async function validar_nombre_usuario(input, msg) {
        const nombre_usuario = input.value.trim();
        const id_solicitud = ++solicitud_usuario;

        nombre_usuario_valido = false;

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

        } catch (error) {
            if (id_solicitud !== solicitud_usuario || input.value.trim() !== nombre_usuario) {
                return;
            }

            console.error(error);

            nombre_usuario_valido = false;

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

        if (/\s/.test(contrasenia)) {
            contrasenia_valida = false;

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

        } catch (error) {
            if (id_solicitud !== solicitud_password || input_clave.value !== contrasenia) {
                return;
            }

            console.error(error);

            contrasenia_valida = false;

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

            const respuesta = await fetch("/registrar_clientes_foro/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario,
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            await Swal.fire({
                title: resultado.title,
                text: resultado.descripcion,
                icon: resultado.icon
            });

            formulario_registrar.reset();

            reiniciar_indicadores_password();

            contenedor_mensaje_correo.innerHTML = ""
            contenedor_mensaje_identificador.innerHTML = ""
            contenedor_mensaje_telefono.innerHTML = ""
            contenedor_mensaje_password.innerHTML = ""
            contenedor_mensaje_user.innerHTML = ""
        } catch (error) {
            console.error(error);
        }
    });

});