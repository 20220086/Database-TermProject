import duckdb

from FlatFlightRouteRepository import IFlightRouteRepository


class DuckDBFlightRouteRepository(IFlightRouteRepository):
    """운항 노선 테이블을 DuckDB로 관리하는 구현체."""

    def __init__(self, con: duckdb.DuckDBPyConnection):
        self.con = con

    def save(self, data_list: list[dict]):
        for item in data_list:
            self.con.execute("DELETE FROM routes WHERE route_id = ?", [item["route_id"]])
            self.con.execute(
                """
                INSERT INTO routes (route_id, airline_id, departure_airport, arrival_airport, aircraft, flight_time)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    item["route_id"], item["airline_id"], item["departure_airport"],
                    item["arrival_airport"], item.get("aircraft"), item.get("flight_time")
                ]
            )

    def find_by_id(self, route_id: int) -> dict:
        row = self.con.execute(
            """
            SELECT route_id, airline_id, departure_airport, arrival_airport, aircraft, flight_time
            FROM routes WHERE route_id = ?
            """,
            [route_id]
        ).fetchone()
        if row is None:
            return {}
        return self._row_to_dict(row)

    def find_all(self) -> list[dict]:
        rows = self.con.execute(
            """
            SELECT route_id, airline_id, departure_airport, arrival_airport, aircraft, flight_time
            FROM routes ORDER BY route_id
            """
        ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def update(self, data_list: list[dict]):
        for item in data_list:
            self.con.execute(
                """
                UPDATE routes
                SET airline_id = ?, departure_airport = ?, arrival_airport = ?, aircraft = ?, flight_time = ?
                WHERE route_id = ?
                """,
                [
                    item.get("airline_id"), item.get("departure_airport"), item.get("arrival_airport"),
                    item.get("aircraft"), item.get("flight_time"), item["route_id"]
                ]
            )

    def delete_by_id(self, route_id: int) -> bool:
        before = self.con.execute("SELECT COUNT(*) FROM routes WHERE route_id = ?", [route_id]).fetchone()[0]
        if before == 0:
            return False
        self.con.execute("DELETE FROM routes WHERE route_id = ?", [route_id])
        return True

    @staticmethod
    def _row_to_dict(row) -> dict:
        return {
            "route_id": row[0],
            "airline_id": row[1],
            "departure_airport": row[2],
            "arrival_airport": row[3],
            "aircraft": row[4],
            "flight_time": row[5],
        }
