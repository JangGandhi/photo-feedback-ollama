from flask import Flask, request, render_template, redirect, url_for
import os
import requests
import base64

app = Flask(__name__)

# 폴더 및 파일 경로 설정
UPLOAD_FOLDER = 'static/uploads'
LOG_FILE = 'log/feedback_log.txt'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('log', exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ✅ Gemini API Key 설정
GEMINI_API_KEY = "AIzaSyBv-pIij9fpDqD5CRD1Cu-AT9j8FtoGeR8"
GEMINI_MODEL = "gemini-1.5-flash"  # 또는 "gemini-2.0-pro-vision", "gemini-2.0-flash"

def analyze_with_gemini_rest(image_path, prompt):
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"

    with open(image_path, "rb") as f:
        image_base64 = base64.b64encode(f.read()).decode("utf-8")

    headers = {
        "Content-Type": "application/json"
    }

    payload = {
        "contents": [
            {
                "parts": [
                    { "text": prompt },
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": image_base64
                        }
                    }
                ]
            }
        ]
    }

    response = requests.post(endpoint, headers=headers, json=payload)
    try:
        result = response.json()
        return result['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return f"오류 발생: {e}"


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['image']
    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                previous_feedback = f.read()
            prompt = """
            다음 사진을 보고 아래 항목에 대해 평가해줘:

            1. 셔터 속도에 대한 평가와 점수 (10점 만점)
            2. 조리개 값에 대한 평가와 점수 (10점 만점)
            3. ISO 감도에 대한 평가와 점수 (10점 만점)
            4. 위 세 항목이 사진 전체에 미친 영향을 간단히 요약해줘
            5. 이 사진을 개선하기 위해 어떤 각도에서 촬영하면 더 좋을지 구체적으로 조언해줘

            사진의 구도, 피사체, 노출 조건을 고려해서 구체적으로 평가해줘.
            """
        else:
            prompt = "이 사진을 보고 사진의 점수(10점 만점), 잘한 점, 개선할 점을 알려줘."

        feedback = analyze_with_gemini_rest(filepath, prompt)

        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            f.write(feedback)

        return render_template('index.html', image_path=filepath, feedback=feedback)

    return redirect(url_for('index'))


@app.route('/clear_log', methods=['POST'])
def clear_log():
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True, port=5000)
