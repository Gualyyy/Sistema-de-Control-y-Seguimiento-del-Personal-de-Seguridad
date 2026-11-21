document.addEventListener("DOMContentLoaded", () => {

    const estado = document.getElementById("ultimo_inicio_estado");
    const fecha = document.getElementById("ultimo_inicio_fecha");
    const cierre = document.getElementById("ultimo_inicio_cierre");
    const ip = document.getElementById("ultimo_inicio_ip");
    const dispositivo = document.getElementById("ultimo_inicio_dispositivo");
    const mensaje = document.getElementById("ultimo_inicio_mensaje");
    const titulo = document.getElementById("ultimo_inicio_titulo");

    /* VARIABLES DE TASAS */
    let tasa_dolar = 0;
    let tasa_euro = 0;

    let fecha_tasa_dolar = null;
    let fecha_tasa_euro = null;

    /* REGISTROS DEL SISTEMA DEL CLIENTE */
    async function registros_sistema() {

        const contenedor = document.querySelector(
            ".contenedor_panel_usuario"
        );

        if (!contenedor) return;

        const url = contenedor.dataset.urlRegistros;

        if (!url) {
            console.error("No se encontró la URL de los registros del cliente.");
            return;
        }

        const contadores = contenedor.querySelectorAll(
            ".numero_contador[data-campo]"
        );

        const formato_cantidad = new Intl.NumberFormat("es-VE", {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        });

        function formatear_valor(valor) {

            return formato_cantidad.format(valor);

        }

        function animar_contador(contador, valor) {

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
                    valor_actual
                );

                if (progreso < 1) {

                    requestAnimationFrame(animar);

                } else {

                    contador.textContent = formatear_valor(
                        valor
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
                },
                credentials: "same-origin"
            });
            const resultado = await respuesta.json();
            console.log("Registros del cliente:", resultado);

            if (!respuesta.ok || resultado.estado !== "exito") {

                throw new Error(
                    resultado.descripcion ||
                    "No fue posible obtener los registros del cliente."
                );

            }

            contadores.forEach((contador) => {
                const campo = contador.dataset.campo;
                const valor = Number(resultado[campo] ?? 0);

                if (!Number.isFinite(valor)) {
                    contador.textContent = formatear_valor(0);
                    return;
                }

                contador.dataset.total = valor;
                animar_contador(contador, valor);
            });
        } catch (error) {
            console.error("Error al cargar los registros del cliente:", error);
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

    let grafica_productos_mas_comprados = null;

    async function cargar_productos_mas_comprados() {

        const contenedor = document.querySelector(
            ".estadistica_equipos_entregados[data-url-grafica]"
        );

        const canvas = document.getElementById(
            "grafica_productos_mas_comprados"
        );

        if (!contenedor || !canvas) {

            console.error(
                "No se encontró el contenedor o canvas de productos más comprados."
            );

            return;
        }

        const url = contenedor.dataset.urlGrafica;

        if (!url) {

            console.error(
                "No se encontró la URL de la estadística de productos."
            );

            return;
        }

        try {

            const respuesta = await fetch(url, {

                method: "GET",

                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                    "Accept": "application/json"
                },

                credentials: "same-origin"

            });

            const contentType = respuesta.headers.get("content-type");

            if (!contentType || !contentType.includes("application/json")) {

                const contenido = await respuesta.text();

                console.error(
                    "Respuesta recibida del servidor:",
                    {
                        status: respuesta.status,
                        contentType: contentType,
                        contenido: contenido.substring(0, 500)
                    }
                );

                throw new Error(
                    "El servidor no devolvió una respuesta JSON."
                );
            }

            const datos = await respuesta.json();

            console.log(
                "Respuesta de productos más comprados:",
                datos
            );

            if (!respuesta.ok || datos.estado !== "exito") {

                throw new Error(
                    datos.descripcion ||
                    "No fue posible obtener los productos más comprados."
                );
            }

            if (!Array.isArray(datos.productos)) {

                console.error(
                    "La propiedad productos no contiene un arreglo:",
                    datos.productos
                );

                throw new Error(
                    "La información recibida de los productos tiene un formato incorrecto."
                );
            }

            generar_grafica_productos_mas_comprados(
                canvas,
                datos.productos
            );

        } catch (error) {

            console.error(
                "Error al cargar productos más comprados:",
                error
            );

            if (grafica_productos_mas_comprados) {

                grafica_productos_mas_comprados.destroy();

                grafica_productos_mas_comprados = null;
            }
        }
    }

    function generar_grafica_productos_mas_comprados(canvas, productos) {

        if (grafica_productos_mas_comprados) {

            grafica_productos_mas_comprados.destroy();

            grafica_productos_mas_comprados = null;
        }

        const contexto = canvas.getContext("2d");

        if (!contexto) {

            console.error(
                "No fue posible obtener el contexto del canvas."
            );

            return;
        }

        /* ==========================================
           VALIDAR PRODUCTOS
        ========================================== */

        if (!Array.isArray(productos)) {

            console.error(
                "Los productos recibidos no son un arreglo:",
                productos
            );

            productos = [];
        }

        /* ==========================================
           GRÁFICA SIN REGISTROS
        ========================================== */

        if (productos.length === 0) {

            console.info(
                "No existen productos vendidos para mostrar."
            );

            grafica_productos_mas_comprados = new Chart(contexto, {

                type: "bar",

                data: {

                    labels: ["Sin registros"],

                    datasets: [{

                        label: "Cantidad vendida",

                        data: [0],

                        backgroundColor: "#b9dce8",

                        borderColor: "#00779e",

                        borderWidth: 1,

                        borderRadius: 7
                    }]
                },

                options: {

                    indexAxis: "y",

                    responsive: true,

                    maintainAspectRatio: false,

                    plugins: {

                        legend: {
                            display: false
                        },

                        tooltip: {
                            enabled: false
                        }
                    },

                    scales: {

                        x: {
                            display: false,
                            beginAtZero: true
                        },

                        y: {
                            grid: {
                                display: false
                            },

                            ticks: {
                                color: "#102f4e"
                            }
                        }
                    }
                }
            });

            return;
        }


        /* ==========================================
           PREPARAR INFORMACIÓN
        ========================================== */

        const productos_validos = productos.filter(producto => {

            return producto &&
                typeof producto === "object" &&
                Number.isFinite(Number(producto.cantidad_vendida));
        });

        if (productos_validos.length === 0) {

            console.info(
                "No existen cantidades válidas para representar."
            );

            generar_grafica_productos_mas_comprados(
                canvas,
                []
            );

            return;
        }

        const nombres = productos_validos.map(producto =>
            producto.nombre || "Producto sin nombre"
        );

        const cantidades = productos_validos.map(producto =>
            Number(producto.cantidad_vendida) || 0
        );

        const unidades = productos_validos.map(producto =>
            producto.abreviatura || ""
        );


        /* ==========================================
           COLORES DE LAS BARRAS
        ========================================== */

        const colores = productos_validos.map((producto, indice) => {

            if (indice === 0) return "#00779e";

            if (indice === 1) return "#009bc4";

            if (indice === 2) return "#00b6ea";

            return "#75cce5";
        });


        /* ==========================================
           CREAR GRÁFICA
        ========================================== */

        grafica_productos_mas_comprados = new Chart(contexto, {

            type: "bar",

            data: {

                labels: nombres,

                datasets: [{

                    label: "Cantidad vendida",

                    data: cantidades,

                    backgroundColor: colores,

                    borderColor: "#00445f",

                    borderWidth: 1,

                    borderRadius: 7,

                    borderSkipped: false,

                    barThickness: 25,

                    maxBarThickness: 30
                }]
            },

            options: {

                indexAxis: "y",

                responsive: true,

                maintainAspectRatio: false,

                animation: {
                    duration: 900
                },

                layout: {

                    padding: {

                        right: 25,

                        left: 5,

                        top: 5,

                        bottom: 5
                    }
                },

                plugins: {

                    legend: {
                        display: false
                    },

                    tooltip: {

                        backgroundColor: "#102f4e",

                        titleColor: "#ffffff",

                        bodyColor: "#ffffff",

                        padding: 12,

                        cornerRadius: 7,

                        displayColors: true,

                        callbacks: {

                            label: function (contexto) {

                                const indice = contexto.dataIndex;

                                const cantidad = contexto.parsed.x;

                                const unidad = unidades[indice];

                                return ` ${cantidad.toLocaleString("es-VE")} ${unidad}`;
                            },


                            afterLabel: function (contexto) {

                                const producto = productos_validos[
                                    contexto.dataIndex
                                ];

                                const ingresos_usd = Number(
                                    producto.ingresos_totales
                                ) || 0;

                                const ingresos_bs = tasa_dolar > 0
                                    ? ingresos_usd * tasa_dolar
                                    : null;

                                const informacion = [

                                    `Código: ${producto.codigo || "No disponible"}`,

                                    `Categoría: ${producto.categoria || "No disponible"}`,

                                    `Ventas: ${producto.total_ventas || 0}`,

                                    `Ingresos USD: $${ingresos_usd.toLocaleString("es-VE", {
                                        minimumFractionDigits: 2,
                                        maximumFractionDigits: 2
                                    })}`
                                ];

                                if (ingresos_bs !== null) {

                                    informacion.push(
                                        `Ingresos Bs: Bs. ${formato_bolivares.format(ingresos_bs)}`
                                    );

                                    informacion.push(
                                        `Tasa aplicada: Bs. ${formato_bolivares.format(tasa_dolar)} por USD`
                                    );

                                } else {

                                    informacion.push(
                                        "Conversión a bolívares: Tasa no disponible"
                                    );
                                }

                                return informacion;
                            }

                        }
                    }
                },

                scales: {

                    x: {

                        beginAtZero: true,

                        title: {

                            display: true,

                            text: "Cantidad de productos vendidos",

                            color: "#102f4e",

                            font: {

                                size: 12,

                                weight: "bold"
                            }
                        },

                        ticks: {

                            color: "#526b7c",

                            precision: 0
                        },

                        grid: {

                            color: "rgba(0, 68, 95, 0.10)"
                        }
                    },

                    y: {

                        ticks: {

                            color: "#102f4e",

                            font: {

                                size: 11,

                                weight: "600"
                            }
                        },

                        grid: {

                            display: false
                        }
                    }
                }
            }
        });
    }
    cargar_productos_mas_comprados();

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