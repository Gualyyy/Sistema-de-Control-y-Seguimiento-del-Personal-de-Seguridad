document.addEventListener("DOMContentLoaded", () => {

    const select_nacionalidad_busqueda = document.getElementById("nacionalidad");
    const input_cedula_busqueda = document.getElementById("cedula_identidad");
    const select_categoria_equipo = document.getElementById("categorias_registradas");

    const btn_lista_asignacion_pdf = document.getElementById("lista_asignacion_pdf");
    const btn_equipo_asignado_pdf = document.getElementById("equipo_asignado_pdf");

    const contenedor_asignaciones = document.getElementById("registros_asignaciones");

    const dialogo_asignacion = document.getElementById("dialogo_asignacion");
    const btn_cerrar_asignacion = document.getElementById("btn_cerrar_asignacion");

    const dialogo_devolucion = document.getElementById("dialogo_devolucion");
    const btn_cerrar_devolucion = document.getElementById("btn_cerrar_devolucion");

    const input_id_asignacion_v = document.getElementById("id_asignacion_visualizar");
    const empleado_asignado_v = document.getElementById("empleado_asignado_visualizar");
    const cedula_empleado_v = document.getElementById("cedula_empleado_visualizar");
    const nombre_equipo_v = document.getElementById("nombre_equipo_visualizar");
    const codigo_equipo_v = document.getElementById("codigo_equipo_visualizar");
    const categoria_equipo_v = document.getElementById("categoria_equipo_visualizar");
    const fecha_entrega_v = document.getElementById("fecha_entrega_visualizar");
    const fecha_devolucion_v = document.getElementById("fecha_devolucion_visualizar");
    const cantidad_devuelto_v = document.getElementById("cantidad_devuelto_visualizar");
    const cantidad_equipo_v = document.getElementById("cantidad_equipo_visualizar");
    const estado_equipo_v = document.getElementById("estado_equipo_visualizar");

    const formulario_devolucion = document.getElementById("formulario_devolucion");

    const input_id_asignacion_d = document.getElementById("id_asignacion_devolucion");
    const input_ci_usuario_d = document.getElementById("ci_usuario_devolucion");

    const input_empleado_asignado_d = document.getElementById("empleado_asignado_devolucion");
    const input_equipo_asignado_d = document.getElementById("equipo_asignado_devolucion");
    const input_cantidad_asignada_d = document.getElementById("cantidad_asignada_devolucion");
    const select_tipos_d = document.getElementById("tipos_devolucion");
    const select_estados_d = document.getElementById("estados_devolucion");
    const input_cantidad_d = document.getElementById("cantidad_devolver");
    const input_cantidad_devuelto_d = document.getElementById("cantidad_equipo_devuelto");
    const input_cantidad_posee_d = document.getElementById("cantidad_posee");

    const contenedor_msg_cantidad = document.getElementById("contenedor_msg_cantidad");

    const contenedor_estado_devolucion = document.getElementById("contenedor_estado_devolucion");

    const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;

    const btn_registro = document.getElementById("btn_registro");

    let cedula = "", nacionalidad = "", categoria = "", asignacion = "";
    let descripcion_cantidad_devuelto = "";

    btn_registro.disabled = true;

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

        await datos_asignados();
    });

    input_cedula_busqueda.addEventListener("input", async () => {
        cedula = input_cedula_busqueda.value;

        await datos_asignados();
    });

    select_categoria_equipo.addEventListener("change", async () => {
        categoria = select_categoria_equipo.value;

        await datos_asignados();
    });

    async function datos_asignados() {
        try {
            const formulario = new FormData();
            formulario.append("nacionalidad", nacionalidad);
            formulario.append("cedula", cedula);
            formulario.append("categoria", categoria);

            const respuesta = await fetch("/asignaciones/gestionar_asignaciones_equipos/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            if (resultado.estado == "fallo") {
                await Swal.fire({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon,
                });
                return;
            }

            contenedor_asignaciones.innerHTML = "";
            resultado.forEach((asignacion, index) => {
                let accion;

                if (asignacion.estado === "Asignado" || asignacion.estado === "Parcial") {
                    accion = `
                        <button 
                            type="button"
                            class="btn_bloquear_tabla"
                            data-id="${asignacion.id}">
                            Devolución
                        </button>
                    `;
                } else {
                    accion = `
                        <span class="estado_asignacion estado_${asignacion.estado.toLowerCase()}">
                            ${asignacion.estado.replace("_", " ")}
                        </span>
                    `;
                }

                contenedor_asignaciones.innerHTML += `
                    <tr data-id_asignacion="${asignacion.id}">
                        <td>${index + 1}</td>
                        <td>${asignacion.empleado}</td>
                        <td>${asignacion.equipo}</td>
                        <td>${asignacion.cantidad_asignada}</td>
                        <td>${asignacion.fecha_entrega}</td>
                        <td>${accion}</td>
                    </tr>
                `;
            });
        } catch (error) {
            console.error(error);
        }
    }
    datos_asignados();

    contenedor_asignaciones.addEventListener("click", async (e) => {
        const button = e.target.closest("button");
        if (button) {
            const fila = button.closest("tr");
            asignacion = fila.dataset.id_asignacion;

            await devolucion_equipo();
            return;
        }

        const fila = e.target.closest("tr");
        if (fila) {
            asignacion = fila.dataset.id_asignacion;

            await datos_asignacion();
        }
    });

    async function datos_asignacion() {
        try {
            const formulario = new FormData();
            formulario.append("id_asignacion", asignacion);

            const respuesta = await fetch("/asignaciones/buscar_datos_asignacion_equipo/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            dialogo_asignacion.showModal();

            input_id_asignacion_v.value = resultado.datos.id;
            empleado_asignado_v.value = resultado.datos.empleado;
            cedula_empleado_v.value = resultado.datos.cedula;
            nombre_equipo_v.value = resultado.datos.equipo;
            codigo_equipo_v.value = resultado.datos.codigo;
            fecha_entrega_v.value = resultado.datos.fecha_entrega;

            if (resultado.fecha_devolucion != "") {
                fecha_devolucion_v.value = resultado.datos.fecha_devolucion;
            } else {
                fecha_devolucion_v.value = "N/A";
            }

            if (resultado.cantidad_devuelta > 0) {
                const cantidad = resultado.cantidad_devuelta;

                descripcion_cantidad_devuelto = `Devuelto: ${cantidad} ${cantidad === 1 ? "unidad" : "unidades"}.`;
            } else {
                descripcion_cantidad_devuelto = "No ha devuelto ninguna unidad.";
            }

            cantidad_devuelto_v.value = descripcion_cantidad_devuelto;

            const cantidad = resultado.datos.cantidad_asignada;

            input_cantidad_asignada_d.value = `${cantidad} ${cantidad === 1 ? "unidad" : "unidades"}`;

            cantidad_equipo_v.value = resultado.datos.estado === "Error Humano" ? "Se devolvió la cantidad asignada"
                : `${resultado.datos.cantidad_asignada} ${resultado.datos.cantidad_asignada === 1 ? "unidad" : "unidades"}`;
            estado_equipo_v.value = resultado.datos.estado;
            categoria_equipo_v.value = resultado.datos.categoria;
        } catch (error) {
            console.error(error);
        }
    }

    async function devolucion_equipo() {
        try {
            const formulario = new FormData();
            formulario.append("id_asignacion", asignacion);

            const respuesta = await fetch("/asignaciones/buscar_equipo_devolver/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken
                },
                body: formulario
            });

            const resultado = await respuesta.json();
            console.log(resultado);

            if (resultado.estado !== "exito") {
                await Swal.fire({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon
                });
                return;
            }

            const datos = resultado.asignacion;

            input_id_asignacion_d.value = datos.id;
            input_ci_usuario_d.value = datos.cedula;
            input_empleado_asignado_d.value = `${datos.nombres} ${datos.apellidos}`;
            input_equipo_asignado_d.value = datos.equipo;

            const cantidad_asignada = Number(datos.cantidad_asignada);
            const cantidad_devuelta = Number(datos.cantidad_devuelta);
            const cantidad_pendiente = Number(datos.cantidad_pendiente);

            input_cantidad_asignada_d.value = `${cantidad_asignada} ${cantidad_asignada === 1 ? "unidad" : "unidades"}`;

            input_cantidad_devuelto_d.value = cantidad_devuelta > 0
                ? `Devuelto: ${cantidad_devuelta} ${cantidad_devuelta === 1 ? "unidad" : "unidades"}.`
                : "No ha devuelto ninguna unidad.";

            input_cantidad_posee_d.value = `${cantidad_pendiente} ${cantidad_pendiente === 1 ? "unidad" : "unidades"}`;

            input_cantidad_asignada_d.dataset.cantidad = cantidad_pendiente;

            input_cantidad_d.max = cantidad_pendiente;
            input_cantidad_d.value = "";
            input_cantidad_d.readOnly = false;

            select_tipos_d.value = "";
            restablecer_estados();

            contenedor_estado_devolucion.hidden = false;

            estados_devolucion.required = true;

            contenedor_msg_cantidad.textContent = "";
            contenedor_msg_cantidad.classList.remove("error", "exito", "espera");

            dialogo_devolucion.showModal();

        } catch (error) {
            console.error(error);
        }
    }

    formulario_devolucion.addEventListener("submit", async (e) => {
        e.preventDefault();

        if (!formulario_devolucion.reportValidity()) {
            return;
        }

        const boton_submit = formulario_devolucion.querySelector(
            'button[type="submit"]'
        );

        if (boton_submit.disabled) {
            return;
        }

        boton_submit.disabled = true;

        try {
            const formulario = new FormData(formulario_devolucion);

            if (select_tipos_d.value === "CORRECCION") {
                formulario.set("estados_devolucion", "BUEN_ESTADO");
            }

            mostrar_mensaje_dialogo(
                "contenedor_mensajes_devolucion",
                "Procesando operación...",
                "informacion"
            );

            const respuesta = await fetch("/asignaciones/devolucion_equipos_asignado/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            const tipos_mensaje = {
                success: "exito",
                warning: "advertencia",
                error: "error",
                info: "informacion"
            };

            const tipo_mensaje = tipos_mensaje[resultado.icon] || "error";

            await mostrar_mensaje_temporal(
                "contenedor_mensajes_devolucion",
                resultado.descripcion || "No se pudo completar la operación.",
                tipo_mensaje,
                4
            );

            ocultar_mensaje_dialogo("contenedor_mensajes_devolucion");

            dialogo_devolucion.close();
            formulario_devolucion.reset();

            contenedor_msg_cantidad.textContent = "";
            contenedor_msg_cantidad.classList.remove(
                "error",
                "exito",
                "espera"
            );

            await datos_asignados();

        } catch (error) {
            console.error(error);
            ocultar_mensaje_dialogo("contenedor_mensajes_devolucion");
        } finally {
            boton_submit.disabled = false;
        }
    });

    function restablecer_estados() {
        select_estados_d.innerHTML = `
            <option value="" selected>Seleccione el Estado de la Devolución</option>
            <option value="BUEN_ESTADO">Buen estado</option>
            <option value="DETERIORADO">Deteriorado</option>
            <option value="DAÑADO">Dañado</option>
        `;

        select_estados_d.disabled = false;
    }

    function validar_cantidad_devolucion() {
        const tipo = select_tipos_d.value;
        const cantidad_pendiente = Number(input_cantidad_asignada_d.dataset.cantidad);

        const valor = input_cantidad_d.value.trim();
        const cantidad = Number(valor);

        contenedor_msg_cantidad.classList.remove("error", "exito", "espera");

        // Sin tipo de devolución o sin cantidad
        if (tipo === "" || valor === "") {
            contenedor_msg_cantidad.textContent = "";
            btn_registro.disabled = true;
            return;
        }

        // Verificar que exista una cantidad pendiente válida
        if (!Number.isInteger(cantidad_pendiente) || cantidad_pendiente <= 0) {
            contenedor_msg_cantidad.textContent = "No se pudo determinar la cantidad pendiente.";

            contenedor_msg_cantidad.classList.add("error");
            btn_registro.disabled = true;
            return;
        }

        // La cantidad debe ser un entero positivo
        if (!Number.isInteger(cantidad) || cantidad <= 0) {
            contenedor_msg_cantidad.textContent = "La cantidad debe ser un número mayor que cero.";

            contenedor_msg_cantidad.classList.add("error");
            btn_registro.disabled = true;
            return;
        }

        // No permitir devolver más de lo pendiente
        if (cantidad > cantidad_pendiente) {
            contenedor_msg_cantidad.textContent = `La cantidad máxima que puede devolver es ${cantidad_pendiente}.`;

            contenedor_msg_cantidad.classList.add("error");
            btn_registro.disabled = true;
            return;
        }

        // Cantidad válida
        contenedor_msg_cantidad.textContent = "Cantidad válida.";
        contenedor_msg_cantidad.classList.add("exito");

        btn_registro.disabled = false;
    }

    select_tipos_d.addEventListener("change", () => {
        const tipo = select_tipos_d.value;

        contenedor_msg_cantidad.textContent = "";
        contenedor_msg_cantidad.classList.remove(
            "error",
            "exito",
            "espera"
        );

        btn_registro.disabled = true;

        if (tipo === "DEVOLUCION") {
            contenedor_estado_devolucion.hidden = false;

            select_estados_d.disabled = false;
            select_estados_d.required = true;

            restablecer_estados();
            select_estados_d.value = "";

            input_cantidad_d.readOnly = false;
            input_cantidad_d.value = "";
            input_cantidad_d.max = input_cantidad_asignada_d.dataset.cantidad || "";

        } else if (tipo === "CORRECCION") {
            contenedor_estado_devolucion.hidden = false;

            select_estados_d.required = false;

            restablecer_estados();
            select_estados_d.value = "BUEN_ESTADO";
            select_estados_d.disabled = true;

            input_cantidad_d.readOnly = true;
            input_cantidad_d.value = input_cantidad_asignada_d.dataset.cantidad || "";

        } else {
            contenedor_estado_devolucion.hidden = false;

            select_estados_d.disabled = false;
            select_estados_d.required = true;

            restablecer_estados();
            select_estados_d.value = "";

            input_cantidad_d.readOnly = false;
            input_cantidad_d.value = "";
            input_cantidad_d.max = input_cantidad_asignada_d.dataset.cantidad || "";
        }

        validar_cantidad_devolucion();
    });

    input_cantidad_d.addEventListener("input", () => {
        if (!input_cantidad_d.readOnly) {
            input_cantidad_d.value =
                input_cantidad_d.value.replace(/\D/g, "");
        }

        validar_cantidad_devolucion();
    });

    // 

    function mostrar_mensaje_dialogo(id_contenedor, mensaje, tipo = "informacion") {
        const contenedor = document.getElementById(id_contenedor);

        if (!contenedor) return;

        contenedor.className = `contenedor_mensajes ${tipo}`;
        contenedor.replaceChildren();

        const reloj = document.createElement("i");
        reloj.className = "fa-solid fa-hourglass-half reloj_procesamiento";
        reloj.setAttribute("aria-hidden", "true");

        const texto = document.createElement("span");
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

            const texto = document.createElement("span");
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

    function ocultar_mensaje_dialogo(id_contenedor) {
        const contenedor = document.getElementById(id_contenedor);

        if (!contenedor) return;

        contenedor.hidden = true;
        contenedor.replaceChildren();
    }


    btn_cerrar_devolucion.addEventListener("click", () => {
        dialogo_devolucion.close();
    });

    btn_cerrar_asignacion.addEventListener("click", () => {
        dialogo_asignacion.close();
    });


    btn_lista_asignacion_pdf.addEventListener("click", async () => {
        const categoria = select_categoria_equipo.value;

        try {
            const formulario = new FormData();
            formulario.append("categoria", categoria);

            const respuesta = await fetch("/asignaciones/lista_asignaciones_pdf/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken
                },
                body: formulario
            });

            const tipoContenido = respuesta.headers.get("content-type") || "";

            if (tipoContenido.includes("application/pdf")) {
                const blob = await respuesta.blob();
                const url = URL.createObjectURL(blob);
                window.open(url, "_blank");

                setTimeout(() => URL.revokeObjectURL(url), 60000);
                return;
            }

            const resultado = await respuesta.json();

            Swal.fire({
                icon: resultado.icon || "warning",
                title: resultado.title || "Advertencia",
                text: resultado.descripcion || "No se pudo generar el reporte.",
                confirmButtonText: "Entendido"
            });

        } catch (error) {
            console.error(error);
        }
    });

    btn_equipo_asignado_pdf.addEventListener("click", async () => {
        try {
            const formulario = new FormData();
            formulario.append("id_asignacion", input_id_asignacion_v.value);

            const respuesta = await fetch("/asignaciones/datos_asignacion_pdf/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken
                },
                body: formulario
            });

            const tipo_contenido = respuesta.headers.get("content-type") || "";

            if (tipo_contenido.includes("application/json")) {
                const resultado = await respuesta.json();

                Swal.fire({
                    icon: resultado.icon || "error",
                    title: resultado.title || "Error",
                    text: resultado.descripcion || "No se pudo generar el reporte."
                });
                return;
            }

            if (!respuesta.ok || !tipo_contenido.includes("application/pdf")) {
                Swal.fire({
                    icon: "error",
                    title: "Error",
                    text: "No se pudo generar el PDF de la asignación."
                });
                return;
            }

            const pdf = await respuesta.blob();
            const url_pdf = URL.createObjectURL(pdf);

            window.open(url_pdf, "_blank");

            setTimeout(() => URL.revokeObjectURL(url_pdf), 60000);

        } catch (error) {
            console.error(error);
        }
    });

});