#!/usr/bin/env python3
"""
scripts/parse_cv.py
Parser integral para CV de Marcelo Sotaminga:
1. Extrae información de cv.tex
2. Extrae publicaciones de bibliografia.bib
3. Combina con data/enrichment.json
4. Genera topología del Knowledge Graph (Espacio Latente)
5. Produce data/cv_data.json
"""

import os
import re
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CV_TEX_PATH = BASE_DIR / "cv.tex"
CV2_TEX_PATH = BASE_DIR / "Cv2.tex"
BIB_PATH = BASE_DIR / "bibliografia.bib"
ENRICHMENT_PATH = BASE_DIR / "data" / "enrichment.json"
CERTIFICATES_PATH = BASE_DIR / "data" / "certificates.json"
OUTPUT_PATH = BASE_DIR / "data" / "cv_data.json"

def clean_latex(text: str) -> str:
    """Limpia macros comunes de LaTeX, tildes, llaves de BibTeX y caracteres especiales."""
    if not text:
        return ""
    
    # 1. Reemplazos de acentos y caracteres especiales LaTeX (con y sin llaves)
    replacements = [
        # Acentos agudos: \'a, \'{a}, etc.
        (r"\\\'\{a\}", "á"), (r"\\\'\{e\}", "é"), (r"\\\'\{i\}", "í"), (r"\\\'\{o\}", "ó"), (r"\\\'\{u\}", "ú"),
        (r"\\\'\{\\i\}", "í"), (r"\\\'\{A\}", "Á"), (r"\\\'\{E\}", "É"), (r"\\\'\{I\}", "Í"), (r"\\\'\{O\}", "Ó"), (r"\\\'\{U\}", "Ú"),
        (r"\\\'a", "á"), (r"\\\'e", "é"), (r"\\\'i", "í"), (r"\\\'o", "ó"), (r"\\\'u", "ú"),
        (r"\\\'A", "Á"), (r"\\\'E", "É"), (r"\\\'I", "Í"), (r"\\\'O", "Ó"), (r"\\\'U", "Ú"),
        
        # Acentos graves: \`a, \`{a}, etc.
        (r"\\`\{a\}", "à"), (r"\\`\{e\}", "è"), (r"\\`\{i\}", "ì"), (r"\\`\{o\}", "ò"), (r"\\`\{u\}", "ù"),
        (r"\\`a", "à"), (r"\\`e", "è"), (r"\\`i", "ì"), (r"\\`o", "ò"), (r"\\`u", "ù"),

        # Tilde (ñ, etc.): \~n, \~{n}, \~ n, etc.
        (r"\\~\{n\}", "ñ"), (r"\\~\{N\}", "Ñ"), (r"\\~n", "ñ"), (r"\\~N", "Ñ"), (r"\\~\s*n", "ñ"), (r"\\~\s*N", "Ñ"),

        # Diéresis / Umlaut: \"u, \"{u}, etc.
        (r'\\\"\{u\}', "ü"), (r'\\\"\{U\}', "Ü"), (r'\\\"u', "ü"), (r'\\\"U', "Ü"),
        (r'\\\"\{a\}', "ä"), (r'\\\"\{e\}', "ë"), (r'\\\"\{i\}', "ï"), (r'\\\"\{o\}', "ö"),

        # Cedilla: \c{c}, \c c
        (r"\\c\{c\}", "ç"), (r"\\c\{C\}", "Ç"), (r"\\c\s*c", "ç"), (r"\\c\s*C", "Ç"),

        # Circunflejo: \^a, \^{a}
        (r"\\\^\{a\}", "â"), (r"\\\^\{e\}", "ê"), (r"\\\^\{i\}", "î"), (r"\\\^\{o\}", "ô"), (r"\\\^\{u\}", "û"),
        (r"\\\^a", "â"), (r"\\\^e", "ê"), (r"\\\^i", "î"), (r"\\\^o", "ô"), (r"\\\^u", "û"),

        # Símbolos especiales
        (r"\\&", "&"), (r"\\%", "%"), (r"\\#", "#"), (r"\\_", "_"), (r"\\\$", "$"),
        (r"---", "—"), (r"--", "–"),
        (r"\\par\b", " "), (r"\\quad\b", " "), (r"\\qquad\b", " "),
        (r"\\vspace\{[^}]*\}", " "), (r"\\hspace\{[^}]*\}", " "),
        (r"\\multicolumn\{[^}]*\}\{[^}]*\}\{[^}]*\}", " "),
        (r"\\fb\b", ""), (r"\\titlerule\b", "")
    ]

    for pat, rep in replacements:
        text = re.sub(pat, rep, text)

    # 2. Comandos LaTeX con argumentos: \textbf{...}, \emph{...}, etc.
    for cmd in ["textsc", "textbf", "emph", "textit", "footnotesize", "small", "large", "Large", "LARGE", "url"]:
        text = re.sub(r"\\" + cmd + r"\{([^}]*)\}", r"\1", text)
    text = re.sub(r"\\href\{[^}]*\}\{([^}]*)\}", r"\1", text)

    # 3. Tratar i sin punto (dotless i): {\i} o \i
    text = re.sub(r"\{\\i\}", "i", text)
    text = re.sub(r"\\i\b", "i", text)

    # 4. Remover cualquier secuencia de control LaTeX restante
    text = re.sub(r"\\[a-zA-Z]+", "", text)

    # 5. Remover llaves protectoras de BibTeX {{...}} o {...}
    while "{" in text or "}" in text:
        prev = text
        text = re.sub(r"\{([^{}]*)\}", r"\1", text)
        if text == prev:
            text = text.replace("{", "").replace("}", "")
            break

    # 6. Limpiar virgulillas usadas como espacios duros
    text = text.replace("~", " ")

    # 7. Normalizar espacios múltiples
    text = re.sub(r"\s+", " ", text).strip()
    return text

def extract_bib_field(name: str, block: str) -> str:
    """Extrae el valor completo de un campo BibTeX respetando llaves anidadas balanceadas."""
    match = re.search(r'\b' + re.escape(name) + r'\s*=\s*', block, re.IGNORECASE)
    if not match:
        return ""
    idx = match.end()
    if idx >= len(block):
        return ""
    
    first_char = block[idx]
    if first_char == '{':
        depth = 0
        start = idx + 1
        for i in range(idx, len(block)):
            if block[i] == '{':
                depth += 1
            elif block[i] == '}':
                depth -= 1
                if depth == 0:
                    return block[start:i].strip()
        return block[start:].split('\n')[0].strip().rstrip(',')
    elif first_char == '"':
        start = idx + 1
        for i in range(start, len(block)):
            if block[i] == '"' and block[i-1] != '\\':
                return block[start:i].strip()
        return block[start:].split('\n')[0].strip().rstrip(',')
    else:
        end_match = re.search(r'[,}\n]', block[idx:])
        if end_match:
            return block[idx:idx + end_match.start()].strip()
        return block[idx:].split('\n')[0].strip().rstrip(',')

def parse_bib_file(bib_path: Path):
    """Parsea el archivo BibTeX a objetos estructurados con soporte de copia BibTeX."""
    if not bib_path.exists():
        return []
    
    content = bib_path.read_text(encoding='utf-8')
    entries = []
    
    # Regex para capturar entradas completas
    raw_entries = re.findall(r'(@[a-zA-Z]+\s*\{([^,]+),\s*([\s\S]*?\n\}))', content)
    
    for raw_block, cite_key, fields_block in raw_entries:
        entry_type_match = re.match(r'@([a-zA-Z]+)', raw_block)
        entry_type = entry_type_match.group(1).lower() if entry_type_match else "article"
        
        title = clean_latex(extract_bib_field('title', fields_block))
        author_raw = extract_bib_field('author', fields_block)
        authors = [clean_latex(a.strip()) for a in author_raw.split(' and ') if a.strip()]
        journal = clean_latex(extract_bib_field('journaltitle', fields_block) or extract_bib_field('journal', fields_block) or extract_bib_field('booktitle', fields_block))
        year = extract_bib_field('date', fields_block) or extract_bib_field('year', fields_block) or ""
        year = year.split('-')[0].strip()
        doi = extract_bib_field('doi', fields_block)
        url = extract_bib_field('url', fields_block)
        if not url and doi:
            url = f"https://doi.org/{doi}"
        abstract = clean_latex(extract_bib_field('abstract', fields_block))
        publisher = clean_latex(extract_bib_field('publisher', fields_block))
        keywords_raw = extract_bib_field('keywords', fields_block)
        keywords = [clean_latex(k) for k in keywords_raw.split(',') if k.strip() and not k.startswith('/') and 'No DOI' not in k]
        
        # Determinar cluster temático para el grafo
        cluster = "tecnopedagogia"
        text_for_cluster = f"{title} {abstract} {' '.join(keywords)}".lower()
        if any(w in text_for_cluster for w in ["ai", "inteligencia artificial", "deep learning", "diagnóstico", "cognitivo", "data", "ontolog"]):
            cluster = "ia_data_science"
        elif any(w in text_for_cluster for w in ["politica", "política", "gobernanza", "mintel", "unesco", "ética", "digital transformation"]):
            cluster = "politicas_direccion"
            
        entries.append({
            "id": cite_key.strip(),
            "type": entry_type,
            "title": title,
            "authors": authors,
            "venue": journal,
            "year": year,
            "doi": doi,
            "url": url,
            "abstract": abstract,
            "publisher": publisher,
            "keywords": keywords,
            "cluster": cluster,
            "bibtex": raw_block.strip()
        })
        
    # Ordenar por año descendente
    entries.sort(key=lambda x: x.get('year', '0'), reverse=True)
    return entries

def extract_section_content(latex: str, section_title: str) -> str:
    """Extrae el texto de una sección de LaTeX hasta la siguiente sección."""
    pattern = r'\\section\{' + re.escape(section_title) + r'\}'
    match = re.search(pattern, latex)
    if not match:
        return ""
    start = match.end()
    next_match = re.search(r'\\section\{', latex[start:])
    if next_match:
        return latex[start:start + next_match.start()]
    return latex[start:]

def parse_work_experience(section_text: str):
    """Extrae experiencias de la tabla de Experiencia Profesional."""
    items = []
    # Dividir por multicolumn o separadores de filas
    blocks = re.split(r'\\multicolumn\{2\}\{c\}\{\s*\}', section_text)
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        
        # Fechas
        dates_match = re.search(r'\\textsc\{([^}]+)\}(?:\s*(?:Actual|[\d]{2,4}|[a-zA-Z]+))?', block)
        date_str = ""
        if dates_match:
            date_str = clean_latex(dates_match.group(0))
            
        # Entidad
        org_match = re.search(r'\\textsc\{([^}]+)\}\s*\\\\(?:\s*([^\\]+)\\\\)?', block)
        org = clean_latex(org_match.group(1)) if org_match else ""
        unit = clean_latex(org_match.group(2)) if (org_match and org_match.group(2)) else ""
        
        # Cargo
        role_match = re.search(r'\\emph\{([^}]+)\}', block)
        role = clean_latex(role_match.group(1)) if role_match else ""
        
        # Descripción
        desc_match = re.search(r'\\footnotesize\{([^}]+)\}', block)
        desc = clean_latex(desc_match.group(1)) if desc_match else ""
        
        if org or role:
            items.append({
                "period": date_str or "Trayectoria",
                "organization": org,
                "unit": unit,
                "role": role,
                "description": desc,
                "type": "professional"
            })
    return items

def parse_teaching_experience(section_text: str):
    """Extrae experiencias docentes."""
    items = []
    blocks = re.split(r'\\multicolumn\{2\}\{c\}\{\s*\}', section_text)
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        
        # Fechas
        dates_match = re.search(r'\\textsc\{([^}]+)\}', block)
        date_str = clean_latex(dates_match.group(1)) if dates_match else ""
        
        # Universidad
        univ_match = re.search(r'\\textsc\{([^}]+)\}\s*\\\\', block)
        univ = clean_latex(univ_match.group(1)) if univ_match else ""
        
        # Cargo
        role_match = re.search(r'\\emph\{([^}]+)\}', block)
        role = clean_latex(role_match.group(1)) if role_match else "Docente"
        
        # Asignaturas
        subj_match = re.search(r'\\textbf\{Asignaturas impartidas[^:]*:\}\s*([^\\]+)', block)
        if not subj_match:
            subj_match = re.search(r'\\textbf\{Cursos impartidos:\}\s*([^\\]+)', block)
        subjects = clean_latex(subj_match.group(1)) if subj_match else ""
        
        # Descripción general
        desc_match = re.search(r'\\footnotesize\{([^}]+)\}', block)
        desc = clean_latex(desc_match.group(1)) if desc_match else ""
        
        if univ:
            items.append({
                "period": date_str,
                "institution": univ,
                "role": role,
                "subjects": subjects,
                "description": desc,
                "type": "teaching"
            })
    return items

def parse_education(section_text: str):
    """Extrae títulos universitarios."""
    items = []
    blocks = re.split(r'\\multicolumn\{2\}\{c\}\{\s*\}', section_text)
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        
        year_match = re.search(r'\\textsc\{(\d{4})\}', block)
        year = year_match.group(1) if year_match else ""
        
        univ_match = re.search(r'\\textbf\{([^}]+)\}', block)
        univ = clean_latex(univ_match.group(1)) if univ_match else ""
        
        # Grado
        degree_match = re.search(r'(Doctorado|Diplomado|Máster Universitario|Posgrado|Especialización|Licenciatura[^\\]*)', block)
        degree_type = degree_match.group(1).strip() if degree_match else "Título"
        
        spec_match = re.search(r'\\textsc\{([^}]+)\}', block[year_match.end():] if year_match else block)
        spec = clean_latex(spec_match.group(1)) if spec_match else ""
        
        title = f"{degree_type} en {spec}" if spec and degree_type != spec else (spec or degree_type)
        
        status = "En curso" if "En curso" in block else "Concluido"
        
        items.append({
            "year": year,
            "degree": clean_latex(title),
            "institution": univ,
            "status": status
        })
    return items

def parse_certifications(section_text: str, json_path: Path):
    """Extrae certificaciones de cv.tex y las fusiona con data/certificates.json."""
    items = []
    
    # 1. Parsear desde cv.tex si hay sección
    if section_text:
        blocks = re.split(r'\\multicolumn\{2\}\{c\}\{\s*\}', section_text)
        for block in blocks:
            block = block.strip()
            if not block:
                continue
            year_match = re.search(r'\\textsc\{(\d{4})\}', block)
            year = year_match.group(1) if year_match else ""
            
            # Título completo de la línea
            title = ""
            if '&' in block:
                title_line = block.split('&', 1)[1]
                title_raw = title_line.split('\\\\')[0].strip() if '\\\\' in title_line else title_line.split('\n')[0].strip()
                title = clean_latex(title_raw)
            
            # Emisor
            inst_match = re.search(r'\\textbf\{([^}]+)\}', block)
            issuer = clean_latex(inst_match.group(1)) if inst_match else ""
            
            # URL
            url_match = re.search(r'\\(?:url|href(?:\{[^}]*\})?)\{([^}]+)\}', block)
            url = url_match.group(1) if url_match else ""
            
            # Registro
            reg_match = re.search(r'Reg\.?\s*([^\n\\]+)', block)
            reg = clean_latex(reg_match.group(1)) if reg_match else ""
            
            if title:
                items.append({
                    "id": f"cert-tex-{year}-{len(items)}",
                    "docType": "Cert",
                    "fileName": "",
                    "shortName": "",
                    "role": "Participante",
                    "title": title,
                    "issuer": issuer,
                    "year": str(year),
                    "date": str(year) if year else "",
                    "hours": None,
                    "modality": "",
                    "credentialId": reg or None,
                    "verificationUrl": url if "drive.google.com" not in url else None,
                    "driveUrl": url if "drive.google.com" in url else None,
                    "cluster": "tecnopedagogia",
                    "skills": []
                })

    # 2. Cargar y fusionar con data/certificates.json (Google Drive / Gemini)
    if json_path.exists():
        try:
            drive_certs = json.loads(json_path.read_text(encoding='utf-8'))
            for dc in drive_certs:
                title = clean_latex(dc.get("title", ""))
                norm_key = re.sub(r'\W+', '', title.lower())
                
                # Buscar si ya existe para enriquecer
                matched = next((item for item in items if norm_key in re.sub(r'\W+', '', item["title"].lower()) or re.sub(r'\W+', '', item["title"].lower()) in norm_key), None)
                if matched:
                    if dc.get("docType"):
                        matched["docType"] = dc["docType"]
                    if dc.get("fileName"):
                        matched["fileName"] = dc["fileName"]
                    if dc.get("shortName"):
                        matched["shortName"] = dc["shortName"]
                    if dc.get("role"):
                        matched["role"] = dc["role"]
                    if dc.get("driveUrl"):
                        matched["driveUrl"] = dc["driveUrl"]
                    if dc.get("skills"):
                        matched["skills"] = dc["skills"]
                    if dc.get("cluster"):
                        matched["cluster"] = dc["cluster"]
                    if dc.get("hours"):
                        matched["hours"] = dc["hours"]
                    if dc.get("modality"):
                        matched["modality"] = dc["modality"]
                    if dc.get("credentialId"):
                        matched["credentialId"] = dc["credentialId"]
                    if dc.get("date"):
                        matched["date"] = dc["date"]
                    if dc.get("month"):
                        matched["month"] = str(dc["month"])
                    if dc.get("yearShort"):
                        matched["yearShort"] = str(dc["yearShort"])
                    if dc.get("verificationUrl"):
                        matched["verificationUrl"] = dc["verificationUrl"]
                else:
                    items.append({
                        "id": dc.get("id", f"cert-{len(items)}"),
                        "docType": dc.get("docType", "Cert"),
                        "fileName": dc.get("fileName", ""),
                        "shortName": dc.get("shortName", ""),
                        "role": dc.get("role", ""),
                        "title": title,
                        "issuer": clean_latex(dc.get("issuer", "")),
                        "year": str(dc.get("year", "")),
                        "yearShort": str(dc.get("yearShort", "")),
                        "month": str(dc.get("month", "")),
                        "date": dc.get("date", ""),
                        "hours": dc.get("hours"),
                        "modality": dc.get("modality", ""),
                        "credentialId": dc.get("credentialId"),
                        "verificationUrl": dc.get("verificationUrl"),
                        "driveUrl": dc.get("driveUrl"),
                        "cluster": dc.get("cluster", "tecnopedagogia"),
                        "skills": dc.get("skills", [])
                    })
        except Exception as e:
            print(f"[!] Error leyendo {json_path}: {e}")
            
    # Ordenar estrictamente por año y mes descendente (más reciente primero)
    def get_sort_key(item):
        date_str = str(item.get("date") or "").strip()
        m_date = re.match(r'^(\d{4})[-/](\d{1,2})', date_str)
        if m_date:
            return f"{m_date.group(1)}-{m_date.group(2).zfill(2)}"
        
        y = str(item.get("year") or "0000").strip()
        m_y = re.search(r'\d{4}', y)
        year_val = m_y.group(0) if m_y else (("20" + y) if len(y) == 2 and y.isdigit() else "0000")
        
        month_val = str(item.get("month") or "00").strip().zfill(2)
        return f"{year_val}-{month_val}"

    items.sort(key=get_sort_key, reverse=True)
    return items

def parse_projects(section_text: str):
    """Extrae los proyectos relevantes de la tabla."""
    items = []
    blocks = re.split(r'\\multicolumn\{2\}\{c\}\{\s*\}', section_text)
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        
        year_match = re.search(r'\\textsc\{(\d{4})\}', block)
        year = year_match.group(1) if year_match else ""
        
        org_match = re.search(r'\\textsc\{([^}]+)\}', block[year_match.end():] if year_match else block)
        org = clean_latex(org_match.group(1)) if org_match else ""
        
        proj_match = re.search(r'\\emph\{Proyecto:\s*([^}]+)\}', block)
        if not proj_match:
            proj_match = re.search(r'\\emph\{([^}]+)\}', block)
        proj = clean_latex(proj_match.group(1)) if proj_match else ""
        
        if org or proj:
            items.append({
                "year": year,
                "organization": org,
                "project": proj
            })
    return items

def build_knowledge_graph(profile, projects, publications, digital_resources, github_repos=None, digital_garden_posts=None, certifications=None):
    """Construye los nodos y aristas del Espacio Latente (Knowledge Graph interactivo)."""
    clusters = [
        {
            "id": "ia_data_science",
            "name": "Inteligencia Artificial & Data Science",
            "color": "#0ea5e9",
            "description": "Modelos de diagnóstico cognitivo, Deep Learning, analítica educativa, ontologías y ecosistemas neuro-simbólicos."
        },
        {
            "id": "politicas_direccion",
            "name": "Políticas Públicas & Dirección",
            "color": "#8b5cf6",
            "description": "Gobernanza de tecnologías emergentes, ética de la IA (UNESCO), agendas digitales (BID, CEPAL, CAN) y dirección estratégica."
        },
        {
            "id": "tecnopedagogia",
            "name": "Tecnopedagogía & Aprendizaje Digital",
            "color": "#10b981",
            "description": "Producción virtual e-learning a gran escala, LMS Moodle, diseño tecnopedagógico, pensamiento computacional y STEAM."
        }
    ]
    
    nodes = []
    links = []
    node_ids = set()
    
    def add_node(node_id, label, cluster, node_type, size=15, info=""):
        if node_id not in node_ids:
            nodes.append({
                "id": node_id,
                "label": label,
                "cluster": cluster,
                "type": node_type,
                "size": size,
                "info": info
            })
            node_ids.add(node_id)
            
    def add_link(source, target, relationship="relacionado", value=1):
        links.append({
            "source": source,
            "target": target,
            "relationship": relationship,
            "value": value
        })
        
    # Nodo Central
    root_id = "marcelo"
    add_node(root_id, "Marcelo Sotaminga", "central", "root", size=30, info="Arquitecto Tecnopedagógico e Investigador en IA")
    
    # Nodos Cluster
    for c in clusters:
        add_node(c["id"], c["name"], c["id"], "cluster_root", size=24, info=c["description"])
        add_link(root_id, c["id"], "dimensión clave", value=3)
        
    # Nodos para IA & Data Science
    ai_pillars = [
        ("diagnostico_cognitivo", "Diagnóstico Cognitivo", "Modelos psicométricos y redes neuronales"),
        ("neuro_simbolico", "Ecosistema Neuro-Simbólico", "IALab Universidad de La Sabana"),
        ("deep_learning", "Deep Learning & NLP", "Modelos de lenguaje y feedback formativo"),
        ("ontologias", "Ontologías Educativas", "Modelamiento semántico del conocimiento"),
        ("python_data", "Python & SQL / R", "Flujos ETL y analítica de datos")
    ]
    for nid, lbl, inf in ai_pillars:
        add_node(nid, lbl, "ia_data_science", "pillar", size=18, info=inf)
        add_link("ia_data_science", nid, "área técnica", value=2)
        
    # Nodos para Políticas Públicas & Dirección
    policy_pillars = [
        ("mintel_te", "MINTEL Tecnologías Emergentes", "Dirección nacional de adopción tecnológica"),
        ("unesco_etica", "Ética de la IA - UNESCO", "Red de países adoptantes de recomendaciones éticas"),
        ("agenda_bid", "Agenda Transformación Digital - BID", "Estrategia país con el Banco Interamericano"),
        ("agenda_andina", "Agenda Digital Andina (CAN)", "Integración y telecomunicaciones"),
        ("espiral_ceo", "Dirección Espiral Educativa", "Gestión de proyectos y consultoría internacional")
    ]
    for nid, lbl, inf in policy_pillars:
        add_node(nid, lbl, "politicas_direccion", "pillar", size=18, info=inf)
        add_link("politicas_direccion", nid, "iniciativa clave", value=2)
        
    # Nodos para Tecnopedagogía & Aprendizaje
    ed_pillars = [
        ("unisabana_pv", "Jefatura Producción Virtual Unisabana", "Ecosistemas e-learning y gobernanza TIC"),
        ("moodle_scale", "LMS Moodle a Escala", "Administración, plugins, SCORM y analítica"),
        ("pensamiento_comp", "Pensamiento Computacional (Scratch)", "Proyectos con OEI y CIESPAL"),
        ("docencia_posgrados", "Docencia Posgrados Iberoamérica", "Maestrías en UOC, Sabana, UNAE, UTEG"),
        ("evaluacion_calidad", "Calidad & Acreditación Superior", "Modelos tecnopedagógicos y SGIC")
    ]
    for nid, lbl, inf in ed_pillars:
        add_node(nid, lbl, "tecnopedagogia", "pillar", size=18, info=inf)
        add_link("tecnopedagogia", nid, "competencia núcleo", value=2)
        
    # Conexiones sinérgicas inter-cluster (Puentes Tecnopedagógicos)
    add_link("neuro_simbolico", "unisabana_pv", "investigación aplicada", value=2)
    add_link("deep_learning", "moodle_scale", "asistentes de feedback en LMS", value=2)
    add_link("unesco_etica", "pensamiento_comp", "formación ciudadana y ética digital", value=2)
    add_link("docencia_posgrados", "diagnostico_cognitivo", "evaluación de competencias en aula", value=2)
    
    # Conectar Repositorios de GitHub destacados
    for repo in (github_repos or []):
        repo_id = f"repo_{repo['name']}"
        add_node(repo_id, repo['title'][:28] + "...", repo['cluster'], "repository", size=13, info=f"{repo['title']} - {repo['description'][:80]}...")
        if repo['name'] == 'curso_llm':
            add_link("deep_learning", repo_id, "repositorio GitHub", value=2)
        elif repo['name'] in ['scriptScratch', 'ProgramacionPensamientoComputacional']:
            add_link("pensamiento_comp", repo_id, "recurso abierto STEAM", value=2)
        elif repo['name'] in ['ibook-FSO', 'ebook-IHM', 'cajaherramientas']:
            add_link("unisabana_pv", repo_id, "material docente interactivo", value=2)
        elif repo['name'] == 'ebook-matematica-discreta':
            add_link("diagnostico_cognitivo", repo_id, "recurso de ingeniería", value=2)
        elif repo['name'] == 'marchelo2212.github.io':
            add_link("ontologias", repo_id, "jardín digital Quartz", value=2)
        else:
            add_link(repo['cluster'], repo_id, "código abierto", value=1)

    # Conectar notas y ensayos de investigación del Jardín Digital (Quartz)
    for post in (digital_garden_posts or []):
        post_id = f"blog_{post['title'][:20].lower().replace(' ', '_').replace(':', '')}"
        add_node(post_id, post['title'][:26] + "...", post['cluster'], "blog_post", size=13, info=f"[{post['collection']}] {post['title']} - {post['description'][:80]}...")
        t_low = post['title'].lower()
        if "ia" in t_low or "mitos" in t_low:
            add_link("deep_learning", post_id, "ensayo conceptual", value=2)
        elif "moodle" in t_low:
            add_link("moodle_scale", post_id, "artículo técnico LMS", value=2)
        elif "telegram" in t_low or "obsidian" in t_low:
            add_link("ontologias", post_id, "metodología PKM", value=2)
        elif "robotica" in t_low or "steam" in t_low:
            add_link("pensamiento_comp", post_id, "recurso STEAM", value=2)
        else:
            add_link(post['cluster'], post_id, "publicación digital", value=1)

    # Conectar certificaciones clave al Knowledge Graph
    for cert in (certifications or []):
        c_title = cert.get("title", "")
        c_id = f"cert_{cert.get('id', c_title[:20].lower().replace(' ', '_'))}"
        cluster = cert.get("cluster", "tecnopedagogia")
        add_node(c_id, c_title[:26] + "...", cluster, "certification", size=13, info=f"Certificación: {c_title} ({cert.get('issuer', '')}, {cert.get('year', '')})")
        add_link(cluster, c_id, "credencial validada", value=2)

    return {
        "clusters": clusters,
        "nodes": nodes,
        "links": links
    }

def main():
    print(f"[*] Parseando CV desde {CV_TEX_PATH}...")
    tex_content = CV_TEX_PATH.read_text(encoding='utf-8')
    
    # 1. Metadatos de perfil
    profile = {
        "fullName": "Marcelo Javier Sotaminga Cinilin",
        "title": "Arquitecto Tecnopedagógico & Investigador en IA Educativa",
        "orcid": "0000-0003-4250-906X",
        "orcidUrl": "https://orcid.org/0000-0003-4250-906X",
        "github": "marchelo2212",
        "githubUrl": "https://github.com/marchelo2212",
        "linkedin": "marchelo2212",
        "linkedinUrl": "https://www.linkedin.com/in/marchelo2212",
        "twitter": "marchelo2212",
        "twitterUrl": "https://x.com/marchelo2212",
        "facebook": "marchelo2212",
        "facebookUrl": "https://www.facebook.com/marchelo2212",
        "email": "marcelo.sotaminga@gmail.com",
        "emailUnisabana": "marcelo.sotaminga@unisabana.edu.co",
        "emailUoc": "msotaminga@uoc.edu",
        "emails": [
            { "label": "Universidad de La Sabana", "address": "marcelo.sotaminga@unisabana.edu.co", "badge": "Unisabana", "type": "institutional" },
            { "label": "Universitat Oberta de Catalunya", "address": "msotaminga@uoc.edu", "badge": "UOC", "type": "institutional" },
            { "label": "Correo Personal", "address": "marcelo.sotaminga@gmail.com", "badge": "Personal", "type": "personal" }
        ],
        "social": [
            { "name": "LinkedIn", "url": "https://www.linkedin.com/in/marchelo2212", "icon": "fa-brands fa-linkedin-in", "handle": "marchelo2212" },
            { "name": "X (Twitter)", "url": "https://x.com/marchelo2212", "icon": "fa-brands fa-x-twitter", "handle": "@marchelo2212" },
            { "name": "Facebook", "url": "https://www.facebook.com/marchelo2212", "icon": "fa-brands fa-facebook-f", "handle": "marchelo2212" },
            { "name": "GitHub", "url": "https://github.com/marchelo2212", "icon": "fa-brands fa-github", "handle": "marchelo2212" },
            { "name": "ORCID", "url": "https://orcid.org/0000-0003-4250-906X", "icon": "fa-brands fa-orcid", "handle": "0000-0003-4250-906X" }
        ],
        "website": "https://marchelo2212.espiraleducativa.org",
        "currentRole": "Jefe de Producción Virtual | Unisabana e-learning",
        "doctorate": "Doctorando en Ingeniería (Informática), Universidad de La Sabana",
        "location": "Cajicá / Bogotá, Colombia",
        "photo": "foto_ms.png"
    }
    
    # Acerca de mí
    about_text = extract_section_content(tex_content, "Acerca de mí")
    profile["bio"] = clean_latex(about_text)
    
    # 2. Experiencia Profesional
    exp_text = extract_section_content(tex_content, "Experiencia Profesional")
    work_experience = parse_work_experience(exp_text)
    
    # 3. Experiencia Docente
    teaching_text = extract_section_content(tex_content, "Experiencia Docente en Educación Superior")
    teaching_experience = parse_teaching_experience(teaching_text)
    
    # 4. Educación
    edu_text = extract_section_content(tex_content, "Educación Universitaria")
    education = parse_education(edu_text)
    
    # 4b. Certificaciones y Credenciales
    cert_text = extract_section_content(tex_content, "Certificaciones")
    certifications = parse_certifications(cert_text, CERTIFICATES_PATH)
    
    # 5. Proyectos
    proj_text = extract_section_content(tex_content, "Proyectos Relevantes")
    projects_raw = parse_projects(proj_text)
    
    # 6. Publicaciones desde bibliografia.bib
    print(f"[*] Parseando publicaciones desde {BIB_PATH}...")
    publications = parse_bib_file(BIB_PATH)
    
    # 7. Leer Enriquecimiento manual (data/enrichment.json)
    enrichment = {}
    if ENRICHMENT_PATH.exists():
        print(f"[*] Cargando enriquecimiento desde {ENRICHMENT_PATH}...")
        enrichment = json.loads(ENRICHMENT_PATH.read_text(encoding='utf-8'))
        
    # Mezclar proyectos con enriquecimiento
    enriched_projects = []
    project_enrichments = enrichment.get("projectEnrichments", [])
    for p in projects_raw:
        matched_enr = next((e for e in project_enrichments if e.get("matchKey", "").lower() in p["project"].lower()), None)
        item = {
            "year": p["year"],
            "organization": p["organization"],
            "title": p["project"],
            "cluster": matched_enr.get("cluster", "tecnopedagogia") if matched_enr else "tecnopedagogia",
            "featured": matched_enr.get("featured", False) if matched_enr else False,
            "badge": matched_enr.get("badge", "") if matched_enr else "",
            "links": matched_enr.get("links", []) if matched_enr else [],
            "tags": matched_enr.get("tags", []) if matched_enr else [],
            "image": matched_enr.get("image", "") if matched_enr else ""
        }
        enriched_projects.append(item)
        
    digital_resources = enrichment.get("digitalResources", [])
    github_repositories = enrichment.get("githubRepositories", [])
    digital_garden_posts = enrichment.get("digitalGardenPosts", [])
    ai_knowledge = enrichment.get("aiAssistantKnowledge", [])
    
    # Actualizar bio o detalles si vienen en enrichment
    if "profileAdditions" in enrichment:
        for k, v in enrichment["profileAdditions"].items():
            if v:
                profile[k] = v
                
    # 8. Generar Knowledge Graph
    knowledge_graph = build_knowledge_graph(profile, enriched_projects, publications, digital_resources, github_repositories, digital_garden_posts, certifications=certifications)
    
    # 9. Métricas Cuantitativas
    metrics = [
        { "value": "15+", "label": "Años de Trayectoria", "subtext": "Transformación digital & EdTech" },
        { "value": "4", "label": "Países con Cooperación", "subtext": "UNESCO, BID, CEPAL, CAN" },
        { "value": "10+", "label": "Universidades & Posgrados", "subtext": "Docencia de grado y posgrado" },
        { "value": f"{len(publications)}", "label": "Publicaciones Indexadas", "subtext": "Springer, Scopus, Latindex" }
    ]
    
    # 10. Estructura final del JSON
    final_data = {
        "profile": profile,
        "metrics": metrics,
        "knowledgeGraph": knowledge_graph,
        "aiKnowledgeBase": ai_knowledge,
        "publications": publications,
        "projects": enriched_projects,
        "digitalResources": digital_resources,
        "githubRepositories": github_repositories,
        "digitalGardenPosts": digital_garden_posts,
        "workExperience": work_experience,
        "teachingExperience": teaching_experience,
        "education": education,
        "certifications": certifications
    }
    
    OUTPUT_PATH.write_text(json.dumps(final_data, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"[+] Archivo generado con éxito en: {OUTPUT_PATH}")
    print(f"    - Publicaciones extraídas: {len(publications)}")
    print(f"    - Certificaciones registradas: {len(certifications)}")
    print(f"    - Proyectos procesados: {len(enriched_projects)}")
    print(f"    - Repositorios de GitHub incorporados: {len(github_repositories)}")
    print(f"    - Experiencias laborales: {len(work_experience)}")
    print(f"    - Experiencias docentes: {len(teaching_experience)}")
    print(f"    - Nodos del Knowledge Graph: {len(knowledge_graph['nodes'])}")
    print(f"    - Aristas del Knowledge Graph: {len(knowledge_graph['links'])}")

if __name__ == "__main__":
    main()

