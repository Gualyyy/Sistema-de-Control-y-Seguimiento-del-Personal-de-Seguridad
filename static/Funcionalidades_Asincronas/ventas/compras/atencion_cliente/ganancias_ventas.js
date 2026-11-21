
document.addEventListener("DOMContentLoaded", () => {

    const modulo_ganancias = document.querySelector(
        ".modulo_ganancias_ventas"
    );

    if (!modulo_ganancias) return;

    const ingresos_netos = document.getElementById("ingresos_netos");
    const costo_mercancia = document.getElementById("costo_mercancia");
    const ganancia_ventas = document.getElementById("ganancia_ventas");

    const contenedor_evolucion_ganancias = document.getElementById(
        "evolucion_ganancias"
    );

    const contenedor_ganancias_producto = document.getElementById(
        "ganancias_producto"
    );

    const contenedor_ganancias_periodo = document.getElementById(
        "ganancias_por_periodo"
    );

    const botones_periodo = document.querySelectorAll(
        ".opciones_periodo_ganancias button"
    );

    const URLS = {
        resumen: modulo_ganancias.dataset.urlResumen,
        productos: modulo_ganancias.dataset.urlProductos,
        periodos: modulo_ganancias.dataset.urlPeriodos
    };

    let grafica_evolucion = null;
    let grafica_productos = null;
    let grafica_periodos = null;

    let periodo_actual = "semanal";
    let solicitud_periodo = 0;

    // ==========================================
    // CONFIGURACIÓN GENERAL
    // ==========================================

    const COLORES = {
        principal: "#00779e",
        secundario: "#00b6ea",
        ganancia: "#16845b",
        costo: "#78909c",
        texto: "#526779",
        textoSuave: "#8496a5",
        borde: "#e7eef3",
        fondo: "#ffffff"
    };

    // ==========================================
    // FORMATO MONETARIO EN BOLÍVARES
    // ==========================================

    const formato_moneda = new Intl.NumberFormat("es-VE", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });

    const formato_cantidad = new Intl.NumberFormat("es-VE", {
        maximumFractionDigits: 3
    });

    function formatoMoneda(valor) {

        return formato_moneda.format(
            Number(valor) || 0
        );
    }

    function formatoCantidad(valor) {

        return formato_cantidad.format(
            Number(valor) || 0
        );
    }

    function monedaCompleta(valor) {

        return "Bs. " + formatoMoneda(valor);
    }

    // ==========================================
    // ESCAPAR HTML
    // ==========================================

    function escaparHTML(valor) {

        return String(valor ?? "").replace(/[&<>"']/g, caracter => ({
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;"
        })[caracter]);
    }

    // ==========================================
    // FORMATEAR FECHAS
    // ==========================================

    function obtener_fecha_legible(fecha, periodo = null) {

        if (!fecha) return "";

        const valor = String(fecha);

        const partes = valor.includes("/")
            ? valor.split("/").reverse()
            : valor.split("-");

        const anio = Number(partes[0]);
        const mes = Number(partes[1] || 1);
        const dia = Number(partes[2] || 1);

        const fecha_local = new Date(anio, mes - 1, dia);

        if (periodo === "anual") {
            return String(anio);
        }

        if (periodo === "mensual") {

            return fecha_local.toLocaleDateString("es-VE", {
                month: "short",
                year: "numeric"
            });
        }

        return fecha_local.toLocaleDateString("es-VE", {
            day: "2-digit",
            month: "short"
        });
    }

    // ==========================================
    // DESTRUIR GRÁFICAS
    // ==========================================

    function destruir_grafica(grafica) {

        if (grafica) {
            grafica.destroy();
        }

        return null;
    }

    // ==========================================
    // MENSAJES
    // ==========================================

    function mostrar_sin_registros(contenedor, mensaje) {

        if (!contenedor) return;

        contenedor.innerHTML = `
            <div class="mensaje_sin_registros">
                <i class="fa-solid fa-chart-simple"></i>
                <span>${mensaje}</span>
            </div>
        `;
    }

    function mostrar_cargando(contenedor) {

        if (!contenedor) return;

        contenedor.innerHTML = `
            <div class="mensaje_sin_registros">
                <i class="fa-solid fa-spinner fa-spin"></i>
                <span>Procesando información financiera...</span>
            </div>
        `;
    }

    // ==========================================
    // SOLICITUDES AJAX
    // ==========================================

    async function solicitar_datos(url, datos = {}) {

        if (!url) {
            throw new Error(
                "No se encontró la dirección del servicio solicitado."
            );
        }

        const cookie_csrf = document.cookie
            .split("; ")
            .find(cookie => cookie.startsWith("csrftoken="));

        const token_csrf = cookie_csrf
            ? decodeURIComponent(
                cookie_csrf.substring("csrftoken=".length)
            )
            : "";

        if (!token_csrf) {

            throw new Error(
                "No se encontró el token de seguridad CSRF."
            );
        }

        const respuesta = await fetch(url, {

            method: "POST",

            headers: {
                "X-Requested-With": "XMLHttpRequest",
                "X-CSRFToken": token_csrf,
                "Content-Type": "application/x-www-form-urlencoded"
            },

            body: new URLSearchParams(datos)
        });

        let resultado;

        try {

            resultado = await respuesta.json();

        } catch {

            throw new Error(
                "El servidor devolvió una respuesta inválida."
            );
        }

        if (!respuesta.ok || resultado.estado !== "exito") {

            throw new Error(
                resultado.descripcion ||
                resultado.title ||
                "No se pudo obtener la información."
            );
        }

        return resultado;
    }

    // ==========================================
    // OPCIONES BASE DE APEXCHARTS
    // ==========================================

    function opciones_base() {

        return {

            chart: {
                fontFamily: "inherit",
                foreColor: COLORES.texto,
                background: "transparent",

                toolbar: {
                    show: true,

                    tools: {
                        download: true,
                        selection: false,
                        zoom: false,
                        zoomin: false,
                        zoomout: false,
                        pan: false,
                        reset: false
                    }
                },

                animations: {
                    enabled: true,
                    easing: "easeinout",
                    speed: 650,

                    animateGradually: {
                        enabled: true,
                        delay: 100
                    }
                }
            },

            grid: {
                borderColor: COLORES.borde,
                strokeDashArray: 4,

                padding: {
                    left: 8,
                    right: 12,
                    top: 5,
                    bottom: 0
                }
            },

            dataLabels: {
                enabled: false
            },

            tooltip: {
                theme: "light",

                style: {
                    fontSize: "12px"
                }
            },

            noData: {
                text: "No hay información disponible.",
                align: "center",
                verticalAlign: "middle",

                style: {
                    color: COLORES.textoSuave,
                    fontSize: "13px"
                }
            },

            responsive: [{
                breakpoint: 650,

                options: {

                    chart: {
                        toolbar: {
                            show: false
                        }
                    },

                    legend: {
                        position: "bottom",
                        horizontalAlign: "center"
                    }
                }
            }]
        };
    }

    // ==========================================
    // ACTUALIZAR INDICADORES FINANCIEROS
    // ==========================================

    function actualizar_estadisticas(datos) {

        if (ingresos_netos) {

            ingresos_netos.textContent = monedaCompleta(
                datos.ingresos_neto
            );
        }

        if (costo_mercancia) {

            costo_mercancia.textContent = monedaCompleta(
                datos.costo_mercancia
            );
        }

        if (ganancia_ventas) {

            ganancia_ventas.textContent = monedaCompleta(
                datos.ganancia
            );
        }
    }

    // ==========================================
    // EVOLUCIÓN FINANCIERA
    // ==========================================

    function generar_grafica_evolucion(datos) {

        grafica_evolucion = destruir_grafica(
            grafica_evolucion
        );

        if (!datos.length) {

            mostrar_sin_registros(
                contenedor_evolucion_ganancias,
                "No hay movimientos financieros en este período."
            );

            return;
        }

        contenedor_evolucion_ganancias.innerHTML = "";

        const series = [

            {
                name: "Ingresos netos",

                data: datos.map(item =>
                    Number(item.ingresos) || 0
                )
            },

            {
                name: "Costo de mercancía",

                data: datos.map(item =>
                    Number(item.costos) || 0
                )
            },

            {
                name: "Ganancia de ventas",

                data: datos.map(item =>
                    Number(item.ganancia) || 0
                )
            }
        ];

        const opciones = {

            ...opciones_base(),

            series: series,

            chart: {
                ...opciones_base().chart,
                type: "area",
                height: 360
            },

            colors: [
                COLORES.principal,
                COLORES.costo,
                COLORES.ganancia
            ],

            stroke: {
                curve: "smooth",
                width: [3, 2, 3],
                lineCap: "round"
            },

            fill: {

                type: "gradient",

                gradient: {
                    shadeIntensity: 0.5,
                    opacityFrom: 0.30,
                    opacityTo: 0.04,
                    stops: [0, 90, 100]
                }
            },

            markers: {

                size: 3,
                strokeWidth: 2,

                hover: {
                    size: 6
                }
            },

            xaxis: {

                categories: datos.map(item =>
                    obtener_fecha_legible(item.fecha)
                ),

                labels: {

                    rotate: -35,
                    hideOverlappingLabels: true,

                    style: {
                        fontSize: "11px",
                        colors: COLORES.textoSuave
                    }
                },

                axisBorder: {
                    show: false
                },

                axisTicks: {
                    show: false
                }
            },

            yaxis: {

                labels: {

                    formatter: valor =>
                        monedaCompleta(valor),

                    style: {
                        fontSize: "11px",
                        colors: COLORES.textoSuave
                    }
                }
            },

            legend: {

                position: "top",
                horizontalAlign: "left",
                fontSize: "12px",

                markers: {
                    radius: 12
                },

                itemMargin: {
                    horizontal: 12,
                    vertical: 5
                }
            },

            tooltip: {

                ...opciones_base().tooltip,

                shared: true,
                intersect: false,

                y: {
                    formatter: valor =>
                        monedaCompleta(valor)
                }
            }
        };

        grafica_evolucion = new ApexCharts(
            contenedor_evolucion_ganancias,
            opciones
        );

        grafica_evolucion.render();
    }

    // ==========================================
    // RENTABILIDAD POR PRODUCTO
    // ==========================================

    function generar_grafica_productos(datos) {

        grafica_productos = destruir_grafica(
            grafica_productos
        );

        if (!datos.length) {

            mostrar_sin_registros(
                contenedor_ganancias_producto,
                "No hay productos vendidos en el período seleccionado."
            );

            return;
        }

        contenedor_ganancias_producto.innerHTML = "";

        // ORDENAR PRODUCTOS POR GANANCIA EN BOLÍVARES

        const productos = [...datos].sort(
            (a, b) => Number(b.ganancia) - Number(a.ganancia)
        );

        const altura = Math.max(
            340,
            productos.length * 48
        );

        // FORMATO MONETARIO PARA EL TOOLTIP

        const mostrar_monedas = monto => {

            return `
                <strong style="
                    color: #102f4e;
                    font-size: 12px;
                    white-space: nowrap;
                ">
                    ${monedaCompleta(monto)}
                </strong>
            `;
        };

        const opciones = {

            ...opciones_base(),

            series: [{

                name: "Ganancia",

                data: productos.map(item =>
                    Number(item.ganancia) || 0
                )
            }],

            chart: {
                ...opciones_base().chart,
                type: "bar",
                height: altura
            },

            colors: [
                COLORES.ganancia
            ],

            plotOptions: {

                bar: {

                    horizontal: true,
                    borderRadius: 5,
                    borderRadiusApplication: "end",
                    barHeight: "58%",
                    distributed: false
                }
            },

            xaxis: {

                categories: productos.map(item =>
                    item.nombre
                ),

                labels: {

                    formatter: valor =>
                        monedaCompleta(valor),

                    style: {
                        fontSize: "11px",
                        colors: COLORES.textoSuave
                    }
                },

                axisBorder: {
                    show: false
                },

                axisTicks: {
                    show: false
                }
            },

            yaxis: {

                labels: {

                    maxWidth: 180,

                    style: {
                        fontSize: "12px",
                        colors: COLORES.texto
                    }
                }
            },

            dataLabels: {

                enabled: true,

                formatter: valor =>
                    monedaCompleta(valor),

                textAnchor: "start",

                offsetX: 8,

                style: {
                    fontSize: "11px",
                    fontWeight: 600,
                    colors: ["#ffffff"]
                }
            },

            grid: {

                ...opciones_base().grid,

                padding: {
                    left: 8,
                    right: 35
                }
            },

            tooltip: {

                ...opciones_base().tooltip,

                custom: ({ dataPointIndex }) => {

                    const producto = productos[dataPointIndex];

                    if (!producto) return "";

                    return `

                        <div style="
                            padding: 14px 16px;
                            min-width: 245px;
                            font-family: inherit;
                        ">

                            <div style="
                                font-weight: 700;
                                color: #102f4e;
                                font-size: 13px;
                                margin-bottom: 12px;
                                padding-bottom: 9px;
                                border-bottom: 1px solid #e2e8f0;
                            ">
                                ${escaparHTML(producto.nombre)}
                            </div>

                            <div style="
                                display: flex;
                                justify-content: space-between;
                                align-items: center;
                                gap: 15px;
                                margin-bottom: 10px;
                            ">
                                <span>Ingresos:</span>

                                ${mostrar_monedas(producto.ingresos)}
                            </div>

                            <div style="
                                display: flex;
                                justify-content: space-between;
                                align-items: center;
                                gap: 15px;
                                margin-bottom: 10px;
                            ">
                                <span>Costo:</span>

                                ${mostrar_monedas(producto.costo_total)}
                            </div>

                            <div style="
                                display: flex;
                                justify-content: space-between;
                                align-items: center;
                                gap: 15px;
                                margin-bottom: 10px;
                                padding-top: 9px;
                                border-top: 1px solid #e2e8f0;
                            ">

                                <span style="
                                    color: #16845b;
                                    font-weight: 600;
                                ">
                                    Ganancia:
                                </span>

                                ${mostrar_monedas(producto.ganancia)}
                            </div>

                            <div style="
                                display: flex;
                                justify-content: space-between;
                                gap: 15px;
                                margin-bottom: 9px;
                            ">
                                <span>Margen:</span>

                                <strong>
                                    ${formatoMoneda(producto.margen)}%
                                </strong>
                            </div>

                            <div style="
                                display: flex;
                                justify-content: space-between;
                                gap: 15px;
                            ">
                                <span>Cantidad:</span>

                                <strong>
                                    ${formatoCantidad(producto.cantidad_vendida)}
                                </strong>
                            </div>

                        </div>
                    `;
                }
            }
        };

        grafica_productos = new ApexCharts(
            contenedor_ganancias_producto,
            opciones
        );

        grafica_productos.render();
    }

    // ==========================================
    // GANANCIAS POR PERÍODO
    // ==========================================

    async function cargar_ganancias_periodo(periodo) {

        const numero_solicitud = ++solicitud_periodo;

        mostrar_cargando(
            contenedor_ganancias_periodo
        );

        try {

            const resultado = await solicitar_datos(
                URLS.periodos,
                { periodo }
            );

            if (numero_solicitud !== solicitud_periodo) {
                return;
            }

            generar_grafica_periodos(
                resultado.datos || [],
                periodo
            );

        } catch (error) {

            if (numero_solicitud !== solicitud_periodo) {
                return;
            }

            console.error(
                "Error al consultar ganancias por período:",
                error
            );

            grafica_periodos = destruir_grafica(
                grafica_periodos
            );

            mostrar_sin_registros(
                contenedor_ganancias_periodo,
                "No se pudieron cargar las ganancias por período."
            );
        }
    }

    function generar_grafica_periodos(datos, periodo) {

        grafica_periodos = destruir_grafica(
            grafica_periodos
        );

        if (!datos.length) {

            mostrar_sin_registros(
                contenedor_ganancias_periodo,
                "No hay información financiera para este período."
            );

            return;
        }

        contenedor_ganancias_periodo.innerHTML = "";

        const opciones = {

            ...opciones_base(),

            series: [

                {
                    name: "Ingresos netos",

                    data: datos.map(item =>
                        Number(item.ingresos) || 0
                    )
                },

                {
                    name: "Costo de mercancía",

                    data: datos.map(item =>
                        Number(item.costo_ventas) || 0
                    )
                },

                {
                    name: "Ganancia de ventas",

                    data: datos.map(item =>
                        Number(item.ganancia) || 0
                    )
                }
            ],

            chart: {
                ...opciones_base().chart,
                type: "bar",
                height: 365
            },

            colors: [
                COLORES.principal,
                COLORES.costo,
                COLORES.ganancia
            ],

            plotOptions: {

                bar: {

                    horizontal: false,
                    columnWidth: "48%",
                    borderRadius: 5,
                    borderRadiusApplication: "end"
                }
            },

            xaxis: {

                categories: datos.map(item =>
                    obtener_fecha_legible(item.fecha, periodo)
                ),

                labels: {

                    rotate: -35,
                    hideOverlappingLabels: true,

                    style: {
                        fontSize: "11px",
                        colors: COLORES.textoSuave
                    }
                },

                axisBorder: {
                    show: false
                },

                axisTicks: {
                    show: false
                }
            },

            yaxis: {

                labels: {

                    formatter: valor =>
                        monedaCompleta(valor),

                    style: {
                        fontSize: "11px",
                        colors: COLORES.textoSuave
                    }
                }
            },

            legend: {

                position: "top",
                horizontalAlign: "left",
                fontSize: "12px",

                markers: {
                    radius: 12
                }
            },

            tooltip: {

                shared: true,
                intersect: false,
                followCursor: true,
                theme: "light",

                y: {

                    formatter: valor =>
                        monedaCompleta(valor)
                }
            },

            responsive: [{

                breakpoint: 650,

                options: {

                    chart: {

                        height: 380,

                        toolbar: {
                            show: false
                        }
                    },

                    plotOptions: {

                        bar: {
                            columnWidth: "65%"
                        }
                    },

                    legend: {

                        position: "bottom",
                        horizontalAlign: "center"
                    }
                }
            }]
        };

        grafica_periodos = new ApexCharts(
            contenedor_ganancias_periodo,
            opciones
        );

        grafica_periodos.render();
    }

    // ==========================================
    // CARGAR RESUMEN GENERAL
    // ==========================================

    async function cargar_resumen_ganancias() {

        mostrar_cargando(
            contenedor_evolucion_ganancias
        );

        try {

            const resultado = await solicitar_datos(
                URLS.resumen
            );

            const datos = resultado.datos || {};

            actualizar_estadisticas(datos);

            generar_grafica_evolucion(
                datos.estadistica_grafica || []
            );

        } catch (error) {

            console.error(
                "Error al cargar el resumen financiero:",
                error
            );

            mostrar_sin_registros(
                contenedor_evolucion_ganancias,
                "No se pudo cargar la evolución financiera."
            );
        }
    }

    // ==========================================
    // CARGAR RENTABILIDAD POR PRODUCTO
    // ==========================================

    async function cargar_ganancias_producto() {

        mostrar_cargando(
            contenedor_ganancias_producto
        );

        try {

            const resultado = await solicitar_datos(
                URLS.productos
            );

            generar_grafica_productos(
                resultado.datos?.productos || []
            );

        } catch (error) {

            console.error(
                "Error al cargar ganancias por producto:",
                error
            );

            mostrar_sin_registros(
                contenedor_ganancias_producto,
                "No se pudo cargar la rentabilidad por producto."
            );
        }
    }

    // ==========================================
    // CAMBIAR PERÍODO
    // ==========================================

    async function cambiar_periodo(periodo, boton) {

        if (periodo === periodo_actual) return;

        if (
            !["semanal", "mensual", "anual"].includes(periodo)
        ) {
            return;
        }

        periodo_actual = periodo;

        botones_periodo.forEach(elemento => {
            elemento.classList.remove("activo");
        });

        boton.classList.add("activo");

        await cargar_ganancias_periodo(periodo);
    }

    // ==========================================
    // INICIALIZACIÓN
    // ==========================================

    async function inicializar_estadisticas() {

        if (typeof ApexCharts === "undefined") {

            console.error(
                "ApexCharts no está cargado."
            );

            mostrar_sin_registros(
                contenedor_evolucion_ganancias,
                "No se encuentra disponible el motor de gráficas."
            );

            mostrar_sin_registros(
                contenedor_ganancias_producto,
                "No se encuentra disponible el motor de gráficas."
            );

            mostrar_sin_registros(
                contenedor_ganancias_periodo,
                "No se encuentra disponible el motor de gráficas."
            );

            return;
        }

        await Promise.allSettled([

            cargar_resumen_ganancias(),

            cargar_ganancias_producto(),

            cargar_ganancias_periodo(periodo_actual)

        ]);
    }

    // ==========================================
    // EVENTOS
    // ==========================================

    botones_periodo.forEach(boton => {

        boton.addEventListener("click", async () => {

            const periodo = boton.dataset.periodo;

            await cambiar_periodo(
                periodo,
                boton
            );
        });
    });

    // ==========================================
    // EJECUTAR MÓDULO
    // ==========================================

    inicializar_estadisticas();

});
