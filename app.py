# 통합 서버: 업로드 → AI 피드백 → 필터 추천 → 필터 적용 → 이전 피드백 확인 + 로그기록 초기화
from flask import Flask, request, render_template, redirect, url_for
import os
import requests
import base64
import json
import datetime
from werkzeug.utils import secure_filename
from PIL import Image, ImageFilter, ImageEnhance, ExifTags

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
LOG_FILE = 'log/feedback_log.txt'
HISTORY_FILE = 'log/history.json'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('log', exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

FILTER_MAP = {
    "BLUR": ImageFilter.BLUR,
    "SHARPEN": ImageFilter.SHARPEN,
    "DETAIL": ImageFilter.DETAIL,
    "CONTOUR": ImageFilter.CONTOUR,
    "EDGE_ENHANCE": ImageFilter.EDGE_ENHANCE,
    "SMOOTH": ImageFilter.SMOOTH
}

CURRENT_FILENAME = None
CURRENT_FILTER = None

def fix_image_orientation(image):
    try:
        exif = image._getexif()
        if exif is not None:
            orientation_key = [k for k, v in ExifTags.TAGS.items() if v == "Orientation"]
            if orientation_key:
                orientation = exif.get(orientation_key[0])
                if orientation == 3:
                    image = image.rotate(180, expand=True)
                elif orientation == 6:
                    image = image.rotate(270, expand=True)
                elif orientation == 8:
                    image = image.rotate(90, expand=True)
    except Exception:
        pass
    return image

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/evaluate', methods=['POST'])
def evaluate():
    global CURRENT_FILENAME, CURRENT_FILTER
    file = request.files['image']
    if not file:
        return redirect(url_for('index'))

    filename = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_") + secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    CURRENT_FILENAME = filename

    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            previous_feedback = f.read()
        prompt = f"""
        사용자는 이전에 너로부터 피드백을 받았고, 그 피드백을 반영하여 새롭게 사진을 촬영한 상황.
        이전 피드백: {previous_feedback}
        이번 응답의 목적은 업로드된 새로운 사진을 바탕으로, 이전 피드백과 비교해 어떤 부분이 개선되었는지, 그리고 여전히 보완이 필요한 부분이 무엇인지 평가하는 것.
        만약 개선된 부분이 없다면, 그 사실도 솔직하고 냉정하게 판단하여 서술할 것.

        반드시 한글로 응답할 것.
        반드시 다음 형식에 맞춰 응답할 것: {{
        총점 : "S ~ D 사이의 등급에서 점수를 매길것"
        조리개 : "점수" "느낀점 밑 개선점"
        iso : "점수" "느낀점 밑 개선점"
        셔터속도 : "점수" "느낀점 밑 개선점"
        }}
        절대로 항목을 섞지 말것.
        모든 항목을 채울 것.
        문장을 출력하기 전에 한글이 어색하지 않은지 검토하고 한 번 더 수정할 것.
        """
    else:
        prompt = f"""
        반드시 한글로 응답할 것.
        반드시 다음 형식에 맞춰 응답할 것: {{
        총점 : "S ~ D 사이의 등급에서 점수를 매길것"
        조리개 : "점수" "느낀점 밑 개선점"
        iso : "점수" "느낀점 밑 개선점"
        셔터속도 : "점수" "느낀점 밑 개선점"
        }}
        절대로 항목을 섞지 말것.
        모든 항목을 채울 것.
        문장을 출력하기 전에 한글이 어색하지 않은지 검토하고 한 번 더 수정할 것.
        """

    feedback = get_llava_response(filepath, prompt)
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        f.write(feedback)
    save_history(filename, feedback)

    filter_prompt = """
당신은 사진 전문가입니다. 아래 이미지를 보고 다음 중 하나의 필터를 추천하고 그 이유를 설명하세요.
가능한 필터: ["BLUR", "SHARPEN", "DETAIL", "EDGE_ENHANCE", "SMOOTH"]

아래 JSON 형식으로만 출력하세요. 또한 reason을 출력할때는 반드시 한국어로 설명해줘:
{
  "recommended_filter": "필터 이름",
  "reason": "왜 이 필터를 추천하는지 한글로 설명해줘."
}
"""
    analysis = get_llava_response(filepath, filter_prompt)
    recommended = None
    reason = "없음"
    try:
        import re
        m = re.search(r'"recommended_filter"\s*:\s*"([^"]+)"', analysis)
        if m:
            recommended = m.group(1).strip().upper()
        m2 = re.search(r'"reason"\s*:\s*"([^"]+)"', analysis)
        if m2:
            reason = m2.group(1).strip()
    except Exception:
        pass
    CURRENT_FILTER = recommended

    return render_template('result.html', image_path=filepath, feedback=feedback,
                           filter_name=CURRENT_FILTER, reason=reason)

@app.route('/apply_filter', methods=['POST'])
def apply_filter():
    global CURRENT_FILENAME, CURRENT_FILTER
    if not CURRENT_FILENAME or not CURRENT_FILTER:
        return redirect(url_for('index'))

    original_path = os.path.join(app.config['UPLOAD_FOLDER'], CURRENT_FILENAME)
    name, ext = os.path.splitext(CURRENT_FILENAME)
    if not ext:
        ext = '.jpg'
    filtered_path = os.path.join(app.config['UPLOAD_FOLDER'], f"filtered_{name}{ext}")

    try:
        img = Image.open(original_path)
        img = fix_image_orientation(img)
        if CURRENT_FILTER == "BLUR":
            filtered = img.filter(ImageFilter.GaussianBlur(radius=8))
        elif CURRENT_FILTER == "SHARPEN":
            filtered = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
        elif CURRENT_FILTER == "DETAIL":
            filtered = ImageEnhance.Contrast(img).enhance(1.5)
            filtered = ImageEnhance.Color(filtered).enhance(1.8)
        elif CURRENT_FILTER == "SMOOTH":
            filtered = img.filter(ImageFilter.SMOOTH_MORE)
        elif CURRENT_FILTER in FILTER_MAP:
            filtered = img.filter(FILTER_MAP[CURRENT_FILTER])
        else:
            return "지원하지 않는 필터입니다."

        filtered.save(filtered_path)
        return render_template('filtered.html', image_path=filtered_path, original_path=original_path, filter_name=CURRENT_FILTER)

    except Exception as e:
        return f"필터 적용 오류: {str(e)}"

@app.route('/history')
def history():
    entries = load_history()
    entries.sort(key=lambda x: x['timestamp'], reverse=True)
    return render_template('history.html', entries=entries)

@app.route('/detail/<filename>')
def detail(filename):
    entries = load_history()
    entry = next((e for e in entries if e['filename'] == filename), None)
    if not entry:
        return "해당 피드백이 존재하지 않습니다.", 404
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    return render_template('detail.html', image_path=image_path, feedback=entry['feedback'], timestamp=entry['timestamp'])

@app.route('/delete_history/<filename>', methods=['POST'])
def delete_history(filename):
    entries = load_history()
    entries = [e for e in entries if e['filename'] != filename]
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    try:
        if os.path.exists(image_path):
            os.remove(image_path)
    except Exception:
        pass
    return redirect(url_for('history'))

@app.route('/reset_logs', methods=['POST'])
def reset_logs():
    # 피드백 로그 파일 삭제
    try:
        if os.path.exists(LOG_FILE):
            os.remove(LOG_FILE)
    except Exception:
        pass
    # 히스토리 로그 파일 삭제
    try:
        if os.path.exists(HISTORY_FILE):
            os.remove(HISTORY_FILE)
    except Exception:
        pass
    # 업로드된 이미지 폴더의 모든 파일 삭제(필요시 주석 해제)
    # for filename in os.listdir(UPLOAD_FOLDER):
    #     path = os.path.join(UPLOAD_FOLDER, filename)
    #     if os.path.isfile(path):
    #         os.remove(path)
    return redirect(url_for('index'))

def get_llava_response(image_path, prompt):
    with open(image_path, 'rb') as f:
        encoded_image = base64.b64encode(f.read()).decode('utf-8')

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llava",
            "prompt": prompt,
            "images": [encoded_image],
            "stream": True
        },
        stream=True
    )

    full_text = ""
    for line in response.iter_lines():
        if line:
            try:
                data = json.loads(line.decode('utf-8'))
                full_text += data.get("response", "")
            except Exception:
                continue
    return full_text.strip()

def save_history(filename, feedback):
    entry = {
        "filename": filename,
        "timestamp": datetime.datetime.now().isoformat(),
        "feedback": feedback
    }
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            history = json.load(f)
    else:
        history = []
    history.append(entry)
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

if __name__ == '__main__':
    app.run(debug=True)