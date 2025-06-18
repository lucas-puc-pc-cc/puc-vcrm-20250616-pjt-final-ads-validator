import os
from moviepy.editor import VideoFileClip, vfx


def clear_terminal():
    os.system("cls" if os.name == "nt" else "clear")


def adjust_cam_video_speed(video_errado_path, video_referencia_path, saida_path):
    """
    Corrige a duração de um vídeo (video_errado_path) para que iguale a duração do vídeo de referência.

    Parâmetros:
        video_errado_path (str): Caminho do vídeo com duração incorreta.
        video_referencia_path (str): Caminho do vídeo com a duração correta.
        saida_path (str): Caminho para salvar o vídeo corrigido.
    """
    # Carrega os vídeos
    video_errado = VideoFileClip(video_errado_path)
    video_referencia = VideoFileClip(video_referencia_path)

    # Durações
    duracao_errada = video_errado.duration
    duracao_correta = video_referencia.duration

    if duracao_errada <= 0 or duracao_correta <= 0:
        raise ValueError("Duração inválida em um dos vídeos.")

    # Calcula fator de ajuste de velocidade
    fator_velocidade = duracao_errada / duracao_correta

    print(f"Ajustando velocidade por fator: {fator_velocidade:.4f}")

    # Aplica ajuste de velocidade
    video_corrigido = video_errado.fx(vfx.speedx, factor=fator_velocidade)

    # Salva vídeo corrigido
    video_corrigido.write_videofile(saida_path, codec="libx264", audio_codec="aac")

    # Libera os vídeos
    video_errado.close()
    video_referencia.close()
    video_corrigido.close()
