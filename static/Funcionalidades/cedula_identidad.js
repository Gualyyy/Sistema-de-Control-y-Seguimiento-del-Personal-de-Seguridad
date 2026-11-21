function configurarCedula(campoCedula, selectNacionalidad) {

    function longitudIdentidad() {
        const nacionalidad = selectNacionalidad.value;

        campoCedula.value = "";

        const configuraciones = {
            V: {
                min: 7,
                max: 8,
                placeholder: "Cédula (7-8 números)"
            },
            E: {
                min: 8,
                max: 10,
                placeholder: "Pasaporte/DNI (8-10 números)"
            },
            J: {
                min: 9,
                max: 9,
                placeholder: "RIF jurídico (9 números)"
            },
            G: {
                min: 9,
                max: 9,
                placeholder: "RIF gubernamental (9 números)"
            }
        };

        const configuracion = configuraciones[nacionalidad];

        if (!configuracion) {
            campoCedula.disabled = true;
            campoCedula.placeholder = "Seleccione una nacionalidad";
            campoCedula.removeAttribute("minlength");
            campoCedula.removeAttribute("maxlength");
            campoCedula.setCustomValidity("");
            return;
        }

        campoCedula.disabled = false;
        campoCedula.minLength = configuracion.min;
        campoCedula.maxLength = configuracion.max;
        campoCedula.placeholder = configuracion.placeholder;
    }

    campoCedula.addEventListener("input", function () {
        this.value = this.value.replace(/\D/g, "");

        const nacionalidad = selectNacionalidad.value;

        const longitudes = {
            V: [7, 8],
            E: [8, 10],
            J: [9, 9],
            G: [9, 9]
        };

        const rango = longitudes[nacionalidad];

        if (rango && this.value.length >= rango[0] &&
            this.value.length <= rango[1]) {
            this.setCustomValidity("");
        }
    });

    selectNacionalidad.value = "V";

    selectNacionalidad.addEventListener("change", longitudIdentidad);

    longitudIdentidad();
}