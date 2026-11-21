document.addEventListener("DOMContentLoaded", () => {

    const select_categoria = document.getElementById("categoria_equipos");
    const contenedor_movimiento = document.getElementById("contenedor_movimiento");
    const btn_ret = document.querySelector(".botones_navegacion .btn_ret");
    const btn_av = document.querySelector(".botones_navegacion .btn_av");

    const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;

    let movimientos_recibidos = [];
    let pagina_actual = 1;
    const filas_por_pagina = 10;

    let categoria = "";

    async function categorias_equipos() {
        try {
            const respuesta = await fetch("/asignaciones/categoria_equipo_recibido/");
            const resultado = await respuesta.json();
            console.log(resultado);

            select_categoria.innerHTML = "<option value='' selected>Todos las Categorias</option>";

            if (resultado.estado == "fallo") {
                Swal.fire({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon
                });
                return;
            }

            resultado.categorias.forEach(categoria => {
                const option = document.createElement("option");
                option.value = categoria.id_categoria;
                option.textContent = categoria.nombre;
                select_categoria.append(option);
            });
        } catch (error) {
            console.error(error);
        }
    }
    categorias_equipos();

    select_categoria.addEventListener("change", async () => {
        categoria = select_categoria.value;

        movimiento_equipos();
    });

    async function movimiento_equipos() {
        try {
            const formulario = new FormData();
            formulario.append("categoria", categoria);

            const respuesta = await fetch("/asignaciones/movimiento_equipos/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            if (resultado.estado === "fallo") {
                await Swal.fire({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon
                });
                return;
            }

            movimientos_recibidos = resultado.movimientos;
            pagina_actual = 1;

            mostrarMovimientos();
        } catch (error) {
            console.error(error);
        }
    }
    movimiento_equipos();

    function mostrarMovimientos() {
        contenedor_movimiento.innerHTML = "";

        const inicio = (pagina_actual - 1) * filas_por_pagina;
        const final = inicio + filas_por_pagina;

        const movimientos_pagina = movimientos_recibidos.slice(inicio, final);

        if (movimientos_pagina.length === 0) {
            contenedor_movimiento.innerHTML = `
                <tr>
                    <td colspan="9" class="texto_sin_registros">
                        No hay movimientos registrados.
                    </td>
                </tr>
            `;
            actualizarBotones();
            return;
        }

        movimientos_pagina.forEach((movimiento, index) => {
            const fila = document.createElement("tr");
            fila.dataset.id_movimiento = movimiento.id_movimiento;
            fila.dataset.id_asignacion = movimiento.id_asignacion;

            fila.innerHTML = `
                <td>${inicio + index + 1}</td>
                <td>${movimiento.equipo}</td>
                <td>${movimiento.codigo}</td>
                <td>${movimiento.nombres} ${movimiento.apellidos}</td>
                <td>${movimiento.cedula}</td>
                <td>${movimiento.tipo_display}</td>
                <td>${movimiento.cantidad}</td>
                <td>${movimiento.estado_display}</td>
                <td>${movimiento.fecha} ${movimiento.hora}</td>
            `;

            contenedor_movimiento.appendChild(fila);
        });
        actualizarBotones();
    }

    function actualizarBotones() {
        const total_paginas = Math.ceil(
            movimientos_recibidos.length / filas_por_pagina
        );

        btn_ret.disabled = pagina_actual === 1;

        btn_av.disabled = pagina_actual >= total_paginas;
    }

    btn_ret.addEventListener("click", () => {

        if (pagina_actual > 1) {

            pagina_actual--;

            mostrarMovimientos();
        }
    });

    btn_av.addEventListener("click", () => {

        const total_paginas = Math.ceil(
            movimientos_recibidos.length / filas_por_pagina
        );

        if (pagina_actual < total_paginas) {

            pagina_actual++;

            mostrarMovimientos();
        }
    });
});