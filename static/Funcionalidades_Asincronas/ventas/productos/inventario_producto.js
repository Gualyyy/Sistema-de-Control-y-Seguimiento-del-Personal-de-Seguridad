document.addEventListener("DOMContentLoaded", () => {

    const contenedor_productos = document.getElementById("contenedor_productos");

    const select_categoria_producto = document.getElementById("categoria_producto_b");
    const select_unidad_medida = document.getElementById("unidad_medida_b");

    const btn_ret = document.querySelector(".btn_retroceder");
    const btn_av = document.querySelector(".btn_avanzar");

    let productos_recibidos = [];
    let pagina_actual = 1;
    const filas_por_pagina = 10;

    let categoria = "", unidad = "";

    async function categoria_registrada() {
        try {
            const respuesta = await fetch("/ventas/categorias_productos/");
            const resultado = await respuesta.json();
            console.log(resultado);

            select_categoria_producto.innerHTML = "<option value='' selected>Todas las Categorias</option>";

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

            select_unidad_medida.innerHTML = "<option value='' selected>Todas las Unidades</option>";

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

        await inventario_productos();
    });

    select_unidad_medida.addEventListener("change", async () => {
        unidad = select_unidad_medida.value;

        await inventario_productos();
    });

    async function inventario_productos() {
        try {
            const formulario = new FormData();
            formulario.append("categoria", categoria);
            formulario.append("unidad", unidad);

            const respuesta = await fetch("/ventas/movimiento_producto/", {
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
                pagina_actual = 1;
                mostrarProductos();
                return;
            }

            productos_recibidos = resultado.movimientos;
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
                <td colspan="7" class="texto_sin_registros">
                    No hay movimientos de inventario registrados.
                </td>
            </tr>
        `;

            actualizarBotones();
            return;
        }

        productos_pagina.forEach((producto, index) => {
            const fila = document.createElement("tr");

            fila.dataset.codigo = producto.codigo_producto;

            fila.innerHTML = `
            <td>${inicio + index + 1}</td>
            <td>${producto.nombre_producto}</td>
            <td>${producto.codigo_producto}</td>
            <td>${producto.tipo_movimiento}</td>
            <td>${producto.cantidad} ${producto.abreviatura}</td>
            <td>${producto.valor_total}$</td>
            <td>${producto.fecha_movimiento}</td>
        `;

            contenedor_productos.appendChild(fila);
        });

        actualizarBotones();
    }

    function actualizarBotones() {
        const total_paginas = Math.ceil(
            productos_recibidos.length / filas_por_pagina
        );

        btn_ret.disabled = pagina_actual <= 1;
        btn_av.disabled = pagina_actual >= total_paginas;
    }

    btn_ret.addEventListener("click", () => {
        if (pagina_actual > 1) {
            pagina_actual--;
            mostrarProductos();
        }
    });

    btn_av.addEventListener("click", () => {
        const total_paginas = Math.ceil(
            productos_recibidos.length / filas_por_pagina
        );

        if (pagina_actual < total_paginas) {
            pagina_actual++;
            mostrarProductos();
        }
    });

    inventario_productos();

});