document.addEventListener("DOMContentLoaded", () => {

    const formulario_busqueda = document.getElementById("formulario_busqueda");
    const formulario_actualizar = document.getElementById("formulario_actualizar");

    const select_tipo_cliente_b = document.getElementById("tipo_cliente_b");
    const select_tipo_identificador_b = document.getElementById("tipo_identificador_b");
    const input_identificador_b = document.getElementById("identificador_b");

    const input_id_cliente = document.getElementById("id_cliente");

    const select_tipo_cliente = document.getElementById("tipo_cliente");

    const select_tipo_identificador = document.getElementById("tipo_identificador");
    const input_identificador = document.getElementById("identificador");
    const contenedor_mensaje_identificador = document.getElementById("contenedor_mensaje_identificador");

    const input_nombre_cliente = document.getElementById("nombre_cliente");
    const input_apellido_cliente = document.getElementById("apellido_cliente");
    const input_nombre_empresa = document.getElementById("nombre_empresa");

    const select_prefijo = document.getElementById("prefijo");
    const input_num_telefono = document.getElementById("num_telefono");
    const contenedor_mensaje_telefono = document.getElementById("contenedor_mensaje_telefono");

    const input_correo = document.getElementById("correo");
    const select_dominio = document.getElementById("dominio");
    const contenedor_mensaje_correo = document.getElementById("contenedor_mensaje_correo");

    const btn_actualizar = document.getElementById("btn_actualizar");

    const controles_individuo = document.getElementById("controles_individuo");
    const control_empresa = document.getElementById("control_empresa");

    configurarIdentificador(input_identificador_b, select_tipo_identificador_b, select_tipo_cliente_b);
    configurarIdentificador(input_identificador, select_tipo_identificador, select_tipo_cliente);

    configurarTelefono(input_num_telefono, select_prefijo);
    configurarCorreo(input_correo, select_dominio)

    const controles_actualizacion = [
        select_tipo_cliente,
        select_tipo_identificador,
        input_identificador,
        input_nombre_cliente,
        input_apellido_cliente,
        input_nombre_empresa,
        select_prefijo,
        input_num_telefono,
        input_correo,
        select_dominio,
        btn_actualizar
    ]

    function bloquearFormularioActualizar(bloquear = true) {
        controles_actualizacion.forEach(control => {
            if (control) {
                control.disabled = bloquear;
            }
        });
    }
    bloquearFormularioActualizar(true);

    function soloTexto(input) {
        input.value = input.value.replace(/[^a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]/g, '');
    }

    input_nombre_cliente.addEventListener("input", (e) => {
        soloTexto(e.target);
    });

    input_apellido_cliente.addEventListener("input", (e) => {
        soloTexto(e.target);
    });

    input_nombre_empresa.addEventListener("input", (e) => {
        soloTexto(e.target);
    });

    formulario_busqueda.addEventListener("submit", async (e) => {
        e.preventDefault();

        try {
            const formulario = new FormData(formulario_busqueda);

            const respuesta = await fetch("/ventas/buscar_datos_cliente/", {
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

            if (resultado.estado !== "exito") return;

            bloquearFormularioActualizar(false);

            input_id_cliente.value = resultado.cliente.id_cliente;

            select_tipo_cliente.value = resultado.cliente.tipo_cliente;

            if (resultado.cliente.tipo_cliente === "NATURAL") {
                input_nombre_cliente.value = resultado.cliente.nombres_cliente;
                input_apellido_cliente.value = resultado.cliente.apellidos_cliente;
                input_nombre_empresa.value = "";
            } else {
                input_nombre_empresa.value = resultado.cliente.nombre_razon_social;
                input_nombre_cliente.value = "";
                input_apellido_cliente.value = "";
            }

            actualizar_controles_cliente();

            const [tipo_identificador, identificador] = resultado.cliente.identificador.split("-");

            if (!select_tipo_identificador.querySelector(`option[value="${tipo_identificador}"]`)) {
                const opcion_identificador = document.createElement("option");
                opcion_identificador.value = tipo_identificador;
                opcion_identificador.textContent = tipo_identificador;
                opcion_identificador.hidden = true;
                select_tipo_identificador.append(opcion_identificador);
            }

            select_tipo_identificador.value = tipo_identificador;
            input_identificador.value = identificador;

            const [prefijo, num_telefonico] = resultado.cliente.contacto.telefono.split("-");

            if (!select_prefijo.querySelector(`option[value="${prefijo}"]`)) {
                const opcion_telefonico = document.createElement("option");
                opcion_telefonico.value = prefijo;
                opcion_telefonico.textContent = prefijo;
                opcion_telefonico.hidden = true;
                select_prefijo.append(opcion_telefonico);
            }

            select_prefijo.value = prefijo;
            input_num_telefono.value = num_telefonico;

            const [correo, dominio] = resultado.cliente.contacto.correo.split("@");
            const dominio_completo = "@" + dominio;

            if (!select_dominio.querySelector(`option[value="${dominio_completo}"]`)) {
                const opcion_email = document.createElement("option");
                opcion_email.value = dominio_completo;
                opcion_email.textContent = dominio_completo;
                opcion_email.hidden = true;
                select_dominio.append(opcion_email);
            }

            select_dominio.value = dominio_completo;
            input_correo.value = correo;

            formulario_busqueda.reset();
        } catch (error) {
            console.error(error);
        }
    });

    function actualizar_controles_cliente() {
        const tipo_cliente = select_tipo_cliente.value;

        controles_individuo.classList.toggle("activo", tipo_cliente === "NATURAL");
        control_empresa.classList.toggle("activo", tipo_cliente === "EMPRESA");

        input_nombre_cliente.required = tipo_cliente === "NATURAL";
        input_apellido_cliente.required = tipo_cliente === "NATURAL";
        input_nombre_empresa.required = tipo_cliente === "EMPRESA";
    }

    select_tipo_cliente.addEventListener("change", actualizar_controles_cliente);

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

        if (!/^\d{7}$/.test(valorNumero)) {
            numero.setCustomValidity("El número telefónico debe contener exactamente 7 dígitos.");
            numero.classList.add("is-invalid");
            numero.classList.remove("is-valid");

            msg.textContent = "El número telefónico debe contener exactamente 7 dígitos.";
            msg.classList.add("error");
            msg.classList.remove("exito");
            return;
        }

        const controlador = new AbortController();
        controlador_telefono = controlador;

        try {
            const formulario = new FormData();
            formulario.append("prefijo", valorPrefijo);
            formulario.append("numeros", valorNumero);
            formulario.append("id_cliente", input_id_cliente.value);

            const respuesta = await fetch("/ventas/validar_telefono_cliente/", {
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

        const email = `${valorCorreo}${valorDominio}`;

        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
            correo.setCustomValidity("Ingrese un correo electrónico válido.");
            correo.classList.add("is-invalid");
            correo.classList.remove("is-valid");

            msg.textContent = "Ingrese un correo electrónico válido.";
            msg.classList.add("error");
            msg.classList.remove("exito");
            return;
        }

        const controlador = new AbortController();
        controlador_correo = controlador;

        try {
            const formulario = new FormData();
            formulario.append("correo", valorCorreo);
            formulario.append("dominio", valorDominio);
            formulario.append("id_cliente", input_id_cliente.value);

            const respuesta = await fetch("/ventas/validar_correo_cliente/", {
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

    async function validar_identificador(tipo_identificador, identificador, msg) {
        const tipo = tipo_identificador.value;
        const valor = identificador.value.trim();

        if (!tipo || !valor) {
            msg.textContent = "";
            msg.classList.remove("exito", "error");

            identificador.setCustomValidity("");
            identificador.classList.remove("is-valid", "is-invalid");
            return;
        }

        const longitudes = {
            V: [7, 8],
            E: [8, 10],
            J: [9, 9],
            G: [9, 9]
        };

        const limites = longitudes[tipo];

        if (!limites) {
            msg.textContent = "";
            msg.classList.remove("exito", "error");
            identificador.setCustomValidity("Tipo de identificador no válido.");
            identificador.classList.add("is-invalid");
            identificador.classList.remove("is-valid");
            return;
        }

        const [minimo, maximo] = limites;

        if (!/^\d+$/.test(valor) || valor.length < minimo || valor.length > maximo) {
            msg.textContent = "";
            msg.classList.remove("exito", "error");

            identificador.setCustomValidity(`El identificador debe contener entre ${minimo} y ${maximo} números.`);
            identificador.classList.add("is-invalid");
            identificador.classList.remove("is-valid");
            return;
        }

        try {
            const formulario = new FormData();
            formulario.append("tipo_identificador", tipo);
            formulario.append("identificador", valor);
            formulario.append("id_cliente", input_id_cliente.value);

            const respuesta = await fetch("/ventas/validar_identificador/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            if (resultado.existe) {
                identificador.setCustomValidity("Este identificador ya se encuentra registrado.");
                identificador.classList.add("is-invalid");
                identificador.classList.remove("is-valid");

                msg.textContent = "Este identificador ya se encuentra registrado.";
                msg.classList.add("error");
                msg.classList.remove("exito");
            } else {
                identificador.setCustomValidity("");
                identificador.classList.add("is-valid");
                identificador.classList.remove("is-invalid");

                msg.textContent = "Identificador disponible.";
                msg.classList.add("exito");
                msg.classList.remove("error");
            }
        } catch (error) {
            console.error(error);

            identificador.setCustomValidity(
                "No se pudo comprobar el identificador. Inténtelo nuevamente."
            );
            identificador.classList.add("is-invalid");
            identificador.classList.remove("is-valid");

            msg.textContent = "No se pudo validar el identificador.";
            msg.classList.add("error");
            msg.classList.remove("exito");
        }
    }

    function programar_validacion_identificador() {
        clearTimeout(temporizador_identificador);

        temporizador_identificador = setTimeout(() => {
            validar_identificador(
                select_tipo_identificador,
                input_identificador,
                contenedor_mensaje_identificador
            );
        }, 350);
    }

    input_identificador.addEventListener("input", programar_validacion_identificador);

    select_tipo_identificador.addEventListener("change", () => {
        input_identificador.value = "";
        input_identificador.setCustomValidity("");
        input_identificador.classList.remove("is-valid", "is-invalid");

        contenedor_mensaje_identificador.textContent = "";
        contenedor_mensaje_identificador.classList.remove("exito", "error");
    });

    formulario_actualizar.addEventListener("submit", async (e) => {
        e.preventDefault();

        try {
            const formulario = new FormData(formulario_actualizar);

            const respuesta = await fetch("/ventas/actualizar_clientes_ventas/", {
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

            if (resultado.estado !== "exito") return;

            formulario_actualizar.reset();

            select_tipo_cliente.value = "";
            actualizar_controles_cliente();

            bloquearFormularioActualizar(true);

            contenedor_mensaje_correo.innerHTML = "";
            contenedor_mensaje_identificador.innerHTML = "";
            contenedor_mensaje_telefono.innerHTML = "";

        } catch (error) {
            console.error(error);
        }
    });

});