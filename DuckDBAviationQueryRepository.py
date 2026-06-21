import duckdb

from FlatAviationQueryRepository import IAviationQueryRepository


# routes, airlines, airports(출발/도착 2번) 총 4개 테이블 참조를 조인해서 한 행으로 묶는 공통 SELECT.
# 결과 컬럼 순서를 _row_to_dict와 맞춰서 써야 한다.
_JOIN_SELECT = """
    SELECT
        r.route_id,
        r.airline_id,
        r.departure_airport,
        r.arrival_airport,
        r.aircraft,
        r.flight_time,
        al.airline_name,
        al.country,
        al.alliance,
        dep.airport_name AS departure_airport_name,
        dep.city AS departure_city,
        dep.country AS departure_country,
        arr.airport_name AS arrival_airport_name,
        arr.city AS arrival_city,
        arr.country AS arrival_country
    FROM routes r
    LEFT JOIN airlines al ON r.airline_id = al.airline_id
    LEFT JOIN airports dep ON r.departure_airport = dep.airport_code
    LEFT JOIN airports arr ON r.arrival_airport = arr.airport_code
"""


def _row_to_dict(row) -> dict:
    return {
        "route_id": row[0],
        "airline_id": row[1],
        "departure_airport": row[2],
        "arrival_airport": row[3],
        "aircraft": row[4],
        "flight_time": row[5],
        "airline_name": row[6],
        "country": row[7],
        "alliance": row[8],
        "departure_airport_name": row[9],
        "departure_city": row[10],
        "departure_country": row[11],
        "arrival_airport_name": row[12],
        "arrival_city": row[13],
        "arrival_country": row[14],
    }


class DuckDBAviationQueryRepository(IAviationQueryRepository):
    """3개 테이블(routes, airlines, airports)을 SQL JOIN으로 묶어서 조회하는 구현체.
    기존 FlatAviationQueryRepository는 파이썬에서 딕셔너리 맵을 만들어 조인을 흉내냈지만,
    여기서는 DuckDB의 LEFT JOIN을 그대로 사용한다."""

    def __init__(self, con: duckdb.DuckDBPyConnection):
        self.con = con

    def find_route_detail_with_join(self, route_id: int) -> list[dict]:
        rows = self.con.execute(_JOIN_SELECT + " WHERE r.route_id = ?", [route_id]).fetchall()
        return [_row_to_dict(r) for r in rows]

    def find_routes_by_airline_id(self, airline_id: int) -> list[dict]:
        rows = self.con.execute(_JOIN_SELECT + " WHERE r.airline_id = ?", [airline_id]).fetchall()
        return [_row_to_dict(r) for r in rows]

    def find_routes_by_airport_code(self, airport_code: str) -> list[dict]:
        rows = self.con.execute(
            _JOIN_SELECT + " WHERE r.departure_airport = ? OR r.arrival_airport = ?",
            [airport_code, airport_code]
        ).fetchall()
        return [_row_to_dict(r) for r in rows]

    def find_routes_by_filters(self, airline_name: str = None, departure_city: str = None, arrival_city: str = None) -> list[dict]:
        query = _JOIN_SELECT + " WHERE 1=1"
        params = []
        if airline_name is not None:
            query += " AND al.airline_name = ?"
            params.append(airline_name)
        if departure_city is not None:
            query += " AND dep.city = ?"
            params.append(departure_city)
        if arrival_city is not None:
            query += " AND arr.city = ?"
            params.append(arrival_city)
        query += " ORDER BY r.route_id"

        rows = self.con.execute(query, params).fetchall()
        return [_row_to_dict(r) for r in rows]
