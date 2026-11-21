document.addEventListener("DOMContentLoaded", () => {

    const formulario_actualizar = document.getElementById("formulario_actualizar");

    const input_id_equipo = document.getElementById("id_equipo");

    // Campos Actualizar
    const input_nombre_equipo_actualizar = document.getElementById("nombre_equipo_actualizar");
    const textarea_observacion_equipo_actualizar = document.getElementById("observacion_equipo_actualizar");
    const input_cantidad_disponible_actualizar = document.getElementById("cantidad_disponible_actualizar");
    const select_categoria_equipo_actualizar = document.getElementById("categoria_equipo_actualizar");
    const contador_observacion_actualizar = document.getElementById("contador_observacion_actualizar");
    const contenedor_msg_cantidad_actualizar = document.getElementById("contenedor_msg_cantidad_actualizar");

    // Campos Busqueda
    const contenedor_equipos = document.getElementById("contenedor_equipos");

    const formulario_busqueda_equipos = document.getElementById(
        "formulario_busqueda_equipos"
    );
    const input_codigo_equipo = document.getElementById("codigo_equipo");
    const select_categorias_registradas = document.getElementById("categorias_registradas");
    const dialogo_equipo = document.getElementById("dialogo_equipo");
    const input_id_equipo_detalle = document.getElementById("id_equipo_detalle");
    const btn_cerrar = document.getElementById("btn_cerrar");

    // Visualizar
    const input_nombre_equipo_visualizar = document.getElementById("nombre_equipo_visualizar");
    const input_codigo_equipo_visualizar = document.getElementById("codigo_equipo_visualizar");
    const textarea_observacion_equipo_visualizar = document.getElementById("observacion_equipo_visualizar");
    const input_cantidad_disponible_equipo_visualizar = document.getElementById("cantidad_disponible_equipo_visualizar");
    const input_categoria_equipo_visualizar = document.getElementById("categoria_equipo_visualizar");
    const input_fecha_registr_visualizar = document.getElementById("fecha_registro_visualizar");

    // Desplazamiento de registros
    const boton_retroceder = document.querySelector(".btn_ret");
    const boton_avanzar = document.querySelector(".btn_av");

    const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;

    const FILAS_POR_PAGINA = 10;

    let lista_equipos_registrados = [];
    let pagina_actual = 1;
    let consulta_equipos_activa = null;

    const btn_actualizar = document.getElementById("btn_actualizar");

    function actualizarContador(textarea, contador) {
        contador.textContent = textarea.value.length;
    }

    textarea_observacion_equipo_actualizar.addEventListener("input", () => {
        textarea_observacion_equipo_actualizar.value = textarea_observacion_equipo_actualizar.value.replace(/[^a-zA-ZáéíóúÁÉÍÓÚñÑ0-9\s.,:;()\-*]/g, "");

        actualizarContador(
            textarea_observacion_equipo_actualizar,
            contador_observacion_actualizar
        );
    });

    const controles_actualizacion = [
        input_id_equipo,
        input_nombre_equipo_actualizar,
        textarea_observacion_equipo_actualizar,
        input_cantidad_disponible_actualizar,
        select_categoria_equipo_actualizar,
        btn_actualizar,
    ];

    function bloquearFormularioActualizar(bloquear = true) {
        controles_actualizacion.forEach(control => {
            if (control) {
                control.disabled = bloquear;
            }
        });
    }
    bloquearFormularioActualizar(true);

    function validarCantidadDisponible() {
        const valor = input_cantidad_disponible_actualizar.value.trim();
        const cantidadEntregada = Number(
            input_cantidad_disponible_actualizar.dataset.entregada || 0
        );
        let mensaje = "";

        if (!valor) {
            mensaje = "La cantidad total es obligatoria.";
        } else if (!/^[1-9]\d{0,2}$/.test(valor)) {
            mensaje = "Ingrese un número entero entre 1 y 999, sin ceros al inicio.";
        } else if (Number(valor) < cantidadEntregada) {
            mensaje = `La cantidad total no puede ser menor a ${cantidadEntregada} ${cantidadEntregada === 1 ? "unidad" : "unidades"} entregadas a los supervisores.`;
        }

        input_cantidad_disponible_actualizar.setCustomValidity(mensaje);
        input_cantidad_disponible_actualizar.classList.toggle(
            "is-invalid",
            Boolean(mensaje)
        );
        input_cantidad_disponible_actualizar.classList.toggle(
            "is-valid",
            !mensaje
        );
        contenedor_msg_cantidad_actualizar.textContent = mensaje;
        contenedor_msg_cantidad_actualizar.classList.toggle(
            "error",
            Boolean(mensaje)
        );
        contenedor_msg_cantidad_actualizar.classList.toggle(
            "exito",
            !mensaje
        );

        return !mensaje;
    }

    function actualizarEstadoBoton() {
        const cantidadValida = validarCantidadDisponible();
        const controlesValidos = [
            input_nombre_equipo_actualizar,
            input_cantidad_disponible_actualizar,
            select_categoria_equipo_actualizar
        ].every(control => control.checkValidity());

        btn_actualizar.disabled = (
            !input_id_equipo.value
            || !controlesValidos
            || !cantidadValida
        );
    }

    input_cantidad_disponible_actualizar.addEventListener("input", () => {
        input_cantidad_disponible_actualizar.value =
            input_cantidad_disponible_actualizar.value
                .replace(/[^0-9]/g, "")
                .slice(0, 3);
        actualizarEstadoBoton();
    });

    input_cantidad_disponible_actualizar.addEventListener(
        "change",
        actualizarEstadoBoton
    );
    input_nombre_equipo_actualizar.addEventListener(
        "input",
        actualizarEstadoBoton
    );
    select_categoria_equipo_actualizar.addEventListener(
        "change",
        actualizarEstadoBoton
    );

    async function cargarCategorias() {
        try {
            const respuesta = await fetch("/asignaciones/categoria_registrados/");
            if (!respuesta.ok) {
                throw new Error("No fue posible cargar las categorías.");
            }

            const resultado = await respuesta.json();
            if (!Array.isArray(resultado)) {
                throw new Error("La respuesta de categorías no es válida.");
            }

            select_categoria_equipo_actualizar.innerHTML =
                '<option value="">Seleccione una categoría</option>';
            select_categorias_registradas.innerHTML =
                '<option value="">Todos los catálogos</option>';

            resultado.forEach(categoria => {
                [select_categoria_equipo_actualizar, select_categorias_registradas]
                    .forEach(select => {
                        const opcion = document.createElement("option");
                        opcion.value = categoria.id_categoria;
                        opcion.textContent = categoria.nombre;
                        select.append(opcion);
                    });
            });

            return true;
        } catch (error) {
            console.error("Error al cargar categorías:", error);
            await Swal.fire({
                title: "Error",
                text: "No fue posible cargar las categorías de equipos.",
                icon: "error"
            });
            return false;
        }
    }
    const categorias_cargadas = cargarCategorias();

    formulario_actualizar.addEventListener("submit", async (e) => {
        e.preventDefault();

        actualizarEstadoBoton();
        if (!input_id_equipo.value || !formulario_actualizar.reportValidity()) {
            return;
        }

        try {
            const formulario = new FormData(formulario_actualizar);

            const respuesta = await fetch("/asignaciones/actualizacion_equipos/", {
                method: "POST",
                body: formulario
            });
            const resultado = await respuesta.json();

            await Swal.fire({
                title: resultado.title,
                text: resultado.descripcion,
                icon: resultado.icon
            });

            if (!respuesta.ok || resultado.estado !== "exito") {
                return;
            }

            formulario_actualizar.reset();
            input_id_equipo.value = "";
            input_cantidad_disponible_actualizar.setCustomValidity("");
            input_cantidad_disponible_actualizar.classList.remove(
                "is-invalid",
                "is-valid"
            );
            contenedor_msg_cantidad_actualizar.textContent = "";
            contenedor_msg_cantidad_actualizar.classList.remove(
                "error",
                "exito"
            );
            contador_observacion_actualizar.textContent = "0";
            delete input_cantidad_disponible_actualizar.dataset.entregada;
            bloquearFormularioActualizar(true);
            await equipos_registrados();
        } catch (error) {
            console.error("Error al actualizar el equipo:", error);
            await Swal.fire({
                title: "Error de conexión",
                text: "No fue posible actualizar los datos del equipo.",
                icon: "error"
            });
        }
    });

    // Visualizar los equipos

    function mostrar_equipos_pagina() {
        const total_paginas = Math.max(
            1,
            Math.ceil(lista_equipos_registrados.length / FILAS_POR_PAGINA)
        );

        if (pagina_actual > total_paginas) {
            pagina_actual = total_paginas;
        }

        const inicio = (pagina_actual - 1) * FILAS_POR_PAGINA;

        const equipos_pagina = lista_equipos_registrados.slice(
            inicio,
            inicio + FILAS_POR_PAGINA
        );

        contenedor_equipos.innerHTML = "";

        if (equipos_pagina.length === 0) {
            contenedor_equipos.innerHTML = `
                <tr>
                    <td colspan="4" class="texto_sin_registros">
                        No hay equipos registrados.
                    </td>
                </tr>
            `;
        } else {
            equipos_pagina.forEach((equipo, index) => {
                contenedor_equipos.innerHTML += `
                    <tr class="fila_equipo" data-codigo="${equipo.codigo}">
                        <td>${inicio + index + 1}</td>
                        <td>${equipo.nombre}</td>
                        <td>${equipo.codigo}</td>
                        <td class="acciones_equipo">
                            <button
                                type="button"
                                class="btn_accion btn_actualizar_equipo"
                                data-codigo="${equipo.codigo}"
                                title="Actualizar equipo"
                                aria-label="Actualizar equipo ${equipo.nombre}">
                                Actualizar
                            </button>

                            <button
                                type="button"
                                class="btn_accion btn_detalle_equipo"
                                data-codigo="${equipo.codigo}"
                                title="Ver detalle del equipo"
                                aria-label="Ver detalle de ${equipo.nombre}">
                                Detalle
                            </button>
                        </td>
                    </tr>
                `;
            });
        }

        boton_retroceder.disabled = pagina_actual <= 1;
        boton_avanzar.disabled = pagina_actual >= total_paginas;
    }

    async function equipos_registrados() {
        if (consulta_equipos_activa) {
            consulta_equipos_activa.abort();
        }

        const consultaActual = new AbortController();
        consulta_equipos_activa = consultaActual;

        try {
            const formulario = new FormData();

            formulario.append("codigo", input_codigo_equipo.value.trim());
            formulario.append("categoria", select_categorias_registradas.value);

            const respuesta = await fetch("/asignaciones/visualizacion_equipos/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken
                },
                body: formulario,
                signal: consultaActual.signal
            });

            const resultado = await respuesta.json();

            if (!respuesta.ok || !Array.isArray(resultado)) {
                lista_equipos_registrados = [];
                pagina_actual = 1;

                mostrar_equipos_pagina();

                if (resultado.estado === "fallo") {
                    await Swal.fire({
                        title: resultado.title || "Error",
                        text: resultado.descripcion || "No fue posible consultar los equipos.",
                        icon: resultado.icon || "error"
                    });
                }

                return;
            }

            lista_equipos_registrados = resultado;
            pagina_actual = 1;

            mostrar_equipos_pagina();

        } catch (error) {
            if (error.name !== "AbortError") {
                console.error("Error al consultar los equipos:", error);
            }
        } finally {
            if (consulta_equipos_activa === consultaActual) {
                consulta_equipos_activa = null;
            }
        }
    }

    boton_retroceder.addEventListener("click", () => {
        if (pagina_actual > 1) {
            pagina_actual--;
            mostrar_equipos_pagina();
        }
    });

    boton_avanzar.addEventListener("click", () => {
        const total_paginas = Math.max(
            1,
            Math.ceil(lista_equipos_registrados.length / FILAS_POR_PAGINA)
        );

        if (pagina_actual < total_paginas) {
            pagina_actual++;
            mostrar_equipos_pagina();
        }
    });

    input_codigo_equipo.addEventListener("input", equipos_registrados);

    select_categorias_registradas.addEventListener("change", equipos_registrados);
    formulario_busqueda_equipos.addEventListener("submit", e => {
        e.preventDefault();
        equipos_registrados();
    });

    equipos_registrados();

    // Buscar datos del equipo dependiendo el enfoque

    contenedor_equipos.addEventListener("click", async (e) => {
        const boton = e.target.closest(".btn_accion");

        if (!boton) return;

        const codigo = boton.dataset.codigo;

        if (!codigo) return;

        if (boton.classList.contains("btn_actualizar_equipo")) {
            await buscar_datos_actualizar(codigo);
        }

        if (boton.classList.contains("btn_detalle_equipo")) {
            await buscar_datos_detalle(codigo);
        }
    });
    
    async function buscar_datos_actualizar(codigo) {
        try {
            if (!(await categorias_cargadas)) {
                return;
            }

            const formulario = new FormData();
            formulario.append("codigo_equipo", codigo);

            const respuesta = await fetch("/asignaciones/buscar_equipos/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken
                },
                body: formulario
            });

            const resultado = await respuesta.json();

            if (!respuesta.ok || resultado.estado === "fallo") {
                await Swal.fire({
                    title: resultado.title || "Error",
                    text: resultado.descripcion || "No fue posible obtener los datos del equipo.",
                    icon: resultado.icon || "error"
                });
                return;
            }

            const equipo = resultado.equipo;

            await Swal.fire({
                title: "Datos encontrados",
                text: "Los datos del equipo fueron encontrados correctamente.",
                icon: "success"
            });

            bloquearFormularioActualizar(false);

            input_id_equipo.value = equipo.id_equipo;
            input_nombre_equipo_actualizar.value = equipo.nombre;
            textarea_observacion_equipo_actualizar.value = equipo.observacion;

            actualizarContador(
                textarea_observacion_equipo_actualizar,
                contador_observacion_actualizar
            );

            const cantidadTotal = (
                Number(equipo.cantidad_disponible)
                + Number(equipo.cantidad_entregada)
            );
            input_cantidad_disponible_actualizar.value = cantidadTotal;

            input_cantidad_disponible_actualizar.dataset.entregada = equipo.cantidad_entregada;
            select_categoria_equipo_actualizar.value = String(
                equipo.id_categoria
            );
            actualizarEstadoBoton();

        } catch (error) {
            console.error("Error al buscar equipo para actualizar:", error);

            await Swal.fire({
                title: "Error de conexión",
                text: "No fue posible consultar la información del equipo.",
                icon: "error"
            });
        }
    }
    
    async function buscar_datos_detalle(codigo) {
        try {
            const formulario = new FormData();
            formulario.append("codigo_equipo", codigo);

            const respuesta = await fetch("/asignaciones/buscar_equipos/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken
                },
                body: formulario
            });

            const resultado = await respuesta.json();

            if (!respuesta.ok || resultado.estado === "fallo") {
                await Swal.fire({
                    title: resultado.title || "Error",
                    text: resultado.descripcion || "No fue posible obtener los datos del equipo.",
                    icon: resultado.icon || "error"
                });
                return;
            }

            const equipo = resultado.equipo;

            input_id_equipo_detalle.value = equipo.id_equipo;
            input_nombre_equipo_visualizar.value = equipo.nombre;
            input_codigo_equipo_visualizar.value = equipo.codigo;
            textarea_observacion_equipo_visualizar.value = equipo.observacion;
            input_cantidad_disponible_equipo_visualizar.value = `${equipo.cantidad_disponible} unidades disponibles`;
            input_categoria_equipo_visualizar.value = equipo.categoria;
            input_fecha_registr_visualizar.value = equipo.fecha_registro;

            dialogo_equipo.showModal();

        } catch (error) {
            console.error("Error al buscar detalle del equipo:", error);

            await Swal.fire({
                title: "Error de conexión",
                text: "No fue posible consultar el detalle del equipo.",
                icon: "error"
            });
        }
    }

    btn_cerrar.addEventListener("click", () => {
        dialogo_equipo.close();
    });

});