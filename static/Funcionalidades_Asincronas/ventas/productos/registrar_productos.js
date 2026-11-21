document.addEventListener("DOMContentLoaded", () => {

    const formulario_registrar = document.getElementById("formulario_registrar");

    const input_nombre_producto = document.getElementById("nombre_producto");
    const input_codigo_producto = document.getElementById("codigo_producto");

    const input_precio_base = document.getElementById("precio_base");
    const input_costo_base = document.getElementById("costo_base");
    const contenedor_mensaje_costo_base = document.getElementById("contenedor_mensaje_costo_base");

    const select_categoria_producto = document.getElementById("categoria_producto");
    const select_unidad_producto = document.getElementById("unidad_producto");

    const btn_registrar = document.getElementById("btn_registrar");

    async function categoria_registrada() {
        try {
            const respuesta = await fetch("/ventas/categorias_productos/");
            const resultado = await respuesta.json();
            console.log(resultado);

            select_categoria_producto.innerHTML = "";

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

            select_unidad_producto.innerHTML = "";

            resultado.forEach(unidad => {
                const option = document.createElement("option");
                option.value = unidad.id_unidad;
                option.textContent = unidad.nombre + " | " + unidad.abreviatura;
                select_unidad_producto.append(option);
            });
        } catch (error) {
            console.error(error);
        }
    }
    unidades_medida();

    function codigo_producto() {
        input_codigo_producto.value = `P-${Math.floor(100000 + Math.random() * 900000)}`;
    }
    codigo_producto();
    function soloTexto(input) {
        let valor = input.value.replace(/[^a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s0-9.]/g, '');

        let numeros = 0;
        let punto = false;

        input.value = [...valor].filter(caracter => {
            if (/[0-9]/.test(caracter)) {
                if (numeros >= 3) return false;
                numeros++;
                return true;
            }

            if (caracter === '.') {
                if (punto) return false;
                punto = true;
            }

            return true;
        }).join('');
    }

    input_nombre_producto.addEventListener("input", function () {
        soloTexto(input_nombre_producto);
    });

    [input_precio_base, input_costo_base].forEach(input => {
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

            validar_costo_base();
        });
    });

    function validar_costo_base() {
        const precio = input_precio_base.value;
        const costo = input_costo_base.value;

        input_costo_base.setCustomValidity("");
        input_costo_base.classList.remove("is-valid", "is-invalid");
        contenedor_mensaje_costo_base.classList.remove("exito", "error");

        if (precio === "" || costo === "") {
            contenedor_mensaje_costo_base.textContent = "";
            btn_registrar.disabled = true;
            return false;
        }

        const precio_base = parseFloat(precio);
        const costo_base = parseFloat(costo);

        if (costo_base >= precio_base) {
            const mensaje = costo_base === precio_base
                ? "El costo base no puede ser igual al precio base."
                : "El costo base no puede ser mayor al precio base.";

            input_costo_base.setCustomValidity(mensaje);
            input_costo_base.classList.add("is-invalid");

            contenedor_mensaje_costo_base.textContent = mensaje;
            contenedor_mensaje_costo_base.classList.add("error");

            btn_registrar.disabled = true;
            return false;
        }

        input_costo_base.classList.add("is-valid");

        contenedor_mensaje_costo_base.textContent = "El costo base es válido.";
        contenedor_mensaje_costo_base.classList.add("exito");

        btn_registrar.disabled = false;
        return true;
    }

    formulario_registrar.addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
            const formulario = new FormData(formulario_registrar);

            const respuesta = await fetch("/ventas/registrar_productos/", {
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
            contenedor_mensaje_costo_base.innerHTML = "";
            codigo_producto();
        } catch (error) {
            console.error(error);
        }
    });

});