import streamlit as st
import pandas as pd
import gspread
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
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
    if st.session_state.phan_quyen == "2" and x == st.secrets["sheet_name"]["input_1"]:
        data_final = data_final.drop(["Phân quyền","Mật khẩu"], axis=1)
    if x == st.secrets["sheet_name"]["input_2"]:
        data_final = data_final.drop(["Kết quả đánh giá","Tồn đọng"], axis=1)
    return data_final

@st.cache_data(ttl=10)
def get_key_from_value(dictionary, value):
    return next((key for key, val in dictionary.items() if val == value), None)

@st.cache_data(ttl=10)
def load_data_GSheet(name):
    credentials = load_credentials()
    gc = gspread.authorize(credentials)
    sheet = gc.open(name).sheet1
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
    start_date = st.session_state.sd
    end_date = st.session_state.ed + timedelta(days=1)
    df = df[(df['Timestamp'] >= pd.Timestamp(start_date)) & (df['Timestamp'] < pd.Timestamp(end_date))]
    if name != st.secrets["sheet_name"]["output_4"]:
        df["Data"] = df["Data"].str.replace("#", "\n")
        df["Data"] = df["Data"].str.replace("|", "  ")
    if name == st.secrets["sheet_name"]["output_1"]:
        df = df.drop(["Mã quy trình","Tỉ lệ tuân thủ","Tỉ lệ an toàn"], axis=1)
    return df

def change_GS(stt,tt1,kq1):
    credentials = load_credentials()
    gc = gspread.authorize(credentials)
    sheeto4 = st.secrets["sheet_name"]["output_4"]
    sheet = gc.open(sheeto4).sheet1
    sheet.update_cell(stt+1, 8, tt1)
    sheet.update_cell(stt+1, 9, kq1)
    st.toast("Đã cập nhật thay đổi")

def xoa_dong(stt_xx,sheetb):
    credentials = load_credentials()
    gc = gspread.authorize(credentials)
    sheet = gc.open(sheetb).sheet1
    sheet.delete_rows(stt_xx+1)
    stt_xx = [[i] for i in range(1, len(sheet.get_all_values()))]  # Danh sách số thứ tự

    # Xây vùng cần cập nhật (ví dụ A2:A101 nếu cột A là STT)
    start_row = 2  # Bỏ qua tiêu đề
    end_row = len(sheet.get_all_values())
    col_letter = chr(64 + 1)  # 1 -> A, 2 -> B, ...
    cell_range = f"{col_letter}{start_row}:{col_letter}{end_row}"

    # Dùng batch update
    cell_range_obj = sheet.range(cell_range)
    for i, cell in enumerate(cell_range_obj):
        cell.value = i + 1  # STT bắt đầu từ 1

    sheet.update_cells(cell_range_obj)  # Gửi 1 lần duy nhất
    st.toast("Đã xóa dòng theo yêu cầu")
#########################################################################################################
#Cài thời gian sẵn
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
        <p style="color:#b36002; padding-left:25px">TRANG QUẢN TRỊ</p>
        </div>
    </div>
    <div class="header-underline"></div>

 """, unsafe_allow_html=True)
html_code = f'<p class="admin_1"><i>Xin chào admin:{st.session_state.username}</i></p>'
st.html(html_code)

#Giá trị này giúp cache nhận ra sự thay đổi đầu vào
input_data = {
              "input_1":"Danh sách nhân sự",
              "input_2":"Giám sát quy trình",
              "input_3":"Hồ sơ bệnh án",
              "input_4":"Giáo dục sức khỏe",
              }
inp = st.selectbox(label="Input",
            options=["---"]+ list(input_data.values()),
            index=0,             
            )
if inp and inp != "---":
    with st.expander("Mở rộng 🌦️"):
        try:
            a = get_key_from_value(input_data, inp)
            sheet = st.secrets["sheet_name"][a]
            data_in = load_data(sheet)
            st.dataframe(data_in, hide_index=True,height=225)
        except:
            st.write("Chọn bảng input")
output_data = {
              "output_1":"Data giám sát quy trình",
              "output_2":"Data hồ sơ bệnh án",
              "output_3":"Data giáo dục sức khỏe",
              "output_4":"Các yêu cầu bổ sung/phân quyền"
              }
outp = st.selectbox(label="Output",
            options=["---"]+ list(output_data.values()),
            index=0,             
            )

now_vn = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
md = date(2025, 1, 1) 
if outp and outp != "---":
        with st.expander("Mở rộng 🌦️"):
            with st.form("Thời gian"):
                cold = st.columns([5,5])
                with cold[0]:
                    sd = st.date_input(
                    label="Ngày bắt đầu",
                    value=md,
                    min_value=md,
                    max_value=now_vn.date(), 
                    format="DD/MM/YYYY",
                    key="sd",
                    )
                with cold[1]:
                    ed = st.date_input(
                    label="Ngày kết thúc",
                    value=now_vn.date(),
                    min_value=md,
                    max_value=now_vn.date(), 
                    format="DD/MM/YYYY",
                    key="ed",
                    )
                submit_thoigian = st.form_submit_button("Cập nhật ngày")
            if submit_thoigian:
                if ed < sd:
                    st.error("Ngày kết thúc đến trước ngày bắt đầu. Vui lòng chọn lại")                    
            try:
                placeholder = st.empty()
                b = get_key_from_value(output_data, outp)
                sheetb = st.secrets["sheet_name"][b]
                data_out = load_data_GSheet(sheetb)
                if data_out.empty:
                    st.warning("Không có dữ liệu trong khoảng thời gian yêu cầu")
                else:
                    columns = data_out.columns.tolist()
                    rows = list(range(1,len(data_out)+1))
                    placeholder.dataframe(data_out, hide_index=True)
                    if outp == "Các yêu cầu bổ sung/phân quyền":
                        st.write("Thông tin muốn chỉnh sửa")
                        with st.form("Thay đổi tình trạng"):
                            col = st.columns([2,3,3])
                            with col[0]:
                                stt = st.number_input(label="STT yêu cầu", 
                                                    min_value=1, 
                                                    max_value=len(data_out), 
                                                    step=1,
                                                    key="stt",
                                                    )
                            with col[1]:
                                tt = st.selectbox("Đổi tình trạng", 
                                                options=["Chưa xem","Đã xem"],
                                                key="tt",
                                                )
                            with col[2]:
                                kq = st.selectbox("Đổi kết quả", 
                                                options=["Trống","Hoàn thành","Từ chối"],
                                                key="kq",
                                                )
                            submit_tt = st.form_submit_button("Lưu")
                        if submit_tt:
                            if (tt == "Chưa xem" and kq == "Từ chối") or (tt == "Chưa xem" and kq == "Hoàn thành"):
                                st.write("Giá trị kết quả không phù hợp")
                            else:
                                print('qqqq')
                                if tt == "Chưa xem":
                                    tt1 = ""
                                    kq1 = ""
                                else:
                                    tt1 = "x"
                                if kq == "Trống":
                                    kq1 = ""
                                elif kq == "Hoàn thành":
                                    kq1 = "1"
                                else:
                                    kq1 = "0"
                                change_GS(stt,tt1,kq1)
                                data_out = load_data_GSheet(sheetb)
                                placeholder.dataframe(data_out, hide_index=True)
                    else:
                        # col = st.columns([5,5])
                        # with col[0]:
                        with st.form("Xóa và sửa bảng"):
                            stt_xx = st.number_input(label="STT dòng cần xóa", 
                                                min_value=1, 
                                                max_value=len(data_out), 
                                                step=1,
                                                key="stt_xx",
                                                )
                            submitxs = st.form_submit_button("Xóa")
                        if submitxs:
                            xoa_dong(stt_xx,sheetb)
            except Exception as e:
                st.write("Lỗi xảy ra:", e)
                
                       
        
        