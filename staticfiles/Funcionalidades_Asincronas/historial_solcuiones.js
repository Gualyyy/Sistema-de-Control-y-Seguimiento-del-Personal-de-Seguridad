document.addEventListener("DOMContentLoaded", () => {

    const contenedor_soluciones = document.getElementById("contenedor_soluciones");

    const btn_retroceder = document.querySelector(".btn_retroceder");
    const btn_avanzar = document.querySelector(".btn_avanzar");

    let historial_soluciones = [];
    let pagina_actual = 1;
    const filas_por_pagina = 10;

    async function cargarHistorialSoluciones() {
        try {
            const respuesta = await fetch("/incidencias/historial_soluciones/");
            const resultado = await respuesta.json();
            console.log(resultado);

            if (resultado.estado !== "exito") {
                return;
            }

            historial_soluciones = resultado.historial;
            pagina_actual = 1;

            mostrarHistorialSoluciones();
        } catch (error) {
            console.error(error);
        }
    }
    cargarHistorialSoluciones();

    function mostrarHistorialSoluciones() {
        contenedor_soluciones.innerHTML = "";

        const inicio = (pagina_actual - 1) * filas_por_pagina;
        const final = inicio + filas_por_pagina;

        const historial_pagina = historial_soluciones.slice(
            inicio,
            final
        );

        if (historial_pagina.length === 0) {
            contenedor_soluciones.innerHTML = `
            <tr>
                <td colspan="7">
                    No hay acciones registradas.
                </td>
            </tr>
        `;

            actualizarBotonesHistorial();
            return;
        }

        historial_pagina.forEach((item, index) => {
            const fila = document.createElement("tr");

            fila.dataset.id_solucion = item.id_solucion;
            fila.dataset.id_incidencia = item.id_incidencia;

            fila.innerHTML = `
                <td>${inicio + index + 1}</td>
                <td>${item.usuario}</td>
                <td>${item.tipo}</td>
                <td>${item.titulo}</td>
                <td>${item.estado}</td>
                <td>${item.descripcion}</td>
                <td>${item.fecha_hora}</td>
            `;

            contenedor_soluciones.appendChild(fila);
        });

        actualizarBotonesHistorial();
    }

    function actualizarBotonesHistorial() {
        const total_paginas = Math.ceil(historial_soluciones.length / filas_por_pagina);

        btn_retroceder.disabled = pagina_actual <= 1;
        btn_avanzar.disabled = pagina_actual >= total_paginas;
    }

    btn_retroceder.addEventListener("click", () => {
        if (pagina_actual > 1) {
            pagina_actual--;

            mostrarHistorialSoluciones();
        }
    });

    btn_avanzar.addEventListener("click", () => {
        const total_paginas = Math.ceil(historial_soluciones.length / filas_por_pagina);

        if (pagina_actual < total_paginas) {
            pagina_actual++;

            mostrarHistorialSoluciones();
        }
    });
});