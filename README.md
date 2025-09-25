# Tableau Data Source Migration Tool

Tableau Server의 데이터 원본을 Tableau Cloud로 자동 마이그레이션하는 도구입니다.

## 주요 기능

- Tableau Server에서 데이터 원본 자동 다운로드
- Tableau Cloud로 데이터 원본 자동 업로드
- 전체 또는 최근 업데이트된 데이터 원본 선택적 마이그레이션
- 실시간 진행 상황 모니터링 
- 상세 마이그레이션 결과 리포트
- Tableau Cloud 프로젝트 설정 도구

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

# 실행 권한 부여
chmod +x run.sh

# 실행
./run.sh
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

# 업데이트 기준 설정
UPDATE_CRITERIA_TYPE='days'    # 가능한 값: days, hours, minutes
UPDATE_CRITERIA_VALUE='1'      # 숫자값: 업데이트 기준 기간
```

### 사용 방법

실행 스크립트(`run.sh`)를 실행하면 다음 메뉴가 표시됩니다:

1. **전체 데이터 원본 마이그레이션**
   - Tableau Server의 모든 데이터 원본을 Cloud로 마이그레이션
   - 진행 상황과 결과가 실시간으로 표시

2. **업데이트된 데이터 원본만 마이그레이션**
   - 설정된 기간 내에 업데이트된 데이터 원본만 마이그레이션
   - 업데이트 기준은 `properties.env`에서 설정 가능
   ```env
   # 예: 3일 이내 업데이트
   UPDATE_CRITERIA_TYPE='days'
   UPDATE_CRITERIA_VALUE='3'
   
   # 예: 12시간 이내 업데이트
   UPDATE_CRITERIA_TYPE='hours'
   UPDATE_CRITERIA_VALUE='12'
   ```

3. **Tableau Cloud 프로젝트 설정**
   - Cloud의 사용 가능한 프로젝트 목록 표시
   - 프로젝트 선택 시 자동으로 `properties.env` 파일에 설정
   - 마이그레이션 대상 프로젝트를 쉽게 변경 가능

### 실행 결과

- 마이그레이션 진행 상황이 실시간으로 표시
- 성공/실패 항목 구분 표시
- 오류 발생 시 상세 메시지 제공
- 최종 결과 요약 리포트 제공

### 스케줄링 설정

#### macOS에서 설정

1. crontab 편집:
```bash
crontab -e
```

2. 원하는 스케줄로 실행 명령 추가:
```bash
# 매일 자정에 업데이트된 데이터 원본 마이그레이션
0 0 * * * cd /path/to/tableau-migration-tool && ./run.sh << EOF
2
EOF

# 매주 일요일 새벽 3시에 전체 마이그레이션
0 3 * * 0 cd /path/to/tableau-migration-tool && ./run.sh << EOF
1
EOF
```

#### 로깅 설정

자동 실행 시 로그를 저장하려면 다음과 같이 설정:

```bash
# 로그 파일과 함께 실행
0 0 * * * cd /path/to/tableau-migration-tool && ./run.sh << EOF
2
EOF >> /path/to/tableau-migration-tool/logs/migration_$(date +\%Y\%m\%d).log 2>&1
```

#### 주요 스케줄링 예시

- 매일 특정 시간 실행:
```bash
0 3 * * * # 매일 새벽 3시
```

- 주중(월-금)만 실행:
```bash
0 1 * * 1-5 # 평일 새벽 1시
```

- 특정 간격으로 실행:
```bash
0 */4 * * * # 4시간마다
```

#### 스케줄링 모니터링

- 로그 확인:
```bash
tail -f /path/to/tableau-migration-tool/logs/migration_$(date +%Y%m%d).log
```

- cron 작업 목록 확인:
```bash
crontab -l
```

## 라이선스

이 프로젝트는 MIT 라이선스로 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 기여하기

버그를 발견하셨거나 새로운 기능을 제안하고 싶으시다면 이슈를 생성해주세요.