#!/usr/bin/env python3
"""
fill_uce_excel.py
Puebla de manera automática y estructurada la plantilla oficial de la UCE (MSotaminga-UCE.xlsx)
con los datos personales, académicos, laborales, docentes y científicos de Marcelo Sotaminga.
"""

import zipfile
import xml.etree.ElementTree as ET
import os

EXCEL_FILE = "CV-UCE/MSotaminga-UCE.xlsx.bak"
OUTPUT_FILE = "CV-UCE/MSotaminga-UCE.xlsx"

# Mapeo de celdas a valores
CELL_DATA = {
    # 1.a) Datos personales
    "B13": "MARCELO JAVIER",
    "O13": "SOTAMINGA",
    "AC13": "CINILIN",
    "B16": "Cédula",
    "I16": "1719920041",
    "T16": "Masculino ",
    "AA16": "22480590",
    "B19": "marcelo.sotaminga@gmail.com",
    "T19": "marcelo.sotaminga@unisabana.edu.co / msotaminga@uoc.edu",

    # 1.b) Lugar de nacimiento
    "B25": "22/12/1988",
    "G25": "Ecuador",
    "M25": "Pichincha",
    "T25": "San Blas",
    "AA25": "Quito",
    "AF25": "Ecuatoriana",
    "AF26": "No aplica",
    "B30": "No aplica",
    "G30": "No aplica",
    "O30": "No aplica",
    "W30": "No aplica",
    "AC30": "No aplica",

    # 1.c) Identificación étnica
    "B33": "Mestizo",
    "P33": "No aplica",

    # 1.d) Estado civil
    "B36": "Casado/a  ",

    # 1.e) Dirección domiciliaria
    "B40": "Ecuador",
    "P40": "Pichincha",
    "AC40": "Quito",
    "B42": "Calderón",
    "P42": "Calderón",
    "AC42": "Conjunto Habitacional La Finca 4",
    "B44": "Av. Cacha",
    "P44": "Cantabria (Calle F)",
    "AC44": "Casa 9 C",
    "B48": "Conjunto Habitacional La Finca 4, Casa 9 C; cerca de la Av. Cacha",
    "AC48": "170155",
    "B50": "No aplica",
    "P50": "0992888378",
    "AC50": "No aplica",
    "AJ50": "No aplica",

    # 1.f) Contacto de Emergencia
    "B54": "MALES VILLA MONICA ALEXANDRA",
    "V54": "Cónyuge",
    "AC54": "monaalexandra0114@gmail.com",
    "B56": "0998007040",
    "V56": "No aplica",

    # 1.g) Información bancaria
    "B60": "BANCO PICHINCHA",
    "P60": "Ahorros ",
    "AA60": "2203026326",

    # 1.h) Otra relación laboral con UCE
    "B64": "No aplica",
    "P64": "No aplica",
    "AA64": "No aplica",
    "AJ64": "No aplica",

    # 2. Formación Académica Superior (Orden descendente)
    # Fila 70: Doctorado en curso
    "B70": "Cuarto nivel",
    "D70": "EN TRAMITE",
    "H70": "UNIVERSIDAD DE LA SABANA",
    "P70": "No aplica",
    "X70": "DOCTORADO EN INGENIERÍA (Cursando 3er semestre regular, Certificado N° 777872)",
    "AG70": "Extranjero ",
    "AI70": "En curso",
    "AK70": "No aplica",

    # Fila 71: Máster Gestión Estratégica
    "B71": "Cuarto nivel",
    "D71": "7241199351",
    "H71": "UNIVERSITAT OBERTA DE CATALUNYA",
    "P71": "No aplica",
    "X71": "MÁSTER UNIVERSITARIO EN GESTIÓN ESTRATÉGICA DE LA INFORMACIÓN Y EL CONOCIMIENTO EN LAS ORGANIZACIONES",
    "AG71": "Extranjero ",
    "AI71": "11/02/2022",
    "AK71": "27/06/2022",

    # Fila 72: Máster Calidad Educación Superior
    "B72": "Cuarto nivel",
    "D72": "7241175728",
    "H72": "UNIVERSITAT OBERTA DE CATALUNYA",
    "P72": "No aplica",
    "X72": "MÁSTER UNIVERSITARIO EN EVALUACIÓN Y GESTIÓN DE LA CALIDAD EN LA EDUCACIÓN SUPERIOR",
    "AG72": "Extranjero ",
    "AI72": "14/02/2020",
    "AK72": "23/03/2021",

    # Fila 73: Máster Educación y TIC
    "B73": "Cuarto nivel",
    "D73": "7241115069",
    "H73": "UNIVERSITAT OBERTA DE CATALUNYA",
    "P73": "No aplica",
    "X73": "MÁSTER UNIVERSITARIO EN EDUCACIÓN Y TIC",
    "AG73": "Extranjero ",
    "AI73": "14/07/2017",
    "AK73": "14/12/2017",

    # Fila 74: Licenciatura UCE
    "B74": "Tercer nivel",
    "D74": "1005-15-1388142",
    "H74": "UNIVERSIDAD CENTRAL DEL ECUADOR",
    "P74": "No aplica",
    "X74": "LICENCIADO EN CIENCIAS DE LA EDUCACIÓN MENCIÓN INFORMÁTICA",
    "AG74": "Nacional",
    "AI74": "29/11/2014",
    "AK74": "20/07/2015",

    # 3. Capacitación (Últimos 5 años)
    # Fila 81
    "B81": "UNIVERSIDAD DE LA SABANA",
    "F81": "DIPLOMADO EN INTELIGENCIA ARTIFICIAL CON DEEP LEARNING",
    "O81": "Virtual",
    "S81": "Certificación",
    "X81": "25/06/2025",
    "AB81": "Participante",
    "AG81": "Aprobación",
    "AJ81": 96,

    # Fila 82
    "B82": "UNESCO-IESALC",
    "F82": "CLAVES DE LA FORMACIÓN VIRTUAL: APRENDIZAJE ACTIVO E INTEGRACIÓN DE TIC",
    "O82": "Virtual",
    "S82": "Curso",
    "X82": "11/10/2026",
    "AB82": "Participante",
    "AG82": "Aprobación",
    "AJ82": 40,

    # Fila 83
    "B83": "EDES BUSINESS SCHOOL - UTPL",
    "F83": "REQUISITOS DEL SECTOR PÚBLICO PARA GESTIONAR EQUIPOS DE TRABAJO",
    "O83": "Virtual",
    "S83": "Curso",
    "X83": "06/11/2021",
    "AB83": "Participante",
    "AG83": "Aprobación",
    "AJ83": 40,

    # Fila 84
    "B84": "SERVICIO NACIONAL DE CONTRATACIÓN PÚBLICA (SERCOP)",
    "F84": "CERTIFICACIÓN DE FUNDAMENTOS EN CONTRATACIÓN PÚBLICA",
    "O84": "Virtual",
    "S84": "Certificación",
    "X84": "15/02/2022",
    "AB84": "Participante",
    "AG84": "Aprobación",
    "AJ84": 40,

    # Fila 85
    "B85": "GOOGLE ACTÍVATE E INCIBE",
    "F85": "PROTEGEMOS TU NEGOCIO: CIBERSEGURIDAD EN EL TELETRABAJO",
    "O85": "Virtual",
    "S85": "Curso",
    "X85": "14/07/2022",
    "AB85": "Participante",
    "AG85": "Aprobación",
    "AJ85": 40,

    # Fila 86
    "B86": "UNIVERSITAT OBERTA DE CATALUNYA (UOC)",
    "F86": "PROTECCIÓN DE DATOS (RGPD) PARA PERSONAL DOCENTE E INVESTIGADOR",
    "O86": "Virtual",
    "S86": "Curso",
    "X86": "20/06/2022",
    "AB86": "Participante",
    "AG86": "Aprobación",
    "AJ86": 25,

    # Fila 87
    "B87": "UNIVERSITAT OBERTA DE CATALUNYA (UOC)",
    "F87": "FORMACIÓN DOCENTE TECNOPEDAGÓGICA Y EVALUACIÓN DE COMPETENCIAS",
    "O87": "Virtual",
    "S87": "Curso",
    "X87": "15/03/2022",
    "AB87": "Participante",
    "AG87": "Aprobación",
    "AJ87": 30,

    # Fila 88
    "B88": "UNIVERSIDAD DE GRANADA (UGR)",
    "F88": "MOBILE LEARNING Y METODOLOGÍAS ACTIVAS EN EDUCACIÓN SUPERIOR",
    "O88": "Virtual",
    "S88": "Curso",
    "X88": "10/11/2022",
    "AB88": "Participante",
    "AG88": "Aprobación",
    "AJ88": 40,

    # Fila 89
    "B89": "TECNOLÓGICO DE MONTERREY",
    "F89": "EVALUACIÓN DE PROYECTOS DE INNOVACIÓN EDUCATIVA NOVUS 2022",
    "O89": "Virtual",
    "S89": "Taller",
    "X89": "15/10/2022",
    "AB89": "Invitado",
    "AG89": "Asistencia ",
    "AJ89": 20,

    # Fila 90
    "B90": "UNIVERSIDAD ANTONIO DE NEBRIJA - SANTANDER",
    "F90": "INTELIGENCIA ARTIFICIAL Y ANALÍTICA DE APRENDIZAJE EN EL AULA",
    "O90": "Virtual",
    "S90": "Curso",
    "X90": "20/05/2021",
    "AB80": "Participante",
    "AG90": "Aprobación",
    "AJ90": 40,

    # Fila 91
    "B91": "FUNDACIÓN TELEFÓNICA MOVISTAR - PROFUTURO",
    "F91": "COMPETENCIAS DIGITALES DOCENTES E INNOVACIÓN PEDAGÓGICA",
    "O91": "Virtual",
    "S91": "Curso",
    "X91": "15/08/2021",
    "AB91": "Participante",
    "AG91": "Aprobación",
    "AJ91": 50,

    # Fila 92
    "B92": "ESCUELA POLITÉCNICA NACIONAL - CEC EPN",
    "F92": "FORMADOR DE FORMADORES EN ENTORNOS VIRTUALES Y MOODLE",
    "O92": "Virtual",
    "S92": "Curso",
    "X92": "10/12/2021",
    "AB92": "Participante",
    "AG92": "Aprobación",
    "AJ92": 40,

    # Fila 93
    "B93": "MOODLEMOOT COLOMBIA",
    "F93": "MOODLEMOOT COLOMBIA 2026: ECOSISTEMAS DE APRENDIZAJE Y TECNOLOGÍAS EDUCATIVAS",
    "O93": "Presencial",
    "S93": "Seminario ",
    "X93": "18/06/2026",
    "AB93": "Participante",
    "AG93": "Asistencia ",
    "AJ93": 20,

    # 4. Experiencia Profesional (Últimos 5 años)
    # Fila 103: UniSabana
    "B103": "UNIVERSIDAD DE LA SABANA",
    "F103": "JEFE DE PRODUCCIÓN VIRTUAL",
    "O103": "Dirigir el proceso de uso, integración y apropiación de las TIC y tecnologías emergentes en programas de educación formal a nivel de grado, posgrado y educación continua.",
    "AG103": "01/03/2026",
    "AJ103": "Actual",

    # Fila 104: Espiral Educativa
    "B104": "ESPIRAL EDUCATIVA",
    "F104": "DIRECTOR DE PROYECTOS",
    "O104": "Diseño instruccional de programas y proyectos, transformación digital en organizaciones, creación de aulas virtuales en LMS Moodle, gestión del cambio, metodologías ágiles (SCRUM, Design Thinking) y métricas de impacto KPI.",
    "AG104": "01/09/2015",
    "AJ104": "30/09/2024",

    # Fila 105: MINTEL
    "B105": "MINISTERIO DE TELECOMUNICACIONES Y DE LA SOCIEDAD DE LA INFORMACIÓN (MINTEL)",
    "F105": "DIRECTOR DE FOMENTO DE TECNOLOGÍAS EMERGENTES",
    "O105": "Desarrollar planes, programas, proyectos y acciones para el uso adecuado y progresivo de las Tecnologías Emergentes a nivel nacional, diseño de proyectos con cooperación internacional, planificación estratégica y KPIs.",
    "AG105": "20/09/2021",
    "AJ105": "30/06/2022",

    # Fila 106: ProFuturo - ChildFund
    "B106": "PROFUTURO - CHILDFUND",
    "F106": "COORDINADOR COMUNIDADES DE APRENDIZAJE DIGITAL",
    "O106": "Diseño, ejecución y evaluación de proyectos de innovación educativa, conformación de comunidades de aprendizaje digital, investigación educativa cualitativa y cuantitativa, reportes de impacto social.",
    "AG106": "01/04/2021",
    "AJ106": "19/09/2021",

    # Fila 107: Fundación de Waal
    "B107": "FUNDACIÓN DE WAAL",
    "F107": "COORDINADOR EDUCACIÓN VIRTUAL Y TIC",
    "O107": "Planificación de proyectos educativos con TIC, diseño tecnopedagógico, administración y desarrollo de plataformas LMS Moodle para 4 países, capacitación docente en TIC y dashboards de seguimiento KPI.",
    "AG107": "01/04/2013",
    "AJ107": "31/12/2020",

    # Fila 108: UNAE
    "B108": "UNIVERSIDAD NACIONAL DE EDUCACIÓN (UNAE)",
    "F108": "CONSULTOR ESPECIALISTA EN DISEÑO VIRTUAL",
    "O108": "Diseño tecnopedagógico y virtualización del aula virtual para la Maestría en Educación Inclusiva, estructuración de entornos de aprendizaje y recursos educativos digitales.",
    "AG108": "01/08/2021",
    "AJ108": "16/10/2021",

    # 5. Experiencia Docente en Educación Superior
    # Fila 112: UCE Posgrado
    "B112": "UNIVERSIDAD CENTRAL DEL ECUADOR",
    "F112": "Facultad de Filosofía, Letras y Ciencias de la Educación - Consejo de Posgrado",
    "O112": "Módulo: Metodologías Activas para la Enseñanza de la Informática (Maestría en Educación, mención Gestión del Aprendizaje mediado por TIC)",
    "AB112": "Posgrado",
    "AG112": "11/04/2019",
    "AJ112": "11/05/2019",

    # Fila 113: Universidad de La Sabana
    "B113": "UNIVERSIDAD DE LA SABANA",
    "F113": "Facultad de Ingeniería",
    "O113": "Asignatura: Bases de Datos (Carreras de Ingeniería Informática e Ingeniería en Ciencia de Datos). Aprendizaje basado en proyectos y evaluación formativa.",
    "AB113": "Grado ",
    "AG113": "01/07/2025",
    "AJ113": "Actual",

    # Fila 114: Universidad Indoamérica
    "B114": "UNIVERSIDAD TECNOLÓGICA INDOAMÉRICA",
    "F114": "Facultad de Ingeniería y Tecnologías de la Información",
    "O114": "Asignaturas: Computación y Sociedad, Fundamentos de Sistemas Operativos, Interacción Humano-Máquina, Matemáticas Discretas. Coordinación Académica de Carrera.",
    "AB114": "Grado ",
    "AG114": "01/10/2022",
    "AJ114": "30/09/2024",

    # Fila 115: UOC
    "B115": "UNIVERSITAT OBERTA DE CATALUNYA",
    "F115": "Estudios de Informática, Multimedia y Telecomunicación",
    "O115": "Asignatura: Competencias en Tecnologías de la Información y de la Comunicación (C-TIC). Docencia virtual, trabajo colaborativo en red y evaluación continua.",
    "AB115": "Grado ",
    "AG115": "01/08/2020",
    "AJ115": "30/09/2023",

    # Fila 116: Universidad Católica de Cuenca
    "B116": "UNIVERSIDAD CATÓLICA DE CUENCA",
    "F116": "Unidad Académica de Posgrados",
    "O116": "Módulos de Posgrado: Recursos Tecnológicos para la Innovación; Tecnologías Aplicadas a la Educación; Recursos Tecnológicos para el Aprendizaje de la Educación Física.",
    "AB116": "Posgrado",
    "AG116": "01/03/2022",
    "AJ116": "10/08/2023",

    # Fila 117: Universidad Técnica del Norte
    "B117": "UNIVERSIDAD TÉCNICA DEL NORTE",
    "F117": "Instituto de Posgrado",
    "O117": "Módulo de Posgrado: Herramientas Colaborativas y TIC en la Educación (Maestría en Tecnología e Innovación Educativa).",
    "AB117": "Posgrado",
    "AG117": "14/02/2020",
    "AJ117": "01/06/2020",

    # 6.2 Capítulos de Libro (Últimos 5 años)
    # Fila 131: Springer CISTI
    "B131": "Proceedings of 20th Iberian Conference on Information Systems and Technologies (CISTI 2025)",
    "G131": "Advanced Customer Segmentation in the Natural Supplements Industry to Enhance Marketing Strategies Using Big Data Tools",
    "K131": "Springer Nature Switzerland",
    "P131": "Suiza - Cham",
    "T131": "10.1007/978-3-032-10721-3_63",
    "W131": "978-3-032-10720-6",
    "Z131": "15/01/2026",
    "AB131": "Si ",
    "AE131": "https://link.springer.com/chapter/10.1007/978-3-032-10721-3_63",
    "AI131": "Universidad de La Sabana",

    # Fila 132: Springer Emerging Technologies
    "B132": "Emerging Technologies in Applied Engineering and Education",
    "G132": "Student Perceptions of an AI-Based Assistant for Formative Feedback in Higher Education",
    "K132": "Springer Nature Switzerland",
    "P132": "Suiza - Cham",
    "T132": "10.1007/978-3-032-10310-9_15",
    "W132": "978-3-032-10309-3",
    "Z132": "10/01/2026",
    "AB132": "Si ",
    "AE132": "https://link.springer.com/chapter/10.1007/978-3-032-10310-9_15",
    "AI132": "Universidad de La Sabana",

    # Fila 133: Springer CISTI
    "B133": "Proceedings of 20th Iberian Conference on Information Systems and Technologies (CISTI 2025)",
    "G133": "Technological Migration and Software Optimization for Measuring Entrepreneurship Maturity",
    "K133": "Springer Nature Switzerland",
    "P133": "Suiza - Cham",
    "T133": "10.1007/978-3-032-10721-3_74",
    "W133": "978-3-032-10720-6",
    "Z133": "15/01/2026",
    "AB133": "Si ",
    "AE133": "https://link.springer.com/chapter/10.1007/978-3-032-10721-3_74",
    "AI133": "Universidad de La Sabana",

    # Fila 134: CIESPAL
    "B134": "Pensamiento computacional, programación creativa y ciencias de la computación para la educación",
    "G134": "Pensamiento computacional, programación creativa y ciencias de la computación para la educación. Reflexiones y experiencias desde América Latina",
    "K134": "Ediciones CIESPAL",
    "P134": "Ecuador - Quito",
    "T134": "No aplica",
    "W134": "978-9978-55-197-4",
    "Z134": "10/11/2021",
    "AB134": "Si ",
    "AE134": "https://ediciones.ciespal.org/index.php/ediciones/catalog/download/30/34/230-1?inline=1",
    "AI134": "MINTEL - Ecuador",

    # 6.3 Artículos Científicos
    # Fila 140: MQRInvestigar
    "B140": "Competencias digitales de los docentes de la unidad educativa amauta ñanpi",
    "M140": "MQRInvestigar",
    "S140": "10.56048/MQR20225.9.1.2025.e236",
    "V140": "2588-0659",
    "Y140": "15/01/2025",
    "AB140": "Latindex Catálogo 2.0",
    "AE140": "https://mqrinvestigar.com/2025/index.php/mqr/article/view/236",
    "AI140": "Universidad Tecnológica Indoamérica",

    # Fila 141: Revista Conrado 1
    "B141": "Usos de Internet con fines educativos: perspectivas para su fortalecimiento",
    "M141": "Revista Conrado",
    "S141": "No aplica",
    "V141": "1990-8644",
    "Y141": "10/01/2023",
    "AB141": "Scielo / Latindex Catálogo 2.0",
    "AE141": "https://conrado.ucf.edu.cu/index.php/conrado/article/view/2887",
    "AI141": "Universidad Nacional de Educación",

    # Fila 142: Revista Conrado 2
    "B142": "Nivel de satisfacción estudiantil en el uso de estrategias y metodologías en la Educación Virtual",
    "M142": "Revista Conrado",
    "S142": "No aplica",
    "V142": "1990-8644",
    "Y142": "15/07/2023",
    "AB142": "Scielo / Latindex Catálogo 2.0",
    "AE142": "https://conrado.ucf.edu.cu/index.php/conrado/article/view/3370",
    "AI142": "Universidad Tecnológica Indoamérica",

    # Fila 143: Revista Arbitrada Interdisciplinaria Koinonía
    "B143": "Escape room como estrategia didáctica para el desarrollo del pensamiento crítico",
    "M143": "Revista Arbitrada Interdisciplinaria Koinonía",
    "S143": "10.35381/r.k.v7i2.1968",
    "V143": "2542-3088",
    "Y143": "10/08/2022",
    "AB143": "Scopus / Latindex Catálogo 2.0",
    "AE143": "https://fundacionkoinonia.com.ve/ojs/index.php/revistakoinonia/article/view/1968",
    "AI143": "Universidad Católica de Cuenca",

    # Fila 144: Dominio de las Ciencias
    "B144": "Escape room educativo: Una mirada desde la experiencia de los estudiantes en Endodoncia",
    "M144": "Dominio de las Ciencias",
    "S144": "10.23857/dc.v8i3.2964",
    "V144": "2477-8818",
    "Y144": "05/08/2022",
    "AB144": "Latindex Catálogo 2.0 / Dialnet",
    "AE144": "https://doi.org/10.23857/dc.v8i3.2964",
    "AI144": "Universidad Católica de Cuenca",

    # Fila 145: CIENCIAMATRIA
    "B145": "Aprendizaje basado en problemas. Experiencia en estudiantes universitarios",
    "M145": "CIENCIAMATRIA",
    "S145": "10.35381/cm.v8i4.850",
    "V145": "2542-3029",
    "Y145": "15/07/2022",
    "AB145": "Latindex Catálogo 2.0",
    "AE145": "https://cienciamatriarevista.org.ve/index.php/cm/article/view/850",
    "AI145": "Universidad Católica de Cuenca",

    # 7. Contribuciones presentadas en Congresos y Conferencias (Últimos 5 años)
    # Fila 150: Scratch Day
    "B150": "Scratch Day Quito 2025",
    "J150": "Conferencia ",
    "K150": "Pensamiento Computacional y Programación Creativa en el Aula",
    "Q150": "No aplica",
    "S150": "Edición 2025",
    "V150": "Fundación Openlab Ecuador",
    "Z150": "Ecuador - Quito",
    "AC150": "03/06/2025",
    "AF150": "https://openlab.ec",
    "AI150": "03/06/2025",
    "AK150": "03/06/2025",

    # Fila 151: MinEduc Webinar
    "B151": "Webinar del Ministerio de Educación del Ecuador",
    "J151": "Seminario ",
    "K151": "Ponente Experto en el Webinar Uso de Recursos Educativos en el Aula",
    "Q151": "No aplica",
    "S151": "Ciclo 2023",
    "V151": "Ministerio de Educación del Ecuador",
    "Z151": "Ecuador - Quito",
    "AC151": "25/08/2023",
    "AF151": "https://educacion.gob.ec",
    "AI151": "25/08/2023",
    "AK151": "25/08/2023",

    # Fila 152: OEA RIED
    "B152": "Seminario Virtual de la RIED 2022",
    "J152": "Seminario ",
    "K152": "Innovación Tecnopedagógica y Formación Docente",
    "Q152": "No aplica",
    "S152": "Edición 2022",
    "V152": "Red Interamericana de Educación Docente (RIED) - OEA",
    "Z152": "Estados Unidos - Washington",
    "AC152": "15/11/2022",
    "AF152": "https://oas.org",
    "AI152": "10/11/2022",
    "AK152": "15/11/2022",

    # Fila 153: UNACH
    "B153": "VII Congreso Internacional de Educación Contemporánea",
    "J153": "Conferencia ",
    "K153": "Miembro del Comité Científico-Evaluador Externo y Ponente",
    "Q153": "No aplica",
    "S153": "VII Edición",
    "V153": "Universidad Nacional de Chimborazo",
    "Z153": "Ecuador - Riobamba",
    "AC153": "20/11/2022",
    "AF153": "https://unach.edu.ec",
    "AI153": "18/11/2022",
    "AK153": "20/11/2022",

    # Fila 154: Fundación Telefónica
    "B154": "Tertulia Dialógica Fundación Telefónica",
    "J154": "Conferencia ",
    "K154": "Mejorando nuestras vidas en comunidad, con el uso de las TIC",
    "Q154": "No aplica",
    "S154": "Edición 2022",
    "V154": "Fundación Telefónica Movistar Ecuador y ChildFund Ecuador",
    "Z154": "Ecuador - Quito",
    "AC154": "15/10/2022",
    "AF154": "https://fundaciontelefonica.com.ec",
    "AI154": "15/10/2022",
    "AK154": "15/10/2022",

    # Fila 155: Campamentos MinEduc
    "B155": "Campamentos Escuelas que me Inspiran 2021",
    "J155": "Conferencia ",
    "K155": "Capacitación y formación en innovación tecnopedagógica para la comunidad educativa",
    "Q155": "No aplica",
    "S155": "Edición 2021",
    "V155": "Ministerio de Educación del Ecuador",
    "Z155": "Ecuador - Quito",
    "AC155": "20/01/2022",
    "AF155": "https://educacion.gob.ec",
    "AI155": "15/01/2022",
    "AK155": "20/01/2022",

    # 8. Propiedad Industrial
    "B159": "No aplica",
    "M159": "No aplica",
    "S159": "No aplica",
    "V159": "No aplica",
    "AB159": "No aplica",
    "AG159": "No aplica",
    "AJ159": "No aplica",

    # 9. Producción Artística
    "B168": "No aplica",
    "S168": "No aplica",
    "AB168": "No aplica",

    # 10. Obras y/o Diseños Técnicos (Software)
    "B177": "Ecosistema Neuro-Simbólico de Evaluación Inteligente (Sabana Centro STEM)",
    "S177": "Universidad de La Sabana",
    "AB177": "IALab Sabana",
    "AI177": "Universidad de La Sabana",

    "B178": "Campus de Formación Virtual y Arquitectura LMS Moodle Corporativa",
    "S178": "Corporación Nacional de Finanzas Populares y Solidarias (CONAFIPS)",
    "AB178": "Innovanci Internacional",
    "AI178": "Innovanci Internacional",

    # Respaldo Documental (Conteo de hojas)
    "AJ188": 2,   # Cédula + Certificado de votación
    "AJ192": 15,  # Certificados de experiencia laboral y docente
    "AJ193": 0,
    "AJ194": 0,
    "AJ195": 1,   # Certificado bancario
    "AJ196": 3,   # Historial laboral IESS tiempo servicio por empleador
    "AJ198": 2,   # RUC con actividad de docencia superior

    # Fecha final
    "Z201": "15/10/2026"
}

def main():
    print(f"Cargando archivo: {EXCEL_FILE}")
    
    # 1. Leer el archivo zip original
    with zipfile.ZipFile(EXCEL_FILE, "r") as zin:
        xml_sheet1 = zin.read("xl/worksheets/sheet1.xml")
        xml_sst = zin.read("xl/sharedStrings.xml")
        file_list = {item.filename: zin.read(item.filename) for item in zin.infolist()}

    # 2. Registrar todos los espacios de nombres oficiales de OpenXML/Excel
    namespaces = {
        "": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
        "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
        "xdr": "http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing",
        "x14": "http://schemas.microsoft.com/office/spreadsheetml/2009/9/main",
        "mc": "http://schemas.openxmlformats.org/markup-compatibility/2006",
        "x14ac": "http://schemas.microsoft.com/office/spreadsheetml/2009/9/ac",
        "xm": "http://schemas.microsoft.com/office/excel/2006/main",
    }
    for prefix, uri in namespaces.items():
        ET.register_namespace(prefix, uri)

    ns_main = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    sst_root = ET.fromstring(xml_sst)
    
    # Mapear strings existentes
    shared_strings = []
    str_to_idx = {}
    for i, si in enumerate(sst_root.findall(f"{{{ns_main}}}si")):
        t_el = si.find(f"{{{ns_main}}}t")
        text_val = t_el.text if t_el is not None and t_el.text is not None else ""
        shared_strings.append(text_val)
        if text_val not in str_to_idx:
            str_to_idx[text_val] = i

    def get_or_add_str(val):
        str_val = str(val)
        if str_val in str_to_idx:
            return str_to_idx[str_val]
        idx = len(shared_strings)
        shared_strings.append(str_val)
        str_to_idx[str_val] = idx
        # Agregar al XML de sharedStrings
        si = ET.SubElement(sst_root, f"{{{ns_main}}}si")
        t = ET.SubElement(si, f"{{{ns_main}}}t")
        t.text = str_val
        return idx

    # 3. Parsear sheet1.xml
    sheet1_root = ET.fromstring(xml_sheet1)
    sheet_data = sheet1_root.find(f"{{{ns_main}}}sheetData")
    
    # Mapear filas por r
    rows_by_idx = {}
    for r in sheet_data.findall(f"{{{ns_main}}}row"):
        r_num = int(r.attrib.get("r"))
        rows_by_idx[r_num] = r

    # Procesar celdas
    for coord, val in CELL_DATA.items():
        # Separar columna y fila
        col_letters = "".join([c for c in coord if c.isalpha()])
        row_num = int("".join([c for c in coord if c.isdigit()]))

        if row_num not in rows_by_idx:
            print(f"Advertencia: Fila {row_num} no encontrada para celda {coord}")
            continue

        row_el = rows_by_idx[row_num]
        
        # Buscar la celda c
        cell_el = None
        for c in row_el.findall(f"{{{ns_main}}}c"):
            if c.attrib.get("r") == coord:
                cell_el = c
                break

        if cell_el is None:
            # Crear la celda en la posición ordenada correcta
            cell_el = ET.Element(f"{{{ns_main}}}c")
            cell_el.attrib["r"] = coord
            # Encontrar dónde insertarla para mantener orden de columnas
            inserted = False
            for idx, c in enumerate(row_el.findall(f"{{{ns_main}}}c")):
                c_col = "".join([ch for ch in c.attrib.get("r", "") if ch.isalpha()])
                if len(c_col) > len(col_letters) or (len(c_col) == len(col_letters) and c_col > col_letters):
                    row_el.insert(idx, cell_el)
                    inserted = True
                    break
            if not inserted:
                row_el.append(cell_el)

        # Asignar valor numérico o string
        if isinstance(val, (int, float)):
            # Valor numérico directo
            if "t" in cell_el.attrib:
                del cell_el.attrib["t"]
            v = cell_el.find(f"{{{ns_main}}}v")
            if v is None:
                v = ET.SubElement(cell_el, f"{{{ns_main}}}v")
            v.text = str(val)
        else:
            # Shared string
            s_idx = get_or_add_str(str(val))
            cell_el.attrib["t"] = "s"
            v = cell_el.find(f"{{{ns_main}}}v")
            if v is None:
                v = ET.SubElement(cell_el, f"{{{ns_main}}}v")
            v.text = str(s_idx)

    # Actualizar count en sst_root
    sst_root.attrib["count"] = str(len(shared_strings))
    sst_root.attrib["uniqueCount"] = str(len(shared_strings))

    # 4. Generar bytes de los XMLs modificados
    file_list["xl/sharedStrings.xml"] = ET.tostring(sst_root, encoding="utf-8", xml_declaration=True)
    file_list["xl/worksheets/sheet1.xml"] = ET.tostring(sheet1_root, encoding="utf-8", xml_declaration=True)

    # 5. Escribir nuevo zip preservando absolutamente todos los demás archivos
    with zipfile.ZipFile(OUTPUT_FILE, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for fname, data in file_list.items():
            zout.writestr(fname, data)

    print(f"✓ Archivo {OUTPUT_FILE} generado exitosamente con {len(CELL_DATA)} campos poblados.")

if __name__ == "__main__":
    main()
