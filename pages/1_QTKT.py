import streamlit as st
import pandas as pd
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

# ======================== UTILS ========================

@st.cache_data(ttl=3600)
def get_img_as_base64(file):
    with open(file, "rb") as f:
        return base64.b64encode(f.read()).decode()

def load_css(file_path):
    encoding = "utf-8"
    try:
        with open(file_path, "r", encoding=encoding) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except UnicodeDecodeError:
        with open(file_path, "r", encoding="latin-1") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def load_credentials():
    creds_info = {k: st.secrets["google_service_account"][k] for k in [
        "type", "project_id", "private_key_id", "private_key", "client_email",
        "client_id", "auth_uri", "token_uri",
        "auth_provider_x509_cert_url", "client_x509_cert_url", "universe_domain",
    ]}
    return Credentials.from_service_account_info(
        creds_info,
        scopes=["https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"],
    )

@st.cache_data(ttl=3600)
def load_data(x):
    gc = gspread.authorize(load_credentials())
    data = gc.open(x).sheet1.get_all_values()
    return pd.DataFrame(data[1:], columns=data[0])

# ======================== UI COMPONENTS ========================

def thong_tin_hanh_chinh():
    fv = st.session_state.get("form_version", 0)
    data_nv = load_data(st.secrets["sheet_name"]["input_1"])
    chon_khoa = st.selectbox("Khoa/Đơn vị",
                             options=data_nv["Khoa"].unique(),
                             index=None, placeholder="",
                             key=f"khoa_select_{fv}")
    if not chon_khoa:
        st.session_state.pop("khoa_GSQT", None)
        return

    st.session_state.khoa_GSQT = chon_khoa
    data_nv1 = data_nv.loc[data_nv["Khoa"] == chon_khoa]

    if chon_khoa == "Khoa Khám bệnh":
        chon_nhanvien = st.selectbox("Nhân viên thực hiện quy trình",
                                     options=data_nv1["Nhân viên"],
                                     index=None, placeholder="",
                                     key=f"nhanvien_select_{fv}")
        st.radio(label="Đối tượng được giám sát",
                 options=["Nhân viên bàn điều phối", "Nhân viên bàn khám"],
                 index=None, horizontal=True, key=f"doituong_duocgiamsat_{fv}")
        # Đồng bộ sang key cố định để upload_data_GS đọc được
        st.session_state["doituong_duocgiamsat"] = st.session_state.get(f"doituong_duocgiamsat_{fv}")
    else:
        chon_nhanvien = st.selectbox("Nhân viên thực hiện quy trình",
                                     options=data_nv1["Nhân viên"],
                                     index=None, placeholder="",
                                     key=f"nhanvien_select_{fv}")

    if chon_nhanvien:
        st.session_state.nv_thuchien_GSQT = chon_nhanvien
        st.session_state.email_nvthqt = data_nv1.loc[
            data_nv1["Nhân viên"] == chon_nhanvien, "Email"].values[0]
    else:
        st.session_state.pop("nv_thuchien_GSQT", None)

def vitrigs():
    fv = st.session_state.get("form_version", 0)
    vitri_gsv = [
        "Điều dưỡng trưởng tại khoa phụ trách",
        "Điều dưỡng trưởng giám sát chéo",
        "Điều dưỡng trưởng phiên",
        "Điều dưỡng phụ trách quy trình",
        "Điều dưỡng viên giám sát chéo",
        "Nhân viên Phòng Điều dưỡng",
    ]
    vitri = st.radio(label="Vị trí nhân viên giám sát", options=vitri_gsv,
                     index=None, key=f"vitri_radio_{fv}")
    if vitri:
        st.session_state.vtgs_GSQT = vitri
    else:
        st.session_state.pop("vtgs_GSQT", None)

def bang_kiem_quy_trinh():
    fv = st.session_state.get("form_version", 0)
    loaiquytrinh = st.radio(
        label="Loại quy trình kỹ thuật",
        options=["QTKT cơ bản", "QTKT chuyên khoa", "QT hành chính chuyên môn"],
        index=None, key=f"loai_quy_trinh_{fv}", horizontal=True,
    )
    prefix_map = {"QTKT cơ bản": "QTCB", "QTKT chuyên khoa": "QTCK", "QT hành chính chuyên môn": "QTHC"}

    data_qt2 = load_data(st.secrets["sheet_name"]["input_2"])
    if loaiquytrinh is None:
        options = data_qt2["Tên quy trình"].unique()
    else:
        prefix = prefix_map.get(loaiquytrinh)
        options = data_qt2.loc[data_qt2["Mã bước QT"].str[:4] == prefix, "Tên quy trình"].unique()
    chon_qt = st.selectbox("Tên quy trình kỹ thuật", options=options, index=None, placeholder="",
                           key=f"chon_qt_{fv}")

    if not chon_qt:
        st.session_state.pop("quy_trinh", None)
        return

    qtx = data_qt2.loc[data_qt2["Tên quy trình"] == chon_qt]
    st.session_state.quy_trinh = qtx
    st.session_state.ten_quy_trinh = qtx["Tên quy trình"].iloc[0]
    st.session_state.sttqt = qtx["STT QT"].iloc[0]
    st.session_state.ma_quy_trinh = qtx["Mã bước QT"].iloc[0][:4]

    ds_buocantoan, ds_buocNDNB = [], []
    for i, row in qtx.iterrows():
        buoc = int(row["Bước"])
        if row["Chỉ số an toàn"] == "x":
            ds_buocantoan.append(buoc)
        if row["Nhận dạng"] == "x":
            ds_buocNDNB.append(buoc)
    st.session_state.ds_buocantoan = ds_buocantoan
    st.session_state.ds_buocNDNB = ds_buocNDNB

# ======================== DIALOGS ========================

@st.dialog("Thông báo")
def warning(x, y):
    messages = {
        1: lambda: st.warning(f"Các bước chưa đánh giá: {y}"),
        2: lambda: st.warning("Vui lòng điền đầy đủ số vào viện và năm sinh người bệnh"),
        3: lambda: st.warning("Lỗi nhập kết quả không hợp lí: tất cả các bước KHÔNG ÁP DỤNG"),
        4: lambda: st.success("Đã lưu thành công."),
        5: lambda: st.warning("⚠️ Bạn đã gửi kết quả này rồi!"),
    }
    messages.get(x, lambda: None)()

# ======================== EMAIL ========================

def gui_email_qtkt(receiver_email, data):
    now_vn = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
    timestamp = now_vn.strftime("%H:%M %d-%m-%Y")
    subject = f"KẾT QUẢ GIÁM SÁT QUY TRÌNH KỸ THUẬT - {timestamp}"

    html_table = data.to_html(index=False, border=1, justify="left")
    soup = BeautifulSoup(html_table, "html.parser")
    widths = ["8.33%", "41.67%", "25%", "25%"]
    base_td_style = (
        "padding:8px 12px;border:1px solid #cfcfcf;"
        "text-align:left;font-family:Arial,sans-serif;font-size:14px;"
    )
    for i, th in enumerate(soup.find_all("th")):
        th["style"] = base_td_style + f"width:{widths[i]};background-color:#2c25b3;color:#fff;"
    for row in soup.find_all("tr"):
        for i, td in enumerate(row.find_all("td")):
            td["style"] = base_td_style + f"width:{widths[i]};"
    html_table = str(soup)

    st.markdown(html_table, unsafe_allow_html=True)

    tltt_formatted = f"{float(st.session_state.tltt) * 100:.2f}"
    body = f"""
    <html>
      <head><style>
        .hospital-info {{display:flex;gap:30px;align-items:left;}}
        .hospital-info img {{height:30px;width:30px;padding-right:5px;object-fit:contain;}}
        .hospital-text h5 {{margin:0;color:DodgerBlue;font-size:12.5px;line-height:1.25;}}
      </style></head>
      <body>
        <h4 style="color:DodgerBlue;">&nbsp;&nbsp;&nbsp; Kính gửi Điều dưỡng: {st.session_state.nv_thuchien_GSQT} - {st.session_state.khoa_GSQT}</h4>
        <p>&nbsp;&nbsp;&nbsp; Căn cứ theo kế hoạch giám sát thường quy/ đột xuất của Phòng Điều dưỡng và các Khoa/Đơn vị lâm sàng,
        Phòng Điều dưỡng kính gửi kết quả giám sát quy trình kỹ thuật vừa thực hiện của Quý Anh/Chị như sau:</p>
        <div class="highlight">
          <p><strong>Tên quy trình kỹ thuật:</strong> {st.session_state.ten_quy_trinh}</p>
          <p><strong>Nhân viên giám sát:</strong> {st.session_state.username}</p>
          <p><strong>Thời gian giám sát:</strong> {timestamp}</p>
          <p><strong>Tỉ lệ tuân thủ:</strong> {tltt_formatted}%</p>
        </div>
        <p><strong>Bảng chi tiết kết quả giám sát:</strong></p>
        {html_table}
        <br><br>
        <p class="footer">
          <b><i>&nbsp;&nbsp;&nbsp;Trân trọng./.</i></b><br><br><br>
          <div class="hospital-info">
            <img src="data:image/png;base64,{img}" alt="logo">
            <div class="hospital-text">
              <h5>PHÒNG ĐIỀU DƯỠNG<br>BỆNH VIỆN ĐẠI HỌC Y DƯỢC THÀNH PHỐ HỒ CHÍ MINH &#174;</h5>
            </div>
          </div>
        </p>
      </body>
    </html>"""

    sender_email = st.secrets["email_info"]["sender_email"]
    sender_password = st.secrets["email_info"]["sender_password"]
    msg = MIMEText(body, "html", "utf-8")
    msg["Subject"] = subject
    msg["From"] = sender_email

    recipients = [receiver_email]
    for key in ["email2", "email3"]:
        if st.session_state.get(key):
            recipients.append(st.session_state[key])

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, sender_password)
        for recipient in recipients:
            msg.replace_header("To", recipient) if "To" in msg else msg.__setitem__("To", recipient)
            server.sendmail(sender_email, recipient, msg.as_string())

# ======================== DATA HELPERS ========================

def precheck_table():
    fv = st.session_state.get("form_version", 0)
    quy_trinh = st.session_state.quy_trinh
    rows = [
        {
            "Bước": quy_trinh.iloc[i, 6],
            "Nội dung": quy_trinh.iloc[i, 7],
            "Kết quả": st.session_state.get(f"radio_{i}_{fv}", ""),
            "Tồn đọng": st.session_state.get(f"text_{i}_{fv}", ""),
        }
        for i in range(len(quy_trinh))
    ]
    return pd.DataFrame(rows)

def clear_all_selections():
    fv = st.session_state.get("form_version", 0)
    quy_trinh = st.session_state.get("quy_trinh")
    if quy_trinh is not None:
        for i in range(len(quy_trinh)):
            st.session_state.pop(f"radio_{i}_{fv}", None)
            st.session_state.pop(f"text_{i}_{fv}", None)
    for key in ["nv2", "nv3", "email2", "email3", "precheck", "luu",
                "quy_trinh", "ten_quy_trinh", "loaiqt", "sttqt",
                "ds_buocantoan", "ds_buocNDNB", "ma_quy_trinh", "tltt",
                "khoa_GSQT", "nv_thuchien_GSQT", "email_nvthqt", "vtgs_GSQT",
                "doituong_duocgiamsat"]:
        st.session_state.pop(key, None)
    # Tăng version → toàn bộ widget key thay đổi → Streamlit render widget trắng
    st.session_state["form_version"] = fv + 1
    st.session_state["form_cleared"] = True

def check_duplicate_submission(column_khoa, column_nvth, column_nvgs, column_vtndg, column_qt, column_data):
    try:
        gc = gspread.authorize(load_credentials())
        sheet = gc.open(st.secrets["sheet_name"]["output_1"]).sheet1
        all_data = sheet.get_all_values()
        if len(all_data) <= 1:
            return False, None

        today_date = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).strftime("%Y-%m-%d")
        for row_idx, row in enumerate(all_data[1:], start=1):
            if len(row) < 8:
                continue
            row_date = row[1].split(" ")[0] if row[1] else ""
            if (row_date == today_date
                    and row[2].strip() == column_khoa.strip()
                    and row[3].strip() == column_nvth.strip()
                    and row[4].strip() == column_nvgs.strip()
                    and row[6].strip() == column_qt.strip()
                    and row[7].strip() == column_data.strip()):
                return True, row_idx
        return False, None
    except Exception as e:
        st.error(f"❌ Lỗi kiểm tra trùng lặp: {str(e)}")
        return False, None

def append_row_safe(sheet, row_data, retries=3):
    for i in range(retries):
        try:
            last_row = len(sheet.col_values(1))
            next_row = last_row + 1
            if next_row > sheet.row_count:
                sheet.add_rows(1000)
            sheet.update(f"A{next_row}:N{next_row}", [row_data])
            return True
        except Exception as e:
            if i < retries - 1:
                time.sleep(1)
            else:
                raise e

def upload_data_GS(data):
    gc = gspread.authorize(load_credentials())
    sheet = gc.open(st.secrets["sheet_name"]["output_1"]).sheet1

    now_vn = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
    ds_buocantoan = st.session_state.ds_buocantoan
    ds_buocNDNB = st.session_state.ds_buocNDNB

    column_data = ""
    so_buoc_dung_du = buoc_an_toan_dung_du = buoc_nhan_dang_dung_du = 0
    tong_so_buoc_tru_KAD = len(data)
    tong_an_toan_tru_an_toan_va_KAD = len(ds_buocantoan)
    tong_nhan_dang_tru_nhan_dang_va_KAD = len(ds_buocNDNB)

    for i, row in data.iterrows():
        buoc, ketqua, tondong = str(row["Bước"]), str(row["Kết quả"]), str(row["Tồn đọng"])
        buoc_int = i + 1
        if ketqua == "Thực hiện đúng, đủ":
            so_buoc_dung_du += 1
            if buoc_int in ds_buocantoan:
                buoc_an_toan_dung_du += 1
            if buoc_int in ds_buocNDNB:
                buoc_nhan_dang_dung_du += 1
        if ketqua == "KHÔNG ÁP DỤNG":
            tong_so_buoc_tru_KAD -= 1
            if buoc_int in ds_buocantoan:
                tong_an_toan_tru_an_toan_va_KAD -= 1
            if buoc_int in ds_buocNDNB:
                tong_nhan_dang_tru_nhan_dang_va_KAD -= 1
            if tong_so_buoc_tru_KAD == 0:
                st.session_state.loi_KAD = True
                st.session_state.loi_KADtime = time.time()
                st.rerun()
        separator = "#" if tondong in ("Chưa điền", "") else tondong + "#"
        column_data += f"{buoc}|{ketqua}|{'#' if tondong in ('Chưa điền', '') else tondong + '#'}"

    tltt = round(so_buoc_dung_du / tong_so_buoc_tru_KAD, 4)
    st.session_state.tltt = tltt
    tlan = round(buoc_an_toan_dung_du / tong_an_toan_tru_an_toan_va_KAD, 4) if tong_an_toan_tru_an_toan_va_KAD else ""
    tlnd = round(buoc_nhan_dang_dung_du / tong_nhan_dang_tru_nhan_dang_va_KAD, 4) if tong_nhan_dang_tru_nhan_dang_va_KAD else ""
    column_data = column_data.rstrip("#")

    column_ghichu1 = st.session_state.get("nv2") or st.session_state.get("doituong_duocgiamsat") or ""
    column_ghichu2 = st.session_state.get("nv3") or ""

    is_duplicate, _ = check_duplicate_submission(
        st.session_state.khoa_GSQT, st.session_state.nv_thuchien_GSQT,
        st.session_state.username, st.session_state.vtgs_GSQT,
        st.session_state.ten_quy_trinh, column_data,
    )
    if is_duplicate:
        warning(5, 2)
        return False

    row_data = [
        len(sheet.col_values(1)),
        now_vn.strftime("%Y-%m-%d %H:%M:%S"),
        st.session_state.khoa_GSQT,
        st.session_state.nv_thuchien_GSQT,
        st.session_state.username,
        st.session_state.vtgs_GSQT,
        st.session_state.ten_quy_trinh,
        column_data,
        st.session_state.ma_quy_trinh,
        tltt, tlan, tlnd,
        column_ghichu1, column_ghichu2,
    ]
    append_row_safe(sheet, row_data)
    return True

# ======================== MAIN SECTION========================

# form_version là bộ đếm suffix cho tất cả widget key.
# Mỗi lần clear_all_selections() tăng lên 1 → Streamlit tạo widget mới hoàn toàn,
# không phục hồi giá trị cũ từ bộ nhớ nội bộ.
if "form_version" not in st.session_state:
    st.session_state["form_version"] = 0

if st.session_state.get("loi_KAD", False):
    if time.time() - st.session_state.get("loi_KADtime", 0) < 2:
        warning(3, 2)
    else:
        st.session_state.pop("loi_KAD", None)
        st.session_state.pop("loi_KADtime", None)

load_css(pathlib.Path("asset/style.css"))
img = get_img_as_base64("pages/img/logo.png")

st.markdown(f"""
    <div class="fixed-header">
        <div class="header-content">
            <img src="data:image/png;base64,{img}" alt="logo">
            <div class="header-text">
                <h1>BỆNH VIỆN ĐẠI HỌC Y DƯỢC THÀNH PHỐ HỒ CHÍ MINH<span style="vertical-align: super; font-size: 0.6em;">&#174;</span>
                <br><span style="color:#c15088">Phòng Điều dưỡng</span></h1>
            </div>
        </div>
        <div class="header-subtext"><p>GIÁM SÁT QUY TRÌNH</p></div>
    </div>
    <div class="header-underline"></div>
""", unsafe_allow_html=True)

st.html(f'<p class="demuc"><i>Nhân viên đang giám sát: {st.session_state.username}</i></p>')
vitrigs()
thong_tin_hanh_chinh()
st.divider()
bang_kiem_quy_trinh()

if st.session_state.get("form_cleared", False):
    st.session_state["form_cleared"] = False
    st.stop()

luachon = [
    "Thực hiện đúng, đủ",
    "Thực hiện đúng nhưng chưa đủ",
    "Thực hiện chưa đúng, KHÔNG thực hiện",
    "KHÔNG ÁP DỤNG",
]

if all([
    st.session_state.get("khoa_GSQT"),
    st.session_state.get("nv_thuchien_GSQT"),
    st.session_state.get("vtgs_GSQT") is not None,
    st.session_state.get("quy_trinh") is not None,
]):
    quy_trinh = st.session_state.quy_trinh
    fv = st.session_state.get("form_version", 0)
    data_nv = None  # lazy load chỉ khi cần

    for stt, extra_label in [("215", "Nhân viên thực hiện quy trình 2"), ("216", "Nhân viên thực hiện quy trình 3")]:
        if st.session_state.sttqt in (stt, "216") if stt == "215" else st.session_state.sttqt == stt:
            if data_nv is None:
                data_nv = load_data(st.secrets["sheet_name"]["input_1"])
            data_nv1 = data_nv.loc[data_nv["Khoa"].str.contains("Khoa Gây mê hồi sức", case=False)]
            key = "nv2" if stt == "215" else "nv3"
            email_key = "email2" if stt == "215" else "email3"
            chon_nv = st.selectbox(label=extra_label, options=data_nv1["Nhân viên"],
                                   index=None, placeholder="", key=f"{key}_{fv}")
            if chon_nv:
                st.session_state[key] = chon_nv
                matches = data_nv1.loc[data_nv1["Nhân viên"] == chon_nv, "Email"]
                if not matches.empty:
                    st.session_state[email_key] = matches.values[0]
                else:
                    st.warning("Không tìm thấy email của nhân viên này")

    st.divider()
    for i in range(len(quy_trinh)):
        st.radio(
            label=f"Bước {quy_trinh.iloc[i, 5]}: {quy_trinh.iloc[i, 7]}",
            options=luachon,
            key=f"radio_{i}_{fv}",
            index=None,
        )
        kq = st.session_state.get(f"radio_{i}_{fv}")
        if kq not in ("Thực hiện đúng, đủ", "KHÔNG ÁP DỤNG", None):
            st.text_input(label="Tồn đọng", placeholder="Ghi rõ tồn đọng", key=f"text_{i}_{fv}")

    precheck = st.checkbox(label="Xem lại kết quả vừa nhập", key=f"precheck_{fv}")
    if precheck:
        buoc_chua_dien = [quy_trinh.iloc[j, 6]
                          for j in range(len(quy_trinh))
                          if not st.session_state.get(f"radio_{j}_{fv}")]
        if buoc_chua_dien:
            warning(1, ", ".join(buoc_chua_dien))
        else:
            st.dataframe(precheck_table(), hide_index=True)

    if st.button("Lưu kết quả", type="primary", key=f"luu_{fv}"):
        buoc_chua_dien = [quy_trinh.iloc[j, 6]
                          for j in range(len(quy_trinh))
                          if not st.session_state.get(f"radio_{j}_{fv}")]
        if buoc_chua_dien:
            warning(1, ", ".join(buoc_chua_dien))
        else:
            prechecktable = precheck_table()
            if upload_data_GS(prechecktable):
                warning(4, 2)
                #gui_email_qtkt(st.session_state.email_nvthqt, prechecktable)
                time.sleep(0.5)
                clear_all_selections()
else:
    st.warning("Vui lòng chọn đầy đủ các mục")