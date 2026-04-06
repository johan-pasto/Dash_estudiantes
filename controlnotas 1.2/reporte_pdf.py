from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)

# ── COLORES ──────────────────────────────────────────────────────────────────
DARK     = colors.HexColor("#1a1a18")
MUTED    = colors.HexColor("#9a9a94")
BORDER   = colors.HexColor("#e8e8e4")
BG       = colors.HexColor("#f7f7f5")
GREEN    = colors.HexColor("#27ae60");  GREEN_S  = colors.HexColor("#eafaf1")
YELLOW   = colors.HexColor("#d4ac0d");  YELLOW_S = colors.HexColor("#fefaec")
RED      = colors.HexColor("#c0392b");  RED_S    = colors.HexColor("#fdf0ee")
GOLD     = colors.HexColor("#c9a84c");  GOLD_S   = colors.HexColor("#fdf5e0")


def _color_promedio(p):
    """Devuelve (color_texto, color_fondo) según el nivel del promedio."""
    if p == 5.0: return GOLD,   GOLD_S
    if p >= 4.0: return GREEN,  GREEN_S
    if p >= 3.0: return YELLOW, YELLOW_S
    return RED, RED_S


def _label_promedio(p):
    if p == 5.0: return "Excepcional"
    if p >= 4.0: return "Bueno"
    if p >= 3.0: return "Regular"
    return "Malo"


def generar_pdf(estudiante, historial, stats, posicion, diferencia):
    """
    Genera el PDF del reporte del estudiante y lo devuelve como BytesIO.
    Parámetros:
        estudiante  — dict con nombre, carrera, nota1, nota2, nota3, promedio
        historial   — lista de registros de historial_notas
        stats       — dict con promedio_carrera, total, aprobados, reprobados
        posicion    — int, puesto en la carrera
        diferencia  — float, promedio estudiante - promedio carrera
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        rightMargin=0.75*inch, leftMargin=0.75*inch,
        topMargin=0.75*inch,   bottomMargin=0.75*inch,
    )
    styles = getSampleStyleSheet()
    story  = []

    # ── ESTILOS ───────────────────────────────────────────────────────────────
    s_titulo = ParagraphStyle("titulo", fontSize=20, fontName="Helvetica-Bold",
                               textColor=DARK, alignment=TA_LEFT, spaceAfter=2)
    s_sub    = ParagraphStyle("sub", fontSize=10, fontName="Helvetica",
                               textColor=MUTED, alignment=TA_LEFT)
    s_sec    = ParagraphStyle("sec", fontSize=7, fontName="Helvetica-Bold",
                               textColor=MUTED, spaceBefore=14, spaceAfter=8)
    s_normal = ParagraphStyle("nor", fontSize=9, fontName="Helvetica", textColor=DARK)
    s_fecha  = ParagraphStyle("fec", fontSize=8, fontName="Helvetica",
                               textColor=MUTED, alignment=TA_RIGHT)
    s_pie    = ParagraphStyle("pie", fontSize=7, fontName="Helvetica",
                               textColor=MUTED, alignment=TA_CENTER)

    # ── ENCABEZADO ────────────────────────────────────────────────────────────
    fecha_hoy = datetime.now().strftime("%d/%m/%Y %H:%M")
    header = Table([[
        Paragraph("Reporte de Notas", s_titulo),
        Paragraph(f"Generado el {fecha_hoy}", s_fecha),
    ]], colWidths=["70%","30%"])
    header.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"BOTTOM"),
                                 ("BOTTOMPADDING",(0,0),(-1,-1),0)]))
    story.append(header)
    story.append(Paragraph(
        f"{estudiante['nombre']}  -  {estudiante.get('carrera','')}", s_sub))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1, color=BORDER))
    story.append(Spacer(1, 12))

    # ── NOTAS ACTUALES ────────────────────────────────────────────────────────
    story.append(Paragraph("NOTAS ACTUALES", s_sec))
    promedio = float(estudiante.get("promedio") or 0)
    tc, bc   = _color_promedio(promedio)
    nivel    = _label_promedio(promedio)

    t_notas = Table(
        [["Nota 1","Nota 2","Nota 3","Promedio","Nivel"],
         [str(estudiante.get("nota1","—")), str(estudiante.get("nota2","—")),
          str(estudiante.get("nota3","—")), str(promedio), nivel]],
        colWidths=["18%","18%","18%","23%","23%"]
    )
    t_notas.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,0), BG),
        ("TEXTCOLOR",     (0,0),(-1,0), MUTED),
        ("FONTNAME",      (0,0),(-1,0), "Helvetica-Bold"),
        ("FONTSIZE",      (0,0),(-1,0), 7),
        ("ALIGN",         (0,0),(-1,-1),"CENTER"),
        ("TOPPADDING",    (0,0),(-1,-1), 7),
        ("BOTTOMPADDING", (0,0),(-1,-1), 7),
        ("FONTNAME",      (0,1),(-1,1), "Helvetica-Bold"),
        ("FONTSIZE",      (0,1),(-1,1), 13),
        ("BACKGROUND",    (4,1),(4,1),  bc),
        ("TEXTCOLOR",     (4,1),(4,1),  tc),
        ("GRID",          (0,0),(-1,-1), 0.5, BORDER),
    ]))
    story.append(t_notas)
    story.append(Spacer(1, 12))

    # ── COMPARACIÓN CON LA CARRERA ────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
    story.append(Paragraph("COMPARACION CON LA CARRERA", s_sec))

    s = stats or {}
    pc         = float(s.get("promedio_carrera") or 0)
    total      = s.get("total",      0) or 0
    aprobados  = s.get("aprobados",  0) or 0
    reprobados = s.get("reprobados", 0) or 0

    t_comp = Table(
        [["Promedio carrera","Total estudiantes","Aprobados","Reprobados","Tu posicion"],
         [str(pc), str(total), str(aprobados), str(reprobados),
          f"#{posicion}" if posicion else "—"]],
        colWidths=["22%","20%","18%","18%","22%"]
    )
    t_comp.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,0), BG),
        ("TEXTCOLOR",     (0,0),(-1,0), MUTED),
        ("FONTNAME",      (0,0),(-1,0), "Helvetica-Bold"),
        ("FONTSIZE",      (0,0),(-1,0), 7),
        ("ALIGN",         (0,0),(-1,-1),"CENTER"),
        ("TOPPADDING",    (0,0),(-1,-1), 7),
        ("BOTTOMPADDING", (0,0),(-1,-1), 7),
        ("FONTNAME",      (0,1),(-1,1), "Helvetica-Bold"),
        ("FONTSIZE",      (0,1),(-1,1), 13),
        ("GRID",          (0,0),(-1,-1), 0.5, BORDER),
    ]))
    story.append(t_comp)
    story.append(Spacer(1, 8))

    # Mensaje diferencia
    if diferencia > 0:
        diff_msg   = f"Estas {diferencia} puntos por encima del promedio de tu carrera."
        diff_color = GREEN
    elif diferencia < 0:
        diff_msg   = f"Estas {abs(diferencia)} puntos por debajo del promedio de tu carrera."
        diff_color = RED
    else:
        diff_msg   = "Estas exactamente en el promedio de tu carrera."
        diff_color = MUTED

    story.append(Paragraph(diff_msg, ParagraphStyle(
        "diff", fontSize=9, fontName="Helvetica-Bold", textColor=diff_color)))
    story.append(Spacer(1, 12))

    # ── HISTORIAL ─────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
    story.append(Paragraph("HISTORIAL DE CAMBIOS DE NOTAS", s_sec))

    if historial:
        hist_rows = [["#","Fecha","Nota 1","Nota 2","Nota 3","Promedio","Tendencia"]]
        for i, h in enumerate(historial):
            p_h = float(h.get("promedio") or 0)
            if i < len(historial) - 1:
                p_ant = float(historial[i+1].get("promedio") or 0)
                tend = "Subio" if p_h > p_ant else ("Bajo" if p_h < p_ant else "Igual")
            else:
                tend = "Inicial"
            hist_rows.append([
                str(i+1), h.get("fecha_fmt","—"),
                str(h.get("nota1","—")), str(h.get("nota2","—")),
                str(h.get("nota3","—")), str(p_h), tend,
            ])

        t_hist = Table(hist_rows, colWidths=["6%","22%","12%","12%","12%","14%","22%"])
        hist_style = [
            ("BACKGROUND",    (0,0),(-1,0), BG),
            ("TEXTCOLOR",     (0,0),(-1,0), MUTED),
            ("FONTNAME",      (0,0),(-1,0), "Helvetica-Bold"),
            ("FONTSIZE",      (0,0),(-1,-1), 8),
            ("ALIGN",         (0,0),(-1,-1), "CENTER"),
            ("TOPPADDING",    (0,0),(-1,-1), 6),
            ("BOTTOMPADDING", (0,0),(-1,-1), 6),
            ("GRID",          (0,0),(-1,-1), 0.5, BORDER),
            ("ROWBACKGROUNDS",(0,1),(-1,-1), [colors.white, BG]),
        ]
        # Color de fondo en celda de promedio según nivel
        for i, h in enumerate(historial):
            _, bg = _color_promedio(float(h.get("promedio") or 0))
            hist_style.append(("BACKGROUND", (5, i+1), (5, i+1), bg))

        t_hist.setStyle(TableStyle(hist_style))
        story.append(t_hist)
    else:
        story.append(Paragraph(
            "Aun no hay cambios registrados en las notas de este estudiante.",
            ParagraphStyle("vacio", fontSize=9, fontName="Helvetica", textColor=MUTED)
        ))

    # ── PIE ───────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "Control de Notas  -  Documento generado automaticamente", s_pie))

    doc.build(story)
    buffer.seek(0)
    return buffer