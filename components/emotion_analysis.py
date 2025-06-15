from fer import FER
import av
import cv2
import os
import pandas as pd

DATA_OUT_PATH = "data"
FRAME_OUT_PATH = DATA_OUT_PATH  # "data/frames"


def process_emotions(video_path_cam, video_path_ad, progress_callback=None):
    detector = FER(mtcnn=True)
    cap_face = cv2.VideoCapture(video_path_cam)
    cap_source = cv2.VideoCapture(video_path_ad)

    data = []
    frame_num = 0
    total_frames = int(cap_face.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap_face.get(cv2.CAP_PROP_FPS)

    # Pastas para salvar os frames
    os.makedirs(FRAME_OUT_PATH, exist_ok=True)

    # Dicionário para registrar a primeira ocorrência de cada emoção
    first_occurrences = {}

    while True:
        ret_face, frame_face = cap_face.read()
        if not ret_face:
            break

        timestamp = frame_num / fps

        # Lê frame do vídeo assistido no mesmo instante
        cap_source.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
        ret_source, frame_source = cap_source.read()

        result = detector.detect_emotions(frame_face)

        if result:
            emotions = result[0]["emotions"]
            dominant = max(emotions, key=emotions.get)
            confidence = int(emotions[dominant] * 100)
        else:
            dominant = "none"
            confidence = 0

        # Salvar dados do frame
        data.append({
            "frame": frame_num,
            "time": timestamp,
            "emotion": dominant,
            "confidence": confidence
        })

        # Verifica e salva apenas a primeira ocorrência de cada emoção
        if dominant != "none" and dominant not in first_occurrences:
            first_occurrences[dominant] = {
                "timestamp": timestamp,
                "frame_face": frame_face.copy(),
                "frame_source": frame_source.copy() if ret_source else None,
                "confidence": confidence
            }

        frame_num += 1

        if progress_callback is not None and total_frames > 0:
            progress_callback(frame_num / total_frames)

    cap_face.release()
    cap_source.release()

    # Salva CSV com os dados
    df = pd.DataFrame(data)
    os.makedirs(DATA_OUT_PATH, exist_ok=True)
    csv_path = os.path.join(DATA_OUT_PATH, "emotion_analysis.csv")
    df.to_csv(csv_path, index=False)

    # Salva os frames correspondentes à primeira ocorrência de cada emoção
    for emotion, info in first_occurrences.items():
        ts_ms = int(info["timestamp"] * 1000)
        filename_suffix = f"{ts_ms}ms_{emotion}_{info['confidence']}"

        # Frame da webcam
        webcam_filename = os.path.join(FRAME_OUT_PATH, f"cam_{filename_suffix}.jpg")
        cv2.imwrite(webcam_filename, info["frame_face"])

        # Frame do vídeo assistido
        if info["frame_source"] is not None:
            ad_filename = os.path.join(FRAME_OUT_PATH, f"ad_{filename_suffix}.jpg")
            cv2.imwrite(ad_filename, info["frame_source"])



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
