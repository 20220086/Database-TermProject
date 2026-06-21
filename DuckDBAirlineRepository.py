import duckdb

from IAirlineRepository import IAirlineRepository


class DuckDBAirlineRepository(IAirlineRepository):
    """항공사 테이블을 DuckDB로 관리하는 구현체. 메서드 시그니처는 FlatAirlineRepository와 동일하게 맞춰서
    main.py 쪽 호출 코드는 손댈 필요가 없도록 했다."""

    def __init__(self, con: duckdb.DuckDBPyConnection):
        self.con = con

    def save(self, data_list: list[dict]):
        # 기존에 같은 airline_id가 있으면 지우고 새로 넣는 방식(덮어쓰기)으로 구버전과 동작을 맞춤
        for item in data_list:
            self.con.execute("DELETE FROM airlines WHERE airline_id = ?", [item["airline_id"]])
            self.con.execute(
                "INSERT INTO airlines (airline_id, airline_name, country, alliance) VALUES (?, ?, ?, ?)",
                [item["airline_id"], item.get("airline_name"), item.get("country"), item.get("alliance")]
            )

    def find_by_id(self, airline_id: int) -> dict:
        row = self.con.execute(
            "SELECT airline_id, airline_name, country, alliance FROM airlines WHERE airline_id = ?",
            [airline_id]
        ).fetchone()
        if row is None:
            return {}
        return {"airline_id": row[0], "airline_name": row[1], "country": row[2], "alliance": row[3]}

    def find_all(self) -> list[dict]:
        rows = self.con.execute(
            "SELECT airline_id, airline_name, country, alliance FROM airlines ORDER BY airline_id"
        ).fetchall()
        return [
            {"airline_id": r[0], "airline_name": r[1], "country": r[2], "alliance": r[3]}
            for r in rows
        ]

    def find_by_conditions(self, country: str = None, alliance: str = None) -> list[dict]:
        query = "SELECT airline_id, airline_name, country, alliance FROM airlines WHERE 1=1"
        params = []
        if country is not None:
            query += " AND country = ?"
            params.append(country)
        if alliance is not None:
            query += " AND alliance = ?"
            params.append(alliance)

        rows = self.con.execute(query, params).fetchall()
        return [
            {"airline_id": r[0], "airline_name": r[1], "country": r[2], "alliance": r[3]}
            for r in rows
        ]

    def update(self, data_list: list[dict]):
        for item in data_list:
            self.con.execute(
                """
                UPDATE airlines
                SET airline_name = ?, country = ?, alliance = ?
                WHERE airline_id = ?
                """,
                [item.get("airline_name"), item.get("country"), item.get("alliance"), item["airline_id"]]
            )

    def delete_by_id(self, airline_id: int) -> bool:
        before = self.con.execute("SELECT COUNT(*) FROM airlines WHERE airline_id = ?", [airline_id]).fetchone()[0]
        if before == 0:
            return False
        self.con.execute("DELETE FROM airlines WHERE airline_id = ?", [airline_id])
        return True
