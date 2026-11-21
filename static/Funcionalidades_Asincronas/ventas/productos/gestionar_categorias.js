document.addEventListener("DOMContentLoaded", () => {

    const formulario_registrar = document.getElementById("formulario_registrar");
    const input_nombre_categoria = document.getElementById("nombre_categoria");

    const dialogo_categoria = document.getElementById("dialogo_categoria");
    const btn_cerrar = document.getElementById("btn_cerrar");

    const formulario_actualizar = document.getElementById("formulario_actualizar");
    const input_id_categoria = document.getElementById("id_categoria");
    const input_nuevo_nombre = document.getElementById("nuevo_nombre");

    const contenedor_categorias = document.getElementById("contenedor_categorias");

    const btn_ret = document.querySelector(".btn_retroceder");
    const btn_av = document.querySelector(".btn_avanzar");

    function soloTexto(input) {
        input.value = input.value.replace(/[^a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]/g, '');
    }

    input_nombre_categoria.addEventListener("input", function () {
        soloTexto(input_nombre_categoria);
    });

    formulario_registrar.addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
            const formulario = new FormData(formulario_registrar);

            const respuesta = await fetch("/ventas/registrar_categorias/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            await Swal.fire({
                title: resultado.title,
                text: resultado.descripcion,
                icon: resultado.icon
            });

            formulario_registrar.reset();
            productos_registrados();
        } catch (error) {
            console.error(error);
        }
    });

    let categorias_recibidas = [];
    let pagina_actual = 1;
    const filas_por_pagina = 10;

    // CATEGORÍAS REGISTRADAS
    async function productos_registrados() {
        try {
            const respuesta = await fetch("/ventas/categorias_productos/");
            const resultado = await respuesta.json();
            console.log(resultado);

            categorias_recibidas = resultado;
            pagina_actual = 1;

            mostrarCategorias();
        } catch (error) {
            console.error(error);

            categorias_recibidas = [];
            mostrarCategorias();
        }
    }

    // MOSTRAR CATEGORÍAS
    function mostrarCategorias() {
        contenedor_categorias.innerHTML = "";

        const inicio = (pagina_actual - 1) * filas_por_pagina;
        const final = inicio + filas_por_pagina;

        const categorias_pagina = categorias_recibidas.slice(inicio, final);

        if (categorias_pagina.length === 0) {
            contenedor_categorias.innerHTML = `
                <tr>
                    <td colspan="3" class="texto_sin_registros">
                        No hay categorías registradas.
                    </td>
                </tr>
            `;

            actualizarBotones();
            return;
        }

        categorias_pagina.forEach((categoria, index) => {
            const fila = document.createElement("tr");

            fila.dataset.id = categoria.id_categoria;

            fila.innerHTML = `
                <td>${inicio + index + 1}</td>
                <td></td>
                <td>
                    <button type="button"
                        class="btn_tabla ${categoria.activo ? 'estado_activo' : 'estado_inactivo'}"
                        data-id="${categoria.id_categoria}"
                        data-estado="${categoria.activo}">
                        ${categoria.activo ? 'Activo' : 'Inactivo'}
                    </button>
                </td>
                <td>
                    <button type="button" 
                        class="btn_tabla btn_actualizar_categoria"
                        data-id="${categoria.id_categoria}"
                        data-nombre="${categoria.nombre}">
                        <i class="fa-solid fa-pen-to-square"></i>
                        Actualizar
                    </button>
                </td>
            `;

            fila.children[1].textContent = categoria.nombre;

            contenedor_categorias.appendChild(fila);
        });

        actualizarBotones();
    }

    // ACTUALIZAR BOTONES DE PAGINACIÓN
    function actualizarBotones() {
        const total_paginas = Math.ceil(
            categorias_recibidas.length / filas_por_pagina
        );

        btn_ret.disabled = pagina_actual === 1;
        btn_av.disabled = pagina_actual >= total_paginas;
    }

    // RETROCEDER
    btn_ret.addEventListener("click", () => {
        if (pagina_actual > 1) {
            pagina_actual--;
            mostrarCategorias();
        }
    });

    // AVANZAR
    btn_av.addEventListener("click", () => {
        const total_paginas = Math.ceil(
            categorias_recibidas.length / filas_por_pagina
        );

        if (pagina_actual < total_paginas) {
            pagina_actual++;
            mostrarCategorias();
        }
    });

    // INICIALIZAR
    productos_registrados();

    let id_categoria = "";

    contenedor_categorias.addEventListener("click", async (e) => {
        const btn_actualizar = e.target.closest(".btn_actualizar_categoria");
        if (btn_actualizar) {
            id_categoria = btn_actualizar.dataset.id;

            await buscar_categoria();

            dialogo_categoria.showModal();
            return;
        }

        const btn_estado = e.target.closest(".estado_activo, .estado_inactivo");
        if (btn_estado) {
            id_categoria = btn_estado.dataset.id;

            const estado_actual = btn_estado.dataset.estado;
            const nuevo_estado = estado_actual === "true" ? "false" : "true";

            await actualizar_estado(nuevo_estado);
        }
    });

    async function buscar_categoria() {
        try {
            const formulario = new FormData();
            formulario.append("id_categoria", id_categoria);

            const respuesta = await fetch("/ventas/buscar_categoria/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            if (resultado.estado != "exito") {
                await Swal.fire({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon
                });
                return;
            }

            input_id_categoria.value = resultado.id_categoria;
            input_nuevo_nombre.value = resultado.nombre;
        } catch (error) {
            console.error(error);
        }
    }

    formulario_actualizar.addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
            const formulario = new FormData(formulario_actualizar);

            const respuesta = await fetch("/ventas/actualizar_categoria/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            dialogo_categoria.close();

            await Swal.fire({
                title: resultado.title,
                text: resultado.descripcion,
                icon: resultado.icon
            });

            formulario_actualizar.reset();
            productos_registrados();
        } catch (error) {
            console.error(error);
        }
    });

    async function actualizar_estado(nuevo_estado) {
        const datos = new FormData();
        datos.append("id_categoria", id_categoria);
        datos.append("estado", nuevo_estado);

        try {
            const respuesta = await fetch("/ventas/estado_categoria/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: datos
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            if (resultado.estado === "exito") {
                await productos_registrados();
            }

            Swal.fire({
                title: resultado.title,
                text: resultado.descripcion,
                icon: resultado.icon
            });

        } catch (error) {
            console.error(error);
        }
    }

    btn_cerrar.addEventListener("click", () => {
        dialogo_categoria.close();
    });

});