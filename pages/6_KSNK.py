import streamlit as st
import pandas as pd
import gspread
from datetime import datetime, timedelta    
from zoneinfo import ZoneInfo
import pathlib
import base64
import time
from google.oauth2.service_account import Credentials
# FS

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
def load_data(x):
    credentials = load_credentials()
    gc = gspread.authorize(credentials)
    sheet = gc.open(x).sheet1
    data = sheet.get_all_values()
    header = data[0]
    values = data[1:]
    data_final = pd.DataFrame(values, columns=header)
    return data_final

def kiem_tra():
    noi_dung_thieu=[]
    if st.session_state.get("nkbv_moi") is None:
        noi_dung_thieu.append("nkbv_moi")
    if st.session_state.get("nkbv_moi_hoi_suc") is None:
        noi_dung_thieu.append("nkbv_moi_hoi_suc")
    if st.session_state.get("VAP") is None:
        noi_dung_thieu.append("VAP")
    if st.session_state.get("CLABSI") is None:
        noi_dung_thieu.append("CLABSI")
    if st.session_state.get("CAUTI") is None:
        noi_dung_thieu.append("CAUTI")
    if st.session_state.get("vst_truc_tiep") is None:
        noi_dung_thieu.append("vst_truc_tiep")
    if st.session_state.get("vst_camera") is None:
        noi_dung_thieu.append("vst_camera")
    if st.session_state.get("vst_ngoai_khoa") is None:
        noi_dung_thieu.append("vst_ngoai_khoa")
    return noi_dung_thieu

@st.dialog("Thông báo")
def warning(x):
    if x == 1:
        st.warning("Vui lòng nhập đầy đủ nội dung báo cáo")
    if x == 2:
        st.success("Đã lưu thành công")

def upload_data_PCCS():
    credentials = load_credentials()
    gc = gspread.authorize(credentials)
    sheeto9 = st.secrets["sheet_name"]["output_9"]
    sheet = gc.open(sheeto9).sheet1
    column_index = len(sheet.get_all_values())
    now_vn = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))  
    column_timestamp = now_vn.strftime('%Y-%m-%d %H:%M:%S')
    column_ngay_bao_cao = st.session_state.ngay_bao_cao.strftime('%Y-%m-%d')
    column_nguoi_bao_cao = str(st.session_state.username)
    nkbv_moi = round(float(st.session_state.get("nkbv_moi", 0)),4)
    nkbv_moi_hoi_suc = round(float(st.session_state.get("nkbv_moi_hoi_suc", 0)),4)
    VAP = round(float(st.session_state.get("VAP", 0)),4)
    CLABSI = round(float(st.session_state.get("CLABSI", 0)),4)
    CAUTI = round(float(st.session_state.get("CAUTI", 0)),4)
    vst_truc_tiep = round(float(st.session_state.get("vst_truc_tiep", 0)),3)
    vst_camera = round(float(st.session_state.get("vst_camera", 0)),3)
    vst_ngoai_khoa = round(float(st.session_state.get("vst_ngoai_khoa", 0)),3)
  
    sheet.append_row([column_index,column_timestamp,column_ngay_bao_cao,column_nguoi_bao_cao,nkbv_moi,nkbv_moi_hoi_suc,VAP,CLABSI,CAUTI,vst_truc_tiep,vst_camera,vst_ngoai_khoa])


def clear_form_state():
    for key in ["ngay_bao_cao", "nkbv_moi", "nkbv_moi_hoi_suc", "VAP", "CLABSI", "CAUTI", "vst_truc_tiep", "vst_camera", "vst_ngoai_khoa"]:
        if key in st.session_state:
            del st.session_state[key]

# Main Section ####################################################################################
css_path = pathlib.Path("asset/style.css")
load_css(css_path)
img = get_img_as_base64("pages/img/logo.png")
st.markdown(f"""
    <div class="fixed-header">
        <div class="header-content">
            <img src="data:image/png;base64,{img}" alt="logo">
            <div class="header-text">
                <h1>BỆNH VIỆN ĐẠI HỌC Y DƯỢC THÀNH PHỐ HỒ CHÍ MINH<span style="vertical-align: super; font-size: 0.6em;">&#174;</span><br><span style="color:#c15088">Phòng Điều dưỡng</span></h1>
            </div>
        </div>
        <div class="header-subtext">
        <p>BÁO CÁO SỐ LIỆU KSNK</p>
        </div>
    </div>
    <div class="header-underline"></div>
     """, unsafe_allow_html=True)
html_code = f'<p class="demuc"><i>Nhân viên báo cáo: {st.session_state.username}</i></p>'
st.html(html_code)

now_vn = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
st.date_input(
    label="Ngày báo cáo",
    value=now_vn.date(),
    format="DD/MM/YYYY",
    key="ngay_bao_cao",
    max_value=now_vn.date(),
)

st.divider()

nkbv_moi = st.number_input(
                label="Tỷ suất mắc mới NKBV toàn viện",
                value=st.session_state.get("nkbv_moi", None),
                step=0.0001,
                format="%.4f",
                key=f"nkbv_moi"
            )

st.markdown("**:orange[I. Tỷ suất mắc mới NKBV tại Khối Hồi sức]**")

nkbv_moi_hoi_suc = st.number_input(
                label="Nhiễm khuẩn bệnh viện/ 1000 người bệnh",
                value=st.session_state.get("nkbv_moi_hoi_suc", None),
                step=0.0001,
                format="%.4f",
                key=f"nkbv_moi_hoi_suc"
            )

VAP = st.number_input(
                label="Viêm phổi bệnh viện liên quan đến thở máy (VAP)/1000 máy thở-ngày",
                value=st.session_state.get("VAP", None),
                step=0.0001,
                format="%.4f",
                key=f"VAP"
            )

CLABSI = st.number_input(
                label="Nhiễm khuẩn liên quan đến catheter (CLABSI)/1000 catheter-ngày",
                value=st.session_state.get("CLABSI", None),
                step=0.0001,
                format="%.4f",                
                key=f"CLABSI"
            )

CAUTI = st.number_input(
                label="Nhiễm khuẩn tiết niệu liên quan đến thông tiểu (CAUTI)/1000 thông tiểu-ngày",
                value=st.session_state.get("CAUTI", None),
                step=0.0001,
                format="%.4f",
                key=f"CAUTI"
            )

st.markdown("**:orange[II. Vệ sinh tay]**")

vst_truc_tiep = st.number_input(
                label="Tỷ lệ tuân thủ VST thường quy (quan sát trực tiếp)",
                value=st.session_state.get("vst_truc_tiep", None),
                step=0.001,
                format="%.3f",
                key=f"vst_truc_tiep"
            )

vst_camera = st.number_input(
                label="Tỷ lệ tuân thủ VST thường quy (quan sát qua camera)",
                value=st.session_state.get("vst_camera", None),
                step=0.001,
                format="%.3f",
                key=f"vst_camera"
            )

vst_ngoai_khoa = st.number_input(
                label="Tỷ lệ tuân thủ VST ngoại khoa",
                value=st.session_state.get("vst_ngoai_khoa", None),
                step=0.001,
                format="%.3f",
                key=f"vst_ngoai_khoa"
            )

Luu = st.button("Lưu kết quả", type='primary',key="luu")
if Luu:
    kiem_tra = kiem_tra()
    if len(kiem_tra) == 0:    
        upload_data_PCCS ()
        warning(2)
        clear_form_state()
        st.session_state.dmk = True
        st.session_state.dmk_time = time.time()
        st.rerun()
    else:
        warning(1)
