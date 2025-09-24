# Tableau Data Source Migration Tool

Tableau Server의 데이터 원본을 Tableau Cloud로 자동 마이그레이션하는 도구입니다.

## 기능
- Tableau Server 데이터 원본을 Tableau Cloud로 마이그레이션
- 전체 또는 최근 업데이트된 데이터 원본 선택적 마이그레이션
- 실시간 진행 상황 모니터링
- 상세 결과 리포트 제공

## 설치 방법
```bash
# 저장소 복제
git clone https://github.com/giyori91/tableau-migration-tool.git
cd tableau-migration-tool

# 실행 권한 부여
chmod +x run.sh

# 실행
./run.sh
```

## 환경 설정
1. `properties.env` 파일을 생성하고 필요한 정보 입력:
```env
# Tableau Server 설정
TS_SERVER='your-server-url'
TS_SITE='your-site-name'
TS_PAT_NAME='your-pat-name'
TS_PAT_SECRET='your-pat-secret'

# Tableau Cloud 설정
TC_SERVER='your-cloud-url'
TC_SITE='your-cloud-site'
TC_PAT_NAME='your-cloud-pat-name'
TC_PAT_SECRET='your-cloud-pat-secret'
TC_PROJECT_ID='your-project-id'
```

자세한 내용은 [설치 가이드](docs/INSTALL.md)를 참조하세요.