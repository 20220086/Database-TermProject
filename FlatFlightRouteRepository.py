from abc import ABC, abstractmethod

class IFlightRouteRepository(ABC):
    @abstractmethod
    def save(self, data_list: list[dict]):
        """신규 운항 노선 스케줄 등록 (CREATE) - Use Case 3.5"""
        pass
        
    @abstractmethod
    def find_by_id(self, route_id: int) -> dict:
        """노선 고유 번호로 단건 조회 (READ)"""
        pass
        
    @abstractmethod
    def find_all(self) -> list[dict]:
        """전체 운항 노선 목록 조회 (READ) - Use Case 3.3"""
        pass
        
    @abstractmethod
    def update(self, data_list: list[dict]):
        """노선의 항공기 기종 및 운항 시간 정보 수정 (UPDATE) - Use Case 3.6"""
        pass
        
    @abstractmethod
    def delete_by_id(self, route_id: int) -> bool:
        """특정 운항 노선 안전 삭제 (DELETE) - Use Case 3.7"""
        pass


class FlatFlightRouteRepository(IFlightRouteRepository):
    def __init__(self, data_list: list[dict] = None):
        # 딕셔너리 리스트 형태로 내부 데이터를 관리합니다.
        if data_list is not None:
            self.data = [item.copy() for item in data_list]
        else:
            self.data = []
            
    def save(self, data_list: list[dict]):
        # 중복 방지를 위해 기존 데이터에서 새로 추가될 route_id를 가진 데이터는 미리 제거(덮어쓰기)
        new_ids = {item['route_id'] for item in data_list}
        self.data = [item for item in self.data if item['route_id'] not in new_ids]
        
        # 새 데이터 추가
        for item in data_list:
            self.data.append(item.copy())
        
    def find_by_id(self, route_id: int) -> dict:
        # 조건에 맞는 첫 번째 아이템을 찾고, 없으면 빈 딕셔너리 반환
        for item in self.data:
            if item['route_id'] == route_id:
                return item.copy()
        return {}
        
    def find_all(self) -> list[dict]:
        # 원본 데이터 보호를 위해 복사본 반환
        return [item.copy() for item in self.data]
        
    def update(self, data_list: list[dict]):
        # 제공된 데이터 목록을 순회하며 기존 데이터 수정
        for new_item in data_list:
            for item in self.data:
                if item['route_id'] == new_item['route_id']:
                    # 일치하는 항목이 있으면 모든 키-값 업데이트
                    item.update(new_item)
                        
    def delete_by_id(self, route_id: int) -> bool:
        initial_len = len(self.data)
        # 해당 ID가 아닌 데이터만 남겨서 삭제 처리
        self.data = [item for item in self.data if item['route_id'] != route_id]
        return len(self.data) < initial_len