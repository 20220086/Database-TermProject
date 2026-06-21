from abc import ABC, abstractmethod

from IAirlineRepository import FlatAirlineRepository
from FlatAirportRepository import FlatAirportRepository
from FlatFlightRouteRepository import FlatFlightRouteRepository

class IAviationQueryRepository(ABC):
    @abstractmethod
    def find_route_detail_with_join(self, route_id: int) -> list[dict]:
        """FlightRoutes, Airlines, Airports 다중 조인 조회"""
        pass
        
    @abstractmethod
    def find_routes_by_airline_id(self, airline_id: int) -> list[dict]:
        """특정 항공사가 보유한 운항 노선 목록 조회"""
        pass
        
    @abstractmethod
    def find_routes_by_airport_code(self, airport_code: str) -> list[dict]:
        """특정 공항을 출발지 또는 도착지로 하는 운항 노선 목록 조회"""
        pass
        
    @abstractmethod
    def find_routes_by_filters(self, airline_name: str = None, departure_city: str = None, arrival_city: str = None) -> list[dict]:
        """항공사명, 출발지, 도착지 조건에 매칭되는 운항 노선 필터 조회"""
        pass


class FlatAviationQueryRepository(IAviationQueryRepository):
    def __init__(self, airline_repo: FlatAirlineRepository, airport_repo: FlatAirportRepository, route_repo: FlatFlightRouteRepository):
        self.airline_repo = airline_repo
        self.airport_repo = airport_repo
        self.route_repo = route_repo
        
    def _get_joined_data(self, routes: list[dict]) -> list[dict]:
        """판다스의 pd.merge(how='left')를 대신하여 다중 조인을 수행하는 내부 헬퍼 메서드"""
        # 빠른 조인을 위해 항공사와 공항 데이터를 딕셔너리(ID/Code: 데이터) 맵으로 변환합니다.
        airlines_map = {a['airline_id']: a for a in self.airline_repo.find_all()}
        airports_map = {a['airport_code']: a for a in self.airport_repo.find_all()}
        
        joined_results = []
        for r in routes:
            # 원본 노선 데이터 복사
            merged_row = r.copy()
            
            # 1. Airline 조인
            airline_info = airlines_map.get(merged_row.get('airline_id'))
            if airline_info:
                # 필요한 항공사 정보 병합
                merged_row['airline_name'] = airline_info.get('airline_name')
                merged_row['country'] = airline_info.get('country')
                merged_row['alliance'] = airline_info.get('alliance')
                
            # 2. 출발 공항 조인 (컬럼명 변경 규칙 적용)
            dep_info = airports_map.get(merged_row.get('departure_airport'))
            if dep_info:
                merged_row['departure_airport_name'] = dep_info.get('airport_name')
                merged_row['departure_city'] = dep_info.get('city')
                merged_row['departure_country'] = dep_info.get('country')
                
            # 3. 도착 공항 조인 (컬럼명 변경 규칙 적용)
            arr_info = airports_map.get(merged_row.get('arrival_airport'))
            if arr_info:
                merged_row['arrival_airport_name'] = arr_info.get('airport_name')
                merged_row['arrival_city'] = arr_info.get('city')
                merged_row['arrival_country'] = arr_info.get('country')
                
            joined_results.append(merged_row)
            
        return joined_results

    def find_route_detail_with_join(self, route_id: int) -> list[dict]:
        routes = self.route_repo.find_all()
        # 단건 필터링
        target_route = [r for r in routes if r.get('route_id') == route_id]
        
        if not target_route:
            return []
            
        return self._get_joined_data(target_route)
        
    def find_routes_by_airline_id(self, airline_id: int) -> list[dict]:
        routes = self.route_repo.find_all()
        # 특정 항공사 필터링
        filtered_routes = [r for r in routes if r.get('airline_id') == airline_id]
        
        if not filtered_routes:
            return []
            
        # 항공사 조인만 필요하므로 전체 조인 로직 재활용 또는 간단하게 반환
        return self._get_joined_data(filtered_routes)
        
    def find_routes_by_airport_code(self, airport_code: str) -> list[dict]:
        routes = self.route_repo.find_all()
        # 출발지 또는 도착지 공항코드 매칭
        return [r for r in routes if r.get('departure_airport') == airport_code or r.get('arrival_airport') == airport_code]
        
    def find_routes_by_filters(self, airline_name: str = None, departure_city: str = None, arrival_city: str = None) -> list[dict]:
        routes = self.route_repo.find_all()
        
        # 우선 전체 다중 조인을 수행합니다.
        merged_list = self._get_joined_data(routes)
        
        # 조건별 필터링 진행 (리스트 컴프리헨션)
        if airline_name is not None:
            merged_list = [r for r in merged_list if r.get('airline_name') == airline_name]
        if departure_city is not None:
            merged_list = [r for r in merged_list if r.get('departure_city') == departure_city]
        if arrival_city is not None:
            merged_list = [r for r in merged_list if r.get('arrival_city') == arrival_city]
            
        return merged_list