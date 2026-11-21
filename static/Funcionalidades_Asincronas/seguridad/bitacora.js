document.addEventListener("DOMContentLoaded", async () => {

    const contenedor_bitacora = document.getElementById("contenedor_bitacora");

    const input_cedula_identidad = document.getElementById("cedula_identidad");
    const select_nacionalidad = document.getElementById("nacionalidad");

    const btn_ret = document.querySelector(".botones_navegacion .btn_ret");
    const btn_av = document.querySelector(".botones_navegacion .btn_av");
    
    const total_acciones = document.getElementById("total_acciones_bitacora");
    const total_usuarios = document.getElementById("total_usuarios_bitacora");
    const total_modulos = document.getElementById("total_modulos_bitacora");
    const canvas_grafica_bitacora = document.getElementById("grafica_bitacora");
    const contenedor_grafica_bitacora = document.getElementById("contenedor_grafica_bitacora");
    
    const mensaje_grafica_bitacora = document.getElementById("mensaje_grafica_bitacora");
    const estado_bitacora = document.getElementById("estado_bitacora");

    configurarCedula(input_cedula_identidad, select_nacionalidad);

    const FILAS_POR_PAGINA = 10;

    let cedula = "", nacionalidad = "";
    let registros_bitacora = [];
    let pagina_actual = 1;
    let grafica_bitacora = null;

    select_nacionalidad.addEventListener("change", async () => {
        await bitacora_registrados();
    });

    input_cedula_identidad.addEventListener("input", async () => {
        await bitacora_registrados();
    });

    function actualizarBotonesBitacora() {
        const total_paginas = Math.ceil(
            registros_bitacora.length / FILAS_POR_PAGINA
        );

        btn_ret.disabled = pagina_actual <= 1;
        btn_av.disabled = pagina_actual >= total_paginas;
    }

    function actualizarEstadisticasBitacora() {
        total_acciones.textContent = registros_bitacora.length;
        total_usuarios.textContent = new Set(
            registros_bitacora.map(registro => registro.cedula).filter(Boolean)
        ).size;
        total_modulos.textContent = new Set(
            registros_bitacora.map(registro => registro.nombre_modulo).filter(Boolean)
        ).size;

        if (typeof Chart === "undefined") {
            contenedor_grafica_bitacora.hidden = true;
            mensaje_grafica_bitacora.textContent =
                "No se pudo cargar la gráfica de estadísticas.";
            mensaje_grafica_bitacora.hidden = false;
            return;
        }

        const acciones_por_fecha = new Map();

        registros_bitacora.forEach(registro => {
            const fecha = (registro.fecha || "").split(" ")[0];
            const partes = fecha.split("/");
            if (partes.length !== 3) return;

            const [dia, mes, anio] = partes;
            if (!dia || !mes || !anio) return;

            const clave_fecha = `${anio}-${mes.padStart(2, "0")}-${dia.padStart(2, "0")}`;
            acciones_por_fecha.set(
                clave_fecha,
                (acciones_por_fecha.get(clave_fecha) || 0) + 1
            );
        });

        const fechas_ordenadas = [...acciones_por_fecha.entries()]
            .sort(([fecha_a], [fecha_b]) => fecha_a.localeCompare(fecha_b));

        if (fechas_ordenadas.length === 0) {
            if (grafica_bitacora) {
                grafica_bitacora.destroy();
                grafica_bitacora = null;
            }

            contenedor_grafica_bitacora.hidden = true;
            mensaje_grafica_bitacora.textContent = "No hay datos para mostrar.";
            mensaje_grafica_bitacora.hidden = false;
            return;
        }

        contenedor_grafica_bitacora.hidden = false;
        mensaje_grafica_bitacora.hidden = true;

        const datos_grafica = {
            labels: fechas_ordenadas.map(([fecha]) => {
                const [anio, mes, dia] = fecha.split("-");
                return `${dia}/${mes}/${anio}`;
            }),
            datasets: [{
                label: "Acciones",
                data: fechas_ordenadas.map(([, total]) => total),
                borderColor: "#00779e",
                backgroundColor: "rgba(0, 119, 158, 0.14)",
                fill: true,
                tension: 0.3,
                pointRadius: 3
            }]
        };

        if (!grafica_bitacora) {
            grafica_bitacora = new Chart(canvas_grafica_bitacora, {
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
                                        contexto.parsed.y === 1 ? "acción" : "acciones"
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
            grafica_bitacora.data = datos_grafica;
            grafica_bitacora.update();
        }
    }

    function mostrar_bitacora() {
        contenedor_bitacora.innerHTML = "";

        const inicio = (pagina_actual - 1) * FILAS_POR_PAGINA;
        const fin = inicio + FILAS_POR_PAGINA;

        const registros_pagina = registros_bitacora.slice(inicio, fin);

        if (registros_pagina.length === 0) {
            contenedor_bitacora.innerHTML = `
            <tr>
                <td colspan="7" class="texto_sin_registros">
                    No hay registros en la bitácora.
                </td>
            </tr>
        `;

            actualizarEstadisticasBitacora();
            actualizarBotonesBitacora();
            return;
        }

        registros_pagina.forEach((registro, indice) => {
            const fila = document.createElement("tr");
            const valores = [
                inicio + indice + 1,
                registro.usuario,
                registro.cedula,
                registro.cargo_usuario,
                registro.nombre_modulo,
                registro.fecha,
                registro.accion
            ];

            valores.forEach((valor) => {
                const celda = document.createElement("td");
                celda.textContent = valor ?? "No especificado";
                fila.appendChild(celda);
            });

            contenedor_bitacora.appendChild(fila);
        });

        actualizarEstadisticasBitacora();
        actualizarBotonesBitacora();
    }

    btn_av.addEventListener("click", () => {
        const total_paginas = Math.ceil(
            registros_bitacora.length / FILAS_POR_PAGINA
        );

        if (pagina_actual < total_paginas) {
            pagina_actual++;
            mostrar_bitacora();
        }
    });

    btn_ret.addEventListener("click", () => {
        if (pagina_actual > 1) {
            pagina_actual--;
            mostrar_bitacora();
        }
    });

    async function bitacora_registrados() {
        try {
            const formulario = new FormData();


            cedula = input_cedula_identidad.value.trim();
            nacionalidad = select_nacionalidad.value;

            formulario.append("cedula", cedula);
            formulario.append("nacionalidad", nacionalidad);

            console.log("Cédula:", cedula);
            console.log("Nacionalidad:", nacionalidad);
            console.log(cedula)
            console.log(nacionalidad)

            const respuesta = await fetch("/bitacora_registradas/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector(
                        "[name=csrfmiddlewaretoken]"
                    ).value
                },
                body: formulario
            });

            if (!respuesta.ok) {
                throw new Error("Error al consultar la bitácora.");
            }

            const resultado = await respuesta.json();

            console.log(resultado);

            registros_bitacora = Array.isArray(resultado)
                ? resultado
                : resultado.registros || [];

            estado_bitacora.hidden = true;
            pagina_actual = 1;

            mostrar_bitacora();

        } catch (error) {
            console.error("Error al cargar la bitácora:", error);
            estado_bitacora.textContent =
                "No se pudo cargar la bitácora. Inténtelo nuevamente.";
            estado_bitacora.hidden = false;
            registros_bitacora = [];
            pagina_actual = 1;
            mostrar_bitacora();
        }
    }

    bitacora_registrados();

});