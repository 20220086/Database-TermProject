"""
flight_data.json에 있던 데이터를 DuckDB 파일(flight.db)로 옮기는 스크립트.
처음 한 번만 실행하면 되고, 그 이후로는 main.py가 flight.db를 직접 사용한다.

실행:
    python migrate_json_to_duckdb.py
"""
import json
import os
import duckdb

current_dir = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(current_dir, "flight_data.json")
db_path = os.path.join(current_dir, "flight.db")


def create_tables(con: duckdb.DuckDBPyConnection):
    # 항공사 테이블
    con.execute("""
        CREATE TABLE IF NOT EXISTS airlines (
            airline_id INTEGER PRIMARY KEY,
            airline_name VARCHAR,
            country VARCHAR,
            alliance VARCHAR
        )
    """)

    # 공항 테이블 - image_path는 신규 공항 등록할 때 같이 저장되는 칼럼
    con.execute("""
        CREATE TABLE IF NOT EXISTS airports (
            airport_code VARCHAR PRIMARY KEY,
            airport_name VARCHAR,
            city VARCHAR,
            country VARCHAR,
            image_path VARCHAR
        )
    """)

    # 운항 노선 테이블 - airlines, airports를 참조하는 외래키 보유
    con.execute("""
        CREATE TABLE IF NOT EXISTS routes (
            route_id INTEGER PRIMARY KEY,
            airline_id INTEGER,
            departure_airport VARCHAR,
            arrival_airport VARCHAR,
            aircraft VARCHAR,
            flight_time DOUBLE,
            FOREIGN KEY (airline_id) REFERENCES airlines(airline_id),
            FOREIGN KEY (departure_airport) REFERENCES airports(airport_code),
            FOREIGN KEY (arrival_airport) REFERENCES airports(airport_code)
        )
    """)


def load_json_data():
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def migrate():
    if os.path.exists(db_path):
        print(f"⚠️ {db_path} 가 이미 존재합니다. 기존 파일을 지우고 새로 만듭니다.")
        os.remove(db_path)

    con = duckdb.connect(db_path)
    create_tables(con)

    data = load_json_data()

    for a in data.get("airlines", []):
        con.execute(
            "INSERT INTO airlines VALUES (?, ?, ?, ?)",
            [a["airline_id"], a["airline_name"], a.get("country"), a.get("alliance")]
        )

    for ap in data.get("airports", []):
        con.execute(
            "INSERT INTO airports VALUES (?, ?, ?, ?, ?)",
            [ap["airport_code"], ap.get("airport_name"), ap.get("city"), ap.get("country"), ap.get("image_path")]
        )

    for r in data.get("routes", []):
        con.execute(
            "INSERT INTO routes VALUES (?, ?, ?, ?, ?, ?)",
            [r["route_id"], r["airline_id"], r["departure_airport"], r["arrival_airport"], r.get("aircraft"), r.get("flight_time")]
        )

    airline_count = con.execute("SELECT COUNT(*) FROM airlines").fetchone()[0]
    airport_count = con.execute("SELECT COUNT(*) FROM airports").fetchone()[0]
    route_count = con.execute("SELECT COUNT(*) FROM routes").fetchone()[0]

    con.close()

    print(f"✅ 마이그레이션 완료: airlines={airline_count}, airports={airport_count}, routes={route_count}")
    print(f"✅ DB 파일 위치: {db_path}")


if __name__ == "__main__":
    migrate()
