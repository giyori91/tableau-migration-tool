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
            with self.tableau_connection(is_cloud=False) as server:
                all_datasources, _ = server.datasources.get()
                
            # 서버 연결 밖에서 마이그레이션 수행
            for ds in all_datasources:
                self.migrate_datasource(ds)
                
        except Exception as e:
            self.logger.error(f"Failed to migrate all datasources: {str(e)}")

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
                        time_diff = datetime.now(ds.updated_at.tzinfo) - ds.updated_at
                        status = {
                            'name': ds.name,
                            'updated_at': ds.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                            'status': 'pending'
                        }
                        
                        if time_diff.days < 1:
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Tableau 데이터 원본 마이그레이션 도구')
    parser.add_argument('--mode', choices=['all', 'updated'], 
                       default='updated',
                       help='마이그레이션 모드 선택 (all: 전체, updated: 업데이트된 항목만)')
    
    args = parser.parse_args()
    worker = TableauMigrationWorker()
    
    if args.mode == 'all':
        worker.migrate_all_datasources()
    else:
        worker.migrate_updated_datasources()