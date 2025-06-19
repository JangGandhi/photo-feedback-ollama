# ollama-photo-feedback# 사진 피드백 웹 애플리케이션 (Flask + Ollama LLaVA)

이 프로젝트는 사용자가 업로드한 사진을 AI 모델(LLaVA)을 통해 분석하여  
사진의 점수 및 개선점을 피드백하고, 이전 사진과 비교 평가까지 해주는 웹 서비스입니다.

---

## 1. Python 라이브러리 설치

pip install flask requests

## 2. Ollama 설치 및 모델 준비
Ollama 설치
https://ollama.com/download 에서 운영체제에 맞는 설치파일을 다운로드하여 설치하세요.

LLaVA 모델 설치 명령어

ollama pull llava


## 3. Ollama 서버 실행 명령어

ollama run llava

위 명령어를 입력하면 LLaVA 모델이 로컬에서 실행되고,
Flask는 이 서버에 이미지를 전달하여 AI 피드백을 받아옵니다.

## 4. Flask 서버 실행 명령어

python app.py

웹 브라우저에서 아래 주소로 접속하세요:
http://localhost:5000

## 프로젝트 폴더 구조 예시

project/

├── app.py

├── templates/

│   └── index.html

├── static/

│   ├── uploads/           ← 업로드된 이미지 저장

│   └── css/

│       └── style.css      ← 선택적 CSS 스타일 파일

├── log/

│   └── feedback_log.txt   ← AI 피드백 기록 (자동 생성됨)

## 기능 요약

첫 번째 사진 업로드 → AI가 점수 및 개선점 피드백

두 번째 사진부터는 이전 분석 내용과 비교해 향상된 점/부족한 점 평가

분석 로그 초기화 버튼 → 다시 첫 번째 사진처럼 분석

## 기타

Ollama 서버는 백그라운드에서 계속 켜져 있어야 정상 작동합니다.

---
