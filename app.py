from flask import Flask, request, render_template, redirect, url_for
import os
import requests
import base64
import json

app = Flask(__name__)

# 업로드 및 로그 폴더 설정
UPLOAD_FOLDER = 'static/uploads'
LOG_FILE = 'log/feedback_log.txt'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('log', exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['image']
    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

        # 첫 번째 업로드인지 확인
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                previous_feedback = f.read()
            prompt = (
                f"다음은 이전 사진에 대한 피드백이야:\n{previous_feedback}\n"
                f"지금 업로드된 새로운 사진을 보고, 이전 피드백과 비교해 어떤 점이 개선되었는지, "
                f"여전히 개선할 점이 무엇인지 평가해줘."
            )
        else:
            prompt = "이 사진을 보고 사진의 점수(10점 만점), 잘한 점, 개선할 점을 알려줘."

        # LLaVA 분석 요청
        feedback = analyze_with_llava(filepath, prompt)

        # 피드백 로그 저장
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            f.write(feedback)

        return render_template('index.html', image_path=filepath, feedback=feedback)

    return redirect(url_for('index'))


@app.route('/clear_log', methods=['POST'])
def clear_log():
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
    return redirect(url_for('index'))


def analyze_with_llava(image_path, prompt):
    with open(image_path, 'rb') as f:
        encoded_image = base64.b64encode(f.read()).decode('utf-8')

    # 스트리밍 요청 처리
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

    # 응답을 한 줄씩 읽고 문자열로 이어붙이기
    full_response = ""
    for line in response.iter_lines():
        if line:
            try:
                data = json.loads(line.decode('utf-8'))
                full_response += data.get("response", "")
            except json.JSONDecodeError:
                continue

    return full_response if full_response else "AI 응답 없음"


if __name__ == '__main__':
    app.run(debug=True)
