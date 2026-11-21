document.addEventListener("DOMContentLoaded", () => {

    const contenedor_historial_entregas = document.getElementById("contenedor_historial_entregas");

    const select_supervisores_encargados = document.getElementById("supervisores_encargados");
    const select_categoria_equipos = document.getElementById("categoria_equipos");

    const dialogo_historial = document.getElementById("dialogo_historial");
    const btn_cerrar = document.getElementById("btn_cerrar");

    const btn_retroceder = document.querySelector(".btn_ret");
    const btn_avanzar = document.querySelector(".btn_av");

    const equipo_entregado = document.getElementById("equipo_entregado");
    const categoria_equipo = document.getElementById("categoria_equipo");
    const codigo_equipo = document.getElementById("codigo_equipo");

    const cantidad_entrega_anterior = document.getElementById("cantidad_entrega_anterior");
    const cantidad_entrega_nueva = document.getElementById("cantidad_entrega_nueva");

    const cantidad_disponibles_anterior = document.getElementById("cantidad_disponibles_anterior");
    const cantidad_disponibles_nuevo = document.getElementById("cantidad_disponibles_nuevo");

    const estado_anterior = document.getElementById("estado_anterior");
    const estado_nuevo = document.getElementById("estado_nuevo");

    const motivo_incidencia_anterior = document.getElementById("motivo_incidencia_anterior");
    const motivo_incidencia_nueva = document.getElementById("motivo_incidencia_nueva");

    const observacion_anterior = document.getElementById("observacion_anterior");
    const observacion_nueva = document.getElementById("observacion_nueva");

    const fecha_actualizacion = document.getElementById("fecha_actualizacion");
    const motivo_actualizacion = document.getElementById("motivo_actualizacion");

    let entregas_equipos = [];
    let pagina_actual = 1;
    const filas_por_pagina = 10;

    let supervisor = "", categoria = "";

    async function supervisores_registrados() {
        try {
            const respuesta = await fetch("/asignaciones/supervisores_registrados/");
            const resultado = await respuesta.json();
            console.log(resultado);

            select_supervisores_encargados.innerHTML = "<option value=''>Selecciona un Supervisor</option>"

            if (resultado.estado == "fallo") {
                await Swal.fire({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon
                });
                return;
            }

            resultado.supervisores.forEach(supervisor => {
                const option_supervisor = document.createElement("option");
                option_supervisor.value = supervisor.id_supervisor;
                option_supervisor.textContent = supervisor.nombres + " " + supervisor.apellidos + " | " + supervisor.turno;
                select_supervisores_encargados.append(option_supervisor);
            });
        } catch (error) {
            console.error(error);
        }
    }
    supervisores_registrados();

    select_supervisores_encargados.addEventListener("change", async () => {
        supervisor = select_supervisores_encargados.value;

        await historial_entregas_equipos();
    });

    async function categoria_equipos() {
        try {
            const respuesta = await fetch("/asignaciones/categoria_registrados/");
            const resultado = await respuesta.json();

            select_categoria_equipos.innerHTML = "<option value=''>Todas las categorías</option>";

            resultado.forEach(categoria => {
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

        await historial_entregas_equipos();
    });

    // Si tienes un selector de supervisores:
    select_supervisores_encargados.addEventListener("change", async () => {
        supervisor = select_supervisores_encargados.value;

        await historial_entregas_equipos();
    });

    async function historial_entregas_equipos() {
        try {
            const formulario = new FormData();
            formulario.append("categoria", categoria);
            formulario.append("supervisor", supervisor);

            const respuesta = await fetch("/asignaciones/historial_entregas_equipos/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            if (resultado.estado !== "exito") {
                entregas_equipos = [];
                pagina_actual = 1;
                mostrar_entregas_equipos();

                Swal.fire({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon
                });
                return;
            }

            entregas_equipos = resultado.historial;
            pagina_actual = 1;

            mostrar_entregas_equipos();

        } catch (error) {
            console.error(error);
        }
    }

    function mostrar_entregas_equipos() {
        contenedor_historial_entregas.innerHTML = "";

        const inicio = (pagina_actual - 1) * filas_por_pagina;
        const fin = inicio + filas_por_pagina;

        const entregas_pagina = entregas_equipos.slice(inicio, fin);

        if (entregas_pagina.length === 0) {
            contenedor_historial_entregas.innerHTML = `
                <tr>
                    <td colspan="4">
                        No hay entregas registradas.
                    </td>
                </tr>
            `;

            actualizar_botones_entregas();
            return;
        }

        entregas_pagina.forEach((entrega, index) => {
            const fila = document.createElement("tr");

            fila.dataset.id_historial = entrega.id_historial;

            fila.innerHTML = `
                <td>${index + 1}</td>
                <td>${entrega.nombres + " " + entrega.apellidos}</td>
                <td>${entrega.turno}</td>
                <td>${entrega.equipo}</td>
            `;

            contenedor_historial_entregas.appendChild(fila);
        });

        actualizar_botones_entregas();
    }

    function actualizar_botones_entregas() {
        const total_paginas = Math.ceil(
            entregas_equipos.length / filas_por_pagina
        );

        btn_retroceder.disabled = pagina_actual <= 1;
        btn_avanzar.disabled = pagina_actual >= total_paginas || total_paginas === 0;
    }

    btn_retroceder.addEventListener("click", () => {
        if (pagina_actual > 1) {
            pagina_actual--;
            mostrar_entregas_equipos();
        }
    });

    btn_avanzar.addEventListener("click", () => {
        const total_paginas = Math.ceil(
            entregas_equipos.length / filas_por_pagina
        );

        if (pagina_actual < total_paginas) {
            pagina_actual++;
            mostrar_entregas_equipos();
        }
    });
    historial_entregas_equipos();

    btn_cerrar.addEventListener("click", () => {
        dialogo_historial.close();
    });

    contenedor_historial_entregas.addEventListener("click", async (e) => {
        const fila = e.target.closest("tr")
        if (!fila) return;

        try {
            const formulario = new FormData();
            formulario.append("id_historial", fila.dataset.id_historial);

            const respuesta = await fetch("/asignaciones/detalle_historial_entrega/", {
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

            dialogo_historial.showModal();

            equipo_entregado.value = resultado.historial.equipo.nombre;
            codigo_equipo.value = resultado.historial.equipo.codigo;
            categoria_equipo.value = resultado.historial.equipo.categoria;

            cantidad_entrega_anterior.value = resultado.historial.cantidad_entregada_anterior;
            cantidad_entrega_nueva.value = resultado.historial.cantidad_entregada_nueva;

            cantidad_disponibles_anterior.value = resultado.historial.cantidad_disponible_anterior;
            cantidad_disponibles_nuevo.value = resultado.historial.cantidad_disponible_nueva;

            estado_anterior.value = resultado.historial.estado_anterior;
            estado_nuevo.value = resultado.historial.estado_nuevo;

            motivo_incidencia_anterior.value = resultado.historial.motivo_incidencia_anterior;
            motivo_incidencia_nueva.value = resultado.historial.motivo_incidencia_nuevo;

            observacion_anterior.value = resultado.historial.observacion_anterior;
            observacion_nueva.value = resultado.historial.observacion_nueva;

            motivo_actualizacion.value = resultado.historial.motivo_actualizacion;

            fecha_actualizacion.value = resultado.historial.fecha_actualizacion;

        } catch (error) {
            console.error(error);
        }
    });

});