document.addEventListener("DOMContentLoaded", () => {

    const formulario_registrar = document.getElementById("formulario_registrar");

    const select_vigilantes_registrados = document.getElementById("vigilantes_registrados");
    const select_tipos_incidencia = document.getElementById("tipos_incidencias");
    const input_titulo_incidencia = document.getElementById("titulo_incidencia");
    const textarea_descripcion_incidencia = document.getElementById("descripcion_incidencia");
    const contador_descripcion_incidencia = document.getElementById("contador_descripcion_incidencia");
    const campoFecha = document.getElementById("fecha_hora_incidencia");

    function validacion_campo_fecha() {
        const hoy = new Date();
        const ayer = new Date(hoy);
        ayer.setDate(hoy.getDate() - 1);

        const formatearFecha = (fecha) => {
            const año = fecha.getFullYear();
            const mes = String(fecha.getMonth() + 1).padStart(2, "0");
            const dia = String(fecha.getDate()).padStart(2, "0");

            return `${año}-${mes}-${dia}`;
        };

        campoFecha.min = `${formatearFecha(ayer)}T00:00`;
        campoFecha.max = `${formatearFecha(hoy)}T23:59`;
    }
    validacion_campo_fecha()

    async function vigilantes_registrados() {
        try {
            const respuesta = await fetch("/incidencias/vigilantes_registrados/");
            const resultado = await respuesta.json();
            console.log(resultado);

            select_vigilantes_registrados.innerHTML = "<option value='' selected>Selecciona el Vigilante</option>";

            resultado.vigilantes.forEach(vigilante => {
                const option = document.createElement("option");
                option.value = vigilante.id_vigilante;
                option.textContent = vigilante.nombres + " " + vigilante.apellidos;
                select_vigilantes_registrados.append(option);
            });
        } catch (error) {
            console.error(error);
        }
    }
    vigilantes_registrados();

    async function tipos_incidencias() {
        try {
            const respuesta = await fetch("/incidencias/tipos_incidencias/");
            const resultado = await respuesta.json();
            console.log(resultado);

            select_tipos_incidencia.innerHTML = "<option value='' selected>Selecciona el Tipo de Incidencia</option>";

            resultado.forEach(incidencia => {
                const option = document.createElement("option");
                option.value = incidencia.id_tipo;
                option.textContent = incidencia.nombre;
                select_tipos_incidencia.append(option);
            });
        } catch (error) {
            console.error(error);
        }
    }
    tipos_incidencias();

    textarea_descripcion_incidencia.addEventListener("input", () => {
        textarea_descripcion_incidencia.value = textarea_descripcion_incidencia.value.replace(/[^a-zA-ZáéíóúÁÉÍÓÚñÑ0-9\s.,:;()\-]/g, "");

        contador_descripcion_incidencia.textContent = textarea_descripcion_incidencia.value.length;
    });

    function soloTexto(input) {
        input.value = input.value.replace(/[^a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]/g, '');
    }

    textarea_descripcion_incidencia.addEventListener("input", () => {
        soloTexto(textarea_descripcion_incidencia);
    });

    input_titulo_incidencia.addEventListener("input", () => {
        soloTexto(input_titulo_incidencia);
    });

    formulario_registrar.addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
            const formulario = new FormData(formulario_registrar);

            const respuesta = await fetch("/incidencias/registrar_incidencias/", {
                method: "POST",
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            await Swal.fire({
                title: resultado.title,
                text: resultado.descripcion,
                icon: resultado.icon
            });

            if (resultado.estado == "exito") {
                formulario_registrar.reset();
                contador_descripcion_incidencia.textContent = "0";
            }
        } catch (error) {
            console.error(error);
        }
    });

});