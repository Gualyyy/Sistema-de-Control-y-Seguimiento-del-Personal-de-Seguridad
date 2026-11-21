
document.addEventListener("DOMContentLoaded", () => {
    const select_bancos = document.getElementById("bancos");

    const input_cedula_identidad = document.getElementById("cedula_identidad");
    const select_nacionalidad = document.getElementById("nacionalidad");

    const input_num_telefono = document.getElementById("num_telefono");
    const select_prefijo = document.getElementById("prefijo");

    const select_metodos_pagos = document.getElementById("metodos_pagos");

    const contenedor_transferencia = document.getElementById("contenedor_transferencia");
    const contenedor_mensaje_num_cuenta = document.getElementById("contenedor_mensaje_num_cuenta");
    const input_numeros_cuenta = document.getElementById("numeros_cuenta");
    const select_tipo_cuenta = document.getElementById("tipo_cuenta");

    const formulario_registrar = document.getElementById("formulario_registrar");

    configurarCedula(input_cedula_identidad, select_nacionalidad);
    configurarTelefono(input_num_telefono, select_prefijo);

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
            console.log(resultado);

            select_metodos_pagos.innerHTML = "";

            resultado.metodos.forEach(metodo => {
                const option = document.createElement("option");
                option.value = metodo.id_metodo;
                option.textContent = metodo.nombre;
                select_metodos_pagos.append(option);
            });

            configurarCamposTransferencia();
        } catch (error) {
            console.error(error);
        }
    }
    metodos_registrados();

    let controlador_numero_cuenta = null;

    function configurarCamposTransferencia() {
        const metodo_seleccionado = select_metodos_pagos
            .options[select_metodos_pagos.selectedIndex]
            ?.textContent.trim().toUpperCase();

        const es_transferencia = metodo_seleccionado === "TRANSFERENCIA BANCARIA";

        contenedor_transferencia.hidden = !es_transferencia;

        input_numeros_cuenta.required = es_transferencia;
        select_tipo_cuenta.required = es_transferencia;

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

    async function validar_numero_cuenta() {
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
            input_numeros_cuenta.setCustomValidity(
                "El número de cuenta debe contener exactamente 20 dígitos."
            );

            input_numeros_cuenta.classList.add("is-invalid");
            input_numeros_cuenta.classList.remove("is-valid");

            contenedor_mensaje_num_cuenta.textContent = "El número de cuenta debe contener exactamente 20 dígitos.";

            contenedor_mensaje_num_cuenta.classList.add("error");
            contenedor_mensaje_num_cuenta.classList.remove("exito");

            return false;
        }

        const controlador = new AbortController();
        controlador_numero_cuenta = controlador;

        try {
            const formulario = new FormData();
            formulario.append("numero_cuenta", valor);

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
                input_numeros_cuenta.setCustomValidity(
                    "Este número de cuenta ya se encuentra registrado."
                );

                input_numeros_cuenta.classList.add("is-invalid");
                input_numeros_cuenta.classList.remove("is-valid");

                contenedor_mensaje_num_cuenta.textContent = "Este número de cuenta ya se encuentra registrado.";

                contenedor_mensaje_num_cuenta.classList.add("error");
                contenedor_mensaje_num_cuenta.classList.remove("exito");

                return false;
            }

            input_numeros_cuenta.setCustomValidity("");

            input_numeros_cuenta.classList.add("is-valid");
            input_numeros_cuenta.classList.remove("is-invalid");

            contenedor_mensaje_num_cuenta.textContent = "Número de cuenta disponible.";

            contenedor_mensaje_num_cuenta.classList.add("exito");
            contenedor_mensaje_num_cuenta.classList.remove("error");

            return true;

        } catch (error) {
            if (error.name === "AbortError") {
                return false;
            }

            console.error(
                "Error al validar el número de cuenta:",
                error
            );

            input_numeros_cuenta.setCustomValidity(
                "No se pudo validar el número de cuenta."
            );

            input_numeros_cuenta.classList.add("is-invalid");
            input_numeros_cuenta.classList.remove("is-valid");

            contenedor_mensaje_num_cuenta.textContent =
                "No se pudo validar el número de cuenta. Inténtelo nuevamente.";

            contenedor_mensaje_num_cuenta.classList.add("error");
            contenedor_mensaje_num_cuenta.classList.remove("exito");

            return false;

        } finally {
            if (controlador_numero_cuenta === controlador) {
                controlador_numero_cuenta = null;
            }
        }
    }

    function solo_numeros(input) {
        input.value = input.value.replace(/\D/g, "");
    }

    input_numeros_cuenta.addEventListener("input", () => {
        solo_numeros(input_numeros_cuenta);
        validar_numero_cuenta();
    });

    formulario_registrar.addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
            const formulario = new FormData(formulario_registrar);

            const respuesta = await fetch("/ventas/registrar_cuentas/", {
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

            await Swal.fire({
                title: resultado.title,
                text: resultado.descripcion,
                icon: resultado.icon
            });

            formulario_registrar.reset();
            contenedor_mensaje_num_cuenta.innerHTML = "";

            contenedor_transferencia.hidden = true;
        } catch (error) {
            console.error(error);
        }
    });

});
