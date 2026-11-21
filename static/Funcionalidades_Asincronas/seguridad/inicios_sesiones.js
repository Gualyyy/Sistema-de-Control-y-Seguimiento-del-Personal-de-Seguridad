document.addEventListener("DOMContentLoaded", () => {

    const select_fechas = document.getElementById("fechas_registradas");

    const btn_ret = document.querySelector(".botones_navegacion .btn_ret");
    const btn_av = document.querySelector(".botones_navegacion .btn_av");

    const contenedor_inicios_sesiones = document.getElementById("contenedor_inicios_sesiones");
    const total_sesiones = document.getElementById("total_sesiones");
    const sesiones_activas = document.getElementById("sesiones_activas");
    const usuarios_con_sesion = document.getElementById("usuarios_con_sesion");
    const canvas_grafica_sesiones = document.getElementById("grafica_sesiones");
    const contenedor_grafica_sesiones = document.getElementById(
        "contenedor_grafica_sesiones"
    );
    const mensaje_grafica_sesiones = document.getElementById(
        "mensaje_grafica_sesiones"
    );
    const estado_sesiones = document.getElementById("estado_sesiones");

    const FILAS_POR_PAGINA = 10;

    let fecha = "";
    let registros_inicios_sesiones = [];
    let pagina_actual = 1;
    let grafica_sesiones = null;

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

    function actualizarBotonesIniciosSesiones() {
        const total_paginas = Math.ceil(
            registros_inicios_sesiones.length / FILAS_POR_PAGINA
        );

        btn_ret.disabled = pagina_actual <= 1;
        btn_av.disabled = pagina_actual >= total_paginas;
    }

    function actualizarEstadisticasSesiones() {
        total_sesiones.textContent = registros_inicios_sesiones.length;
        sesiones_activas.textContent = registros_inicios_sesiones.filter(
            registro => registro.activa
        ).length;
        usuarios_con_sesion.textContent = new Set(
            registros_inicios_sesiones
                .map(registro => registro.cedula_identidad)
                .filter(Boolean)
        ).size;

        if (typeof Chart === "undefined") {
            contenedor_grafica_sesiones.hidden = true;
            mensaje_grafica_sesiones.textContent =
                "No se pudo cargar la gráfica de estadísticas.";
            mensaje_grafica_sesiones.hidden = false;
            return;
        }

        const sesiones_por_fecha = new Map();

        registros_inicios_sesiones.forEach(registro => {
            const fecha_inicio = (registro.fecha_inicio || "").split(" ")[0];
            const partes = fecha_inicio.split("/");
            if (partes.length !== 3) return;

            const [dia, mes, anio] = partes;
            if (!dia || !mes || !anio) return;

            const clave_fecha = `${anio}-${mes.padStart(2, "0")}-${dia.padStart(2, "0")}`;
            sesiones_por_fecha.set(
                clave_fecha,
                (sesiones_por_fecha.get(clave_fecha) || 0) + 1
            );
        });

        const fechas_ordenadas = [...sesiones_por_fecha.entries()]
            .sort(([fecha_a], [fecha_b]) => fecha_a.localeCompare(fecha_b));

        if (fechas_ordenadas.length === 0) {
            if (grafica_sesiones) {
                grafica_sesiones.destroy();
                grafica_sesiones = null;
            }

            contenedor_grafica_sesiones.hidden = true;
            mensaje_grafica_sesiones.textContent = "No hay datos para mostrar.";
            mensaje_grafica_sesiones.hidden = false;
            return;
        }

        contenedor_grafica_sesiones.hidden = false;
        mensaje_grafica_sesiones.hidden = true;

        const datos_grafica = {
            labels: fechas_ordenadas.map(([fecha]) => {
                const [anio, mes, dia] = fecha.split("-");
                return `${dia}/${mes}/${anio}`;
            }),
            datasets: [{
                label: "Inicios de sesión",
                data: fechas_ordenadas.map(([, total]) => total),
                borderColor: "#00779e",
                backgroundColor: "rgba(0, 119, 158, 0.14)",
                fill: true,
                tension: 0.3,
                pointRadius: 3
            }]
        };

        if (!grafica_sesiones) {
            grafica_sesiones = new Chart(canvas_grafica_sesiones, {
                type: "line",
                data: datos_grafica,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            callbacks: {
                                label: contexto =>
                                    `${contexto.parsed.y} ${
                                        contexto.parsed.y === 1
                                            ? "inicio de sesión"
                                            : "inicios de sesión"
                                    }`
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                precision: 0
                            }
                        }
                    }
                }
            });
        } else {
            grafica_sesiones.data = datos_grafica;
            grafica_sesiones.update();
        }
    }

    function mostrar_inicios_sesiones() {
        contenedor_inicios_sesiones.innerHTML = "";

        const inicio = (pagina_actual - 1) * FILAS_POR_PAGINA;
        const final = inicio + FILAS_POR_PAGINA;

        const inicios_sesiones_pagina = registros_inicios_sesiones.slice(inicio, final);

        if (inicios_sesiones_pagina.length === 0) {
            contenedor_inicios_sesiones.innerHTML = `
            <tr>
                <td colspan="8" class="texto_sin_registros">
                    No hay inicios de sesión registrados.
                </td>
            </tr>
        `;

            actualizarEstadisticasSesiones();
            actualizarBotonesIniciosSesiones();
            return;
        }

        inicios_sesiones_pagina.forEach((registro, index) => {
            const fila = document.createElement("tr");

            fila.innerHTML = `
            <td>${inicio + index + 1}</td>
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

        actualizarEstadisticasSesiones();
        actualizarBotonesIniciosSesiones();
    }

    btn_av.addEventListener("click", () => {
        const total_paginas = Math.ceil(
            registros_inicios_sesiones.length / FILAS_POR_PAGINA
        );

        if (pagina_actual < total_paginas) {
            pagina_actual++;
            mostrar_inicios_sesiones();
        }
    });

    btn_ret.addEventListener("click", () => {
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
                    "X-CSRFToken": document.querySelector(
                        "[name=csrfmiddlewaretoken]"
                    ).value
                },
                body: formulario
            });

            const resultado = await respuesta.json();

            console.log(resultado);

            if (!respuesta.ok) {
                throw new Error("Error al consultar los inicios de sesión.");
            }

            registros_inicios_sesiones = Array.isArray(resultado)
                ? resultado
                : resultado.registros || [];

            estado_sesiones.hidden = true;
            pagina_actual = 1;

            mostrar_inicios_sesiones();

        } catch (error) {
            console.error("Error al cargar los inicios de sesión:", error);
            estado_sesiones.textContent =
                "No se pudieron cargar los inicios de sesión. Inténtelo nuevamente.";
            estado_sesiones.hidden = false;
            registros_inicios_sesiones = [];
            pagina_actual = 1;
            mostrar_inicios_sesiones();
        }
    }

    inicios_sesiones_registradas();
});