import os
from dotenv import load_dotenv
import tableauserverclient as TSC

class Config:
    def __init__(self):
        load_dotenv('properties.env')
        
        # Tableau Server 설정
        self.server = {
            'url': os.getenv('TS_SERVER'),
            'site': os.getenv('TS_SITE'),
            'pat_name': os.getenv('TS_PAT_NAME'),
            'pat_secret': os.getenv('TS_PAT_SECRET')
        }
        
        # Tableau Cloud 설정
        self.cloud = {
            'url': os.getenv('TC_SERVER'),
            'site': os.getenv('TC_SITE'),
            'pat_name': os.getenv('TC_PAT_NAME'),
            'pat_secret': os.getenv('TC_PAT_SECRET'),
            'project_id': os.getenv('TC_PROJECT_ID')
        }

    def validate(self):
        """설정값 검증"""
        # Server 설정 검증
        if not all([self.server['url'], self.server['site'], 
                   self.server['pat_name'], self.server['pat_secret']]):
            raise ValueError("Required Tableau Server settings are missing in properties.env")
            
        # Cloud 설정 검증
        if not all([self.cloud['url'], self.cloud['site'],
                   self.cloud['pat_name'], self.cloud['pat_secret'],
                   self.cloud['project_id']]):
            raise ValueError("Required Tableau Cloud settings are missing in properties.env")

def get_project_id(project_name):
    config = Config()
    
    # Tableau Cloud 연결
    server = TSC.Server(config.cloud['url'])
    tableau_auth = TSC.PersonalAccessTokenAuth(
        config.cloud['pat_name'],
        config.cloud['pat_secret'],
        config.cloud['site']
    )
    
    with server.auth.sign_in_with_personal_access_token(tableau_auth):  # 메서드명 수정
        # 모든 프로젝트 조회
        all_projects, _ = server.projects.get()
        
        # 프로젝트 이름으로 ID 찾기
        for project in all_projects:
            if project.name == project_name:
                print(f"프로젝트 '{project_name}'의 ID: {project.id}")
                return project.id
    
    print(f"프로젝트 '{project_name}'를 찾을 수 없습니다.")
    return None

if __name__ == "__main__":
    # 실제 찾고자 하는 프로젝트 이름을 입력하세요
    project_id = get_project_id("03-DataMig")  # 예: "03-DataMig" 프로젝트