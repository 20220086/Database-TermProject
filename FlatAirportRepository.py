from abc import ABC, abstractmethod

class IAirportRepository(ABC):
    @abstractmethod
    def save(self, data_list: list[dict]):
        """신규 공항 개설 등록 (CREATE) - Use Case 3.5"""
        pass
        
    @abstractmethod
    def find_by_code(self, airport_code: str) -> dict:
        """공항 3자리 코드(PK)로 단건 상세 조회 (READ) - Use Case 3.2.1 Triumph"""
        pass
        
    @abstractmethod
    def find_all(self) -> list[dict]:
        """전체 공항 목록 조회 (READ) - Use Case 3.2"""
        pass
        
    @abstractmethod
    def find_by_conditions(self, city: str = None, country: str = None) -> list[dict]:
        """도시, 국가 조건별 공항 필터 조회 (READ) - Use Case 3.2"""
        pass
        
    @abstractmethod
    def update(self, data_list: list[dict]):
        """공항 정보 수정 (UPDATE)"""
        pass
        
    @abstractmethod
    def delete_by_code(self, airport_code: str) -> bool:
        """공항 정보 삭제 (DELETE)"""
        pass


class FlatAirportRepository(IAirportRepository):
    def __init__(self, data_list: list[dict] = None):
        # 딕셔너리 리스트 형태로 내부 데이터를 관리합니다.
        if data_list is not None:
            self.data = [item.copy() for item in data_list]
        else:
            self.data = []
            
    def save(self, data_list: list[dict]):
        # 중복 방지를 위해 기존 데이터에서 새로 추가될 코드를 가진 데이터는 미리 제거(덮어쓰기 준비)
        new_codes = {item['airport_code'] for item in data_list}
        self.data = [item for item in self.data if item['airport_code'] not in new_codes]
        
        # 새 데이터 추가
        for item in data_list:
            self.data.append(item.copy())
        
    def find_by_code(self, airport_code: str) -> dict:
        # 조건에 맞는 첫 번째 아이템을 찾고, 없으면 빈 딕셔너리 반환
        for item in self.data:
            if item['airport_code'] == airport_code:
                return item.copy()
        return {}
        
    def find_all(self) -> list[dict]:
        # 원본 데이터 보호를 위해 복사본 반환
        return [item.copy() for item in self.data]
        
    def find_by_conditions(self, city: str = None, country: str = None) -> list[dict]:
        filtered_data = self.data
        
        if city is not None:
            filtered_data = [item for item in filtered_data if item.get('city') == city]
        if country is not None:
            filtered_data = [item for item in filtered_data if item.get('country') == country]
            
        return [item.copy() for item in filtered_data]
        
    def update(self, data_list: list[dict]):
        # 제공된 데이터 목록을 순회하며 기존 데이터 수정
        for new_item in data_list:
            for item in self.data:
                if item['airport_code'] == new_item['airport_code']:
                    # 일치하는 항목이 있으면 모든 키-값 업데이트
                    item.update(new_item)
                        
    def delete_by_code(self, airport_code: str) -> bool:
        initial_len = len(self.data)
        # 해당 코드가 아닌 데이터만 남겨서 삭제 처리
        self.data = [item for item in self.data if item['airport_code'] != airport_code]
        return len(self.data) < initial_len