import streamlit as st
from moviepy.video.io.VideoFileClip import VideoFileClip
import os

# Streamlit 설정 (업로드 최대 용량 500MB)
st.set_option("server.maxUploadSize", 500)

st.title("🎬 Video Processing App")
st.write("비디오 파일을 업로드하고 변환할 수 있습니다.")

uploaded_file = st.file_uploader("비디오 파일을 업로드하세요 (최대 500MB)", type=["mp4", "avi", "mov"])

if uploaded_file is not None:
    temp_video_path = f"temp_{uploaded_file.name}"
    with open(temp_video_path, "wb") as f:
        f.write(uploaded_file.read())

    # 비디오 정보 확인
    clip = VideoFileClip(temp_video_path)
    st.video(temp_video_path)
    st.write(f"📌 비디오 길이: {clip.duration:.2f} 초")
    st.write(f"📌 비디오 크기: {clip.size} (width x height)")

    # FPS 변경 기능
    new_fps = st.slider("변환할 FPS 선택", min_value=5, max_value=60, value=30)

    if st.button("비디오 변환 시작"):
        output_video_path = f"converted_{uploaded_file.name}"
        clip.set_fps(new_fps).write_videofile(output_video_path, codec="libx264")

        st.success("🎉 변환 완료!")
        with open(output_video_path, "rb") as f:
            st.download_button(
                label="📥 변환된 비디오 다운로드",
                data=f,
                file_name=output_video_path,
                mime="video/mp4"
            )

        os.remove(temp_video_path)
        os.remove(output_video_path)
