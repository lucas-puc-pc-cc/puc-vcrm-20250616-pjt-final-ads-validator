from fer import FER
import av
import cv2
import numpy as np
import os
import pandas as pd

DATA_OUT_PATH = "data"
FRAME_OUT_PATH = DATA_OUT_PATH  # "data/frames"


def process_emotions(video_path_cam, video_path_ad, progress_callback=None):
    detector = FER(mtcnn=True)
    cap_face = cv2.VideoCapture(video_path_cam)

    data = []
    frame_num = 0
    total_frames = int(cap_face.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap_face.get(cv2.CAP_PROP_FPS)

    while True:
        ret_face, frame_face = cap_face.read()
        if not ret_face:
            break

        timestamp = frame_num / fps
        result = detector.detect_emotions(frame_face)

        if result:
            emotions = result[0]["emotions"]
            dominant = max(emotions, key=emotions.get)
            confidence = int(emotions[dominant] * 100)
        else:
            dominant = "none"
            confidence = 0

        data.append({"frame": frame_num, "time": timestamp, "emotion": dominant, "confidence": confidence})

        frame_num += 1
        if progress_callback and total_frames > 0:
            progress_callback(frame_num / total_frames)

    cap_face.release()

    # Salvar CSV
    df = pd.DataFrame(data)
    os.makedirs(DATA_OUT_PATH, exist_ok=True)
    csv_path = os.path.join(DATA_OUT_PATH, "emotion_analysis.csv")
    df.to_csv(csv_path, index=False)

    # 2. Etapa de Salvamento de Frames Baseados no CSV (após análise)
    cap_face = cv2.VideoCapture(video_path_cam)
    cap_ad = cv2.VideoCapture(video_path_ad)

    os.makedirs(FRAME_OUT_PATH, exist_ok=True)
    saved_emotions = set()

    for _, row in df.iterrows():
        emotion = row["emotion"]
        if emotion == "none" or emotion in saved_emotions:
            continue  # Só salva a primeira ocorrência de cada emoção válida

        timestamp = row["time"]
        ts_ms = int(timestamp * 1000)
        confidence = row["confidence"]

        # Captura frame da webcam
        cap_face.set(cv2.CAP_PROP_POS_MSEC, ts_ms)
        ret_cam, frame_cam = cap_face.read()

        # Captura frame do vídeo assistido
        cap_ad.set(cv2.CAP_PROP_POS_MSEC, ts_ms)
        ret_ad, frame_ad = cap_ad.read()

        filename_suffix = f"{ts_ms}ms_{emotion}_{confidence}"

        if ret_ad:
            ad_filename = os.path.join(FRAME_OUT_PATH, f"ad_{filename_suffix}.jpg")
            cv2.imwrite(ad_filename, frame_ad)

        # if ret_cam:
        #     webcam_filename = os.path.join(FRAME_OUT_PATH, f"cam_{filename_suffix}.jpg")
        #     cv2.imwrite(webcam_filename, frame_cam)

        if ret_cam:
            faces = detector.detect_emotions(frame_cam)  # seu código para detectar emoções
            for face in faces:
                (x, y, w, h) = face["box"]
                emotions = face["emotions"]

                # Cor amarela personalizada em BGR
                color = (0, 224, 224)

                # Desenha o retângulo ao redor do rosto
                cv2.rectangle(frame_cam, (x, y), (x + w, y + h), color, 2)

                # Prepara as linhas de texto
                lines = [f"{emotion}: {value:.2f}" for emotion, value in emotions.items()]

                # Posição inicial do texto
                text_x = x + w + 5
                text_y = y + 15

                # Escreve cada linha com espessura maior (negrito)
                for i, line in enumerate(lines):
                    y_pos = text_y + i * 20  # aumentei o espaçamento pra caber o negrito
                    cv2.putText(frame_cam, line, (text_x, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2, cv2.LINE_AA)

            # Salva o frame com os desenhos
            webcam_filename = os.path.join(FRAME_OUT_PATH, f"cam_{filename_suffix}.jpg")
            cv2.imwrite(webcam_filename, frame_cam)

        saved_emotions.add(emotion)

    cap_face.release()
    cap_ad.release()


def live_emotion_map(frame: av.VideoFrame) -> av.VideoFrame:
    detector = FER(mtcnn=True)

    img = frame.to_ndarray(format="bgr24")

    results = detector.detect_emotions(img)

    for face in results:
        (x, y, w, h) = face["box"]
        emotions = face["emotions"]
        top_emotion = max(emotions, key=emotions.get)
        score = emotions[top_emotion]

        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
        text = f"{top_emotion} ({score:.2f})"
        cv2.putText(img, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    return av.VideoFrame.from_ndarray(img, format="bgr24")
