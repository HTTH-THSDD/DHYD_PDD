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
        st.session_state.khoa_GSQT = chon_khoa
        data_nv1=data_nv.loc[data_nv["Khoa"]==f"{chon_khoa}"]
        chon_nhanvien = st.selectbox(label="Nhân viên thực hiện quy trình",
                                    options=data_nv1["Nhân viên"],
                                    index=None,
                                    placeholder="")
        
        if chon_nhanvien:
            st.session_state.nv_thuchien_GSQT = chon_nhanvien
        else:
            if "nv_thuchien_GSQT" in st.session_state:
                del st.session_state["nv_thuchien_GSQT"]
    else:
        if "khoa_GSQT" in st.session_state:
            del st.session_state["khoa_GSQT"]

def vitrigs():
    vitri_gsv=["Điều dưỡng trưởng tại khoa lâm sàng", "Điều dưỡng trưởng giám sát chéo", "Điều dưỡng trưởng phiên", "Điều dưỡng phụ trách quy trình","Điều dưỡng viên giám sát chéo", "Nhân viên Phòng Điều dưỡng"]
    vitri = st.radio(label="Vị trí nhân viên giám sát",
                 options=vitri_gsv,
                 index=None)
    if vitri:
        st.session_state.vtgs_GSQT = vitri
    else:
        if "vtgs_GSQT" in st.session_state:
            del st.session_state["vtgs_GSQT"]

def bang_kiem_quy_trinh():
    sheeti2 = st.secrets["sheet_name"]["input_2"]
    data_qt2 = load_data(sheeti2)
    chon_qt = st.selectbox("Tên quy trình",
                             options=data_qt2["Tên quy trình"].unique(),
                             index=None,
                             key="qt",
                             placeholder="",
                             )
    if chon_qt:
        qtx = data_qt2.loc[data_qt2["Tên quy trình"]==chon_qt]
        st.session_state.quy_trinh = qtx
        st.session_state.ten_quy_trinh =  qtx["Tên quy trình"].iloc[0]
        ma_quy_trinh = qtx["Mã bước QT"].iloc[0]
        danh_sach_buoc_an_toan = []
        for i in range(0,len(qtx)):
            if qtx["Chỉ số an toàn"].iloc[i] == "x":
                danh_sach_buoc_an_toan.append(int(qtx["Bước"].iloc[i]))
        st.session_state.ds_buocantoan = danh_sach_buoc_an_toan
        st.session_state.ma_quy_trinh = ma_quy_trinh[:4]
    else:
        if "quy_trinh" in st.session_state:
            del st.session_state["quy_trinh"]

def precheck_table():
    buoc = []
    nd = []
    ketqua = []
    tondong = []
    for i in range(0, len(st.session_state.quy_trinh)):
        buoc.append(st.session_state.quy_trinh.iloc[i, 6])
        nd.append(st.session_state.quy_trinh.iloc[i, 7])
        ketqua.append(st.session_state[f"radio_{i}"])
        if f"text_{i}" in st.session_state:
            tondong.append(st.session_state[f"text_{i}"])
        else:
            tondong.append("")
    k = {"Bước": pd.Series(buoc),
                "Nội dung": pd.Series(nd),
                "Kết quả": pd.Series(ketqua),
                "Tồn đọng": pd.Series(tondong),
                }
    precheck_table = pd.DataFrame(k)
    return precheck_table

def upload_data_GS(data):
    credentials = load_credentials()
    gc = gspread.authorize(credentials)
    sheeto1 = st.secrets["sheet_name"]["output_1"]
    sheet = gc.open(sheeto1).sheet1
    sheet = gc.open("Output-st-GSQT").sheet1
    column_index = len(sheet.get_all_values())
    now_vn = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))    
    column_timestamp = now_vn.strftime('%Y-%m-%d %H:%M:%S')
    column_khoa = str(st.session_state.khoa_GSQT)
    column_nvgs = str(st.session_state.username)
    column_nvth = str(st.session_state.nv_thuchien_GSQT)
    column_vtndg = str(st.session_state.vtgs_GSQT)
    column_qt = str(st.session_state.ten_quy_trinh)
    column_data=""
    so_buoc_dung_du = 0
    tong_so_buoc_tru_KAD = len(data)
    buoc_an_toan_dung_du = 0
    tong_an_toan_tru_an_toan_va_KAD = len(st.session_state.ds_buocantoan)
    for i in range (0, len(data)):
        buoc = str(data.iloc[i]["Bước"])  
        ketqua = str(data.iloc[i]["Kết quả"])  
        tondong = str(data.iloc[i]["Tồn đọng"])
        if ketqua == "Thực hiện đúng, đủ":
            so_buoc_dung_du +=1
            if i+1 in st.session_state.ds_buocantoan:
               buoc_an_toan_dung_du +=1 
        if ketqua == "KHÔNG ÁP DỤNG":
            tong_so_buoc_tru_KAD -=1
            if i+1 in st.session_state.ds_buocantoan:
                tong_an_toan_tru_an_toan_va_KAD -=1   
        if tondong in ["Chưa điền",""]:
            column_data += buoc + "|" + ketqua + "|#"
        else:
            column_data += buoc + "|" + ketqua + "|" + tondong + "#"
    tltt = round(so_buoc_dung_du/tong_so_buoc_tru_KAD,4)
    if tong_an_toan_tru_an_toan_va_KAD == 0:
        tlan = ""
    else:
        tlan = round(buoc_an_toan_dung_du/tong_an_toan_tru_an_toan_va_KAD,4)
    column_data=column_data.rstrip("#")
    column_mqt = st.session_state.ma_quy_trinh
    sheet.append_row([column_index,column_timestamp,column_khoa,column_nvth,column_nvgs,column_vtndg,column_qt,column_data,column_mqt,tltt,tlan])
    warning(3)

@st.dialog("Thông báo")
def warning(x):
    if x == 1:
        st.warning("Các bước bị thiếu được liệt kê bên dưới")
    if x == 2:
        st.warning("Vui lòng điền đầy đủ số vào viện và năm sinh người bệnh")
    if x == 3:
        st.success("Đã lưu thành công")
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
        <p>GIÁM SÁT QUY TRÌNH KỸ THUẬT</p>
        </div>
    </div>
    <div class="header-underline"></div>

 """, unsafe_allow_html=True)
html_code = f'<p class="demuc"><i>Nhân viên giám sát: {st.session_state.username}</i></p>'
st.html(html_code)
vitrigs()
#st.html(f'<p class="demuc"><i>Nhân viên thực hiện quy trình</i></p>')
thong_tin_hanh_chinh()
st.divider()
bang_kiem_quy_trinh()
luachon = ["Thực hiện chưa đúng, KHÔNG thực hiện", "Thực hiện đúng nhưng chưa đủ", "Thực hiện đúng, đủ", "KHÔNG ÁP DỤNG"]
if (
    "khoa_GSQT" in st.session_state and st.session_state["khoa_GSQT"] 
    and "nv_thuchien_GSQT" in st.session_state and st.session_state["nv_thuchien_GSQT"] 
    and "vtgs_GSQT" in st.session_state and st.session_state["vtgs_GSQT"] is not None
    and "quy_trinh" in st.session_state and st.session_state["quy_trinh"] is not None
):
    st.divider()
    quy_trinh = st.session_state.quy_trinh
    quy_trinh["Nội dung"] = quy_trinh["Nội dung"].str.replace(" + ", "<br>• ", regex=False)
    for i in range (0,len(quy_trinh)):
        st.markdown(f"Bước {quy_trinh.iloc[i, 5]}: {quy_trinh.iloc[i, 7]}", unsafe_allow_html=True)
        st.radio(
        label="Lựa chọn"
        options=luachon,
        key=f"radio_{i}",
        index=None,
        )
        if st.session_state.get(f"radio_{i}") != "Thực hiện đúng, đủ" and st.session_state.get(f"radio_{i}") != None:
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
                buoc_chua_dien.append(f"{quy_trinh.iloc[j,6]}")
        buoc_chua_dien_str = ", ".join(buoc_chua_dien)
        if buoc_chua_dien_str == "":
            prechecktable = precheck_table()
            st.write(f"Nhân viên giám sát: {st.session_state.username}")
            st.write(f"Vị trí nhân viên giám sát: {st.session_state.vtgs_GSQT}")
            st.write(f"Khoa: {st.session_state.khoa_GSQT}")
            st.write(f"Nhân viên thực hiện quy trình: {st.session_state.nv_thuchien_GSQT}")
            st.write(st.session_state.ten_quy_trinh)
            st.dataframe(prechecktable, hide_index=True)
            if st.button("Lưu"):
                upload_data_GS(prechecktable)
        else:
            warning(1)
            st.warning(f"Các bước chưa chọn kết quả: {buoc_chua_dien_str}") 
else:
    st.warning("Vui lòng chọn đầy đủ các mục")