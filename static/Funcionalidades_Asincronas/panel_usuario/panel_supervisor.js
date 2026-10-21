document.addEventListener("DOMContentLoaded", () => {
    const contadores = document.querySelectorAll(".contenedor_estadisticas .numero_contador");
    const grafica_empleados = document.getElementById("grafica_perfiles_registrados").getContext("2d");
    const grafica_equipos_entregados = document.getElementById("grafica_equipos_entregados").getContext("2d");
    const grafica_tipos_incidencias = document.getElementById("grafica_tipos_incidencias").getContext("2d");
    const grafica_equipos_asignados = document.getElementById("grafica_equipos_asignados").getContext("2d");

    const estado = document.getElementById("ultimo_inicio_estado");
    const fecha = document.getElementById("ultimo_inicio_fecha");
    const cierre = document.getElementById("ultimo_inicio_cierre");
    const ip = document.getElementById("ultimo_inicio_ip");
    const dispositivo = document.getElementById("ultimo_inicio_dispositivo");
    const mensaje = document.getElementById("ultimo_inicio_mensaje");
    const titulo = document.getElementById("ultimo_inicio_titulo");

    async function registro_sistema_supervisor() {
        try {
            const respuesta = await fetch("/registro_sistema_supervisor/");
            const resultado = await respuesta.json();
            console.log(resultado);

            if (resultado.estado !== "exito") {
                Swal.fire({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon
                });
                return;
            }

            contadores.forEach((contador) => {
                const campo = contador.dataset.campo;
                const total = Number(resultado[campo]);

                if (!Number.isFinite(total)) {
                    contador.textContent = "0";
                    return;
                }

                contador.dataset.total = total;

                const duracion = 1000;
                const inicio = performance.now();

                function animarContador(tiempoActual) {
                    const progreso = Math.min(
                        (tiempoActual - inicio) / duracion,
                        1
                    );

                    const avance = 1 - Math.pow(1 - progreso, 3);
                    const valorActual = Math.floor(total * avance);

                    contador.textContent = valorActual.toLocaleString("es-ES");

                    if (progreso < 1) {
                        requestAnimationFrame(animarContador);
                    } else {
                        contador.textContent = total.toLocaleString("es-ES");
                    }
                }

                requestAnimationFrame(animarContador);
            });

        } catch (error) {
            console.error(error);
        }
    }
    registro_sistema_supervisor();

    const grafica_perfiles = new Chart(grafica_empleados, {
        type: "bar",
        data: {
            labels: [
                "Personal de limpieza",
                "Despachadores",
                "Vigilantes"
            ],
            datasets: [{
                label: "Personal registrado",
                data: [0, 0, 0],
                backgroundColor: [
                    "#168039",
                    "#06d9a4",
                    "#6855c5"
                ],
                borderRadius: 6,
                maxBarThickness: 35
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    enabled: true
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    },
                    title: {
                        display: true,
                        text: "Cantidad de empleados"
                    },
                    grid: {
                        color: "#edf1f5"
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });

    async function empleados_supervisor_turno() {
        try {
            const respuesta = await fetch("/empleados_supervisor_turno/");
            const resultado = await respuesta.json();
            console.log(resultado);

            if (resultado.estado !== "exito") {
                Swal.fire({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon
                });
                return;
            }

            grafica_perfiles.data.datasets[0].data = [
                resultado.cantidad_limpieza,
                resultado.cantidad_despachadores,
                resultado.cantidad_vigilantes
            ];

            grafica_perfiles.update();
        } catch (error) {
            console.error(error);
        }
    }
    empleados_supervisor_turno();

    const grafica_equipos = new Chart(grafica_equipos_entregados, {
        type: "doughnut",
        data: {
            labels: [],
            datasets: [{
                label: "Equipos entregados",
                data: [],
                backgroundColor: [
                    "#102f4e",
                    "#00779e",
                    "#16805d",
                    "#d97706",
                    "#6855c5",
                    "#c0395b",
                    "#64748b"
                ],
                borderColor: "#ffffff",
                borderWidth: 3,
                hoverOffset: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "bottom",
                    labels: {
                        usePointStyle: true,
                        padding: 18
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function (contexto) {
                            return `${contexto.label}: ${contexto.raw} equipo(s)`;
                        }
                    }
                }
            }
        }
    });

    async function equipos_entregados() {
        try {
            const respuesta = await fetch("/equipos_entregados_supervisores/");
            const resultado = await respuesta.json();
            console.log(resultado);

            if (resultado.estado !== "exito") {
                Swal.fire({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon
                });
                return;
            }

            const categorias = resultado.categorias;

            grafica_equipos.data.labels = categorias.map(
                item => item.nombre
            );

            grafica_equipos.data.datasets[0].data = categorias.map(
                item => item.cantidad_equipos
            );

            grafica_equipos.update();
        } catch (error) {
            console.error(error);
        }
    }
    equipos_entregados();

    const grafica_incidencias = new Chart(grafica_tipos_incidencias, {
        type: "line",
        data: {
            labels: [],
            datasets: [{
                label: "Incidencias registradas",
                data: [],
                borderColor: "#00779e",
                backgroundColor: "rgba(0, 119, 158, 0.15)",
                borderWidth: 3,
                pointBackgroundColor: "#102f4e",
                pointBorderColor: "#ffffff",
                pointBorderWidth: 2,
                pointRadius: 5,
                pointHoverRadius: 7,
                tension: 0.3,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "bottom",
                    labels: {
                        usePointStyle: true,
                        padding: 18
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function (contexto) {
                            return `${contexto.dataset.label}: ${contexto.raw}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0,
                        stepSize: 1
                    },
                    title: {
                        display: true,
                        text: "Cantidad de incidencias"
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: "Tipo de incidencia"
                    }
                }
            }
        }
    });

    async function incidencias_ocurridos_supervisor() {
        try {
            const respuesta = await fetch("/incidencias_ocurridos_supervisor/");
            const resultado = await respuesta.json();
            console.log(resultado);

            if (resultado.estado !== "exito") {
                Swal.fire({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon
                });
                return;
            }

            const incidencias = resultado.incidencias_por_tipo;

            grafica_incidencias.data.labels = incidencias.map(
                item => item.nombre
            );

            grafica_incidencias.data.datasets[0].data = incidencias.map(
                item => item.cantidad
            );

            grafica_incidencias.update();
        } catch (error) {
            console.error(error);
        }
    }
    incidencias_ocurridos_supervisor();

    const grafica_asignados = new Chart(grafica_equipos_asignados, {
        type: "bar",
        data: {
            labels: [],
            datasets: [
                {
                    label: "Equipos asignados",
                    data: [],
                    backgroundColor: "#102f4e",
                    borderRadius: 5
                },
                {
                    label: "Equipos devueltos",
                    data: [],
                    backgroundColor: "#00779e",
                    borderRadius: 5
                },
                {
                    label: "Equipos en posesión",
                    data: [],
                    backgroundColor: "#16805d",
                    borderRadius: 5
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "bottom",
                    labels: {
                        usePointStyle: true,
                        padding: 18
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function (contexto) {
                            return `${contexto.dataset.label}: ${contexto.raw} equipo(s)`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0,
                        stepSize: 1
                    },
                    title: {
                        display: true,
                        text: "Cantidad de equipos"
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: "Categoría de equipo"
                    }
                }
            }
        }
    });

    async function equipos_asignados_supervisor() {
        try {
            const respuesta = await fetch("/equipos_asignados_supervisor/");
            const resultado = await respuesta.json();
            console.log(resultado);

            if (resultado.estado !== "exito") {
                Swal.fire({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon
                });
                return;
            }

            const categorias = resultado.categorias;

            grafica_asignados.data.labels = categorias.map(
                item => item.categoria
            );

            grafica_asignados.data.datasets[0].data = categorias.map(
                item => item.cantidad_asignada
            );

            grafica_asignados.data.datasets[1].data = categorias.map(
                item => item.cantidad_devuelta
            );

            grafica_asignados.data.datasets[2].data = categorias.map(
                item => item.cantidad_en_posesion
            );

            grafica_asignados.update();
        } catch (error) {
            console.error(error);
        }
    }
    equipos_asignados_supervisor();

    async function cargar_ultimo_inicio_sesion() {

        const formatear_fecha = valor => {
            if (!valor) return "No disponible";

            const fecha = new Date(valor);

            if (Number.isNaN(fecha.getTime())) return "No disponible";

            return fecha.toLocaleString("es-VE", {
                dateStyle: "long",
                timeStyle: "short"
            });
        };

        try {
            const respuesta = await fetch("/ultimo_inicio_sesion/");
            const resultado = await respuesta.json();
            console.log(resultado);

            const sesion = resultado.sesion;

            if (!sesion) {
                titulo.textContent = "Sin sesiones anteriores";
                estado.textContent = "Sin registros";
                estado.className = "ultimo_inicio_estado sesion_sin_registro";

                fecha.textContent = "No disponible";
                cierre.textContent = "No disponible";
                ip.textContent = "No disponible";
                dispositivo.textContent = "No disponible";

                mensaje.textContent = "No existen registros de sesiones anteriores.";
                mensaje.hidden = false;

                return;
            }

            titulo.textContent = "Sesión anterior";

            estado.textContent = sesion.activa ? "Activa" : "Finalizada";
            estado.className = "ultimo_inicio_estado " +
                (sesion.activa ? "sesion_activa" : "sesion_cerrada");

            fecha.textContent = formatear_fecha(sesion.fecha_inicio);
            cierre.textContent = formatear_fecha(sesion.fecha_fin);
            ip.textContent = sesion.direccion_ip || "No disponible";

            if (sesion.dispositivo && typeof sesion.dispositivo === "object") {
                const info = sesion.dispositivo;

                dispositivo.textContent = [
                    info.dispositivo,
                    info.sistema,
                    info.navegador,
                    info.version ? `Versión ${info.version}` : ""
                ].filter(Boolean).join(" · ");
            } else {
                dispositivo.textContent = sesion.dispositivo || "No disponible";
            }

            mensaje.textContent = "";
            mensaje.hidden = true;

        } catch (error) {
            console.error("Error al consultar la sesión:", error);

            titulo.textContent = "Último inicio de sesión";
            estado.textContent = "No disponible";
            estado.className = "ultimo_inicio_estado sesion_sin_registro";

            fecha.textContent = "No disponible";
            cierre.textContent = "No disponible";
            ip.textContent = "No disponible";
            dispositivo.textContent = "No disponible";

            mensaje.textContent = "No fue posible cargar la información de la sesión.";
            mensaje.hidden = false;
        }
    }
    cargar_ultimo_inicio_sesion();
});