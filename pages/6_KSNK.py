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
        time.sleep(1)
    if x == 2:
        st.success("Đã lưu thành công")
        time.sleep(1)

def upload_data_PCCS():
    credentials = load_credentials()
    gc = gspread.authorize(credentials)
    sheeto9 = st.secrets["sheet_name"]["output_9"]
    sheet = gc.open(sheeto9).sheet1
    column_index = len(sheet.get_all_values())
    now_vn = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))  
    column_timestamp = now_vn.strftime('%Y-%m-%d %H:%M:%S')
    column_thoi_gian_bao_cao = f"{st.session_state.nam_bao_cao}-{st.session_state.thang_bao_cao:02d}"
    column_nguoi_bao_cao = str(st.session_state.username)
    nkbv_moi = round(float(st.session_state.get("nkbv_moi", 0)),4)
    nkbv_moi_hoi_suc = round(float(st.session_state.get("nkbv_moi_hoi_suc", 0)),4)
    VAP = round(float(st.session_state.get("VAP", 0)),4)
    CLABSI = round(float(st.session_state.get("CLABSI", 0)),4)
    CAUTI = round(float(st.session_state.get("CAUTI", 0)),4)
    vst_truc_tiep = round(float(st.session_state.get("vst_truc_tiep", 0)),3)
    vst_camera = round(float(st.session_state.get("vst_camera", 0)),3)
    vst_ngoai_khoa = round(float(st.session_state.get("vst_ngoai_khoa", 0)),3)
  
    sheet.append_row([column_index,column_timestamp,column_thoi_gian_bao_cao,column_nguoi_bao_cao,nkbv_moi,nkbv_moi_hoi_suc,VAP,CLABSI,CAUTI,vst_truc_tiep,vst_camera,vst_ngoai_khoa])


def clear_form_state():
    for key in ["nam_bao_cao","thang_bao_cao","nkbv_moi", "nkbv_moi_hoi_suc", "VAP", "CLABSI", "CAUTI", "vst_truc_tiep", "vst_camera", "vst_ngoai_khoa"]:
        if key in st.session_state:
            del st.session_state[key]


def number_input_custom(label, key, step=0.0001, format_str="%.4f", help_text=None, label_color="#005259", label_size="15px"):
    st.markdown(
        f'<p style="color: {label_color}; font-size: {label_size}; font-weight: bold;">{label}</p>',
        unsafe_allow_html=True
    )
    current_value = st.session_state.get(key, None)
    default_text = format_str % current_value if current_value is not None else ""
    text_value = st.text_input(
        label=label,
        value= default_text,
        key=f"{key}_text",
        placeholder=f"VD: {format_str % step}",
        help=help_text or f"Nhập số thập phân. Có thể dùng dấu chấm (.) hoặc dấu phẩy (,). VD: {format_str % (step*10)}",
        label_visibility="collapsed",
    )
    if text_value and text_value.strip():
        try:
            cleaned_value = text_value.strip().replace(',', '.')
            number_value = float(cleaned_value)
            st.session_state[key] = number_value
            return number_value     
        except ValueError:
            st.error("❌")
            st.session_state[key] = None
            return None
    else:
        st.session_state[key] = None
        st.write("")  # Placeholder để giữ layout
        return None



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
if "nam_bao_cao" not in st.session_state:
    st.session_state.nam_bao_cao = now_vn.year
if "thang_bao_cao" not in st.session_state:
    st.session_state.thang_bao_cao = now_vn.month

col1, col2 = st.columns(2)
with col1:
    nam_list = list(range(2024, now_vn.year + 1))
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

nkbv_moi = number_input_custom(
                label="Tỷ suất mắc mới NKBV toàn viện",
                step=0.0001,
                format_str="%.4f",
                key=f"nkbv_moi"
            )

st.markdown("**:orange[I. Tỷ suất mắc mới NKBV tại Khối Hồi sức]**")

nkbv_moi_hoi_suc = number_input_custom(
                label="Nhiễm khuẩn bệnh viện/ 1000 người bệnh",
                step=0.0001,
                format_str="%.4f",
                key=f"nkbv_moi_hoi_suc"
            )

VAP = number_input_custom(
                label="Viêm phổi bệnh viện liên quan đến thở máy (VAP)/1000 máy thở-ngày",
                step=0.0001,
                format_str="%.4f",
                key=f"VAP"
            )

CLABSI = number_input_custom(
                label="Nhiễm khuẩn liên quan đến catheter (CLABSI)/1000 catheter-ngày",
                step=0.0001,
                format_str="%.4f",                
                key=f"CLABSI"
            )

CAUTI = number_input_custom(
                label="Nhiễm khuẩn tiết niệu liên quan đến thông tiểu (CAUTI)/1000 thông tiểu-ngày",
                step=0.0001,
                format_str="%.4f",
                key=f"CAUTI"
            )

st.markdown("**:orange[II. Vệ sinh tay]**")

vst_truc_tiep = number_input_custom(
                label="Tỷ lệ tuân thủ VST thường quy (quan sát trực tiếp)",
                step=0.001,
                format_str="%.3f",
                key=f"vst_truc_tiep"
            )

vst_camera = number_input_custom(
                label="Tỷ lệ tuân thủ VST thường quy (quan sát qua camera)",
                step=0.001,
                format_str="%.3f",
                key=f"vst_camera"
            )

vst_ngoai_khoa = number_input_custom(
                label="Tỷ lệ tuân thủ VST ngoại khoa",
                step=0.001,
                format_str="%.3f",
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
