import streamlit as st
import pandas as pd
import numpy as np
import gspread
from datetime import datetime
from zoneinfo import ZoneInfo
import pathlib
import base64
from google.oauth2.service_account import Credentials
import smtplib
from email.mime.text import MIMEText
import time
from bs4 import BeautifulSoup
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
            st.session_state.email_nvthqt = data_nv1.loc[data_nv1["Nhân viên"]==chon_nhanvien, "Email"].values[0]
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
    loaiquytrinh = st.radio(label="Loại quy trình kỹ thuật",
             options=["Quy trình kỹ thuật cơ bản","Quy trình kỹ thuật chuyên khoa"],
             index=None,
             key="loai_quy_trinh",
             horizontal=True,
             )
    sheeti2 = st.secrets["sheet_name"]["input_2"]
    data_qt2 = load_data(sheeti2)
    if loaiquytrinh == "Quy trình kỹ thuật cơ bản":
        chon_qt = st.selectbox("Tên quy trình kỹ thuật",
                                options=data_qt2["Tên quy trình"].loc[data_qt2["Mã bước QT"].str[:4] == "QTCB"].unique(),
                                index=None,
                                placeholder="",
                                )
    else:
        chon_qt = st.selectbox("Tên quy trình kỹ thuật",
                                options=data_qt2["Tên quy trình"].loc[data_qt2["Mã bước QT"].str[:4] == "QTCK"].unique(),
                                index=None,
                                placeholder="",
                                )
    if chon_qt:
        st.session_state.loaiqt = chon_qt
        qtx = data_qt2.loc[data_qt2["Tên quy trình"]==chon_qt]
        st.session_state.quy_trinh = qtx
        st.session_state.ten_quy_trinh =  qtx["Tên quy trình"].iloc[0]
        ma_quy_trinh = qtx["Mã bước QT"].iloc[0]
        st.session_state.sttqt = qtx["STT QT"].iloc[0]
        danh_sach_buoc_an_toan = []
        for i in range(0,len(qtx)):
            if qtx["Chỉ số an toàn"].iloc[i] == "x":
                danh_sach_buoc_an_toan.append(int(qtx["Bước"].iloc[i]))
        st.session_state.ds_buocantoan = danh_sach_buoc_an_toan
        st.session_state.ma_quy_trinh = ma_quy_trinh[:4]
    else:
        if "quy_trinh" in st.session_state:
            del st.session_state["quy_trinh"]

    if chon_qt:
        qtx = data_qt2.loc[data_qt2["Tên quy trình"]==chon_qt]
        st.session_state.quy_trinh = qtx
        st.session_state.ten_quy_trinh =  qtx["Tên quy trình"].iloc[0]
        ma_quy_trinh = qtx["Mã bước QT"].iloc[0]    
        danh_sach_buoc_nhan_dang = []
        for i in range(0,len(qtx)):
            if qtx["Nhận dạng"].iloc[i] == "x":
                danh_sach_buoc_nhan_dang.append(int(qtx["Bước"].iloc[i]))
        st.session_state.ds_buocNDNB = danh_sach_buoc_nhan_dang
        st.session_state.ma_quy_trinh = ma_quy_trinh[:4]
    else:
        if "quy_trinh" in st.session_state:
            del st.session_state["quy_trinh"]

def gui_email_qtkt(receiver_email,data):
    now_vn = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
    timestamp = now_vn.strftime('%H:%M %d-%m-%Y')
    subject = f"KẾT QUẢ GIÁM SÁT QUY TRÌNH KỸ THUẬT - {timestamp}"

    html_table = data.to_html(index=False, border=1, justify='left')
    soup = BeautifulSoup(html_table, "html.parser")

    # Tỉ lệ cột: 1:5:3:3 (tổng 12 phần => 8.33%, 41.67%, 25%, 25%)
    widths = ["8.33%", "41.67%", "25%", "25%"]

    # Tô màu dòng tiêu đề
    for i, th in enumerate(soup.find_all("th")):
        th["style"] = (
            f"padding:8px 12px;"
            f"border:1px solid #cfcfcf;"
            f"text-align:left;"
            f"font-family:Arial,sans-serif;"
            f"font-size:14px;"
            f"width:{widths[i]};"
            f"background-color:#2c25b3;"
            f"color:#fff;"
        )

    # Style cho từng ô dữ liệu
    for row in soup.find_all("tr"):
        for i, td in enumerate(row.find_all("td")):
            td["style"] = (
                f"padding:8px 12px;"
                f"border:1px solid #cfcfcf;"
                f"text-align:left;"
                f"font-family:Arial,sans-serif;"
                f"font-size:14px;"
                f"width:{widths[i]};"
            )

    html_table = str(soup)
    # Khi gửi email hoặc hiển thị trên Streamlit:
    st.markdown(html_table, unsafe_allow_html=True)
    
    tltt = float(st.session_state.tltt)*100
    # Tạo nội dung email dạng HTML, bạn có thể tùy chỉnh style thêm nếu muốn
    body = f"""
    <html>
        <body>
            <h4 style="color:DodgerBlue;">Kính gửi Điều dưỡng: {st.session_state.nv_thuchien_GSQT} - {st.session_state.khoa_GSQT}</h4>
            <p>
              Căn cứ theo kế hoạch giám sát thường quy/ đột xuất của Phòng Điều dưỡng và các Khoa/Đơn vị lâm sàng,
            Phòng Điều dưỡng xin gửi kết quả giám sát quy trình kỹ thuật vừa thực hiện của Quý Anh/Chị như sau:
            </p>

            <div class="highlight">
            <p><strong>Tên quy trình kỹ thuật:</strong> {st.session_state.ten_quy_trinh}</p>       
            <p><strong>Nhân viên giám sát:</strong> {st.session_state.username}</p>
            <p><strong>Thời gian giám sát:</strong> {timestamp}</p>
            <p><strong>Tỉ lệ tuân thủ:</strong> {tltt}%</p>
            </div>

            <p><strong>Bảng chi tiết kết quả giám sát:</strong></p>
            {html_table}
            <br><br><br><br><br>
            <p class="footer">
            Trân trọng./.<br />
            
            <h5 style="color:DodgerBlue;">Phòng Điều dưỡng
            <br>BỆNH VIỆN ĐẠI HỌC Y DƯỢC THÀNH PHỐ HỒ CHÍ MINH</h5>
            </p>
        </body>
    </html>
    """


    # Thiết lập thông tin email
    sender_email = st.secrets["email_info"]["sender_email"]
    sender_password = st.secrets["email_info"]["sender_password"]

    msg = MIMEText(body, "html", "utf-8")
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = receiver_email

    # Gửi email
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
    if "email2" in st.session_state and st.session_state.email2:
        msg["To"] = st.session_state.email2
        server.sendmail(sender_email, st.session_state.email2, msg.as_string())
    if "email3" in st.session_state and st.session_state.email3:
        msg["To"] = st.session_state.email3
        server.sendmail(sender_email, st.session_state.email3, msg.as_string())

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

def clear_session_state():
    keys_to_clear = [
        "khoa_GSQT", "nv_thuchien_GSQT", "vtgs_GSQT", "quy_trinh"
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

def upload_data_GS(data):
    credentials = load_credentials()
    gc = gspread.authorize(credentials)
    sheeto1 = st.secrets["sheet_name"]["output_1"]
    sheet = gc.open(sheeto1).sheet1
    now_vn = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
    column_index = len(sheet.get_all_values())    
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
    buoc_nhan_dang_dung_du = 0
    tong_nhan_dang_tru_nhan_dang_va_KAD = len(st.session_state.ds_buocNDNB)
    for i in range (0, len(data)):
        buoc = str(data.iloc[i]["Bước"])  
        ketqua = str(data.iloc[i]["Kết quả"])  
        tondong = str(data.iloc[i]["Tồn đọng"])
        if ketqua == "Thực hiện đúng, đủ":
            so_buoc_dung_du +=1
            if i+1 in st.session_state.ds_buocantoan:
               buoc_an_toan_dung_du +=1
            if i+1 in st.session_state.ds_buocNDNB:
               buoc_nhan_dang_dung_du +=1  
        if ketqua == "KHÔNG ÁP DỤNG":
            tong_so_buoc_tru_KAD -=1
            if i+1 in st.session_state.ds_buocantoan:
                tong_an_toan_tru_an_toan_va_KAD -=1 
            if i+1 in st.session_state.ds_buocNDNB:
                tong_nhan_dang_tru_nhan_dang_va_KAD -=1
            if tong_so_buoc_tru_KAD == 0:
                st.session_state.loi_KAD = True
                st.session_state.loi_KADtime = time.time()
                st.rerun()
        if tondong in ["Chưa điền",""]:
            column_data += buoc + "|" + ketqua + "|#"
        else:
            column_data += buoc + "|" + ketqua + "|" + tondong + "#"
    tltt = round(so_buoc_dung_du/tong_so_buoc_tru_KAD,4)
    st.session_state.tltt = tltt
    tlan = ""
    tlnd = ""
    if tong_an_toan_tru_an_toan_va_KAD != 0:
        tlan = round(buoc_an_toan_dung_du/tong_an_toan_tru_an_toan_va_KAD,4)
    if tong_nhan_dang_tru_nhan_dang_va_KAD != 0:
        tlnd = round(buoc_nhan_dang_dung_du/tong_nhan_dang_tru_nhan_dang_va_KAD,4)
    column_data=column_data.rstrip("#")
    column_mqt = st.session_state.ma_quy_trinh
    column_ghichu1 = ""
    if "nv2" in st.session_state and st.session_state.nv2:
        column_ghichu1 = str(st.session_state.nv2)
    if "nv3" in st.session_state and st.session_state.nv3:
        column_ghichu2 = str(st.session_state.nv3)
    sheet.append_row([column_index,column_timestamp,column_khoa,column_nvth,column_nvgs,column_vtndg,column_qt,column_data,column_mqt,tltt,tlan,tlnd,column_ghichu1,column_ghichu2,])
    warning(4,2)
    
@st.dialog("Thông báo")
def warning(x,y):
    if x == 1:
        st.warning(f"Các bước chưa đánh giá: {y}")
    if x == 2:
        st.warning("Vui lòng điền đầy đủ số vào viện và năm sinh người bệnh")
    if x == 3:
        st.warning("Lỗi nhập kết quả không hợp lí: tất cả các bước KHÔNG ÁP DỤNG") 
    if x == 4:
        st.success("Đã lưu thành công")

# Main Section ####################################################################################
if st.session_state.get("loi_KAD", False):
        if time.time() - st.session_state.get("loi_KADtime", 0) < 2:
            warning(3,2)
        else:
            del st.session_state["loi_KAD"]
            del st.session_state["loi_KADtime"]
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
        <p>GIÁM SÁT QUY TRÌNH KỸ THUẬT</p>
        </div>
    </div>
    <div class="header-underline"></div>

 """, unsafe_allow_html=True)
html_code = f'<p class="demuc"><i>Nhân viên đang giám sát: {st.session_state.username}</i></p>'
st.html(html_code)
vitrigs()
#st.html(f'<p class="demuc"><i>Nhân viên thực hiện quy trình</i></p>')
thong_tin_hanh_chinh()
st.divider()
bang_kiem_quy_trinh()
luachon = ["Thực hiện đúng, đủ","Thực hiện đúng nhưng chưa đủ","Thực hiện chưa đúng, KHÔNG thực hiện","KHÔNG ÁP DỤNG"]
if (
    "khoa_GSQT" in st.session_state and st.session_state["khoa_GSQT"] 
    and "nv_thuchien_GSQT" in st.session_state and st.session_state["nv_thuchien_GSQT"] 
    and "vtgs_GSQT" in st.session_state and st.session_state["vtgs_GSQT"] is not None
    and "quy_trinh" in st.session_state and st.session_state["quy_trinh"] is not None
):
    quy_trinh = st.session_state.quy_trinh
    if st.session_state.sttqt == "215" or st.session_state.sttqt == "216":
        sheeti1 = st.secrets["sheet_name"]["input_1"]
        data_nv = load_data(sheeti1)
        data_nv1 = data_nv.loc[data_nv["Khoa"].str.contains("Khoa Gây mê hồi sức", case=False)]
        chon_nv2 = st.selectbox(label="Nhân viên thực hiện quy trình 2",
                                    options=data_nv1["Nhân viên"],
                                    index=None,
                                    placeholder="",
                                    key="nv2")
        if chon_nv2 is not None:
            email_matches = data_nv1.loc[data_nv1["Nhân viên"]==chon_nv2, "Email"]
            if not email_matches.empty:
                st.session_state.email2 = email_matches.values[0]
            else:
                st.warning("Không tìm thấy email của nhân viên này")
    if st.session_state.sttqt == "216":
        sheeti1 = st.secrets["sheet_name"]["input_1"]
        data_nv = load_data(sheeti1)
        data_nv1 = data_nv.loc[data_nv["Khoa"].str.contains("Khoa Gây mê hồi sức", case=False)]
        chon_nv3 = st.selectbox(label="Nhân viên thực hiện quy trình 3",
                                    options=data_nv1["Nhân viên"],
                                    index=None,
                                    placeholder="",
                                    key="nv3")
        if chon_nv3 is not None:
            email_matches = data_nv1.loc[data_nv1["Nhân viên"]==chon_nv3, "Email"]
            if not email_matches.empty:
                st.session_state.email3 = email_matches.values[0]
            else:
                st.warning("Không tìm thấy email của nhân viên này")

    st.divider()
    for i in range (0,len(quy_trinh)):   
        st.radio(
        label=f"Bước {quy_trinh.iloc[i, 5]}: {quy_trinh.iloc[i, 7]}",
        options=luachon,
        key=f"radio_{i}",
        index=None,
        )
        if st.session_state.get(f"radio_{i}") != "Thực hiện đúng, đủ" and \
            st.session_state.get(f"radio_{i}") != "KHÔNG ÁP DỤNG" and \
            st.session_state.get(f"radio_{i}") != None:
            
            st.text_input(
                label="Tồn đọng",
                placeholder="Ghi rõ tồn đọng",
                key=f"text_{i}",
            )                        
    precheck = st.checkbox(label="Xem lại kết quả vừa nhập")
    if precheck:
        buoc_chua_dien = []
        for j in range (0,len(quy_trinh)):
            if f"radio_{j}" not in st.session_state or not st.session_state[f"radio_{j}"]:
                buoc_chua_dien.append(f"{quy_trinh.iloc[j,6]}")
        buoc_chua_dien_str = ", ".join(buoc_chua_dien)
        if buoc_chua_dien_str == "":
            prechecktable = precheck_table()         
            st.dataframe(prechecktable, hide_index=True)
        else:
            warning(1,buoc_chua_dien_str)
    if st.button("Lưu"):
        buoc_chua_dien = []
        for j in range (0,len(quy_trinh)):
            if f"radio_{j}" not in st.session_state or not st.session_state[f"radio_{j}"]:
                buoc_chua_dien.append(f"{quy_trinh.iloc[j,6]}")
        buoc_chua_dien_str = ", ".join(buoc_chua_dien)
        if buoc_chua_dien_str == "":
                prechecktable = precheck_table()         
                upload_data_GS(prechecktable)
                gui_email_qtkt(st.session_state.email_nvthqt, prechecktable)
                clear_session_state()
        else:
            warning(1,buoc_chua_dien_str)
  
        
else:
    st.warning("Vui lòng chọn đầy đủ các mục")

