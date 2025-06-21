# ollama-photo-feedback# 사진 피드백 웹 애플리케이션 (Flask + Ollama LLaVA)

이 프로젝트는 사용자가 업로드한 사진을 AI 모델(LLaVA)을 통해 분석하여  
사진의 점수 및 개선점을 피드백하고, 이전 사진과 비교 평가까지 해주는 웹 서비스입니다.

---
## 🚀 How to Start

### 1. Python 라이브러리 설치

pip install flask requests pillow

### 2. Ollama 설치 및 모델 준비

Ollama 설치
https://ollama.com/download 에서 운영체제에 맞는 설치파일을 다운로드하여 설치하세요.

### LLaVA 모델 설치 명령어

ollama pull llava


### 3. Ollama 서버 실행 명령어

ollama run llava

위 명령어를 입력하면 LLaVA 모델이 로컬에서 실행되고,
Flask는 이 서버에 이미지를 전달하여 AI 피드백을 받아옵니다.

### 4. Flask 서버 실행 명령어

python app.py

웹 브라우저에서 아래 주소로 접속하세요:
http://localhost:5000

## 프로젝트 폴더 구조 예시

├── app.py # 메인 Flask 서버 파일

├── log/

│ ├── feedback_log.txt # AI 피드백 로그 기록 파일

│ └── history.json # 업로드/피드백 히스토리 저장 파일

├── static/

│ ├── uploads/ # 사용자가 업로드한 원본/필터 사진 저장 폴더

│ └── css/

│ └── style.css # 추가 스타일시트 파일

├── templates/

│ ├── index.html # 메인 페이지(사진 업로드/초기화 등)

│ ├── result.html # 평가 결과 페이지

│ ├── history.html # 피드백 히스토리(타임라인) 페이지

│ ├── filtered.html # 필터 적용 결과 페이지

│ └── detail.html # 사진/피드백 상세 보기 페이지

└── README.md # 프로젝트 설명 파일(이 문서)

## 📹 Demo
### 🪐 메인페이지

### 🪐 사진 피드백 페이지

### 🪐 이미지 필터 적용 결과 페이지

### 🪐 이전 피드백 결과 페이지

## 💻 System Architechture
![Image](https://github.com/user-attachments/assets/c13af8f0-42f9-42fc-a66c-93c6e9ce116e)
---

## 💡 Tech stack 
<br>
<div align =center>

분야| 사용 기술|
:--------:|:------------------------------:|
**Fronted** | <img src="https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white"> <img src="https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white">
**Backend** | <img src="https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white"> <img src="https://img.shields.io/badge/Pillow-3693F3?style=for-the-badge&logo=python&logoColor=white">
**LLM** | <img src="https://img.shields.io/badge/Ollama-000000?style=for-the-badge&logo=llama&logoColor=white"> <img src="https://img.shields.io/badge/LLaVA-FF6F00?style=for-the-badge&logo=OpenAI&logoColor=white">
</div>

## 사용 방법 

사진을 업로드하고 "평가 받기" 버튼 클릭

AI가 피드백 제공

AI가 추천한 필터 내용을 확인

"필터 적용하기" 버튼 클릭 시 추천된 필터가 적용된 이미지를 원본과 함께 확인

"이전 피드백 확인" 버튼을 통해 과거 분석 이력을 확인

"로그기록 초기화" 버튼 클릭시 이전에 저장되어있던 피드백 로그 기록들을 초기화함

## 기타

Ollama 서버는 백그라운드에서 계속 켜져 있어야 정상 작동합니다.

---
