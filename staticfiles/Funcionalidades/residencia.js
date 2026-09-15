document.addEventListener("DOMContentLoaded", function () {

    const municipioSelect = document.getElementById("municipio_residencia");
    const parroquiaSelect = document.getElementById("parroquia_residencia");
    const direccionTextarea = document.getElementById("direccion_domicilio");

    const municipios = ["Barinas", "Pedraza", "Antonio José de Sucre", "Ezequiel Zamora", "Bolívar", "Alberto Arvelo Torrealba", "Rojas", "Obispo", "Sosa", "Cruz Paredes", "Arismendi", "Andrés Eloy Blanco"];

    const parroquiasPorMunicipio = {
        "Barinas": ["Alfredo Arvelo Larriva", "San Silvestre", "Santa Inés", "Santa Lucía", "Torunos", "El Carmen", "Alto Barinas", "Rómulo Betancourt", "Corazón de Jesús", "Ramón Ignacio Méndez", "Manuel Palacio Fajardo", "Juan Antonio Rodríguez Domínguez", "Domingo Ortiz de Páez"],

        "Pedraza": ["Ciudad Bolivia", "Ignacio Briceño", "José Félix Ribas", "Páez"],

        "Antonio José de Sucre": ["Ticoporo", "Andrés Bello", "Nicolás Pulido"],

        "Ezequiel Zamora": ["Santa Bárbara", "José Ignacio del Pumar", "Pedro Briceño Méndez", "Ramón Ignacio Méndez"],

        "Bolívar": ["Barinitas", "Altamira de Cáceres", "Calderas"],

        "Alberto Arvelo Torrealba": ["Sabaneta", "El Real"],

        "Rojas": ["Libertad", "Dolores", "Palacios Fajardo", "Santa Rosa", "Simón Rodríguez"],

        "Obispo": ["Obispos", "El Real", "La Luz", "Los Guasimitos"],

        "Sosa": ["Ciudad de Nutrias", "El Regalo", "Puerto de Nutrias", "Santa Catalina", "Simón Bolívar"],

        "Cruz Paredes": ["Barrancas", "El Socorro", "Masparrito"],

        "Arismendi": ["Arismendi", "Guadarrama", "La Unión", "San Antonio"],

        "Andrés Eloy Blanco": ["El Cantón", "Santa Cruz de Guacas", "Puerto Vivas", "Dominga Ortiz de Páez"]
    };

    /********************MUNICIPIO REDENCIA***********************/

    function cargarMunicipios() {

        municipioSelect.innerHTML =
            '<option value="" disabled selected hidden>Elija el Municipio</option>';

        municipios.forEach(municipio => {

            const option = document.createElement("option");

            option.value = municipio;
            option.textContent = municipio;

            municipioSelect.appendChild(option);
        });

        // Municipio obligatorio
        municipioSelect.disabled = false;
        municipioSelect.required = true;

        // Parroquia todavía no disponible
        parroquiaSelect.disabled = true;
        parroquiaSelect.required = false;

        // Dirección siempre disponible y obligatoria
        direccionTextarea.disabled = false;
        direccionTextarea.required = true;
    }

    cargarMunicipios();

    /********************PARROQUIA REDENCIA***********************/

    function actualizarParroquias() {

        const municipio = municipioSelect.value;

        parroquiaSelect.innerHTML =
            '<option value="" disabled selected hidden>Elija la Parroquia</option>';

        // Mientras no haya municipio
        if (!municipio) {

            parroquiaSelect.disabled = true;
            parroquiaSelect.required = false;

            return;
        }

        // Si existe el municipio
        if (municipio in parroquiasPorMunicipio) {

            parroquiasPorMunicipio[municipio].forEach(parroquia => {

                const option = document.createElement("option");

                option.value = parroquia;
                option.textContent = parroquia;

                parroquiaSelect.appendChild(option);
            });

            // Parroquia ahora sí es obligatoria
            parroquiaSelect.disabled = false;
            parroquiaSelect.required = true;

        } else {

            parroquiaSelect.disabled = true;
            parroquiaSelect.required = false;
        }

        // Dirección obligatoria
        direccionTextarea.disabled = false;
        direccionTextarea.required = true;
    }

    actualizarParroquias();

    municipioSelect.addEventListener("change", actualizarParroquias);

});
