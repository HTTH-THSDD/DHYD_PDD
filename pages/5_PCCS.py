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
    if st.session_state.get("chon_khoa") is None:
        noi_dung_thieu.append("Khoa báo cáo")
    if st.session_state.get("ngay_bao_cao") is None:
        noi_dung_thieu.append("Ngày báo cáo")
    if st.session_state.get("SL_NB_cap_1s") is None:
        noi_dung_thieu.append("Số người bệnh PCCS cấp I ca sáng")
    if st.session_state.get("SL_DD_cap_1s") is None:
        noi_dung_thieu.append("Số điều dưỡng PCCS cấp I ca sáng")
    if st.session_state.get("SL_NB_cap_1c") is None:
        noi_dung_thieu.append("Số người bệnh PCCS cấp I ca chiều")
    if st.session_state.get("SL_DD_cap_1c") is None:
        noi_dung_thieu.append("Số điều dưỡng PCCS cấp I ca chiều")
    if st.session_state.get("SL_NB_cap_1t") is None:
        noi_dung_thieu.append("Số người bệnh PCCS cấp I ca tối")
    if st.session_state.get("SL_DD_cap_1t") is None:
        noi_dung_thieu.append("Số điều dưỡng PCCS cấp I ca tối")
    return noi_dung_thieu


@st.dialog("Thông báo")
def warning(x):
    if x == 1:
        st.warning("Vui lòng nhập đầy đủ nội dung báo cáo")
    if x == 2:
        st.warning("Lỗi nhập kết quả không hợp lí: số Điều dưỡng chăm sóc bằng 0")
    if x == 3:
        st.success("Đã lưu thành công")

def upload_data_PCCS():
    credentials = load_credentials()
    gc = gspread.authorize(credentials)
    sheeto8 = st.secrets["sheet_name"]["output_8"]
    sheet = gc.open(sheeto8).sheet1

    all_values = sheet.get_all_values()
    if len(all_values) > 1:
        try:
            new_stt = int(all_values[-1][0]) + 1
        except:
            new_stt = len(all_values)
    else:
        new_stt = 1

    now_vn = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))  
    column_timestamp = now_vn.strftime('%Y-%m-%d %H:%M:%S')
    column_ngay_bao_cao = st.session_state.ngay_bao_cao.strftime('%Y-%m-%d')
    column_khoa_bao_cao = str(st.session_state.chon_khoa)
    column_nguoi_bao_cao = str(st.session_state.username)
    SL_NB_cap_1s = int(st.session_state.get("SL_NB_cap_1s", 0))
    SL_DD_cap_1s = int(st.session_state.get("SL_DD_cap_1s", 0))
    SL_NB_cap_1c = int(st.session_state.get("SL_NB_cap_1c", 0))
    SL_DD_cap_1c = int(st.session_state.get("SL_DD_cap_1c", 0))
    SL_NB_cap_1t = int(st.session_state.get("SL_NB_cap_1t", 0))
    SL_DD_cap_1t = int(st.session_state.get("SL_DD_cap_1t", 0))
    column_data = (
        f"Ca sáng (7g00 - 14g00)|{SL_NB_cap_1s}|{SL_DD_cap_1s}"
        f"#Ca chiều (14g00 - 21g00)|{SL_NB_cap_1c}|{SL_DD_cap_1c}"
        f"#Ca đêm (21g00 - 7g00)|{SL_NB_cap_1t}|{SL_DD_cap_1t}"
    )

    if SL_DD_cap_1s == 0 or SL_DD_cap_1c == 0 or SL_DD_cap_1t == 0:
        warning(2)
        st.stop()
    else:
        ti_le_sang = round(SL_NB_cap_1s/SL_DD_cap_1s,2)
        ti_le_chieu = round(SL_NB_cap_1c/SL_DD_cap_1c,2)
        ti_le_toi = round(SL_NB_cap_1t/SL_DD_cap_1t,2)

        # Tạo dòng dữ liệu mới để append
        new_row = [
            new_stt,
            column_timestamp,
            column_ngay_bao_cao,
            column_khoa_bao_cao,
            column_nguoi_bao_cao,
            column_data,
            ti_le_sang,
            ti_le_chieu,
            ti_le_toi
        ]
        next_row = len(all_values) + 1
        range_to_update = f'A{next_row}:I{next_row}'
        sheet.update(range_to_update, [new_row], value_input_option='USER_ENTERED')        
        st.toast("✅ Báo cáo đã được gửi thành công")
        st.cache_data.clear()

def clear_form_state():
    for key in ["chon_khoa", "ngay_bao_cao", "SL_NB_cap_1s", "SL_DD_cap_1s","SL_NB_cap_1c", "SL_DD_cap_1c","SL_NB_cap_1t", "SL_DD_cap_1t"]:
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
        <p>NGƯỜI BỆNH PCCS CẤP I/ ĐIỀU DƯỠNG</p>
        </div>
    </div>
    <div class="header-underline"></div>
 """, unsafe_allow_html=True)
html_code = f'<p class="demuc"><i>Nhân viên báo cáo: {st.session_state.username}</i></p>'
st.html(html_code)
chon_khoa = st.selectbox("Khoa/Đơn vị báo cáo",
                             options=["Đơn vị Gây mê hồi sức Phẫu thuật tim mạch",
                                      "Đơn vị Hồi sức Ngoại Thần kinh",
                                      "Khoa Hô hấp",
                                      "Khoa Hồi sức tích cực",
                                      "Khoa Thần kinh",
                                      "Khoa Nội Tim mạch",
                                      "Khoa Phẫu thuật tim mạch",
                                      "Khoa Tim mạch can thiệp"],
                             index=None,
                             placeholder="",
                             key="chon_khoa",
                             )

now_vn = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
default_date = now_vn.date() - timedelta(days=1)
st.date_input(
    label="Ngày báo cáo",
    value = default_date,
    format="DD/MM/YYYY",
    key="ngay_bao_cao",
    max_value= default_date,
)
st.markdown(":red[***📌Lưu ý: Ngày báo cáo tự động hiển thị giá trị mặc định trước ngày hiện tại.***]")
if st.session_state.get("dmk", False):
        if time.time() - st.session_state.get("dmk_time", 0) < 5:
            st.toast("Báo cáo đã được gửi thành công")
        else:
            del st.session_state["dmk"]
            del st.session_state["dmk_time"]
# Báo cáo ca sáng
st.markdown('''
    <p class="subtitle-pccs">
        <span style="color: #0e0bf7; font-weight: bold;">
            Ca sáng (7g00 - 14g00)
        </span>
    </p>
''', unsafe_allow_html=True)
col1s, col2s,col3s = st.columns([1,9,9])
with col2s:    
    SL_NB_cap_1 = st.number_input(
                    label="Số người bệnh",
                    value=st.session_state.get("SL_NB_cap_1s", None),
                    step=1,  # Chuyển đổi giá trị thành số nguyên
                    placeholder="sáng",
                    key=f"SL_NB_cap_1s"
                )
with col3s:
    SL_DD_cap_1 = st.number_input(
                    label="Số điều dưỡng",
                    value=st.session_state.get("SL_DD_cap_1s", None),
                    step=1,  # Chuyển đổi giá trị thành số nguyên
                    placeholder="sáng",
                    key=f"SL_DD_cap_1s"
                )

# Báo cáo ca chiều
st.markdown('''
    <p class="subtitle-pccs">
        <span style="color: #0e0bf7; font-weight: bold;">
            Ca chiều (14g00 - 21g00)
        </span>    
    </p>
''', unsafe_allow_html=True)
col1c, col2c,col3c = st.columns([1,9,9])
with col2c:    
    SL_NB_cap_1 = st.number_input(
                    label="Số người bệnh",
                    value=st.session_state.get("SL_NB_cap_1c", None),
                    step=1,  # Chuyển đổi giá trị thành số nguyên
                    placeholder="chiều",
                    key=f"SL_NB_cap_1c"
                )
with col3c:
    SL_DD_cap_1 = st.number_input(
                    label="Số điều dưỡng",
                    value=st.session_state.get("SL_DD_cap_1c", None),
                    step=1,  # Chuyển đổi giá trị thành số nguyên
                    placeholder="chiều",
                    key=f"SL_DD_cap_1c"
                )

# Báo cáo ca tối
st.markdown('''
    <p class="subtitle-pccs">
        <span style="color: #0e0bf7; font-weight: bold;">    
            Ca tối (21g00 - 7g00)
        </span>    
    </p>
''', unsafe_allow_html=True)
col1t, col2t,col3t = st.columns([1,9,9])
with col2t:    
    SL_NB_cap_1 = st.number_input(
                    label="Số người bệnh",
                    value=st.session_state.get("SL_NB_cap_1t", None),
                    step=1,  # Chuyển đổi giá trị thành số nguyên
                    placeholder="tối",
                    key=f"SL_NB_cap_1t"
                )
with col3t:
    SL_DD_cap_1 = st.number_input(
                    label="Số điều dưỡng",
                    value=st.session_state.get("SL_DD_cap_1t", None),
                    step=1,  # Chuyển đổi giá trị thành số nguyên
                    placeholder="tối",
                    key=f"SL_DD_cap_1t"
                )
st.markdown('''<br><br>''', unsafe_allow_html=True)
# Thời gian hiển thị nút (giây)
# show_time = 10

# Kiểm tra nếu chưa hết thời gian thì hiển thị nút
# if time.time() - st.session_state.show_gui_time < show_time:
# st.markdown('''<div class="button-container">''', unsafe_allow_html=True)


Luu = st.button("Lưu kết quả", type='primary',key="luu")
if Luu:
    kiem_tra = kiem_tra()
    if len(kiem_tra) == 0:    
        upload_data_PCCS ()
        warning(3)
        clear_form_state()
        st.session_state.dmk = True
        st.session_state.dmk_time = time.time()
        st.rerun()
    else:
        warning(1)

