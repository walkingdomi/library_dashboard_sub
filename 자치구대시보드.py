
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from streamlit_echarts import st_echarts
import requests
from datetime import datetime 

with st.sidebar:
    # ... (기존 사이드바 구성 요소들)
    pass

st.set_page_config(page_title="서울시 도서관 대시보드", layout="wide")
st.title("📊 서울시 자치구별 현황")

# 자치구 코드 ↔ 이름 매핑
gu_dict = {
    1: '강남구', 2: '강동구', 3: '강북구', 4: '강서구', 5: '관악구', 6: '광진구',
    7: '구로구', 8: '금천구', 9: '노원구', 10: '도봉구', 11: '동대문구', 12: '동작구',
    13: '마포구', 14: '서대문구', 15: '서초구', 16: '성동구', 17: '성북구', 18: '송파구',
    19: '양천구', 20: '영등포구', 21: '용산구', 22: '은평구', 23: '종로구', 24: '중구', 25: '중랑구'
}
reverse_gu_dict = {v: k for k, v in gu_dict.items()}

# 자치구명 → 세부지역 코드 매핑 (도서관정보나루용)
dtl_region_dict = {
    '종로구': 11010,
    '중구': 11020,
    '용산구': 11030,
    '성동구': 11040,
    '광진구': 11050,
    '동대문구': 11060,
    '중랑구': 11070,
    '성북구': 11080,
    '강북구': 11090,
    '도봉구': 11100,
    '노원구': 11110,
    '은평구': 11120,
    '서대문구': 11130,
    '마포구': 11140,
    '양천구': 11150,
    '강서구': 11160,
    '구로구': 11170,
    '금천구': 11180,
    '영등포구': 11190,
    '동작구': 11200,
    '관악구': 11210,
    '서초구': 11220,
    '강남구': 11230,
    '송파구': 11240,
    '강동구': 11250
}

# Validate selected_gu mapping
if 'selected_gu' in locals() and selected_gu not in dtl_region_dict:
    st.error(f"선택한 자치구 '{selected_gu}'에 대한 지역 코드가 없습니다.")
    st.stop()

# 파일 불러오기
pop_df = pd.read_csv("district_age_gender_population.csv")
xlsx_path = "2024_Seoul_Library_User_Survey_data.csv"
df = pd.read_csv(xlsx_path, encoding="utf-8-sig")

# 자치구 선택 관련 코드(pop_df 로드 이후)
gu_list = sorted(pop_df['자치구'].unique())
selected_gu = st.selectbox("자치구 선택", gu_list)
dtl_code = dtl_region_dict.get(selected_gu, 11010)
selected_gu_code = reverse_gu_dict[selected_gu]

tab1, tab2, tab3, tab4 = st.tabs([
    "👥 인구통계",
    "📚 문화지표",
    "🎯 성과조사",
    "📖 도서관정보나루"
])


# ------------------------ 공통 처리 ------------------------
question_cols = [col for col in df.columns if col.startswith(("Q1_", "Q2_", "Q3_", "Q4_", "Q5_", "Q6_"))]
df = df[['SQ3'] + question_cols].rename(columns={"SQ3": "자치구"})

def convert_score(x):
    return (x - 1) * 100 / 6 if pd.notna(x) and x != 9 else None

def classify_section(q):
    if q.startswith("Q1_"): return "공간이용"
    if q.startswith("Q2_"): return "정보활용"
    if q.startswith("Q3_"): return "소통정책"
    if q.startswith("Q4_"): return "문화교육"
    if q.startswith("Q5_"): return "사회관계"
    if q.startswith("Q6_"): return "장기효과"





with tab1:
    # --- 인구 구조 및 복지 ---
    gu_df = pop_df[pop_df['자치구'] == selected_gu]
    age_order = gu_df['연령'].unique().tolist()
    age_df = gu_df.groupby('연령')['인구수'].sum().reindex(age_order)
    bar_x = age_df.index.tolist()
    bar_y = age_df.values.tolist()

    import re

    color_old = "#ffae00"    # orange (65세 이상)
    color_young = "#8ed6fb"  # skyblue (65세 미만)

    bar_colors = []
    for label in bar_x:
        label_clean = str(label).strip()
        m = re.match(r"(\d+)", label_clean)
        age = int(m.group(1)) if m else 0
        if age >= 65:
            bar_colors.append(color_old)
        else:
            bar_colors.append(color_young)

    male_sum = gu_df[gu_df['성별'] == '남자']['인구수'].sum()
    female_sum = gu_df[gu_df['성별'] == '여자']['인구수'].sum()
    total_sum = male_sum + female_sum
    percent_man = male_sum / total_sum if total_sum else 0
    percent_woman = female_sum / total_sum if total_sum else 0

    import plotly.graph_objects as go
    labels = ['남자', '여자']
    values = [male_sum, female_sum]
    colors = ['#b7dde9', '#fac4d5']

    st.markdown("### 👥 인구 구조")
    col1, col2 = st.columns([0.7, 2.3])  # 성별 차트 좁게, 인구 차트 넓게

    with col1:
        fig_gender = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.3,  # 구멍 작게
            marker=dict(colors=colors),
            textinfo='label+percent',
            textfont=dict(size=16),  # 폰트 약간 작게
            insidetextorientation='auto'
        )])
        fig_gender.update_traces(
            hoverinfo='label+value+percent'
        )
        fig_gender.update_layout(
            showlegend=False,
            margin=dict(l=30, r=30, t=30, b=30),
            height=270
        )
        st.plotly_chart(fig_gender, use_container_width=True, height=270)
    with col2:
        fig = go.Figure(data=[go.Bar(x=bar_x, y=bar_y, marker_color=bar_colors)])
        fig.update_layout(
            title="연령별 인구수 (남+여 합계)",
            xaxis_title="연령대",
            yaxis_title="인구수",
            yaxis=dict(tickformat=",", separatethousands=True),
            margin=dict(l=30, r=20, t=40, b=40),
            height=350
        )
        st.plotly_chart(fig, use_container_width=True, height=350)

    # --- 수급률 강조 ---
    df_gu = pd.read_csv("district_data_combined.csv")
    df_gu.rename(columns={df_gu.columns[0]: "자치구"}, inplace=True)

    def make_welfare_stat_block(gu_name):
        value = df_gu[df_gu["자치구"] == gu_name]["수급률"].values[0]
        value_fmt = f"{value:.1f}%"
        seoul_avg = 5.044  # 서울 전체 자치구 평균 수급률
        return f"""
        <div style="padding: 10px; background-color: #f8f9fa; border: 1px solid #ddd;
                    border-radius: 8px; text-align: center; font-size: 20px;">
            <strong>수급률</strong><br>
            <span style="font-size: 36px; color: #0d6efd;"><strong>{value_fmt}</strong></span><br>
            <span style="font-size: 14px; color: #dc3545;">서울 평균: {seoul_avg:.1f}%</span>
        </div>
        """
    st.markdown("### 💠 자치구 수급률")
    st.markdown(make_welfare_stat_block(selected_gu), unsafe_allow_html=True)
    st.markdown("<div style='height:48px;'></div>", unsafe_allow_html=True)

    # --- 다문화 국적 구성 (상위 5개 + 기타) ---
    import plotly.express as px
    import plotly.graph_objects as go
    st.markdown("### 🌐 다문화 국적 구성 비율")
    st.markdown("<div style='height:5px;'></div>", unsafe_allow_html=True)
    df_gu = pd.read_csv("district_data_combined.csv", na_values="NA")
    df_gu.rename(columns={df_gu.columns[0]: "자치구"}, inplace=True)
    df_gu.iloc[:, 2:34] = df_gu.iloc[:, 2:34].apply(pd.to_numeric, errors="coerce")
    multicultural_cols = df_gu.columns[2:34]
    row = df_gu[df_gu["자치구"] == selected_gu][multicultural_cols].iloc[0]
    if row.sum() == 0 or row.dropna().empty:
        st.warning("선택한 자치구에는 다문화 국적 데이터가 없습니다.")
    else:
        top5 = row.sort_values(ascending=False).head(5)
        others_sum = row.sum() - top5.sum()
        top5["기타"] = others_sum
        percentages = top5 / top5.sum() * 100
        fig = go.Figure()
        for col, val in zip(percentages.index, percentages.values):
            fig.add_trace(go.Bar(
                x=[val],
                y=["다문화 국적 구성"],
                orientation='h',
                name=col,
                text=f"{val:.1f}%",
                textposition='inside'
            ))
        fig.update_layout(
            barmode='stack',
            height=140,
            margin=dict(t=30, b=30),
            xaxis=dict(range=[0, 100], showticklabels=False),
            yaxis=dict(showticklabels=False),
            title="다문화 국적 구성 비율 (상위 5개 + 기타)",
            legend=dict(orientation="h", y=-0.3, x=0.5, xanchor="center")
        )
        st.plotly_chart(fig, use_container_width=True)

    # --- 장애 유형 100% 누적 막대그래프 ---
    import plotly.graph_objects as go
    st.markdown("### ♿ 장애 유형별 인원 구성 비율")
    df_gu = pd.read_csv("district_data_combined.csv", na_values="NA")
    df_gu.rename(columns={df_gu.columns[0]: "자치구"}, inplace=True)
    df_gu.iloc[:, 35:41] = df_gu.iloc[:, 35:41].apply(pd.to_numeric, errors="coerce")
    disability_cols = df_gu.columns[35:41]
    row = df_gu[df_gu["자치구"] == selected_gu][disability_cols].iloc[0]
    if row.sum() == 0 or row.dropna().empty:
        st.warning("선택한 자치구에는 장애 유형 데이터가 없습니다.")
    else:
        total = row.sum()
        percentages = row / total * 100
        fig = go.Figure()
        for col, val in zip(percentages.index, percentages.values):
            fig.add_trace(go.Bar(
                x=[val],
                y=["장애 유형 구성"],
                orientation='h',
                name=col,
                text=f"{val:.1f}%",
                textposition='inside'
            ))
        fig.update_layout(
            barmode='stack',
            xaxis=dict(range=[0, 100], showticklabels=False),
            yaxis=dict(showticklabels=False),
            height=140,
            margin=dict(t=30, b=30),
            legend=dict(orientation="h", y=-0.3, x=0.5, xanchor="center"),
            title="장애 유형 구성 비율 (100% 누적)"
        )
        st.plotly_chart(fig, use_container_width=True)

    # --- 가구 유형 시각화 (열 이름 strip 포함) ---
    import plotly.graph_objects as go
    st.markdown("### 🏠 가구 유형별 구성 비율")
    df_gu = pd.read_csv("district_data_combined.csv", na_values="NA")
    df_gu.rename(columns={df_gu.columns[0]: "자치구"}, inplace=True)
    df_gu.columns = df_gu.columns.str.strip()
    df_gu.iloc[:, 41:45] = df_gu.iloc[:, 41:45].apply(pd.to_numeric, errors="coerce")
    house_cols = df_gu.columns[41:45]
    row = df_gu[df_gu["자치구"] == selected_gu][house_cols].iloc[0]
    if row.sum() == 0 or row.dropna().empty:
        st.warning("선택한 자치구의 가구 유형 데이터가 없습니다.")
    else:
        total = row.sum()
        percentages = row / total * 100
        fig_house = go.Figure()
        for col, val in zip(percentages.index, percentages.values):
            fig_house.add_trace(go.Bar(
                x=[val],
                y=["가구 유형"],
                orientation='h',
                name=col,
                text=f"{val:.1f}%",
                textposition='inside'
            ))
        fig_house.update_layout(
            barmode='stack',
            height=140,
            margin=dict(t=30, b=30),
            xaxis=dict(range=[0, 100], showticklabels=False),
            yaxis=dict(showticklabels=False),
            title="가구 구성원 수 기준 비율 (100% 누적)",
            legend=dict(orientation="h", y=-0.3, x=0.5, xanchor="center")
        )
        fig_house.add_annotation(
            text="서울시 1인가구 비율 평균: 40.9%",
            xref="paper", yref="paper",
            x=0.5, y=-0.35,
            showarrow=False,
            font=dict(size=12, color="red"),
            align="center"
        )
        st.plotly_chart(fig_house, use_container_width=True)

    # --- 1인 가구 수 vs 서울 평균 ---
    st.markdown("### 🏘️ 1인 가구 수 비교")
    household_data = pd.read_csv("district_data_combined.csv")
    household_data = household_data.rename(columns={household_data.columns[0]: "자치구"})
    selected_gu_oneperson = household_data[household_data["자치구"] == selected_gu]["1인가구"].values[0]
    avg_oneperson = round(household_data["1인가구"].mean())
    fig_household = go.Figure()
    fig_household.add_trace(go.Bar(
        y=[selected_gu],
        x=[selected_gu_oneperson],
        orientation='h',
        name=selected_gu,
        marker_color='steelblue',
        text=[f"{selected_gu_oneperson:,}가구"],
        textposition='outside',
        textfont=dict(color='black')
    ))
    fig_household.add_shape(
        type="line",
        x0=avg_oneperson,
        x1=avg_oneperson,
        y0=-0.5,
        y1=0.5,
        line=dict(color="red", width=2)
    )
    fig_household.add_annotation(
        x=avg_oneperson,
        y=0,
        text=f"서울 평균: {avg_oneperson:,}가구",
        showarrow=True,
        arrowhead=2,
        ax=20,
        ay=-30,
        font=dict(color="black")
    )
    fig_household.update_layout(
        title=f"📏 1인 가구 수 비교 ({selected_gu} vs 서울 평균)",
        xaxis=dict(range=[0, 180000], showgrid=False),
        yaxis=dict(showticklabels=False),
        margin=dict(l=0, r=0, t=60, b=60),
        height=180,
        showlegend=False,
        plot_bgcolor='#f9f9f9'
    )
    st.plotly_chart(fig_household, use_container_width=True)




with tab2:
    # ------------------------ 문화지표 ~ 문화·복지 시설: tab2 (이동) ------------------------
    st.markdown("### 📚 문화지표 요약 (강좌 비율, 이용 관심도 등)")
    df_culture = pd.read_csv("district_data_combined.csv", na_values="NA")
    df_culture.rename(columns={df_culture.columns[0]: "자치구"}, inplace=True)
    df_culture.columns = df_culture.columns.str.strip()
    if selected_gu not in df_culture["자치구"].values:
        st.warning("해당 자치구의 문화지표 데이터가 없습니다.")
    else:
        row = df_culture[df_culture["자치구"] == selected_gu].iloc[0]
        card_style = """
    <div style="
        height: 180px;
        width: 100%;
        min-width: 0;
        min-height: 180px;
        background-color: #f8f9fa;
        border: 1px solid #ddd;
        border-radius: 16px;
        text-align: center;
        font-size: 20px;
        line-height: 1.5;
        margin-bottom: 10px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        box-sizing: border-box;
    ">
        <div style='font-size:28px; margin-bottom:3px'>{icon} {title}</div>
        <span style='font-size:48px; color:#007bff; font-weight: bold;'>{value}</span>
        <div style='font-size:15px; margin-top:2px; color:#666;'>{unit}</div>
    </div>
"""
        row1_col1, row1_col2 = st.columns(2)
        row2_col1, row2_col2 = st.columns(2)
        with row1_col1:
            st.markdown(card_style.format(
                icon="📘",
                title="강좌 비율",
                value=f"{row['강좌_비율']:.1f}" if pd.notna(row['강좌_비율']) else "정보 없음",
                unit="1만명당 강좌횟수"
            ), unsafe_allow_html=True)
        with row1_col2:
            st.markdown(card_style.format(
                icon="⭐",
                title="운영 관심도 점수",
                value=f"{row['운영_관심도_점수']:.1f}" if pd.notna(row['운영_관심도_점수']) else "정보 없음",
                unit=""
            ), unsafe_allow_html=True)
        with row2_col1:
            st.markdown(card_style.format(
                icon="👥",
                title="참가자 비율",
                value=f"{row['참가자_비율']:.1f}" if pd.notna(row['참가자_비율']) else "정보 없음",
                unit="1만명당 참가자 수"
            ), unsafe_allow_html=True)
        with row2_col2:
            st.markdown(card_style.format(
                icon="🌟",
                title="이용 관심도 점수",
                value=f"{row['이용_관심도_점수']:.1f}" if pd.notna(row['이용_관심도_점수']) else "정보 없음",
                unit=""
            ), unsafe_allow_html=True)

    st.markdown("### 🏛️ 문화·복지 시설 유형별 개수")
    import plotly.graph_objects as go
    df_fac = pd.read_csv("district_data_combined.csv", na_values="NA")
    df_fac.rename(columns={df_fac.columns[0]: "자치구"}, inplace=True)
    df_fac.columns = df_fac.columns.str.strip()
    facility_cols = df_fac.columns[50:54]
    df_fac[facility_cols] = df_fac[facility_cols].apply(pd.to_numeric, errors="coerce")
    row = df_fac[df_fac["자치구"] == selected_gu][facility_cols].iloc[0]
    if row.dropna().sum() == 0:
        st.warning("해당 자치구의 문화·복지 시설 데이터가 없습니다.")
    else:
        fig_fac = go.Figure()
        for col in facility_cols:
            color = '#d62728' if "공공도서관" in col else '#1f77b4'
            fig_fac.add_trace(go.Bar(
                x=[col],
                y=[row[col]],
                name=col,
                marker_color=color,
                text=[f"{int(row[col])}개"],
                textposition='outside'
            ))
        fig_fac.update_layout(
            title=f"{selected_gu} 내 문화·복지 시설 수 (공공도서관 강조)",
            yaxis_title="시설 수",
            yaxis=dict(range=[0, 20]),
            height=350,
            margin=dict(t=60, b=60),
            showlegend=False
        )
        st.plotly_chart(fig_fac, use_container_width=True)

    # ------------------------ 문화행사 API 카드: tab2 (이동) ------------------------
    st.markdown(f"### 🎭 {selected_gu} – {datetime.now().strftime('%Y년 %m월')} 문화행사")
    api_key = '5075546443646f6833344f5553734b'
    current_month = datetime.now().strftime('%Y-%m')
    url = f"http://openapi.seoul.go.kr:8088/{api_key}/json/culturalEventInfo/1/1000//%20/{current_month}"
    r = requests.get(url)
    r.encoding = 'utf-8'
    data = r.json()
    events = data.get('culturalEventInfo', {}).get('row', [])
    filtered_events = []
    for e in events:
        date_str = e.get("DATE")
        if date_str and date_str.startswith(current_month) and e.get("GUNAME") == selected_gu:
            filtered_events.append(e)
    count = len(filtered_events)
    card_html = f"""
    <div style="
        padding: 15px;
        background-color: #f8f9fa;
        border: 1px solid #ddd;
        border-radius: 8px;
        text-align: center;
        font-size: 18px;
        line-height: 1.5;
        height: 120px;">
        <strong>{selected_gu} – {datetime.now().strftime('%Y년 %m월')} 문화행사 수</strong><br>
        <span style='font-size: 32px; color: #2ca02c;'><strong>{count}</strong>건</span>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)
    st.markdown("<div style='height:32px;'></div>", unsafe_allow_html=True)

    # ------------------------ 초/중/고 학교 수 시각화: tab2 (이동) ------------------------
    st.markdown("### 🏫 초·중·고 학교 수")
    df_school = pd.read_csv("district_data_combined.csv", na_values="NA")
    df_school.rename(columns={df_school.columns[0]: "자치구"}, inplace=True)
    df_school.columns = df_school.columns.str.strip()
    if selected_gu not in df_school["자치구"].values:
        st.warning("해당 자치구의 학교 수 데이터가 없습니다.")
    else:
        row = df_school[df_school["자치구"] == selected_gu].iloc[0]
        elementary = int(row['초등학교']) if pd.notna(row['초등학교']) else 0
        middle = int(row['중학교']) if pd.notna(row['중학교']) else 0
        high = int(row['고등학교']) if pd.notna(row['고등학교']) else 0
        card_style = """
            <div style="
                padding: 35px;
                background-color: #f8f9fa;
                border: 1px solid #ddd;
                border-radius: 18px;
                text-align: center;
                font-size: 24px;
                line-height: 1.5;
                box-shadow: 0px 2px 12px #f0f0f0;">
                <strong>{title}</strong><br>
                <span style='font-size: 48px; color: #28a745;'><strong>{value}</strong>개</span>
            </div>
        """
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(card_style.format(title="초등학교", value=elementary), unsafe_allow_html=True)
        with col2:
            st.markdown(card_style.format(title="중학교", value=middle), unsafe_allow_html=True)
        with col3:
            st.markdown(card_style.format(title="고등학교", value=high), unsafe_allow_html=True)
with tab3:
    # ------------------------ 만족도 분석(항목 선택 ~ 문항 테이블): tab3 ------------------------
    melted = df.melt(id_vars='자치구', var_name='문항', value_name='원점수')
    melted['환산점수'] = melted['원점수'].apply(convert_score)
    melted['항목'] = melted['문항'].apply(classify_section)
    melted = melted.dropna(subset=['환산점수', '항목'])
    grouped = melted.groupby(['자치구', '항목'])['환산점수'].mean().reset_index()
    seoul_avg = grouped.groupby('항목')['환산점수'].mean().reset_index(name='서울시 평균')
    detail_grouped = melted.groupby(['자치구', '항목', '문항'])['환산점수'].mean().reset_index()
    sections = ['공간이용', '정보활용', '소통정책', '문화교육', '사회관계', '장기효과']
    selected_section = st.selectbox("항목 선택", sections)
    st.markdown("---")
    # 레이더 차트
    data_gu = grouped[grouped['자치구'] == selected_gu_code]
    data_gu = data_gu.merge(seoul_avg, on='항목')
    fig1 = go.Figure()
    fig1.add_trace(go.Scatterpolar(
        r=data_gu['환산점수'],
        theta=data_gu['항목'],
        fill='toself',
        name=selected_gu
    ))
    fig1.add_trace(go.Scatterpolar(
        r=data_gu['서울시 평균'],
        theta=data_gu['항목'],
        name='서울 평균',
        line=dict(color='black', dash='dash')
    ))
    fig1.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[60, 100], tickfont=dict(color="black"))
        ),
        showlegend=True,
        title=f"{selected_gu} vs 서울 평균 (항목별 평균 점수)",
        margin=dict(l=80, r=80, t=80, b=80),
        height=550
    )
    st.plotly_chart(fig1, use_container_width=True)
    # 막대 차트 (세부 문항)
    detail_data = detail_grouped[
        (detail_grouped['자치구'] == selected_gu_code) &
        (detail_grouped['항목'] == selected_section)
    ]
    seoul_section = detail_grouped[
        detail_grouped['항목'] == selected_section
    ].groupby('문항', sort=False)['환산점수'].mean().reset_index(name='서울시 평균')
    merged = detail_data.merge(seoul_section, on='문항', how='left')
    section_avg = grouped[
        (grouped['자치구'] == selected_gu_code) &
        (grouped['항목'] == selected_section)
    ]['환산점수'].values[0]
    import re
    from pandas.api.types import CategoricalDtype
    def extract_question_order(q):
        match = re.match(r"Q(\d)_(\d+)", str(q))
        return int(match.group(1)) * 100 + int(match.group(2)) if match else float('inf')
    merged = merged.sort_values(by="문항", key=lambda col: col.map(extract_question_order))
    question_order_sorted = merged["문항"].tolist()
    cat_type = CategoricalDtype(categories=question_order_sorted, ordered=True)
    merged["문항"] = merged["문항"].astype(cat_type)
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(x=merged['문항'], y=merged['환산점수'], name=selected_gu, marker_color='blue'))
    fig2.add_trace(go.Bar(x=merged['문항'], y=merged['서울시 평균'], name="서울 평균", marker_color='orange'))
    fig2.add_trace(go.Scatter(x=merged['문항'], y=[section_avg]*len(merged), name="자치구 평균선", mode='lines',
                              line=dict(color='red', dash='solid')))
    fig2.update_layout(
        barmode='group',
        title=f"[{selected_section}] 세부 문항별 점수 + 자치구 평균선",
        yaxis=dict(range=[0, 100]),
        height=550
    )
    st.plotly_chart(fig2, use_container_width=True)
    # 선택 항목 문항 테이블
    st.markdown("### 📄 해당 항목 문항 목록")
    meta_table = pd.read_csv("user_survey_variable_guide.csv")
    meta_table = meta_table[['문항번호', '내용']].copy()
    meta_table = meta_table.dropna()
    meta_table = meta_table[meta_table['문항번호'].astype(str).str.startswith("Q")]
    selected_questions = merged['문항'].tolist()
    filtered_table = meta_table[meta_table['문항번호'].isin(selected_questions)]
    filtered_table['문항번호'] = filtered_table['문항번호'].astype(
        CategoricalDtype(categories=question_order_sorted, ordered=True)
    )
    filtered_table = filtered_table.sort_values('문항번호')
    st.dataframe(filtered_table, use_container_width=True, height=300)

    # ------------------------ 서비스 효과 vs 영향력: tab3 ------------------------
    st.markdown("---")
    st.markdown("### 🎯 차원별 서비스 효과(A) vs 영향력(B) 비교")
    meta_raw = pd.read_csv("user_survey_variable_guide.csv")
    meta_ab = meta_raw[['문항번호', '차원', '분류']].copy()
    meta_ab = meta_ab[meta_ab['문항번호'].notna()]
    meta_ab = meta_ab[meta_ab['문항번호'].astype(str).str.startswith("Q")]
    meta_ab = meta_ab[meta_ab['분류'].isin(['A', 'B'])]
    meta_ab = meta_ab[~meta_ab['차원'].str.contains("Q6")]
    dimension_map = {
        "Q1": "공간 및 이용 편의성",
        "Q2": "정보 획득 및 활용",
        "Q3": "소통 및 정책반영",
        "Q4": "문화ㆍ교육향유",
        "Q5": "사회적 관계형성"
    }
    meta_ab["차원명"] = meta_ab["차원"].map(dimension_map)
    df_long = df[["자치구"] + question_cols].melt(id_vars="자치구", var_name="문항번호", value_name="원점수")
    df_long = df_long[df_long["원점수"] != 9]
    df_long["환산점수"] = df_long["원점수"].apply(convert_score)
    df_long = df_long.merge(meta_ab, on="문항번호", how="left")
    df_long = df_long.dropna(subset=["차원명", "분류"])
    df_ab = df_long[df_long["분류"].isin(["A", "B"])]
    df_ab_gu = df_ab[df_ab["자치구"] == selected_gu_code]
    grouped_gu = df_ab_gu.groupby(["차원명", "분류"])["환산점수"].mean().reset_index()
    from pandas.api.types import CategoricalDtype
    ordered_dims = [
        "공간 및 이용 편의성",
        "정보 획득 및 활용",
        "소통 및 정책반영",
        "문화ㆍ교육향유",
        "사회적 관계형성"
    ]
    cat_type = CategoricalDtype(categories=ordered_dims, ordered=True)
    grouped_gu["차원명"] = grouped_gu["차원명"].astype(cat_type)
    pivot = grouped_gu.pivot(index="차원명", columns="분류", values="환산점수").reset_index()
    fig_ab = go.Figure()
    fig_ab.add_trace(go.Bar(
        x=pivot["차원명"],
        y=pivot["A"],
        name="A (서비스 효과)",
        offsetgroup="A",
        marker_color="#1f77b4",
        text=pivot["A"].round(1),
        textposition="outside"
    ))
    fig_ab.add_trace(go.Bar(
        x=pivot["차원명"],
        y=pivot["B"],
        name="B (서비스 영향력)",
        offsetgroup="B",
        marker_color="#d62728",
        text=pivot["B"].round(1),
        textposition="outside"
    ))
    fig_ab.update_layout(
        barmode='group',
        title=f"📌 {selected_gu} – 서비스 효과(A) / 영향력(B) 비교",
        yaxis_title="평균 환산점수",
        yaxis=dict(range=[0, 100]),
        xaxis_title="차원 (Q1~Q5)",
        height=550
    )
    st.plotly_chart(fig_ab, use_container_width=True)


with tab4:
    # ------------------------ 키워드 순위 테이블 (최근 12개월) ------------------------
    st.markdown("### 🗂️ 서울시 인기 키워드 TOP 10")

    from dateutil.relativedelta import relativedelta
    from collections import Counter

    keyword_trend = {}
    for i in range(12):
        month_str = (datetime.now() - relativedelta(months=11 - i)).strftime("%Y-%m")
        url = "http://data4library.kr/api/monthlyKeywords"
        params = {
            "authKey": "1a9e6e084f13de6ecec549f3397de9c292025d6e139a145a8a694d840c6cc76e",
            "month": month_str
        }
        try:
            res = requests.get(url, params=params, timeout=5)
            res.raise_for_status()
            import xml.etree.ElementTree as ET
            root = ET.fromstring(res.content)
            words = root.findall(".//keyword/word")
            keyword_trend[month_str] = [w.text for w in words if w is not None]
        except:
            keyword_trend[month_str] = []

    # 상위 키워드 10개 추출
    all_keywords = sum(keyword_trend.values(), [])
    top10 = [kw for kw, _ in Counter(all_keywords).most_common(10)]

    # 피벗 테이블 생성
    heat_df = pd.DataFrame(columns=["월", "키워드", "빈도"])
    for month, words in keyword_trend.items():
        for kw in top10:
            count = words.count(kw)
            heat_df = pd.concat([
                heat_df,
                pd.DataFrame([{"월": month, "키워드": kw, "빈도": count}])
            ], ignore_index=True)
    pivot_df = heat_df.pivot(index="키워드", columns="월", values="빈도").fillna(0)

    # 1. 순위 역순 정렬 방지 (1위가 위로)
    rank_table = pd.DataFrame(columns=["월", "순위", "키워드"])
    for month, keywords in keyword_trend.items():
        for i, kw in enumerate(keywords[:10]):
            rank_table = pd.concat([
                rank_table,
                pd.DataFrame([{"월": month, "순위": f"{i+1}위", "키워드": kw}])
            ], ignore_index=True)
    rank_table['순위'] = pd.Categorical(rank_table['순위'],
                                        categories=[f"{i}위" for i in range(1, 11)],
                                        ordered=True)
    pivot_rank_table = rank_table.pivot(index="순위", columns="월", values="키워드")
    pivot_rank_table = pivot_rank_table.sort_index()

    # 고유 키워드 색상 매핑 (2회 이상 등장한 키워드만 색 지정)
    import seaborn as sns
    from collections import Counter
    all_ranked_keywords = rank_table["키워드"].dropna().tolist()
    keyword_counts = Counter(all_ranked_keywords)
    recurring_keywords = [kw for kw, count in keyword_counts.items() if count >= 2]
    palette = sns.color_palette("hls", len(recurring_keywords)).as_hex()
    color_map = dict(zip(recurring_keywords, palette))

    def highlight_keyword(val):
        if pd.isna(val):
            return ''
        # 해당 키워드가 전체 데이터에서 두 번 이상 등장하면 색상 지정
        if all_ranked_keywords.count(val) >= 2:
            color = color_map.get(val, "#ffffff")
            return f'background-color: {color}; color: black;'
        else:
            return 'background-color: white; color: black;'

    styled_pivot = pivot_rank_table.style.applymap(highlight_keyword)

    # 3. 출력
    st.dataframe(styled_pivot, use_container_width=True)

    # 제목 위 공백 스페이서
    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
    st.markdown(
        f"<div style='margin-left:24px;'><span style='font-size:2rem; font-weight:bold; color:#000;'>📖 {selected_gu} 도서관 정보 제공 현황</span></div>",
        unsafe_allow_html=True
    )
    api_key = "1a9e6e084f13de6ecec549f3397de9c292025d6e139a145a8a694d840c6cc76e"
    region_code = 11  # 서울특별시
    url = f"http://data4library.kr/api/libSrch?authKey={api_key}&region={region_code}&dtl_region={dtl_code}&format=json&pageSize=50"
    lib_count = 0
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        data = r.json()
        libs = data.get("response", {}).get("libs", [])
        lib_count = len(libs)
        # 버퍼 파일에서 전체 도서관 수 계산
        df_buffer = pd.read_csv("Seoul_Public_Library_2km_Buffer.csv", encoding="utf-8-sig")
        # 선택된 자치구의 도서관명 중복 제거 후 고유 개수 카운팅
        unique_libs = df_buffer[df_buffer["자치구"] == selected_gu]["도서관명"].drop_duplicates()
        total_lib_count = unique_libs.nunique()
        card_html = f'''
        <div style="
            width:calc(100% - 48px);
            margin:0 24px;
            padding:16px 10px;
            background-color:#f8f9fa;
            border:2px solid #d3d3d3;
            border-radius:18px;
            text-align:center;
            display:flex; flex-direction:column; justify-content:center;
            height:320px; box-sizing:border-box;">
            <span style="font-size:1.84rem; font-weight:bold; color:#000; line-height:1.2; display:inline-block; text-align:center;">
                {selected_gu} 도서관<br>정보 제공 현황
            </span>
            <span style="display:block; margin-top:4px;">
              <span style="font-size:6.75rem; font-weight:bold; color:#ffae00;">{total_lib_count}</span>
              <span style="font-size:2.5rem; color:#000;">/{lib_count}관</span>
            </span>
        </div>
        '''
        # 카드와 목록을 좌우로 배치
        list_df = pd.DataFrame(unique_libs, columns=["도서관명"])
        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown(card_html, unsafe_allow_html=True)
        with col2:
            st.markdown("<div style='margin-left:24px; padding-top:16px;'>", unsafe_allow_html=True)
            st.dataframe(list_df, use_container_width=True, height=320)
            st.markdown("</div>", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"API 요청 또는 데이터 처리 실패: {e}")

    # ------------------------ 인기 대출 도서 조회 UI ------------------------
    col_title, col_button = st.columns([5, 1])
    with col_title:
        st.markdown("### 📚 인기 대출 도서 조회")
    with col_button:
        st.empty()  # 버튼 제거

    # 필터 드롭다운 그룹
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        gender_option = st.selectbox("성별", ["전체", "남자", "여자"], index=0, key="gender")
    with col2:
        age_option = st.selectbox("연령대", ["전체", "10", "20", "30", "40", "50", "60"], index=0, key="age")
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
        period_option = st.selectbox("기간", ["1주일", "2주일", "1개월", "3개월", "6개월", "1년"], index=4, key="period")

    from datetime import timedelta
    period_days = {
        "1주일": 7,
        "2주일": 14,
        "1개월": 30,
        "3개월": 90,
        "6개월": 180,
        "1년": 365
    }
    # start_date, end_date will be re-computed below after getting period_option from session_state

    # 기본값으로 조회 실행
    # Retrieve filter values from widget selections
    kdc_option = kdc_dict[kdc_label]
    start_date = (datetime.now() - timedelta(days=period_days[period_option])).strftime("%Y-%m-%d")
    end_date = datetime.now().strftime("%Y-%m-%d")

    # 이하 기존 코드 유지 (loan_url, loan_params 설정, API 요청 및 카드 렌더링)
    loan_url = "http://data4library.kr/api/loanItemSrch"
    dynamic_dtl_code = dtl_region_dict.get(selected_gu, 11010)
    loan_params = {
        "authKey": "1a9e6e084f13de6ecec549f3397de9c292025d6e139a145a8a694d840c6cc76e",
        "startDt": start_date,
        "endDt": end_date,
        "region": "11",
        "dtl_region": str(dynamic_dtl_code),
        "addCode": "0",
        "pageNo": "1",
        "pageSize": "10",
        "format": "xml"
    }

    if gender_option == "남자":
        loan_params["gender"] = "1"
    elif gender_option == "여자":
        loan_params["gender"] = "2"

    if age_option != "전체":
        loan_params["age"] = age_option

    if kdc_option:
        loan_params["kdc"] = kdc_option

    # 카드용 스타일
    st.markdown("""
        <style>
        .card {
            background-color: #fefefe;
            padding: 1rem;
            border-radius: 10px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.1);
            text-align: center;
            margin-bottom: 1rem;
            min-height: 230px;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: center;
            flex-grow: 1;
        }
        .rank {
            font-size: 1.1rem;
            font-weight: bold;
            color: #333;
        }
        .title {
            font-size: 1.05rem;
            font-weight: 600;
            margin: 0.5rem 0;
            color: #222;
        }
        .loan {
            color: #007BFF;
            font-weight: 500;
        }
        </style>
    """, unsafe_allow_html=True)
    # API 요청
    import xml.etree.ElementTree as ET
    loan_response = requests.get(loan_url, params=loan_params)
    if loan_response.status_code == 200:
        root = ET.fromstring(loan_response.content)
        docs = root.findall(".//doc")
        if not docs:
            st.warning("도서 정보가 없습니다.")
        else:
            cols = st.columns(5)
            for idx, doc in enumerate(docs[:10]):
                col = cols[idx % 5]
                with col:
                    with st.container():
                        title = doc.findtext("bookname")
                        card_html = f"""
                            <div class='card'>
                                <div class='rank'>🥇 {idx + 1}위</div>
                                <div class='title'>{title or '제목 없음'}</div>
                                <div class='loan'>📚 {doc.findtext('loan_count') or '0'}건 대출</div>
                            </div>
                        """
                        st.markdown(card_html, unsafe_allow_html=True)
                if (idx + 1) % 5 == 0 and idx < 9:
                    cols = st.columns(5)
    else:
        st.error(f"❌ API 요청 실패: {loan_response.status_code}")

    # ------------------------ 연령별 독서량/독서율 시각화 ------------------------
    st.markdown("### 📈 연령별 독서량 및 독서율")
    readqt_url = "http://data4library.kr/api/readQt"
    readqt_params = {
        "authKey": "1a9e6e084f13de6ecec549f3397de9c292025d6e139a145a8a694d840c6cc76e",
        "region": "11",
        "dtl_region": str(dtl_code),
        "year": str(datetime.now().year - 1),
        "format": "xml"
    }
    try:
        readqt_response = requests.get(readqt_url, params=readqt_params, timeout=5)
        readqt_response.raise_for_status()
        import xml.etree.ElementTree as ET
        root = ET.fromstring(readqt_response.content)
        result = root.findall(".//result")
        if not result:
            st.warning("해당 자치구의 독서량/독서율 데이터가 없습니다.")
        else:
            age_list = []
            quantity_list = []
            rate_list = []
            for r in result:
                age = r.findtext("age")
                quantity = r.findtext("quantity")
                rate = r.findtext("rate")
                if age and quantity and rate:
                    age_list.append(age)
                    quantity_list.append(float(quantity))
                    rate_list.append(float(rate) * 100)  # 독서율을 %로 변환

            # 📌 연령대 순서 정렬
            age_order = [
                "전체", "영유아", "유아", "초등", "청소년",
                "20대", "30대", "40대", "50대", "60대 이상"
            ]
            sorted_data = sorted(
                zip(age_list, quantity_list, rate_list),
                key=lambda x: age_order.index(x[0]) if x[0] in age_order else 99
            )
            age_list, quantity_list, rate_list = zip(*sorted_data)

            import plotly.graph_objects as go
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=age_list,
                y=quantity_list,
                name="독서량 (권)",
                marker_color="#1f77b4",
                text=[round(q, 1) for q in quantity_list],
                textposition="outside"
            ))
            fig.add_trace(go.Scatter(
                x=age_list,
                y=rate_list,
                name="독서율 (%)",
                yaxis="y2",
                mode="lines+markers",
                line=dict(color="orange", width=3),
                marker=dict(size=8)
            ))
            fig.update_layout(
                title=f"{selected_gu} – 연령별 독서량 및 독서율",
                xaxis_title="연령대",
                yaxis=dict(title="독서량 (권)", range=[0, max(quantity_list) + 10]),
                yaxis2=dict(
                    title="독서율 (%)",
                    overlaying="y",
                    side="right",
                    range=[0, max(rate_list) + 10],
                    showgrid=False
                ),
                legend=dict(orientation="h", y=-0.3),
                height=550
            )
            st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"API 요청 또는 데이터 처리 실패: {e}")
        
    # ------------------------ 최근 12개월 이달의 키워드 추이 ------------------------
   
