from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import grey, lightgrey
import numpy as np
import os
import re
from datetime import datetime

# --- Configurações ---
IMAGE_DIR = "data"
OUTPUT_DIR = "out"
PDF_PATH = os.path.join(".", "AVBER-Report.pdf")

PAGE_SIZE = letter
PAGE_WIDTH, PAGE_HEIGHT = PAGE_SIZE

# Layout
MARGIN_X = 50
TOP_MARGIN = PAGE_HEIGHT - 60
BOTTOM_MARGIN = 40
IMAGE_WIDTH, IMAGE_HEIGHT = 250, 180
GAP_X, GAP_Y = 30, 15


# --- Funções Auxiliares ---
def extract_times_from_images(directory):
    times = set()
    pattern = re.compile(r"(ad|cam)_(\d+)ms_.*\.(jpg|jpeg|png)", re.IGNORECASE)
    for f in os.listdir(directory):
        match = pattern.match(f)
        if match:
            times.add(int(match.group(2)))
    return sorted(times)

def extract_emotion_from_filename(filename):
    match = re.match(r"cam_\d+ms_([a-zA-Z]+)_\d+\.(jpg|jpeg|png)", filename, re.IGNORECASE)
    if match:
        return match.group(1).capitalize()
    return "Unknown"


def generate_emotion_data(times_ms):
    times_sec = np.array(times_ms) / 1000
    return (
        0.3 + 0.1 * np.sin(times_sec / 3),
        0.5 + 0.05 * np.cos(times_sec / 4),
        0.7 + 0.3 * np.sin(times_sec / 5),
        0.4 + 0.05 * np.cos(times_sec / 6),
    )


def extract_info(filename):
    match = re.match(r"(ad|cam)_(\d+)ms_.*\.(jpg|jpeg|png)", filename, re.IGNORECASE)
    if match:
        return match.group(1).lower(), int(match.group(2))
    return None, None


def group_images_by_timestamp(directory):
    grouped = {}
    for fname in os.listdir(directory):
        if fname.lower().endswith((".jpg", ".jpeg", ".png")):
            tipo, ms = extract_info(fname)
            if tipo and ms is not None:
                grouped.setdefault(ms, {})[tipo] = os.path.join(directory, fname)
    return grouped


def ms_to_min_sec(ms):
    minutes = (ms // 1000) // 60
    seconds = (ms // 1000) % 60
    return f"{minutes}min {seconds}s"


# --- Criação do PDF ---
def create_pdf(pairs, pdf_path, page_size=PAGE_SIZE):
    width, height = page_size
    c = canvas.Canvas(pdf_path, pagesize=page_size)
    page_num = 1

    def draw_header():
        logo_path = "assets/PUCMinas.ico"
        logo_width, logo_height = 45, 45

        if os.path.exists(logo_path):
            c.drawImage(
                logo_path, MARGIN_X, height - logo_height - 20, width=logo_width, height=logo_height, mask="auto"
            )

        # Título centralizado levando em conta o logo
        c.setFont("Times-Bold", 30)
        c.drawCentredString(width / 2, height - 50, "AVBER - Results Report")

        # Linha separadora
        c.setStrokeColor(lightgrey)
        c.setLineWidth(0.5)
        c.line(MARGIN_X, height - 70, width - MARGIN_X, height - 70)

    def draw_footer():
        c.setFont("Times-Roman", 9)
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        c.setFillColor(grey)
        c.drawString(MARGIN_X, 25, f"{now}")
        c.drawRightString(width - MARGIN_X, 25, f"Page {page_num}")
        c.setFillColor("black")

    # --- Inserção dos gráficos principais ---
    graph1 = os.path.join(OUTPUT_DIR, "emotion_plot.png")
    graph2 = os.path.join(OUTPUT_DIR, "heatmap.png")
    has_graphs = os.path.exists(graph1) and os.path.exists(graph2)

    draw_header()

    y_pos = height - 90
    if has_graphs:
        graph_height = 160
        for i, graph in enumerate([graph1, graph2]):
            c.drawImage(
                graph,
                MARGIN_X,
                y_pos - graph_height,
                width=width - 2 * MARGIN_X,
                height=graph_height,
                preserveAspectRatio=True,
            )
            y_pos -= graph_height + 15

        c.setFont("Times-Bold", 14)
        c.drawString(MARGIN_X, y_pos, "AD Frame X Emotion")
        y_pos -= 20

    c.setFont("Times-Roman", 11)

    for ms in sorted(pairs.keys()):
        pair = pairs[ms]
        if y_pos < BOTTOM_MARGIN + IMAGE_HEIGHT + 40:
            draw_footer()
            c.showPage()
            page_num += 1
            y_pos = height - 80
            draw_header()
            c.setFont("Times-Roman", 11)

        img_y = y_pos - IMAGE_HEIGHT

        if "ad" in pair:
            c.drawImage(pair["ad"], MARGIN_X, img_y, width=IMAGE_WIDTH, height=IMAGE_HEIGHT)
            c.drawCentredString(MARGIN_X + IMAGE_WIDTH / 2, img_y - 12, f"AD - {ms_to_min_sec(ms)}")

        if "cam" in pair:
            cam_x = MARGIN_X + IMAGE_WIDTH + GAP_X
            cam_path = pair["cam"]
            emotion = extract_emotion_from_filename(os.path.basename(cam_path))
            c.drawImage(cam_path, cam_x, img_y, width=IMAGE_WIDTH, height=IMAGE_HEIGHT)
            c.drawCentredString(cam_x + IMAGE_WIDTH / 2, img_y - 12, f"Cam - {ms_to_min_sec(ms)} - Emotion: {emotion}")


        y_pos = img_y - 25  # espaço abaixo das imagens

    draw_footer()
    c.save()
    print(f"PDF criado em: {pdf_path}")


# --- Execução Principal ---
if __name__ == "__main__":
    times_ms = extract_times_from_images(IMAGE_DIR)
    raiva, tristeza, alegria, surpresa = generate_emotion_data(times_ms)
    pairs = group_images_by_timestamp(IMAGE_DIR)
    create_pdf(pairs, PDF_PATH)
