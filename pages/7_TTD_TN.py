import streamlit as st
import pandas as pd
import gspread
from datetime import datetime, timedelta    
from zoneinfo import ZoneInfo
import pathlib
import base64
import time
import locale
from google.oauth2.service_account import Credentials
# FS

# Thiết lập locale để đảm bảo dấu thập phân nhất quán
try:
    locale.setlocale(locale.LC_NUMERIC, 'C') # Sử dụng định dạng số chuẩn quốc tế
except:
    pass  # Nếu không set được, bỏ qua

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
    if st.session_state.get("ngay_dieu_tri") is None:
        noi_dung_thieu.append("Ngày điều trị")
    if st.session_state.get("hien_mac") is None:
        noi_dung_thieu.append("Số ca loét hiện mắc")
    if st.session_state.get("mac_moi") is None:
        noi_dung_thieu.append("Số ca loét mắc mới")
    if st.session_state.get("te_nga") is None:
        noi_dung_thieu.append("Số ca té ngã")
    return noi_dung_thieu

@st.dialog("Thông báo")
def warning(x):
    if x == 1:
        st.warning("Vui lòng nhập đầy đủ nội dung báo cáo")
        time.sleep(1)
    if x == 2:
        st.success("Đã lưu thành công")
        time.sleep(1)

def upload_data_PCCS():
    credentials = load_credentials()
    gc = gspread.authorize(credentials)
    sheeto10 = st.secrets["sheet_name"]["output_10"]
    sheet = gc.open(sheeto10).sheet1
    column_index = len(sheet.get_all_values())
    now_vn = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))  
    column_timestamp = now_vn.strftime('%Y-%m-%d %H:%M:%S')
    column_thoi_gian_bao_cao = f"{st.session_state.nam_bao_cao}-{st.session_state.thang_bao_cao:02d}"
    column_nguoi_bao_cao = str(st.session_state.username)
    column_ngay_dieu_tri = int(st.session_state.get("ngay_dieu_tri", 0))
    column_hien_mac = int(st.session_state.get("hien_mac", 0))
    column_mac_moi = int(st.session_state.get("mac_moi", 0))
    column_te_nga = int(st.session_state.get("te_nga", 0))
  
    sheet.append_row([column_index,column_timestamp,column_thoi_gian_bao_cao,column_nguoi_bao_cao,
                      column_ngay_dieu_tri,column_hien_mac,column_mac_moi,
                      column_te_nga
                     ])


def clear_form_state():
    for key in ["nam_bao_cao","thang_bao_cao","ngay_dieu_tri", "hien_mac", "mac_moi", "te_nga"]:
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
        <p>BÁO CÁO SỐ LIỆU TỔN THƯƠNG DA DO ÁP LỰC VÀ TÉ NGÃ </p>
        </div>
    </div>
    <div class="header-underline"></div>
     """, unsafe_allow_html=True)
html_code = f'<p class="demuc"><i>Nhân viên báo cáo: {st.session_state.username}</i></p>'
st.html(html_code)

now_vn = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
if "nam_bao_cao" not in st.session_state:
    st.session_state.nam_bao_cao = now_vn.year
if "thang_bao_cao" not in st.session_state:
    st.session_state.thang_bao_cao = now_vn.month

col1, col2 = st.columns(2)
with col1:
    nam_list = list(range(2020, now_vn.year + 1))
    nam = st.selectbox(
        label="Năm báo cáo",
        options=nam_list,
        key="nam_bao_cao"
    )
with col2:
    thang = st.selectbox(
        label="Tháng báo cáo",
        options=list(range(1, 13)),
        format_func=lambda x: f"Tháng {x}",
        key="thang_bao_cao"
    )


# Hiển thị tháng/năm đã chọn
st.info(f"📅 Báo cáo số liệu cho: **Tháng {st.session_state.thang_bao_cao}/{st.session_state.nam_bao_cao}**")

st.divider()

ngay_dieu_tri = st.number_input(
                label="Ngày điều trị",
                step=1,
                key=f"ngay_dieu_tri"
            )

st.markdown("**:orange[I. Tổn thương da do áp lực]**")

hien_mac = st.number_input(
                label="Số ca tổn thương da do áp lực HIỆN MẮC",
                step=1,
                key=f"hien_mac"
            )

mac_moi = st.number_input(
                label="Số ca tổn thương da do áp lực MẮC MỚI",
                step=1,
                key=f"mac_moi"
            )

st.markdown("**:orange[II. Té ngã]**")

te_nga = st.number_input(
                label="Số ca té ngã trong tháng",
                step=1,
                key=f"te_nga"
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