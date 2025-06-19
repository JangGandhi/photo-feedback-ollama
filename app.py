# 서버 파일
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
            prompt = """사용자는 이전에 너로부터 피드백을 받았고, 그 피드백을 반영하여 새롭게 사진을 촬영환 상황.
                        이전 피드백: {previous_feedback}
                        이번 응답의 목적은 업로드된 새로운 사진을 바탕으로, 이전 사진과 비교해 어떤 부분이 개선되었는지, 그리고 여전히 보완이 필요한 부분이 무엇인지 평가하는 것.
                        만약 개선된 부분이 없다면, 그 사실도 솔직하고 냉정하게 판단하여 서술할 것.
                        반드시 한글로 응답할 것.
                        대괄호([]) 안에 있는 문장들은 예시 또는 설명이므로, 응답 생성 시 반드시 제외하고 출력할 것.
                        반드시 아래 JSON 형식에 맞춰 응답할 것:
                
                        {
                            "overall_grade": "" [설명: 전체적인 사진에 대한 평점. A~D 등급 중 하나. 예시: A]
                            "overall_feedback": "" [설명: 전체적인 사진에 대한 평가를 한글로 자세히 서술하고, 후보정 시 추천되는 작업이 있다면 함께 제안할 것. 예시: "전체적으로 색감과 구도가 훌륭하지만, 하이라이트가 다소 날아갔습니다. 후보정에서 밝기와 대비를 조절하면 개선될 수 있습니다."]

                            "shutter_speed_score": "" [설명: 셔터 속도를 중점으로 평가한 점수. 1~10 사이의 정수. 예시: 6]
                            "shutter_speed_comment": "" [설명: 셔터 속도에 대한 평가를 한글로 자세히 서술할 것. 예시: "셔터 속도가 약간 빠릅니다. 동작이 너무 정지되어 보일 수 있습니다."]

                            "aperture_score": "" [설명: 조리개 값을 중점으로 평가한 점수. 1~10 사이의 정수. 예시: 6]
                            "aperture_comment": "" [설명: 조리개 값에 대한 평가를 한글로 자세히 서술할 것. 예시: "조리개를 조금 더 열면 배경 흐림이 자연스러워질 수 있습니다."]

                            "iso_score": "" [설명: ISO 감도를 중점으로 평가한 점수. 1~10 사이의 정수. 예시: 6]
                            "iso_comment": "" [설명: ISO 감도에 대한 평가를 한글로 자세히 서술할 것. 예시: "노이즈가 조금 보입니다. ISO를 더 낮추는 것이 좋습니다."]
                        }"""
            
        else:
            prompt = """반드시 한글로 응답할 것.
                        대괄호([]) 안에 있는 문장들은 예시 또는 설명이므로, 응답 생성 시 반드시 제외하고 출력할 것.
                        반드시 아래 JSON 형식에 맞춰 응답할 것:

                        {
                            "overall_grade": "" [설명: 전체적인 사진에 대한 평점. A~D 등급 중 하나. 예시: A]
                            "overall_feedback": "" [설명: 전체적인 사진에 대한 평가를 한글로 자세히 서술하고, 후보정 시 추천되는 작업이 있다면 함께 제안할 것. 예시: "전체적으로 색감과 구도가 훌륭하지만, 하이라이트가 다소 날아갔습니다. 후보정에서 밝기와 대비를 조절하면 개선될 수 있습니다."]

                            "shutter_speed_score": "" [설명: 셔터 속도를 중점으로 평가한 점수. 1~10 사이의 정수. 예시: 6]
                            "shutter_speed_comment": "" [설명: 셔터 속도에 대한 평가를 한글로 자세히 서술할 것. 예시: "셔터 속도가 약간 빠릅니다. 동작이 너무 정지되어 보일 수 있습니다."]

                            "aperture_score": "" [설명: 조리개 값을 중점으로 평가한 점수. 1~10 사이의 정수. 예시: 6]
                            "aperture_comment": "" [설명: 조리개 값에 대한 평가를 한글로 자세히 서술할 것. 예시: "조리개를 조금 더 열면 배경 흐림이 자연스러워질 수 있습니다."]

                            "iso_score": "" [설명: ISO 감도를 중점으로 평가한 점수. 1~10 사이의 정수. 예시: 6]
                            "iso_comment": "" [설명: ISO 감도에 대한 평가를 한글로 자세히 서술할 것. 예시: "노이즈가 조금 보입니다. ISO를 더 낮추는 것이 좋습니다."]
                        }"""


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
