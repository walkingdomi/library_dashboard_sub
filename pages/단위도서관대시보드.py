from datetime import timedelta
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go
import requests
from datetime import datetime
from math import radians, cos, sin, asin, sqrt

# 카카오 REST API 키
KAKAO_REST_API_KEY = "933978dff78eafd4230e6e06e5fb764c"

st.set_page_config(
    page_title="서울시 공공도서관 대시보드",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.title("📚 서울시 개별도서관 별 현황")

tab1, tab2 = None, None  # placeholder for tabs, will define after dropdowns

df_libcode = pd.read_csv("./libnamecode.csv", encoding='utf-8-sig')

# 🔹 데이터 로드
@st.cache_data(ttl=3600)
def load_data():
    df_library = pd.read_csv("./Seoul_Public_Library_2km_Buffer.csv", encoding='utf-8-sig')
    df_pop = pd.read_csv("./2_population_and_senior.csv", encoding='utf-8-sig', na_values='-')
    df_gender = pd.read_csv("./3_gender.csv", encoding='utf-8-sig', na_values='-')
    welfare_df = pd.read_csv("./5_number_of_recipients.csv", encoding='utf-8-sig')
    return df_library, df_pop, df_gender, welfare_df

df_library, df_pop, df_gender, welfare_df = load_data()
df_gender[['남자', '여자']] = df_gender[['남자', '여자']].apply(pd.to_numeric, errors='coerce').fillna(0)
df_pop.iloc[:, 2:] = df_pop.iloc[:, 2:].apply(pd.to_numeric, errors='coerce')

# 🔹 자치구 & 도서관 선택 (탭 위로 이동)
# 자치구 이름 필터링 (구로 끝나는 것만 선택)
gu_list = sorted([x for x in df_library['자치구'].dropna().unique() if x.endswith('구')])
default_gu = '강남구'
col1, col2 = st.columns(2)
with col1:
    selected_gu = st.selectbox("자치구 선택", gu_list, index=gu_list.index(default_gu))
with col2:
    library_list = sorted(df_library[df_library['자치구'] == selected_gu]['도서관명'].dropna().unique())
    selected_library = st.selectbox("도서관 선택", library_list)
    
tab1, tab2 = st.tabs(["🏛 개별도서관 현황", "📖 정보나루"])

with tab1:
    # 현재 달 (YYYY-MM)
    current_month = datetime.now().strftime('%Y-%m')

    # 🔹 성별 / 연령대 차트 & 수급자수 카드
    with st.container():
        st.markdown("### 👥 도서관 반경 2km 인구 현황")
        age_sum = df_pop[df_pop['행정동'].isin(df_library[
            (df_library['자치구'] == selected_gu) &
            (df_library['도서관명'] == selected_library)
        ]['행정동'].unique())].iloc[:, 2:].sum()
        age_sum['95세 이상'] = age_sum.get('95~99세', 0) + age_sum.get('100세 이상', 0)
        age_sum = age_sum.drop(['95~99세', '100세 이상'])
        covered_dongs = df_library[
            (df_library['자치구'] == selected_gu) &
            (df_library['도서관명'] == selected_library)
        ]['행정동'].unique()
        gender_sum = df_gender[df_gender['행정동'].isin(covered_dongs)].sum()

        col_pie, col_bar = st.columns([4, 6])
        with col_pie:
            # 파이차트
            fig_pie = go.Figure(data=[go.Pie(
                labels=['남자', '여자'],
                values=[gender_sum['남자'], gender_sum['여자']],
                marker=dict(colors=['lightblue', 'pink']),
                textinfo='label+percent',
                hole=0.3
            )])
            fig_pie.update_layout(height=200, margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})

            # 수급자수 카드
            covered_welfare = welfare_df[welfare_df['행정동'].isin(covered_dongs)]
            avg_welfare_rate = covered_welfare['수급자수'].mean()
            seoul_avg = welfare_df['수급자수'].mean()
            st.markdown(f"""
            <div style="padding: 10px; background-color: #f8f9fa; border: 1px solid #ddd;
                         border-radius: 8px; text-align: center; font-size: 20px; margin-top: 10px;">
                <strong>평균 수급자수</strong><br>
                <span style="font-size: 36px; color: #0d6efd;"><strong>{avg_welfare_rate:,.0f}명</strong></span><br>
                <span style="font-size: 14px; color: #dc3545;">행정동 평균: {seoul_avg:,.0f}명</span>
            </div>
            """, unsafe_allow_html=True)

        with col_bar:
            # 65세 이상 컬럼명 리스트
            elderly_cols = ['65~69세', '70~74세', '75~79세', '80~84세', '85~89세', '90~94세', '95세 이상']
            
            # 색상 지정: 65세 이상 오렌지, 나머지 스카이블루
            colors = ['orange' if age in elderly_cols else 'skyblue' for age in age_sum.index]
            
            fig_bar = go.Figure(go.Bar(
                x=age_sum.index,
                y=age_sum.values,
                marker_color=colors,
                text=age_sum.values,
                textposition='outside'
            ))
            fig_bar.update_layout(height=400, margin=dict(l=0, r=0, t=0, b=0), yaxis=dict(tickformat=","))
            st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})

    # 🔹 문화행사 API
    @st.cache_data(ttl=3600)
    def fetch_cultural_events():
        api_key = '5075546443646f6833344f5553734b'
        url = f"http://openapi.seoul.go.kr:8088/{api_key}/json/culturalEventInfo/1/1000/"
        r = requests.get(url)
        r.encoding = 'utf-8'
        if r.status_code == 200:
            data = r.json()
            if 'culturalEventInfo' in data and 'row' in data['culturalEventInfo']:
                return pd.DataFrame(data['culturalEventInfo']['row'])
        return pd.DataFrame()

    df_events_raw = fetch_cultural_events()

    # 🔹 행사 데이터 필터링
    def filter_current_month_events(df):
        start_dates = df['STRTDATE'].astype(str).str[:7]
        end_dates = df['END_DATE'].astype(str).str[:7]
        mask = (start_dates == current_month) | (end_dates == current_month)
        return df[mask]

    df_events = filter_current_month_events(df_events_raw)


    # 🔹 도서관 정보
    library_info = df_library[(df_library['자치구'] == selected_gu) & (df_library['도서관명'] == selected_library)].iloc[0]
    lat, lon = library_info['위도'], library_info['경도']
    # 🔹 도서관 반경 2km 내 포함 행정동 목록
    covered_dongs = df_library[
        (df_library['자치구'] == selected_gu) &
        (df_library['도서관명'] == selected_library)
    ]['행정동'].unique()
    # 🔹 공공장소 검색 함수
    def search_public_places(lat, lon, radius=2000, category_code="PO3"):
        url = "https://dapi.kakao.com/v2/local/search/category.json"
        headers = {"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"}
        params = {
            "category_group_code": category_code,
            "x": lon,
            "y": lat,
            "radius": radius,
            "sort": "distance",
            "size": 15
        }
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json().get("documents", [])
        return []

    # 🔹 거리 계산
    def haversine(lon1, lat1, lon2, lat2):
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        dlon, dlat = lon2 - lon1, lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
        return 6371000 * 2 * asin(sqrt(a))

    # 🔹 지도 및 행사 시각화와 공공기관/행정동/문화행사 3분할 마크업 통합
    display_events = []
    with st.container():
        st.markdown(f"<h4 style='margin: 10px 0;'>📍 {selected_library} 주변 현황</h4>", unsafe_allow_html=True)
        m = folium.Map(location=[lat, lon], zoom_start=14)
        folium.Marker([lat, lon], popup=selected_library, icon=folium.Icon(color='blue', icon='book')).add_to(m)
        # 공공장소 표시
        public_places = search_public_places(lat, lon, radius=2000, category_code="PO3")
        for place in public_places:
            place_name = place["place_name"]
            place_lat = float(place["y"])
            place_lon = float(place["x"])
            folium.Marker(
                [place_lat, place_lon],
                tooltip=place_name,
                icon=folium.Icon(color="purple", icon="info-sign")
            ).add_to(m)
        folium.Circle([lat, lon], radius=1000, color='red', fill=False).add_to(m)
        folium.Circle([lat, lon], radius=2000, color='blue', fill=True, fill_opacity=0.1).add_to(m)

        for _, e in df_events.iterrows():
            lot, lat_val = e.get('LOT'), e.get('LAT')
            if pd.notna(lot) and pd.notna(lat_val) and lot != '0' and lat_val != '0':
                try:
                    e_lat, e_lon = float(lot), float(lat_val)
                    if haversine(lon, lat, e_lon, e_lat) <= 1000:
                        folium.Marker(
                            [e_lat, e_lon],
                            popup=f"<b>{e['TITLE']}</b><br>{e['PLACE']}<br>{e['STRTDATE']} ~ {e['END_DATE']}",
                            tooltip=f"{e['TITLE']} | {e['PLACE']}",
                            icon=folium.Icon(color='green')
                        ).add_to(m)
                        display_events.append(e)
                except ValueError:
                    pass
        st_folium(m, width=1400, height=500)

        col_left, col_center, col_right = st.columns([3, 4, 5])
        with col_left:
            st.markdown("### 🏠 2km 반경 행정동")
            st.markdown(
                f"<div style='height:400px; overflow-y:auto; background:#f9f9f9; padding:10px; border-radius:8px; border:1px solid #ddd;'>"
                + "".join([f"<li>{d}</li>" for d in covered_dongs]) + "</div>",
                unsafe_allow_html=True
            )

        with col_center:
            st.markdown("### 🏛️ 공공기관 정보")
            public_html = "<div style='height:400px; overflow-y:auto; background:#f9f9f9; padding:10px; border-radius:8px; border:1px solid #ddd;'>"
            if public_places:
                for place in public_places:
                    name = place['place_name']
                    address = place.get('road_address_name') or place.get('address_name', '')
                    public_html += f"<div style='margin-bottom:10px; padding:8px; background:white; border:1px solid #ccc; border-radius:6px;'>" \
                                   f"<b>{name}</b><br><small>{address}</small></div>"
            else:
                public_html += "<p>표시할 공공기관이 없습니다.</p>"
            public_html += "</div>"
            st.markdown(public_html, unsafe_allow_html=True)

        with col_right:
            st.markdown("### 🎭 문화행사 상세정보")
            event_html = "<div style='height:400px; overflow-y:auto; background:#f9f9f9; padding:10px; border-radius:8px; border:1px solid #ddd;'>"
            if display_events:
                for _, e in pd.DataFrame(display_events).iterrows():
                    start_date = e['STRTDATE'][:10] if pd.notna(e['STRTDATE']) else ''
                    end_date = e['END_DATE'][:10] if pd.notna(e['END_DATE']) else ''
                    event_html += f"<div style='margin-bottom:15px; padding:8px; background:white; border:1px solid #ccc; border-radius:6px;'>" \
                                   f"<b>{e['TITLE']}</b><br>" \
                                   f"<small>일시: {start_date} ~ {end_date}</small><br>" \
                                   f"<small>장소: {e['PLACE']}</small></div>"
            else:
                event_html += "<p style='color:gray;'>현재 표시할 문화행사가 없습니다.</p>"
            event_html += "</div>"
            st.markdown(event_html, unsafe_allow_html=True)

with tab2:
    # 제목과 필터 섹션
    col_title, col_button = st.columns([5, 1])
    with col_title:
        st.markdown(f"### 📚 {selected_library} 인기 대출 도서 조회")
    with col_button:
        st.empty()

    # 필터 드롭다운 그룹
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        gender_option = st.selectbox("성별", ["전체", "남성", "여성"], index=0, key="gender")
    with col2:
        age_option = st.selectbox("연령대", ["전체", "0-5세", "6-7세", "8-13세", "14-19세", "20대", "30대", "40대", "50대", "60대 이상"], index=0, key="age")
    with col3:
        kdc_dict = {
            "전체": "",
            "총류": "0",
            "철학": "1",
            "종교": "2",
            "사회과학": "3",
            "자연과학": "4",
            "기술과학": "5",
            "예술": "6",
            "언어": "7",
            "문학": "8",
            "역사": "9"
        }
        kdc_label = st.selectbox("주제(KDC)", list(kdc_dict.keys()), index=0, key="kdc_label")
    with col4:
        period_option = st.selectbox("기간", ["1개월", "3개월", "6개월", "1년"], index=1, key="period")

    # 기간 계산
    period_days = {
        "1개월": 30,
        "3개월": 90,
        "6개월": 180,
        "1년": 365
    }
    end_date = datetime.now()
    start_date = end_date - timedelta(days=period_days[period_option])
    
    # 선택된 도서관으로 코드 찾기 (부분 문자열 매칭)
    matched = df_libcode[df_libcode['libName'].str.contains(selected_library.replace('도서관', ''), na=False)]
    lib_code = None  # 기본값 설정
    
    if not matched.empty:
        lib_code = matched['libCode'].values[0]
        
        # API 매개변수 설정
        params = {
            'authKey': '1a9e6e084f13de6ecec549f3397de9c292025d6e139a145a8a694d840c6cc76e',
            'libCode': lib_code,
            'startDt': start_date.strftime("%Y-%m-%d"),
            'endDt': end_date.strftime("%Y-%m-%d"),
            'gender': '0' if gender_option == "전체" else ('1' if gender_option == "남성" else '2'),
            'age': '0' if age_option == "전체" else age_option.split('-')[0].split('대')[0],
            'kdc': kdc_dict[kdc_label],
            'pageNo': '1',
            'pageSize': '50',
            'format': 'json'
        }
        
        # URL 생성
        base_url = "http://data4library.kr/api/loanItemSrchByLib"
        api_url = f"{base_url}?" + "&".join([f"{k}={v}" for k, v in params.items() if v])
        response = requests.get(api_url)
        data = response.json()

        # Simplified card layout for each book and KDC analysis
        if "response" in data and "docs" in data["response"]:
            docs = data["response"]["docs"]
            
                        # 도서 카드 표시 
            rows = [st.columns(5) for _ in range(2)]
            for i, book in enumerate(docs[:10]):
                info = book["doc"]
                col = rows[i // 5][i % 5]
                with col:
                    st.markdown(f"""
                    <div style='padding: 15px; background-color: #ffffff; border: 1px solid #eee;
                                border-radius: 10px; text-align: center; height: 280px; display: flex;
                                flex-direction: column; justify-content: center; align-items: center;'>
                        <div style='font-size: 18px;'>🥇 {info['ranking']}위</div>
                        <img src='{info.get("bookImageURL", "")}' style='width:80px; margin:8px auto;' />
                        <div style='margin-top: 8px; font-weight: bold;'>{info['bookname']}</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # KDC 분포 그래프
            st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)
            st.markdown(f"### 🗂️ {selected_library} 인기 대출 도서 KDC 분포")
            
            from collections import Counter
            import plotly.express as px
            
            # class_nm에서 상위 2개 수준만 추출
            class_names = []
            for book in docs:
                class_nm = book['doc'].get('class_nm', '')
                if class_nm:
                    levels = class_nm.split(' > ')[:2]  # 상위 2개 수준만 사용
                    class_names.append(' > '.join(levels))
            
            class_counter = Counter(class_names)
            
            if class_counter:
                df_class = pd.DataFrame(class_counter.items(), columns=["주제분류", "빈도수"])
                df_class = df_class.sort_values("빈도수", ascending=False).head(10)
                
                fig_class = px.bar(
                    df_class,
                    x="주제분류",
                    y="빈도수",
                    color_discrete_sequence=['#00B0F0']  # 하늘색 계열로 통일
                )
                
                fig_class.update_layout(
                    xaxis_title="주제(KDC)",
                    yaxis_title="도서 수",
                    height=450,
                    margin=dict(t=60, b=60),
                    showlegend=False
                )
                
                st.plotly_chart(fig_class, use_container_width=True)
            else:
                st.info("주제분류(class_nm) 정보가 없습니다.")
        else:
            st.info("해당 도서관의 인기 대출 도서를 찾을 수 없습니다.")
    else:
        st.warning("도서관 코드를 찾을 수 없습니다.")
