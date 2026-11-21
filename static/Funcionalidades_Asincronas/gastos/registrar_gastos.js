document.addEventListener("DOMContentLoaded", () => {

    const select_categoria_gastos = document.getElementById("categoria_gastos");
    const input_monto_gasto = document.getElementById("monto_gasto");
    const input_fecha_gasto = document.getElementById("fecha_gasto");
    const input_descripcion = document.getElementById("descripcion");
    const textarea_observacion = document.getElementById("observacion");
    const contador_observacion = document.getElementById("contador_observacion");
    const formulario_registrar = document.getElementById("formulario_registrar");

    textarea_observacion.addEventListener("input", () => {
        textarea_observacion.value = textarea_observacion.value.replace(
            /[^a-zA-ZáéíóúÁÉÍÓÚñÑ0-9\s.,:;()\-]/g,
            ""
        );

        contador_observacion.textContent = textarea_observacion.value.length;
    });

    async function categorias_registrados() {
        try {
            const respuesta = await fetch("/categorias_gastos/");
            const resultado = await respuesta.json();
            console.log(resultado);

            select_categoria_gastos.innerHTML = "";

            resultado.forEach(categoria => {
                const option = document.createElement("option");
                option.value = categoria.id_categoria_gasto;
                option.textContent = categoria.nombre;
                select_categoria_gastos.append(option);
            });
        } catch (error) {
            console.error(error);
        }
    }
    categorias_registrados();

    input_monto_gasto.addEventListener("input", function () {
        let valor = this.value.replace(/[^0-9.]/g, "");

        const partes = valor.split(".");

        let enteros = partes[0].slice(0, 4);
        let decimales = partes.slice(1).join("").slice(0, 2);

        valor = partes.length > 1
            ? enteros + "." + decimales
            : enteros;

        this.value = valor;
    });

    const fecha_hoy = new Date();
    const fecha_minima = new Date();

    fecha_minima.setDate(fecha_hoy.getDate() - 7);

    const formatear_fecha = (fecha) => {
        const anio = fecha.getFullYear();
        const mes = String(fecha.getMonth() + 1).padStart(2, "0");
        const dia = String(fecha.getDate()).padStart(2, "0");

        return `${anio}-${mes}-${dia}`;
    };

    input_fecha_gasto.min = formatear_fecha(fecha_minima);
    input_fecha_gasto.max = formatear_fecha(fecha_hoy);

    function validar_texto(elemento) {
        elemento.addEventListener("input", function () {
            let valor = this.value;

            valor = valor.replace(/[^a-zA-ZáéíóúÁÉÍÓÚñÑüÜ0-9 .]/g, "");

            let puntos = 0;
            valor = valor.replace(/\./g, () => {
                puntos++;
                return puntos === 1 ? "." : "";
            });

            let cantidad_numeros = 0;
            valor = valor.replace(/[0-9]/g, numero => {
                cantidad_numeros++;
                return cantidad_numeros <= 4 ? numero : "";
            });

            this.value = valor;
        });
    }

    validar_texto(input_descripcion);
    validar_texto(textarea_observacion);

    formulario_registrar.addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
            const formulario = new FormData(formulario_registrar);

            const respuesta = await fetch("/registrar_gastos/", {
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

            await Swal.fire({
                title: resultado.title,
                text: resultado.descripcion,
                icon: resultado.icon
            });

            formulario_registrar.reset();
        } catch (error) {
            console.error(error);
        }
    });

});