#!/bin/bash

# 가상환경이 없다면 생성
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# 가상환경 활성화
source venv/bin/activate

# 필요한 패키지 설치
pip install -r requirements.txt

# 실행 모드 선택
echo "Tableau 데이터 원본 마이그레이션 도구"
echo "1. 전체 데이터 원본 마이그레이션"
echo "2. 업데이트된 데이터 원본만 마이그레이션"
echo "3. Tableau Cloud 프로젝트 설정"
echo "선택하세요 (1, 2 또는 3): "
read choice

case $choice in
  1)
    python src/main.py --mode all
    ;;
  2)
    python src/main.py --mode updated
    ;;
  3)
    echo "현재 사용 가능한 프로젝트 목록을 가져오는 중..."
    # 프로젝트 목록 조회 및 선택
    projects=$(python src/main.py --mode list-projects)
    
    if [ $? -eq 0 ]; then
        echo "$projects"
        echo ""
        echo "프로젝트 번호를 선택하세요: "
        read project_number
        
        # 선택된 프로젝트 ID를 properties.env에 저장
        project_info=$(python src/main.py --mode select-project --number "$project_number")
        
        if [ $? -eq 0 ]; then
            echo "프로젝트가 성공적으로 설정되었습니다."
            echo "$project_info"
        else
            echo "프로젝트 설정 중 오류가 발생했습니다."
            exit 1
        fi
    else
        echo "프로젝트 목록을 가져오는데 실패했습니다."
        exit 1
    fi
    ;;
  *)
    echo "잘못된 선택입니다. 1, 2 또는 3을 선택하세요."
    exit 1
    ;;
esac

# 가상환경 비활성화
deactivate