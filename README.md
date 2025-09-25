# Tableau Data Source Migration Tool

Tableau Server의 데이터 원본을 Tableau Cloud로 자동 마이그레이션하는 도구입니다.

## 주요 기능

- Tableau Server에서 데이터 원본 자동 다운로드
- Tableau Cloud로 데이터 원본 자동 업로드
- 전체 또는 최근 업데이트된 데이터 원본 선택적 마이그레이션
- 실시간 진행 상황 모니터링 
- 상세 마이그레이션 결과 리포트

## 시작하기

### 요구사항

- Python 3.9 이상
- Tableau Server 계정
- Tableau Cloud 계정
- Personal Access Token (PAT)

### 설치

```bash
# 저장소 복제
git clone https://github.com/yourorg/tableau-migration-tool.git
cd tableau-migration-tool

# 가상환경 생성 및 활성화 
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 환경 설정

1. `properties.env` 파일을 생성하고 필요한 정보를 입력합니다:

```env
# Tableau Server 설정
TS_SERVER='https://your-server.com'
TS_SITE='your-site'
TS_PAT_NAME='your-pat-name'
TS_PAT_SECRET='your-pat-secret'

# Tableau Cloud 설정 
TC_SERVER='https://10ax.online.tableau.com'
TC_SITE='your-site'
TC_PAT_NAME='your-cloud-pat'
TC_PAT_SECRET='your-cloud-secret'
TC_PROJECT_ID='target-project-id'
```

### 실행

```bash
# 실행 권한 부여
chmod +x run.sh

# 실행
./run.sh
```

## 사용 방법

1. 전체 마이그레이션
```bash
python src/main.py --mode all
```

2. 최근 업데이트된 데이터 원본만 마이그레이션
```bash 
python src/main.py --mode updated
```

## 라이선스

이 프로젝트는 MIT 라이선스로 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 기여하기

버그를 발견하셨거나 새로운 기능을 제안하고 싶으시다면 이슈를 생성해주세요.