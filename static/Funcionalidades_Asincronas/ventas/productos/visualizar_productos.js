document.addEventListener("DOMContentLoaded", () => {

    const contenedor_productos = document.getElementById("contenedor_productos");

    const select_categoria_producto = document.getElementById("categoria_producto_b");
    const select_unidad_medida = document.getElementById("unidad_medida_b");

    const btn_lista_productos_pdf = document.getElementById("lista_productos_pdf");
    const btn_detalle_producto_pdf = document.getElementById("detalle_producto_pdf");

    const dialogo_detalle = document.getElementById("dialogo_detalle");
    const btn_cerrar_detalle = document.getElementById("btn_cerrar_detalle");

    const input_id_producto = document.getElementById("id_producto");
    const input_imagen_producto = document.getElementById("imagen_producto");
    const input_nombre_producto = document.getElementById("nombre_producto");
    const input_codigo_producto = document.getElementById("codigo_producto");
    const input_precio_base = document.getElementById("precio_base");
    const input_costo_base = document.getElementById("costo_base");
    const input_fecha_producto = document.getElementById("fecha_producto");
    const input_unidad_medida = document.getElementById("unidad_medida");
    const input_categoria_producto = document.getElementById("categoria_producto");

    const btn_ret = document.querySelector(".btn_ret");
    const btn_av = document.querySelector(".btn_av");

    let productos_recibidos = [];
    let pagina_actual = 1;
    const filas_por_pagina = 10;

    let categoria = "", unidad = "";

    async function categoria_registrada() {
        try {
            const respuesta = await fetch("/ventas/categorias_productos/");
            const resultado = await respuesta.json();
            console.log(resultado);

            select_categoria_producto.innerHTML = "<option value='' selected>Selecciona un Catalogo del Producto</option>";

            resultado.forEach(categoria => {
                const option = document.createElement("option");
                option.value = categoria.id_categoria;
                option.textContent = categoria.nombre;
                select_categoria_producto.append(option);
            });
        } catch (error) {
            console.error(error);
        }
    }
    categoria_registrada();

    async function unidades_medida() {
        try {
            const respuesta = await fetch("/ventas/unidades_medida/");
            const resultado = await respuesta.json();
            console.log(resultado);

            select_unidad_medida.innerHTML = "<option value='' selected>Selecciona un Unidad de Medida</option>";

            resultado.forEach(unidad => {
                const option = document.createElement("option");
                option.value = unidad.id_unidad;
                option.textContent = unidad.nombre + " | " + unidad.abreviatura;
                select_unidad_medida.append(option);
            });
        } catch (error) {
            console.error(error);
        }
    }
    unidades_medida();

    select_categoria_producto.addEventListener("change", async () => {
        categoria = select_categoria_producto.value;

        await productos_registrados();
    });

    select_unidad_medida.addEventListener("change", async () => {
        unidad = select_unidad_medida.value;

        await productos_registrados();
    });

    async function productos_registrados() {
        try {
            const formulario = new FormData();
            formulario.append("categoria", categoria);
            formulario.append("unidad", unidad);

            const respuesta = await fetch("/ventas/productos_registrados/", {
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

            if (resultado.estado !== "exito") {
                productos_recibidos = [];
                mostrarProductos();
                return;
            }

            productos_recibidos = resultado.productos;
            pagina_actual = 1;

            mostrarProductos();

        } catch (error) {
            console.error(error);
        }
    }

    function mostrarProductos() {
        contenedor_productos.innerHTML = "";

        const inicio = (pagina_actual - 1) * filas_por_pagina;
        const final = inicio + filas_por_pagina;

        const productos_pagina = productos_recibidos.slice(inicio, final);

        if (productos_pagina.length === 0) {
            contenedor_productos.innerHTML = `
                <tr>
                    <td colspan="4" class="texto_sin_registros">
                        No hay productos registrados.
                    </td>
                </tr>
            `;

            actualizarBotones();
            return;
        }

        productos_pagina.forEach((producto, index) => {
            const fila = document.createElement("tr");

            fila.dataset.codigo = producto.codigo;

            fila.innerHTML = `
                <td>${inicio + index + 1}</td>
                <td>${producto.nombre}</td>
                <td>${producto.codigo}</td>
                <td>${producto.fecha_registro}</td>
            `;

            contenedor_productos.appendChild(fila);
        });

        actualizarBotones();
    }

    function actualizarBotones() {
        const total_paginas = Math.ceil(
            productos_recibidos.length / filas_por_pagina
        );

        btn_ret.disabled = pagina_actual === 1;
        btn_av.disabled = pagina_actual >= total_paginas;
    }

    btn_ret.addEventListener("click", () => {
        if (pagina_actual > 1) {
            pagina_actual--;
            mostrarProductos();
        }
    });

    btn_av.addEventListener("click", () => {
        const total_paginas = Math.ceil(productos_recibidos.length / filas_por_pagina);

        if (pagina_actual < total_paginas) {
            pagina_actual++;
            mostrarProductos();
        }
    });
    productos_registrados();

    contenedor_productos.addEventListener("click", async (e) => {
        const fila = e.target.closest("tr");

        const codigo = fila.dataset.codigo;

        try {
            const formulario = new FormData();
            formulario.append("codigo", codigo);

            const respuesta = await fetch("/ventas/detalle_producto_registrado/", {
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

            input_imagen_producto.src = resultado.producto.imagen;
            input_id_producto.value = resultado.producto.id_producto;
            input_nombre_producto.value = resultado.producto.nombre;
            input_codigo_producto.value = resultado.producto.codigo;
            input_precio_base.value = resultado.producto.precio_base;
            input_costo_base.value = resultado.producto.costo_base;
            input_fecha_producto.value = resultado.producto.fecha_registro;
            input_unidad_medida.value = resultado.producto.unidad + " | " + resultado.producto.abreviatura;
            input_categoria_producto.value = resultado.producto.categoria;

            dialogo_detalle.showModal();
        } catch (error) {
            console.error(error);
        }
    });

    btn_cerrar_detalle.addEventListener("click", () => {
        dialogo_detalle.close();
    });

    btn_lista_productos_pdf.addEventListener("click", async () => {
        try {
            const formulario = new FormData();
            formulario.append("id_categoria", select_categoria_producto.value);
            formulario.append("id_unidad", select_unidad_medida.value);

            const respuesta = await fetch("/ventas/lista_productos_pdf/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector(
                        "[name=csrfmiddlewaretoken]"
                    ).value
                },
                body: formulario
            });

            const tipo_contenido = respuesta.headers.get("content-type") || "";

            if (tipo_contenido.includes("application/pdf")) {
                const archivo_pdf = await respuesta.blob();
                const url_pdf = URL.createObjectURL(archivo_pdf);

                window.open(url_pdf, "_blank");

                setTimeout(() => {
                    URL.revokeObjectURL(url_pdf);
                }, 60000);

                return;
            }
            const resultado = await respuesta.json();

            Swal.fire({
                title: resultado.title,
                text: resultado.descripcion,
                icon: resultado.icon
            });

        } catch (error) {
            console.error(error);
        }
    });

    btn_detalle_producto_pdf.addEventListener("click", async () => {
        try {
            mostrar_mensaje_dialogo(
                "contenedor_mensajes_reporte",
                "Generando reporte PDF...",
                "informacion"
            );

            const formulario = new FormData();
            formulario.append("id_producto", input_id_producto.value);

            const respuesta = await fetch("/ventas/lista_detalle_producto_pdf/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector(
                        "[name=csrfmiddlewaretoken]"
                    ).value
                },
                body: formulario
            });

            const tipo_contenido = respuesta.headers.get("content-type") || "";

            if (tipo_contenido.includes("application/pdf")) {
                const archivo_pdf = await respuesta.blob();
                const url_pdf = URL.createObjectURL(archivo_pdf);

                window.open(url_pdf, "_blank");

                setTimeout(() => {
                    URL.revokeObjectURL(url_pdf);
                }, 60000);

                resetear_mensaje_dialogo(
                    "contenedor_mensajes_reporte"
                );

                return;
            }

            const resultado = await respuesta.json();

            const tipos_mensaje = {
                success: "exito",
                warning: "advertencia",
                error: "error",
                info: "informacion"
            };

            const tipo_mensaje = tipos_mensaje[resultado.icon] || "error";

            await mostrar_mensaje_temporal(
                "contenedor_mensajes_reporte",
                resultado.descripcion,
                tipo_mensaje,
                4
            );

            resetear_mensaje_dialogo(
                "contenedor_mensajes_reporte"
            );

        } catch (error) {
            console.error(error);

            await mostrar_mensaje_temporal(
                "contenedor_mensajes_reporte",
                "Ocurrió un error al generar el reporte PDF.",
                "error",
                4
            );

            resetear_mensaje_dialogo(
                "contenedor_mensajes_reporte"
            );
        }
    });

    function mostrar_mensaje_dialogo(id_contenedor, mensaje, tipo = "informacion") {
        const contenedor = document.getElementById(id_contenedor);

        if (!contenedor) return;

        contenedor.className = `contenedor_mensajes ${tipo}`;
        contenedor.replaceChildren();

        const reloj = document.createElement("i");
        reloj.className = "fa-solid fa-hourglass-half reloj_procesamiento";
        reloj.setAttribute("aria-hidden", "true");

        const texto = document.createElement("p");
        texto.textContent = mensaje;

        contenedor.append(reloj, texto);
        contenedor.hidden = false;
    }

    function mostrar_mensaje_temporal(id_contenedor, mensaje, tipo = "exito", segundos = 4) {
        return new Promise((resolve) => {
            const contenedor = document.getElementById(id_contenedor);

            if (!contenedor) {
                resolve();
                return;
            }

            contenedor.className = `contenedor_mensajes ${tipo}`;
            contenedor.replaceChildren();

            const reloj = document.createElement("i");
            reloj.className = "fa-solid fa-hourglass-half reloj_procesamiento";
            reloj.setAttribute("aria-hidden", "true");

            const texto = document.createElement("p");
            texto.textContent = mensaje;

            const contador = document.createElement("span");
            contador.className = "contador_notificacion";
            contador.setAttribute("aria-live", "off");

            contenedor.append(reloj, texto, contador);
            contenedor.hidden = false;

            let restante = segundos;
            contador.textContent = ` ${restante} s`;

            const intervalo = setInterval(() => {
                restante--;

                if (restante <= 0) {
                    clearInterval(intervalo);
                    resolve();
                    return;
                }

                contador.textContent = ` ${restante} s`;
            }, 1000);
        });
    }

    function resetear_mensaje_dialogo(id_contenedor) {
        const contenedor = document.getElementById(id_contenedor);

        if (!contenedor) return;

        contenedor.className = "contenedor_mensajes informacion";
        contenedor.replaceChildren();

        const reloj = document.createElement("i");
        reloj.className = "fa-solid fa-hourglass-half reloj_procesamiento";
        reloj.setAttribute("aria-hidden", "true");

        const texto = document.createElement("p");
        texto.textContent = "Presione el botón para generar el reporte PDF.";

        contenedor.append(reloj, texto);
        contenedor.hidden = false;
    }
});