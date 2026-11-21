document.addEventListener("DOMContentLoaded", () => {

    const contenedor_equipos_recibido = document.getElementById("contenedor_equipos_recibido");

    const select_categoria_equipos = document.getElementById("categoria_equipos");

    const dialogo_recibido = document.getElementById("dialogo_recibido");
    const btn_cerrar = document.getElementById("btn_cerrar");

    const input_id_recibido_equipo = document.getElementById("id_recibido_equipo");
    const input_equipo_entregado = document.getElementById("equipo_entregado");
    const input_categoria_equipo = document.getElementById("categoria_equipo");
    const input_codigo_equipo = document.getElementById("codigo_equipo");
    const input_cantidad_equipo = document.getElementById("cantidad_equipo");
    const input_cantidad_disponible = document.getElementById("cantidad_disponible");
    const input_fecha_entrega = document.getElementById("fecha_entrega");
    const textarea_observacion_entrega = document.getElementById("observacion_entrega");

    const btn_ret = document.querySelector(".botones_navegacion .btn_ret");
    const btn_av = document.querySelector(".botones_navegacion .btn_av");

    let categoria = "";

    async function categoria_equipos() {
        try {
            const respuesta = await fetch("/asignaciones/categoria_equipo_recibido/");
            const resultado = await respuesta.json();
            console.log(resultado);

            select_categoria_equipos.innerHTML = "<option value=''>Todas las Categorias</option>"

            if (resultado.estado == "fallo") {
                await Swal.fire({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon
                });
                return;
            }

            resultado.categorias.forEach(categoria => {
                const option_categoria = document.createElement("option");
                option_categoria.value = categoria.id_categoria;
                option_categoria.textContent = categoria.nombre;
                select_categoria_equipos.append(option_categoria);
            });
        } catch (error) {
            console.error(error);
        }
    }
    categoria_equipos();

    select_categoria_equipos.addEventListener("change", async () => {
        categoria = select_categoria_equipos.value;

        await equipos_recibido_registrados();
    });

    const filas_por_pagina = 10;
    let pagina_actual = 1;
    let equipos_recibidos = [];

    async function equipos_recibido_registrados() {
        try {
            const formulario = new FormData();
            formulario.append("categoria", categoria);

            const respuesta = await fetch("/asignaciones/visualizar_equipos_supervisor/", {
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
                equipos_recibidos = [];
                pagina_actual = 1;
                mostrar_equipos_recibidos();
                return;
            }

            equipos_recibidos = resultado.equipos || [];
            pagina_actual = 1;

            mostrar_equipos_recibidos();

        } catch (error) {
            console.error(error);
        }
    }

    function mostrar_equipos_recibidos() {
        contenedor_equipos_recibido.innerHTML = "";

        const inicio = (pagina_actual - 1) * filas_por_pagina;
        const fin = inicio + filas_por_pagina;

        const equipos_pagina = equipos_recibidos.slice(inicio, fin);

        const total_paginas = Math.ceil(
            equipos_recibidos.length / filas_por_pagina
        );

        if (equipos_pagina.length === 0) {
            contenedor_equipos_recibido.innerHTML = `
            <tr>
                <td colspan="7" class="texto_sin_registros">
                    No hay equipos recibidos registrados.
                </td>
            </tr>
        `;
        } else {
            equipos_pagina.forEach((recibido, index) => {
                contenedor_equipos_recibido.innerHTML += `
                <tr data-id_recibido="${recibido.id_entrega}">
                    <td>${inicio + index + 1}</td>
                    <td>${recibido.equipo}</td>
                    <td>${recibido.codigo}</td>
                    <td>${recibido.cantidad_entregada}</td>
                    <td>${recibido.cantidad_disponible}</td>
                    <td>${recibido.fecha_entrega}</td>
                    <td>${recibido.estado}</td>
                </tr>
            `;
            });
        }

        btn_ret.disabled = pagina_actual <= 1;
        btn_av.disabled = pagina_actual >= total_paginas;
    }

    btn_ret.addEventListener("click", () => {
        if (pagina_actual > 1) {
            pagina_actual--;
            mostrar_equipos_recibidos();
        }
    });

    btn_av.addEventListener("click", () => {
        const total_paginas = Math.ceil(
            equipos_recibidos.length / filas_por_pagina
        );

        if (pagina_actual < total_paginas) {
            pagina_actual++;
            mostrar_equipos_recibidos();
        }
    });

    equipos_recibido_registrados();

    contenedor_equipos_recibido.addEventListener("click", async (e) => {
        const fila = e.target.closest("tr")
        if (!fila) return;

        try {
            const formulario = new FormData();
            formulario.append("id_recibido", fila.dataset.id_recibido);

            const respuesta = await fetch("/asignaciones/datos_equipo_recibido/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
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

            dialogo_recibido.showModal();

            input_id_recibido_equipo.value = resultado.equipo.id_entrega;
            input_equipo_entregado.value = resultado.equipo.nombre_equipo;
            input_categoria_equipo.value = resultado.equipo.categoria;
            input_codigo_equipo.value = resultado.equipo.codigo_equipo;
            input_cantidad_equipo.value = resultado.equipo.cantidad_entregada;
            input_cantidad_disponible.value = resultado.equipo.cantidad_disponible_entrega;
            input_fecha_entrega.value = resultado.equipo.fecha_entrega;
            textarea_observacion_entrega.value = resultado.equipo.observacion_entrega;
        } catch (error) {
            console.error(error);
        }
    });

    btn_cerrar.addEventListener("click", () => {
        dialogo_recibido.close();
    });

});