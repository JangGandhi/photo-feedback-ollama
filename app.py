# 통합 서버: 업로드 → AI 피드백 → 필터 추천 → 필터 적용 → 이전 피드백 확인
from flask import Flask, request, render_template, redirect, url_for
import os
import requests
import base64
import json
import datetime
from werkzeug.utils import secure_filename
from PIL import Image, ImageFilter, ImageEnhance

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

# 상태 저장 변수
CURRENT_FILENAME = None
CURRENT_FILTER = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/evaluate', methods=['POST'])
def evaluate():
    global CURRENT_FILENAME, CURRENT_FILTER
    file = request.files['image']
    if not file:
        return redirect(url_for('index'))

    # 파일 저장
    filename = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_") + secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    CURRENT_FILENAME = filename

    # 평가 프롬프트 (변경 금지)
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            previous_feedback = f.read()
        prompt = f"""사용자는 이전에 너로부터 피드백을 받았고, 그 피드백을 반영하여 새롭게 사진을 촬영환 상황.
이전 피드백: {previous_feedback}
이번 응답의 목적은 업로드된 새로운 사진을 바탕으로, 이전 사진과 비교해 어떤 부분이 개선되었는지, 그리고 여전히 보완이 필요한 부분이 무엇인지 평가하는 것.
만약 개선된 부분이 없다면, 그 사실도 솔직하고 냉정하게 판단하여 서술할 것.
반드시 한글로 응답할 것.
대괄호([]) 안에 있는 문장들은 예시 또는 설명이므로, 응답 생성 시 반드시 제외하고 출력할 것.
반드시 아래 JSON 형식에 맞춰 응답할 것:

{{
  "overall_grade": "",
  "overall_feedback": "",
  "shutter_speed_score": "",
  "shutter_speed_comment": "",
  "aperture_score": "",
  "aperture_comment": "",
  "iso_score": "",
  "iso_comment": ""
}}"""
    else:
        prompt = """반드시 한글로 응답할 것.
대괄호([]) 안에 있는 문장들은 예시 또는 설명이므로, 응답 생성 시 반드시 제외하고 출력할 것.
반드시 아래 JSON 형식에 맞춰 응답할 것:

{
  "overall_grade": "",
  "overall_feedback": "",
  "shutter_speed_score": "",
  "shutter_speed_comment": "",
  "aperture_score": "",
  "aperture_comment": "",
  "iso_score": "",
  "iso_comment": ""
}"""

    # 피드백 요청
    feedback = analyze_with_llava(filepath, prompt)
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        f.write(json.dumps(feedback, ensure_ascii=False, indent=2))
    save_history(filename, feedback)

    # 필터 추천
    filter_prompt = """
당신은 사진 전문가입니다. 아래 이미지를 보고 다음 중 하나의 필터를 추천하고 그 이유를 설명하세요.
가능한 필터: [\"BLUR\", \"SHARPEN\", \"DETAIL\", \"CONTOUR\", \"EDGE_ENHANCE\", \"SMOOTH\"]

아래 JSON 형식으로만 출력하세요:
{
  "recommended_filter": "필터 이름",
  "reason": "왜 이 필터를 추천하는지 한글로 설명"
}
"""
    analysis = analyze_with_llava(filepath, filter_prompt)
    CURRENT_FILTER = analysis.get("recommended_filter", "").strip().upper() if analysis else None
    reason = analysis.get("reason", "없음") if analysis else "분석 실패"

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

def analyze_with_llava(image_path, prompt):
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
            except:
                continue

    try:
        json_start = full_text.find("{")
        json_end = full_text.rfind("}") + 1
        json_str = full_text[json_start:json_end]
        return json.loads(json_str)
    except Exception as e:
        print("LLaVA 응답 파싱 실패:", e)
        print("응답 원문:\n", full_text)
        return {"error": "파싱 실패", "raw_response": full_text}

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
