document.addEventListener("DOMContentLoaded", () => {

    const formulario_registrar = document.getElementById("formulario_registrar");

    const input_nombre_equipo = document.getElementById("nombre_equipo");
    const input_codigo_equipo = document.getElementById("codigo_equipo");
    const select_categoria_equipo = document.getElementById("categoria_equipo");
    const textarea_observacion_equipo = document.getElementById("observacion_equipo");
    const input_cantidad_total = document.getElementById("cantidad_total");

    const contador_observacion = document.getElementById("contador_observacion");

    function soloTexto(input) {
        input.value = input.value.replace(/[^a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]/g, '');
    }

    input_nombre_equipo.addEventListener("input", function () {
        soloTexto(this);
    });

    input_cantidad_total.addEventListener("input", () => {
        input_cantidad_total.value = input_cantidad_total.value.replace(/[^0-9]/g, "");

        // Máximo 3 dígitos
        if (input_cantidad_total.value.length > 3) {
            input_cantidad_total.value = input_cantidad_total.value.slice(0, 3);
        }

        // No permitir ceros al inicio
        if (input_cantidad_total.value.length > 0 && input_cantidad_total.value.startsWith("0")) {
            input_cantidad_total.setCustomValidity(
                "La cantidad debe ser un número entero mayor a 0 y no puede comenzar con 0."
            );

            input_cantidad_total.reportValidity();
        } else {
            input_cantidad_total.setCustomValidity("");
        }

    });

    async function categoria_equipo_registrados() {
        try {
            const respuesta = await fetch("/categoria_registrados/");
            const resultado = await respuesta.json();
            console.log(resultado);

            select_categoria_equipo.innerHTML = "<option selected>Seleccione la categoria</option>";

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

    function generarCodigoEquipo() {
        const caracteres = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
        let codigo = "EQ-";

        for (let i = 0; i < 4; i++) {
            codigo += caracteres.charAt(
                Math.floor(Math.random() * caracteres.length)
            );
        }

        input_codigo_equipo.value = codigo;
    }
    generarCodigoEquipo();

    textarea_observacion_equipo.addEventListener("input", () => {
        textarea_observacion_equipo.value = textarea_observacion_equipo.value.replace(
            /[^a-zA-ZáéíóúÁÉÍÓÚñÑ0-9\s.,:;()\-]/g,
            ""
        );

        contador_observacion.textContent = textarea_observacion_equipo.value.length;
    });

    formulario_registrar.addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
            const formulario = new FormData(formulario_registrar);

            const respuesta = await fetch("/registros_equipos/", {
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
                generarCodigoEquipo();

                contador_observacion.textContent = "0";
            }
        } catch (error) {
            console.error(error);
        }
    });
});