document.addEventListener("DOMContentLoaded", () => {

    const formulario_busqueda = document.getElementById("formulario_busqueda");
    const formulario_actualizar = document.getElementById("formulario_actualizar")

    const input_cedula_identidad = document.getElementById("cedula_identidad");
    const select_nacionalidad = document.getElementById("nacionalidad");

    const input_id_usuario = document.getElementById("id_usuario")
    const btn_actualizar = document.getElementById("btn_actualizar")

    const input_actualizar_nombre = document.getElementById("actualizar_nombre_usuario")
    const input_actualizar_apellido = document.getElementById("actualizar_apellido_usuario")
    const input_actualizar_cedula = document.getElementById("actualizar_cedula_identidad_usuario")
    const select_actualizar_nacionalidad = document.getElementById("actualizar_nacionalidad_usuario")
    const select_actualizar_genero = document.getElementById("actualizar_genero_usuario")
    const select_actualizar_estado_civil = document.getElementById("actualizar_estado_civil_usuario")
    const input_actualizar_nombre_usuario = document.getElementById("actualizar_usuario")
    const input_actualizar_contrasenia = document.getElementById("clave")

    const input_actualizar_num_telefono_principal = document.getElementById("num_telefono_principal")
    const select_actualizar_prefijo_principal = document.getElementById("prefijo_principal")
    const input_actualizar_num_telefono_secundario = document.getElementById("num_telefono_secundario")
    const select_actualizar_prefijo_secundario = document.getElementById("prefijo_secundario")

    const input_actualizar_correo_principal = document.getElementById("correo_principal")
    const select_actualizar_dominio_principal = document.getElementById("dominio_principal")
    const input_actualizar_correo_secundario = document.getElementById("correo_secundario")
    const select_actualizar_dominio_secundario = document.getElementById("dominio_secundario")

    const select_actualizar_pais_nacimiento = document.getElementById("pais_nacimiento")

    const select_actualizar_estado_nacimiento = document.getElementById("estado_nacimiento")
    const input_actualizar_estado_vzla_nacimiento = document.getElementById("estado_novzla")

    const select_actualizar_municipio_nacimiento = document.getElementById("municipio_nacimiento")
    const input_actualizar_municipio_vzla_nacimiento = document.getElementById("municipio_novzla")

    const select_actualizar_parroquia_nacimiento = document.getElementById("parroquia_nacimiento")
    const input_actualizar_parroquia_vzla_nacimiento = document.getElementById("parroquia_novzla")

    const textarea_actualizar_direccion_nacimiento = document.getElementById("direccion_nacimiento")
    const input_actualizar_fecha_nacimiento = document.getElementById("fecha_nacimiento_usuario")

    const select_actualizar_condicion_residencia = document.getElementById("actualizar_condicion_residencia_usuario")
    const select_actualizar_municipio_residencia = document.getElementById("municipio_residencia")
    const select_actualizar_parroquia_residencia = document.getElementById("parroquia_residencia")
    const textarea_actualizar_direccion_residencia = document.getElementById("direccion_domicilio")

    const contenedor_mensaje_ci = document.getElementById("contenedor_mensaje_ci");
    const contenedor_mensaje_nombre_usuario = document.getElementById("contenedor_mensaje_nombre_usuario");
    const contenedor_mensaje_contrasenia = document.getElementById("contenedor_mensaje_password");
    const contenedor_mensaje_correo_principal = document.getElementById("contenedor_mensaje_correo_principal");
    const contenedor_mensaje_correo_secundario = document.getElementById("contenedor_mensaje_correo_secundario");

    const contador_nacimiento = document.getElementById("contador_nacimiento");
    const contador_residencia = document.getElementById("contador_residencia");

    const contenedorFortaleza = document.querySelector(".fortaleza_contrasenia");
    const barra_fortaleza = document.querySelector(".barra_fortaleza");
    const texto_fortaleza = document.querySelector(".texto_fortaleza");

    configurarCedula(input_cedula_identidad, select_nacionalidad);
    configurarCedula(input_actualizar_cedula, select_actualizar_nacionalidad);

    configurarCorreo(input_actualizar_correo_principal, select_actualizar_dominio_principal);
    configurarCorreo(input_actualizar_correo_secundario, select_actualizar_dominio_secundario);

    configurarTelefono(input_actualizar_num_telefono_principal, select_actualizar_prefijo_principal);
    configurarTelefono(input_actualizar_num_telefono_secundario, select_actualizar_prefijo_secundario);

    const paises = [
        "Afganistán",
        "Albania",
        "Alemania",
        "Andorra",
        "Angola",
        "Antigua y Barbuda",
        "Arabia Saudita",
        "Argelia",
        "Argentina",
        "Armenia",
        "Australia",
        "Austria",
        "Azerbaiyán",
        "Bahamas",
        "Bangladés",
        "Barbados",
        "Baréin",
        "Bélgica",
        "Belice",
        "Benín",
        "Bielorrusia",
        "Birmania",
        "Bolivia",
        "Bosnia y Herzegovina",
        "Botsuana",
        "Brasil",
        "Brunéi",
        "Bulgaria",
        "Burkina Faso",
        "Burundi",
        "Bután",
        "Cabo Verde",
        "Camboya",
        "Camerún",
        "Canadá",
        "Catar",
        "Chad",
        "Chile",
        "China",
        "Chipre",
        "Ciudad del Vaticano",
        "Colombia",
        "Comoras",
        "Corea del Norte",
        "Corea del Sur",
        "Costa de Marfil",
        "Costa Rica",
        "Croacia",
        "Cuba",
        "Dinamarca",
        "Dominica",
        "Ecuador",
        "Egipto",
        "El Salvador",
        "Emiratos Árabes Unidos",
        "Eritrea",
        "Eslovaquia",
        "Eslovenia",
        "España",
        "Estados Unidos",
        "Estonia",
        "Etiopía",
        "Filipinas",
        "Finlandia",
        "Fiyi",
        "Francia",
        "Gabón",
        "Gambia",
        "Georgia",
        "Ghana",
        "Granada",
        "Grecia",
        "Guatemala",
        "Guyana",
        "Guinea",
        "Guinea ecuatorial",
        "Guinea-Bisáu",
        "Haití",
        "Honduras",
        "Hungría",
        "India",
        "Indonesia",
        "Irak",
        "Irán",
        "Irlanda",
        "Islandia",
        "Islas Marshall",
        "Islas Salomón",
        "Israel",
        "Italia",
        "Jamaica",
        "Japón",
        "Jordania",
        "Kazajistán",
        "Kenia",
        "Kirguistán",
        "Kiribati",
        "Kuwait",
        "Laos",
        "Lesoto",
        "Letonia",
        "Líbano",
        "Liberia",
        "Libia",
        "Liechtenstein",
        "Lituania",
        "Luxemburgo",
        "Madagascar",
        "Malasia",
        "Malaui",
        "Maldivas",
        "Malí",
        "Malta",
        "Marruecos",
        "Mauricio",
        "Mauritania",
        "México",
        "Micronesia",
        "Moldavia",
        "Mónaco",
        "Mongolia",
        "Montenegro",
        "Mozambique",
        "Namibia",
        "Nauru",
        "Nepal",
        "Nicaragua",
        "Níger",
        "Nigeria",
        "Noruega",
        "Nueva Zelanda",
        "Omán",
        "Países Bajos",
        "Pakistán",
        "Palaos",
        "Panamá",
        "Papúa Nueva Guinea",
        "Paraguay",
        "Perú",
        "Polonia",
        "Portugal",
        "Reino Unido",
        "República Centroafricana",
        "República Checa",
        "República de Macedonia",
        "República del Congo",
        "República Democrática del Congo",
        "República Dominicana",
        "República Sudafricana",
        "Ruanda",
        "Rumanía",
        "Rusia",
        "Samoa",
        "San Cristóbal y Nieves",
        "San Marino",
        "San Vicente y las Granadinas",
        "Santa Lucía",
        "Santo Tomé y Príncipe",
        "Senegal",
        "Serbia",
        "Seychelles",
        "Sierra Leona",
        "Singapur",
        "Siria",
        "Somalia",
        "Sri Lanka",
        "Suazilandia",
        "Sudán",
        "Sudán del Sur",
        "Suecia",
        "Suiza",
        "Surinam",
        "Tailandia",
        "Tanzania",
        "Tayikistán",
        "Timor Oriental",
        "Togo",
        "Tonga",
        "Trinidad y Tobago",
        "Túnez",
        "Turkmenistán",
        "Turquía",
        "Tuvalu",
        "Ucrania",
        "Uganda",
        "Uruguay",
        "Uzbekistán",
        "Vanuatu",
        "Venezuela",
        "Vietnam",
        "Yemen",
        "Yibuti",
        "Zambia",
        "Zimbabue"
    ];

    const Estado = [
        "Amazonas", "Anzoátegui", "Apure", "Aragua", "Barinas", "Bolívar", "Carabobo", "Cojedes",
        "Delta Amacuro", "Distrito Capital", "Falcón", "Guárico", "Lara", "Mérida", "Miranda", "Monagas",
        "Nueva Esparta", "Portuguesa", "Sucre", "Táchira", "Trujillo", "La Guaira", "Yaracuy", "Zulia", "Dependencias"
    ];

    const municipios = [
        "Barinas", "Pedraza", "Antonio José de Sucre", "Ezequiel Zamora", "Bolívar", "Alberto Arvelo Torrealba", "Rojas", "Obispo", "Sosa", "Cruz Paredes", "Arismendi", "Andrés Eloy Blanco"
    ];

    const municipiosPorEstado = {
        "Amazonas": [
            "Alto Orinoco", "Atabapo", "Atures", "Autana", "Maroa", "Manapiare", "Río Negro"
        ],
        "Anzoátegui": [
            "Anaco", "Aragua", "Bolívar", "Bruzual", "Cajigal", "Carvajal", "Diego Bautista Urbaneja",
            "Freites", "Guanipa", "Guanta", "Independencia", "Libertad", "McGregor", "Miranda",
            "Monagas", "Peñalver", "Píritu", "San Juan de Capistrano", "Santa Ana", "Simón Rodríguez", "Sotillo"
        ],
        "Apure": [
            "Achaguas", "Biruaca", "Muñoz", "Páez", "Pedro Camejo", "Rómulo Gallegos", "San Fernando"
        ],
        "Aragua": [
            "Bolívar", "Camatagua", "Francisco Linares Alcántara", "Girardot", "José Ángel Lamas",
            "José Félix Ribas", "José Rafael Revenga", "Libertador", "Mario Briceño Iragorry",
            "Ocumare de la Costa de Oro", "San Casimiro", "San Sebastián", "Santiago Mariño",
            "Santos Michelena", "Sucre", "Tovar", "Urdaneta", "Zamora"
        ],
        "Barinas": [
            "Alberto Arvelo Torrealba", "Andrés Eloy Blanco", "Antonio José de Sucre", "Arismendi",
            "Barinas", "Bolívar", "Cruz Paredes", "Ezequiel Zamora", "Obispos", "Pedraza",
            "Rojas", "Sosa"
        ],
        "Bolívar": [
            "Caroní", "Cedeño", "El Callao", "Gran Sabana", "Heres", "Piar", "Raúl Leoni",
            "Roscio", "Sifontes", "Sucre", "Padre Pedro Chien"
        ],
        "Carabobo": [
            "Bejuma", "Carlos Arvelo", "Diego Ibarra", "Guacara", "Juan José Mora", "Libertador",
            "Los Guayos", "Miranda", "Montalbán", "Naguanagua", "Puerto Cabello", "San Diego", "San Joaquín", "Valencia"
        ],
        "Cojedes": [
            "Anzoátegui", "El Pao", "Falcón", "Girardot", "Lima Blanco", "Pao de San Juan Bautista",
            "Ricaurte", "Rómulo Gallegos", "San Carlos", "Tinaco"
        ],
        "Delta Amacuro": [
            "Antonio Díaz", "Casacoima", "Pedernales", "Tucupita"
        ],
        "Distrito Capital": [
            "Libertador"
        ],
        "Falcón": [
            "Acosta", "Bolívar", "Buchivacoa", "Cacique Manaure", "Carirubana", "Colina", "Dabajuro",
            "Democracia", "Falcón", "Federación", "Jacura", "Los Taques", "Mauroa", "Miranda",
            "Monseñor Iturriza", "Palmasola", "Petit", "Píritu", "San Francisco", "Silva",
            "Sucre", "Tocópero", "Unión", "Urumaco", "Zamora"
        ],
        "Guárico": [
            "Camaguán", "Chaguaramas", "El Socorro", "Francisco de Miranda", "José Félix Ribas",
            "José Tadeo Monagas", "Juan Germán Roscio", "Julián Mellado", "Las Mercedes", "Leonardo Infante",
            "Ortiz", "San Gerónimo de Guayabal", "San José de Guaribe", "Santa María de Ipire"
        ],
        "La Guaira": [
            "Vargas"
        ],
        "Lara": [
            "Andrés Eloy Blanco", "Crespo", "Iribarren", "Jiménez", "Morán", "Palavecino",
            "Simón Planas", "Torres", "Urdaneta"
        ],
        "Mérida": [
            "Alberto Adriani", "Andrés Bello", "Antonio Pinto Salinas", "Aricagua", "Arzobispo Chacón",
            "Campo Elías", "Caracciolo Parra Olmedo", "Cardenal Quintero", "Guaraque", "Julio César Salas",
            "Justo Briceño", "Libertador", "Miranda", "Obispo Ramos de Lora", "Padre Noguera", "Pueblo Llano",
            "Rangel", "Rivas Dávila", "Santos Marquina", "Sucre", "Tovar", "Tulio Febres Cordero", "Zea"
        ],
        "Miranda": [
            "Acevedo", "Andrés Bello", "Baruta", "Brión", "Buroz", "Carrizal", "Chacao", "Cristóbal Rojas",
            "El Hatillo", "Guaicaipuro", "Independencia", "Lander", "Los Salias", "Páez", "Paz Castillo",
            "Pedro Gual", "Plaza", "Simón Bolívar", "Sucre", "Urdaneta", "Zamora"
        ],
        "Monagas": [
            "Acosta", "Aguasay", "Bolívar", "Caripe", "Cedeño", "Ezequiel Zamora", "Libertador",
            "Maturín", "Piar", "Punceres", "Santa Bárbara", "Sotillo", "Uracoa"
        ],
        "Nueva Esparta": [
            "Antolín del Campo", "Arismendi", "Díaz", "García", "Gómez", "Maneiro", "Marcano",
            "Mariño", "Península de Macanao", "Tubores", "Villalba"
        ],
        "Portuguesa": [
            "Agua Blanca", "Araure", "Esteller", "Guanare", "Guanarito", "Monseñor José Vicente de Unda",
            "Ospino", "Páez", "Papelón", "San Genaro de Boconoito", "San Rafael de Onoto", "Santa Rosalía",
            "Sucre", "Turén"
        ],
        "Sucre": [
            "Andrés Eloy Blanco", "Andrés Mata", "Arismendi", "Benítez", "Bermúdez", "Bolívar",
            "Cajigal", "Cruz Salmerón Acosta", "Libertador", "Mariño", "Mejía", "Montes", "Ribero", "Sucre", "Valdez"
        ],
        "Táchira": [
            "Andrés Bello", "Antonio Rómulo Costa", "Ayacucho", "Bolívar", "Cárdenas", "Córdoba", "Fernández Feo",
            "Francisco de Miranda", "García de Hevia", "Guásimos", "Independencia", "Jáuregui", "José María Vargas",
            "Junín", "Libertad", "Libertador", "Lobatera", "Michelena", "Panamericano", "Pedro María Ureña",
            "Rafael Urdaneta", "Samuel Darío Maldonado", "San Cristóbal", "Seboruco", "Simón Rodríguez", "Sucre", "Torbes", "Uribante"
        ],
        "Trujillo": [
            "Andrés Bello", "Boconó", "Bolívar", "Candelaria", "Carache", "Escuque", "José Felipe Márquez Cañizales",
            "Juan Vicente Campos Elías", "La Ceiba", "Miranda", "Monte Carmelo", "Motatán", "Pampán",
            "Pampanito", "Rafael Rangel", "San Rafael de Carvajal", "Sucre", "Trujillo", "Urdaneta", "Valera"
        ],
        "Yaracuy": [
            "Arístides Bastidas", "Bolívar", "Bruzual", "Cocorote", "Independencia", "José Antonio Páez",
            "La Trinidad", "Manuel Monge", "Nirgua", "Peña", "San Felipe", "Sucre", "Urachiche", "Veroes"
        ],
        "Zulia": [
            "Almirante Padilla", "Baralt", "Cabimas", "Catatumbo", "Colón", "Francisco Javier Pulgar",
            "Guajira", "Jesús Enrique Lossada", "Jesús María Semprún", "La Cañada de Urdaneta", "Lagunillas",
            "Machiques de Perijá", "Mara", "Maracaibo", "Miranda", "Rosario de Perijá", "San Francisco",
            "Santa Rita", "Simón Bolívar", "Sucre", "Valmore Rodríguez"
        ]
    };

    const parroquiasPorMunicipio = {
        "Amazonas": {
            "Alto Orinoco": ["La Esmeralda", "Huachamacare", "Marawaka", "Mavaca", "Sierra Parima"],
            "Atabapo": ["San Fernando de Atabapo", "Ucata", "Yapacana", "Caname"],
            "Atures": ["Fernando Girón Tovar", "Luis Alberto Gómez", "Parhueña", "Platanillal"],
            "Autana": ["Isla de Ratón", "Samariapo", "Sipapo", "Munduapo", "Guayapo"],
            "Maroa": ["Maroa", "Comunidad", "Victorino"],
            "Manapiare": ["San Juan de Manapiare", "Alto Ventuari", "Medio Ventuari", "Bajo Ventuari"],
            "Río Negro": ["San Carlos de Río Negro", "Solano", "Casiquiare", "Cocuy"]
        },
        "Anzoátegui": {
            "Anaco": ["Anaco", "San Joaquín"],
            "Aragua": ["Aragua de Barcelona", "Cachipo"],
            "Fernando de Peñalver": ["Puerto Píritu", "San Miguel", "Sucre"],
            "Francisco del Carmen Carvajal": ["Valle de Guanape", "Santa Bárbara"],
            "Francisco de Miranda": ["Pariaguán"],
            "Guanta": ["Guanta", "Chorrerón"],
            "Independencia": ["Soledad"],
            "José Gregorio Monagas": ["Mapire", "Piar", "Santa Clara", "San Diego de Cabrutica", "Uverito", "Zuata"],
            "Juan Antonio Sotillo": ["Puerto La Cruz"],
            "Juan Manuel Cajigal": ["Onoto", "San Pablo"],
            "Libertad": ["San Mateo", "El Carito", "Santa Inés"],
            "Manuel Ezequiel Bruzual": ["Clarines", "Guanape", "Sabana de Uchire"],
            "Pedro María Freites": ["Cantaura", "Libertador", "Santa Rosa", "Urica"],
            "Píritu": ["Píritu", "San Francisco"],
            "San José de Guanipa": ["San José de Guanipa"],
            "San Juan de Capistrano": ["Boca de Uchire", "Boca de Chávez"],
            "Santa Ana": ["Santa Ana", "Boca de Santa Ana"],
            "Simón Bolívar": ["Bergantín", "Caigua", "El Carmen", "El Pilar", "Naricual", "San Cristóbal"],
            "Simón Rodríguez": ["El Tigre"]
        },
        "Apure": {
            "Achaguas": ["Achaguas", "Apurito", "El Yagual", "Guachara", "Mucuritas", "Queseras del Medio"],
            "Biruaca": ["Biruaca"],
            "Muñoz": ["Bruzual", "Mantecal", "Quintero", "Rincón Hondo", "San Vicente"],
            "Páez": ["Guasdualito", "Aramendi", "El Amparo", "San Camilo", "Urdaneta"],
            "Pedro Camejo": ["San Juan de Payara", "Codazzi", "Cunaviche"],
            "Rómulo Gallegos": ["Elorza", "La Trinidad"],
            "San Fernando": ["San Fernando", "El Recreo", "Peñalver", "San Rafael de Atamaica"]
        },
        "Aragua": {
            "Bolívar": ["San Mateo"],
            "Camatagua": ["Camatagua", "Carmen de Cura"],
            "Francisco Linares Alcántara": ["Santa Rita", "Francisco de Miranda", "Monseñor Feliciano González"],
            "Girardot": ["Pedro José Ovalles", "Joaquín Crespo", "José Casanova Godoy", "Madre María de San José", "Andrés Eloy Blanco", "Los Tacarigua", "Las Delicias", "Choroní"],
            "José Ángel Lamas": ["Santa Cruz"],
            "José Félix Ribas": ["Victoria", "Zuata", "La Quebrada", "Pao de Zárate", "Castor Nieves Ríos"],
            "José Rafael Revenga": ["El Consejo"],
            "Libertador": ["Palo Negro", "San Martín de Porres"],
            "Mario Briceño Iragorry": ["El Limón", "Caña de Azúcar"],
            "Ocumare de la Costa de Oro": ["Ocumare de la Costa"],
            "San Casimiro": ["San Casimiro", "Güiripa", "Ollas de Caramacate", "Valle Morín"],
            "San Sebastián": ["San Sebastián"],
            "Santiago Mariño": ["Turmero", "Arévalo Aponte", "Chuao", "Samán de Güere", "Alfredo Pacheco Miranda"],
            "Santos Michelena": ["Las Tejerías", "Tiara"],
            "Sucre": ["Cagua", "Bella Vista"],
            "Tovar": ["Colonia Tovar"],
            "Urdaneta": ["Barbacoas", "Las Peñitas", "San Francisco de Cara", "Taguay"],
            "Zamora": ["Villa de Cura", "Magdaleno", "San Francisco de Asís", "Valles de Tucutunemo", "Augusto Mijares"]
        },
        "Trujillo": {
            "Andrés Bello": ["Santa Isabel", "Araguaney", "El Jaguito", "La Esperanza"],
            "Boconó": ["Boconó", "Ayacucho", "Burbusay", "El Carmen", "General Ribas", "Guaramacal", "Monseñor Jáuregui", "Mosquey", "Rafael Rangel", "San José", "San Miguel", "Vega de Guaramacal"],
            "Bolívar": ["Sabana Grande", "Cheregüé", "Granados"],
            "Candelaria": ["Chejendé", "Arnoldo Gabaldón", "Bolivia", "Carrillo", "Cegarra", "Manuel Salvador Ulloa", "San José"],
            "Carache": ["Carache", "Cuicas", "La Concepción", "Panamericana", "Santa Cruz"],
            "Escuque": ["Escuque", "La Unión", "Sabana Libre", "Santa Rita"],
            "José Felipe Márquez Cañizales": ["El Socorro", "Antonio José de Sucre", "Los Caprichos"],
            "Juan Vicente Campo Elías": ["Campo Elia", "La Placita", "Los Caprichos"],
            "La Ceiba": ["Santa Apolonia", "Zona Rica", "La Ceiba"],
            "Miranda": ["El Dividive", "Agua Santa", "Agua Caliente", "El Cenizo", "Valerita"],
            "Monte Carmelo": ["Monte Carmelo", "Buena Vista", "Casa de Tabla"],
            "Motatán": ["Motatán", "El Baño", "Jalisco"],
            "Pampán": ["Pampán", "Flor de Patria", "Monay", "Santa Ana"],
            "Pampanito": ["Pampanito", "La concepción", "Pampanito II"],
            "parroquias": ["Betijoque", "José Gregorio Hernández", "La Pueblita", "Los Cedros"],
            "San Rafael de Carvajal": ["Carvajal", "La Cejita", "Campo Alegre", "Las Mesetas"],
            "Sucre": ["Sabana de Mendoza", "El Paraiso", "Junín", "Valmore Rodríguez"],
            "Trujillo": ["Trujillo", "San Lázaro", "Chiquinquirá", "Santa Rosa", "La Plazuela", "San Jacinto", "Tres Esquinas"],
            "Urdaneta": ["Cabimbú", "Jajó", "La Mesa de Esnujaque", "Santiago", "Tuñame", "La Quebrada"],
            "Valera": ["Juan Ignacio Montilla", "La Beatriz", "La Puerta", "Mendoza", "Mercedes Díaz", "San Luis"]
        },
        "Barinas": {
            "Alberto Arvelo Torrealba": ["Sabaneta", "Rodríguez Domínguez"],
            "Andrés Eloy Blanco": ["El Cantón", "Santa Cruz de Guacas", "Puerto Vivas"],
            "Antonio José de Sucre": ["Socopó"],
            "Arismendi": ["Arismendi", "Guadarrama", "La Unión", "San Antonio"],
            "Barinas": ["Alto Barinas", "Alberto Arvelo Larriva", "San Silvestre", "Santa Inés", "Santa Lucía", "Torunos", "El Carmen", "Rómulo Betancourt", "Corazón de Jesús", "Ramón Ignacio Méndez", "Manuel Palacio Fajardo", "Juan Antonio Rodríguez Domínguez", "Domingo Ortiz de Páez"],
            "Bolívar": ["Barinitas", "Altamira de Cáceres", "Calderas"],
            "Cruz Paredes": ["Barrancas", "El Socorro", "Masparrito"],
            "Ezequiel Zamora": ["Santa Bárbara", "José Ignacio del Pumar", "Pedro Briceño Méndez", "Ramón Ignacio Méndez"],
            "Obispo": ["Obispos", "El Real", "La Luz", "Los Guasimitos"],
            "Pedraza": ["Ciudad Bolivia", "Ignacio Briceño", "José Félix Ribas", "Páez"],
            "Rojas": ["Libertad", "Dolores", "Palacios Fajardo", "Santa Rosa", "Simón Rodríguez"],
            "Sosa": ["Ciudad de Nutrias", "El Regalo", "Puerto de Nutrias", "Santa Catalina", "Simón Bolívar"]
        },
        "Bolívar": {
            "Caroní": ["Ciudad Guayana", "Parroquia Cachamay", "Parroquia Chirica", "Parroquia Dalla Costa", "Parroquia Simón Bolívar", "Parroquia Unare"],
            "Cedeño": ["Caicara del Orinoco", "Altagracia", "Ascensión Farreras", "Guaniamo", "La Urbana"],
            "Gran Sabana": ["Ikabarú", "Kavanayén", "Santa Elena de Uairén"],
            "Heres": ["Ciudad Bolívar", "Catedral", "Simón Bolívar", "Marhuanta"],
            "Piar": ["Aripao", "El Pao", "Upata", "San Félix", "El Manteco", "Tumeremo"],
            "Roscio": ["Guasipati", "El Callao"],
            "Sifontes": ["El Dorado", "Tumeremo", "San Isidro"],
            "Sucre": ["Maripa", "Barbacoa", "El Pao"]
        },
        "Carabobo": {
            "Bejuma": ["Bejuma", "Canoabo", "Simón Bolívar", "Fraternidad", "José Rafael Pulgar"],
            "Carlos Arvelo": ["Güigüe", "Tocuyito", "Unión", "Miranda", "Independencia", "Puerto Cabello"],
            "Juan José Mora": ["Morón", "Guacara", "Begoña", "Yagua", "Tacarigua"],
            "Libertador": ["Naguanagua", "San Joaquín", "Morón", "Valencia"],
            "Los Guayos": ["Los Guayos", "Catedral", "Guacara", "Tocuyito"],
            "Puerto Cabello": ["Puerto Cabello", "Bartolomé Salom", "Unión", "Borburata", "Juan José Flores"],
            "San Diego": ["San Diego", "Dallago", "Cascabel", "Vigirima"],
            "San Joaquín": ["San Joaquín", "El Pao", "Quirindai", "Nicolas Pulido"]
        },
        "Cojedes": {
            "Anzoátegui": ["Macapo", "El Baúl", "Puerto Colorado"],
            "Cojedes": ["San Carlos", "Juan de Mata Suárez", "Ramón Ignacio Méndez", "Libertad", "El Pao", "Evaristo Fernández"],
            "Ricaurte": ["Libertad", "El Amparo", "La Aguadita", "Monte Verde"],
            "Pao de San Juan Bautista": ["Pao", "El Baúl", "Las Vegas", "Santa Apolonia"],
            "Tinaco": ["Tinaco", "San Carlos", "Sucre", "Santa Inés"]
        },
        "Delta Amacuro": {
            "Antonio Díaz": ["Antonio Díaz", "Boca de Uracoa", "Boca de Tucupita"],
            "Casacoima": ["Casacoima", "Pedernales", "Tucupita", "El Triunfo"],
            "Tucupita": ["San José de Tucupita", "Boca de Manamo", "Curiapo", "Parguaza"]
        },
        "Falcón": {
            "Buchivacoa": ["Churuguara", "Las Calderas", "Caujaro", "Pueblo Nuevo"],
            "Carirubana": ["Punto Fijo", "Judibana", "Santa Ana"],
            "Colina": ["Chichiriviche", "La Vela de Coro", "Capanaparo", "Cumarebo"],
            "Dabajuro": ["Dabajuro", "Mene de Mauroa"],
            "Falcón": ["Coro", "Santa Ana", "Tocuyo de la Costa", "San Luis"],
            "José Laurencio Silva": ["Judibana", "Santa Ana", "Pueblo Nuevo"],
            "Los Taques": ["Los Taques", "Judibana", "Santa Cruz de Los Taques"],
            "Mauroa": ["Mauroa", "Mene de Mauroa"],
            "Miranda": ["Miranda", "Pueblo Nuevo", "La Vela de Coro"],
            "Monseñor Iturriza": ["Monseñor Iturriza", "Judibana", "Santa Ana"]
        },
        "Guárico": {
            "Camaguán": ["Camaguán", "Uverito", "Chaguaramas"],
            "Chaguaramas": ["Chaguaramas", "El Socorro", "Las Mercedes del Llano"],
            "El Socorro": ["El Socorro", "Las Mercedes del Llano", "San Juan de los Morros"],
            "José Félix Ribas": ["Ortiz", "Tucupido", "Altagracia de Orituco"],
            "Juan Germán Roscio": ["Calabozo", "Las Mercedes", "El Sombrero"],
            "Las Mercedes": ["Las Mercedes", "Ortiz", "Valle de la Pascua"],
            "Leonardo Infante": ["El Sombrero", "Ortiz"],
            "Pedro Zaraza": ["Zaraza", "San José de Unare", "Ortiz"],
            "San Gerónimo de Guayabal": ["San Gerónimo de Guayabal"],
            "Valle de la Pascua": ["Valle de la Pascua", "Calabozo", "San Juan de Los Morros"]
        },
        "Lara": {
            "Iribarren": ["Barquisimeto", "Juan de Villegas", "Santa Rosa", "Atarigua", "Guacara"],
            "Morán": ["El Tocuyo", "Cubiro", "Duaca", "La Aguadita"],
            "Palavecino": ["Cabudare", "Judibana", "Moroturo"],
            "Simón Planas": ["Sarare", "Buría", "Guanare"],
            "Torres": ["Carora", "Aguada Grande", "Bobare"]
        },
        "Mérida": {
            "Alberto Adriani": ["Ejido", "La Azulita", "Lagunillas", "Mucuchíes", "Mucujepe"],
            "Andrés Bello": ["La Pedrera", "Santa Elena de Arenales"],
            "Antonio Pinto Salinas": ["Mérida", "Santa Cruz de Mora"],
            "Aricagua": ["Aricagua", "Chachopo"],
            "Arzobispo Chacón": ["Canagua", "Chiguará", "San Juan"],
            "Campo Elías": ["Ejido", "El Vigía", "Jají"],
            "Caracciolo Parra Olmedo": ["Tabay", "Timotes", "Tucaní"]
        },
        "Miranda": {
            "Acevedo": ["Petare", "Guarenas", "Guatire"],
            "Baruta": ["Baruta", "El Cafetal"],
            "Brión": ["Mamporal", "Curiepe"],
            "Carrizal": ["Carrizal", "Paracotos"],
            "Chacao": ["Chacao", "El Rosal"],
            "Cristóbal Rojas": ["Charallave", "Cúa"],
            "El Hatillo": ["El Hatillo", "La Lagunita"],
            "Los Salias": ["San Antonio de Los Altos", "Carrizal"],
            "Sucre": ["Petare", "Petare Central"],
            "Tomás Lander": ["Ocumare del Tuy", "Santa Teresa del Tuy"]
        },
        "Monagas": {
            "Acosta": ["San Antonio", "Quiriquire"],
            "Aguasay": ["Aguasay", "Jusepín"],
            "Ezequiel Zamora": ["Punta de Mata", "Temblador"],
            "Libertador": ["Temblador", "Temblador"],
            "Maturín": ["Maturín", "San Simón"],
            "Piar": ["Aragua de Maturín", "El Furrial"],
            "Santa Bárbara": ["Santa Bárbara", "Punta de Mata"],
            "Uracoa": ["Uracoa", "Barrancas"]
        },
        "Nueva Esparta": {
            "Antolín del Campo": ["La Plaza de Paraguachí", "Villa Rosa"],
            "Arismendi": ["La Asunción", "El Cercado"],
            "García": ["Porlamar", "Pampatar"],
            "Maneiro": ["Punta de Piedras", "El Valle del Espíritu Santo"],
            "Mariño": ["Porlamar", "Pampatar"]
        },
        "Portuguesa": {
            "Agua Blanca": ["Agua Blanca", "Los Cedros"],
            "Araure": ["Araure", "Ospino"],
            "Esteller": ["Biscucuy", "Guanare"],
            "Guanare": ["Guanare", "Biscucuy"],
            "Ospino": ["Ospino", "Píritu"],
            "Papelón": ["Papelón", "Mesa de Cavaca"],
            "San Genaro de Boconoíto": ["Boconoíto", "Mesa de Cavaca"],
            "Guanarito": ["Guanarito", "Trinidad de la Capilla", "Divina Pastora"]
        },
        "Sucre": {
            "Andrés Mata": ["Cumaná", "Guaraguao"],
            "Benítez": ["Carúpano", "El Pilar"],
            "Bermúdez": ["Cumanacoa", "Boca de Uchire"],
            "Bolívar": ["Santa Fe", "San Antonio"],
            "Cajigal": ["Río Caribe", "Catuaro"],
            "Libertador": ["Tunapuy", "Cariaco"],
            "Maturín": ["El Furrial", "San Antonio de Maturín"],
            "Ribero": ["Cariaco", "San José de Aerocuar"],
            "Valdez": ["Cumanacoa", "Marigüitar"]
        },
        "Distrito Capital": {
            "Libertador": [
                "23 de Enero", "Altagracia", "Catedral", "Coche", "El Paraíso",
                "El Recreo", "El Valle", "La Pastora", "La Vega", "Macarao",
                "San Agustín", "San Bernardino", "San José", "San Juan",
                "Santa Rosalía", "Santa Teresa"
            ]
        },
        "La Guaira": {
            "Vargas": [
                "Carayaca", "Caraballeda", "Catia La Mar", "El Junko",
                "La Guaira", "Macuto", "Naiguatá", "Caribe", "Maiquetía"
            ]
        },
        "Zulia": {
            "Almirante Padilla": [
                "Isla de Toas", "Monagas"
            ],
            "Baralt": [
                "San Timoteo", "General Urdaneta", "Libertador",
                "Marcelino Briceño", "Pueblo Nuevo", "Manuel Guanipa Matos"
            ],
            "Cabimas": [
                "Ambrosio", "Arístides Calvani", "Carmen Herrera",
                "Germán Ríos Linares", "Jorge Hernández", "La Rosa",
                "Punta Gorda", "Rómulo Betancourt", "San Benito"
            ],
            "Catatumbo": [
                "Encontrados", "Udón Pérez"
            ],
            "Colón": [
                "San Carlos del Zulia", "Moralito", "Santa Bárbara",
                "Santa Cruz del Zulia", "Urribarrí"
            ],
            "Francisco Javier Pulgar": [
                "Simón Rodríguez", "Agustín Codazzi",
                "Carlos Quevedo", "Francisco Javier Pulgar"
            ],
            "Guajira": [
                "Sinamaica", "Alta Guajira",
                "Elías Sánchez Rubio", "Guajira"
            ],
            "Jesús Enrique Lossada": [
                "La Concepción", "San José",
                "Mariano Parra León", "José Ramón Yépez"
            ],
            "Jesús María Semprún": [
                "Jesús María Semprún", "Barí"
            ],
            "La Cañada de Urdaneta": [
                "Concepción", "Andrés Bello",
                "Chiquinquirá", "El Carmelo", "Potreritos"
            ],
            "Lagunillas": [
                "Libertad", "Alonso de Ojeda",
                "Venezuela", "Eleazar López Contreras", "Campo Lara"
            ],
            "Machiques de Perijá": [
                "Bartolomé de las Casas", "Libertad",
                "Río Negro", "San José de Perijá"
            ],
            "Mara": [
                "San Rafael", "La Sierrita", "Las Parcelas",
                "Luis de Vicente", "Monseñor Marcos Sergio Godoy",
                "Ricaurte", "Tamare"
            ],
            "Maracaibo": [
                "Antonio Borjas Romero", "Bolívar", "Cacique Mara",
                "Carracciolo Parra Pérez", "Cecilio Acosta", "Cristo de Aranza",
                "Coquivacoa", "Chiquinquirá", "Francisco Eugenio Bustamante",
                "Idelfonso Vásquez", "Juana de Ávila", "Luis Hurtado Higuera",
                "Manuel Dagnino", "Olegario Villalobos", "Raúl Leoni",
                "Santa Lucía", "San Isidro", "Venancio Pulgar"
            ],
            "Miranda": [
                "Altagracia", "Faría", "Ana María Campos",
                "San Antonio", "San José"
            ],
            "Rosario de Perijá": [
                "Donaldo García", "El Rosario", "Sixto Zambrano"
            ],
            "San Francisco": [
                "San Francisco", "El Bajo", "Domitila Flores",
                "Francisco Ochoa", "Los Cortijos", "Marcial Hernández",
                "José Domingo Rus"
            ],
            "Santa Rita": [
                "Santa Rita", "El Mene", "Pedro Lucas Urribarrí",
                "José Cenobio Urribarrí"
            ],
            "Simón Bolívar": [
                "Rafael María Baralt", "Manuel Manrique", "Rafael Urdaneta"
            ],
            "Sucre": [
                "Bobures", "Gibraltar", "Heras",
                "Monseñor Arturo Álvarez", "Rómulo Gallegos", "El Batey"
            ],
            "Valmore Rodríguez": [
                "Rafael Urdaneta", "La Victoria", "Raúl Cuenca"
            ]
        }
    };

    const parroquiasPorMunicipioResidencia = {
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

    function cargarPaises() {
        select_actualizar_pais_nacimiento.innerHTML = "";

        paises.forEach(paises => {
            const opcion = document.createElement("option");
            opcion.value = paises;
            opcion.textContent = paises;
            select_actualizar_pais_nacimiento.appendChild(opcion);
        });
    }
    cargarPaises();

    function cargarEstados() {
        select_actualizar_estado_nacimiento.innerHTML = "";

        Estado.forEach(estado => {
            const opcion = document.createElement("option");
            opcion.value = estado;
            opcion.textContent = estado;
            select_actualizar_estado_nacimiento.appendChild(opcion);
        });
    }
    cargarEstados();

    function cargarMunicipios(municipioSeleccionado = "") {

        const estado = select_actualizar_estado_nacimiento.value;

        select_actualizar_municipio_nacimiento.innerHTML = "";

        if (estado in municipiosPorEstado) {

            municipiosPorEstado[estado].forEach(municipio => {

                const option = document.createElement("option");
                option.value = municipio;
                option.textContent = municipio;

                if (municipio === municipioSeleccionado) {
                    option.selected = true;
                }

                select_actualizar_municipio_nacimiento.appendChild(option);
            });

            if (!municipioSeleccionado) {
                select_actualizar_municipio_nacimiento.selectedIndex = 0;
            }
        }
    }

    function cargarParroquias(parroquiaSeleccionada = "") {
        const estado = select_actualizar_estado_nacimiento.value;
        const municipio = select_actualizar_municipio_nacimiento.value;

        select_actualizar_parroquia_nacimiento.innerHTML = "";

        if (parroquiasPorMunicipio[estado] && parroquiasPorMunicipio[estado][municipio]) {

            parroquiasPorMunicipio[estado][municipio].forEach(parroquia => {

                const option = document.createElement("option");
                option.value = parroquia;
                option.textContent = parroquia;

                if (parroquia === parroquiaSeleccionada) {
                    option.selected = true;
                }

                select_actualizar_parroquia_nacimiento.appendChild(option);
            });

            if (!parroquiaSeleccionada) {
                select_actualizar_parroquia_nacimiento.selectedIndex = 0;
            }
        }
    }

    select_actualizar_estado_nacimiento.addEventListener("change", () => {
        cargarMunicipios();
        cargarParroquias();
    });

    select_actualizar_municipio_nacimiento.addEventListener("change", () => {
        cargarParroquias();
    });

    function cargarMunicipiosResidencia(municipioSeleccionado = "") {
        select_actualizar_municipio_residencia.innerHTML = "";

        municipios.forEach(municipio => {

            const option = document.createElement("option");
            option.value = municipio;
            option.textContent = municipio;

            if (municipio === municipioSeleccionado) {
                option.selected = true;
            }

            select_actualizar_municipio_residencia.appendChild(option);
        });

        if (!municipioSeleccionado) {
            select_actualizar_municipio_residencia.selectedIndex = 0;
        }
    }
    cargarMunicipiosResidencia();

    function cargarParroquiasResidencia(parroquiaSeleccionada = "") {

        const municipio = select_actualizar_municipio_residencia.value;

        select_actualizar_parroquia_residencia.innerHTML = "";

        if (municipio in parroquiasPorMunicipioResidencia) {

            parroquiasPorMunicipioResidencia[municipio].forEach(parroquia => {

                const option = document.createElement("option");
                option.value = parroquia;
                option.textContent = parroquia;

                if (parroquia === parroquiaSeleccionada) {
                    option.selected = true;
                }

                select_actualizar_parroquia_residencia.appendChild(option);
            });

            if (!parroquiaSeleccionada) {
                select_actualizar_parroquia_residencia.selectedIndex = 0;
            }
        }
    }
    cargarParroquiasResidencia();

    select_actualizar_municipio_residencia.addEventListener("change", () => {
        cargarParroquiasResidencia();
    });

    // VALIDAR CAMPOS CRITICOS
    async function validar_ci(nacionalidad, cedula, msg) {
        if (!nacionalidad.value || !cedula.value.trim()) {
            msg.textContent = "";
            msg.classList.remove("exito", "error");

            cedula.setCustomValidity("");
            cedula.classList.remove("is-valid", "is-invalid");

            btn_actualizar.disabled = true;
            return;
        }

        try {
            const formulario = new FormData();

            formulario.append("nacionalidad", nacionalidad.value);
            formulario.append("cedula", cedula.value);
            formulario.append("id_usuario", input_id_usuario.value);

            const respuesta = await fetch("/validar_ci/", {
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

            if (resultado.existe) {

                cedula.setCustomValidity(
                    "Ya se encuentra la cédula de identidad registrada."
                );

                cedula.classList.add("is-invalid");
                cedula.classList.remove("is-valid");

                msg.textContent =
                    "Ya se encuentra la cédula de identidad registrada.";

                msg.classList.add("error");
                msg.classList.remove("exito");

                btn_actualizar.disabled = true;

            } else {

                cedula.setCustomValidity("");

                cedula.classList.add("is-valid");
                cedula.classList.remove("is-invalid");

                msg.textContent =
                    "Cédula de Identidad disponible.";

                msg.classList.add("exito");
                msg.classList.remove("error");

                btn_actualizar.disabled = false;
            }

        } catch (error) {
            console.error("Error al validar la cédula:", error);
        }
    }

    input_actualizar_cedula.addEventListener("input", async () => {
        const nacionalidad = select_actualizar_nacionalidad.value;
        const cedula = input_actualizar_cedula.value.trim();

        // Sin nacionalidad o cédula vacía
        if (!nacionalidad || !cedula) {
            contenedor_mensaje_ci.textContent = "";
            contenedor_mensaje_ci.classList.remove("exito", "error"); // Limpia estilos de caja

            input_actualizar_cedula.setCustomValidity("");
            input_actualizar_cedula.classList.remove("is-valid", "is-invalid");
            return;
        }

        let longitudMinima;
        let longitudMaxima;

        switch (nacionalidad) {
            case "V":
                longitudMinima = 7;
                longitudMaxima = 8;
                break;
            case "E":
                longitudMinima = 8;
                longitudMaxima = 10;
                break;
            default:
                return;
        }

        // Todavía no tiene la longitud mínima o supera la máxima
        if (cedula.length < longitudMinima || cedula.length > longitudMaxima) {
            contenedor_mensaje_ci.textContent = "";
            contenedor_mensaje_ci.classList.remove("exito", "error"); // Limpia estilos de caja

            input_actualizar_cedula.setCustomValidity(`La cédula debe tener entre ${longitudMinima} y ${longitudMaxima} números.`);
            input_actualizar_cedula.classList.remove("is-valid");
            input_actualizar_cedula.classList.add("is-invalid");
            return;
        }

        // Longitud correcta → consultar al servidor
        await validar_ci(select_actualizar_nacionalidad, input_actualizar_cedula, contenedor_mensaje_ci);
    });

    select_actualizar_nacionalidad.addEventListener("change", async () => {
        await validar_ci(select_actualizar_nacionalidad, input_actualizar_cedula, contenedor_mensaje_ci);
    });

    let controlador_correo = null;

    async function validar_correo(correo, dominio, msg) {
        const valorCorreo = correo.value.trim();
        const valorDominio = dominio.value;

        if (controlador_correo) {
            controlador_correo.abort();
        }

        if (!valorDominio || !valorCorreo) {
            msg.textContent = "";
            msg.classList.remove("exito", "error");

            correo.setCustomValidity("");
            correo.classList.remove("is-valid", "is-invalid");

            btn_actualizar.disabled = true;
            return;
        }

        controlador_correo = new AbortController();

        try {
            const formulario = new FormData();

            formulario.append("correo", valorCorreo);
            formulario.append("dominio", valorDominio);
            formulario.append("id_usuario", input_id_usuario.value);

            const respuesta = await fetch("/validar_email/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector(
                        "[name=csrfmiddlewaretoken]"
                    ).value
                },
                body: formulario,
                signal: controlador_correo.signal
            });

            const resultado = await respuesta.json();

            console.log(resultado);

            if (
                correo.value.trim() !== valorCorreo ||
                dominio.value !== valorDominio
            ) {
                return;
            }

            if (resultado.existe) {
                correo.setCustomValidity(
                    "Ya existe un usuario con este correo electrónico."
                );

                correo.classList.add("is-invalid");
                correo.classList.remove("is-valid");

                msg.textContent =
                    "Ya existe un usuario con este correo electrónico.";

                msg.classList.add("error");
                msg.classList.remove("exito");

                btn_actualizar.disabled = true;

            } else {
                correo.setCustomValidity("");

                correo.classList.add("is-valid");
                correo.classList.remove("is-invalid");

                msg.textContent =
                    "El correo electrónico está disponible.";

                msg.classList.add("exito");
                msg.classList.remove("error");

                btn_actualizar.disabled = false;
            }
        } catch (error) {
            if (error.name === "AbortError") {
                return;
            }

            console.error("Error al validar el correo:", error);
        }
    }

    input_actualizar_correo_principal.addEventListener("input", async () => {
        await validar_correo(input_actualizar_correo_principal, select_actualizar_dominio_principal, contenedor_mensaje_correo_principal);
    });

    select_actualizar_dominio_principal.addEventListener("change", async () => {
        await validar_correo(input_actualizar_correo_principal, select_actualizar_dominio_principal, contenedor_mensaje_correo_principal);
    });

    input_actualizar_correo_secundario.addEventListener("input", async () => {
        await validar_correo(input_actualizar_correo_secundario, select_actualizar_dominio_secundario, contenedor_mensaje_correo_secundario);
    });

    select_actualizar_dominio_secundario.addEventListener("change", async () => {
        await validar_correo(input_actualizar_correo_secundario, select_actualizar_dominio_secundario, contenedor_mensaje_correo_secundario);
    });

    let controlador_nombre_usuario = null;

    async function validar_nombre_usuario() {
        const nombre_usuario = input_actualizar_nombre_usuario.value.trim();

        if (controlador_nombre_usuario) {
            controlador_nombre_usuario.abort();
        }

        if (!nombre_usuario) {
            contenedor_mensaje_nombre_usuario.textContent = "";
            contenedor_mensaje_nombre_usuario.classList.remove("exito", "error");

            input_actualizar_nombre_usuario.setCustomValidity("");
            input_actualizar_nombre_usuario.classList.remove("is-valid", "is-invalid");

            btn_actualizar.disabled = true;
            return;
        }

        controlador_nombre_usuario = new AbortController();

        try {
            const formulario = new FormData();

            formulario.append("nombre_usuario", nombre_usuario);
            formulario.append("id_usuario", input_id_usuario.value);

            const respuesta = await fetch("/validar_nombre_usuario/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector(
                        "[name=csrfmiddlewaretoken]"
                    ).value
                },
                body: formulario,
                signal: controlador_nombre_usuario.signal
            });

            const resultado = await respuesta.json();

            console.log(resultado);

            if (
                input_actualizar_nombre_usuario.value.trim() !== nombre_usuario
            ) {
                return;
            }

            if (resultado.existe) {
                input_actualizar_nombre_usuario.setCustomValidity(
                    "Ya existe un nombre de usuario."
                );

                input_actualizar_nombre_usuario.classList.add("is-invalid");
                input_actualizar_nombre_usuario.classList.remove("is-valid");

                contenedor_mensaje_nombre_usuario.textContent =
                    "Ya existe un nombre de usuario.";

                contenedor_mensaje_nombre_usuario.classList.add("error");
                contenedor_mensaje_nombre_usuario.classList.remove("exito");

                btn_actualizar.disabled = true;

            } else {
                input_actualizar_nombre_usuario.setCustomValidity("");

                input_actualizar_nombre_usuario.classList.add("is-valid");
                input_actualizar_nombre_usuario.classList.remove("is-invalid");

                contenedor_mensaje_nombre_usuario.textContent =
                    "El nombre de usuario está disponible.";

                contenedor_mensaje_nombre_usuario.classList.add("exito");
                contenedor_mensaje_nombre_usuario.classList.remove("error");

                btn_actualizar.disabled = false;
            }

        } catch (error) {
            if (error.name === "AbortError") {
                return;
            }

            console.error("Error al validar el nombre de usuario:", error);
        }
    }
    input_actualizar_nombre_usuario.addEventListener("input", validar_nombre_usuario)

    let controlador_contrasenia = null;

    async function validar_contrasenia() {
        const clave = input_actualizar_contrasenia.value.trim();

        if (controlador_contrasenia) {
            controlador_contrasenia.abort();
        }

        if (!clave) {
            contenedor_mensaje_contrasenia.textContent = "";
            contenedor_mensaje_contrasenia.classList.remove("exito", "error");

            input_actualizar_contrasenia.setCustomValidity("");
            input_actualizar_contrasenia.classList.remove("is-valid", "is-invalid");

            btn_actualizar.disabled = true;
            return;
        }

        controlador_contrasenia = new AbortController();

        try {
            const formulario = new FormData();

            formulario.append("clave", clave);
            formulario.append("id_usuario", input_id_usuario.value);

            const respuesta = await fetch("/validar_contrasenia/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector(
                        "[name=csrfmiddlewaretoken]"
                    ).value
                },
                body: formulario,
                signal: controlador_contrasenia.signal
            });

            const resultado = await respuesta.json();

            if (input_actualizar_contrasenia.value.trim() !== clave) {
                return;
            }

            console.log(resultado);

            if (resultado.existe) {
                input_actualizar_contrasenia.setCustomValidity(
                    "Ya se encuentra la contraseña registrada."
                );

                input_actualizar_contrasenia.classList.add("is-invalid");
                input_actualizar_contrasenia.classList.remove("is-valid");

                contenedor_mensaje_contrasenia.textContent =
                    "Ya se encuentra la contraseña registrada.";

                contenedor_mensaje_contrasenia.classList.add("error");
                contenedor_mensaje_contrasenia.classList.remove("exito");

                btn_actualizar.disabled = true;

            } else {
                input_actualizar_contrasenia.setCustomValidity("");

                input_actualizar_contrasenia.classList.add("is-valid");
                input_actualizar_contrasenia.classList.remove("is-invalid");

                contenedor_mensaje_contrasenia.textContent =
                    "Contraseña disponible.";

                contenedor_mensaje_contrasenia.classList.add("exito");
                contenedor_mensaje_contrasenia.classList.remove("error");

                btn_actualizar.disabled = false;
            }

        } catch (error) {
            if (error.name === "AbortError") {
                return;
            }

            console.error("Error al validar la contraseña:", error);
        }
    }
    input_actualizar_contrasenia.addEventListener("input", validar_contrasenia);

    // BLOQUEAR LOS CONTROLES ANTES DE LA BUSQUEDA DE LOS DATOS
    const controles_actualizacion = [
        input_actualizar_nombre,
        input_actualizar_apellido,
        input_actualizar_cedula,
        select_actualizar_nacionalidad,
        select_actualizar_genero,
        select_actualizar_estado_civil,
        input_actualizar_nombre_usuario,
        input_actualizar_contrasenia,

        input_actualizar_num_telefono_principal,
        select_actualizar_prefijo_principal,
        input_actualizar_num_telefono_secundario,
        select_actualizar_prefijo_secundario,

        input_actualizar_correo_principal,
        select_actualizar_dominio_principal,
        input_actualizar_correo_secundario,
        select_actualizar_dominio_secundario,

        select_actualizar_pais_nacimiento,

        select_actualizar_estado_nacimiento,
        input_actualizar_estado_vzla_nacimiento,

        select_actualizar_municipio_nacimiento,
        input_actualizar_municipio_vzla_nacimiento,

        select_actualizar_parroquia_nacimiento,
        input_actualizar_parroquia_vzla_nacimiento,

        textarea_actualizar_direccion_nacimiento,
        input_actualizar_fecha_nacimiento,

        select_actualizar_condicion_residencia,
        select_actualizar_municipio_residencia,
        select_actualizar_parroquia_residencia,
        textarea_actualizar_direccion_residencia,
        btn_actualizar
    ];

    function bloquearFormularioActualizar(bloquear = true) {
        controles_actualizacion.forEach(control => {
            if (control) {
                control.disabled = bloquear;
            }
        });
    }
    bloquearFormularioActualizar(true);

    textarea_actualizar_direccion_nacimiento.addEventListener("input", () => {
        textarea_actualizar_direccion_nacimiento.value =
            textarea_actualizar_direccion_nacimiento.value.replace(
                /[^a-zA-ZáéíóúÁÉÍÓÚñÑ0-9\s.,:;()\-*]/g,
                ""
            );

        actualizarContador(textarea_actualizar_direccion_nacimiento, contador_nacimiento);
    });

    textarea_actualizar_direccion_residencia.addEventListener("input", () => {
        textarea_actualizar_direccion_residencia.value =
            textarea_actualizar_direccion_residencia.value.replace(
                /[^a-zA-ZáéíóúÁÉÍÓÚñÑ0-9\s.,:;()\-*]/g,
                ""
            );

        actualizarContador(textarea_actualizar_direccion_residencia, contador_residencia);
    });

    function actualizarContador(textarea, contador) {
        contador.textContent = textarea.value.length;
    }

    function evaluarContrasenia(contraseña) {
        let puntos = 0;

        if (contraseña.length >= 5) puntos++;
        if (contraseña.length >= 8) puntos++;
        if (/[a-z]/.test(contraseña)) puntos++;
        if (/[A-Z]/.test(contraseña)) puntos++;
        if (/[0-9]/.test(contraseña)) puntos++;
        if (/[^a-zA-Z0-9]/.test(contraseña)) puntos++;

        return puntos;
    }

    function actualizarFortalezaContrasenia() {
        const clave = input_actualizar_contrasenia.value;
        const puntos = evaluarContrasenia(clave);

        // Limpia clases de estado anteriores
        contenedorFortaleza.classList.remove("debil", "media", "fuerte");

        // Si el campo está vacío
        if (!clave) {
            texto_fortaleza.textContent = "";
            input_actualizar_contrasenia.setCustomValidity("");
            return;
        }

        // Asignación de estados según el puntaje
        if (puntos <= 2) {
            contenedorFortaleza.classList.add("debil");
            texto_fortaleza.textContent = "Contraseña débil";
        } else if (puntos <= 4) {
            contenedorFortaleza.classList.add("media");
            texto_fortaleza.textContent = "Contraseña media";
        } else {
            contenedorFortaleza.classList.add("fuerte");
            texto_fortaleza.textContent = "Contraseña fuerte";
        }
    }

    input_actualizar_contrasenia.addEventListener("input", actualizarFortalezaContrasenia);

    function soloTexto(input) {
        input.value = input.value.replace(/[^a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]/g, '');
    }

    input_actualizar_nombre.addEventListener("input", () => {
        soloTexto(this);
    });

    input_actualizar_apellido.addEventListener("input", () => {
        soloTexto(this);
    });

    // BUSCAR LOS DATOS DEL EMPLEADO
    formulario_busqueda.addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
            const formulario = new FormData(formulario_busqueda)

            const respuesta = await fetch("/buscar_datos_usuario/", {
                method: "POST",
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            select_nacionalidad.selectedIndex = 0;

            formulario_busqueda.reset();

            if (resultado.estado == "fallo") {
                Swal.fire({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon
                });
                return;
            }

            Swal.fire({
                title: "Datos encontrados",
                text: "Los datos del usuario fueron encontrados correctamente.",
                icon: "success"
            });

            bloquearFormularioActualizar(false);

            input_id_usuario.value = resultado.usuario.id;
            input_actualizar_nombre.value = resultado.usuario.nombres;
            input_actualizar_apellido.value = resultado.usuario.apellidos;

            const [nacionalidad, cedula] = resultado.usuario.cedula_identidad.split("-");

            input_actualizar_cedula.value = cedula;

            const option_nacionalidad = document.createElement("option");
            option_nacionalidad.value = nacionalidad;
            option_nacionalidad.textContent = nacionalidad;
            option_nacionalidad.selected = true;
            option_nacionalidad.hidden = true;
            select_actualizar_nacionalidad.append(option_nacionalidad);
            input_actualizar_cedula.value = cedula;

            const option_genero = document.createElement("option");
            option_genero.value = resultado.usuario.genero;
            option_genero.textContent = resultado.usuario.genero;
            option_genero.selected = true;
            option_genero.hidden = true;
            select_actualizar_genero.append(option_genero);

            const option_estado_civil = document.createElement("option");
            option_estado_civil.value = resultado.usuario.estado_civil;
            option_estado_civil.textContent = resultado.usuario.estado_civil;
            option_estado_civil.selected = true;
            option_estado_civil.hidden = true;
            select_actualizar_estado_civil.append(option_estado_civil);

            input_actualizar_nombre_usuario.value = resultado.credenciales.nombre_usuario;

            const [prefijo_principal, telefono_principal] = resultado.contacto.telefono_principal.split("-");

            input_actualizar_num_telefono_principal.value = telefono_principal;

            const option_prefijo_principal = document.createElement("option");
            option_prefijo_principal.value = prefijo_principal;
            option_prefijo_principal.textContent = prefijo_principal;
            option_prefijo_principal.selected = true;
            option_prefijo_principal.hidden = true;
            select_actualizar_prefijo_principal.append(option_prefijo_principal);

            if (resultado.contacto.telefono_secundario != "N/A") {
                const [prefijo_secundaria, telefono_secundaria] = resultado.contacto.telefono_secundario.split("-");

                input_actualizar_num_telefono_secundario.value = telefono_secundaria;

                const option_prefijo_secundaria = document.createElement("option");
                option_prefijo_secundaria.value = prefijo_secundaria;
                option_prefijo_secundaria.textContent = prefijo_secundaria;
                option_prefijo_secundaria.selected = true;
                option_prefijo_secundaria.hidden = true;
                select_actualizar_prefijo_secundario.append(option_prefijo_secundaria);
            }

            const [correo_principal, dominio_principal] = resultado.contacto.correo_principal.split("@");

            input_actualizar_correo_principal.value = correo_principal;

            const option_dominio_principal = document.createElement("option");
            option_dominio_principal.value = "@" + dominio_principal;
            option_dominio_principal.textContent = "@" + dominio_principal;
            option_dominio_principal.selected = true;
            option_dominio_principal.hidden = true;
            select_actualizar_dominio_principal.append(option_dominio_principal);

            if (resultado.contacto.correo_secundario) {
                const [correo_secundaria, dominio_secundaria] = resultado.contacto.correo_secundario.split("@");

                input_actualizar_correo_secundario.value = correo_secundaria;

                const option_dominio_secundaria = document.createElement("option");
                option_dominio_secundaria.value = "@" + dominio_secundaria;
                option_dominio_secundaria.textContent = "@" + dominio_secundaria;
                option_dominio_secundaria.selected = true;
                option_dominio_secundaria.hidden = true;

                select_actualizar_dominio_secundario.append(option_dominio_secundaria);
            }

            const option_pais_nacimiento = document.createElement("option");
            option_pais_nacimiento.value = resultado.nacimiento.pais;
            option_pais_nacimiento.textContent = resultado.nacimiento.pais;
            option_pais_nacimiento.selected = true;
            option_pais_nacimiento.hidden = true;
            select_actualizar_pais_nacimiento.append(option_pais_nacimiento);

            if (resultado.nacimiento.pais == "Venezuela") {
                const option_estado_nacimiento = document.createElement("option");
                option_estado_nacimiento.value = resultado.nacimiento.estado;
                option_estado_nacimiento.textContent = resultado.nacimiento.estado;
                option_estado_nacimiento.selected = true;
                option_estado_nacimiento.hidden = true;
                select_actualizar_estado_nacimiento.append(option_estado_nacimiento);

                const option_municipio_nacimiento = document.createElement("option");
                option_municipio_nacimiento.value = resultado.nacimiento.municipio;
                option_municipio_nacimiento.textContent = resultado.nacimiento.municipio;
                option_municipio_nacimiento.selected = true;
                option_municipio_nacimiento.hidden = true;
                select_actualizar_municipio_nacimiento.append(option_municipio_nacimiento);

                const option_parroquia_nacimiento = document.createElement("option");
                option_parroquia_nacimiento.value = resultado.nacimiento.parroquia;
                option_parroquia_nacimiento.textContent = resultado.nacimiento.parroquia;
                option_parroquia_nacimiento.selected = true;
                option_parroquia_nacimiento.hidden = true;
                select_actualizar_parroquia_nacimiento.append(option_parroquia_nacimiento);

                cargarMunicipios(resultado.nacimiento.municipio);

                cargarParroquias(resultado.nacimiento.parroquia);
            } else {
                input_actualizar_estado_vzla_nacimiento.value = resultado.nacimiento.estado;
                input_actualizar_municipio_vzla_nacimiento.value = resultado.nacimiento.municipio;
                input_actualizar_parroquia_vzla_nacimiento.value = resultado.nacimiento.parroquia;
            }

            textarea_actualizar_direccion_nacimiento.value = resultado.nacimiento.direccion;

            actualizarContador(textarea_actualizar_direccion_nacimiento, contador_nacimiento);

            input_actualizar_fecha_nacimiento.value = resultado.nacimiento.fecha_nacimiento;

            const option_condicion_residencia = document.createElement("option");
            option_condicion_residencia.value = resultado.residencia.condicion_residencia;
            option_condicion_residencia.textContent = resultado.residencia.condicion_residencia;
            option_condicion_residencia.selected = true;
            option_condicion_residencia.hidden = true;
            select_actualizar_condicion_residencia.append(option_condicion_residencia);

            const option_municipio_residencia = document.createElement("option");
            option_municipio_residencia.value = resultado.residencia.municipio;
            option_municipio_residencia.textContent = resultado.residencia.municipio;
            option_municipio_residencia.selected = true;
            option_municipio_residencia.hidden = true;
            select_actualizar_municipio_residencia.append(option_municipio_residencia);

            const option_parroquia_residencia = document.createElement("option");
            option_parroquia_residencia.value = resultado.residencia.parroquia;
            option_parroquia_residencia.textContent = resultado.residencia.parroquia;
            option_parroquia_residencia.selected = true;
            option_parroquia_residencia.hidden = true;
            select_actualizar_parroquia_residencia.append(option_parroquia_residencia);

            cargarMunicipiosResidencia(resultado.residencia.municipio);

            cargarParroquiasResidencia(resultado.residencia.parroquia);

            textarea_actualizar_direccion_residencia.value = resultado.residencia.direccion;

            actualizarContador(textarea_actualizar_direccion_residencia, contador_residencia)
        } catch (error) {
            console.error(error);
        }
    });

    // ACTUALIZAR LOS DATOS DEL EMPLEADO
    const navegacion = configurarFormularioPasos(formulario_actualizar);

    formulario_actualizar.addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
            const formulario = new FormData(formulario_actualizar);

            const respuesta = await fetch("/actualizacion_datos_usuarios/", {
                method: "POST",
                body: formulario
            });
            const resultado = await respuesta.json();

            await Swal.fire({
                title: resultado.title,
                text: resultado.descripcion,
                icon: resultado.icon
            });

            if (resultado.estado == "exito") {
                bloquearFormularioActualizar(true);
                navegacion.reiniciar();
                formulario_actualizar.reset();

                barra_fortaleza.innerHTML = ""
                texto_fortaleza.innerHTML = "";
                contenedorFortaleza.classList.remove("debil", "media", "fuerte");

                contenedor_mensaje_ci.innerHTML = "";
                contenedor_mensaje_nombre_usuario.innerHTML = "";
                contenedor_mensaje_contrasenia.innerHTML = "";
                contenedor_mensaje_correo_secundario.innerHTML = "";
                contenedor_mensaje_correo_principal.innerHTML = "";
            }
        } catch (error) {
            console.error(error);
        }
    });
});