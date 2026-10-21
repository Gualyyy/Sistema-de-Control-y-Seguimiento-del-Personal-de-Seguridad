document.addEventListener("DOMContentLoaded", () => {

    const contenedor_clientes = document.getElementById("contenedor_clientes");

    const select_tipo_cliente_b = document.getElementById("tipo_cliente_b");
    const select_tipo_identificador_b = document.getElementById("tipo_identificador_b");
    const input_identificador_b = document.getElementById("identificador_b");

    const dialogo_detalle = document.getElementById("dialogo_detalle");
    const btn_cerrar_detalle = document.getElementById("btn_cerrar_detalle");

    const btn_lista_clientes_pdf = document.getElementById("lista_clientes_pdf");
    const btn_detalle_cliente_pdf = document.getElementById("detalle_cliente_pdf");

    const input_id_cliente = document.getElementById("id_cliente");
    const input_cliente_registrado = document.getElementById("cliente_registrado");
    const input_identificador = document.getElementById("identificador");
    const input_tipo_cliente = document.getElementById("tipo_cliente");
    const input_telefono = document.getElementById("telefono");
    const input_correo_electronico = document.getElementById("correo_electronico");
    const input_fecha_registro = document.getElementById("fecha_registro");

    const btn_retroceder = document.querySelector(".btn_ret");
    const btn_avanzar = document.querySelector(".btn_av");

    configurarIdentificador(input_identificador_b, select_tipo_identificador_b, select_tipo_cliente_b);

    let clientes_recibidos = [];
    let pagina_actual = 1;
    const filas_por_pagina = 10;

    let tipo_cliente = "", tipo_identificador = "", identificador = "";

    select_tipo_cliente_b.addEventListener("change", async () => {
        tipo_cliente = select_tipo_cliente_b.value;

        await clientes_registrados();
    });

    select_tipo_identificador_b.addEventListener("change", async () => {
        tipo_identificador = select_tipo_identificador_b.value;

        await clientes_registrados();
    });

    input_identificador_b.addEventListener("input", async () => {
        identificador = input_identificador_b.value;

        await clientes_registrados();
    });

    function mostrarClientes() {
        contenedor_clientes.innerHTML = "";

        const inicio = (pagina_actual - 1) * filas_por_pagina;
        const final = inicio + filas_por_pagina;

        const clientes_pagina = clientes_recibidos.slice(inicio, final);

        if (clientes_pagina.length === 0) {
            contenedor_clientes.innerHTML = `
                <tr>
                    <td colspan="4" class="texto_sin_registros">
                        No hay clientes registrados.
                    </td>
                </tr>
            `;

            actualizarBotones();
            return;
        }

        clientes_pagina.forEach((cliente, index) => {
            const fila = document.createElement("tr");
            fila.dataset.id_cliente = cliente.id_cliente;

            fila.innerHTML = `
                <td>${inicio + index + 1}</td>
                <td>${cliente.nombre_razon_social}</td>
                <td>${cliente.identificador}</td>
                <td>${cliente.tipo_cliente}</td>
            `;

            contenedor_clientes.appendChild(fila);
        });
        actualizarBotones();
    }

    function actualizarBotones() {
        const total_paginas = Math.ceil(
            clientes_recibidos.length / filas_por_pagina
        );

        btn_retroceder.disabled = pagina_actual === 1;
        btn_avanzar.disabled = pagina_actual >= total_paginas;
    }

    btn_retroceder.addEventListener("click", () => {
        if (pagina_actual > 1) {
            pagina_actual--;
            mostrarClientes();
        }
    });

    btn_avanzar.addEventListener("click", () => {
        const total_paginas = Math.ceil(
            clientes_recibidos.length / filas_por_pagina
        );

        if (pagina_actual < total_paginas) {
            pagina_actual++;
            mostrarClientes();
        }
    });

    async function clientes_registrados() {
        try {
            const formulario = new FormData();
            formulario.append("tipo_cliente", tipo_cliente);
            formulario.append("tipo_identificador", tipo_identificador);
            formulario.append("identificador", identificador);

            const respuesta = await fetch("/ventas/clientes_registrados_ventas/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            if (resultado.estado !== "exito") {
                return;
            }

            clientes_recibidos = resultado.clientes;
            pagina_actual = 1;

            mostrarClientes();
        } catch (error) {
            console.error(error);
        }
    }
    clientes_registrados();

    btn_cerrar_detalle.addEventListener("click", () => {
        dialogo_detalle.close();
    });

    contenedor_clientes.addEventListener("click", async (e) => {
        const fila = e.target.closest("tr");

        const id_cliente = fila.dataset.id_cliente;

        try {
            const formulario = new FormData();
            formulario.append("id_cliente", id_cliente);

            const respuesta = await fetch("/ventas/detalle_registro_cliente/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            input_id_cliente.value = resultado.cliente.id_cliente;
            input_cliente_registrado.value = resultado.cliente.nombre_razon_social;
            input_identificador.value = resultado.cliente.identificador;
            input_tipo_cliente.value = resultado.cliente.tipo_cliente;
            input_telefono.value = resultado.cliente.telefono;
            input_correo_electronico.value = resultado.cliente.correo;
            input_fecha_registro.value = resultado.cliente.fecha_registro;

            dialogo_detalle.showModal();
        } catch (error) {
            console.error(error);
        }
    });

    btn_lista_clientes_pdf.addEventListener("click", async () => {
        try {
            const formulario = new FormData();
            formulario.append("tipo_cliente", select_tipo_cliente_b.value);

            const respuesta = await fetch("/ventas/clientes_registrados_pdf/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector(
                        "[name=csrfmiddlewaretoken]"
                    ).value
                },
                body: formulario
            });

            const tipo_contenido = respuesta.headers.get("content-type") || "";

            if (tipo_contenido.includes("application/json")) {
                const resultado = await respuesta.json();

                Swal.fire({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon
                });
                return;
            }

            const archivo = await respuesta.blob();
            const url_pdf = URL.createObjectURL(archivo);

            window.open(url_pdf, "_blank");
        } catch (error) {
            console.error(error);
        }
    });

    btn_detalle_cliente_pdf.addEventListener("click", async () => {
        try {
            const formulario = new FormData();
            formulario.append("id_cliente", input_id_cliente.value);

            const respuesta = await fetch("/ventas/detalle_cliente_pdf/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector(
                        "[name=csrfmiddlewaretoken]"
                    ).value
                },
                body: formulario
            });

            const tipo_contenido = respuesta.headers.get("content-type") || "";

            if (tipo_contenido.includes("application/json")) {
                const resultado = await respuesta.json();

                Swal.fire({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon
                });
                return;
            }

            const archivo = await respuesta.blob();
            const url_pdf = URL.createObjectURL(archivo);

            window.open(url_pdf, "_blank");
        } catch (error) {
            console.error(error);
        }
    });

});