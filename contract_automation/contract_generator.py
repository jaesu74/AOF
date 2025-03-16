import jinja2
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

class ContractGenerator:
    """계약서 자동 생성을 위한 클래스"""
    
    def __init__(self, templates_dir: str = 'templates'):
        """
        Args:
            templates_dir (str): 계약서 템플릿이 저장된 디렉토리 경로
        """
        self.templates_dir = Path(templates_dir)
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.templates_dir)),
            autoescape=True
        )
    
    def generate_contract(self, template_name: str, data: Dict[str, Any]) -> str:
        """
        계약서 템플릿에 데이터를 적용하여 최종 계약서를 생성합니다.
        
        Args:
            template_name (str): 사용할 템플릿 파일명
            data (Dict[str, Any]): 템플릿에 적용할 데이터
            
        Returns:
            str: 생성된 계약서 내용
        """
        try:
            template = self.env.get_template(template_name)
            contract = template.render(**data)
            return contract
        except jinja2.TemplateNotFound:
            raise FileNotFoundError(f"템플릿 파일을 찾을 수 없습니다: {template_name}")
        except Exception as e:
            raise Exception(f"계약서 생성 중 오류 발생: {str(e)}")
    
    def save_contract(self, content: str, output_path: str) -> str:
        """
        생성된 계약서를 파일로 저장합니다.
        
        Args:
            content (str): 저장할 계약서 내용
            output_path (str): 저장할 파일 경로
            
        Returns:
            str: 저장된 파일의 절대 경로
        """
        try:
            output_file = Path(output_path)
            output_file.write_text(content, encoding='utf-8')
            return str(output_file.absolute())
        except Exception as e:
            raise Exception(f"계약서 저장 중 오류 발생: {str(e)}")

# 사용 예시
if __name__ == "__main__":
    # 테스트용 데이터
    sample_data = {
        "company_name": "테스트 기업",
        "contact_person": "홍길동",
        "start_date": datetime.now().strftime("%Y-%m-%d"),
        "end_date": datetime(2024, 12, 31).strftime("%Y-%m-%d"),
        "contract_type": "서비스 이용 계약",
    }
    
    generator = ContractGenerator()
    contract = generator.generate_contract("service_contract.html", sample_data)
    saved_path = generator.save_contract(contract, "generated_contracts/contract_001.html") 