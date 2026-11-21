document.addEventListener("DOMContentLoaded", () => {

    const select_fechas = document.getElementById("fechas_registradas");
    const contenedor_intentos_sesion = document.getElementById("contenedor_intentos_sesion");
    const total_intentos = document.getElementById("total_intentos");
    const intentos_exitosos = document.getElementById("intentos_exitosos");
    const intentos_fallidos = document.getElementById("intentos_fallidos");
    const canvas_grafica_intentos = document.getElementById("grafica_intentos");
    const contenedor_grafica_intentos = document.getElementById(
        "contenedor_grafica_intentos"
    );
    const mensaje_grafica_intentos = document.getElementById(
        "mensaje_grafica_intentos"
    );
    const estado_intentos = document.getElementById("estado_intentos");

    const btn_ret = document.querySelector(".botones_navegacion .btn_ret");
    const btn_av = document.querySelector(".botones_navegacion .btn_av");

    let fecha = "";

    const FILAS_POR_PAGINA_INTENTOS = 10;

    let registros_intentos = [];
    let pagina_actual_intentos = 1;
    let grafica_intentos = null;

    async function fechas_registradas() {
        try {
            const respuesta = await fetch("/fechas_intentos_registrados/");
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

        await intentos_registrados();
    });

    function actualizarBotonesIntentos() {
        const total_paginas = Math.ceil(
            registros_intentos.length / FILAS_POR_PAGINA_INTENTOS
        );

        btn_ret.disabled = pagina_actual_intentos <= 1;
        btn_av.disabled = pagina_actual_intentos >= total_paginas;
    }

    function actualizarEstadisticasIntentos() {
        const exitosos = registros_intentos.filter(
            intento => intento.exitoso
        ).length;

        total_intentos.textContent = registros_intentos.length;
        intentos_exitosos.textContent = exitosos;
        intentos_fallidos.textContent = registros_intentos.length - exitosos;

        if (typeof Chart === "undefined") {
            contenedor_grafica_intentos.hidden = true;
            mensaje_grafica_intentos.textContent =
                "No se pudo cargar la gráfica de estadísticas.";
            mensaje_grafica_intentos.hidden = false;
            return;
        }

        const intentos_por_fecha = new Map();

        registros_intentos.forEach(intento => {
            const fecha_hora = (intento.fecha_hora || "").split(" ")[0];
            const partes = fecha_hora.split("/");
            if (partes.length !== 3) return;

            const [dia, mes, anio] = partes;
            if (!dia || !mes || !anio) return;

            const clave_fecha = `${anio}-${mes.padStart(2, "0")}-${dia.padStart(2, "0")}`;
            intentos_por_fecha.set(
                clave_fecha,
                (intentos_por_fecha.get(clave_fecha) || 0) + 1
            );
        });

        const fechas_ordenadas = [...intentos_por_fecha.entries()]
            .sort(([fecha_a], [fecha_b]) => fecha_a.localeCompare(fecha_b));

        if (fechas_ordenadas.length === 0) {
            if (grafica_intentos) {
                grafica_intentos.destroy();
                grafica_intentos = null;
            }

            contenedor_grafica_intentos.hidden = true;
            mensaje_grafica_intentos.textContent = "No hay datos para mostrar.";
            mensaje_grafica_intentos.hidden = false;
            return;
        }

        contenedor_grafica_intentos.hidden = false;
        mensaje_grafica_intentos.hidden = true;

        const datos_grafica = {
            labels: fechas_ordenadas.map(([fecha]) => {
                const [anio, mes, dia] = fecha.split("-");
                return `${dia}/${mes}/${anio}`;
            }),
            datasets: [{
                label: "Intentos de sesión",
                data: fechas_ordenadas.map(([, total]) => total),
                borderColor: "#00779e",
                backgroundColor: "rgba(0, 119, 158, 0.14)",
                fill: true,
                tension: 0.3,
                pointRadius: 3
            }]
        };

        if (!grafica_intentos) {
            grafica_intentos = new Chart(canvas_grafica_intentos, {
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
                                            ? "intento"
                                            : "intentos"
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
            grafica_intentos.data = datos_grafica;
            grafica_intentos.update();
        }
    }

    function mostrar_intentos() {
        contenedor_intentos_sesion.innerHTML = "";

        const inicio = (pagina_actual_intentos - 1) * FILAS_POR_PAGINA_INTENTOS;
        const fin = inicio + FILAS_POR_PAGINA_INTENTOS;

        const intentos_pagina = registros_intentos.slice(inicio, fin);

        if (intentos_pagina.length === 0) {
            contenedor_intentos_sesion.innerHTML = `
            <tr>
                <td colspan="6" class="texto_sin_registros">
                    No hay intentos de inicio de sesión registrados.
                </td>
            </tr>
        `;

            actualizarEstadisticasIntentos();
            actualizarBotonesIntentos();
            return;
        }

        intentos_pagina.forEach((intento, indice) => {
            const fila = document.createElement("tr");

            fila.innerHTML = `
            <td>${inicio + indice + 1}</td>
            <td>${intento.usuario}</td>
            <td>${intento.nombre_usuario}</td>
            <td>${intento.direccion_ip}</td>
            <td>${intento.exitoso ? "Exitoso" : "Fallido"}</td>
            <td>${intento.fecha_hora}</td>
        `;

            contenedor_intentos_sesion.appendChild(fila);
        });

        actualizarEstadisticasIntentos();
        actualizarBotonesIntentos();
    }

    btn_av.addEventListener("click", () => {
        const total_paginas = Math.ceil(
            registros_intentos.length / FILAS_POR_PAGINA_INTENTOS
        );

        if (pagina_actual_intentos < total_paginas) {
            pagina_actual_intentos++;
            mostrar_intentos();
        }
    });

    btn_ret.addEventListener("click", () => {
        if (pagina_actual_intentos > 1) {
            pagina_actual_intentos--;
            mostrar_intentos();
        }
    });

    async function intentos_registrados() {
        try {
            const formulario = new FormData();
            formulario.append("fecha", fecha);

            const csrf = document.querySelector("[name=csrfmiddlewaretoken]");

            const respuesta = await fetch("/intentos_registrados/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrf.value
                },
                body: formulario
            });

            if (!respuesta.ok) {
                throw new Error("Error al consultar los intentos de sesión.");
            }

            const resultado = await respuesta.json();

            if (resultado.estado !== "exito") {
                throw new Error(
                    resultado.mensaje || "No se pudieron obtener los intentos."
                );
            }

            registros_intentos = resultado.intentos || [];
            estado_intentos.hidden = true;
            pagina_actual_intentos = 1;

            mostrar_intentos();

        } catch (error) {
            console.error("Error al cargar los intentos:", error);

            registros_intentos = [];
            pagina_actual_intentos = 1;
            estado_intentos.textContent =
                "No se pudieron cargar los intentos de sesión. Inténtelo nuevamente.";
            estado_intentos.hidden = false;
            actualizarEstadisticasIntentos();

            contenedor_intentos_sesion.innerHTML = `
            <tr>
                <td colspan="6" class="texto_sin_registros">
                    Ocurrió un error al cargar los intentos de sesión.
                </td>
            </tr>
        `;

            btn_ret.disabled = true;
            btn_av.disabled = true;
        }
    }

    intentos_registrados();
});