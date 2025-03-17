import streamlit as st
import gdown
from moviepy.video.io.VideoFileClip import VideoFileClip
import os

st.title("🎬 Google Drive Video Converter")
st.write("Google Drive에서 비디오 파일을 가져와 변환할 수 있습니다.")

# Google Drive 파일 ID 입력 받기
drive_file_id = st.text_input("📥 Google Drive 파일 ID를 입력하세요 (예: 1A2B3C4D5E)")

# Google Drive 파일 다운로드
def download_from_drive(file_id):
    url = f"https://drive.google.com/uc?id={file_id}"
    output_path = "downloaded_video.mp4"
    gdown.download(url, output_path, quiet=False)
    return output_path

if drive_file_id:
    if st.button("📥 Google Drive에서 비디오 가져오기"):
        with st.spinner("파일 다운로드 중..."):
            video_path = download_from_drive(drive_file_id)
            st.success("✅ 다운로드 완료!")
            st.video(video_path)

        # 비디오 정보 확인
        clip = VideoFileClip(video_path)
        st.write(f"📌 비디오 길이: {clip.duration:.2f} 초")
        st.write(f"📌 비디오 크기: {clip.size} (width x height)")

        # FPS 변경 기능
        new_fps = st.slider("변환할 FPS 선택", min_value=5, max_value=60, value=30)

        if st.button("🎬 비디오 변환 시작"):
            output_video_path = "converted_video.mp4"
            clip.set_fps(new_fps).write_videofile(output_video_path, codec="libx264")

            st.success("🎉 변환 완료!")
            with open(output_video_path, "rb") as f:
                st.download_button(
                    label="📥 변환된 비디오 다운로드",
                    data=f,
                    file_name="converted_video.mp4",
                    mime="video/mp4"
                )

            # 임시 파일 삭제
            os.remove(video_path)
            os.remove(output_video_path)
