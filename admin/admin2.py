import streamlit as st
import pandas as pd
import gspread
import pathlib
import base64
from google.oauth2.service_account import Credentials

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

@st.cache_data(ttl=10)
def load_data(x):
    credentials = load_credentials()
    gc = gspread.authorize(credentials)
    sheet = gc.open(x).sheet1
    data = sheet.get_all_values()
    header = data[0]
    values = data[1:]
    data_final = pd.DataFrame(values, columns=header)
    return data_final

def phan_quyen(row,quyen):
    credentials = load_credentials()
    gc = gspread.authorize(credentials)
    sheeti1 =  st.secrets["sheet_name"]["input_1"]
    sheet = gc.open(sheeti1).sheet1
    if quyen in [""," "]:
         sheet.update_cell(row+2, 21, "")
    else:
        sheet.update_cell(row+2, 21, quyen)
    st.toast("Phân quyền thành công")

def doi_mat_khau(row, mkm1):
    credentials = load_credentials()
    gc = gspread.authorize(credentials)
    sheeti1 =  st.secrets["sheet_name"]["input_1"]
    sheet = gc.open(sheeti1).sheet1
    mk= mkm1.upper()
    sheet.update_cell(row+2,22,mk)
    st.toast("Đổi mật khẩu thành công")
#########################################################################################################
css_path = pathlib.Path("asset/style.css")
load_css(css_path)
img = get_img_as_base64("pages/img/logo.png")
st.markdown(f"""
    <div class="fixed-header">
        <div class="header-content">
            <img src="data:image/png;base64,{img}" alt="logo">
            <div class="header-text">
                <h1>BỆNH VIỆN ĐẠI HỌC Y DƯỢC THÀNH PHỐ HỒ CHÍ MINH®<br><span style="color:#c15088">Phòng Điều dưỡng</span></h1>
            </div>
        </div>
        <div class="header-subtext">
        <p style="color:#b36002; padding-left:25px">TRANG QUẢN LÝ MẬT KHẨU & PHÂN QUYỀN</p>
        </div>
    </div>
    <div class="header-underline"></div>

 """, unsafe_allow_html=True)
html_code = f'<p class="admin_1"><i>Xin chào admin:{st.session_state.username}</i></p>'
st.html(html_code)
sheeti1 =  st.secrets["sheet_name"]["input_1"]
data_in = load_data(sheeti1)
data_in1 = data_in[["Nhân viên","Phân quyền","Mật khẩu"]]

data_in2 = data_in[["Nhân viên","Phân quyền","Mật khẩu", "Mã số"]]
tim_nv = st.selectbox(label="Tên hoặc mã nhân viên",
                      options=["Tất cả nhân viên"] + list(data_in["Nhân viên"]),
                      key="sl")
data_sl=data_in1.loc[data_in1["Nhân viên"]==tim_nv]
if tim_nv == "Tất cả nhân viên": 
    st.dataframe(data_in1, hide_index=True, height=225)
else:
    data_sl = data_in1.loc[data_in1["Nhân viên"] == tim_nv]
    if data_sl.empty:
        st.warning("Không tìm thấy nhân viên theo yêu cầu")
    else:
        st.dataframe(data_sl, hide_index=True)

if st.button("Tải lại"):
    st.rerun()
col = st.columns([5,5])
with col[0]:
    with st.form("Đổi mật khẩu"):
        st.write("Đổi mật khẩu")
        manv = st.text_input("Mã nhân viên")
        mk = st.text_input("Mật khẩu mới:")
        manv = manv.upper()
        submit1 = st.form_submit_button("Đổi mật khẩu")
    if submit1:
        if manv in data_in2["Mã số"].values:
            row1 = data_in2.index[data_in2["Mã số"] == manv].tolist()[0]
            doi_mat_khau(row1, mk)
        else:
            st.warning("Không tìm thấy mã nhân viên.")
with col[1]:
    with st.form("Phân quyền"):
        st.write("Phân quyền")
        mnv = st.text_input("Mã nhân viên")
        quyen = st.text_input("Phân quyền cấp:",max_chars=1)
        mnv = mnv.upper()
        submit = st.form_submit_button("Phân quyền")
    if submit:
        if mnv in data_in2["Mã số"].values:
            row = data_in2.index[data_in2["Mã số"]==mnv].tolist()[0]
            phan_quyen(row,quyen)
        else:
            st.warning("Không tìm thấy mã nhân viên.")