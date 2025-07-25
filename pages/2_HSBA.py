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
    with open(file_path) as f:
        st.html(f"<style>{f.read()}</style>")

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

def thong_tin_hanh_chinh():
    sheeti1 = st.secrets["sheet_name"]["input_1"]
    data_nv = load_data(sheeti1)
    chon_khoa = st.selectbox("Khoa/Đơn vị ",
                             options=data_nv["Khoa"].unique(),
                             index=None,
                             placeholder="",
                             )
    if chon_khoa:
        st.session_state.khoa_HSBA = chon_khoa
    else:
        if "khoa_HSBA" in st.session_state:
            del st.session_state["khoa_HSBA"]

def vitri_hsba():
    vitri_gsv=["Điều dưỡng trưởng khoa lâm sàng", "Điều dưỡng trưởng phiên", "Điều dưỡng phụ trách ghi chép hồ sơ", "Điều dưỡng viên đánh giá chéo", "Nhân viên Phòng Điều dưỡng"]
    vitri = st.radio(label="Vị trí nhân viên đánh giá",
                 options=vitri_gsv,
                 index=None,
                 )
    if vitri:
        st.session_state.vtgs_HSBA = vitri
    else:
        if "vtgs_HSBA" in st.session_state:
            del st.session_state["vtgs_HSBA"]

def upload_data_HSBA(len_data):
    credentials = load_credentials()
    gc = gspread.authorize(credentials)
    sheeto2 = st.secrets["sheet_name"]["output_2"]
    sheet = gc.open(sheeto2).sheet1
    now_vn = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
    column_index = len(sheet.get_all_values())
    column_timestamp = now_vn.strftime('%Y-%m-%d %H:%M:%S')
    column_khoa = str(st.session_state.khoa_HSBA)
    column_svv = str(st.session_state.svv_HSBA)
    column_yob_nb = str(st.session_state.yob_HSBA)
    column_vtndg = str(st.session_state.vtgs_HSBA)
    column_nv_gs = str(st.session_state.username)
    column_data=""
    so_buoc_dung_du = 0
    so_buoc_dung_nhung_chua_du = 0
    so_buoc_Khong_thuc_hien = 0
    tong_so_buoc_tru_KAD = int(len_data)
    for i in range (0, int(len_data)):
        buoc = f"B{i+1}" 
        ketqua = str(st.session_state[f"hsbaradio_{i}"])  
        tondong = str(st.session_state[f"hsbatext_{i}"]) 
        if tondong == "":
            column_data += buoc + "|" + ketqua + "|#"
        else:
            column_data += buoc + "|" + ketqua + "|" + tondong + "#"
        if ketqua == "Thực hiện đúng, đủ":
            so_buoc_dung_du +=1
        elif ketqua == "Thực hiện đúng nhưng chưa đủ":
            so_buoc_dung_nhung_chua_du +=1
        elif ketqua == "KHÔNG thực hiện, hoặc ghi sai":
            so_buoc_Khong_thuc_hien +=1
        else:
            tong_so_buoc_tru_KAD -=1
        column_tl_dung_du = round(so_buoc_dung_du/tong_so_buoc_tru_KAD,4)
        column_tl_dung_nhung_chua_du = round(so_buoc_dung_nhung_chua_du/tong_so_buoc_tru_KAD,4)
        column_tl_Khong_thuc_hien = round(so_buoc_Khong_thuc_hien/tong_so_buoc_tru_KAD,4)
    column_data=column_data.rstrip("#")
    sheet.append_row([column_index, column_timestamp, column_khoa, column_svv, column_yob_nb, column_vtndg, column_nv_gs, column_data,column_tl_dung_du,column_tl_dung_nhung_chua_du,column_tl_Khong_thuc_hien])
    warning (3,3)

def kiemtra_svv():
    match = re.match(r"^\d{2}-\d{7}$",st.session_state.svv_HSBA)
    if match:
        return True
    else:
        return False

@st.dialog("Thông báo")
def warning(x,y):
    if x == 1:
        st.warning(f"Vui lòng kiểm tra lại các bước sau: {y}")
    if x == 2:
        st.warning("Vui lòng điền đầy đủ số vào viện và năm sinh người bệnh")
    if x == 3:
        st.success("Đã lưu thành công")    
    if x == 4:
        st.warning(f"Số vào viện không hợp lệ. Vui lòng nhập lại VD: 25-1234567")

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
        <p>ĐÁNH GIÁ HỒ SƠ BỆNH ÁN</p>
        </div>
    </div>
    <div class="header-underline"></div>
 """, unsafe_allow_html=True)
html_code = f'<p class="demuc"><i>Nhân viên đánh giá: {st.session_state.username}</i></p>'
st.html(html_code)
vitri_hsba()
thong_tin_hanh_chinh()
sheeti3 = st.secrets["sheet_name"]["input_3"]
data_hsba = load_data(sheeti3)
now_vn = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))  
if "khoa_HSBA" in st.session_state and st.session_state["khoa_HSBA"] and "vtgs_HSBA" in st.session_state and st.session_state["vtgs_HSBA"] is not None:
    st.markdown('''
    <h4><span style="color:#003b62">Phần đánh giá hồ sơ bệnh án
                </span></h4>
''',unsafe_allow_html=True)
    luachon = [ "KHÔNG ÁP DỤNG", "KHÔNG thực hiện, hoặc ghi sai", "Thực hiện đúng nhưng chưa đủ", "Thực hiện đúng, đủ"]
    with st.form(key="hsba"):
        row1 = st.columns([5,5])
        st.session_state.svv_HSBA = row1[0].text_input("Số vào viện", max_chars=10, placeholder="VD: 25-1234567",)
        st.session_state.yob_HSBA = row1[1].number_input(
            "Năm sinh",
            min_value=1900,
            max_value=now_vn.year,
            value=None,
            step=1,
            placeholder="VD: 1990",
            )
        st.divider()
        for i in range (0,len(data_hsba)):
            st.subheader(f"Bước {data_hsba['Mục'][i][1:]}: {data_hsba['Nội dung'][i]}")
            st.radio(
                label=f"{data_hsba['Chi tiết'][i]}",
                options=luachon,
                key=f"hsbaradio_{i}",
                index=None,
            )
            st.text_input(
                    label="Tồn đọng",
                    placeholder="Ghi rõ tồn đọng",
                    key=f"hsbatext_{i}",
                )
        submitbutton = st.form_submit_button("Gửi")
    if submitbutton:
        if "svv_HSBA" in st.session_state and st.session_state.svv_HSBA and "yob_HSBA" in st.session_state and st.session_state.yob_HSBA:
            if kiemtra_svv() != True:
                warning(4,4)
            else:
                buoc_chua_dien = []
                for j in range (0,len(data_hsba)):
                    if f"hsbaradio_{j}" not in st.session_state or not st.session_state[f"hsbaradio_{j}"]:
                        buoc_chua_dien.append(f"Bước {j+1}")
                buoc_chua_dien_str = ", ".join(buoc_chua_dien)
                if buoc_chua_dien_str == "":
                    upload_data_HSBA(len(data_hsba))
                else:
                    warning(1,buoc_chua_dien_str)
        else:
            warning(2,2)
else:
    st.warning("Vui lòng chọn đầy đủ các mục")
        
    
