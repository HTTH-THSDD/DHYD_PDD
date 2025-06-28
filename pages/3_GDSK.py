import streamlit as st
import pandas as pd
import gspread
from datetime import datetime
from zoneinfo import ZoneInfo
import pathlib
import base64
from google.oauth2.service_account import Credentials
import re
# Functional section

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

def load_css(file_path):
    with open(file_path) as f:
        st.html(f"<style>{f.read()}</style>")

@st.cache_data(ttl=3600)
def get_img_as_base64(file):
    with open(file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

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
        st.session_state.khoa_GDSK = chon_khoa
    else:
        if "khoa_GDSK" in st.session_state:
            del st.session_state["khoa_GDSK"]

def vitri_gdsk():
    vitri_gsv=["Điều dưỡng trưởng tại khoa lâm sàng", "Điều dưỡng trưởng đánh giá chéo", "Điều dưỡng trưởng phiên","Điều dưỡng viên đánh giá chéo", "Nhân viên Phòng Điều dưỡng"]
    vitri = st.radio(label="Vị trí nhân viên đánh giá",
                 options=vitri_gsv,
                 index=None,
                 )
    if vitri:
        st.session_state.vtgs_GDSK = vitri
    else:
        if "vtgs_GDSK" in st.session_state:
            del st.session_state["vtgs_GDSK"]

# def precheck_table_gdsk(data):
#     buoc = []
#     nd = []
#     ketqua = []
#     tondong = []
#     taophieu = []
#     for i in range(0, 11):
#         buoc.append(data.iloc[i,0])
#         nd.append(data.iloc[i,1])
#         ketqua.append(st.session_state[f"gdskradio_{i}"])
#         taophieu.append(st.session_state[f"gdskdateinput_{i}"].strftime("%d-%m-%y"))
#         if f"gdsktext_{i}" in st.session_state and st.session_state[f"gdsktext_{i}"] is not None:
#             tondong.append(st.session_state[f"gdsktext_{i}"])
#         else:
#             tondong.append("")
#     k = {"Bước": pd.Series(buoc),
#                 "Nội dung": pd.Series(nd),
#                 "Kết quả": pd.Series(ketqua),
#                 "Tồn đọng": pd.Series(tondong),
#                 "Ngày tạo phiếu": pd.Series(taophieu),
#                 }
#     precheck_table = pd.DataFrame(k)
#     return precheck_table

def upload_data_GDSK(len_data):
    credentials = load_credentials()
    gc = gspread.authorize(credentials)
    sheeto3 = st.secrets["sheet_name"]["output_3"]
    sheet = gc.open(sheeto3).sheet1
    column_index = len(sheet.get_all_values())
    now_vn = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))    
    column_timestamp = now_vn.strftime('%Y-%m-%d %H:%M:%S')
    column_khoa = str(st.session_state.khoa_GDSK)
    column_svv = str(st.session_state.svv_GDSK)
    column_yob_nb = str(st.session_state.yob_GDSK)
    column_vtndg = str(st.session_state.vtgs_GDSK)
    column_nv_gs = str(st.session_state.username)
    column_data=""
    so_buoc_hieu = 0
    so_buoc_biet = 0
    so_buoc_khong_biet = 0
    tong_so_buoc_tru_KAD = int(len_data)
    for i in range (0, int(len_data)):
        buoc = f"ND{i+1}" 
        ketqua = str(st.session_state[f"gdskradio_{i}"])  
        tondong = str(st.session_state[f"gdsktext_{i}"]) 
        if tondong =="":
            column_data += buoc + "|" + ketqua + "#"
        else:
            column_data += buoc + "|" + ketqua + "|" + tondong +"#"
        if ketqua == "Hiểu":
            so_buoc_hieu +=1
        elif ketqua == "Biết":
            so_buoc_biet +=1
        elif ketqua == "Không biết":
            so_buoc_khong_biet +=1
        else:
            tong_so_buoc_tru_KAD -=1
        column_tl_hieu = round(so_buoc_hieu/tong_so_buoc_tru_KAD,4)
        column_tl_buoc_biet = round(so_buoc_biet/tong_so_buoc_tru_KAD,4)
        column_tl_khong_biet = round(so_buoc_khong_biet/tong_so_buoc_tru_KAD,4)
    column_data=column_data.rstrip("#")
    sheet.append_row([column_index, column_timestamp, column_khoa, column_svv, column_yob_nb, column_vtndg, column_nv_gs, column_data,column_tl_hieu,column_tl_buoc_biet,column_tl_khong_biet])
    warning(3)

def kiemtra_svv():
    match = re.match(r"^\d{2}-\d{7}$",st.session_state.svv_GDSK)
    if match:
        return True
    else:
        return False


@st.dialog("Thông báo")
def warning(x):
    if x == 1:
        st.warning("Các bước chưa đánh giá được liệt kê bên dưới")
    if x == 2:
        st.warning("Vui lòng điền đầy đủ số vào viện và năm sinh người bệnh")
    if x == 3:
        st.success("Đã lưu thành công")
    if x == 4:
        st.warning("Số vào viện không hợp lệ. Vui lòng nhập lại VD: 25-1234567")


############################ Main section ##################
css_path = pathlib.Path("asset/style.css")
load_css(css_path)
img = get_img_as_base64("pages/img/logo.png")
st.markdown(f"""
    <div class="fixed-header">
        <div class="header-content">
            <img src="data:image/png;base64,{img}" alt="logo">
            <div class="header-text">
                <h1>BỆNH VIỆN ĐẠI HỌC Y DƯỢC THÀNH PHỐ HỒ CHÍ MINH<span style="vertical-align: super; font-size: 0.6em;">&reg;</span><br><span style="color:#c15088">Phòng Điều dưỡng</span></h1>
            </div>
        </div>
        <div class="header-subtext">
        <p>ĐÁNH GIÁ GIÁO DỤC SỨC KHỎE</p>
        </div>
    </div>
    <div class="header-underline"></div>
 """, unsafe_allow_html=True)
html_code = f'<p class="demuc"><i>Nhân viên đánh giá: {st.session_state.username}</i></p>'
st.html(html_code)
vitri_gdsk()
thong_tin_hanh_chinh()
sheeti4 = st.secrets["sheet_name"]["input_4"]
data_gdsk = load_data(sheeti4)
now_vn = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")) 
if "khoa_GDSK" in st.session_state and st.session_state["khoa_GDSK"] and "vtgs_GDSK" in st.session_state and st.session_state["vtgs_GDSK"] is not None:
# if "khoa_GDSK" in st.session_state and "nv_thuchien_GDSK" in st.session_state and "vtgs_GDSK" in st.session_state:
    st.markdown('''
    <h4><span style="color:#003b62">Phần đánh giá giáo dục sức khỏe
                </span></h4>
''',unsafe_allow_html=True)
    luachon = [ "Hiểu", "Biết", "Không biết", "KHÔNG ÁP DỤNG"]
    with st.form(key="gdsk"):
        row1 = st.columns([5,5])
        st.session_state.svv_GDSK = row1[0].text_input("Số vào viện", max_chars=10, placeholder="VD: 25-1234567" )
        st.session_state.yob_GDSK = row1[1].number_input(
            "Năm sinh",
            min_value=1900,
            max_value=now_vn.year,
            value=None,
            step=1,
            placeholder="VD: 1990",
        )
        st.divider()
        for i in range (0,len(data_gdsk)):
            st.radio(
                label=f"Nội dung {data_gdsk['STT'][i]}: {data_gdsk['NỘI DUNG'][i]}",
                options=luachon,
                key=f"gdskradio_{i}",
                index=None,
            )
            st.text_input(
                    label="Tồn đọng",
                    placeholder="Ghi rõ tồn đọng",
                    key=f"gdsktext_{i}",
                )
        submitbutton = st.form_submit_button("Gửi")
    if submitbutton:
        if "svv_GDSK" in st.session_state and st.session_state.svv_GDSK and "yob_GDSK" in st.session_state and st.session_state.yob_GDSK:
            if kiemtra_svv() != True:
                warning(4)
            else:
                buoc_chua_dien = []
                for j in range (0,len(data_gdsk)):
                    if f"gdskradio_{j}" not in st.session_state or not st.session_state[f"gdskradio_{j}"]:
                        buoc_chua_dien.append(f"Nội dung {data_gdsk.iloc[j,0]}")
                buoc_chua_dien_str = ", ".join(buoc_chua_dien)
                if buoc_chua_dien_str == "":
                    upload_data_GDSK(len(data_gdsk))
                else:
                    warning(4)
                    st.info(f"Các bước chưa chọn kết quả: {buoc_chua_dien_str}", icon="ℹ️")
        else:
            warning(2)
else:
    st.warning("Vui lòng chọn đầy đủ các mục")