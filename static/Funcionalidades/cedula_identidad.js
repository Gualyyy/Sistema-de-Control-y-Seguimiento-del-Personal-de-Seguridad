function configurarCedula(campoCedula, selectNacionalidad) {

    function longitudIdentidad() {
        const nacionalidad = selectNacionalidad.value;

        if (nacionalidad === "") {
            campoCedula.disabled = true;
            campoCedula.placeholder = "Seleccione nacionalidad";
            return;
        }

        campoCedula.disabled = false;

        switch (nacionalidad) {

            case "V":
                campoCedula.maxLength = 8;
                campoCedula.minLength = 7;
                campoCedula.placeholder = "Cédula (7-8 números)";
                campoCedula.value = "";
                break;

            case "E":
                campoCedula.maxLength = 10;
                campoCedula.minLength = 8;
                campoCedula.placeholder = "Pasaporte/DNI (8-10 números)";
                campoCedula.value = "";
                break;
        }
    }

    campoCedula.addEventListener("input", function () {
        this.value = this.value.replace(/\D/g, "");
    });

    selectNacionalidad.addEventListener("change", longitudIdentidad);

    longitudIdentidad();
}