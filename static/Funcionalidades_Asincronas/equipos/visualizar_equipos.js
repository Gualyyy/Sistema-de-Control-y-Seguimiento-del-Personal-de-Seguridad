document.addEventListener("DOMContentLoaded", () => {

    const contenedor_equipos = document.getElementById("contenedor_equipos");
    const input_codigo_equipo = document.getElementById("codigo_equipo");
    const select_categorias_registradas = document.getElementById("categorias_registradas");
    const dialogo_equipo = document.getElementById("dialogo_equipo");
    const btn_cerrar = document.getElementById("btn_cerrar");

    const input_id_equipo = document.getElementById("id_equipo");
    const nombre_equipo = document.getElementById("nombre_equipo");
    const codigo_equipo = document.getElementById("codigo_equipo_visualizar");
    const observacion_equipo = document.getElementById("observacion_equipo");
    const cantidad_disponible_equipo = document.getElementById("cantidad_disponible_equipo");
    const categoria_equipo = document.getElementById("categoria_equipo");
    const fecha_registro = document.getElementById("fecha_registro");

    const boton_retroceder = document.querySelector(".btn_retroceder");
    const boton_avanzar = document.querySelector(".btn_avanzar");

    const btn_lista_equipos_pdf = document.getElementById("lista_equipos_pdf");
    const btn_datos_equipo_pdf = document.getElementById("datos_equipo_pdf");

    const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;

    const FILAS_POR_PAGINA = 10;

    let lista_equipos_registrados = [];
    let pagina_actual = 1;

    async function categoria_equipo_registrados() {
        try {
            const respuesta = await fetch("/asignaciones/categoria_registrados/");
            const resultado = await respuesta.json();
            console.log(resultado);

            select_categorias_registradas.innerHTML = "<option selected>Seleccione la categoria</option>";

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

    function mostrar_equipos_pagina() {
        const total_paginas = Math.max(1, Math.ceil(lista_equipos_registrados.length / FILAS_POR_PAGINA));

        if (pagina_actual > total_paginas) {
            pagina_actual = total_paginas;
        }

        const inicio = (pagina_actual - 1) * FILAS_POR_PAGINA;
        const equipos_pagina = lista_equipos_registrados.slice(
            inicio,
            inicio + FILAS_POR_PAGINA
        );

        contenedor_equipos.innerHTML = "";

        equipos_pagina.forEach((equipo, index) => {
            contenedor_equipos.innerHTML += `
            <tr data-codigo="${equipo.codigo}">
                <td>${inicio + index + 1}</td>
                <td>${equipo.nombre}</td>
                <td>${equipo.codigo}</td>
                <td>${equipo.cantidad_disponible}</td>
                <td>${equipo.fecha_registro}</td>
            </tr>
        `;
        });

        boton_retroceder.disabled = pagina_actual === 1;
        boton_avanzar.disabled = pagina_actual === total_paginas;
    }

    async function equipos_registrados() {
        try {
            const formulario = new FormData();
            formulario.append("codigo", input_codigo_equipo.value);
            formulario.append("categoria", select_categorias_registradas.value);

            const respuesta = await fetch("/asignaciones/visualizacion_equipos/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken
                },
                body: formulario
            });

            const resultado = await respuesta.json();

            if (!respuesta.ok || !Array.isArray(resultado)) {
                lista_equipos_registrados = [];
                pagina_actual = 1;
                mostrar_equipos_pagina();

                if (resultado.estado === "fallo") {
                    await Swal.fire({
                        title: resultado.title,
                        text: resultado.descripcion,
                        icon: resultado.icon
                    });
                }

                return;
            }

            lista_equipos_registrados = resultado;
            pagina_actual = 1;

            mostrar_equipos_pagina();
        } catch (error) {
            console.error(error);
        }
    }

    boton_retroceder.addEventListener("click", () => {
        if (pagina_actual > 1) {
            pagina_actual--;
            mostrar_equipos_pagina();
        }
    });

    boton_avanzar.addEventListener("click", () => {
        const total_paginas = Math.ceil(lista_equipos_registrados.length / FILAS_POR_PAGINA);

        if (pagina_actual < total_paginas) {
            pagina_actual++;
            mostrar_equipos_pagina();
        }
    });

    input_codigo_equipo.addEventListener("input", equipos_registrados);
    select_categorias_registradas.addEventListener("change", equipos_registrados);

    equipos_registrados();

    contenedor_equipos.addEventListener("click", async (e) => {
        const fila = e.target.closest("tr");
        if (!fila) return;

        const equipo = fila.dataset.codigo;
        try {
            const formulario = new FormData();
            formulario.append("codigo_equipo", equipo);

            const respuesta = await fetch("/asignaciones/buscar_equipos/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            if (resultado.estado == "fallo") {
                await Swal.fire({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon
                });
                return;
            }

            dialogo_equipo.showModal();

            input_id_equipo.value = resultado.equipo.id_equipo;
            nombre_equipo.value = resultado.equipo.nombre;
            codigo_equipo.value = resultado.equipo.codigo;
            observacion_equipo.value = resultado.equipo.observacion;
            cantidad_disponible_equipo.value = resultado.equipo.cantidad_disponible;
            categoria_equipo.value = resultado.equipo.categoria;
            fecha_registro.value = resultado.equipo.fecha_registro;
        } catch (error) {
            console.error(error);
        }
    });

    btn_cerrar.addEventListener("click", () => {
        dialogo_equipo.close();
    });

    btn_lista_equipos_pdf.addEventListener("click", async () => {
        try {
            const formulario = new FormData();
            formulario.append("csrfmiddlewaretoken", csrfToken);
            formulario.append("categoria", select_categorias_registradas.value);

            const respuesta = await fetch("/asignaciones/lista_equipos_pdf/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken
                },
                body: formulario
            });
            const tipo = respuesta.headers.get("content-type") || "";

            if (tipo.includes("application/json")) {
                const resultado = await respuesta.json();

                await Swal.fire({
                    title: resultado.title || "Advertencia",
                    text: resultado.descripcion || "No hay equipos para generar el reporte.",
                    icon: resultado.icon || "warning"
                });
                return;
            }

            if (!respuesta.ok || !tipo.includes("application/pdf")) {
                await Swal.fire({
                    title: "Error",
                    text: "No fue posible generar el reporte PDF.",
                    icon: "error"
                });
                return;
            }

            const archivo = await respuesta.blob();
            const url = URL.createObjectURL(archivo);

            window.open(url, "_blank");

            setTimeout(() => {
                URL.revokeObjectURL(url);
            }, 60000);

        } catch (error) {
            console.error(error);
        }
    });

    btn_datos_equipo_pdf.addEventListener("click", async () => {
        try {
            const formulario = new FormData();
            formulario.append("csrfmiddlewaretoken", csrfToken);
            formulario.append("id_equipo", input_id_equipo.value);

            const respuesta = await fetch("/asignaciones/datos_equipos_pdf/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken
                },
                body: formulario
            });

            const tipo = respuesta.headers.get("content-type") || "";
            if (tipo.includes("application/json")) {
                const resultado = await respuesta.json();

                await Swal.fire({
                    title: resultado.title || "Advertencia",
                    text: resultado.descripcion || "No se pudo generar el reporte.",
                    icon: resultado.icon || "warning"
                });

                return;
            }

            if (!respuesta.ok || !tipo.includes("application/pdf")) {
                await Swal.fire({
                    title: "Error",
                    text: "No fue posible generar el reporte del equipo.",
                    icon: "error"
                });
                return;
            }

            const archivo = await respuesta.blob();
            const url = URL.createObjectURL(archivo);

            window.open(url, "_blank");

            setTimeout(() => {
                URL.revokeObjectURL(url);
            }, 60000);

        } catch (error) {
            console.error(error);
        }
    });
});