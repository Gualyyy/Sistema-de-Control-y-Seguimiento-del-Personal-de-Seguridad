document.addEventListener("DOMContentLoaded", () => {

    const contenedor_productos_disponibles = document.getElementById("productos_disponibles");

    const btn_moneda = document.getElementById("btn_moneda");
    const opciones_monedas = document.getElementById("opciones_monedas");
    const input_moneda = document.getElementById("moneda_seleccionada");

    const input_tasa_monetaria = document.getElementById("tasa_monetaria");
    const input_fecha_tasa = document.getElementById("fecha_tasa");

    const moneda_seleccionada = btn_moneda.querySelector(".moneda_seleccionada");

    const imagen_seleccionada = moneda_seleccionada?.querySelector("img");
    const codigo_seleccionado = moneda_seleccionada?.querySelector("strong");
    const nombre_seleccionado = moneda_seleccionada?.querySelector("small");

    const opciones = opciones_monedas.querySelectorAll("button[data-moneda]");

    const btn_acceso_cliente = document.getElementById("btn_acceso_cliente");
    const dialogo_cliente = document.getElementById("dialogo_cliente");
    const btn_cerrar = document.getElementById("btn_cerrar");

    const input_buscar_producto = document.getElementById("buscar_producto");

    let tasa_dolar = null;
    let tasa_euro = null;

    let fecha_tasa_dolar = null;
    let fecha_tasa_euro = null;

    let moneda_actual = "USD";

    /* ABRIR Y CERRAR EL SELECTOR */
    function abrir_opciones() {
        opciones_monedas.hidden = false;
        btn_moneda.setAttribute("aria-expanded", "true");
    }

    function cerrar_opciones() {
        opciones_monedas.hidden = true;
        btn_moneda.setAttribute("aria-expanded", "false");
    }

    btn_moneda.addEventListener("click", function () {
        if (opciones_monedas.hidden) {
            abrir_opciones();
        } else {
            cerrar_opciones();
        }
    });

    /* SELECCIONAR MONEDA */
    opciones.forEach(function (e) {
        e.addEventListener("click", async function () {
            const codigo = this.dataset.moneda;
            const nombre = this.dataset.nombre;
            const bandera = this.querySelector("img");

            if (!codigo || !nombre || !bandera) {
                return;
            }

            imagen_seleccionada.src = bandera.src;
            imagen_seleccionada.alt = bandera.alt;

            codigo_seleccionado.textContent = codigo;
            nombre_seleccionado.textContent = nombre;

            input_moneda.value = codigo;
            moneda_actual = codigo;

            cerrar_opciones();

            console.log("Moneda seleccionada:", codigo);

            try {
                if (codigo === "USD" || codigo === "VES") {
                    if (tasa_dolar === null) {
                        await tasa_oficial_dolar();
                    }
                }

                if (codigo === "EUR") {
                    if (tasa_euro === null) {
                        await tasa_oficial_euro();
                    }
                }

                mostrar_tasa();
                actualizar_precios();
            } catch (error) {
                console.error("Error al obtener las tasas:", error);
            }
        });
    });

    /* CERRAR AL HACER CLIC FUERA */
    document.addEventListener("click", function (e) {
        if (!e.target.closest(".selector_moneda")) {
            cerrar_opciones();
        }
    });

    /* CERRAR CON ESCAPE */
    document.addEventListener("keydown", function (e) {
        if (e.key === "Escape" && !opciones_monedas.hidden) {
            cerrar_opciones();
            btn_moneda.focus();
        }
    });

    /* CONSULTAR TASA OFICIAL DEL DÓLAR */
    async function tasa_oficial_dolar() {
        try {
            const respuesta = await fetch(
                "https://ve.dolarapi.com/v1/dolares/oficial"
            );

            const resultado = await respuesta.json();

            console.log("Datos del dólar:", resultado);

            const tasa = Number(resultado.promedio);

            tasa_dolar = Number(tasa.toFixed(2));

            fecha_tasa_dolar = resultado.fechaActualizacion || null;

        } catch (error) {
            console.error("Error al consultar el dólar:", error);
        }
    }

    /* CONSULTAR TASA OFICIAL DEL EURO */
    async function tasa_oficial_euro() {
        try {
            const respuesta = await fetch(
                "https://ve.dolarapi.com/v1/euros/oficial"
            );

            const resultado = await respuesta.json();

            console.log("Datos del euro:", resultado);

            const tasa = Number(resultado.promedio);

            tasa_euro = Number(tasa.toFixed(2));

            fecha_tasa_euro = resultado.fechaActualizacion || null;

        } catch (error) {
            console.error("Error al consultar el euro:", error);
        }
    }

    /* CONVERTIR PRECIOS */
    function convertir_precio(precio_usd, moneda) {
        if (moneda === "USD") {
            return precio_usd;
        }

        if (moneda === "VES" && tasa_dolar !== null) {
            return precio_usd * tasa_dolar;
        }

        if (moneda === "EUR" && tasa_dolar !== null && tasa_euro !== null) {
            return (precio_usd * tasa_dolar) / tasa_euro;
        }

        return null;
    }

    /* MOSTRAR TASA MONETARIA Y FECHA */
    function mostrar_tasa() {
        let tasa = null;
        let fecha = null;

        if (moneda_actual === "USD") {
            input_tasa_monetaria.value = "Precio por defecto";
            input_fecha_tasa.value = "No aplica";
            return;
        }

        if (moneda_actual === "VES") {
            tasa = tasa_dolar;
            fecha = fecha_tasa_dolar;
        } else if (moneda_actual === "EUR") {
            tasa = tasa_euro;
            fecha = fecha_tasa_euro;
        }

        input_tasa_monetaria.value = tasa !== null
            ? `${tasa.toLocaleString("es-VE", {
                minimumFractionDigits: 2,
                maximumFractionDigits: 4
            })} Bs.`
            : "No disponible";

        if (fecha) {
            const fecha_formateada = new Date(fecha);

            input_fecha_tasa.value = !Number.isNaN(fecha_formateada.getTime())
                ? fecha_formateada.toLocaleDateString("es-VE", {
                    day: "2-digit",
                    month: "2-digit",
                    year: "numeric",
                    timeZone: "UTC"
                })
                : fecha;
        } else {
            input_fecha_tasa.value = "No disponible";
        }
    }

    /* ACTUALIZAR PRECIOS DE LOS PRODUCTOS */
    function actualizar_precios() {
        document.querySelectorAll(".carta_producto").forEach(function (carta) {
            const elemento_precio = carta.querySelector(".precio_producto");

            if (!elemento_precio) {
                return;
            }

            const precio_usd = Number(elemento_precio.dataset.precioUsd);

            if (!Number.isFinite(precio_usd)) {
                elemento_precio.textContent = "Precio no disponible";
                return;
            }

            const precio_convertido = convertir_precio(
                precio_usd,
                moneda_actual
            );

            if (precio_convertido === null) {
                elemento_precio.textContent = "Precio no disponible";
                return;
            }

            const formatos = {
                USD: {
                    locale: "en-US",
                    currency: "USD"
                },
                VES: {
                    locale: "es-VE",
                    currency: "VES"
                },
                EUR: {
                    locale: "es-ES",
                    currency: "EUR"
                }
            };

            const formato = formatos[moneda_actual];

            elemento_precio.textContent = new Intl.NumberFormat(
                formato.locale,
                {
                    style: "currency",
                    currency: formato.currency,
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                }
            ).format(precio_convertido);
        });
    }

    /* CARGA INICIAL */
    async function inicializar_monedas() {
        try {
            await tasa_oficial_dolar();

            mostrar_tasa();
            actualizar_precios();

        } catch (error) {
            mostrar_tasa();
            actualizar_precios();

            console.error("No se pudieron cargar las tasas iniciales:", error);
        }
    }
    inicializar_monedas();

    /* BUSCAR PRODUCTOS REGISTRADOS DESDE EL FORO */
    input_buscar_producto.addEventListener("input", async () => {
        await productos();
    });

    /* PRODUCTOS REGISTRADOS Y CON DISPONIBILIDAD EN INVENTARIO */
    async function productos() {
        try {
            const formulario = new FormData();
            formulario.append("producto", input_buscar_producto.value.trim());

            const respuesta = await fetch("/ventas/productos_exhibicion/", {
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

            contenedor_productos_disponibles.innerHTML = "";

            if (!resultado.productos || resultado.productos.length === 0) {
                contenedor_productos_disponibles.innerHTML = `
                    <p class="mensaje_sin_productos">
                        No se encontraron productos disponibles.
                    </p>
                `;
                return;
            }

            resultado.productos.forEach(producto => {
                const carta = document.createElement("article");
                carta.className = "carta_producto";

                const imagen = producto.imagen
                    ? producto.imagen
                    : "/static/Imagenes/producto_sin_imagen.png";

                carta.innerHTML = `
                    <div class="imagen_producto">
                        <img src="${imagen}" alt="${producto.nombre}" loading="lazy" onerror="this.onerror=null; this.src='/static/Imagenes/producto_sin_imagen.png';">
                    </div>

                    <div class="informacion_producto">
                        <h3 class="nombre_producto">
                            ${producto.nombre}
                        </h3>

                        <p class="codigo_producto">
                            Código: <span>${producto.codigo}</span>
                        </p>

                        <p class="precio_producto"  data-precio-usd="${Number(producto.precio_base)}">
                            $${Number(producto.precio_base).toFixed(2)}
                        </p>

                        <div class="detalles_producto">
                            <span>
                                <i class="fa-solid fa-boxes-stacked"></i>
                                Existencia: ${producto.cantidad_actual ?? 0}
                            </span>

                            <span>
                                <i class="fa-solid fa-weight-hanging"></i>
                                ${producto.unidad} (${producto.abreviatura})
                            </span>
                        </div>
                    </div>
                `;

                contenedor_productos_disponibles.appendChild(carta);
            });

            actualizar_precios();

        } catch (error) {
            console.error(error);

            contenedor_productos_disponibles.innerHTML = `
                <p class="mensaje_sin_productos">
                    Ocurrió un error al cargar los productos disponibles.
                </p>
            `;
        }
    }
    productos();

    btn_acceso_cliente.addEventListener("click", () => {
        dialogo_cliente.showModal();
    });

    btn_cerrar.addEventListener("click", () => {
        dialogo_cliente.close();
    });

});