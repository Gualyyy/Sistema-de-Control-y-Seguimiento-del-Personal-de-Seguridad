document.addEventListener("DOMContentLoaded", () => {

    const contadores = document.querySelectorAll(".contenedor_estadisticas .numero_contador");
    const grafica_empleados = document.getElementById("grafica_perfiles_registrados").getContext("2d");
    const grafica_categoria_equipo = document.getElementById("grafica_categoria_equipo").getContext("2d");

    const estado = document.getElementById("ultimo_inicio_estado");
    const fecha = document.getElementById("ultimo_inicio_fecha");
    const cierre = document.getElementById("ultimo_inicio_cierre");
    const ip = document.getElementById("ultimo_inicio_ip");
    const dispositivo = document.getElementById("ultimo_inicio_dispositivo");
    const mensaje = document.getElementById("ultimo_inicio_mensaje");
    const titulo = document.getElementById("ultimo_inicio_titulo");

    async function registros_sistema() {
        try {
            const respuesta = await fetch("/registros_sistema/");
            const resultado = await respuesta.json();
            console.log(resultado);

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
    registros_sistema();

    const grafica_perfiles = new Chart(grafica_empleados, {
        type: "bar",
        data: {
            labels: [
                "Supervisores",
                "Personal de limpieza",
                "Despachadores",
                "Vigilantes"
            ],
            datasets: [{
                label: "Personal registrado",
                data: [0, 0, 0, 0],
                backgroundColor: [
                    "#00779e",
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

    async function empleados_administrador() {
        try {
            const respuesta = await fetch("/empleados_administrador/");
            const resultado = await respuesta.json();
            console.log(resultado);

            grafica_perfiles.data.datasets[0].data = [
                resultado.total_supervisores,
                resultado.total_limpieza,
                resultado.total_despachadores,
                resultado.total_vigilantes
            ];

            grafica_perfiles.update();

        } catch (error) {
            console.error(error);
        }
    }
    empleados_administrador();

    const grafica_categoria = new Chart(grafica_categoria_equipo, {
        type: "doughnut",
        data: {
            labels: [],
            datasets: [{
                label: "Equipos registrados",
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

    async function categoria_equipo() {
        try {
            const respuesta = await fetch("/registro_equipo_categoria/");
            const resultado = await respuesta.json();
            console.log(resultado);

            const categorias = resultado.categorias;

            grafica_categoria.data.labels = categorias.map(item => item.categoria);
            grafica_categoria.data.datasets[0].data = categorias.map(item => item.total);

            grafica_categoria.update();

        } catch (error) {
            console.error(error);
        }
    }
    categoria_equipo();

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