document.addEventListener("DOMContentLoaded", () => {

    const select_categoria_gastos = document.getElementById("categoria_gastos");
    const contenedor_gastos = document.getElementById("contenedor_gastos");

    const formulario_actualizar = document.getElementById("formulario_actualizar");

    const btn_ret = document.querySelector(".btn_retroceder");
    const btn_av = document.querySelector(".btn_avanzar");

    const input_id_gasto = document.getElementById("id_gasto");

    const contador_observacion = document.getElementById("contador_observacion");

    const select_nueva_categoria = document.getElementById("nueva_categoria");
    const input_descripcion = document.getElementById("descripcion");
    const input_monto_gasto = document.getElementById("monto_gasto");
    const input_fecha_gasto = document.getElementById("fecha_gasto");
    const select_es_recurrente = document.getElementById("es_recurrente");
    const contenedor_frecuencia = document.getElementById("contenedor_frecuencia");
    const select_frecuencia = document.getElementById("frecuencia");
    const input_referencia = document.getElementById("referencia");
    const textarea_observacion = document.getElementById("observacion");

    const dialogo_gasto = document.getElementById("dialogo_gasto");
    const btn_cerrar = document.getElementById("btn_cerrar");
    const campos_visualizacion = {
        categoria: document.getElementById("gasto_visualizar_categoria"),
        descripcion: document.getElementById("gasto_visualizar_descripcion"),
        monto: document.getElementById("gasto_visualizar_monto"),
        fecha: document.getElementById("gasto_visualizar_fecha"),
        estado: document.getElementById("gasto_visualizar_estado"),
        recurrente: document.getElementById("gasto_visualizar_recurrente"),
        frecuencia: document.getElementById("gasto_visualizar_frecuencia"),
        referencia: document.getElementById("gasto_visualizar_referencia"),
        observacion: document.getElementById("gasto_visualizar_observacion")
    };

    const campo_csrf = document.querySelector("[name=csrfmiddlewaretoken]");
    const token_csrf = campo_csrf ? campo_csrf.value : "";

    let gasto = "";
    let gastos_recibidos = [];
    let pagina_actual = 1;
    const filas_por_pagina = 10;

    formulario_actualizar.addEventListener("invalid", () => {
        formulario_actualizar.classList.add("validando");
    }, true);

    input_descripcion.addEventListener("input", () => {
        input_descripcion.setCustomValidity("");
    });

    textarea_observacion.addEventListener("input", () => {
        actualizarContador(textarea_observacion, contador_observacion);
    });

    function actualizarContador(textarea, contador) {
        contador.textContent = textarea.value.length;
    }

    async function solicitarJson(url, opciones = {}) {
        const respuesta = await fetch(url, opciones);
        const tipo_contenido = respuesta.headers.get("content-type") || "";

        if (!respuesta.ok || !tipo_contenido.includes("application/json")) {
            throw new Error(`Respuesta inválida del servidor (${respuesta.status}).`);
        }

        return respuesta.json();
    }

    async function categorias_registrados() {
        try {
            const resultado = await solicitarJson("/categorias_gastos/");

            select_categoria_gastos.replaceChildren(
                new Option("Todas las categorías", "")
            );
            select_nueva_categoria.replaceChildren(
                new Option("Seleccione una categoría", "")
            );

            resultado.forEach(categoria => {
                const option_busqueda = document.createElement("option");
                option_busqueda.value = categoria.id_categoria_gasto;
                option_busqueda.textContent = categoria.nombre;
                select_categoria_gastos.append(option_busqueda);

                const option_categoria = document.createElement("option");
                option_categoria.value = categoria.id_categoria_gasto;
                option_categoria.textContent = categoria.nombre;
                select_nueva_categoria.append(option_categoria);
            });
            return true;
        } catch (error) {
            console.error(error);
            await Swal.fire({
                title: "Error al cargar categorías",
                text: "No se pudieron cargar las categorías. Recargue la página e inténtelo de nuevo.",
                icon: "error"
            });
            return false;
        }
    }
    const categorias_cargadas = categorias_registrados();

    const fecha_hoy = new Date();
    const formatear_fecha = (fecha) => {
        const anio = fecha.getFullYear();
        const mes = String(fecha.getMonth() + 1).padStart(2, "0");
        const dia = String(fecha.getDate()).padStart(2, "0");

        return `${anio}-${mes}-${dia}`;
    };

    input_fecha_gasto.max = formatear_fecha(fecha_hoy);

    function mostrarGastos() {
        contenedor_gastos.innerHTML = "";

        const inicio = (pagina_actual - 1) * filas_por_pagina;
        const final = inicio + filas_por_pagina;

        const gastos_pagina = gastos_recibidos.slice(inicio, final);

        if (gastos_pagina.length === 0) {
            contenedor_gastos.innerHTML = `
                <tr>
                    <td colspan="4" class="texto_sin_registros">
                        No hay gastos registrados.
                    </td>
                </tr>
            `;
            actualizarBotones();
            return;
        }

        gastos_pagina.forEach((gasto, index) => {
            const fila = document.createElement("tr");
            fila.dataset.id = gasto.id_gasto;
            fila.classList.add("fila_gasto");

            fila.innerHTML = `
                <td>${inicio + index + 1}</td>
                <td>${gasto.categoria}</td>
                <td>
                    <span class="estado_${gasto.estado.toLowerCase()}">
                        ${gasto.estado}
                    </span>
                </td>
                <td>
                    <div class="acciones_gasto">
                        <button type="button"
                            class="btn_tabla btn_actualizar_gasto"
                            data-id="${gasto.id_gasto}">
                            <i class="fa-solid fa-pen-to-square"></i>
                            Actualizar
                        </button>
                        <button type="button"
                            class="btn_tabla btn_visualizar_gasto"
                            data-id="${gasto.id_gasto}">
                            <i class="fa-solid fa-eye"></i>
                            Visualizar
                        </button>
                    </div>
                </td>
            `;
            contenedor_gastos.appendChild(fila);
        });
        actualizarBotones();
    }

    function actualizarBotones() {
        const total_paginas = Math.ceil(
            gastos_recibidos.length / filas_por_pagina
        );

        btn_ret.disabled = pagina_actual <= 1;

        btn_av.disabled = pagina_actual >= total_paginas;
    }

    btn_ret.addEventListener("click", () => {
        if (pagina_actual > 1) {
            pagina_actual--;
            mostrarGastos();
        }
    });

    btn_av.addEventListener("click", () => {
        const total_paginas = Math.ceil(
            gastos_recibidos.length / filas_por_pagina
        );

        if (pagina_actual < total_paginas) {
            pagina_actual++;
            mostrarGastos();
        }
    });

    select_categoria_gastos.addEventListener("change", async () => {
        gasto = select_categoria_gastos.value;

        await gestion_gastos();
    });

    async function gestion_gastos() {
        try {
            const formulario = new FormData();
            formulario.append("categoria_gasto", gasto);

            const resultado = await solicitarJson("/visualizar_gastos/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": token_csrf
                },
                body: formulario
            });

            if (resultado.estado !== "exito" || !Array.isArray(resultado.gastos)) {
                throw new Error(resultado.descripcion || "No se pudieron cargar los gastos.");
            }

            gastos_recibidos = resultado.gastos;
            pagina_actual = 1;

            mostrarGastos();
        } catch (error) {
            console.error(error);

            gastos_recibidos = [];
            pagina_actual = 1;

            mostrarGastos();
        }
    }
    gestion_gastos();

    contenedor_gastos.addEventListener("click", async (e) => {
        const btn_actualizar = e.target.closest(".btn_actualizar_gasto");
        if (btn_actualizar) {
            await actualizar_gasto(btn_actualizar.dataset.id);
            return;
        }

        const btn_visualizar = e.target.closest(".btn_visualizar_gasto");
        if (btn_visualizar) {
            await visualizar_gasto(btn_visualizar.dataset.id);
        }
    });

    async function buscar_datos_gasto(id_gasto) {
        const formulario = new FormData();
        formulario.append("id_gasto", id_gasto);

        const resultado = await solicitarJson("/buscar_gasto/", {
            method: "POST",
            headers: {
                "X-CSRFToken": token_csrf
            },
            body: formulario
        });

        if (resultado.estado !== "exito") {
            await Swal.fire({
                title: resultado.title || "No se encontró el gasto",
                text: resultado.descripcion || "No se pudieron cargar los datos.",
                icon: resultado.icon || "error"
            });
            return null;
        }

        return resultado.gasto;
    }

    async function actualizar_gasto(id_gasto) {
        try {
            const categorias_disponibles = await categorias_cargadas;
            if (!categorias_disponibles) {
                throw new Error("No se pudieron cargar las categorías del gasto.");
            }

            const datos = await buscar_datos_gasto(id_gasto);
            if (!datos) return;

            input_id_gasto.value = datos.id_gasto;
            select_nueva_categoria.value = String(datos.id_categoria_gasto);
            input_descripcion.value = datos.descripcion;
            input_monto_gasto.value = datos.monto;
            input_fecha_gasto.value = datos.fecha_gasto;
            select_es_recurrente.value = datos.es_recurrente ? "true" : "false";
            select_frecuencia.value = datos.es_recurrente ? datos.frecuencia : "";
            actualizarVisibilidadFrecuencia();
            input_referencia.value = datos.referencia;
            textarea_observacion.value = datos.observacion;
            actualizarContador(textarea_observacion, contador_observacion);
            validar_monto_gasto();
        } catch (error) {
            console.error(error);
            await Swal.fire({
                title: "Error",
                text: error.message || "No se pudieron cargar los datos del gasto.",
                icon: "error"
            });
        }
    }

    async function visualizar_gasto(id_gasto) {
        try {
            const datos = await buscar_datos_gasto(id_gasto);
            if (!datos) return;

            campos_visualizacion.categoria.value = datos.categoria;
            campos_visualizacion.descripcion.value = datos.descripcion;
            campos_visualizacion.monto.value = datos.monto;
            campos_visualizacion.fecha.value = datos.fecha_gasto;
            campos_visualizacion.estado.value = datos.estado;
            campos_visualizacion.recurrente.value = datos.es_recurrente ? "Sí" : "No";
            campos_visualizacion.frecuencia.value = datos.es_recurrente
                ? ({
                    SEMANAL: "Semanal",
                    MENSUAL: "Mensual",
                    ANUAL: "Anual"
                }[datos.frecuencia] || datos.frecuencia || "")
                : "No aplica";
            campos_visualizacion.referencia.value = datos.referencia || "—";
            campos_visualizacion.observacion.value = datos.observacion || "—";

            dialogo_gasto.showModal();
        } catch (error) {
            console.error(error);
            await Swal.fire({
                title: "Error",
                text: error.message || "No se pudieron cargar los datos del gasto.",
                icon: "error"
            });
        }
    }

    function actualizarVisibilidadFrecuencia() {
        const es_recurrente = select_es_recurrente.value === "true";

        contenedor_frecuencia.hidden = !es_recurrente;
        select_frecuencia.disabled = !es_recurrente;
        select_frecuencia.required = es_recurrente;

        if (!es_recurrente) {
            select_frecuencia.value = "";
        }
    }

    select_es_recurrente.addEventListener("change", actualizarVisibilidadFrecuencia);
    actualizarVisibilidadFrecuencia();

    formulario_actualizar.addEventListener("submit", async (e) => {
        e.preventDefault();

        validar_monto_gasto();
        input_descripcion.setCustomValidity(
            input_descripcion.value.trim()
                ? ""
                : "Ingrese la descripción del gasto."
        );

        if (!formulario_actualizar.reportValidity()) {
            return;
        }

        input_descripcion.value = input_descripcion.value.trim();
        input_referencia.value = input_referencia.value.trim();
        textarea_observacion.value = textarea_observacion.value.trim();
        actualizarContador(textarea_observacion, contador_observacion);


        
        try {
            const formulario = new FormData(formulario_actualizar);

            const resultado = await solicitarJson("/actualizar_datos_gasto/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": token_csrf
                },
                body: formulario
            });

            if (resultado.estado === "exito") {
                formulario_actualizar.reset();
                formulario_actualizar.classList.remove("validando");
                input_id_gasto.value = "";
                input_monto_gasto.setCustomValidity("");
                actualizarVisibilidadFrecuencia();
                actualizarContador(textarea_observacion, contador_observacion);
                await gestion_gastos();
            }

            await Swal.fire({
                title: resultado.title || "Resultado de la actualización",
                text: resultado.descripcion || "No se pudo actualizar el gasto.",
                icon: resultado.icon || (
                    resultado.estado === "exito" ? "success" : "error"
                )
            });
        } catch (error) {
            console.error(error);

            await Swal.fire({
                title: "Error",
                text: "Ocurrió un error al intentar actualizar el gasto. Inténtelo nuevamente.",
                icon: "error"
            });
        }
    });

    [input_monto_gasto].forEach(input => {
        input.addEventListener("input", function () {
            let valor = this.value.replace(/[^0-9.]/g, "");
            const partes = valor.split(".");

            let enteros = partes[0].slice(0, 3);
            let decimales = partes.slice(1).join("").slice(0, 2);

            if (partes.length > 1 && enteros !== "") {
                valor = `${enteros}.${decimales}`;
            } else {
                valor = enteros;
            }

            this.value = valor;

            validar_monto_gasto();
        });
    });

    function validar_monto_gasto() {
        const monto = input_monto_gasto.value.trim();
        input_monto_gasto.setCustomValidity("");

        if (!monto) {
            return false;
        }

        if (!/^[0-9]{1,3}(\.[0-9]{1,2})?$/.test(monto)) {
            input_monto_gasto.setCustomValidity(
                "Ingrese un monto con hasta 3 dígitos enteros y 2 decimales."
            );
            return false;
        }

        if (!Number.isFinite(Number(monto)) || Number(monto) <= 0) {
            input_monto_gasto.setCustomValidity(
                "El monto debe ser un número mayor que cero."
            );
            return false;
        }

        return true;
    }

    btn_cerrar.addEventListener("click", () => {
        dialogo_gasto.close();
    })


});