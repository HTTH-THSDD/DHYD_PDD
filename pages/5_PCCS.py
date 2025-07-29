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
    with open(file_path) as f:
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
    column_index = len(sheet.get_all_values())  
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
        st.session_state.ti_le = ti_le_sang
        ti_le_chieu = round(SL_NB_cap_1c/SL_DD_cap_1c,2)
        st.session_state.ti_le = ti_le_chieu
        ti_le_toi = round(SL_NB_cap_1t/SL_DD_cap_1t,2)
        st.session_state.ti_le = ti_le_toi
    sheet.append_row([column_index, column_timestamp, column_ngay_bao_cao,
                       column_khoa_bao_cao, column_nguoi_bao_cao, column_data,ti_le_sang,ti_le_chieu,ti_le_toi])

def clear_form_state():
    for key in ["chon_khoa", "ngay_bao_cao", "SL_NB_cap_1s", "SL_DD_cap_1s","SL_NB_cap_1c", "SL_DD_cap_1c","SL_NB_cap_1t", "SL_DD_cap_1t"]:
        if key in st.session_state:
            del st.session_state[key]

# Main Section ####################################################################################
css_path = pathlib.Path("asset/style_4_VTTB.css")
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
st.markdown("❗:red[***Lưu ý: Ngày báo cáo đang được mặc định là ngày hôm qua.***]")
if st.session_state.get("dmk", False):
        if time.time() - st.session_state.get("dmk_time", 0) < 5:
            st.toast("Báo cáo đã được gửi thành công")
        else:
            del st.session_state["dmk"]
            del st.session_state["dmk_time"]
# Báo cáo ca sáng
col1s, col2s,col3s = st.columns(3)
with col1s:
    Ca_Sang = st.markdown("**Ca sáng (7g00 - 14g00)**")
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
col1c, col2c,col3c = st.columns(3)
with col1c:
    Ca_Chieu = st.markdown("**Ca chiều (14g00 - 21g00)**")
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
col1t, col2t,col3t = st.columns(3)
with col1t:
    Ca_Toi = st.markdown("**Ca tối (21g00 - 7g00)**")
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
col_left, col_center, col_right = st.columns([1,2,1])
with col_center:
    Gui= st.button("Gửi báo cáo",type='primary', key="bao_cao") 
    if Gui:
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

