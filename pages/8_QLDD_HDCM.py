import streamlit as st
import pandas as pd
import gspread
from datetime import datetime
from zoneinfo import ZoneInfo
import pathlib
import base64
from google.oauth2.service_account import Credentials
import re

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

@st.cache_data(ttl=3600)
def get_img_as_base64(file):
    with open(file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

def load_css(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except UnicodeDecodeError:
        # Fallback to different encoding if UTF-8 fails
        with open(file_path, 'r', encoding='latin-1') as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def load_data(x):
    credentials = load_credentials()
    gc = gspread.authorize(credentials)
    sheet = gc.open(x).sheet1
    data = sheet.get_all_values()
    header = data[0]
    values = data[1:]
    data_final = pd.DataFrame(values, columns=header)
    return data_final

@st.cache_data(ttl=600)  #Thời gian cache tự load lại file sau 10 phút
def load_sheet_by_name(sheet_name, worksheet_name):
    try:
        credentials = load_credentials()
        gc = gspread.authorize(credentials)
        spreadsheet = gc.open(sheet_name)
        try:
            sheet = spreadsheet.worksheet(worksheet_name)
            data = sheet.get_all_values()
        except gspread.exceptions.WorksheetNotFound:
            worksheet_map = {
                "Sheet 0": 0, "Sheet 1": 1, "Sheet 2": 2,
            }
            if worksheet_name in worksheet_map:
                idx = worksheet_map[worksheet_name]
                sheet = spreadsheet.get_worksheet(idx)
                data = sheet.get_all_values()
            else:
                sheet = spreadsheet.get_worksheet(0)
                data = sheet.get_all_values()
        if len(data) > 0:
            header = data[0]
            values = data[1:]
            return pd.DataFrame(values, columns=header)
        return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()

def thong_tin_hanh_chinh():
    sheeti1 = st.secrets["sheet_name"]["input_1"]
    data_nv = load_data(sheeti1)
    chon_khoa = st.selectbox("Khoa/Đơn vị ",
                             options=data_nv["Khoa"].unique(),
                             index=None,
                             placeholder="",
                             )
    if chon_khoa:
        st.session_state.khoa_qldd = chon_khoa
    else:
        if "khoa_qldd" in st.session_state:
            del st.session_state["khoa_qldd"]

def bang_kiem():
    sheeti1 = st.secrets["sheet_name"]["input_8"]
    data_qldd1 = load_sheet_by_name(sheeti1, "Sheet 0")
    chon_bang_kiem = st.selectbox("Tên bảng kiểm",
                            options=data_qldd1["Tên bảng kiểm"].unique(),
                            index=None,
                            placeholder="",
                            )
    if chon_bang_kiem:
        st.session_state.chon_bang_kiem = chon_bang_kiem
    else:
        if "vtgs_HSBA" in st.session_state:
            del st.session_state["vtgs_HSBA"]

@st.dialog("Thông báo")
def warning(x,y):
    if x == 1:
        st.warning(f"Vui lòng kiểm tra lại các bước sau: {y}")
    if x == 2:
        st.warning("Vui lòng điền đầy đủ số vào viện và năm sinh người bệnh")
    if x == 3:
        st.success("Đã lưu thành công")    
    if x == 4:
        st.warning("Số vào viện không hợp lệ. Vui lòng nhập lại VD: 25-1234567")
    if x == 5:
        st.warning("⚠️ Bạn đã gửi kết quả này rồi!")


# Main ####################################################################################
img = get_img_as_base64("pages/img/logo.png")
css_path = pathlib.Path("asset/style.css")
load_css(css_path)
st.markdown(f"""
    <div class="fixed-header">
        <div class="header-content">
            <img src="data:image/png;base64,{img}" alt="logo">
            <div class="header-text">
                <h1>BỆNH VIỆN ĐẠI HỌC Y DƯỢC THÀNH PHỐ HỒ CHÍ MINH<span style="vertical-align: super; font-size: 0.6em;">&#174;</span><br><span style="color:#c15088">Phòng Điều dưỡng</span></h1>
            </div>
        </div>
        <div class="header-subtext">
        <p>NHẬP KẾT QUẢ ĐÁNH GIÁ QLĐD VÀ HĐCM </p>
        </div>
    </div>
    <div class="header-underline"></div>
 """, unsafe_allow_html=True)
html_code = f'<p class="demuc"><i>Nhân viên nhập: {st.session_state.username}</i></p>'
st.html(html_code)
thong_tin_hanh_chinh()
sheeti8 = st.secrets["sheet_name"]["input_8"]
data_qldd = load_sheet_by_name(sheeti8, "Sheet 0")
now_vn = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
bang_kiem()
st.divider()
if "chon_bang_kiem" in st.session_state is not None:
    st.markdown('''
    <h4><span style="color:#003b62">Phần đánh giá hồ sơ bệnh án
                </span></h4>
''',unsafe_allow_html=True)