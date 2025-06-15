import matplotlib.font_manager as font_manager
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


def generate_graphs():
    # ===============================
    # GRÁFICO DE EMOÇÕES AO LONGO DO TEMPO (com confiança)
    # ===============================

    # Carregar os dados
    df = pd.read_csv("data/emotion_analysis.csv")

    # Mapear e traduzir emoções
    mapeamento = {
        "angry": "Raiva",
        "sad": "Tristeza",
        "happy": "Alegria",
        "surprised": "Surpresa",
        "neutral": "Neutro",
    }
    df["emotion"] = df["emotion"].map(mapeamento)

    # Filtrar emoções de interesse
    df = df[df["emotion"].isin(["Raiva", "Tristeza", "Alegria", "Surpresa"])]

    # Arredondar tempo para agrupar (ex: a cada 0.5s)
    df["time_bin"] = (df["time"] // 0.5) * 0.5  # bin de 0.5 segundos

    # Calcular média da confiança por emoção e tempo
    emotion_time = df.groupby(["time_bin", "emotion"])["confidence"].mean().unstack(fill_value=0)

    # Normalizar para o intervalo de 0 a 1.5
    emotion_time = emotion_time / 100 * 1.5  # pois confidence vai de 0 a 100

    # Paleta de cores suave
    emotion_palette = {
        "Raiva": "#8B0000",
        "Tristeza": "#FFAE00",
        "Alegria": "#228B22",
        "Surpresa": "#1E90FF",
        "Neutra": "#7A7A7A",
    }

    # Plotagem
    plt.figure(figsize=(12, 6))
    for emotion in emotion_palette:
        if emotion in emotion_time.columns:
            y = emotion_time[emotion].rolling(window=4, center=True).mean()  # suavização
            plt.plot(emotion_time.index, y, label=emotion, color=emotion_palette[emotion], linewidth=2.5)

    # Estilo visual
    plt.style.use("default")
    plt.grid(True, linestyle="--", linewidth=0.5, alpha=0.3)
    plt.gca().set_facecolor("#FAFAFA")  # fundo off-white

    # Título e eixos
    plt.title("Emotions X Time", fontsize=20, weight="bold", family="sans-serif")
    plt.xlabel("Time (s)", fontsize=12)
    plt.ylabel("Normalized Intensity", fontsize=12)
    plt.xticks(np.arange(0, df["time"].max() + 1, step=2))
    plt.yticks(np.linspace(0, 1.5, 6))
    plt.ylim(0, 1.5)

    # Legenda abaixo do gráfico
    plt.legend(
        title="",
        loc="upper center",
        bbox_to_anchor=(0.5, -0.15),
        fancybox=True,
        shadow=False,
        ncol=4,
        frameon=False,
    )

    # Layout final
    plt.tight_layout()
    plt.savefig("out/emotion_plot.png", dpi=300, bbox_inches="tight")
    plt.close()

    # ################################################### #
    # Heatmap (simples) com contagem de direções do olhar #
    # ################################################### #
    df_gaze = pd.read_csv("data/gaze_data.csv")
    counts = (
        df_gaze["direction"]
        .value_counts()
        .reindex(
            [
                "left",
                "center",
                "right",
                "blinking",
                "unknown",
            ],
            fill_value=0,
        )
    )

    plt.figure(figsize=(6, 4))
    sns.heatmap(
        counts.values.reshape(1, -1),
        annot=True,
        xticklabels=counts.index,
        yticklabels=["Gaze"],
        cmap="YlOrRd",
        fmt="d",
    )
    plt.title("Heatmap Gaze Tracking")
    plt.savefig("out/heatmap.png")
    plt.close()
