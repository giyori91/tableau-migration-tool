from config import Config
import tableauserverclient as TSC
import logging
import os
from datetime import datetime
from contextlib import contextmanager
from prometheus_client import Summary, Counter
from tqdm import tqdm
from typing import List, Dict
import argparse

class TableauMigrationWorker:
    def __init__(self):
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.download_path = "./downloads"  # 다운로드 폴더 지정
        os.makedirs(self.download_path, exist_ok=True)  # 다운로드 폴더 생성

    @contextmanager
    def tableau_connection(self, is_cloud=False):
        """Tableau 서버 연결 관리"""
        conf = self.config.cloud if is_cloud else self.config.server
        server = TSC.Server(conf['url'], use_server_version=True)
        
        try:
            auth = TSC.PersonalAccessTokenAuth(
                token_name=conf['pat_name'],
                personal_access_token=conf['pat_secret'],
                site_id=conf['site']
            )
            server.auth.sign_in_with_personal_access_token(auth)
            self.logger.info(f"Successfully connected to {'Tableau Cloud' if is_cloud else 'Tableau Server'}")
            yield server
        except Exception as e:
            self.logger.error(f"Failed to connect to {'Tableau Cloud' if is_cloud else 'Tableau Server'}: {str(e)}")
            raise
        finally:
            server.auth.sign_out()

    def download_datasource(self, datasource):
        """데이터 원본 다운로드"""
        try:
            file_name = f"{datasource.name}_{datetime.now().isoformat()}"
            file_path = os.path.join(self.download_path, file_name)
            
            with self.tableau_connection(is_cloud=False) as server:
                server.datasources.download(datasource.id, file_path, include_extract=True)
                
            # 실제 다운로드된 파일 경로 찾기
            downloaded_file = None
            for f in os.listdir(self.download_path):
                if f.startswith(file_name):
                    downloaded_file = os.path.join(self.download_path, f)
                    break
            
            if not downloaded_file or not os.path.exists(downloaded_file):
                raise FileNotFoundError(f"Downloaded file not found for {datasource.name}")
                
            return downloaded_file
        except Exception as e:
            self.logger.error(f"Failed to download {datasource.name}: {str(e)}")
            raise

    def upload_to_cloud(self, datasource_name, file_path):
        """클라우드에 데이터 원본 업로드"""
        try:
            with self.tableau_connection(is_cloud=True) as cloud:
                # 프로젝트 ID 검증
                project_id = self.config.cloud.get('project_id')
                if not project_id:
                    raise ValueError("Project ID is not configured in properties.env")
                
                # 프로젝트 존재 여부 확인
                all_projects, _ = cloud.projects.get()
                project_exists = any(p.id == project_id for p in all_projects)
                
                if not project_exists:
                    raise ValueError(f"Project with ID {project_id} does not exist in Tableau Cloud")
                
                # 데이터 원본 게시
                item = TSC.DatasourceItem(
                    project_id=project_id,
                    name=datasource_name
                )
                cloud.datasources.publish(item, file_path, mode='Overwrite')
                self.logger.info(f"Successfully published {datasource_name} to Tableau Cloud")
        except Exception as e:
            self.logger.error(f"Failed to upload {datasource_name}: {str(e)}")
            raise

    def migrate_datasource(self, datasource):
        """단일 데이터 원본 마이그레이션"""
        downloaded_file = None
        try:
            downloaded_file = self.download_datasource(datasource)
            self.upload_to_cloud(datasource.name, downloaded_file)
        except Exception as e:
            self.logger.error(f"Failed to migrate {datasource.name}: {str(e)}")
        finally:
            if downloaded_file and os.path.exists(downloaded_file):
                os.remove(downloaded_file)

    def migrate_all_datasources(self):
        """모든 데이터 원본 마이그레이션"""
        try:
            migration_results = {
                'total': 0,
                'success': 0,
                'failed': 0,
                'details': []
            }

            print("\n1. 데이터 원본 수집 중...")
            with self.tableau_connection(is_cloud=False) as server:
                all_datasources, _ = server.datasources.get()
                migration_results['total'] = len(all_datasources)

                # 프로그레스바로 데이터 원본 정보 수집
                print("\n2. 데이터 원본 상세 정보:")
                print(f"{'데이터 원본명':<30} {'최종 수정일':<20} {'소유자':<20}")
                print("-" * 70)
                
                for ds in tqdm(all_datasources, desc="데이터 원본 정보 수집"):
                    ds = server.datasources.get_by_id(ds.id)
                    updated_at = ds.updated_at.strftime('%Y-%m-%d %H:%M:%S') if ds.updated_at else 'N/A'
                    owner = ds.owner_id if hasattr(ds, 'owner_id') else 'Unknown'
                    
                    print(f"{ds.name:<30} {updated_at:<20} {owner:<20}")
                    migration_results['details'].append({
                        'name': ds.name,
                        'updated_at': updated_at,
                        'owner': owner,
                        'status': 'pending'
                    })

            # 마이그레이션 실행
            print("\n3. 마이그레이션 실행 중...")
            for ds in tqdm(all_datasources, desc="마이그레이션 진행"):
                try:
                    self.migrate_datasource(ds)
                    migration_results['success'] += 1
                    # 결과 상태 업데이트
                    for detail in migration_results['details']:
                        if detail['name'] == ds.name:
                            detail['status'] = 'success'
                except Exception as e:
                    migration_results['failed'] += 1
                    # 결과 상태 업데이트
                    for detail in migration_results['details']:
                        if detail['name'] == ds.name:
                            detail['status'] = 'failed'
                            detail['error'] = str(e)

            # 최종 결과 출력
            print("\n4. 마이그레이션 결과 요약:")
            print(f"총 데이터 원본 수: {migration_results['total']}")
            print(f"성공: {migration_results['success']}")
            print(f"실패: {migration_results['failed']}")

            # 성공/실패 상세 내역
            if migration_results['success'] > 0:
                print("\n5. 성공한 데이터 원본:")
                for detail in migration_results['details']:
                    if detail['status'] == 'success':
                        print(f"✓ {detail['name']} ({detail['updated_at']})")

            if migration_results['failed'] > 0:
                print("\n6. 실패한 데이터 원본:")
                for detail in migration_results['details']:
                    if detail['status'] == 'failed':
                        print(f"✗ {detail['name']}: {detail.get('error', 'Unknown error')}")

        except Exception as e:
            self.logger.error(f"Failed to migrate all datasources: {str(e)}")

    def check_update_needed(self, updated_at):
        """업데이트 필요 여부 확인"""
        if not updated_at:
            return False
            
        time_diff = datetime.now(updated_at.tzinfo) - updated_at
        criteria_type = self.config.update_criteria['type']
        criteria_value = self.config.update_criteria['value']
        
        if criteria_type == 'days':
            return time_diff.days < criteria_value
        elif criteria_type == 'hours':
            return time_diff.total_seconds() / 3600 < criteria_value
        elif criteria_type == 'minutes':
            return time_diff.total_seconds() / 60 < criteria_value
        
        return False

    def migrate_updated_datasources(self):
        """업데이트된 데이터 원본 마이그레이션"""
        try:
            updated_datasources = []
            migration_results = {
                'total': 0,
                'updated': 0,
                'success': 0,
                'failed': 0,
                'skipped': 0,
                'details': []
            }
            
            print("\n1. 데이터 원본 검사 중...")
            with self.tableau_connection(is_cloud=False) as server:
                all_datasources, _ = server.datasources.get()
                migration_results['total'] = len(all_datasources)
                
                # 프로그레스바로 데이터 원본 검사
                for ds in tqdm(all_datasources, desc="데이터 원본 검사"):
                    ds = server.datasources.get_by_id(ds.id)
                    
                    if ds.updated_at:
                        status = {
                            'name': ds.name,
                            'updated_at': ds.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                            'status': 'pending'
                        }
                        
                        if self.check_update_needed(ds.updated_at):
                            status['status'] = 'update_needed'
                            updated_datasources.append(ds)
                            migration_results['updated'] += 1
                        else:
                            status['status'] = 'skipped'
                            migration_results['skipped'] += 1
                            
                        migration_results['details'].append(status)
                    else:
                        migration_results['skipped'] += 1
            
            # 업데이트 대상 요약 출력
            print("\n2. 업데이트 대상 데이터 원본:")
            print(f"{'데이터 원본명':<30} {'마지막 업데이트':<20}")
            print("-" * 50)
            for detail in migration_results['details']:
                if detail['status'] == 'update_needed':
                    print(f"{detail['name']:<30} {detail['updated_at']:<20}")
            
            # 마이그레이션 실행
            print("\n3. 마이그레이션 실행 중...")
            for ds in tqdm(updated_datasources, desc="마이그레이션 진행"):
                try:
                    self.migrate_datasource(ds)
                    migration_results['success'] += 1
                    # 결과 상태 업데이트
                    for detail in migration_results['details']:
                        if detail['name'] == ds.name:
                            detail['status'] = 'success'
                except Exception as e:
                    migration_results['failed'] += 1
                    # 결과 상태 업데이트
                    for detail in migration_results['details']:
                        if detail['name'] == ds.name:
                            detail['status'] = 'failed'
                            detail['error'] = str(e)
            
            # 최종 결과 출력
            print("\n4. 마이그레이션 결과 요약:")
            print(f"총 데이터 원본 수: {migration_results['total']}")
            print(f"업데이트 대상: {migration_results['updated']}")
            print(f"성공: {migration_results['success']}")
            print(f"실패: {migration_results['failed']}")
            print(f"건너뜀: {migration_results['skipped']}")
            
            # 실패한 항목이 있다면 상세 내역 출력
            if migration_results['failed'] > 0:
                print("\n5. 실패한 데이터 원본:")
                for detail in migration_results['details']:
                    if detail['status'] == 'failed':
                        print(f"- {detail['name']}: {detail.get('error', 'Unknown error')}")
                        
        except Exception as e:
            self.logger.error(f"Failed to migrate updated datasources: {str(e)}")

    def list_cloud_projects(self):
        """Tableau Cloud의 프로젝트 목록 조회"""
        try:
            with self.tableau_connection(is_cloud=True) as cloud:
                all_projects, _ = cloud.projects.get()
                
                print("\n사용 가능한 프로젝트 목록:")
                print(f"{'번호':<4} {'프로젝트명':<30} {'프로젝트 ID':<36}")
                print("-" * 70)
                
                for idx, project in enumerate(all_projects, 1):
                    print(f"{idx:<4} {project.name:<30} {project.id:<36}")
                
                return all_projects
        except Exception as e:
            self.logger.error(f"프로젝트 목록 조회 실패: {str(e)}")
            raise

    def select_and_save_project(self, number, projects):
        """선택된 프로젝트를 properties.env에 저장"""
        try:
            if not (1 <= number <= len(projects)):
                raise ValueError("잘못된 프로젝트 번호입니다.")
            
            selected_project = projects[number - 1]
            
            # properties.env 파일 읽기
            with open('properties.env', 'r') as f:
                lines = f.readlines()
            
            # TC_PROJECT_ID 업데이트
            updated = False
            for i, line in enumerate(lines):
                if line.startswith('TC_PROJECT_ID='):
                    lines[i] = f"TC_PROJECT_ID='{selected_project.id}'\n"
                    updated = True
                    break
            
            # TC_PROJECT_ID가 없으면 추가
            if not updated:
                lines.append(f"\nTC_PROJECT_ID='{selected_project.id}'\n")
            
            # 파일 저장
            with open('properties.env', 'w') as f:
                f.writelines(lines)
            
            return f"\n설정된 프로젝트 정보:\n이름: {selected_project.name}\nID: {selected_project.id}"
        
        except Exception as e:
            self.logger.error(f"프로젝트 설정 실패: {str(e)}")
            raise

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['all', 'updated', 'list-projects', 'select-project'], required=True)
    parser.add_argument('--number', type=int, help='프로젝트 번호')
    args = parser.parse_args()
    
    worker = TableauMigrationWorker()
    
    if args.mode == 'all':
        worker.migrate_all_datasources()
    elif args.mode == 'updated':
        worker.migrate_updated_datasources()
    elif args.mode == 'list-projects':
        worker.list_cloud_projects()
    elif args.mode == 'select-project':
        if not args.number:
            print("프로젝트 번호가 필요합니다.")
            sys.exit(1)
        projects = worker.list_cloud_projects()
        print(worker.select_and_save_project(args.number, projects))