document.addEventListener("DOMContentLoaded", () => {

    const input_codigo_equipo = document.getElementById("codigo_equipo");
    const select_categorias_registradas = document.getElementById("categorias_registradas");
    const contenedor_historial = document.getElementById("contenedor_historial");

    const btn_retroceder = document.querySelector(".btn_ret");
    const btn_avanzar = document.querySelector(".btn_av");

    const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;

    let consulta_equipos_activa = null;
    let lista_historial = [];
    let pagina_actual = 1;

    const filas_por_pagina = 10;

    async function categoria_equipo_registrados() {
        try {
            const respuesta = await fetch("/asignaciones/categoria_registrados/");
            const resultado = await respuesta.json();
            console.log(resultado);

            select_categorias_registradas.innerHTML = "<option selected>Todos los Catalogos</option>";

            resultado.forEach(categoria => {
                const option_categoria = document.createElement("option");
                option_categoria.value = categoria.id_categoria;
                option_categoria.textContent = categoria.nombre;
                select_categorias_registradas.append(option_categoria);
            });

        } catch (error) {
            console.error(error);
        }
    }
    categoria_equipo_registrados();



    async function historial_inventario_equipo() {
        if (consulta_equipos_activa) {
            consulta_equipos_activa.abort();
        }

        const controlador = new AbortController();
        consulta_equipos_activa = controlador;

        try {
            const formulario = new FormData();

            formulario.append("codigo", input_codigo_equipo.value.trim());
            formulario.append("categoria", select_categorias_registradas.value);

            const respuesta = await fetch("/asignaciones/historial_inventario_equipos/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken
                },
                body: formulario,
                signal: controlador.signal
            });

            const resultado = await respuesta.json();

            if (resultado.estado === "fallo") {
                lista_historial = [];
                pagina_actual = 1;

                mostrar_historial_pagina();

                await Swal.fire({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon
                });

                return;
            }

            lista_historial = Array.isArray(resultado.historial)
                ? resultado.historial
                : [];

            pagina_actual = 1;
            mostrar_historial_pagina();

        } catch (error) {
            if (error.name !== "AbortError") {
                console.error("Error al consultar el historial:", error);

                await Swal.fire({
                    title: "Error",
                    text: "No fue posible consultar el historial del inventario.",
                    icon: "error"
                });
            }
        } finally {
            if (consulta_equipos_activa === controlador) {
                consulta_equipos_activa = null;
            }
        }
    }

    function mostrar_historial_pagina() {
        contenedor_historial.innerHTML = "";

        const inicio = (pagina_actual - 1) * filas_por_pagina;
        const fin = inicio + filas_por_pagina;

        const historial_pagina = lista_historial.slice(inicio, fin);

        if (historial_pagina.length === 0) {
            contenedor_historial.innerHTML = `
            <tr>
                <td colspan="9">No hay movimientos registrados.</td>
            </tr>
        `;
        } else {
            historial_pagina.forEach((registro, index) => {
                const fila = document.createElement("tr");

                fila.innerHTML = `
                <td>${index + 1}</td>
                <td>${escapar_html(registro.equipo)}</td>
                <td>${escapar_html(registro.tipo_movimiento)}</td>
                <td>${registro.cantidad_anterior}</td>
                <td>${registro.cantidad_movimiento}</td>
                <td>${registro.cantidad_nueva}</td>
                <td>${formatear_estado(registro.activo_anterior)}</td>
                <td>${formatear_estado(registro.activo_nuevo)}</td>
                <td>${registro.fecha_movimiento}</td>
            `;

                contenedor_historial.appendChild(fila);
            });
        }

        btn_retroceder.disabled = pagina_actual === 1;

        btn_avanzar.disabled = fin >= lista_historial.length;
    }

    function formatear_estado(estado) {
        if (estado === null || estado === undefined) {
            return "No aplica";
        }

        return estado ? "Activo" : "Inactivo";
    }

    function escapar_html(valor) {
        return String(valor ?? "").replace(/[&<>"']/g, caracter => ({
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;"
        })[caracter]);
    }

    input_codigo_equipo.addEventListener("input", historial_inventario_equipo);

    select_categorias_registradas.addEventListener("change", historial_inventario_equipo);

    btn_retroceder.addEventListener("click", () => {
        if (pagina_actual > 1) {
            pagina_actual--;
            mostrar_historial_pagina();
        }
    });

    btn_avanzar.addEventListener("click", () => {
        if (pagina_actual * filas_por_pagina < lista_historial.length) {
            pagina_actual++;
            mostrar_historial_pagina();
        }
    });

    historial_inventario_equipo();
});