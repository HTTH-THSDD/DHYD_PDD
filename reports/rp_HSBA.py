import streamlit as st
import pandas as pd
import gspread
import datetime
import pathlib
import base64
from google.oauth2.service_account import Credentials
import numpy as np

@st.cache_data(ttl=3600)
def get_img_as_base64(file):
    with open(file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

def load_css(file_path):
    with open(file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
css_path = pathlib.Path("asset/style.css")

@st.cache_data(ttl=10)
def get_key_from_value(dictionary, value):
    return next((key for key, val in dictionary.items() if val == value), None)
@st.cache_data(ttl=3600)
def load_credentials():
    creds_info = {
    "type": st.secrets["google_service_account"]["type"],
    "project_id": st.secrets["google_service_account"]["project_id"],
    "private_key_id": st.secrets["google_service_account"]["private_key_id"],
    "private_key": st.secrets["google_service_account"]["private_key"],
    "client_email": st.secrets["google_service_account"]["client_email"],
    "client_id": st.secrets["google_service_account"]["client_id"],
    "auth_uri": st.secrets["google_service_account"]["auth_uri"],
    "token_uri": st.secrets["google_service_account"]["token_uri"],
    "auth_provider_x509_cert_url": st.secrets["google_service_account"]["auth_provider_x509_cert_url"],
    "client_x509_cert_url": st.secrets["google_service_account"]["client_x509_cert_url"],
    "universe_domain": st.secrets["google_service_account"]["universe_domain"],
    }
    # Dùng để kết nối Google APIs
    credentials = Credentials.from_service_account_info(
        creds_info,
        scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    )
    return credentials

@st.cache_data(ttl=10)
def load_data(x,sd,ed):
    credentials = load_credentials()
    gc = gspread.authorize(credentials)
    sheet = gc.open(x).sheet1
    data = sheet.get_all_values()
    header = data[0]
    values = data[1:]
    data = pd.DataFrame(values, columns=header)
    data['Timestamp'] = pd.to_datetime(data['Timestamp'], errors='coerce')
    start_date = sd
    end_date = ed + datetime.timedelta(days=1)
    data_final = data[(data['Timestamp'] >= pd.Timestamp(start_date)) & (data['Timestamp'] < pd.Timestamp(end_date))]
    return data_final

def tao_thong_ke(x,y):
    df = pd.DataFrame(x)
    if y == "Chi tiết":
        df = pd.DataFrame(df).sort_values(["Timestamp","Khoa"])
        df.insert(0, 'STT', range(1, len(df) + 1))
        if st.session_state.phan_quyen == "4" and st.session_state.username not in ["Trần Thị Bích Thủy (E98-020)","Nguyễn Thị Thanh Trúc (D05-118)","Phạm Hồng Khuyên (D05-066)"]:
            df = df.drop("Khoa",axis=1)
        return df
    else:
        df = pd.DataFrame(df).sort_values("Khoa")
        df.insert(0, 'STT', range(1, len(df) + 1))
        if st.session_state.phan_quyen == "4" and st.session_state.username not in ["Trần Thị Bích Thủy (E98-020)","Nguyễn Thị Thanh Trúc (D05-118)","Phạm Hồng Khuyên (D05-066)"]:
            df=df.drop("Khoa",axis=1)
        return df
##################################### Main Section ###############################################
load_css(css_path)
img = get_img_as_base64("pages/img/logo.png")
st.markdown(f"""
    <div class="fixed-header">
        <div class="header-content">
            <img src="data:image/png;base64,{img}" alt="logo">
            <div class="header-text">
                <h1>BỆNH VIỆN ĐẠI HỌC Y DƯỢC THÀNH PHỐ HỒ CHÍ MINH<br><span style="color:#c15088">Phòng Điều dưỡng</span></h1>
            </div>
        </div>
        <div class="header-subtext">
        <p style="color:green">BÁO CÁO GIÁM SÁT QUY TRÌNH KỸ THUẬT</p>
        </div>
    </div>
    <div class="header-underline"></div>

 """, unsafe_allow_html=True)
html_code = f'<p class="demuc"><i>Điều dưỡng: {st.session_state.username}</i></p>'
st.html(html_code)
with st.form("Thời gian"):
    cold = st.columns([5,5])
    with cold[0]:
        sd = st.date_input(
        label="Ngày bắt đầu",
        value=datetime.date(2025, 1, 1),
        min_value=datetime.date(2025, 1, 1),
        max_value=datetime.date.today(), 
        format="DD/MM/YYYY",
        )
    with cold[1]:
        ed = st.date_input(
        label="Ngày kết thúc",
        value=datetime.date.today(),
        min_value=datetime.date(2025, 1, 1),
        max_value=datetime.date.today(), 
        format="DD/MM/YYYY",
        )
    submit_thoigian = st.form_submit_button("Xem thống kê")
if submit_thoigian:
    if ed < sd:
        st.error("Ngày kết thúc đến trước ngày bắt đầu. Vui lòng chọn lại")  
    else:
        data = load_data("Output-st-HSBA",sd,ed)
        if st.session_state.phan_quyen == "4":
            if st.session_state.username == "Trần Thị Bích Thủy (E98-020)":
                data = data.loc[data["Khoa"].isin([
                        "Khoa Gây mê hồi sức - Gây mê",
                        "Khoa Gây mê hồi sức - Hồi tỉnh",
                        "Khoa Gây mê hồi sức - Dụng cụ"
                    ])]
            elif st.session_state.username == "Phạm Hồng Khuyên (D05-066)":
                data = data.loc[data["Khoa"].isin([
                        "Khoa Ngoại Thần kinh",
                        "Khoa Nội Cơ Xương Khớp",
                    ])]
            elif st.session_state.username == "Nguyễn Thị Thanh Trúc (D05-118)":
                data = data.loc[data["Khoa"].isin([
                        "Khoa Lồng ngực mạch máu",
                        "Khoa Tiết niệu",
                    ])]
            else:
                data = data.loc[data["Khoa"]==st.session_state.khoa]
        if data.empty:
            st.warning("Không có dữ liệu theo yêu cầu")
        else:
            with st.expander("Thống kê tổng quát"):
                thongke = tao_thong_ke(data,"Tổng quát")
                st.dataframe(thongke, 
                            hide_index=True)
            with st.expander("Thống kê chi tiết"):
                thongkechitiet = tao_thong_ke(data,"Chi tiết")
                st.dataframe(thongkechitiet,
                        hide_index=True)
st.write("Chưa biết thống kê chỉ số như nào")

    


