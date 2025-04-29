import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import pathlib
import base64

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
    with open(file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def logout():
    for key in st.session_state.keys():  # Use list() to avoid runtime modification issues
        del st.session_state[key]
    st.rerun()

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

def doi_mat_khau(row, mkm1):
    credentials = load_credentials()
    gc = gspread.authorize(credentials)
    sheet = gc.open("Input-st-DSNS").sheet1
    mk= mkm1.upper()
    sheet.update_cell(row+2,22,mk)
    st.toast("Đổi mật khẩu thành công")

# Main Section ####################################################################################
css_path = pathlib.Path("asset/style.css")
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
        <p style="color:#9F2B68">ĐỔI MẬT KHẨU</p>
        </div>
    </div>
    <div class="header-underline"></div>

 """, unsafe_allow_html=True)
html_code = f'<p class="demuc"><i>Nhân viên gửi yêu cầu: {st.session_state.username}</i></p>'
st.html(html_code)
data = load_data("Input-st-DSNS")
if "nhap_sai" not in st.session_state:
    st.session_state.nhap_sai = 0
else:
    if st.session_state.nhap_sai >= 2:
        logout()
with st.form("Xác minh lại thông tin"):
    mkc = st.text_input("Mật khẩu cũ",type="password")
    mkm1 = st.text_input("Mật khẩu mới", type="password")
    mkm2 = st.text_input("Nhập lại mật khẩu mới", type="password", max_chars=15)
    submit = st.form_submit_button("Gửi")
if submit:
    if mkm1 != mkm2:
        st.warning("Vui lòng nhập 2 mật khẩu mới trùng khớp")
    else:
        mkc = mkc.upper()
        data1 = data.loc[data["Nhân viên"] == st.session_state.username]
        if mkc == data1["Mật khẩu"].tolist()[0]:
            row=data.index[data["Nhân viên"]==st.session_state.username].tolist()[0]
            doi_mat_khau(row,mkm1)
        else:
            st.session_state.nhap_sai +=1
            st.warning(f"Bạn đã nhập sai mặt khẩu cũ. Bạn còn {3-st.session_state.nhap_sai} lần thử")
        # if mkc == str(data1.at[0, "Mật khẩu"]):
        #     row = int(data.index[data["Nhân viên"]==st.session_state.username])
        #     doi_mat_khau(row,mkm1)
        # data1=data.loc[data["Mã nhân viên"]==mnv]
        # if data1.empty:
        #     st.warning("Mã nhân viên khôg tồn tại")
        # else:
        #     data1=data1.loc["Họ và tên"==ho_ten]
        #     if data1.empty:
        #         st.warning("Tên nhân viên không trùng khớp với mã")
        #     else:
        #         if mkc == str(data1.at[0, "Mật khẩu"]):
        #             row = int(data.index[data["Mã nhân viên"]==mnv])
        #             doi_mat_khau(row,mkm1)
        #         else:
        #             st.warning("Mật khẩu cũ không chính xác")