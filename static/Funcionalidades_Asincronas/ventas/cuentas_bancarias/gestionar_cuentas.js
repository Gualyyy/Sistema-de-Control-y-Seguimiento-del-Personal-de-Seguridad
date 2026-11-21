document.addEventListener("DOMContentLoaded", () => {

    const formulario_actualizar = document.getElementById("formulario_actualizar");

    const select_metodos_pagos = document.getElementById("metodos_pagos");
    const contenedor_cuentas = document.getElementById("contenedor_cuentas");

    const dialogo_gestionar = document.getElementById("dialogo_gestionar");
    const btn_cerrar = document.getElementById("btn_cerrar");

    const id_cuenta = document.getElementById("id_cuenta");

    const select_bancos = document.getElementById("bancos");
    const metodos_pagos = document.getElementById("metodos");

    const select_nacionalidad = document.getElementById("nacionalidad");
    const input_cedula_identidad = document.getElementById("cedula_identidad");

    const select_prefijo = document.getElementById("prefijo");
    const input_num_telefono = document.getElementById("num_telefono");

    const contenedor_transferencia = document.getElementById("contenedor_transferencia");
    const input_numeros_cuenta = document.getElementById("numeros_cuenta");
    const select_tipo_cuenta = document.getElementById("tipo_cuenta");

    const contenedor_mensaje_num_cuenta = document.getElementById("contenedor_mensaje_num_cuenta");

    const btn_ret = document.querySelector(".btn_retroceder");
    const btn_av = document.querySelector(".btn_avanzar");

    configurarCedula(input_cedula_identidad, select_nacionalidad);
    configurarTelefono(input_num_telefono, select_prefijo);

    let cuentas_recibidas = [];
    let pagina_actual = 1;
    const filas_por_pagina = 10;
    let metodo = "";

    const bancos = [
        "Banco de Venezuela", "Bancaribe", "Banco Nacional de Credito", "Bancamiga",
        "Venezolano de Credito", "Banco Plaza", "Banco del Tesoro", "Banco Activo Universal",
        "BANFANB", "Banesco", "BBVA Provincial", "Banco Exterior",
        "Banco Digital de los Trabajadores", "Mercantil", "Banplus",
        "Banco Sofitasa", "100% Banco"
    ];

    function bancos_registrados() {
        select_bancos.innerHTML = "";

        bancos.forEach(banco => {
            const option = document.createElement("option");
            option.value = banco;
            option.textContent = banco;
            select_bancos.append(option);
        });
    }
    bancos_registrados();

    async function metodos_registrados() {
        try {
            const respuesta = await fetch("/ventas/metodos_registrados/");
            const resultado = await respuesta.json();

            select_metodos_pagos.innerHTML = "";
            metodos_pagos.innerHTML = "";

            resultado.metodos.forEach(metodo => {
                const option_busqueda = document.createElement("option");
                option_busqueda.value = metodo.id_metodo;
                option_busqueda.textContent = metodo.nombre;
                select_metodos_pagos.append(option_busqueda);

                const option_actualizar = document.createElement("option");
                option_actualizar.value = metodo.id_metodo;
                option_actualizar.textContent = metodo.nombre;
                metodos_pagos.append(option_actualizar);
            });
        } catch (error) {
            console.error(error);
        }
    }
    metodos_registrados();

    metodos_pagos.addEventListener("change", async () => {
        metodo = metodos_pagos.value;

        cuentas_registradas();
    });

    function mostrarCuentas() {
        contenedor_cuentas.innerHTML = "";

        const inicio = (pagina_actual - 1) * filas_por_pagina;
        const final = inicio + filas_por_pagina;

        const cuentas_pagina = cuentas_recibidas.slice(inicio, final);

        if (cuentas_pagina.length === 0) {
            contenedor_cuentas.innerHTML = `
                <tr>
                    <td colspan="6" class="texto_sin_registros">
                        No hay cuentas de destino registradas.
                    </td>
                </tr>
            `;

            actualizarBotones();
            return;
        }

        cuentas_pagina.forEach((cuenta, index) => {
            const fila = document.createElement("tr");
            fila.dataset.id = cuenta.id_cuenta_destino;

            fila.innerHTML = `
                <td>${inicio + index + 1}</td>
                <td>${cuenta.metodo_pago}</td>
                <td>${cuenta.banco}</td>
                <td>
                    <button type="button"
                        class="btn_tabla ${cuenta.activo ? 'estado_activo' : 'estado_inactivo'}"
                        data-id="${cuenta.id_cuenta_destino}"
                        data-estado="${cuenta.activo}">
                        ${cuenta.activo ? 'Activo' : 'Inactivo'}
                    </button>
                </td>
                <td>
                    <button type="button"
                        class="btn_tabla btn_actualizar_cuenta"
                        data-id="${cuenta.id_cuenta_destino}">
                        <i class="fa-solid fa-pen-to-square"></i>
                        Actualizar
                    </button>
                </td>
            `;

            contenedor_cuentas.appendChild(fila);
        });

        actualizarBotones();
    }

    function actualizarBotones() {
        const total_paginas = Math.ceil(
            cuentas_recibidas.length / filas_por_pagina
        );

        btn_ret.disabled = pagina_actual === 1;

        btn_av.disabled = pagina_actual >= total_paginas;
    }

    btn_ret.addEventListener("click", () => {
        if (pagina_actual > 1) {
            pagina_actual--;
            mostrarCuentas();
        }
    });

    btn_av.addEventListener("click", () => {
        const total_paginas = Math.ceil(
            cuentas_recibidas.length / filas_por_pagina
        );

        if (pagina_actual < total_paginas) {
            pagina_actual++;
            mostrarCuentas();
        }
    });

    function soloNumeros(input) {
        input.value = input.value.replace(/[^0-9]/g, '');
    }

    input_numeros_cuenta.addEventListener("input", () => {
        soloNumeros(input_numeros_cuenta);
    });

    async function cuentas_registradas() {
        try {
            const formulario = new FormData();
            formulario.append("metodo", metodo);

            const respuesta = await fetch("/ventas/visualizar_cuentas/", {
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

            cuentas_recibidas = resultado.cuentas || [];
            pagina_actual = 1;

            mostrarCuentas();

        } catch (error) {
            console.error(error);

            cuentas_recibidas = [];
            pagina_actual = 1;

            mostrarCuentas();
        }
    }
    cuentas_registradas();

    async function validar_numero_cuenta() {
        if (contenedor_transferencia.hidden) {
            input_numeros_cuenta.setCustomValidity("");
            return true;
        }

        const valor = input_numeros_cuenta.value.trim();

        if (controlador_numero_cuenta) {
            controlador_numero_cuenta.abort();
            controlador_numero_cuenta = null;
        }

        if (!valor) {
            input_numeros_cuenta.setCustomValidity("");

            input_numeros_cuenta.classList.remove(
                "is-valid",
                "is-invalid"
            );

            contenedor_mensaje_num_cuenta.textContent = "";
            contenedor_mensaje_num_cuenta.classList.remove(
                "exito",
                "error"
            );

            return true;
        }

        if (!/^\d{20}$/.test(valor)) {
            const mensaje = "El número de cuenta debe contener exactamente 20 dígitos.";
            input_numeros_cuenta.setCustomValidity(mensaje);

            input_numeros_cuenta.classList.add("is-invalid");
            input_numeros_cuenta.classList.remove("is-valid");

            contenedor_mensaje_num_cuenta.textContent = mensaje;

            contenedor_mensaje_num_cuenta.classList.add("error");
            contenedor_mensaje_num_cuenta.classList.remove("exito");

            return false;
        }

        input_numeros_cuenta.setCustomValidity("");

        const controlador = new AbortController();
        controlador_numero_cuenta = controlador;

        try {
            const formulario = new FormData();
            formulario.append("numero_cuenta", valor);
            formulario.append("id_cuenta", id_cuenta.value);

            const respuesta = await fetch("/ventas/validar_numero_cuenta/", {
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

            if (input_numeros_cuenta.value.trim() !== valor) {
                return false;
            }

            if (resultado.existe) {
                const mensaje = "Este número ya está registrado, ingrese otro número de cuenta.";
                input_numeros_cuenta.setCustomValidity(mensaje);

                input_numeros_cuenta.classList.add("is-invalid");
                input_numeros_cuenta.classList.remove("is-valid");

                contenedor_mensaje_num_cuenta.textContent = mensaje;

                contenedor_mensaje_num_cuenta.classList.add("error");
                contenedor_mensaje_num_cuenta.classList.remove("exito");
                return false;

            } else {
                input_numeros_cuenta.setCustomValidity("");

                input_numeros_cuenta.classList.add("is-valid");
                input_numeros_cuenta.classList.remove("is-invalid");

                contenedor_mensaje_num_cuenta.textContent = "Número de cuenta disponible.";

                contenedor_mensaje_num_cuenta.classList.add("exito");
                contenedor_mensaje_num_cuenta.classList.remove("error");
                return true;
            }

        } catch (error) {
            if (error.name !== "AbortError") {
                console.error(
                    "Error al validar el número de cuenta:",
                    error
                );

                input_numeros_cuenta.setCustomValidity(
                    "No se pudo validar el número de cuenta."
                );

                input_numeros_cuenta.classList.add("is-invalid");
                input_numeros_cuenta.classList.remove("is-valid");

                contenedor_mensaje_num_cuenta.textContent = "No se pudo validar el número de cuenta. Inténtelo nuevamente.";

                contenedor_mensaje_num_cuenta.classList.add("error");
                contenedor_mensaje_num_cuenta.classList.remove("exito");
            }

            return false;
        } finally {
            if (controlador_numero_cuenta === controlador) {
                controlador_numero_cuenta = null;
            }
        }
    }

    let controlador_numero_cuenta = null;

    function configurarCamposTransferencia(tipo_cuenta_almacenado = null) {
        const metodo_seleccionado = select_metodos_pagos
            .options[select_metodos_pagos.selectedIndex]
            ?.textContent.trim().toUpperCase();

        const es_transferencia = metodo_seleccionado === "TRANSFERENCIA BANCARIA";

        contenedor_transferencia.hidden = !es_transferencia;

        input_numeros_cuenta.required = es_transferencia;
        select_tipo_cuenta.required = es_transferencia;

        if (es_transferencia) {
            const tipo_cuenta = tipo_cuenta_almacenado?.trim().toUpperCase();

            select_tipo_cuenta.value = tipo_cuenta || "";
        }

        if (!es_transferencia) {
            if (controlador_numero_cuenta) {
                controlador_numero_cuenta.abort();
                controlador_numero_cuenta = null;
            }

            input_numeros_cuenta.setCustomValidity("");
            input_numeros_cuenta.classList.remove("is-valid", "is-invalid");

            contenedor_mensaje_num_cuenta.textContent = "";
            contenedor_mensaje_num_cuenta.classList.remove("exito", "error");
        }
    }

    select_metodos_pagos.addEventListener("change", () => {
        configurarCamposTransferencia();
    });

    function solo_numeros(input) {
        input.value = input.value.replace(/\D/g, "");
    }

    input_numeros_cuenta.addEventListener("input", async () => {
        solo_numeros(input_numeros_cuenta);
        validar_numero_cuenta();
    });

    // EVENTOS DE LA TABLA DE CUENTAS
    contenedor_cuentas.addEventListener("click", async (e) => {
        const btn_actualizar = e.target.closest(".btn_actualizar_cuenta");
        if (btn_actualizar) {
            id_cuenta.value = btn_actualizar.dataset.id;

            await buscar_cuentas();

            dialogo_gestionar.showModal();
            return;
        }

        const btn_estado = e.target.closest(".estado_activo, .estado_inactivo");
        if (btn_estado) {
            id_cuenta.value = btn_estado.dataset.id;
            await actualizar_estado();
            return;
        }
    });

    async function buscar_cuentas() {
        try {
            const formulario = new FormData();
            formulario.append("id_cuenta", id_cuenta.value);

            const respuesta = await fetch("/ventas/buscar_cuentas/", {
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
                await Swal.fire({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon
                });
                return;
            }
            const cuenta = resultado.cuenta;

            id_cuenta.value = cuenta.id_cuenta_destino;

            const opcion_banco = document.createElement("option");
            opcion_banco.value = cuenta.banco;
            opcion_banco.textContent = cuenta.banco;
            opcion_banco.hidden = true;
            opcion_banco.selected = true;
            select_bancos.append(opcion_banco);

            const opcion_metodo = document.createElement("option");
            opcion_metodo.value = cuenta.id_metodo;
            opcion_metodo.textContent = cuenta.metodo_pago;
            opcion_metodo.hidden = true;
            opcion_metodo.selected = true;
            select_metodos_pagos.append(opcion_metodo);

            const [nacionalidad, num_cedula] = cuenta.documento.split("-");

            const opcion_nacionalidad = document.createElement("option");
            opcion_nacionalidad.value = nacionalidad;
            opcion_nacionalidad.textContent = nacionalidad;
            opcion_nacionalidad.hidden = true;
            opcion_nacionalidad.selected = true;
            select_nacionalidad.append(opcion_nacionalidad);

            input_cedula_identidad.value = num_cedula;

            const [prefijo, num_telefonico] = cuenta.telefono.split("-");

            const opcion_prefijo = document.createElement("option");
            opcion_prefijo.value = prefijo;
            opcion_prefijo.textContent = prefijo;
            opcion_prefijo.hidden = true;
            opcion_prefijo.selected = true;
            select_prefijo.append(opcion_prefijo);

            input_num_telefono.value = num_telefonico;

            const opcion_tipo_cuenta = document.createElement("option");
            opcion_tipo_cuenta.value = cuenta.tipo_cuenta;
            opcion_tipo_cuenta.textContent = cuenta.tipos_cuenta_valor;
            opcion_tipo_cuenta.hidden = true;
            opcion_tipo_cuenta.selected = true;
            select_tipo_cuenta.append(opcion_tipo_cuenta);

            configurarCamposTransferencia(cuenta.tipo_cuenta);

            input_numeros_cuenta.value = cuenta.numero_cuenta;
        } catch (error) {
            console.error(error);
        }
    }

    async function actualizar_estado() {
        try {
            const formulario = new FormData();
            formulario.append("id_cuenta", id_cuenta.value);

            const respuesta = await fetch("/ventas/estado_cuenta/", {
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

            Swal.fire({
                title: resultado.title,
                text: resultado.descripcion,
                icon: resultado.icon
            });

            await cuentas_registradas();
        } catch (error) {
            console.error(error);
        }
    }

    let temporizador_mensaje_actualizar = null;

    formulario_actualizar.addEventListener("submit", async (e) => {
        e.preventDefault();

        const numero_cuenta_valido = await validar_numero_cuenta();
        if (!numero_cuenta_valido) {
            input_numeros_cuenta.reportValidity();
            return;
        }

        if (!formulario_actualizar.reportValidity()) {
            return;
        }

        try {
            const formulario = new FormData(formulario_actualizar);

            const respuesta = await fetch("/ventas/actualizar_cuentas/", {
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

            if (temporizador_mensaje_actualizar) {
                clearInterval(temporizador_mensaje_actualizar);
                temporizador_mensaje_actualizar = null;
            }

            await mostrar_mensaje_temporal(
                "contenedor_mensajes_actualizar",
                resultado.descripcion,
                resultado.estado === "exito" ? "exito" : "error"
            );

            if (resultado.estado === "exito") {
                await cuentas_registradas();
            }

            contenedor_mensaje_num_cuenta.innerHTML = "";
        } catch (error) {
            console.error(error);

            if (temporizador_mensaje_actualizar) {
                clearInterval(temporizador_mensaje_actualizar);
                temporizador_mensaje_actualizar = null;
            }

            await mostrar_mensaje_temporal(
                "contenedor_mensajes_actualizar",
                "Ocurrió un error al intentar actualizar la cuenta.",
                "error"
            );
        }
    });

    // MENSAJES TEMPORALES

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

                    if (id_contenedor === "contenedor_mensajes_actualizar") {
                        temporizador_mensaje_actualizar = null;
                    }

                    ocultar_mensaje_dialogo(id_contenedor);
                    resolve();
                    return;
                }

                contador.textContent = ` ${restante} s`;
            }, 1000);

            if (id_contenedor === "contenedor_mensajes_actualizar") {
                temporizador_mensaje_actualizar = intervalo;
            }
        });
    }

    function ocultar_mensaje_dialogo(id_contenedor) {
        const contenedor = document.getElementById(id_contenedor);

        if (!contenedor) return;

        contenedor.hidden = true;
        contenedor.replaceChildren();
    }

    btn_cerrar.addEventListener("click", () => {
        dialogo_gestionar.close();
    });

});