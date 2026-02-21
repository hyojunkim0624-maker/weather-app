import streamlit as st
import requests
import time
from streamlit_js_eval import get_geolocation, streamlit_js_eval

# 1. 페이지 설정
st.set_page_config(page_title="Global Weather Dash", page_icon="🌤️", layout="centered")

# 2. [필수] API 키 가져오기
try:
    API_KEY = st.secrets["WEATHER_API_KEY"]
except KeyError:
    st.error("API 키가 설정되지 않았습니다. .streamlit/secrets.toml 파일을 확인하세요.")
    st.stop()

# ==========================================
# 3. [핵심 수정] 세션 상태 초기화 (무한 루프 방지)
# ==========================================
if 'user_location' not in st.session_state:
    st.session_state.user_location = None
    
# GPS를 이미 한 번 확인했는지 기억하는 변수 추가
if 'auto_gps_done' not in st.session_state:
    st.session_state.auto_gps_done = False 

# 4. [핵심 수정] 위치 정보 가져오기 (최초 1회만 실행)
if not st.session_state.auto_gps_done:
    loc = get_geolocation()
    if loc:
        st.session_state.user_location = loc
        st.session_state.auto_gps_done = True # "이제 GPS 잡았으니까 더 이상 자동 실행하지 마!" 라고 기록
        st.rerun()

# 5. 데이터 정의
countries_cities = {
    "South Korea (한국)": ["Seoul (서울)", "Busan (부산)", "Asan (아산)", "Boeun (보은)", "Incheon (인천)", "Daegu (대구)", "Daejeon (대전)", "Jeju (제주)"],
    "USA (미국)": ["New York (뉴욕)", "Los Angeles (로스앤젤레스)", "Chicago (시카고)"],
    "Japan (일본)": ["Tokyo (도쿄)", "Osaka (오사카)", "Nagoya (나고야)"],
    "United Kingdom (영국)": ["London (런던)", "Manchester (맨체스터)"],
    "France (프랑스)": ["Paris (파리)", "Nice (니스)"],
    "Germany (독일)": ["Berlin (베를린)", "Munich (뮌헨)"],
    "China (중국)": ["Beijing (베이징)", "Shanghai (상하이)"]
}

moon_phase_ko = {
    "New Moon": "신월 🌑", "Waxing Crescent": "초승달 🌒", "First Quarter": "상현달 🌓",
    "Waxing Gibbous": "상현달과 보름달 사이 🌔", "Full Moon": "보름달 🌕",
    "Waning Gibbous": "보름달과 하현달 사이 🌖", "Last Quarter": "하현달 🌗", "Waning Crescent": "그믐달 🌘"
}

# 🌐 언어 선택
lang_col1, lang_col2 = st.columns([0.7, 0.3])
with lang_col2:
    language = st.radio("Language", ("한국어", "English"), horizontal=True, label_visibility="collapsed")

if language == "한국어":
    st.title("🌡️ 실시간 날씨 대시보드")
    gps_button_text = "📍 내 위치로 날씨 보기 (GPS)"
    reset_text = "🔄 위치/데이터 초기화"
    labels = ["습도", "체감 온도", "자외선", "달의 모양", "풍속", "최고", "최저", "강수 확률"]
    hot_msg = "폭염 주의! 🥵"
else:
    st.title("🌡️ Weather Dashboard")
    gps_button_text = "📍 Use Current Location"
    reset_text = "🔄 Reset Location & Data"
    labels = ["Humidity", "Feels Like", "UV Index", "Moon Phase", "Wind", "Max", "Min", "Rain Chance"]
    hot_msg = "Heatwave Warning! 🥵"

st.markdown("---")

# 6. 위치 및 도시 선택 로직
target_location = None
display_name = ""

def clear_gps():
    st.session_state.user_location = None
    # 드롭다운을 만지면 GPS 정보만 지우고, auto_gps_done은 건드리지 않아서 다시 GPS를 잡지 않게 합니다.

# [핵심 수정] GPS 수동 버튼 로직 개선
if st.button(gps_button_text, use_container_width=True):
    st.info("위치 정보를 요청 중입니다..." if language=="한국어" else "Requesting location...")
    st.session_state.auto_gps_done = False # 버튼을 누르면 다시 GPS를 잡도록 허용
    st.session_state.user_location = None
    st.rerun() # 브라우저 새로고침(reload) 대신 부드러운 rerun 사용

col1, col2 = st.columns(2)
with col1:
    selected_country = st.selectbox("Country", list(countries_cities.keys()), on_change=clear_gps, label_visibility="collapsed")
with col2:
    display_city = st.selectbox("City", countries_cities[selected_country], on_change=clear_gps, label_visibility="collapsed")

# 우선순위 결정: GPS > 선택한 도시
if st.session_state.user_location and 'coords' in st.session_state.user_location:
    coords = st.session_state.user_location['coords']
    target_location = f"{coords['latitude']},{coords['longitude']}"
    display_name = "📍 현재 내 위치 (GPS)" if language == "한국어" else "📍 Current Location"
    
    if st.button(reset_text):
        st.session_state.user_location = None
        st.rerun()
else:
    target_location = display_city.split(" (")[0]
    display_name = display_city

# 7. 날씨 데이터 호출
if target_location:
    timestamp = int(time.time())
    url = f"http://api.weatherapi.com/v1/forecast.json?key={API_KEY}&q={target_location}&days=2&aqi=no&lang=ko&t={timestamp}"
    
    try:
        response = requests.get(url)
        if response.status_code != 200:
            st.error(f"API Error: {response.status_code}")
        else:
            data = response.json()
            curr = data['current']
            f_today = data['forecast']['forecastday'][0]
            f_tomorrow = data['forecast']['forecastday'][1]

            st.markdown(f"### {display_name}")
            
            h1, h2 = st.columns([0.2, 0.8])
            with h1: st.image("https:" + curr['condition']['icon'], width=100)
            with h2:
                st.subheader(f"{curr['temp_c']}°C")
                st.write(f"**{curr['condition']['text']}**")
            
            if curr['temp_c'] >= 32: st.warning(hot_msg)

            st.markdown("#### 📊 Detail")
            m1, m2, m3 = st.columns(3)
            m1.metric(labels[1], f"{curr['feelslike_c']}°C")
            m2.metric(labels[0], f"{curr['humidity']}%")
            m3.metric(labels[2], f"{curr['uv']}")

            st.markdown("---")
            
            i1, i2 = st.columns(2)
            with i1:
                st.write(f"💨 **{labels[4]}:** {curr['wind_kph']} km/h")
                m_phase = f_today['astro']['moon_phase']
                st.write(f"🌙 **{labels[3]}:** {moon_phase_ko.get(m_phase, m_phase) if language=='한국어' else m_phase}")
            with i2:
                st.markdown(f"**📅 {'내일 예보' if language=='한국어' else 'Tomorrow'}**")
                st.write(f"📈 {labels[5]}/{labels[6]}: {f_tomorrow['day']['maxtemp_c']}°C / {f_tomorrow['day']['mintemp_c']}°C")
                st.write(f"☔ {labels[7]}: {f_tomorrow['day']['daily_chance_of_rain']}%")

            st.caption(f"Last Update: {curr['last_updated']}")

    except Exception as e:
        st.error(f"Connection Error: {e}")