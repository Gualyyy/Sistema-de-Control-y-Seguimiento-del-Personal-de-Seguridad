document.addEventListener("DOMContentLoaded", () => {

    const formulario_busqueda = document.getElementById("formulario_busqueda");
    const formulario_actualizar = document.getElementById("formulario_actualizar");

    const select_tipo_cliente_b = document.getElementById("tipo_cliente_b");
    const select_tipo_identificador_b = document.getElementById("tipo_identificador_b");
    const input_identificador_b = document.getElementById("identificador_b");

    const input_id_usuario = document.getElementById("id_usuario");

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

    const select_condicion_residencia = document.getElementById("condicion_residencia");
    const select_municipio_residencia = document.getElementById("municipio_residencia");
    const select_parroquia_residencia = document.getElementById("parroquia_residencia");
    const textarea_direccion_domicilio = document.getElementById("direccion_domicilio");

    const contador_residencia = document.getElementById("contador_residencia");

    configurarIdentificador(input_identificador_b, select_tipo_identificador_b, select_tipo_cliente_b);
    configurarIdentificador(input_identificador, select_tipo_identificador, select_tipo_cliente);

    configurarTelefono(input_num_telefono, select_prefijo);
    configurarCorreo(input_correo, select_dominio)

    const municipios = [
        "Barinas", "Pedraza", "Antonio José de Sucre", "Ezequiel Zamora", "Bolívar", "Alberto Arvelo Torrealba", "Rojas", "Obispo", "Sosa", "Cruz Paredes", "Arismendi", "Andrés Eloy Blanco"
    ];

    const parroquiasPorMunicipioResidencia = {
        "Barinas": ["Alfredo Arvelo Larriva", "San Silvestre", "Santa Inés", "Santa Lucía", "Torunos", "El Carmen", "Alto Barinas", "Rómulo Betancourt", "Corazón de Jesús", "Ramón Ignacio Méndez", "Manuel Palacio Fajardo", "Juan Antonio Rodríguez Domínguez", "Domingo Ortiz de Páez"],
        "Pedraza": ["Ciudad Bolivia", "Ignacio Briceño", "José Félix Ribas", "Páez"],
        "Antonio José de Sucre": ["Ticoporo", "Andrés Bello", "Nicolás Pulido"],
        "Ezequiel Zamora": ["Santa Bárbara", "José Ignacio del Pumar", "Pedro Briceño Méndez", "Ramón Ignacio Méndez"],
        "Bolívar": ["Barinitas", "Altamira de Cáceres", "Calderas"],
        "Alberto Arvelo Torrealba": ["Sabaneta", "El Real"],
        "Rojas": ["Libertad", "Dolores", "Palacios Fajardo", "Santa Rosa", "Simón Rodríguez"],
        "Obispo": ["Obispos", "El Real", "La Luz", "Los Guasimitos"],
        "Sosa": ["Ciudad de Nutrias", "El Regalo", "Puerto de Nutrias", "Santa Catalina", "Simón Bolívar"],
        "Cruz Paredes": ["Barrancas", "El Socorro", "Masparrito"],
        "Arismendi": ["Arismendi", "Guadarrama", "La Unión", "San Antonio"],
        "Andrés Eloy Blanco": ["El Cantón", "Santa Cruz de Guacas", "Puerto Vivas", "Dominga Ortiz de Páez"]
    };

    function cargarMunicipiosResidencia(municipioSeleccionado = "Barinas") {
        select_municipio_residencia.innerHTML = "";

        municipios.forEach(municipio => {
            const option = document.createElement("option");
            option.value = municipio;
            option.textContent = municipio;
            if (municipio === municipioSeleccionado) {
                option.selected = true;
            }
            select_municipio_residencia.appendChild(option);
        });
    }

    function cargarParroquiasResidencia(parroquiaSeleccionada = "El Carmen") {
        const municipio = select_municipio_residencia.value;

        select_parroquia_residencia.innerHTML = "";

        if (municipio in parroquiasPorMunicipioResidencia) {

            parroquiasPorMunicipioResidencia[municipio].forEach(parroquia => {
                const option = document.createElement("option");
                option.value = parroquia;
                option.textContent = parroquia;
                if (parroquia === parroquiaSeleccionada) {
                    option.selected = true;
                }
                select_parroquia_residencia.appendChild(option);
            });
        }
    }

    // CARGA INICIAL
    cargarMunicipiosResidencia();
    cargarParroquiasResidencia();

    // CAMBIOS MANUALES
    select_municipio_residencia.addEventListener("change", () => {
        cargarParroquiasResidencia();
    });

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
        btn_actualizar,
        select_condicion_residencia,
        select_municipio_residencia,
        select_parroquia_residencia,
        textarea_direccion_domicilio
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

    textarea_direccion_domicilio.addEventListener("input", (e) => {
        soloTexto(e.target);
    });

    textarea_direccion_domicilio.addEventListener("input", () => {
        textarea_direccion_domicilio.value = textarea_direccion_domicilio.value.replace(
            /[^a-zA-ZáéíóúÁÉÍÓÚñÑ0-9\s.,:;()\-*]/g,
            ""
        );

        actualizarContador(textarea_direccion_domicilio, contador_residencia);
    });

    function actualizarContador(textarea, contador) {
        contador.textContent = textarea.value.length;
    }

    formulario_busqueda.addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
            const formulario = new FormData(formulario_busqueda);

            const respuesta = await fetch("/buscar_datos_cliente/", {
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

            input_id_usuario.value = resultado.cliente.id_usuario;

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

            const option_condicion_residencia = document.createElement("option");
            option_condicion_residencia.value = resultado.cliente.residencia.condicion_residencia;
            option_condicion_residencia.textContent = resultado.cliente.residencia.condicion_residencia;
            option_condicion_residencia.selected = true;
            option_condicion_residencia.hidden = true;
            select_condicion_residencia.append(option_condicion_residencia);

            const option_municipio_residencia = document.createElement("option");
            option_municipio_residencia.value = resultado.cliente.residencia.municipio;
            option_municipio_residencia.textContent = resultado.cliente.residencia.municipio;
            option_municipio_residencia.selected = true;
            option_municipio_residencia.hidden = true;
            select_municipio_residencia.append(option_municipio_residencia);

            const option_parroquia_residencia = document.createElement("option");
            option_parroquia_residencia.value = resultado.cliente.residencia.parroquia;
            option_parroquia_residencia.textContent = resultado.cliente.residencia.parroquia;
            option_parroquia_residencia.selected = true;
            option_parroquia_residencia.hidden = true;
            select_parroquia_residencia.append(option_parroquia_residencia);

            cargarMunicipiosResidencia(resultado.cliente.residencia.municipio);
            cargarParroquiasResidencia(resultado.cliente.residencia.parroquia);

            textarea_direccion_domicilio.value = resultado.cliente.residencia.direccion;

            actualizarContador(textarea_direccion_domicilio, contador_residencia);

            formulario_busqueda.reset();
        } catch (error) {
            console.error(error);
        }
    });

    function actualizar_controles_cliente() {
        const tipo_cliente = select_tipo_cliente.value;

        controles_individuo.hidden = tipo_cliente !== "NATURAL";
        control_empresa.hidden = tipo_cliente !== "EMPRESA";

        controles_individuo.classList.toggle(
            "activo",
            tipo_cliente === "NATURAL"
        );

        control_empresa.classList.toggle(
            "activo",
            tipo_cliente === "EMPRESA"
        );

        input_nombre_cliente.required = tipo_cliente === "NATURAL";
        input_apellido_cliente.required = tipo_cliente === "NATURAL";
        input_nombre_empresa.required = tipo_cliente === "EMPRESA";

        if (tipo_cliente === "NATURAL") {
            input_nombre_empresa.value = "";
        } else if (tipo_cliente === "EMPRESA") {
            input_nombre_cliente.value = "";
            input_apellido_cliente.value = "";
        } else {
            input_nombre_cliente.value = "";
            input_apellido_cliente.value = "";
            input_nombre_empresa.value = "";
        }

        input_identificador.setCustomValidity("");

        input_identificador.classList.remove(
            "is-valid",
            "is-invalid"
        );

        contenedor_mensaje_identificador.textContent = "";

        contenedor_mensaje_identificador.classList.remove(
            "exito",
            "error"
        );

        if (
            select_tipo_identificador.value &&
            input_identificador.value.trim() &&
            tipo_cliente
        ) {
            validar_identificador(
                select_tipo_identificador,
                input_identificador,
                contenedor_mensaje_identificador
            );
        }
    }

    select_tipo_cliente.value = "NATURAL";

    actualizar_controles_cliente();

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

        const controlador = new AbortController();
        controlador_telefono = controlador;

        try {
            const formulario = new FormData();
            formulario.append("prefijo", valorPrefijo);
            formulario.append("numeros", valorNumero);
            formulario.append("id_usuario", input_id_usuario.value);

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
                numero.setCustomValidity(
                    "Este número telefónico ya está registrado."
                );

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
                console.error("Error al validar el teléfono:", error);
            }
        } finally {
            if (controlador_telefono === controlador) {
                controlador_telefono = null;
            }
        }
    }

    input_num_telefono.addEventListener("input", () => {
        validar_telefono(
            select_prefijo,
            input_num_telefono,
            contenedor_mensaje_telefono
        );
    });

    select_prefijo.addEventListener("change", () => {
        validar_telefono(
            select_prefijo,
            input_num_telefono,
            contenedor_mensaje_telefono
        );
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
            formulario.append("id_usuario", input_id_usuario.value);

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

            if (
                correo.value.trim().toLowerCase() !== valorCorreo ||
                dominio.value.trim().toLowerCase() !== valorDominio
            ) {
                return;
            }

            if (resultado.existe) {
                correo.setCustomValidity(
                    "Este correo electrónico ya está registrado."
                );
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
                console.error("Error al validar el correo:", error);
            }
        } finally {
            if (controlador_correo === controlador) {
                controlador_correo = null;
            }
        }
    }

    input_correo.addEventListener("input", () => {
        validar_correo(
            input_correo,
            select_dominio,
            contenedor_mensaje_correo
        );
    });

    select_dominio.addEventListener("change", () => {
        validar_correo(
            input_correo,
            select_dominio,
            contenedor_mensaje_correo
        );
    });

    let controlador_identificador = null;

    async function validar_identificador(tipo_identificador, identificador, msg) {
        const tipo = tipo_identificador.value.trim().toUpperCase();
        const valor = identificador.value.trim();
        const tipo_cliente = select_tipo_cliente.value.trim().toUpperCase();

        if (controlador_identificador) {
            controlador_identificador.abort();
            controlador_identificador = null;
        }

        if (!tipo || !valor || !tipo_cliente) {
            msg.textContent = "";
            msg.classList.remove("exito", "error");

            identificador.setCustomValidity("");
            identificador.classList.remove("is-valid", "is-invalid");
            return;
        }

        const controlador = new AbortController();
        controlador_identificador = controlador;

        try {
            const formulario = new FormData();
            formulario.append("tipo_identificador", tipo);
            formulario.append("identificador", valor);
            formulario.append("tipo_cliente", tipo_cliente);
            formulario.append("id_usuario", input_id_usuario.value);

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

            if (identificador.value.trim() !== valor ||
                tipo_identificador.value.trim().toUpperCase() !== tipo ||
                select_tipo_cliente.value.trim().toUpperCase() !== tipo_cliente) {
                return;
            }

            if (resultado.existe) {
                identificador.setCustomValidity(
                    "Este identificador ya se encuentra registrado."
                );
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
            if (error.name === "AbortError") {
                return;
            }

            console.error(error);

            identificador.setCustomValidity(
                "No se pudo comprobar el identificador. Inténtelo nuevamente."
            );
            identificador.classList.add("is-invalid");
            identificador.classList.remove("is-valid");

            msg.textContent = "No se pudo validar el identificador.";
            msg.classList.add("error");
            msg.classList.remove("exito");
        } finally {
            if (controlador_identificador === controlador) {
                controlador_identificador = null;
            }
        }
    }

    select_tipo_identificador.addEventListener("change", () => {
        if (controlador_identificador) {
            controlador_identificador.abort();
            controlador_identificador = null;
        }

        input_identificador.value = "";
        input_identificador.setCustomValidity("");
        input_identificador.classList.remove("is-valid", "is-invalid");

        contenedor_mensaje_identificador.textContent = "";
        contenedor_mensaje_identificador.classList.remove("exito", "error");
    });

    select_tipo_cliente.addEventListener("change", () => {
        if (controlador_identificador) {
            controlador_identificador.abort();
            controlador_identificador = null;
        }

        input_identificador.setCustomValidity("");
        input_identificador.classList.remove("is-valid", "is-invalid");

        contenedor_mensaje_identificador.textContent = "";
        contenedor_mensaje_identificador.classList.remove("exito", "error");

        if (input_identificador.value.trim()) {
            validar_identificador(
                select_tipo_identificador,
                input_identificador,
                contenedor_mensaje_identificador
            );
        }
    });

    input_identificador.addEventListener("input", () => {
        validar_identificador(
            select_tipo_identificador,
            input_identificador,
            contenedor_mensaje_identificador
        );
    });

    formulario_actualizar.addEventListener("submit", async (e) => {
        e.preventDefault();

        try {
            const formulario = new FormData(formulario_actualizar);

            const respuesta = await fetch("/actualizar_clientes_ventas/", {
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

            select_tipo_cliente.value = "NATURAL";

            bloquearFormularioActualizar(true);

            contenedor_mensaje_correo.innerHTML = "";
            contenedor_mensaje_identificador.innerHTML = "";
            contenedor_mensaje_telefono.innerHTML = "";
        } catch (error) {
            console.error(error);
        }
    });

});