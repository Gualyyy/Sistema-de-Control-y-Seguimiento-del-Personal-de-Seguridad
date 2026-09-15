document.addEventListener("DOMContentLoaded", () => {
    const input_clave = document.getElementById("clave");
    const input_checkbox = document.getElementById("evento");
    const icono_visualizar = document.getElementById("id_mostrar");
    const icono_ocultar = document.getElementById("id_ocultar");

    function campo_contrasenia() {
        if (input_checkbox.checked) {
            input_clave.type = "text";

            icono_visualizar.classList.add("ocultar");
            icono_ocultar.classList.remove("ocultar");

        } else {
            input_clave.type = "password";

            icono_visualizar.classList.remove("ocultar");
            icono_ocultar.classList.add("ocultar");
        }
    }

    input_checkbox.addEventListener("change", campo_contrasenia);

    campo_contrasenia();
});