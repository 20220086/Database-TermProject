from abc import ABC, abstractmethod

class IAirlineRepository(ABC):
    @abstractmethod
    def save(self, data_list: list[dict]):
        """신규 항공사 정보 단건 등록 (CREATE) - Use Case 3.4"""
        pass
        
    @abstractmethod
    def find_by_id(self, airline_id: int) -> dict:
        """항공사 고유 번호로 단건 조회 (READ)"""
        pass
        
    @abstractmethod
    def find_all(self) -> list[dict]:
        """전체 항공사 목록 조회 (READ) - Use Case 3.1"""
        pass
        
    @abstractmethod
    def find_by_conditions(self, country: str = None, alliance: str = None) -> list[dict]:
        """허브 국가, 항공 동맹체 조건별 항공사 필터 조회 (READ) - Use Case 3.1"""
        pass
        
    @abstractmethod
    def update(self, data_list: list[dict]):
        """항공사 정보 수정 (UPDATE)"""
        pass
        
    @abstractmethod
    def delete_by_id(self, airline_id: int) -> bool:
        """항공사 정보 삭제 (DELETE)"""
        pass


class FlatAirlineRepository(IAirlineRepository):
    def __init__(self, data_list: list[dict] = None):
        # 딕셔너리 리스트 형태로 내부 데이터를 관리합니다.
        if data_list is not None:
            self.data = [item.copy() for item in data_list]
        else:
            self.data = []
            
    def save(self, data_list: list[dict]):
        # 중복 방지를 위해 기존 데이터에서 새로 추가될 airline_id를 가진 데이터는 미리 제거(덮어쓰기)
        new_ids = {item['airline_id'] for item in data_list}
        self.data = [item for item in self.data if item['airline_id'] not in new_ids]
        
        # 새 데이터 추가
        for item in data_list:
            self.data.append(item.copy())
        
    def find_by_id(self, airline_id: int) -> dict:
        # 조건에 맞는 첫 번째 아이템을 찾고, 없으면 빈 딕셔너리 반환
        for item in self.data:
            if item['airline_id'] == airline_id:
                return item.copy()
        return {}
        
    def find_all(self) -> list[dict]:
        # 원본 데이터 보호를 위해 복사본 반환
        return [item.copy() for item in self.data]
        
    def find_by_conditions(self, country: str = None, alliance: str = None) -> list[dict]:
        filtered_data = self.data
        
        if country is not None:
            filtered_data = [item for item in filtered_data if item.get('country') == country]
        if alliance is not None:
            filtered_data = [item for item in filtered_data if item.get('alliance') == alliance]
            
        return [item.copy() for item in filtered_data]
        
    def update(self, data_list: list[dict]):
        # 제공된 데이터 목록을 순회하며 기존 데이터 수정
        for new_item in data_list:
            for item in self.data:
                if item['airline_id'] == new_item['airline_id']:
                    # 일치하는 항목이 있으면 모든 키-값 업데이트
                    item.update(new_item)
                        
    def delete_by_id(self, airline_id: int) -> bool:
        initial_len = len(self.data)
        # 해당 ID가 아닌 데이터만 남겨서 삭제 처리
        self.data = [item for item in self.data if item['airline_id'] != airline_id]
        return len(self.data) < initial_len