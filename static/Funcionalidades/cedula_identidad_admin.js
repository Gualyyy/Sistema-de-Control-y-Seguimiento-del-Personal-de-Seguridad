document.addEventListener("DOMContentLoaded", () => {

    const campo_cedula = document.getElementById("id_cedula_identidad");
    const select_nacionalidad = document.getElementById("id_nacionalidad");

    if (!campo_cedula || !select_nacionalidad) {
        return;
    }

    function longitud_identidad() {
        const nacionalidad = select_nacionalidad.value;

        if (nacionalidad === "") {

            campo_cedula.disabled = true;
            campo_cedula.placeholder = "Seleccione nacionalidad";
            campo_cedula.value = "";

            return;
        }


        campo_cedula.disabled = false;


        switch (nacionalidad) {

            case "V":
                campo_cedula.minLength = 7;
                campo_cedula.maxLength = 8;
                campo_cedula.placeholder = "Cédula (7-8 números)";

                break;
            case "E":

                campo_cedula.minLength = 8;
                campo_cedula.maxLength = 10;
                campo_cedula.placeholder = "Pasaporte/DNI (8-10 números)";

                break;
        }


        campo_cedula.value = "";
    }



    campo_cedula.addEventListener("input", function () {

        this.value = this.value.replace(/\D/g, "");

    });



    select_nacionalidad.addEventListener(
        "change",
        longitud_identidad
    );


    // Ejecutar al cargar el formulario
    longitud_identidad();

});