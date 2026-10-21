document.addEventListener("DOMContentLoaded", () => {

    const contenedor_entregas_equipos = document.getElementById("contenedor_entregas_equipos");

    const select_supervisores_encargados = document.getElementById("supervisores_encargados");
    const select_categoria_equipos = document.getElementById("categoria_equipos");

    const dialogo_entrega = document.getElementById("dialogo_entrega");
    const btn_cerrar = document.getElementById("btn_cerrar");

    const input_id_entrega_equipo = document.getElementById("id_entrega_equipo");
    const input_supervisor_encargado = document.getElementById("supervisor_encargado");
    const input_cedula_identidad = document.getElementById("cedula_identidad");
    const input_turno_laboral = document.getElementById("turno_laboral");
    const input_equipo_entregado = document.getElementById("equipo_entregado");
    const input_categoria_equipo = document.getElementById("categoria_equipo");
    const input_codigo_equipo = document.getElementById("codigo_equipo");
    const input_cantidad_equipo = document.getElementById("cantidad_equipo");
    const input_fecha_entrega = document.getElementById("fecha_entrega");
    const textarea_observacion_entrega = document.getElementById("observacion_entrega");

    const btn_lista_entrega_pdf = document.getElementById("lista_entrega_pdf");
    const btn_datos_entrega_pdf = document.getElementById("datos_entrega_pdf");

    const btn_retroceder = document.querySelector(".btn_retroceder");
    const btn_avanzar = document.querySelector(".btn_avanzar");

    let entregas_equipos = [];
    let pagina_actual = 1;
    const filas_por_pagina = 10;

    let supervisor = "", categoria = "";

    async function supervisores_registrados() {
        try {
            const respuesta = await fetch("/supervisores_registrados/");
            const resultado = await respuesta.json();
            console.log(resultado);

            select_supervisores_encargados.innerHTML = "<option value=''>Selecciona un Supervisor</option>"

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

        await entregas_equipos_registradas();
    });

    async function categoria_equipos() {
        try {
            const respuesta = await fetch("/asignaciones/categoria_registrados/");
            const resultado = await respuesta.json();
            console.log(resultado);

            select_categoria_equipos.innerHTML = "<option value=''>Selecciona la Categoria</option>"

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

        await entregas_equipos_registradas();
    });

    async function entregas_equipos_registradas() {
        try {
            const formulario = new FormData();
            formulario.append("categoria", categoria);
            formulario.append("supervisor", supervisor);

            const respuesta = await fetch("/asignaciones/entregas_equipos_registradas/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });

            const resultado = await respuesta.json();

            if (resultado.estado !== "exito") {
                entregas_equipos = [];
                pagina_actual = 1;
                mostrar_entregas_equipos();
                return;
            }

            entregas_equipos = resultado.entregas;
            pagina_actual = 1;

            mostrar_entregas_equipos();

        } catch (error) {
            console.error(error);
        }
    }

    function mostrar_entregas_equipos() {
        contenedor_entregas_equipos.innerHTML = "";

        const inicio = (pagina_actual - 1) * filas_por_pagina;
        const fin = inicio + filas_por_pagina;
        const entregas_pagina = entregas_equipos.slice(inicio, fin);

        entregas_pagina.forEach((entrega, index) => {
            contenedor_entregas_equipos.innerHTML += `
            <tr data-id_entrega="${entrega.id_entrega}">
                <td>${inicio + index + 1}</td>
                <td>${entrega.supervisor_encargado}</td>
                <td>${entrega.turno}</td>
                <td>${entrega.equipo}</td>
                <td>${entrega.cantidad_entregada}</td>
                <td>${entrega.fecha_entrega}</td>
            </tr>
        `;
        });

        const total_paginas = Math.ceil(entregas_equipos.length / filas_por_pagina);

        btn_retroceder.disabled = pagina_actual <= 1;
        btn_avanzar.disabled = pagina_actual >= total_paginas;
    }

    btn_retroceder.addEventListener("click", () => {
        if (pagina_actual > 1) {
            pagina_actual--;
            mostrar_entregas_equipos();
        }
    });

    btn_avanzar.addEventListener("click", () => {
        const total_paginas = Math.ceil(entregas_equipos.length / filas_por_pagina);

        if (pagina_actual < total_paginas) {
            pagina_actual++;
            mostrar_entregas_equipos();
        }
    });

    entregas_equipos_registradas();

    contenedor_entregas_equipos.addEventListener("click", async (e) => {
        const fila = e.target.closest("tr")
        if (!fila) return;

        try {
            const formulario = new FormData();
            formulario.append("id_entrega", fila.dataset.id_entrega);

            const respuesta = await fetch("/asignaciones/busca_entrega_equipos/", {
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

            dialogo_entrega.showModal();

            input_id_entrega_equipo.value = resultado.entrega.id_entrega;
            input_supervisor_encargado.value = resultado.entrega.supervisor_encargado;
            input_cedula_identidad.value = resultado.entrega.cedula_supervisor;
            input_turno_laboral.value = resultado.entrega.turno;
            input_equipo_entregado.value = resultado.entrega.equipo;
            input_categoria_equipo.value = resultado.entrega.categoria;
            input_codigo_equipo.value = resultado.entrega.codigo_equipo;
            input_cantidad_equipo.value = `Cantidad entregada: ${resultado.entrega.cantidad_entregada}`;
            input_fecha_entrega.value = resultado.entrega.fecha_entrega;
            textarea_observacion_entrega.value = resultado.entrega.observacion;
        } catch (error) {
            console.error(error);
        }
    });

    btn_cerrar.addEventListener("click", () => {
        dialogo_entrega.close();
    });

    btn_lista_entrega_pdf.addEventListener("click", async () => {
        const formulario = new FormData();
        formulario.append("categoria", select_categoria_equipos.value);
        formulario.append("supervisor", select_supervisores_encargados.value);
        formulario.append("csrfmiddlewaretoken", document.querySelector("[name=csrfmiddlewaretoken]").value);

        try {
            const respuesta = await fetch("/asignaciones/lista_entrega_equipos_pdf/", {
                method: "POST",
                body: formulario
            });

            const contentType = respuesta.headers.get("content-type") || "";

            if (!respuesta.ok || !contentType.includes("application/pdf")) {
                const resultado = await respuesta.json();
                Swal.fire({
                    title: resultado.title || "Error",
                    text: resultado.descripcion || "No se pudo generar el reporte.",
                    icon: resultado.icon || "error"
                });
                return;
            }

            const blob = await respuesta.blob();
            const url = URL.createObjectURL(blob);

            window.open(url, "_blank");

            setTimeout(() => URL.revokeObjectURL(url), 60000);

        } catch (error) {
            console.error(error);
        }
    });

    btn_datos_entrega_pdf.addEventListener("click", async () => {
        const formulario = new FormData();
        formulario.append("id_entrega", input_id_entrega_equipo.value);
        formulario.append("csrfmiddlewaretoken", document.querySelector("[name=csrfmiddlewaretoken]").value);

        try {
            const respuesta = await fetch("/asignaciones/datos_entrega_equipo_pdf/", {
                method: "POST",
                body: formulario
            });
            const contentType = respuesta.headers.get("content-type") || "";

            if (!respuesta.ok || !contentType.includes("application/pdf")) {
                const resultado = await respuesta.json();
                Swal.fire({
                    title: resultado.title || "Error",
                    text: resultado.descripcion || "No se pudo generar el reporte PDF.",
                    icon: resultado.icon || "error"
                });
                return;
            }

            const archivo = await respuesta.blob();
            const url = URL.createObjectURL(archivo);

            window.open(url, "_blank");

            setTimeout(() => URL.revokeObjectURL(url), 60000);

        } catch (error) {
            console.error(error);
        }
    });
});