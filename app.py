import flet as ft
import os
import shutil
import uuid
import duckdb

def main(page: ft.Page):
    page.title = "항공 운항 정보 시스템 (Aviation System)"
    page.padding = 20
    page.theme_mode = ft.ThemeMode.LIGHT

    # DuckDB 파일 연결 - flight.db가 없으면 migrate_json_to_duckdb.py를 먼저 한 번 실행해야 함
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(current_dir, "flight.db")

    if not os.path.exists(db_path):
        raise FileNotFoundError(
            f"{db_path} 가 없습니다. 먼저 'python migrate_json_to_duckdb.py'를 실행해서 DB를 만들어 주세요."
        )

    con = duckdb.connect(db_path)
    print(f"✅ DuckDB에 연결했습니다: {db_path}")

    # 업로드한 공항 이미지를 저장할 폴더 (assets/airport_images)
    assets_dir = os.path.join(current_dir, "assets")
    images_dir_name = "airport_images"
    images_dir_path = os.path.join(assets_dir, images_dir_name)
    os.makedirs(images_dir_path, exist_ok=True)

    # 레포지토리 초기화 - 전부 같은 DuckDB 커넥션을 공유해서 사용
    from DuckDBAirlineRepository import DuckDBAirlineRepository
    from DuckDBAirportRepository import DuckDBAirportRepository
    from DuckDBFlightRouteRepository import DuckDBFlightRouteRepository
    from DuckDBAviationQueryRepository import DuckDBAviationQueryRepository

    airline_repo = DuckDBAirlineRepository(con)
    airport_repo = DuckDBAirportRepository(con)
    route_repo = DuckDBFlightRouteRepository(con)
    query_repo = DuckDBAviationQueryRepository(con)

    # 드롭다운, 화면 표시용으로 들고 있는 캐시. 실제 저장은 DuckDB가 하고,
    # 여기는 매번 DB에서 다시 읽어와서 채워주는 화면용 사본일 뿐이다.
    sample_airlines = airline_repo.find_all()
    sample_airports = airport_repo.find_all()
    sample_routes = route_repo.find_all()
    print(f"✅ 데이터를 성공적으로 불러왔습니다. (노선 수: {len(sample_routes)}개)")

    active_routes_cache = {}

    # 공항 이미지 선택용 FilePicker
    airport_image_picker = ft.FilePicker()
    page.overlay.append(airport_image_picker)

    # UI 컴포넌트 생성
    title_text = ft.Text("✈️ 항공 운항 정보 관리 시스템", size=28, weight=ft.FontWeight.BOLD)

    input_airline = ft.TextField(label="항공사 필터", width=180)
    input_dep_code = ft.TextField(label="출발공항코드 필터", width=180)

    add_route_id = ft.TextField(label="노선 ID", width=100)
    add_airline_dropdown = ft.Dropdown(label="항공사 선택", width=180)
    add_dep_dropdown = ft.Dropdown(label="출발공항 선택", width=150)
    add_arr_dropdown = ft.Dropdown(label="도착공항 선택", width=150)
    add_aircraft = ft.TextField(label="항공기 기종", width=110)
    add_flight_time = ft.TextField(label="운항시간 (시간)", width=100)

    def update_dropdown_options():
        add_airline_dropdown.options = [
            ft.dropdown.Option(key=str(al.get("airline_id")), text=al.get("airline_name"))
            for al in sample_airlines
        ]
        airport_options = [
            ft.dropdown.Option(key=ap.get("airport_code"), text=f"{ap.get('airport_code')} ({ap.get('airport_name', '')})")
            for ap in sample_airports
        ]
        add_dep_dropdown.options = airport_options
        add_arr_dropdown.options = airport_options
        page.update()

    data_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("노선")),
            ft.DataColumn(ft.Text("항공사")),
            ft.DataColumn(ft.Text("출발공항코드")),
            ft.DataColumn(ft.Text("도착공항코드")),
            ft.DataColumn(ft.Text("항공기")),
            ft.DataColumn(ft.Text("운항시간")),
            ft.DataColumn(ft.Text("관리")),
        ],
        rows=[]
    )

    # DuckDB는 각 repo의 save()/delete_by_id() 호출 시점에 바로 반영되므로
    # 기존처럼 따로 파일에 일괄 저장하는 함수가 필요 없다.

    # 지금 열려있는 다이얼로그를 기억해뒀다가 닫기 버튼 눌렸을 때 사용
    current_dialog_ref = {"dialog": None}

    def close_dialog(e):
        print(">>> [DEBUG] close_dialog 호출됨")
        if current_dialog_ref["dialog"]:
            page.close(current_dialog_ref["dialog"])

    # 노선 ID 버튼 클릭하면 상세 팝업 띄우는 핸들러
    def on_route_click(e):
        print(">>> [DEBUG] on_route_click 진입함, e.control.data =", e.control.data)
        try:
            target_route_id = e.control.data
            route_data = active_routes_cache.get(target_route_id)
            print(">>> [DEBUG] active_routes_cache에서 찾은 route_data:", route_data)

            if not route_data:
                print(f"⚠️ 캐시에서 노선 ID {target_route_id}의 데이터를 찾을 수 없습니다.")
                return

            r_id = str(route_data.get('route_id', target_route_id))
            airline_name = str(route_data.get('airline_name', route_data.get('airline_id', '미지정')))

            dep_code = str(route_data.get('departure_airport', '미지정'))
            dep_name = route_data.get('departure_airport_name')
            dep_city = route_data.get('departure_city')

            arr_code = str(route_data.get('arrival_airport', '미지정'))
            arr_name = route_data.get('arrival_airport_name')
            arr_city = route_data.get('arrival_city')

            aircraft = str(route_data.get('aircraft', '미지정'))
            flight_time = f"{route_data.get('flight_time', 0)}시간"

            dep_info = f"{dep_code}"
            if dep_name or dep_city:
                dep_info += f" - {dep_name or ''} ({dep_city or ''})".replace(" ()", "")

            arr_info = f"{arr_code}"
            if arr_name or arr_city:
                arr_info += f" - {arr_name or ''} ({arr_city or ''})".replace(" ()", "")

            # 출발 공항 코드에 매핑된 이미지 경로를 찾아서 띄워줌
            airport_img_url = "https://images.unsplash.com/photo-1436491865332-7a61a109cc05?q=80&w=400"  # 매칭 안되면 기본 이미지
            for ap in sample_airports:
                if ap.get("airport_code") == dep_code and ap.get("image_path"):
                    img_path = ap.get("image_path")
                    # http(s) URL이면 그대로, 아니면 assets 내 로컬 경로로 처리
                    if img_path.startswith("http://") or img_path.startswith("https://"):
                        airport_img_url = img_path
                    else:
                        airport_img_url = f"/{img_path}"
                    break

            print(">>> [DEBUG] 사용할 이미지 URL:", airport_img_url)

            airport_image = ft.Image(
                src=airport_img_url,
                width=350,
                height=180,
                fit=ft.ImageFit.COVER,
                border_radius=8,
                error_content=ft.Text("이미지를 불러올 수 없습니다", size=12, color="grey500"),
            )

            detail_dialog = ft.AlertDialog(
                title=ft.Text(f"📋 노선 상세 정보 (ID: {r_id})", size=20, weight=ft.FontWeight.BOLD),
                content=ft.Column([
                    airport_image,
                    ft.Container(height=5),
                    ft.Text(f"• 운항 항공사: {airline_name}", size=14),
                    ft.Text(f"• 출발 공항: {dep_info}", size=14),
                    ft.Text(f"• 도착 공항: {arr_info}", size=14),
                    ft.Text(f"• 배정 항공기: {aircraft}", size=14),
                    ft.Text(f"• 총 운항시간: {flight_time}", size=14),
                ], tight=True, width=350, height=350),
                actions=[
                    ft.TextButton(content=ft.Text("닫기"), on_click=close_dialog)
                ],
            )
            print(">>> [DEBUG] show_dialog 호출 직전")
            current_dialog_ref["dialog"] = detail_dialog
            page.open(detail_dialog)
            print(">>> [DEBUG] show_dialog 호출 완료 (에러 없음)")

        except Exception as err:
            print(f"❌ 팝업창 렌더링 중 에러 발생: {err}")
            import traceback
            traceback.print_exc()

    def load_data(e=None):
        try:
            airline_name = input_airline.value.strip() if input_airline.value and input_airline.value.strip() else None
            departure_code = input_dep_code.value.strip() if input_dep_code.value and input_dep_code.value.strip() else None

            data_list = query_repo.find_routes_by_filters(airline_name=airline_name, departure_city=departure_code)

            if not data_list and not airline_name and not departure_code:
                data_list = sample_routes

            data_table.rows.clear()
            active_routes_cache.clear()

            if data_list:
                for row in data_list:
                    r_id = row.get('route_id')
                    route_id_str = str(r_id)

                    active_routes_cache[route_id_str] = dict(row)

                    airline = str(row.get('airline_name', row.get('airline_id', '미지정')))
                    dep_code = row.get('departure_airport', '미지정')
                    arr_code = row.get('arrival_airport', '미지정')
                    aircraft = str(row.get('aircraft', '미지정'))
                    flight_time = f"{row.get('flight_time', 0)}시간"

                    delete_btn = ft.IconButton(
                        icon=ft.Icons.DELETE,
                        icon_color="red400",
                        data=r_id,
                        on_click=delete_data
                    )

                    route_click_btn = ft.TextButton(
                        content=ft.Text(route_id_str, color="blue", weight=ft.FontWeight.BOLD),
                        data=route_id_str,
                        on_click=on_route_click
                    )

                    data_table.rows.append(
                        ft.DataRow(
                            cells=[
                                ft.DataCell(route_click_btn),
                                ft.DataCell(ft.Text(airline)),
                                ft.DataCell(ft.Text(dep_code)),
                                ft.DataCell(ft.Text(arr_code)),
                                ft.DataCell(ft.Text(aircraft)),
                                ft.DataCell(ft.Text(flight_time)),
                                ft.DataCell(delete_btn),
                            ]
                        )
                    )
                print(f">>> [DEBUG] load_data 완료, active_routes_cache 키 목록: {list(active_routes_cache.keys())}")
            if page.controls:
                page.update()
        except Exception as err:
            print(f"❌ 데이터 매핑 중 에러 발생: {err}")
            import traceback
            traceback.print_exc()

    def add_data(e):
        try:
            new_route = {
                'route_id': int(add_route_id.value),
                'airline_id': int(add_airline_dropdown.value),
                'departure_airport': add_dep_dropdown.value,
                'arrival_airport': add_arr_dropdown.value,
                'aircraft': add_aircraft.value.strip(),
                'flight_time': float(add_flight_time.value)
            }

            route_repo.save([new_route])
            sample_routes.append(new_route)  # 드롭다운 등 화면 캐시 갱신용

            add_route_id.value = ""
            add_airline_dropdown.value = None
            add_dep_dropdown.value = None
            add_arr_dropdown.value = None
            add_aircraft.value = ""
            add_flight_time.value = ""

            load_data()
        except Exception as err:
            print(f"❌ 데이터 추가 에러: {err}")
            import traceback
            traceback.print_exc()

    def delete_data(e):
        target_id = e.control.data
        if target_id:
            route_repo.delete_by_id(target_id)
            nonlocal sample_routes
            sample_routes = [r for r in sample_routes if r.get('route_id') != target_id]
            load_data()

    def open_add_airline_dialog(e):
        print(">>> [DEBUG] open_add_airline_dialog 진입함")
        new_al_id = ft.TextField(label="항공사 ID (숫자)")
        new_al_name = ft.TextField(label="항공사명")

        def save_airline(ev):
            new_airline = {"airline_id": int(new_al_id.value), "airline_name": new_al_name.value.strip()}
            airline_repo.save([new_airline])
            sample_airlines.append(new_airline)
            update_dropdown_options()
            page.close(dialog)

        dialog = ft.AlertDialog(
            title=ft.Text("✈️ 신규 항공사 등록"),
            content=ft.Column([new_al_id, new_al_name], tight=True),
            actions=[
                ft.TextButton(content=ft.Text("저장"), on_click=save_airline),
                ft.TextButton(content=ft.Text("취소"), on_click=close_dialog)
            ]
        )
        print(">>> [DEBUG] open_add_airline_dialog: show_dialog 호출 직전")
        current_dialog_ref["dialog"] = dialog
        page.open(dialog)
        print(">>> [DEBUG] open_add_airline_dialog: show_dialog 호출 완료")

    # 신규 공항 등록 다이얼로그 - PC에서 이미지 골라서 assets 폴더로 복사해 저장
    def open_add_airport_dialog(e):
        print(">>> [DEBUG] open_add_airport_dialog 진입함")
        new_ap_code = ft.TextField(label="공항 코드 (3자리 대문자)")
        new_ap_name = ft.TextField(label="공항명")
        new_ap_city = ft.TextField(label="도시명")

        # 선택한 이미지의 상대 경로(assets/airport_images/xxxx.jpg)를 들고 있을 상태값
        selected_image_state = {"relative_path": None}

        # 선택 결과 보여줄 텍스트랑 미리보기 이미지
        selected_image_label = ft.Text("선택된 이미지 없음", size=12, color="grey600")
        image_preview = ft.Image(
            src="",
            width=200,
            height=110,
            fit=ft.ImageFit.COVER,
            visible=False,
            border_radius=6,
        )

        # 파일 선택 결과 처리 - 고른 이미지를 assets 폴더로 복사
        def on_image_picked(ev: ft.FilePickerResultEvent):
            if not ev.files:
                return
            picked = ev.files[0]
            source_path = picked.path  # 데스크톱 환경에서만 실제 경로가 내려옴

            if not source_path:
                selected_image_label.value = "⚠️ 파일 경로를 가져올 수 없습니다 (웹 모드에서는 지원되지 않음)"
                selected_image_label.color = "red400"
                page.update()
                return

            # 확장자는 유지하고 파일명은 겹치지 않게 새로 생성
            _, ext = os.path.splitext(picked.name)
            new_filename = f"{uuid.uuid4().hex}{ext}"
            dest_path = os.path.join(images_dir_path, new_filename)

            try:
                shutil.copy(source_path, dest_path)
            except Exception as copy_err:
                selected_image_label.value = f"⚠️ 이미지 복사 실패: {copy_err}"
                selected_image_label.color = "red400"
                page.update()
                return

            # JSON에는 실제 파일이 아니라 "airport_images/파일명" 상대 경로만 저장
            relative_path = f"{images_dir_name}/{new_filename}"
            selected_image_state["relative_path"] = relative_path

            selected_image_label.value = f"✅ 선택됨: {picked.name}"
            selected_image_label.color = "green700"
            image_preview.src = f"/{images_dir_name}/{new_filename}"
            image_preview.visible = True
            page.update()

        # 이전 다이얼로그에서 등록된 핸들러가 남아있을 수 있으니 매번 새로 갈아끼움
        airport_image_picker.on_result = on_image_picked

        pick_image_btn = ft.ElevatedButton(
            "🖼️ PC에서 이미지 선택",
            on_click=lambda ev: airport_image_picker.pick_files(
                dialog_title="공항 이미지 선택",
                allow_multiple=False,
                file_type=ft.FilePickerFileType.IMAGE,
            ),
        )

        def save_airport(ev):
            new_airport = {
                "airport_code": new_ap_code.value.strip().upper(),
                "airport_name": new_ap_name.value.strip(),
                "city": new_ap_city.value.strip(),
                # DB에는 이미지 파일 자체가 아니라 경로 문자열만 들어감
                "image_path": selected_image_state["relative_path"] or ""
            }
            airport_repo.save([new_airport])
            sample_airports.append(new_airport)
            update_dropdown_options()
            page.close(dialog)

        def cancel_airport(ev):
            close_dialog(ev)

        dialog = ft.AlertDialog(
            title=ft.Text("🏢 신규 공항 등록"),
            content=ft.Column([
                new_ap_code,
                new_ap_name,
                new_ap_city,
                ft.Container(height=8),
                ft.Row([pick_image_btn]),
                selected_image_label,
                image_preview,
            ], tight=True, width=320, scroll=ft.ScrollMode.AUTO),
            actions=[
                ft.TextButton(content=ft.Text("저장"), on_click=save_airport),
                ft.TextButton(content=ft.Text("취소"), on_click=cancel_airport)
            ]
        )
        print(">>> [DEBUG] open_add_airport_dialog: show_dialog 호출 직전")
        current_dialog_ref["dialog"] = dialog
        page.open(dialog)
        print(">>> [DEBUG] open_add_airport_dialog: show_dialog 호출 완료")

    search_button = ft.ElevatedButton("조회하기", icon=ft.Icons.SEARCH, on_click=load_data)
    add_button = ft.ElevatedButton("신규 노선 등록", icon=ft.Icons.ADD, on_click=add_data, bgcolor="lightblue", color="black")

    btn_add_airline = ft.ElevatedButton("➕ 신규 항공사 등록", on_click=open_add_airline_dialog)
    btn_add_airport = ft.ElevatedButton("➕ 신규 공항 등록", on_click=open_add_airport_dialog)

    # 레이아웃 배치
    filter_row = ft.Row([input_airline, input_dep_code, search_button], spacing=10)
    add_form_row = ft.Row([
        add_route_id, add_airline_dropdown, add_dep_dropdown, add_arr_dropdown, add_aircraft, add_flight_time, add_button
    ], spacing=8, wrap=True)

    master_admin_row = ft.Row([btn_add_airline, btn_add_airport], spacing=15)

    table_container = ft.Column(
        [
            ft.Text("조회 결과 (파란색 노선 ID 버튼을 누르면 상세 팝업이 항상 열립니다)", size=14, color="grey600"),
            ft.Row([data_table], scroll=ft.ScrollMode.AUTO)
        ],
        scroll=ft.ScrollMode.AUTO,
        expand=True
    )

    page.add(
        title_text,
        ft.Divider(),
        ft.Text("🔍 필터 조회", size=16, weight=ft.FontWeight.BOLD),
        filter_row,
        ft.Divider(),
        ft.Text("⚙️ 기초 데이터 관리 (4.3 / 4.4)", size=16, weight=ft.FontWeight.BOLD),
        master_admin_row,
        ft.Divider(),
        ft.Text("➕ 신규 운항 노선 추가 (우측 항목 선택 가능)", size=16, weight=ft.FontWeight.BOLD),
        add_form_row,
        ft.Divider(),
        table_container
    )

    update_dropdown_options()
    load_data()

if __name__ == "__main__":
    # main.py와 같은 위치의 assets 폴더를 정적 파일 루트로 사용
    ft.app(target=main, assets_dir="assets")
