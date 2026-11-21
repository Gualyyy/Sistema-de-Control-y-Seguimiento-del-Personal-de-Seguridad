document.addEventListener("DOMContentLoaded", () => {

    const input_buscar_producto = document.getElementById("buscar_producto");
    const select_categoria_producto = document.getElementById("categoria_producto");

    const contenedor_productos = document.getElementById("productos_disponibles");
    const contenedor_carrito = document.getElementById("productos_carrito");
    const panel_carrito_compra = document.getElementById("panel_carrito_compra");
    const btn_carrito_flotante = document.getElementById("btn_carrito_flotante");
    const btn_cerrar_carrito = document.getElementById("btn_cerrar_carrito");
    const fondo_carrito = document.getElementById("fondo_carrito");

    const cantidad_productos_carrito = document.getElementById("cantidad_productos_carrito");
    const cantidad_carrito_flotante = document.getElementById("cantidad_carrito_flotante");

    const subtotal_compra_ves = document.getElementById("subtotal_compra_ves");
    const subtotal_compra_usd = document.getElementById("subtotal_compra_usd");
    const descuento_compra_ves = document.getElementById("descuento_compra_ves");
    const descuento_compra_usd = document.getElementById("descuento_compra_usd");
    const iva_compra_ves = document.getElementById("iva_compra_ves");
    const iva_compra_usd = document.getElementById("iva_compra_usd");
    const total_compra_ves = document.getElementById("total_compra_ves");
    const total_compra_usd = document.getElementById("total_compra_usd");

    const btn_comprar = document.getElementById("btn_comprar");

    const dialogo_pago = document.getElementById("dialogo_pago");
    const btn_cerrar = document.getElementById("btn_cerrar_pago");
    const detalle_productos_pago = document.getElementById("detalle_productos_pago");

    const pago_subtotal_ves = document.getElementById("pago_subtotal_ves");
    const pago_subtotal_usd = document.getElementById("pago_subtotal_usd");
    const pago_descuento_ves = document.getElementById("pago_descuento_ves");
    const pago_descuento_usd = document.getElementById("pago_descuento_usd");
    const pago_impuesto_ves = document.getElementById("pago_impuesto_ves");
    const pago_impuesto_usd = document.getElementById("pago_impuesto_usd");
    const pago_total_ves = document.getElementById("pago_total_ves");
    const pago_total_usd = document.getElementById("pago_total_usd");

    const opciones_metodo_pago = document.getElementById("opciones_metodo_pago");
    const cuentas_destino_pago = document.getElementById("cuentas_destino_pago");
    const notificaciones_pago = document.getElementById("notificaciones_pago");
    const mensaje_notificacion_pago = document.getElementById("mensaje_notificacion_pago");

    const referencia_bancaria = document.getElementById("referencia_bancaria");
    const capture_pago = document.getElementById("capture_pago");
    const telefono_origen_pago = document.getElementById("telefono_origen_pago");
    const prefijo_telefono_pago = document.getElementById("prefijo_telefono_pago");
    const fecha_pago_bancario = document.getElementById("fecha_pago_bancario");
    const banco_origen = document.getElementById("banco_origen");

    const btn_confirmar_compra = document.getElementById("btn_confirmar_compra");

    const pasos_pago = [...dialogo_pago.querySelectorAll("[data-paso-pago]")];
    const indicadores_paso = [...dialogo_pago.querySelectorAll("[data-indicador-paso]")];

    const carrito_compras = new Map();
    const precios_volumen_cache = new Map();

    const hoy = new Date();

    const PORCENTAJE_IMPUESTO = 0.16;
    let vista_movil = window.innerWidth <= 850;

    const IMAGEN_PRODUCTO_DEFAULT = "{% static 'Imagenes/producto_sin_imagen.png' %}";

    let tasa_dolar = null;
    let cuentas_pago_disponibles = [];
    let metodo_pago_seleccionado = null;
    let cuenta_pago_seleccionada = null;

    configurarTelefono(telefono_origen_pago, prefijo_telefono_pago);

    function cerrar_carrito_movil(devolver_foco = false) {
        const carrito_oculto = vista_movil;

        panel_carrito_compra.classList.remove("carrito_abierto");
        panel_carrito_compra.setAttribute("aria-hidden", String(carrito_oculto));
        panel_carrito_compra.inert = carrito_oculto;
        fondo_carrito.classList.remove("fondo_carrito_visible");
        fondo_carrito.setAttribute("aria-hidden", "true");
        btn_carrito_flotante.setAttribute("aria-expanded", "false");
        btn_carrito_flotante.setAttribute(
            "aria-label",
            `Abrir carrito, ${cantidad_productos_carrito.textContent} productos`
        );
        document.body.classList.remove("carrito_panel_abierto");

        if (devolver_foco) {
            btn_carrito_flotante.focus();
        }
    }

    function abrir_carrito_movil() {
        panel_carrito_compra.classList.add("carrito_abierto");
        panel_carrito_compra.setAttribute("aria-hidden", "false");
        panel_carrito_compra.inert = false;
        fondo_carrito.classList.add("fondo_carrito_visible");
        fondo_carrito.setAttribute("aria-hidden", "false");
        btn_carrito_flotante.setAttribute("aria-expanded", "true");
        btn_carrito_flotante.setAttribute("aria-label", "Cerrar carrito");
        document.body.classList.add("carrito_panel_abierto");
        btn_cerrar_carrito.focus();
    }

    cerrar_carrito_movil();

    btn_carrito_flotante.addEventListener("click", () => {
        if (panel_carrito_compra.classList.contains("carrito_abierto")) {
            cerrar_carrito_movil();
        } else {
            abrir_carrito_movil();
        }
    });

    btn_cerrar_carrito.addEventListener("click", () => {
        cerrar_carrito_movil(true);
    });

    fondo_carrito.addEventListener("click", () => {
        cerrar_carrito_movil(true);
    });

    document.addEventListener("keydown", (evento) => {
        if (
            evento.key === "Escape" &&
            panel_carrito_compra.classList.contains("carrito_abierto")
        ) {
            cerrar_carrito_movil(true);
        }
    });

    window.addEventListener("resize", () => {
        const vista_movil_actual = window.innerWidth <= 850;

        if (vista_movil_actual !== vista_movil) {
            vista_movil = vista_movil_actual;
            cerrar_carrito_movil();
        }
    });

    btn_comprar.addEventListener("click", () => {
        cerrar_carrito_movil();
    });

    fecha_pago_bancario.max = [
        hoy.getFullYear(),
        String(hoy.getMonth() + 1).padStart(2, "0"),
        String(hoy.getDate()).padStart(2, "0")
    ].join("-");
    const bancos = [
        "Banco de Venezuela",
        "Bancaribe",
        "Banco Nacional de Credito",
        "Bancamiga",
        "Venezolano de Credito",
        "Banco Plaza",
        "Banco del Tesoro",
        "Banco Activo Universal",
        "BANFANB",
        "Banesco",
        "BBVA Provincial",
        "Banco Exterior",
        "Banco Digital de los Trabajadores",
        "Mercantil",
        "Banplus",
        "Banco Sofitasa",
        "100% Banco"
    ];

    function bancos_registrados() {
        bancos.forEach((banco, index) => {
            const option = document.createElement("option");

            option.value = banco;
            option.textContent = banco;

            if (index === 0) {
                option.selected = true;
            }

            banco_origen.append(option);
        });
    }

    bancos_registrados();

    // =========================================
    // CATEGORÍAS
    // =========================================

    async function categoria_registrada() {
        try {
            const respuesta = await fetch("/ventas/categorias_productos/");
            const resultado = await respuesta.json();

            select_categoria_producto.innerHTML = `
                <option value="" selected>Todas las Categorías</option>
            `;

            resultado.forEach(categoria => {
                const option = document.createElement("option");
                option.value = categoria.id_categoria;
                option.textContent = categoria.nombre;
                select_categoria_producto.append(option);
            });
        } catch (error) {
            console.error("Error al cargar las categorías:", error);
        }
    }

    categoria_registrada();


    // =========================================
    // EVENTOS DE BÚSQUEDA
    // =========================================

    input_buscar_producto.addEventListener("input", () => {
        productos_registrados();
    });

    select_categoria_producto.addEventListener("change", () => {
        productos_registrados();
    });

    // =========================================
    // PRECIOS POR VOLUMEN
    // =========================================

    async function obtener_precios_volumen(id_producto) {

        if (precios_volumen_cache.has(id_producto)) {
            return precios_volumen_cache.get(id_producto);
        }

        const formulario = new FormData();
        formulario.append("id_producto", id_producto);

        const csrf_token = document.querySelector(
            "[name=csrfmiddlewaretoken]"
        ).value;

        const respuesta = await fetch("/ventas/precio_volumen_producto/", {
            method: "POST",
            headers: {
                "X-CSRFToken": csrf_token
            },
            body: formulario
        });

        const resultado = await respuesta.json();

        if (!respuesta.ok || resultado.estado !== "exito") {
            throw new Error(
                resultado.descripcion ||
                "No fue posible consultar el descuento por volumen."
            );
        }

        if (!Array.isArray(resultado.precios)) {
            throw new Error(
                "La respuesta de descuentos por volumen no es válida."
            );
        }

        const precios = resultado.precios;

        precios_volumen_cache.set(id_producto, precios);

        return precios;

    }

    function calcular_porcentaje_descuento(producto) {

        const precios = Array.isArray(producto.precios_volumen)
            ? producto.precios_volumen
            : [];

        const cantidad = Number(producto.cantidad);
        const precio_volumen_aplicable = precios.find(precio => {

            const cantidad_minima = Number(precio.cantidad_minima);

            const cantidad_maxima =
                precio.cantidad_maxima === null ||
                    precio.cantidad_maxima === undefined ||
                    precio.cantidad_maxima === ""
                    ? Infinity
                    : Number(precio.cantidad_maxima);

            return (
                Number.isFinite(cantidad_minima) &&
                cantidad >= cantidad_minima &&
                cantidad <= cantidad_maxima
            );

        });

        if (!precio_volumen_aplicable) {
            return 0;
        }

        const porcentaje = Number(
            precio_volumen_aplicable.porcentaje_descuento
        );

        return Number.isFinite(porcentaje) && porcentaje >= 0 && porcentaje <= 100
            ? porcentaje
            : 0;
    }

    function actualizar_precio_unitario(producto) {

        producto.porcentaje_descuento = calcular_porcentaje_descuento(producto);
        producto.precio_unitario = Number(
            (
                Number(producto.precio_base) *
                (1 - producto.porcentaje_descuento / 100)
            ).toFixed(2)
        );

    }

    // =========================================
    // PRODUCTOS DISPONIBLES
    // =========================================

    async function productos_registrados() {

        try {

            const formulario = new FormData();

            formulario.append("nombre_producto", input_buscar_producto.value);
            formulario.append("categoria", select_categoria_producto.value);

            const csrf_token = document.querySelector(
                "[name=csrfmiddlewaretoken]"
            )?.value;

            const respuesta = await fetch("/ventas/productos_disponible_venta/", {

                method: "POST",

                headers: {
                    "X-CSRFToken": csrf_token
                },

                body: formulario

            });

            const resultado = await respuesta.json();

            if (resultado.estado !== "exito") {

                await Swal.fire({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon
                });

                return;

            }

            contenedor_productos.innerHTML = "";

            if (!Array.isArray(resultado.productos) ||
                resultado.productos.length === 0) {

                contenedor_productos.innerHTML = `
                    <div class="mensaje_sin_productos">
                        <i class="fa-solid fa-box-open"></i>
                        <p>No hay productos disponibles.</p>
                    </div>
                `;

                return;

            }

            resultado.productos.forEach(producto => {

                const tarjeta = document.createElement("div");

                tarjeta.classList.add("tarjeta_producto");

                const imagen = producto.imagen || IMAGEN_PRODUCTO_DEFAULT;

                tarjeta.innerHTML = `
                    <div class="imagen_producto">
                        <img
                            src="${imagen}"
                            alt="${producto.nombre}"
                            onerror="this.src='${IMAGEN_PRODUCTO_DEFAULT}'"
                        >
                    </div>

                    <div class="informacion_producto">

                        <h3>${producto.nombre}</h3>

                        <p class="codigo_producto">
                            ${producto.codigo}
                        </p>

                        <p class="unidad_producto">
                            Unidad: ${producto.unidad}
                        </p>

                        <div class="pie_tarjeta_producto">

                            <span class="precio_producto">
                                $${Number(producto.precio_base).toFixed(2)}
                            </span>

                            <button
                                type="button"
                                class="btn_agregar_producto"
                                data-id-producto="${producto.id_producto}"
                                title="Agregar al carrito"
                            >
                                <i class="fa-solid fa-plus"></i>
                            </button>

                        </div>

                    </div>
                `;

                contenedor_productos.appendChild(tarjeta);

                const boton_agregar = tarjeta.querySelector(
                    ".btn_agregar_producto"
                );

                boton_agregar.addEventListener("click", () => {

                    agregar_producto_carrito(producto);

                });

            });

        } catch (error) {

            console.error("Error al cargar los productos:", error);

        }

    }

    productos_registrados();

    // =========================================
    // TASA OFICIAL DEL DÓLAR
    // =========================================

    async function tasa_oficial_dolar() {

        try {

            const respuesta = await fetch(
                "https://ve.dolarapi.com/v1/dolares/oficial"
            );

            const resultado = await respuesta.json();

            const tasa = Number(resultado.promedio);


            tasa_dolar = Number(tasa.toFixed(2));

            formato_bolivares(tasa_dolar);

            actualizar_carrito();

        } catch (error) {

            console.error("Error al consultar el dólar:", error);

            [
                subtotal_compra_ves,
                descuento_compra_ves,
                iva_compra_ves,
                total_compra_ves
            ].forEach(monto => {

                monto.textContent = "No disponible";

            });

        }

    }

    tasa_oficial_dolar();

    // =========================================
    // APARTADO CARRITO DE COMPRA
    // =========================================

    async function agregar_producto_carrito(producto) {

        const id_producto = Number(producto.id_producto);
        const existencia = Number(producto.existencia);

        if (existencia <= 0) {

            Swal.fire({
                title: "Producto agotado",
                text: "Este producto no tiene existencia disponible.",
                icon: "warning"
            });

            return;

        }

        try {

            const producto_existente = carrito_compras.get(id_producto);

            if (
                producto_existente &&
                producto_existente.cantidad >= existencia
            ) {

                Swal.fire({
                    title: "Existencia insuficiente",
                    text: "No puedes agregar más unidades de las disponibles.",
                    icon: "warning"
                });

                return;

            }

            // Obtener los precios por volumen antes de agregar el producto.

            const precios_volumen = producto_existente
                ? producto_existente.precios_volumen
                : await obtener_precios_volumen(id_producto);

            if (producto_existente) {

                producto_existente.cantidad += 1;

                actualizar_precio_unitario(producto_existente);

            } else {

                const nuevo_producto = {

                    id_producto: id_producto,

                    nombre: producto.nombre,

                    codigo: producto.codigo,

                    unidad: producto.unidad,

                    precio_base: Number(producto.precio_base),

                    precio_unitario: Number(producto.precio_base),
                    porcentaje_descuento: 0,

                    precios_volumen: precios_volumen || [],

                    existencia: existencia,

                    imagen: producto.imagen,

                    cantidad: 1

                };

                actualizar_precio_unitario(nuevo_producto);

                carrito_compras.set(id_producto, nuevo_producto);

            }

            actualizar_carrito();

        } catch (error) {

            console.error("Error al agregar producto:", error);

            Swal.fire({
                title: "Error al agregar producto",
                text: error.message ||
                    "No fue posible obtener los precios del producto.",
                icon: "error"
            });

        }

    }

    // =========================================
    // ACTUALIZAR CARRITO
    // =========================================

    function actualizar_carrito() {

        contenedor_carrito.innerHTML = "";

        let cantidad_total = 0;

        carrito_compras.forEach(producto => {

            // Garantizar que siempre exista un precio unitario válido.

            if (
                !Number.isFinite(Number(producto.precio_unitario))
            ) {

                actualizar_precio_unitario(producto);

            }

            const subtotal_bruto = Number(
                (producto.precio_base * producto.cantidad).toFixed(2)
            );
            const descuento = Number(
                (
                    subtotal_bruto *
                    producto.porcentaje_descuento / 100
                ).toFixed(2)
            );
            const importe = subtotal_bruto - descuento;

            cantidad_total += producto.cantidad;

            const elemento = document.createElement("div");

            elemento.classList.add("item_carrito");

            const imagen = producto.imagen || IMAGEN_PRODUCTO_DEFAULT;

            elemento.innerHTML = `

                <div class="imagen_item_carrito">

                    <img
                        src="${imagen}"
                        alt="${producto.nombre}"
                        onerror="this.src='${IMAGEN_PRODUCTO_DEFAULT}'"
                    >

                </div>

                <div class="informacion_item_carrito">

                    <h3>${producto.nombre}</h3>

                    <div class="controles_item_carrito">

                        <div class="control_cantidad">

                            <button
                                type="button"
                                class="btn_disminuir"
                                title="Disminuir cantidad"
                                aria-label="Restar una unidad de ${producto.nombre}"
                                ${producto.cantidad <= 1 ? "disabled" : ""}
                            >
                                <i class="fa-solid fa-minus" aria-hidden="true"></i>
                            </button>

                            <input
                                type="text"
                                value="${producto.cantidad}"
                                readonly
                                aria-label="Cantidad de ${producto.nombre}"
                            >

                            <button
                                type="button"
                                class="btn_aumentar"
                                title="Agregar otra unidad"
                                aria-label="Agregar una unidad de ${producto.nombre}"
                                ${producto.cantidad >= producto.existencia ? "disabled" : ""}
                            >
                                <i class="fa-solid fa-plus" aria-hidden="true"></i>
                            </button>

                        </div>

                        <div class="precios_item_carrito">

                            <span class="precio_original_carrito">
                                Original: $${producto.precio_base.toFixed(2)}
                            </span>

                            <span class="precio_descuento_carrito">
                                Descuento: $${producto.precio_unitario.toFixed(2)}
                            </span>

                            <strong>
                                $${importe.toFixed(2)}
                            </strong>

                        </div>

                    </div>

                </div>

                <button
                    type="button"
                    class="btn_eliminar_carrito"
                    title="Eliminar ${producto.nombre} del carrito"
                    aria-label="Eliminar ${producto.nombre} del carrito"
                >
                    <i class="fa-solid fa-trash" aria-hidden="true"></i>
                    <span>Eliminar</span>
                </button>

            `;

            elemento.querySelector(".btn_aumentar").addEventListener(
                "click",
                () => {
                    modificar_cantidad_carrito(producto.id_producto, 1);
                }
            );

            elemento.querySelector(".btn_disminuir").addEventListener(
                "click",
                () => {
                    modificar_cantidad_carrito(producto.id_producto, -1);
                }
            );

            elemento.querySelector(".btn_eliminar_carrito").addEventListener(
                "click",
                () => {
                    eliminar_producto_carrito(producto.id_producto);
                }
            );

            contenedor_carrito.appendChild(elemento);

        });

        if (carrito_compras.size === 0) {

            contenedor_carrito.innerHTML = `

                <div class="carrito_vacio">

                    <i class="fa-solid fa-cart-shopping"></i>

                    <p>Tu carrito está vacío.</p>

                    <span>
                        Agrega productos para comenzar tu compra.
                    </span>

                </div>

            `;

        }

        const {
            subtotal,
            descuento,
            impuesto,
            total
        } = calcular_resumen_carrito();

        cantidad_productos_carrito.textContent = cantidad_total;
        cantidad_carrito_flotante.textContent = cantidad_total;
        if (!panel_carrito_compra.classList.contains("carrito_abierto")) {
            btn_carrito_flotante.setAttribute(
                "aria-label",
                `Abrir carrito, ${cantidad_total} productos`
            );
        }

        mostrar_monto(
            subtotal_compra_ves,
            subtotal_compra_usd,
            subtotal
        );

        mostrar_monto(
            descuento_compra_ves,
            descuento_compra_usd,
            descuento
        );

        mostrar_monto(
            iva_compra_ves,
            iva_compra_usd,
            impuesto
        );

        mostrar_monto(
            total_compra_ves,
            total_compra_usd,
            total
        );

        actualizar_resumen_dialogo();

        btn_comprar.disabled = carrito_compras.size === 0;

    }

    // =========================================
    // FUNCIONES DEL CARRITO
    // =========================================

    function calcular_resumen_carrito() {

        let subtotal = 0;
        let descuento = 0;

        carrito_compras.forEach(producto => {

            const subtotal_producto = Number(
                (producto.precio_base * producto.cantidad).toFixed(2)
            );
            subtotal += subtotal_producto;
            descuento += Number(
                (
                    subtotal_producto *
                    producto.porcentaje_descuento / 100
                ).toFixed(2)
            );

        });

        const impuesto = (subtotal - descuento) * PORCENTAJE_IMPUESTO;

        const total = subtotal - descuento + impuesto;

        return {
            subtotal,
            descuento,
            impuesto,
            total
        };

    }

    function formato_bolivares(monto_usd) {

        if (tasa_dolar === null) {
            return "No disponible";
        }

        return `${(monto_usd * tasa_dolar).toLocaleString("es-VE", {

            minimumFractionDigits: 2,

            maximumFractionDigits: 2

        })} Bs.`;

    }

    function mostrar_monto(elemento_ves, elemento_usd, monto_usd) {

        elemento_ves.textContent = formato_bolivares(monto_usd);

        elemento_usd.textContent = `$${monto_usd.toFixed(2)}`;

    }

    function actualizar_resumen_dialogo() {

        const resumen = calcular_resumen_carrito();

        mostrar_monto(
            pago_subtotal_ves,
            pago_subtotal_usd,
            resumen.subtotal
        );

        mostrar_monto(
            pago_descuento_ves,
            pago_descuento_usd,
            resumen.descuento
        );

        mostrar_monto(
            pago_impuesto_ves,
            pago_impuesto_usd,
            resumen.impuesto
        );

        mostrar_monto(
            pago_total_ves,
            pago_total_usd,
            resumen.total
        );

    }

    // =========================================
    // MODIFICAR CANTIDAD
    // =========================================

    function modificar_cantidad_carrito(id_producto, cambio) {

        if (!carrito_compras.has(id_producto)) {
            return;
        }

        const producto = carrito_compras.get(id_producto);

        const nueva_cantidad = producto.cantidad + cambio;

        if (nueva_cantidad > producto.existencia) {
            Swal.fire({
                title: "Existencia insuficiente",
                text: `Solo tienes ${producto.existencia} unidades disponibles.`,
                icon: "warning"
            });
            return;
        }

        if (nueva_cantidad < 1) {
            return;
        }

        producto.cantidad = nueva_cantidad;
        actualizar_precio_unitario(producto);

        actualizar_carrito();

    }

    function eliminar_producto_carrito(id_producto) {

        carrito_compras.delete(id_producto);

        actualizar_carrito();

    }

    // =========================================
    // APARTADO DIÁLOGO DE PAGO
    // =========================================

    referencia_bancaria.addEventListener("input", () => {

        referencia_bancaria.value = referencia_bancaria.value
            .replace(/\D/g, "")
            .slice(0, 6);

    });

    dialogo_pago.querySelectorAll("[data-siguiente-paso]").forEach(boton => {

        boton.addEventListener("click", () => {

            const siguiente = Number(boton.dataset.siguientePaso);

            if (siguiente === 2 && !metodo_pago_seleccionado) {

                mostrar_notificacion_pago(
                    "Debes elegir un método de pago para continuar.",
                    "warning"
                );

                return;

            }

            if (siguiente === 3 && !cuenta_pago_seleccionada) {

                mostrar_notificacion_pago(
                    "Debes elegir la cuenta bancaria donde realizaste el pago.",
                    "warning"
                );

                return;

            }

            mostrar_paso_pago(siguiente);

        });

    });

    dialogo_pago.querySelectorAll("[data-paso-anterior]").forEach(boton => {

        boton.addEventListener("click", () => {

            mostrar_paso_pago(
                Number(boton.dataset.pasoAnterior)
            );

        });

    });

    btn_confirmar_compra.addEventListener(
        "click",
        registrar_compra
    );

    // =========================================
    // NOTIFICACIONES DE PAGO
    // =========================================

    function crear_mensaje_pago(contenedor, mensaje, es_error = false) {

        const estado = document.createElement("p");

        estado.classList.add("estado_pago");

        if (es_error) {
            estado.classList.add("error");
        }

        estado.textContent = mensaje;

        contenedor.replaceChildren(estado);

    }

    function mostrar_notificacion_pago(mensaje, tipo = "info") {

        const iconos = {

            info: "fa-circle-info",

            warning: "fa-triangle-exclamation",

            error: "fa-circle-exclamation",

            success: "fa-circle-check"

        };

        const tipo_valido = Object.hasOwn(iconos, tipo)
            ? tipo
            : "info";

        notificaciones_pago.className =
            `notificaciones_pago ${tipo_valido}`;

        notificaciones_pago.setAttribute(
            "role",
            tipo_valido === "error" || tipo_valido === "warning"
                ? "alert"
                : "status"
        );

        notificaciones_pago.hidden = false;

        notificaciones_pago.querySelector("i").className =
            `fa-solid ${iconos[tipo_valido]}`;

        mensaje_notificacion_pago.textContent = mensaje;

    }

    function limpiar_notificacion_pago() {

        notificaciones_pago.hidden = true;

        mensaje_notificacion_pago.textContent = "";

    }

    // =========================================
    // ICONOS DE MÉTODOS DE PAGO
    // =========================================

    function icono_metodo_pago(nombre) {

        const nombre_normalizado = nombre
            .toLowerCase()
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "");

        if (nombre_normalizado.includes("movil")) {
            return "fa-mobile-screen-button";
        }

        if (
            nombre_normalizado.includes("transferencia") ||
            nombre_normalizado.includes("bancaria")
        ) {
            return "fa-building-columns";
        }

        return "fa-wallet";

    }

    // =========================================
    // CUENTAS POR MÉTODO DE PAGO
    // =========================================

    function mostrar_cuentas_metodo(id_metodo) {

        const cuentas = cuentas_pago_disponibles.filter(
            cuenta => String(cuenta.id_metodo) === String(id_metodo)
        );

        metodo_pago_seleccionado = String(id_metodo);

        cuenta_pago_seleccionada = null;

        cuentas_destino_pago.replaceChildren();

        if (cuentas.length === 0) {

            crear_mensaje_pago(
                cuentas_destino_pago,
                "No hay cuentas activas registradas para este método de pago."
            );

            return;

        }

        cuentas.forEach(cuenta => {

            const tarjeta = document.createElement("label");

            tarjeta.classList.add("cuenta_pago");

            const selector = document.createElement("input");

            selector.type = "radio";

            selector.name = "cuenta_destino_pago";

            selector.value = cuenta.id_cuenta_destino;

            selector.addEventListener("change", () => {

                cuenta_pago_seleccionada =
                    String(cuenta.id_cuenta_destino);

                cuentas_destino_pago.querySelectorAll(
                    ".cuenta_pago"
                ).forEach(elemento => {

                    elemento.classList.toggle(
                        "seleccionada",
                        elemento === tarjeta
                    );

                });

            });

            tarjeta.appendChild(selector);

            const contenido = document.createElement("div");

            contenido.classList.add("contenido_cuenta_pago");

            const banco = document.createElement("h4");

            banco.textContent = cuenta.banco || cuenta.metodo_pago;

            contenido.appendChild(banco);

            const datos = document.createElement("dl");

            datos.classList.add("datos_cuenta_pago");

            const campos = [

                ["Método", cuenta.metodo_pago],

                ["Documento", cuenta.documento],

                ["Teléfono", cuenta.telefono],

                ["Número de cuenta", cuenta.numero_cuenta],

                ["Tipo de cuenta", cuenta.tipo_cuenta]

            ];

            campos.forEach(([etiqueta, valor]) => {

                if (!valor || valor === "N/A") {
                    return;
                }

                const fila = document.createElement("div");

                const nombre_campo = document.createElement("dt");

                const valor_campo = document.createElement("dd");

                nombre_campo.textContent = etiqueta;

                valor_campo.textContent = valor;

                fila.append(nombre_campo, valor_campo);

                datos.appendChild(fila);

            });

            contenido.appendChild(datos);

            tarjeta.appendChild(contenido);

            cuentas_destino_pago.appendChild(tarjeta);

        });

    }

    // =========================================
    // SELECCIONAR MÉTODO DE PAGO
    // =========================================

    function seleccionar_metodo_pago(id_metodo) {

        metodo_pago_seleccionado = String(id_metodo);

        cuenta_pago_seleccionada = null;

        const botones = opciones_metodo_pago.querySelectorAll(
            ".opcion_metodo_pago"
        );

        botones.forEach(boton => {

            const seleccionado =
                boton.dataset.metodo === String(id_metodo);

            boton.classList.toggle("activo", seleccionado);

            boton.setAttribute(
                "aria-pressed",
                String(seleccionado)
            );

        });

        mostrar_cuentas_metodo(id_metodo);

    }

    // =========================================
    // CARGAR MÉTODOS Y CUENTAS DE PAGO
    // =========================================

    async function cargar_metodos_y_cuentas_pago() {

        opciones_metodo_pago.replaceChildren();

        cuentas_destino_pago.replaceChildren();

        crear_mensaje_pago(
            opciones_metodo_pago,
            "Cargando métodos de pago..."
        );

        crear_mensaje_pago(
            cuentas_destino_pago,
            "Cargando cuentas disponibles..."
        );

        try {

            const [
                respuesta_metodos,
                respuesta_cuentas
            ] = await Promise.all([

                fetch("/ventas/metodos_registrados/"),

                fetch("/ventas/visualizar_cuentas/")

            ]);

            const [
                resultado_metodos,
                resultado_cuentas
            ] = await Promise.all([

                respuesta_metodos.json(),

                respuesta_cuentas.json()

            ]);

            const metodos = resultado_metodos.metodos.filter(
                metodo => metodo.activo && metodo.nombre
            );

            cuentas_pago_disponibles =
                resultado_cuentas.cuentas.filter(
                    cuenta => cuenta.activo
                );

            opciones_metodo_pago.replaceChildren();

            if (metodos.length === 0) {

                crear_mensaje_pago(
                    opciones_metodo_pago,
                    "No hay métodos de pago activos disponibles."
                );

                crear_mensaje_pago(
                    cuentas_destino_pago,
                    "No hay cuentas disponibles para realizar el pago."
                );

                return;

            }

            metodos.forEach(metodo => {

                const boton = document.createElement("button");

                boton.type = "button";

                boton.classList.add("opcion_metodo_pago");

                boton.dataset.metodo = metodo.id_metodo;

                boton.setAttribute("aria-pressed", "false");

                const icono = document.createElement("i");

                icono.classList.add(
                    "fa-solid",
                    icono_metodo_pago(metodo.nombre)
                );

                icono.setAttribute("aria-hidden", "true");

                const nombre = document.createElement("span");

                nombre.textContent = metodo.nombre;

                boton.append(icono, nombre);

                boton.addEventListener("click", () => {

                    seleccionar_metodo_pago(metodo.id_metodo);

                });

                opciones_metodo_pago.appendChild(boton);

            });

            seleccionar_metodo_pago(metodos[0].id_metodo);

        } catch (error) {

            console.error(
                "Error al cargar los datos de pago:",
                error
            );

            mostrar_notificacion_pago(
                "No se pudieron cargar los métodos o las cuentas de pago. Intenta nuevamente.",
                "error"
            );

            crear_mensaje_pago(
                opciones_metodo_pago,
                "No se pudieron cargar los métodos de pago. Intenta nuevamente.",
                true
            );

            crear_mensaje_pago(
                cuentas_destino_pago,
                "No se pudieron cargar las cuentas de pago.",
                true
            );

        }

    }

    // =========================================
    // ABRIR Y CERRAR DIÁLOGO
    // =========================================

    btn_comprar.addEventListener(
        "click",
        mostrar_dialogo_pago
    );

    btn_cerrar.addEventListener("click", () => {

        dialogo_pago.close();

    });

    async function mostrar_dialogo_pago() {

        if (carrito_compras.size === 0) {
            return;
        }

        detalle_productos_pago.innerHTML = "";

        carrito_compras.forEach(producto => {

            const item = document.createElement("div");

            item.classList.add("item_detalle_pago");

            const descripcion = document.createElement("span");

            descripcion.textContent =
                `${producto.nombre} × ${producto.cantidad}`;

            const importe = document.createElement("strong");

            const subtotal_bruto = Number(
                (producto.precio_base * producto.cantidad).toFixed(2)
            );
            const descuento = Number(
                (
                    subtotal_bruto *
                    producto.porcentaje_descuento / 100
                ).toFixed(2)
            );
            importe.textContent = `$${(subtotal_bruto - descuento).toFixed(2)}`;

            if (producto.porcentaje_descuento > 0) {
                const detalle_descuento = document.createElement("small");
                detalle_descuento.textContent =
                    `Descuento ${producto.porcentaje_descuento}%: -$${descuento.toFixed(2)}`;
                item.append(descripcion, detalle_descuento, importe);
            } else {
                item.append(descripcion, importe);
            }

            detalle_productos_pago.appendChild(item);

        });

        actualizar_resumen_dialogo();

        mostrar_paso_pago(0);

        metodo_pago_seleccionado = null;

        cuenta_pago_seleccionada = null;

        dialogo_pago.showModal();

        await cargar_metodos_y_cuentas_pago();

    }

    // =========================================
    // NAVEGACIÓN ENTRE PASOS
    // =========================================

    function mostrar_paso_pago(indice) {

        limpiar_notificacion_pago();

        pasos_pago.forEach((paso, posicion) => {

            paso.hidden = posicion !== indice;

        });

        indicadores_paso.forEach((indicador, posicion) => {

            const actual = posicion === indice;

            indicador.classList.toggle("activo", actual);

            if (actual) {

                indicador.setAttribute("aria-current", "step");

            } else {

                indicador.removeAttribute("aria-current");

            }

        });

        dialogo_pago.querySelector(".contenedor_datos").scrollTo({

            top: 0,

            behavior: "smooth"

        });

    }

    // =========================================
    // REGISTRAR COMPRA
    // =========================================

    async function registrar_compra() {

        const referencia = referencia_bancaria.value.trim();
        const telefono = `${prefijo_telefono_pago.value}-${telefono_origen_pago.value.trim()}`;
        const fecha = fecha_pago_bancario.value;
        const banco = banco_origen.value;
        const archivo_capture = capture_pago.files[0];

        if (!archivo_capture) {
            capture_pago.focus();
            mostrar_notificacion_pago("Adjunta el capture del pago para continuar.", "warning");
            return;

        }

        if (!/^\d{6}$/.test(referencia)) {
            referencia_bancaria.focus();
            mostrar_notificacion_pago(
                "La referencia bancaria debe tener exactamente 6 dígitos numéricos.",
                "warning"
            );
            return;
        }

        if (!fecha || fecha > fecha_pago_bancario.max) {
            fecha_pago_bancario.focus();
            mostrar_notificacion_pago(
                "Selecciona una fecha válida que no sea posterior al día de hoy.",
                "warning"
            );
            return;
        }

        if (!banco || banco.length > 100) {
            banco_origen.focus();
            mostrar_notificacion_pago(
                "Ingresa el banco desde donde realizaste el pago.",
                "warning"
            );

            return;

        }

        const csrf_token = document.querySelector(
            "[name=csrfmiddlewaretoken]"
        )?.value;

        if (!csrf_token) {

            console.error(
                "No se encontró el token CSRF para registrar la compra."
            );

            mostrar_notificacion_pago(
                "No se pudo validar la solicitud. Actualiza la página e intenta nuevamente.",
                "error"
            );

            return;

        }

        const boton_texto = btn_confirmar_compra.innerHTML;

        let registro_completado = false;
        limpiar_notificacion_pago();
        btn_confirmar_compra.disabled = true;
        btn_confirmar_compra.textContent = "Registrando...";

        try {
            const formulario = new FormData();
            formulario.append("tasa_cambio", String(tasa_dolar));
            formulario.append("productos", JSON.stringify(
                Array.from(carrito_compras.values(), producto => ({
                    id_producto: producto.id_producto,
                    cantidad: producto.cantidad
                })
                )
            ));
            formulario.append("id_metodo", metodo_pago_seleccionado);
            formulario.append("id_cuenta", cuenta_pago_seleccionada);
            formulario.append("referencia", referencia);
            formulario.append("capture_pago", archivo_capture);
            formulario.append("telefono_origen", telefono);
            formulario.append("fecha_pago_bancario", fecha);
            formulario.append("banco_origen", banco);

            const respuesta = await fetch("/ventas/registrar_compra_cliente/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrf_token
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            carrito_compras.clear();

            actualizar_carrito();

            [
                referencia_bancaria,
                capture_pago,
                telefono_origen_pago,
                fecha_pago_bancario,
                banco_origen
            ].forEach(campo => {

                campo.value = "";

            });

            registro_completado = true;

            btn_confirmar_compra.innerHTML =
                '<i class="fa-solid fa-check"></i> Compra registrada';

            mostrar_notificacion_pago(
                resultado.descripcion ||
                "La compra quedó pendiente de revisión.",
                resultado.correo_enviado === false ? "warning" : "success"
            );
        } catch (error) {
            console.error(
                "Error al registrar la compra:",
                error
            );

            mostrar_notificacion_pago(
                error.message ||
                "No se pudo registrar la compra. Intenta nuevamente.",
                "error"
            );
        } finally {
            btn_confirmar_compra.disabled = registro_completado;
            if (!registro_completado) {
                btn_confirmar_compra.innerHTML = boton_texto;
            }
        }
    }

});