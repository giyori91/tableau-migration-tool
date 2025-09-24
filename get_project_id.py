import tableauserverclient as TSC
from config import Config

def get_project_id(project_name):
    config = Config()
    
    # Tableau Cloud 연결 (API 버전 설정 추가)
    server = TSC.Server(config.cloud['url'], use_server_version=True)
    tableau_auth = TSC.PersonalAccessTokenAuth(
        token_name=config.cloud['pat_name'],
        personal_access_token=config.cloud['pat_secret'],
        site_id=config.cloud['site']
    )
    
    try:
        server.auth.sign_in_with_personal_access_token(tableau_auth)
        
        # 모든 프로젝트 조회
        all_projects, _ = server.projects.get()
        
        # 프로젝트 이름으로 ID 찾기
        for project in all_projects:
            print(f"Found project: {project.name} (ID: {project.id})")
            if project.name == project_name:
                print(f"프로젝트 '{project_name}'의 ID: {project.id}")
                return project.id
        
        print(f"프로젝트 '{project_name}'를 찾을 수 없습니다.")
        return None
        
    finally:
        server.auth.sign_out()

if __name__ == "__main__":
    # 실제 찾고자 하는 프로젝트 이름을 입력하세요
    project_id = get_project_id("03-DataMig")  # 찾고자 하는 프로젝트 이름으로 변경