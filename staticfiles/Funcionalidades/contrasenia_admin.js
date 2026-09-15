document.addEventListener("DOMContentLoaded", () => {
    const input_clave = document.getElementById("id_clave");
    if (!input_clave) return;

    const contenedor = input_clave.parentElement;

    const icono_visualizar = document.createElement("i");
    icono_visualizar.classList.add("icon-eye");
    icono_visualizar.id = "id_mostrar";

    const icono_ocultar = document.createElement("i");
    icono_ocultar.classList.add("icon-eye-off");
    icono_ocultar.id = "id_ocultar";
    icono_ocultar.classList.add("ocultar");

    contenedor.classList.add("contenedor-clave");

    contenedor.appendChild(icono_visualizar);
    contenedor.appendChild(icono_ocultar);

    function mostrar_clave(){
        if(input_clave.type === "password"){
            input_clave.type = "text";
            icono_visualizar.classList.add("ocultar");
            icono_ocultar.classList.remove("ocultar");
        }else{
            input_clave.type = "password";
            icono_visualizar.classList.remove("ocultar");
            icono_ocultar.classList.add("ocultar");
        }
    }

    icono_visualizar.addEventListener("click", mostrar_clave);
    icono_ocultar.addEventListener("click", mostrar_clave);
});