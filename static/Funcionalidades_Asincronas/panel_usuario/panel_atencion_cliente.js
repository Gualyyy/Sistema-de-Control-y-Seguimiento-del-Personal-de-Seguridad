document.addEventListener("DOMContentLoaded", () => {

    const estado = document.getElementById("ultimo_inicio_estado");
    const fecha = document.getElementById("ultimo_inicio_fecha");
    const cierre = document.getElementById("ultimo_inicio_cierre");
    const ip = document.getElementById("ultimo_inicio_ip");
    const dispositivo = document.getElementById("ultimo_inicio_dispositivo");
    const mensaje = document.getElementById("ultimo_inicio_mensaje");
    const titulo = document.getElementById("ultimo_inicio_titulo");

    let grafica_evolucion_ventas = null;
    let grafica_productos_mas_vendidos = null;

    /* VARIABLES DE TASAS */
    let tasa_dolar = 0;
    let tasa_euro = 0;

    let fecha_tasa_dolar = null;
    let fecha_tasa_euro = null;

    /* REGISTROS DEL SISTEMA DE ATENCIÓN AL CLIENTE*/
    async function registros_sistema() {

        const contenedor = document.querySelector(
            ".contenedor_panel_usuario"
        );

        if (!contenedor) return;

        const url = contenedor.dataset.urlRegistros;

        const contadores = contenedor.querySelectorAll(
            ".numero_contador"
        );

        const formato_cantidad = new Intl.NumberFormat("es-VE", {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        });

        const formato_moneda = new Intl.NumberFormat("es-VE", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });

        function formatear_valor(valor, formato) {

            if (formato === "ves") {
                return "Bs. " + formato_moneda.format(valor);
            }

            if (formato === "usd") {
                return "$ " + formato_moneda.format(valor);
            }

            return formato_cantidad.format(valor);
        }

        function animar_contador(contador, valor) {

            const formato = contador.dataset.formato || "cantidad";

            const duracion = 1000;
            const inicio = performance.now();

            function animar(tiempo_actual) {
                const progreso = Math.min(
                    (tiempo_actual - inicio) / duracion,
                    1
                );

                const avance = 1 - Math.pow(1 - progreso, 3);

                const valor_actual = valor * avance;

                contador.textContent = formatear_valor(
                    valor_actual,
                    formato
                );

                if (progreso < 1) {

                    requestAnimationFrame(animar);

                } else {

                    contador.textContent = formatear_valor(
                        valor,
                        formato
                    );

                }
            }

            requestAnimationFrame(animar);
        }

        try {
            const respuesta = await fetch(url, {
                method: "GET",
                headers: {
                    "X-Requested-With": "XMLHttpRequest"
                }
            });
            const resultado = await respuesta.json();
            console.log("Registros del sistema:", resultado);

            contadores.forEach((contador) => {

                const campo = contador.dataset.campo;

                const valor = Number(resultado[campo]);

                if (!Number.isFinite(valor)) {

                    contador.textContent = formatear_valor(
                        0,
                        contador.dataset.formato || "cantidad"
                    );

                    return;
                }

                contador.dataset.total = valor;

                animar_contador(contador, valor);

            });
        } catch (error) {
            console.error("Error al cargar los registros del sistema:", error);
        }
    }
    registros_sistema();

    /* FORMATO DE MONEDA */
    const formato_tasa = new Intl.NumberFormat("es-VE", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });

    /* CONSULTAR TASA OFICIAL DEL DÓLAR */
    async function tasa_oficial_dolar() {

        const elemento_valor = document.getElementById("valor_tasa_dolar");
        const elemento_fecha = document.getElementById("fecha_tasa_dolar");

        try {

            const respuesta = await fetch(
                "https://ve.dolarapi.com/v1/dolares/oficial"
            );

            if (!respuesta.ok) {
                throw new Error("No se pudo consultar la tasa del dólar.");
            }

            const resultado = await respuesta.json();

            const tasa = Number(resultado.promedio);

            if (!Number.isFinite(tasa) || tasa <= 0) {
                throw new Error("La tasa del dólar recibida no es válida.");
            }

            tasa_dolar = Number(tasa.toFixed(2));

            fecha_tasa_dolar = resultado.fechaActualizacion || null;

            if (elemento_valor) {
                elemento_valor.textContent = "Bs. " + formato_tasa.format(tasa_dolar);
            }

            if (elemento_fecha) {
                elemento_fecha.textContent = fecha_tasa_dolar
                    ? "Actualizado: " + new Date(fecha_tasa_dolar).toLocaleString("es-VE")
                    : "Tasa oficial";
            }

        } catch (error) {

            console.error("Error al consultar el dólar:", error);

            if (elemento_fecha) {
                elemento_fecha.textContent = "No disponible";
            }

        }
    }

    /* CONSULTAR TASA OFICIAL DEL EURO */
    async function tasa_oficial_euro() {

        const elemento_valor = document.getElementById("valor_tasa_euro");
        const elemento_fecha = document.getElementById("fecha_tasa_euro");

        try {

            const respuesta = await fetch(
                "https://ve.dolarapi.com/v1/euros/oficial"
            );

            if (!respuesta.ok) {
                throw new Error("No se pudo consultar la tasa del euro.");
            }

            const resultado = await respuesta.json();

            const tasa = Number(resultado.promedio);

            if (!Number.isFinite(tasa) || tasa <= 0) {
                throw new Error("La tasa del euro recibida no es válida.");
            }

            tasa_euro = Number(tasa.toFixed(2));

            fecha_tasa_euro = resultado.fechaActualizacion || null;

            if (elemento_valor) {
                elemento_valor.textContent = "Bs. " + formato_tasa.format(tasa_euro);
            }

            if (elemento_fecha) {
                elemento_fecha.textContent = fecha_tasa_euro
                    ? "Actualizado: " + new Date(fecha_tasa_euro).toLocaleString("es-VE")
                    : "Tasa oficial";
            }

        } catch (error) {

            console.error("Error al consultar el euro:", error);

            if (elemento_fecha) {
                elemento_fecha.textContent = "No disponible";
            }

        }
    }

    /* INICIALIZAR TASAS */
    async function inicializar_tasas_cambio() {
        await Promise.allSettled([
            tasa_oficial_dolar(),
            tasa_oficial_euro()
        ]);
    }
    inicializar_tasas_cambio();

    // FORMATO DE BOLÍVARES
    const formato_bolivares = new Intl.NumberFormat("es-VE", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });

    // EVOLUCIÓN DE VENTAS
    async function cargar_evolucion_ventas() {

        const contenedor = document.querySelector(
            ".estadistica_perfiles_registrados[data-url-grafica]"
        );

        const canvas = document.getElementById(
            "grafica_evolucion_ventas"
        );

        if (!contenedor || !canvas) {
            return;
        }

        try {

            const respuesta = await fetch(contenedor.dataset.urlGrafica, {
                method: "GET",
                headers: {
                    "X-Requested-With": "XMLHttpRequest"
                },
                credentials: "same-origin"
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            if (!respuesta.ok || resultado.estado !== "exito") {
                throw new Error(
                    resultado.descripcion || "No se pudo consultar la evolución de ventas."
                );
            }

            if (grafica_evolucion_ventas) {
                grafica_evolucion_ventas.destroy();
            }

            grafica_evolucion_ventas = new Chart(
                canvas,
                {
                    type: "line",

                    data: {
                        labels: resultado.etiquetas,

                        datasets: [
                            {
                                label: "Ventas en bolívares",

                                data: resultado.valores,

                                borderColor: "#00779e",
                                backgroundColor: "rgba(0, 119, 158, 0.12)",

                                borderWidth: 3,

                                fill: true,

                                tension: 0.35,

                                pointRadius: 4,
                                pointHoverRadius: 7,

                                pointBackgroundColor: "#ffffff",
                                pointBorderColor: "#00779e",
                                pointBorderWidth: 2
                            }
                        ]
                    },

                    options: {
                        responsive: true,
                        maintainAspectRatio: false,

                        interaction: {
                            intersect: false,
                            mode: "index"
                        },

                        plugins: {
                            legend: {
                                display: true,
                                position: "top",

                                labels: {
                                    color: "#102f4e",
                                    usePointStyle: true,
                                    padding: 18,
                                    font: {
                                        size: 12,
                                        weight: "600"
                                    }
                                }
                            },

                            tooltip: {
                                backgroundColor: "#102f4e",
                                titleColor: "#ffffff",
                                bodyColor: "#ffffff",
                                padding: 12,

                                callbacks: {
                                    label: function (context) {

                                        return "Ventas: Bs. " +
                                            formato_bolivares.format(
                                                context.parsed.y
                                            );
                                    }
                                }
                            }
                        },

                        scales: {
                            x: {
                                grid: {
                                    display: false
                                },

                                ticks: {
                                    color: "#64748b",
                                    maxRotation: 45,
                                    minRotation: 0
                                },

                                border: {
                                    color: "#c8e0ec"
                                }
                            },

                            y: {
                                beginAtZero: true,

                                grid: {
                                    color: "#e8f1f5"
                                },

                                ticks: {
                                    color: "#64748b",

                                    callback: function (valor) {

                                        return "Bs. " +
                                            formato_bolivares.format(valor);
                                    }
                                },

                                border: {
                                    display: false
                                }
                            }
                        }
                    }
                }
            );

        } catch (error) {

            console.error(
                "Error al cargar la evolución de ventas:",
                error
            );
        }
    }

    // PRODUCTOS MÁS VENDIDOS
    async function cargar_productos_mas_vendidos() {

        const contenedor = document.querySelector(
            ".estadistica_equipos_entregados[data-url-grafica]"
        );

        const canvas = document.getElementById(
            "grafica_productos_mas_vendidos"
        );

        if (!contenedor || !canvas) {
            return;
        }

        try {

            const respuesta = await fetch(contenedor.dataset.urlGrafica, {
                method: "GET",
                headers: {
                    "X-Requested-With": "XMLHttpRequest"
                },
                credentials: "same-origin"
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            if (grafica_productos_mas_vendidos) {
                grafica_productos_mas_vendidos.destroy();
            }

            grafica_productos_mas_vendidos = new Chart(
                canvas,
                {
                    type: "bar",

                    data: {
                        labels: resultado.etiquetas,

                        datasets: [
                            {
                                label: "Cantidad vendida",

                                data: resultado.valores,

                                backgroundColor: [
                                    "#00779e",
                                    "#16835d",
                                    "#6854b8",
                                    "#d97706",
                                    "#2587ad",
                                    "#4c9b85",
                                    "#8b78c8",
                                    "#c18a3b",
                                    "#3b83a6",
                                    "#6995b2"
                                ],

                                borderRadius: 6,
                                borderSkipped: false,

                                maxBarThickness: 32
                            }
                        ]
                    },

                    options: {
                        indexAxis: "y",

                        responsive: true,
                        maintainAspectRatio: false,

                        plugins: {
                            legend: {
                                display: true,
                                position: "top",

                                labels: {
                                    color: "#102f4e",
                                    usePointStyle: true,
                                    padding: 18,
                                    font: {
                                        size: 12,
                                        weight: "600"
                                    }
                                }
                            },

                            tooltip: {
                                backgroundColor: "#102f4e",
                                titleColor: "#ffffff",
                                bodyColor: "#ffffff",
                                padding: 12,

                                callbacks: {
                                    label: function (context) {

                                        return "Cantidad vendida: " +
                                            new Intl.NumberFormat("es-VE", {
                                                maximumFractionDigits: 3
                                            }).format(context.parsed.x);
                                    }
                                }
                            }
                        },

                        scales: {
                            x: {
                                beginAtZero: true,

                                grid: {
                                    color: "#e8f1f5"
                                },

                                ticks: {
                                    color: "#64748b",
                                    precision: 0
                                },

                                border: {
                                    display: false
                                }
                            },

                            y: {
                                grid: {
                                    display: false
                                },

                                ticks: {
                                    color: "#102f4e",
                                    font: {
                                        size: 11,
                                        weight: "600"
                                    }
                                },

                                border: {
                                    color: "#c8e0ec"
                                }
                            }
                        }
                    }
                }
            );

        } catch (error) {

            console.error(
                "Error al cargar los productos más vendidos:",
                error
            );
        }
    }

    // INICIALIZAR GRÁFICAS
    async function inicializar_graficas_atencion_cliente() {

        await Promise.allSettled([
            cargar_evolucion_ventas(),
            cargar_productos_mas_vendidos()
        ]);

    }

    inicializar_graficas_atencion_cliente();

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