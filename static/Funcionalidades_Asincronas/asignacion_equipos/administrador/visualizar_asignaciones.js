document.addEventListener("DOMContentLoaded", () => {

    const select_nacionalidad_busqueda = document.getElementById("nacionalidad");
    const input_cedula_busqueda = document.getElementById("cedula_identidad");
    const select_categoria_equipo = document.getElementById("categorias_registradas");

    const contenedor_asignaciones = document.getElementById("registros_asignaciones");

    const dialogo_asignacion = document.getElementById("dialogo_asignacion");
    const btn_cerrar_asignacion = document.getElementById("btn_cerrar_asignacion");

    const input_id_asignacion = document.getElementById("id_asignacion");
    const input_empleado_asignado = document.getElementById("empleado_asignado");
    const input_cedula_empleado = document.getElementById("cedula_empleado");
    const input_nombre_equipo = document.getElementById("nombre_equipo");
    const input_codigo_equipo = document.getElementById("codigo_equipo");
    const input_categoria_equipo = document.getElementById("categoria_equipo");
    const input_fecha_entrega = document.getElementById("fecha_entrega");
    const input_fecha_devolucion = document.getElementById("fecha_devolucion");
    const input_cantidad_devuelto = document.getElementById("cantidad_devuelto");
    const input_cantidad_equipo = document.getElementById("cantidad_equipo");
    const input_estado_equipo = document.getElementById("estado_equipo");

    const btn_detalle_asignado_pdf = document.getElementById("detalle_asignado_pdf");
    const btn_lista_asignacion_pdf = document.getElementById("lista_asignacion_pdf");

    const btn_retroceder = document.querySelector(".botones_navegacion .btn_retroceder");
    const btn_avanzar = document.querySelector(".botones_navegacion .btn_avanzar");

    const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;

    let cedula = "", nacionalidad = "", categoria = "";
    let asignaciones_recibidas = [];
    let pagina_actual = 1;
    const filas_por_pagina = 10;

    configurarCedula(input_cedula_busqueda, select_nacionalidad_busqueda);

    async function categoria_equipo_registrados() {
        try {
            const respuesta = await fetch("/asignaciones/categoria_registrados/");
            const resultado = await respuesta.json();
            console.log(resultado);

            select_categoria_equipo.innerHTML = "<option value='' selected>Seleccione la categoria</option>";

            resultado.forEach(categoria => {
                const option_categoria = document.createElement("option");
                option_categoria.value = categoria.id_categoria;
                option_categoria.textContent = categoria.nombre;
                select_categoria_equipo.append(option_categoria);
            });
        } catch (error) {
            console.error(error);
        }
    }
    categoria_equipo_registrados();

    select_nacionalidad_busqueda.addEventListener("change", async () => {
        nacionalidad = select_nacionalidad_busqueda.value;

        await asignaciones_empleados()();
    });

    input_cedula_busqueda.addEventListener("input", async () => {
        cedula = input_cedula_busqueda.value;

        await asignaciones_empleados()();
    });

    select_categoria_equipo.addEventListener("change", async () => {
        categoria = select_categoria_equipo.value;

        await asignaciones_empleados()();
    });


    function mostrarAsignaciones() {
        contenedor_asignaciones.innerHTML = "";

        const inicio = (pagina_actual - 1) * filas_por_pagina;
        const final = inicio + filas_por_pagina;

        const asignaciones_pagina = asignaciones_recibidas.slice(inicio, final);

        if (asignaciones_pagina.length === 0) {
            contenedor_asignaciones.innerHTML = `
                <tr>
                    <td colspan="7" class="texto_sin_registros">
                        No existen asignaciones de equipos registradas.
                    </td>
                </tr>
            `;

            actualizarBotones();
            return;
        }

        asignaciones_pagina.forEach((asignacion, index) => {
            const fila = document.createElement("tr");

            fila.dataset.id_asignacion = asignacion.id_asignacion;

            fila.innerHTML = `
                <td>${inicio + index + 1}</td>
                <td>${asignacion.nombres} ${asignacion.apellidos}</td>
                <td>${asignacion.equipo}</td>
                <td>${asignacion.cantidad_asignada}</td>
                <td>${asignacion.cantidad_devuelta}</td>
                <td>${asignacion.fecha_entrega}</td>
                <td>${asignacion.estado}</td>
            `;

            contenedor_asignaciones.appendChild(fila);
        });

        actualizarBotones();
    }

    function actualizarBotones() {
        const total_paginas = Math.ceil(asignaciones_recibidas.length / filas_por_pagina);

        btn_retroceder.disabled = pagina_actual === 1;

        btn_avanzar.disabled = pagina_actual >= total_paginas;
    }

    btn_retroceder.addEventListener("click", () => {
        if (pagina_actual > 1) {
            pagina_actual--;
            mostrarAsignaciones();
        }
    });

    btn_avanzar.addEventListener("click", () => {
        const total_paginas = Math.ceil(asignaciones_recibidas.length / filas_por_pagina);

        if (pagina_actual < total_paginas) {
            pagina_actual++;
            mostrarAsignaciones();
        }
    });

    async function asignaciones_empleados() {
        try {
            const formulario = new FormData();
            formulario.append("nacionalidad", nacionalidad);
            formulario.append("cedula_identidad", cedula);
            formulario.append("categorias_registradas", categoria);

            const respuesta = await fetch("/asignaciones/asignaciones_equipos_admin/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            if (resultado.estado === "fallo") {
                await Swal.fire({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon
                });
                return;
            }

            if (resultado.estado === "vacio" || !resultado.asignaciones?.length) {
                asignaciones_recibidas = [];
                pagina_actual = 1;
                mostrarAsignaciones();
                return;
            }

            asignaciones_recibidas = resultado.asignaciones;
            pagina_actual = 1;

            mostrarAsignaciones();
        } catch (error) {
            console.error(error);
        }
    }
    asignaciones_empleados();



    contenedor_asignaciones.addEventListener("click", async (e) => {
        const fila = e.target.closest("tr");

        const id = fila.dataset.id_asignacion;

        try {
            const formulario = new FormData();
            formulario.append("id_asignacion", id);

            const respuesta = await fetch("/asignaciones/datos_asignacion_admin/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            if (resultado.estado === "fallo") {
                await Swal.fire({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon
                });
                return;
            }

            input_id_asignacion.value = resultado.asignacion.id_asignacion;
            input_empleado_asignado.value = resultado.asignacion.empleado;
            input_cedula_empleado.value = resultado.asignacion.cedula_empleado;
            input_nombre_equipo.value = resultado.asignacion.nombre_equipo;
            input_codigo_equipo.value = resultado.asignacion.codigo_equipo;
            input_categoria_equipo.value = resultado.asignacion.categoria_equipo;
            input_fecha_entrega.value = resultado.asignacion.fecha_entrega;
            input_fecha_devolucion.value = resultado.asignacion.fecha_devolucion;
            input_cantidad_devuelto.value = `${resultado.asignacion.cantidad_devuelto} unidad(es)`;
            input_cantidad_equipo.value = `${resultado.asignacion.cantidad_equipo} unidad(es)`;
            input_estado_equipo.value = resultado.asignacion.estado_equipo;

            dialogo_asignacion.showModal();
        } catch (error) {
            console.error(error);
        }
    });

    btn_cerrar_asignacion.addEventListener("click", () => {
        dialogo_asignacion.close();
    });

    btn_lista_asignacion_pdf.addEventListener("click", async () => {
        try {
            const datos = new FormData();
            datos.append("csrfmiddlewaretoken", csrfToken);
            datos.append("categorias_registradas", select_categoria_equipo.value);
            datos.append("nacionalidad", select_nacionalidad_busqueda.value);
            datos.append("cedula_identidad", input_cedula_busqueda.value.trim());

            const respuesta = await fetch("/asignaciones/lista_asignaciones_pdf_admin/", {
                method: "POST",
                body: datos,
            });
            const tipoContenido = respuesta.headers.get("content-type") || "";

            if (tipoContenido.includes("application/json")) {
                const resultado = await respuesta.json();

                Swal.fire({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon,
                    confirmButtonColor: "#00445F"
                });
                return;
            }

            if (!tipoContenido.includes("application/pdf")) {
                Swal.fire({
                    title: "Error al generar el reporte",
                    text: "No se pudo generar el archivo PDF.",
                    icon: "error",
                    confirmButtonColor: "#00445F"
                });

                return;
            }

            const archivo = await respuesta.blob();
            const url = URL.createObjectURL(archivo);
            const ventana = window.open(url, "_blank");

            if (!ventana) {
                URL.revokeObjectURL(url);

                Swal.fire({
                    title: "Ventana bloqueada",
                    text: (
                        "Permite las ventanas emergentes para "
                        + "poder visualizar el reporte PDF."
                    ),
                    icon: "warning",
                    confirmButtonColor: "#00445F"
                });

                return;
            }

            ventana.addEventListener("load", () => {
                URL.revokeObjectURL(url);
            }, { once: true });

        } catch (error) {
            console.error(error);
        }
    });

    btn_detalle_asignado_pdf.addEventListener("click", async () => {
        try {
            const datos = new FormData();
            datos.append("csrfmiddlewaretoken", csrfToken);
            datos.append("id_asignacion", input_id_asignacion.value);

            const respuesta = await fetch("/asignaciones/detalle_asignacion_pdf_admin/", {
                method: "POST",
                body: datos,
            });
            const tipoContenido = respuesta.headers.get("content-type") || "";

            if (tipoContenido.includes("application/json")) {
                const resultado = await respuesta.json();

                Swal.fire({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon,
                    confirmButtonColor: "#00445F"
                });
                return;
            }

            if (!tipoContenido.includes("application/pdf")) {
                Swal.fire({
                    title: "Error al generar el reporte",
                    text: "No se pudo generar el archivo PDF.",
                    icon: "error",
                    confirmButtonColor: "#00445F"
                });

                return;
            }

            const archivo = await respuesta.blob();
            const url = URL.createObjectURL(archivo);
            const ventana = window.open(url, "_blank");

            if (!ventana) {
                URL.revokeObjectURL(url);

                Swal.fire({
                    title: "Ventana bloqueada",
                    text: (
                        "Permite las ventanas emergentes para "
                        + "poder visualizar el reporte PDF."
                    ),
                    icon: "warning",
                    confirmButtonColor: "#00445F"
                });

                return;
            }

            ventana.addEventListener("load", () => {
                URL.revokeObjectURL(url);
            }, { once: true });

        } catch (error) {
            console.error(error);
        }
    });

});