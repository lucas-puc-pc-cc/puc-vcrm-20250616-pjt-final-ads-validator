import base64
import os
import subprocess
import streamlit as st
import cv2
import tempfile
import time
from components import *
from streamlit_webrtc import webrtc_streamer
import time


def del_files(dir):
    for file in os.listdir(dir):
        file_path = os.path.join(dir, file)
        if os.path.isfile(file_path):
            os.remove(file_path)


OUT_DIR_PATH = "out"
CAM_VIDEO_PATH = f"{OUT_DIR_PATH}/webcam_output.mp4"
CAM_VIDEO_FIXED_PATH = f"{OUT_DIR_PATH}/webcam_output_fixed.mp4"
PDF_PATH = "AVBER-Report.pdf"  # caminho relativo ao arquivo PDF

st.set_page_config(layout="wide")
st.markdown(
    """
    <div style="text-align: center;">
        <img 
            src="https://raw.githubusercontent.com/lucaslealll/puc-vcrm-20250616-pjt-final-ads-validator/main/assets/avber.png"
        width="200">
        <h1 style="margin-top: 10px;">
            AVBER - Ads Validation by Emotion Recognition
        </h1>
    </div>
    """,
    unsafe_allow_html=True,
)

# Initialize session states
if "TMP_VIDEO_PATH" not in st.session_state:
    st.session_state["TMP_VIDEO_PATH"] = None
if "RUNNING_ANALYSIS" not in st.session_state:
    st.session_state["RUNNING_ANALYSIS"] = False
if "STOP_ANALYSIS" not in st.session_state:
    st.session_state["STOP_ANALYSIS"] = False
if "CONCLUDED_ANALYSIS" not in st.session_state:
    st.session_state["CONCLUDED_ANALYSIS"] = False
if "CANCELED_ANALYSIS" not in st.session_state:
    st.session_state["CANCELED_ANALYSIS"] = False
if "LIVE_EMOTION_ON" not in st.session_state:
    st.session_state["LIVE_EMOTION_ON"] = False
if "GENERATE_REPORT" not in st.session_state:
    st.session_state["GENERATE_REPORT"] = False

# ====== LIVE EMOTION TEST ======= #
if not st.session_state["LIVE_EMOTION_ON"]:
    if st.button("🗭 Live Emotion Map", type="primary"):
        st.session_state["LIVE_EMOTION_ON"] = True
        st.rerun()  # rerun to show webrtc_streamer
else:
    # Start the stream
    st.markdown("🗭 Live Emotion Test...")
    webrtc_streamer(
        key="emotion-detector",
        video_frame_callback=live_emotion_map,
        media_stream_constraints={
            "video": {"width": {"ideal": 1280}, "height": {"ideal": 720}, "frameRate": {"ideal": 60}},
            "audio": False,
        },
    )

    # Show the "Stop" button
    if st.button("ⓧ End Test", type="tertiary"):
        st.session_state["LIVE_EMOTION_ON"] = False
        st.rerun()  # rerun to return to the initial button

# ====== LIVE GAZE TEST ======= #
if not st.session_state.get("LIVE_GAZE_ON", False):
    if st.button("👁 Live Gaze Map", type="primary"):
        st.session_state["LIVE_GAZE_ON"] = True
        st.rerun()  # rerun to show webrtc_streamer
else:
    st.markdown("👁 Live Gaze Tracking...")

    webrtc_streamer(
        key="gaze-tracker",
        video_frame_callback=live_gaze_map,
        media_stream_constraints={
            "video": {"width": {"ideal": 1280}, "height": {"ideal": 720}, "frameRate": {"ideal": 60}},
            "audio": False,
        },
    )

    # Button to end the gaze tracking
    if st.button("ⓧ End Gaze Tracking", type="tertiary"):
        st.session_state["LIVE_GAZE_ON"] = False
        st.rerun()


# Video upload
video_file = st.file_uploader("Choose the ad video to be evaluated.", type=["mp4"])
if video_file:
    AD_VIDEO_PATH = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
    st.session_state["TMP_VIDEO_PATH"] = AD_VIDEO_PATH

    with open(AD_VIDEO_PATH, "wb") as f:
        f.write(video_file.read())

    st.markdown(f"🗹 Video uploaded")


# If video is uploaded
if st.session_state["TMP_VIDEO_PATH"]:
    col_video, col_info = st.columns([2, 1])  # YouTube style layout

    with col_info:
        # Control buttons
        if not st.session_state["RUNNING_ANALYSIS"] and not st.session_state["CONCLUDED_ANALYSIS"]:
            if st.button("Start Analysis", icon=":material/play_circle:"):
                st.session_state["RUNNING_ANALYSIS"] = True
                st.session_state["STOP_ANALYSIS"] = False
                st.session_state["CANCELED_ANALYSIS"] = False
                st.rerun()

        elif st.session_state["RUNNING_ANALYSIS"]:
            if st.button("Cancel Analysis", icon=":material/stop_circle:", type="primary"):
                st.session_state["CANCELED_ANALYSIS"] = True
                st.session_state["RUNNING_ANALYSIS"] = False
                st.rerun()

        # Space for status and progress
        status_placeholder = st.empty()
        progress_bar = st.progress(0)

    # Video column
    with col_video:
        if st.session_state["RUNNING_ANALYSIS"]:
            st.video(st.session_state["TMP_VIDEO_PATH"], autoplay=True)

    # Logic for analysis synchronized with video
    if (
        st.session_state["RUNNING_ANALYSIS"]
        and not st.session_state["CANCELED_ANALYSIS"]
        and not st.session_state["CONCLUDED_ANALYSIS"]
    ):
        del_files("data")
        del_files("out")
        cap_video = cv2.VideoCapture(st.session_state["TMP_VIDEO_PATH"])
        cap_webcam = cv2.VideoCapture(0)
        out = cv2.VideoWriter(CAM_VIDEO_PATH, cv2.VideoWriter_fourcc(*"mp4v"), 20.0, (640, 480))

        total_frames = int(cap_video.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap_video.get(cv2.CAP_PROP_FPS)
        frame_duration = 1.0 / fps if fps > 0 else 1.0 / 25  # default fallback

        current_frame = 0
        prev_time = time.time()

        while cap_video.isOpened():
            if st.session_state["CANCELED_ANALYSIS"]:
                status_placeholder.markdown("🗷 Analysis canceled by the user.")
                break

            ret_vid, frame_vid = cap_video.read()
            ret_cam, frame_cam = cap_webcam.read()

            if not ret_vid or not ret_cam:
                break

            out.write(frame_cam)
            current_frame += 1

            # Update progress and status
            progress = current_frame / total_frames
            progress_bar.progress(progress)
            status_placeholder.markdown(f"● Capturing reactions... {int(progress * 100)}%")

            # Wait the correct time for the next frame (synchronized with FPS)
            elapsed = time.time() - prev_time
            sleep_time = frame_duration - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)
            prev_time = time.time()

        with col_info:
            st.markdown(f"🗹 Capturing reactions... 100%")

        # Release resources
        cap_video.release()
        cap_webcam.release()
        out.release()

        if not st.session_state["CANCELED_ANALYSIS"]:

            adjust_cam_video_speed(CAM_VIDEO_PATH, AD_VIDEO_PATH, CAM_VIDEO_FIXED_PATH)

            def update_progress(progress):
                percent = int(progress * 100)
                status_placeholder.markdown(f"🗘 Processing emotions... {percent}%")
                progress_bar.progress(percent)

            process_emotions(CAM_VIDEO_FIXED_PATH, AD_VIDEO_PATH, progress_callback=update_progress)
            with col_info:
                st.markdown(f"🗹 Processing emotions... 100%")

            status_placeholder.markdown("🗘 Processing gaze tracking...")
            track_gaze(CAM_VIDEO_FIXED_PATH)
            with col_info:
                st.markdown("🗹 Processing gaze tracking... 100%")

            status_placeholder.markdown("🗘 Generating graphs...")
            generate_graphs()
            with col_info:
                st.markdown("🗹 Generating graphs... 100%")

            # st.image(f"{OUT_DIR_PATH}/emotion_plot.png", caption="Emotion Chart", use_column_width=True)
            # st.image(f"{OUT_DIR_PATH}/heatmap.png", caption="Gaze Heatmap", use_column_width=True)
            status_placeholder.markdown("🗹 Analysis completed!")

            st.session_state["RUNNING_ANALYSIS"] = False
            st.session_state["CONCLUDED_ANALYSIS"] = True

            subprocess.run(["python", "report.py"], capture_output=True, text=True)

            with col_info:
                st.markdown("🗎 PDF created at local directory!")


if st.session_state["CONCLUDED_ANALYSIS"]:
    st.success("Analysis completed.")
    if st.button("New Analysis", icon=":material/refresh:"):
        st.session_state.update(
            {
                "RUNNING_ANALYSIS": False,
                "STOP_ANALYSIS": False,
                "CONCLUDED_ANALYSIS": False,
                "CANCELED_ANALYSIS": False,
                "TMP_VIDEO_PATH": None,
            }
        )
        st.rerun()

    # Botão para exibir o PDF
    if st.button("Preview Report", icon=":material/picture_as_pdf:"):
        with open("AVBER-Report.pdf", "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode("utf-8")

        pdf_display = f"""
        <iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="1000" type="application/pdf"></iframe>
        """
        st.markdown(pdf_display, unsafe_allow_html=True)
