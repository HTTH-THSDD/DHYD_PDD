import streamlit as st
import pandas as pd
import gspread
from datetime import datetime
from zoneinfo import ZoneInfo
import pathlib
import base64
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

def thong_tin_hanh_chinh():
    sheeti1 = st.secrets["sheet_name"]["input_1"]
    data_nv = load_data(sheeti1)
    chon_khoa = st.selectbox("Khoa/Đơn vị ",
                             options=data_nv["Khoa"].unique(),
                             index=None,
                             placeholder=""
                             )
    if chon_khoa:
        st.session_state.khoa_PRIME = chon_khoa
        data_nv1=data_nv.loc[data_nv["Khoa"]==f"{chon_khoa}"]
        chon_nhanvien = st.selectbox(label="Nhân viên được đánh giá",
                                    options=data_nv1["Nhân viên"],
                                    index=None,
                                    placeholder="")
        
        if chon_nhanvien:
            st.session_state.nv_thuchien_PRIME = chon_nhanvien
        else:
            if "nv_thuchien_PRIME" in st.session_state:
                del st.session_state["nv_thuchien_PRIME"]
    else:
        if "khoa_PRIME" in st.session_state:
            del st.session_state["khoa_PRIME"]

def vitrigs():
    vitri_gsv=["Điều dưỡng trưởng tại khoa lâm sàng", "Điều dưỡng trưởng phiên là Champion", "Điều dưỡng viên là Champion", "Nhân viên Phòng Điều dưỡng"]
    vitri = st.radio(label="Vị trí nhân viên đánh giá",
                 options=vitri_gsv,
                 index=None)
    if vitri:
        st.session_state.vtgs_PRIME = vitri
    else:
        if "vtgs_PRIME" in st.session_state:
            del st.session_state["vtgs_PRIME"]

def bang_kiem_quy_trinh():
    sheeti6 = st.secrets["sheet_name"]["input_6"]
    data_qt6 = load_data(sheeti6)
    st.session_state.quy_trinh = data_qt6

def precheck_table():
    tieu_chi = []
    nd = []
    ketqua = []
    tondong = []
    for i in range(0, len(st.session_state.quy_trinh)):
        tieu_chi.append(st.session_state.quy_trinh.iloc[i, 3])
        nd.append(st.session_state.quy_trinh.iloc[i, 4])
        ketqua.append(st.session_state[f"radio_{i}"])
        if f"text_{i}" in st.session_state:
            tondong.append(st.session_state[f"text_{i}"])
        else:
            tondong.append("")
    k = {"Tiêu chí": pd.Series(tieu_chi),
                "Nội dung": pd.Series(nd),
                "Kết quả": pd.Series(ketqua),
                "Tồn đọng": pd.Series(tondong),
                }
    precheck_table = pd.DataFrame(k)
    return precheck_table

def upload_data_GS(data):
    credentials = load_credentials()
    gc = gspread.authorize(credentials)
    sheeto1 = st.secrets["sheet_name"]["output_6"]
    sheet = gc.open(sheeto1).sheet1
    sheet = gc.open("Output-st-PRIME").sheet1
    now_vn = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")) 
    column_index = len(sheet.get_all_values())   
    column_timestamp = now_vn.strftime('%Y-%m-%d %H:%M:%S')
    column_khoa = str(st.session_state.khoa_PRIME)
    column_nvgs = str(st.session_state.username)
    column_nvth = str(st.session_state.nv_thuchien_PRIME)
    column_vtndg = str(st.session_state.vtgs_PRIME)
    column_qt = "PRIME duy trì"
    column_data=""
    so_buoc_dat = 0
    tong_so_buoc = len(data)
  
    for i in range (0, len(data)):
        tieu_chi = str(data.iloc[i]["Tiêu chí"])  
        ketqua = str(data.iloc[i]["Kết quả"])  
        tondong = str(data.iloc[i]["Tồn đọng"])
        if ketqua == "Đạt":
            so_buoc_dat +=1
        if tondong in ["Chưa điền",""]:
            column_data += tieu_chi + "|" + ketqua + "|#"
        else:
            column_data += tieu_chi + "|" + ketqua + "|" + tondong + "#"
    tltt = round(so_buoc_dat/tong_so_buoc,4)

    sheet.append_row([column_index,column_timestamp,column_khoa,column_nvth,column_nvgs,column_vtndg,column_qt,column_data,tltt])
    warning(3,3)

@st.dialog("Thông báo")
def warning(x,y):
    if x == 1:
        st.warning("Các tiêu chí chưa đánh giá: " + str(y))
    if x == 3:
        st.success("Gửi thành công")
# Main Section ####################################################################################
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
        <p>NHẬP KẾT QUẢ PRIME</p>
        </div>
    </div>
    <div class="header-underline"></div>

 """, unsafe_allow_html=True)
html_code = f'<p class="demuc"><i>Nhân viên đang đánh giá: {st.session_state.username}</i></p>'
st.html(html_code)
vitrigs()
thong_tin_hanh_chinh()
st.divider()
st.markdown("<h4 style='text-align: center;'>Bảng kiểm PRIME</h4>", unsafe_allow_html=True)
file_id = "1HdoVbeB8LkOD_PGZrGNmAF9j6YjUNa9M"
download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
st.markdown(
    f"""
    <div style="text-align: center;">
        <a href="{download_url}" download target="_blank">
            <button style="padding:5px 5px; font-size:13px; color:#03069c; background-color:#cdf8fa; border: none;">Tải biểu mẫu PDF</button>
        </a>
    </div>
    """,
    unsafe_allow_html=True
)
bang_kiem_quy_trinh()
luachon = ["Đạt", "Không đạt"]
if (
    "khoa_PRIME" in st.session_state and st.session_state["khoa_PRIME"] 
    and "nv_thuchien_PRIME" in st.session_state and st.session_state["nv_thuchien_PRIME"] 
    and "vtgs_PRIME" in st.session_state and st.session_state["vtgs_PRIME"] is not None
):
    st.divider()
    data_qt6 = st.session_state.quy_trinh
    quy_trinh = st.session_state.quy_trinh
    for i in range (0,len(quy_trinh)):   
        st.radio(
        label=f"Tiêu chí {quy_trinh.iloc[i, 3]}: {quy_trinh.iloc[i, 4]}",
        options=luachon,
        key=f"radio_{i}",
        index=None,
        )
        if st.session_state.get(f"radio_{i}") != "Đạt" and st.session_state.get(f"radio_{i}") != None:
            st.text_input(
                label="Tồn đọng",
                placeholder="Ghi rõ tồn đọng",
                key=f"text_{i}",
            )                        
    precheck = st.checkbox(label="Xem trước")
    if precheck:
        buoc_chua_dien = []
        for j in range (0,len(quy_trinh)):
            if f"radio_{j}" not in st.session_state or not st.session_state[f"radio_{j}"]:
                buoc_chua_dien.append(f"{quy_trinh.iloc[j,3]}")
        buoc_chua_dien_str = ", ".join(buoc_chua_dien)
        if buoc_chua_dien_str == "":
            prechecktable = precheck_table()         
            st.dataframe(prechecktable, hide_index=True)
            if st.button("Gửi"):
                upload_data_GS(prechecktable)
        else:
            warning(1,buoc_chua_dien_str)
else:
    st.warning("Vui lòng chọn đầy đủ các mục")




