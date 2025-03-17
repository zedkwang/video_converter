import streamlit as st
import os
import time
import shutil
import tempfile
from pathlib import Path
import threading
import subprocess
from moviepy.editor import VideoFileClip

# 페이지 기본 설정
st.set_page_config(
    page_title="로컬 마운트 동영상 변환기",
    page_icon="🎬",
    layout="wide"
)

# 세션 상태 초기화
if 'files' not in st.session_state:
    st.session_state.files = []
if 'output_files' not in st.session_state:
    st.session_state.output_files = []
if 'logs' not in st.session_state:
    st.session_state.logs = []
if 'converting' not in st.session_state:
    st.session_state.converting = False
if 'progress' not in st.session_state:
    st.session_state.progress = 0
if 'current_file' not in st.session_state:
    st.session_state.current_file = ""
if 'completed_files' not in st.session_state:
    st.session_state.completed_files = 0
if 'total_files' not in st.session_state:
    st.session_state.total_files = 0
if 'drive_path' not in st.session_state:
    st.session_state.drive_path = ""
if 'mounted' not in st.session_state:
    st.session_state.mounted = False

# 임시 디렉토리 설정
TEMP_DIR = tempfile.mkdtemp()
OUTPUT_DIR = os.path.join(TEMP_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def add_log(message):
    """로그 메시지 추가"""
    timestamp = time.strftime('%H:%M:%S')
    st.session_state.logs.append(f"[{timestamp}] {message}")

# 로컬에 마운트된 드라이브 경로 사용
def use_local_mounted_drive(mount_path):
    """로컬에 마운트된 드라이브 경로 사용"""
    if os.path.exists(mount_path) and os.path.isdir(mount_path):
        st.session_state.mounted = True
        st.session_state.drive_path = mount_path
        add_log(f"마운트된 드라이브 경로 설정: {mount_path}")
        return True
    else:
        add_log(f"유효하지 않은 드라이브 마운트 경로: {mount_path}")
        st.error(f"유효하지 않은 마운트 경로입니다: {mount_path}")
        return False

# 파일 정보 추출 함수
def extract_video_info(file_path, file_index):
    """비디오 정보 추출"""
    try:
        # 파일 크기 (MB)
        file_size = os.path.getsize(file_path) / (1024 * 1024)
        
        try:
            # 동영상 정보 추출
            clip = VideoFileClip(file_path, verbose=False, audio=False, has_mask=False)
            duration = clip.duration  # 초 단위
            fps = clip.fps  # 원본 FPS
            width = clip.w  # 너비
            height = clip.h  # 높이
            
            # 시간 포맷팅 (HH:MM:SS)
            hours, remainder = divmod(int(duration), 3600)
            minutes, seconds = divmod(remainder, 60)
            duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
            clip.close()
            
            # 파일 정보 업데이트
            st.session_state.files[file_index].update({
                'duration': duration,
                'duration_str': duration_str,
                'fps': f"{fps:.1f}",
                'width': width,
                'height': height,
                'status': '준비됨'
            })
            
            add_log(f"파일 정보 로드 성공: {os.path.basename(file_path)}")
            
        except Exception as e:
            st.session_state.files[file_index].update({
                'duration': 0,
                'duration_str': "알 수 없음",
                'fps': "?",
                'width': 0,
                'height': 0,
                'status': '정보 추출 실패'
            })
            
            add_log(f"동영상 정보 추출 오류: {os.path.basename(file_path)} - {e}")
    
    except Exception as e:
        add_log(f"파일 정보 처리 오류: {os.path.basename(file_path)} - {e}")
        st.session_state.files[file_index]['status'] = '오류'

# 변환 함수
def convert_video(file_path, fps, resolution):
    """비디오 변환 처리"""
    try:
        # 출력 파일 경로
        input_file = Path(file_path)
        output_filename = f"{input_file.stem}_{resolution}p_{fps}fps.mp4"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        
        # 파일명 중복 확인 및 처리
        counter = 1
        while os.path.exists(output_path):
            output_filename = f"{input_file.stem}_{resolution}p_{fps}fps_{counter}.mp4"
            output_path = os.path.join(OUTPUT_DIR, output_filename)
            counter += 1
        
        # FFmpeg 명령어 구성 (해상도에 따른 최적 설정)
        if resolution == 1080:
            ffmpeg_cmd = [
                "ffmpeg", "-y",
                "-i", file_path,
                "-vf", "scale=1920:-2",
                "-r", str(fps),
                "-c:v", "libx264",
                "-profile:v", "high",
                "-level:v", "4.1",
                "-b:v", "2.5M",
                "-maxrate", "2.75M",
                "-bufsize", "5M",
                "-c:a", "aac",
                "-b:a", "128k",
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                output_path
            ]
        elif resolution == 720:
            ffmpeg_cmd = [
                "ffmpeg", "-y",
                "-i", file_path,
                "-vf", "scale=1280:-2",
                "-r", str(fps),
                "-c:v", "libx264",
                "-profile:v", "high",
                "-level:v", "4.1",
                "-b:v", "1.8M",
                "-maxrate", "2.0M",
                "-bufsize", "3.6M",
                "-c:a", "aac",
                "-b:a", "128k",
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                output_path
            ]
        elif resolution == 480:
            ffmpeg_cmd = [
                "ffmpeg", "-y",
                "-i", file_path,
                "-vf", "scale=854:-2",
                "-r", str(fps),
                "-c:v", "libx264",
                "-profile:v", "high",
                "-level:v", "4.1",
                "-b:v", "1.0M",
                "-maxrate", "1.2M",
                "-bufsize", "2.0M",
                "-c:a", "aac",
                "-b:a", "128k",
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                output_path
            ]
        else:  # 360p 또는 기타 해상도
            ffmpeg_cmd = [
                "ffmpeg", "-y",
                "-i", file_path,
                "-vf", f"scale=-2:{resolution}",
                "-r", str(fps),
                "-c:v", "libx264",
                "-profile:v", "high",
                "-level:v", "4.1",
                "-b:v", "0.5M",
                "-maxrate", "0.6M",
                "-bufsize", "1.0M",
                "-c:a", "aac",
                "-b:a", "128k",
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                output_path
            ]
            
        # FFmpeg 프로세스 실행
        process = subprocess.Popen(
            ffmpeg_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # 프로세스 완료 대기
        stdout, stderr = process.communicate()
        
        # 변환 성공 확인
        if process.returncode == 0 and os.path.exists(output_path):
            # 결과 파일 크기 확인
            converted_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
            original_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
            reduction = (1 - converted_size / original_size) * 100  # 감소율 %
            
            add_log(f"변환 결과: {original_size:.1f} MB → {converted_size:.1f} MB ({reduction:.1f}% 감소)")
            
            return {
                'original_path': file_path,
                'original_name': os.path.basename(file_path),
                'output_path': output_path,
                'output_name': output_filename,
                'size': f"{converted_size:.1f} MB",
                'reduction': f"{reduction:.1f}%",
                'created_at': time.time()
            }
        else:
            add_log(f"FFmpeg 변환 오류: {stderr}")
            return None
            
    except Exception as e:
        add_log(f"변환 처리 오류: {e}")
        return None

# 변환 작업 관리 함수
def process_conversion():
    """선택한 모든 파일 변환 처리"""
    fps = st.session_state.fps
    resolution = st.session_state.resolution
    
    total_files = len(st.session_state.files)
    st.session_state.total_files = total_files
    st.session_state.completed_files = 0
    
    add_log(f"변환 시작: 총 {total_files}개 파일, 해상도={resolution}p, 프레임={fps}fps")
    
    for i, file_info in enumerate(st.session_state.files):
        if not st.session_state.converting:  # 변환 중지 확인
            break
            
        file_path = file_info['path']
        st.session_state.current_file = file_info['name']
        
        # 진행 상황 업데이트
        progress_percent = (i / total_files) * 100
        st.session_state.progress = progress_percent
        
        add_log(f"파일 변환 시작: {file_info['name']}")
        
        # 파일 변환
        result = convert_video(file_path, fps, resolution)
        
        if result:
            st.session_state.output_files.append(result)
            st.session_state.completed_files += 1
            add_log(f"파일 변환 완료: {file_info['name']} -> {result['output_name']}")
        else:
            add_log(f"파일 변환 실패: {file_info['name']}")
    
    # 변환 완료
    st.session_state.converting = False
    st.session_state.progress = 100 if st.session_state.completed_files > 0 else 0
    st.session_state.current_file = ""
    
    add_log(f"모든 파일 변환 완료: {st.session_state.completed_files}/{total_files} 파일 성공")

# 변환 시작 함수
def start_conversion():
    """변환 작업 시작"""
    if not st.session_state.files:
        st.warning("변환할 파일을 먼저 선택해주세요.")
        return
        
    if st.session_state.converting:
        st.warning("이미 변환 중입니다.")
        return
        
    # 변환 상태 초기화
    st.session_state.converting = True
    st.session_state.progress = 0
    st.session_state.current_file = ""
    
    # 별도 스레드에서 변환 실행
    threading.Thread(target=process_conversion, daemon=True).start()

# 변환 중지 함수
def stop_conversion():
    """변환 작업 중지"""
    st.session_state.converting = False
    add_log("사용자 요청으로 변환이 중지되었습니다.")

# 파일 목록 업데이트 함수
def update_file_list():
    """마운트된 드라이브에서 비디오 파일 목록 가져오기"""
    if not st.session_state.mounted:
        st.warning("드라이브가 연결되지 않았습니다.")
        return
    
    # 마운트된 드라이브 폴더 경로에서 동영상 파일 찾기
    try:
        drive_path = st.session_state.drive_path
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv']
        
        # 이전 파일 목록 초기화
        st.session_state.files = []
        
        add_log(f"폴더 스캔 중: {drive_path}")
        
        # 파일 목록 가져오기
        for root, dirs, files in os.walk(drive_path):
            for file in files:
                if any(file.lower().endswith(ext) for ext in video_extensions):
                    file_path = os.path.join(root, file)
                    
                    # 파일 정보 추가
                    file_info = {
                        'name': file,
                        'path': file_path,
                        'size': f"{os.path.getsize(file_path) / (1024 * 1024):.1f} MB",
                        'status': '정보 로드 중'
                    }
                    
                    st.session_state.files.append(file_info)
                    add_log(f"파일 발견: {file}")
        
        # 파일 정보 추출 (별도 스레드)
        for i, file_info in enumerate(st.session_state.files):
            threading.Thread(
                target=extract_video_info,
                args=(file_info['path'], i),
                daemon=True
            ).start()
        
        add_log(f"총 {len(st.session_state.files)}개 비디오 파일 발견")
        
    except Exception as e:
        add_log(f"파일 목록 조회 오류: {str(e)}")
        st.error(f"파일 목록 조회 오류: {str(e)}")

# UI 렌더링
st.title("로컬 마운트 동영상 변환기 🎬")

# 사이드바 - 드라이브 연결 및 설정
with st.sidebar:
    st.header("연결 및 설정")
    
    # 마운트 경로 입력
    drive_path = st.text_input("마운트된 드라이브 경로", 
                              value="/Volumes/GoogleDrive/내 드라이브" if not st.session_state.mounted else st.session_state.drive_path,
                              help="로컬에 마운트된 구글 드라이브 경로를 입력하세요")
    
    if st.button("드라이브 연결", disabled=st.session_state.mounted):
        use_local_mounted_drive(drive_path)
    
    if st.session_state.mounted:
        st.success("드라이브 연결됨 ✅")
        
        # 파일 새로고침 버튼
        if st.button("파일 목록 새로고침"):
            update_file_list()
    
    # 변환 설정
    st.header("변환 설정")
    
    # FPS 설정
    fps_options = [24, 30, 60]
    st.session_state.fps = st.selectbox("프레임 레이트 (FPS)", 
                                        options=fps_options, 
                                        index=1)  # 기본값 30fps
    
    # 해상도 설정
    resolution_options = [360, 480, 720, 1080]
    st.session_state.resolution = st.selectbox("해상도", 
                                              options=resolution_options, 
                                              index=2)  # 기본값 720p
    
    # 변환 버튼
    convert_col, stop_col = st.columns(2)
    with convert_col:
        if st.button("변환 시작", disabled=st.session_state.converting or not st.session_state.files):
            start_conversion()
    
    with stop_col:
        if st.button("변환 중지", disabled=not st.session_state.converting):
            stop_conversion()

# 메인 영역 - 파일 목록, 로그, 진행 상황
file_col, log_col = st.columns([3, 2])

# 파일 목록
with file_col:
    st.header("파일 목록")
    
    if not st.session_state.mounted:
        st.info("드라이브를 먼저 연결해주세요.")
    elif not st.session_state.files:
        st.info("드라이브에서 비디오 파일을 찾을 수 없습니다. 파일 목록 새로고침을 클릭하세요.")
    else:
        # 입력 파일 목록
        st.subheader("입력 파일")
        for i, file_info in enumerate(st.session_state.files):
            with st.expander(f"{i+1}. {file_info['name']} ({file_info['size']})"):
                cols = st.columns([1, 1, 1])
                with cols[0]:
                    st.write(f"상태: {file_info.get('status', '대기 중')}")
                with cols[1]:
                    st.write(f"길이: {file_info.get('duration_str', '알 수 없음')}")
                with cols[2]:
                    st.write(f"FPS: {file_info.get('fps', '?')}")
                
                if 'width' in file_info and 'height' in file_info and file_info['width'] > 0:
                    st.write(f"해상도: {file_info['width']}x{file_info['height']}")
        
        # 출력 파일 목록
        if st.session_state.output_files:
            st.subheader("출력 파일")
            for i, output_file in enumerate(st.session_state.output_files):
                with st.expander(f"{i+1}. {output_file['output_name']} ({output_file['size']})"):
                    cols = st.columns([1, 1])
                    with cols[0]:
                        st.write(f"원본: {output_file['original_name']}")
                    with cols[1]:
                        st.write(f"크기 감소: {output_file['reduction']}")
                    
                    if st.button(f"다운로드: {output_file['output_name']}", key=f"download_{i}"):
                        # 파일 다운로드
                        with open(output_file['output_path'], "rb") as file:
                            st.download_button(
                                label=f"다운로드 확인: {output_file['output_name']}",
                                data=file,
                                file_name=output_file['output_name'],
                                mime="video/mp4",
                                key=f"download_confirm_{i}"
                            )

# 로그 및 진행 상황
with log_col:
    st.header("변환 진행 상황")
    
    # 진행 상황 표시
    if st.session_state.converting:
        st.write(f"현재 파일: {st.session_state.current_file}")
    
    progress_text = f"{st.session_state.completed_files}/{st.session_state.total_files} 파일 완료"
    st.progress(st.session_state.progress / 100, text=progress_text)
    
    # 로그 표시
    st.subheader("로그")
    log_container = st.container()
    with log_container:
        logs = st.session_state.logs
        if logs:
            for log in logs[-30:]:  # 최근 30개 로그만 표시
                st.text(log)
        else:
            st.info("로그가 없습니다.")

# 앱 시작 시 자동 실행
if st.session_state.mounted and not st.session_state.files:
    update_file_list()

# 앱 종료 시 임시 파일 정리
def cleanup():
    """임시 파일 정리"""
    try:
        shutil.rmtree(TEMP_DIR)
    except:
        pass

# 메인 함수
if __name__ == "__main__":
    # 앱 실행 시 초기화
    import atexit
    atexit.register(cleanup)
