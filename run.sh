#!/bin/bash
# filepath: run.sh

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
echo "선택하세요 (1 또는 2): "
read choice

case $choice in
  1)
    python src/main.py --mode all
    ;;
  2)
    python src/main.py --mode updated
    ;;
  *)
    echo "잘못된 선택입니다."
    exit 1
    ;;
esac

# 가상환경 비활성화
deactivate