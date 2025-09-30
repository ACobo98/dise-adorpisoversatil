import streamlit as st
import math
from PIL import Image, ImageDraw
from datetime import datetime
import os

# --- Page Configuration ---
st.set_page_config(page_title="Diseñador de Pisos Versátil", layout="wide")
st.title("🎨 Diseñador de Pisos Versátil v1.0")

# --- Product Constants ---
TAMANO_BALDOSA_M = 0.25 # <-- TAMAÑO ACTUALIZADO

# --- Sidebar: Input Parameters ---
st.sidebar.header("1. Dimensiones del Área")
modo = st.sidebar.radio("Modo de entrada", ["Metros", "Piezas"])

if modo == "Metros":
    ancho_m = st.sidebar.number_input("Ancho deseado (m)", min_value=0.1, step=0.1, value=5.0)
    largo_m = st.sidebar.number_input("Largo deseado (m)", min_value=0.1, step=0.1, value=6.0)
else:
    piezas_ancho_in = st.sidebar.number_input("Piezas de ancho", min_value=1, step=1, value=20)
    piezas_largo_in = st.sidebar.number_input("Piezas de largo", min_value=1, step=1, value=24)
    ancho_m = piezas_ancho_in * TAMANO_BALDOSA_M
    largo_m = piezas_largo_in * TAMANO_BALDOSA_M

# --- Sidebar: Prices and Colors ---
st.sidebar.header("2. Precios y Colores")
precio_m2 = st.sidebar.number_input("Precio por m² de baldosa ($)", min_value=0.0, step=0.5, value=17.50) # <-- PRECIO ACTUALIZADO

# Paleta de colores actualizada para Piso Versátil
PALETA = ["Negro", "Rojo", "Azul", "Blanco", "Amarillo", "Naranja", "Gris"]
color = st.sidebar.selectbox("Color principal de baldosas", PALETA)

# --- Main Calculation Logic ---
baldosas_enteras_ancho = math.floor(ancho_m / TAMANO_BALDOSA_M)
espacio_cubierto_ancho = baldosas_enteras_ancho * TAMANO_BALDOSA_M
espacio_sobrante_ancho = ancho_m - espacio_cubierto_ancho

baldosas_enteras_largo = math.floor(largo_m / TAMANO_BALDOSA_M)
espacio_cubierto_largo = baldosas_enteras_largo * TAMANO_BALDOSA_M
espacio_sobrante_largo = largo_m - espacio_cubierto_largo

st.sidebar.header("3. Acabado de los Extremos")
st.sidebar.info(f"Ancho: {baldosas_enteras_ancho} baldosas enteras cubren {espacio_cubierto_ancho:.2f}m. Faltan **{espacio_sobrante_ancho*100:.1f} cm**.")

# Opciones de acabado simplificadas
opciones_acabado = ["Nada", "Completar con Pieza Cortada"]
col_izq, col_der = st.sidebar.columns(2)
acabado_izquierdo = col_izq.selectbox("Acabado Izquierda", opciones_acabado, key="acabado_izq")
acabado_derecho = col_der.selectbox("Acabado Derecha", opciones_acabado, key="acabado_der")

st.sidebar.info(f"Largo: {baldosas_enteras_largo} baldosas enteras cubren {espacio_cubierto_largo:.2f}m. Faltan **{espacio_sobrante_largo*100:.1f} cm**.")
col_arr, col_abj = st.sidebar.columns(2)
acabado_arriba = col_arr.selectbox("Acabado Arriba", opciones_acabado, key="acabado_arr")
acabado_abajo = col_abj.selectbox("Acabado Abajo", opciones_acabado, key="acabado_abj")

# --- Calculate pieces to dispatch and final dimensions ---
piezas_ancho_despachar = baldosas_enteras_ancho
ancho_necesita_corte = False
if acabado_izquierdo == "Completar con Pieza Cortada":
    piezas_ancho_despachar += 1
    ancho_necesita_corte = True
if acabado_derecho == "Completar con Pieza Cortada" and acabado_izquierdo != "Completar con Pieza Cortada":
    piezas_ancho_despachar += 1
    ancho_necesita_corte = True
dim_final_ancho = ancho_m if ancho_necesita_corte else espacio_cubierto_ancho

piezas_largo_despachar = baldosas_enteras_largo
largo_necesita_corte = False
if acabado_arriba == "Completar con Pieza Cortada":
    piezas_largo_despachar += 1
    largo_necesita_corte = True
if acabado_abajo == "Completar con Pieza Cortada" and acabado_arriba != "Completar con Pieza Cortada":
    piezas_largo_despachar += 1
    largo_necesita_corte = True
dim_final_largo = largo_m if largo_necesita_corte else espacio_cubierto_largo


# --- Color Grid Logic ---
piezas_ancho = piezas_ancho_despachar
piezas_largo = piezas_largo_despachar

grid_shape_actual = (piezas_largo, piezas_ancho)
if ("grid_colors" not in st.session_state) or \
   ("grid_shape" not in st.session_state) or \
   (st.session_state["grid_shape"] != grid_shape_actual):
    st.session_state["grid_colors"] = [[color for _ in range(piezas_ancho)] for _ in range(piezas_largo)]
    st.session_state["grid_shape"] = grid_shape_actual
    st.session_state.color_base_actual = color
elif ("color_base_actual" in st.session_state and st.session_state.color_base_actual != color) and not st.session_state.get("manual_mode_active", False):
    st.session_state["grid_colors"] = [[color for _ in range(piezas_ancho)] for _ in range(piezas_largo)]
    st.session_state.color_base_actual = color

# --- Standard Designs and Manual Editing Section ---
st.sidebar.header("4. Diseños y Edición Manual")

def aplicar_ajedrez(grid, nrows, ncols, c_impar, c_par):
    for r in range(nrows):
        for c in range(ncols):
            grid[r][c] = c_impar if ((r + c) % 2 == 0) else c_par

def rellenar_base(grid, nrows, ncols, c_base):
    for r in range(nrows):
        for c in range(ncols):
            grid[r][c] = c_base

def trazar_marco_interno(grid, nrows, ncols, c_marco):
    if nrows < 3 or ncols < 3: return False
    for i in range(1, nrows - 1):
        grid[i][1] = c_marco
        grid[i][ncols - 2] = c_marco
    for j in range(1, ncols - 1):
        grid[1][j] = c_marco
        grid[nrows - 2][j] = c_marco
    return True

def trazar_marco_externo(grid, nrows, ncols, c_marco):
    for i in range(nrows):
        grid[i][0] = c_marco
        grid[i][ncols - 1] = c_marco
    for j in range(ncols):
        grid[0][j] = c_marco
        grid[nrows - 1][j] = c_marco

preset_enabled = st.sidebar.checkbox("Usar diseño estándar", value=False)
if preset_enabled:
    st.session_state.manual_mode_active = True
    preset_name = st.sidebar.selectbox(
        "Diseño", 
        ["Ajedrez", "Ajedrez + marco interno", "Marco con base uniforme", "Marco doble con base uniforme", "Marco doble con ajedrez interno"]
    )

    if preset_name == "Ajedrez":
        color_impar = st.sidebar.selectbox("Color (posiciones IMPARES)", PALETA, index=PALETA.index(color))
        default_par = [c for c in PALETA if c != color_impar][0]
        color_par = st.sidebar.selectbox("Color (posiciones PARES)", PALETA, index=PALETA.index(default_par))
        if st.sidebar.button("Aplicar Ajedrez"):
            aplicar_ajedrez(st.session_state["grid_colors"], piezas_largo, piezas_ancho, color_impar, color_par)
            st.sidebar.success("Diseño 'Ajedrez' aplicado.")

    elif "Ajedrez + marco interno" in preset_name:
        color_impar = st.sidebar.selectbox("Color (IMPARES)", PALETA, index=PALETA.index(color), key='p_aj_impar')
        default_par = [c for c in PALETA if c != color_impar][0]
        color_par = st.sidebar.selectbox("Color (PARES)", PALETA, index=PALETA.index(default_par), key='p_aj_par')
        default_marco = [c for c in PALETA if c not in (color_impar, color_par)]; default_marco = default_marco[0] if default_marco else color_impar
        color_marco = st.sidebar.selectbox("Color del marco interno", PALETA, index=PALETA.index(default_marco), key='p_aj_marco')
        if st.sidebar.button("Aplicar Ajedrez + Marco"):
            aplicar_ajedrez(st.session_state["grid_colors"], piezas_largo, piezas_ancho, color_impar, color_par)
            ok = trazar_marco_interno(st.session_state["grid_colors"], piezas_largo, piezas_ancho, color_marco)
            if ok: st.sidebar.success("Diseño aplicado.")
            else: st.sidebar.warning("Grilla muy pequeña (n,m ≥ 3).")

    elif "Marco con base uniforme" in preset_name:
        color_base = st.sidebar.selectbox("Color de base", PALETA, index=PALETA.index(color), key='p_mb_base')
        default_marco = [c for c in PALETA if c != color_base][0]
        color_marco = st.sidebar.selectbox("Color del marco", PALETA, index=PALETA.index(default_marco), key='p_mb_marco')
        if st.sidebar.button("Aplicar Marco Simple"):
            rellenar_base(st.session_state["grid_colors"], piezas_largo, piezas_ancho, color_base)
            ok = trazar_marco_interno(st.session_state["grid_colors"], piezas_largo, piezas_ancho, color_marco)
            if ok: st.sidebar.success("Diseño aplicado.")
            else: st.sidebar.warning("Grilla muy pequeña (n,m ≥ 3).")

    elif "Marco doble con base uniforme" in preset_name:
        color_base = st.sidebar.selectbox("Color de base", PALETA, index=PALETA.index(color), key='p_md_base')
        default_ext = [c for c in PALETA if c != color_base][0]
        color_marco_ext = st.sidebar.selectbox("Marco EXTERIOR", PALETA, index=PALETA.index(default_ext), key='p_md_ext')
        default_int = [c for c in PALETA if c not in (color_base, color_marco_ext)]; default_int = default_int[0] if default_int else color_marco_ext
        color_marco_int = st.sidebar.selectbox("Marco INTERIOR", PALETA, index=PALETA.index(default_int), key='p_md_int')
        if st.sidebar.button("Aplicar Marco Doble"):
            rellenar_base(st.session_state["grid_colors"], piezas_largo, piezas_ancho, color_base)
            trazar_marco_externo(st.session_state["grid_colors"], piezas_largo, piezas_ancho, color_marco_ext)
            ok = trazar_marco_interno(st.session_state["grid_colors"], piezas_largo, piezas_ancho, color_marco_int)
            if ok: st.sidebar.success("Diseño aplicado.")
            else: st.sidebar.warning("Grilla muy pequeña (n,m ≥ 3).")

    elif "Marco doble con ajedrez interno" in preset_name:
        st.sidebar.markdown("##### Colores del Ajedrez")
        color_aj_impar = st.sidebar.selectbox("Ajedrez (IMPAR)", PALETA, index=PALETA.index(color), key='p_mdaj_impar')
        default_aj_par = [c for c in PALETA if c != color_aj_impar][0]
        color_aj_par = st.sidebar.selectbox("Ajedrez (PAR)", PALETA, index=PALETA.index(default_aj_par), key='p_mdaj_par')
        
        st.sidebar.markdown("##### Colores de los Marcos")
        default_ext = [c for c in PALETA if c not in (color_aj_impar, color_aj_par)]; default_ext = default_ext[0] if default_ext else color_aj_impar
        color_marco_ext = st.sidebar.selectbox("Marco EXTERIOR", PALETA, index=PALETA.index(default_ext), key='p_mdaj_ext')
        
        default_int = [c for c in PALETA if c not in (color_aj_impar, color_aj_par, color_marco_ext)]; default_int = default_int[0] if default_int else color_marco_ext
        color_marco_int = st.sidebar.selectbox("Marco INTERIOR", PALETA, index=PALETA.index(default_int), key='p_mdaj_int')

        if st.sidebar.button("Aplicar Marco Doble + Ajedrez"):
            aplicar_ajedrez(st.session_state["grid_colors"], piezas_largo, piezas_ancho, color_aj_impar, color_aj_par)
            trazar_marco_externo(st.session_state["grid_colors"], piezas_largo, piezas_ancho, color_marco_ext)
            ok = trazar_marco_interno(st.session_state["grid_colors"], piezas_largo, piezas_ancho, color_marco_int)
            if ok: st.sidebar.success("Diseño aplicado.")
            else: st.sidebar.warning("Grilla muy pequeña (mínimo 3x3).")

manual_mode = st.sidebar.checkbox("Activar edición manual", value=False)
if manual_mode:
    st.session_state.manual_mode_active = True
    st.sidebar.markdown("##### Pintar celdas individuales")
    fila_sel = st.sidebar.number_input("Fila (1=arriba)", 1, piezas_largo, 1, key="fila_sel")
    col_sel = st.sidebar.number_input("Columna (1=izq)", 1, piezas_ancho, 1, key="col_sel")
    color_celda = st.sidebar.selectbox("Color de celda", PALETA, index=PALETA.index(color), key="color_celda")
    if st.sidebar.button("Pintar celda"):
        st.session_state["grid_colors"][fila_sel - 1][col_sel - 1] = color_celda

    with st.sidebar.expander("Pintar área / Resetear"):
        if st.button("🔄 Resetear al color principal"):
            st.session_state["grid_colors"] = [[color for _ in range(piezas_ancho)] for _ in range(piezas_largo)]

# --- Design Result and Quotation ---
st.subheader("📐 Resultado del Diseño")
st.write(f"**Dimensión final cubierta:** {dim_final_ancho:.2f} m × {dim_final_largo:.2f} m")

total_baldosas = piezas_ancho_despachar * piezas_largo_despachar
precio_por_baldosa = precio_m2 * (TAMANO_BALDOSA_M ** 2)
costo_total = total_baldosas * precio_por_baldosa

st.write(f"**Baldosas a despachar:** {total_baldosas} ({piezas_ancho_despachar} x {piezas_largo_despachar})")

st.subheader("💰 Cotización Estimada")
st.success(f"**Total Estimado:** ${costo_total:,.2f}")

# --- Photorealistic Preview with Pillow ---
st.subheader("🖼️ Vista Previa del Diseño Fotorrealista")

@st.cache_data
def load_images(color_palette):
    """Load all necessary PNGs into a cached dictionary to avoid reloading."""
    images = {}
    try:
        for color_name in color_palette:
            # Carga solo baldosas, ya no hay bordes ni esquineros
            images[color_name] = {
                "baldosa": Image.open(os.path.join("imagenes", color_name, "baldosa.png")).convert("RGBA")
            }
        images["marca_de_agua"] = Image.open(os.path.join("imagenes", "marca_de_agua", "logo_marca.png")).convert("RGBA")
        return images
    except FileNotFoundError as e:
        st.error(f"Error al cargar imágenes: No se encontró el archivo {e.filename}. Asegúrate de que la estructura de carpetas es correcta.")
        return None

def draw_dashed_line(draw, start_pos, end_pos, color="red", width=5, dash_length=15):
    """Dibuja una línea discontinua en el objeto Draw de Pillow."""
    dx = end_pos[0] - start_pos[0]
    dy = end_pos[1] - start_pos[1]
    distance = math.sqrt(dx**2 + dy**2)
    
    if distance == 0: return
    
    dash_count = int(distance / dash_length)
    
    for i in range(0, dash_count, 2):
        start_dash_x = start_pos[0] + (dx * i * dash_length / distance)
        start_dash_y = start_pos[1] + (dy * i * dash_length / distance)
        
        end_dash_x = start_pos[0] + (dx * (i + 1) * dash_length / distance)
        end_dash_y = start_pos[1] + (dy * (i + 1) * dash_length / distance)
        
        draw.line([(start_dash_x, start_dash_y), (end_dash_x, end_dash_y)], fill=color, width=width)

loaded_images = load_images(PALETA)

if loaded_images:
    tile_w, tile_h = loaded_images[color]["baldosa"].size
    
    grid_w_px = piezas_ancho * tile_w
    grid_h_px = piezas_largo * tile_h
    
    # Ya no hay extras por bordes
    img_w = grid_w_px
    img_h = grid_h_px

    canvas = Image.new("RGBA", (img_w, img_h), (255, 255, 255, 255))

    for r in range(piezas_largo):
        for c in range(piezas_ancho):
            tile_color_name = st.session_state["grid_colors"][r][c]
            tile_img = loaded_images[tile_color_name]["baldosa"]
            pos_x = c * tile_w
            pos_y = r * tile_h
            canvas.paste(tile_img, (pos_x, pos_y), tile_img)
    
    # Lógica simplificada de líneas de corte
    draw = ImageDraw.Draw(canvas)

    if acabado_derecho == "Completar con Pieza Cortada":
        cut_x = (piezas_ancho - 1) * tile_w + (tile_w / 2)
        draw_dashed_line(draw, (cut_x, 0), (cut_x, img_h))
    
    if acabado_izquierdo == "Completar con Pieza Cortada":
        cut_x = tile_w / 2
        draw_dashed_line(draw, (cut_x, 0), (cut_x, img_h))

    if acabado_abajo == "Completar con Pieza Cortada":
        cut_y = (piezas_largo - 1) * tile_h + (tile_h / 2)
        draw_dashed_line(draw, (0, cut_y), (img_w, cut_y))

    if acabado_arriba == "Completar con Pieza Cortada":
        cut_y = tile_h / 2
        draw_dashed_line(draw, (0, cut_y), (img_w, cut_y))

    # Lógica para marca de agua
    watermark = loaded_images["marca_de_agua"]
    wm_w, wm_h = watermark.size
    scale_factor = 0.8
    new_wm_w = int(img_w * scale_factor)
    new_wm_h = int(new_wm_w * (wm_h / wm_w)) 
    resized_wm = watermark.resize((new_wm_w, new_wm_h), Image.Resampling.LANCZOS)
    pos_wm_x = (img_w - new_wm_w) // 2
    pos_wm_y = (img_h - new_wm_h) // 2
    canvas.paste(resized_wm, (pos_wm_x, pos_wm_y), resized_wm)
    
    # Lógica para mostrar imagen
    MAX_DISPLAY_WIDTH = 800
    if canvas.width > MAX_DISPLAY_WIDTH:
        aspect_ratio = canvas.height / canvas.width
        new_height = int(MAX_DISPLAY_WIDTH * aspect_ratio)
        display_image = canvas.resize((MAX_DISPLAY_WIDTH, new_height), Image.Resampling.LANCZOS)
        caption_text = "Diseño fotorrealista (vista previa redimensionada)."
    else:
        display_image = canvas
        caption_text = "Diseño fotorrealista generado con marca de agua."

    st.image(display_image, caption=caption_text)
    
# --- Dispatch Breakdown and Export Section ---
st.markdown("---")
st.subheader("📋 Exportar Cotización y Desglose")

tile_counts = {}
for row in st.session_state["grid_colors"]:
    for c in row:
        tile_counts[c] = tile_counts.get(c, 0) + 1

desglose_baldosas_texto = ""
for c, cant in tile_counts.items():
    desglose_baldosas_texto += f"- Baldosas color {c}: {cant} unidades\n"

now = datetime.now()
fecha_cotizacion = now.strftime("%Y-%m-%d %H:%M:%S")

texto_cotizacion = f"""
========================================
COTIZACIÓN - PISO VERSÁTIL
========================================
Empresa: Plastileben
Fecha: {fecha_cotizacion}
----------------------------------------
RESUMEN DEL DISEÑO
----------------------------------------
- Dimensiones finales cubiertas: {dim_final_ancho:.2f} m x {dim_final_largo:.2f} m
- Área total aproximada: {(dim_final_ancho * dim_final_largo):.2f} m²
----------------------------------------
DESGLOSE DE MATERIALES A DESPACHAR
----------------------------------------
{desglose_baldosas_texto}
----------------------------------------
DESGLOSE DE COSTOS
----------------------------------------
- Costo de Baldosas: ${costo_total:,.2f}
----------------------------------------
TOTAL ESTIMADO: ${costo_total:,.2f}
========================================
"""

st.text_area(
    "Copia el siguiente texto para enviar la cotización:",
    texto_cotizacion,
    height=400,
    help="Haz clic en el cuadro, presiona Ctrl+A (o Cmd+A en Mac) para seleccionar todo, y luego Ctrl+C (o Cmd+C) para copiar."
)

st.subheader("Desglose de Baldosas por Color")
if tile_counts:
    st.table({"Color": list(tile_counts.keys()), "Cantidad": list(tile_counts.values())})
st.caption(f"Total baldosas: {total_baldosas}")