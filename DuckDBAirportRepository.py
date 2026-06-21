import duckdb

from FlatAirportRepository import IAirportRepository


class DuckDBAirportRepository(IAirportRepository):
    """공항 테이블을 DuckDB로 관리하는 구현체. image_path 칼럼까지 같이 다룬다."""

    def __init__(self, con: duckdb.DuckDBPyConnection):
        self.con = con

    def save(self, data_list: list[dict]):
        for item in data_list:
            self.con.execute("DELETE FROM airports WHERE airport_code = ?", [item["airport_code"]])
            self.con.execute(
                "INSERT INTO airports (airport_code, airport_name, city, country, image_path) VALUES (?, ?, ?, ?, ?)",
                [
                    item["airport_code"],
                    item.get("airport_name"),
                    item.get("city"),
                    item.get("country"),
                    item.get("image_path"),
                ]
            )

    def find_by_code(self, airport_code: str) -> dict:
        row = self.con.execute(
            "SELECT airport_code, airport_name, city, country, image_path FROM airports WHERE airport_code = ?",
            [airport_code]
        ).fetchone()
        if row is None:
            return {}
        return {
            "airport_code": row[0], "airport_name": row[1], "city": row[2],
            "country": row[3], "image_path": row[4]
        }

    def find_all(self) -> list[dict]:
        rows = self.con.execute(
            "SELECT airport_code, airport_name, city, country, image_path FROM airports ORDER BY airport_code"
        ).fetchall()
        return [
            {"airport_code": r[0], "airport_name": r[1], "city": r[2], "country": r[3], "image_path": r[4]}
            for r in rows
        ]

    def find_by_conditions(self, city: str = None, country: str = None) -> list[dict]:
        query = "SELECT airport_code, airport_name, city, country, image_path FROM airports WHERE 1=1"
        params = []
        if city is not None:
            query += " AND city = ?"
            params.append(city)
        if country is not None:
            query += " AND country = ?"
            params.append(country)

        rows = self.con.execute(query, params).fetchall()
        return [
            {"airport_code": r[0], "airport_name": r[1], "city": r[2], "country": r[3], "image_path": r[4]}
            for r in rows
        ]

    def update(self, data_list: list[dict]):
        for item in data_list:
            self.con.execute(
                """
                UPDATE airports
                SET airport_name = ?, city = ?, country = ?, image_path = ?
                WHERE airport_code = ?
                """,
                [
                    item.get("airport_name"), item.get("city"), item.get("country"),
                    item.get("image_path"), item["airport_code"]
                ]
            )

    def delete_by_code(self, airport_code: str) -> bool:
        before = self.con.execute(
            "SELECT COUNT(*) FROM airports WHERE airport_code = ?", [airport_code]
        ).fetchone()[0]
        if before == 0:
            return False
        self.con.execute("DELETE FROM airports WHERE airport_code = ?", [airport_code])
        return True
