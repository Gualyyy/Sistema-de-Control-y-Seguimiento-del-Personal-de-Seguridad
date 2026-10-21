document.addEventListener("DOMContentLoaded", () => {

    const select_fechas = document.getElementById("fechas_registradas");
    const btn_inicios_sesiones_pdf = document.getElementById("inicios_sesiones_pdf");

    const btn_avanzar = document.querySelector(".btn_avanzar");
    const btn_retroceder = document.querySelector(".btn_retroceder");

    const contenedor_inicios_sesiones = document.getElementById("contenedor_inicios_sesiones");

    const FILAS_POR_PAGINA = 10;

    let fecha = "";
    let registros_inicios_sesiones = [];
    let pagina_actual = 1;

    async function fechas_registradas() {
        try {
            const respuesta = await fetch("/fechas_inicios_sesiones/");
            const resultado = await respuesta.json();
            console.log(resultado);

            select_fechas.innerHTML = "<option value='' selected>Seleccione la fecha</option>";

            resultado.fechas.forEach(fecha => {
                const option = document.createElement("option");
                option.value = fecha;
                option.textContent = fecha;
                select_fechas.append(option);
            });
        } catch (error) {
            console.error(error);
        }
    }
    fechas_registradas();

    select_fechas.addEventListener("change", async () => {
        fecha = select_fechas.value;

        await inicios_sesiones_registradas();
    });

    function mostrar_inicios_sesiones() {
        contenedor_inicios_sesiones.innerHTML = "";

        const inicio = (pagina_actual - 1) * FILAS_POR_PAGINA;

        const fin = inicio + FILAS_POR_PAGINA;

        const registros = registros_inicios_sesiones.slice(inicio, fin);

        registros.forEach((registro, indice) => {
            const fila = document.createElement("tr");

            fila.innerHTML = `
                <td>${inicio + indice + 1}</td>
                <td>${registro.usuario}</td>
                <td>${registro.cedula_identidad}</td>
                <td>${registro.fecha_inicio}</td>
                <td>${registro.fecha_fin}</td>
                <td>${registro.activa ? "Sí" : "No"}</td>
                <td>${registro.navegador}</td>
                <td>${registro.direccion_ip}</td>
            `;

            contenedor_inicios_sesiones.appendChild(fila);
        });

        const total_paginas = Math.ceil(registros_inicios_sesiones.length / FILAS_POR_PAGINA);

        btn_retroceder.disabled = pagina_actual <= 1;
        btn_avanzar.disabled = pagina_actual >= total_paginas;
    }

    btn_avanzar.addEventListener("click", () => {
        const total_paginas = Math.ceil(registros_inicios_sesiones.length / FILAS_POR_PAGINA);

        if (pagina_actual < total_paginas) {
            pagina_actual++;
            mostrar_inicios_sesiones();
        }
    });

    btn_retroceder.addEventListener("click", () => {
        if (pagina_actual > 1) {
            pagina_actual--;
            mostrar_inicios_sesiones();
        }
    });

    async function inicios_sesiones_registradas() {
        try {
            const formulario = new FormData();
            formulario.append("fecha", fecha);

            const respuesta = await fetch("/inicios_sesiones_registradas/", {
                method: "POST",
                headers: {
                    "X-CSRFToken":
                        document.querySelector(
                            "[name=csrfmiddlewaretoken]"
                        ).value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            registros_inicios_sesiones = resultado;
            pagina_actual = 1;

            mostrar_inicios_sesiones();
        } catch (error) {
            console.error(error);
        }
    }
    inicios_sesiones_registradas();

    btn_inicios_sesiones_pdf.addEventListener("click", async () => {
        try {
            const csrf = document.querySelector('[name=csrfmiddlewaretoken]').value;
            const fechas = document.querySelector("#fechas_registradas").value;

            const formulario = new FormData();
            formulario.append("csrfmiddlewaretoken", csrf);
            formulario.append("fechas", fechas);

            const respuesta = await fetch("/lista_inicios_sesiones_pdf/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrf
                },
                body: formulario
            });
            const tipo = respuesta.headers.get("content-type") || "";

            if (tipo.includes("application/json")) {
                const resultado = await respuesta.json();

                Swal.fire({
                    icon: resultado.icon || "warning",
                    title: resultado.title || "Sin registros",
                    text: resultado.descripcion
                });

                return;
            }

            if (!respuesta.ok) {
                throw new Error("No se pudo generar el reporte.");
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