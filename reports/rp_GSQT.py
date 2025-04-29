import streamlit as st
import pandas as pd
import gspread
import datetime
import pathlib
import base64
from google.oauth2.service_account import Credentials
import numpy as np

@st.cache_data(ttl=3600)
def get_img_as_base64(file):
    with open(file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

def load_css(file_path):
    with open(file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
css_path = pathlib.Path("asset/style.css")

@st.cache_data(ttl=10)
def get_key_from_value(dictionary, value):
    return next((key for key, val in dictionary.items() if val == value), None)
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

@st.cache_data(ttl=10)
def load_data(x,sd,ed):
    credentials = load_credentials()
    gc = gspread.authorize(credentials)
    sheet = gc.open(x).sheet1
    data = sheet.get_all_values()
    header = data[0]
    values = data[1:]
    data = pd.DataFrame(values, columns=header)
    data['Timestamp'] = pd.to_datetime(data['Timestamp'], errors='coerce')
    start_date = sd
    end_date = ed + datetime.timedelta(days=1)
    data_final = data[(data['Timestamp'] >= pd.Timestamp(start_date)) & (data['Timestamp'] < pd.Timestamp(end_date))]
    return data_final

def tao_thong_ke(x,y):
    df = pd.DataFrame(x)
    #Lấy những cột cần cho hiển thị lên trang báo cáo
    bo_cot = df[['Timestamp','Khoa', 'Tên quy trình', 'Tỉ lệ tuân thủ','Tỉ lệ an toàn','Tên người đánh giá', 'Tên người thực hiện']]
    #Chuyển những cột tuân thủ thành dạng số nhờ đổi dấu "," thành "."
    bo_cot['Tỉ lệ tuân thủ'] = bo_cot['Tỉ lệ tuân thủ'].str.replace(',', '.')
    #Chuyển dạng số chính thức
    bo_cot['Tỉ lệ tuân thủ'] = pd.to_numeric(bo_cot["Tỉ lệ tuân thủ"], errors='coerce')
    #Nhấn 100 thành tỉ lệ phần trăm
    bo_cot['Tỉ lệ tuân thủ'] = bo_cot['Tỉ lệ tuân thủ'] * 100
    #Tương tự với tỉ lệ an toàn
    bo_cot['Tỉ lệ an toàn'] = bo_cot['Tỉ lệ an toàn'].str.replace(',', '.')
    bo_cot['Tỉ lệ an toàn'] = pd.to_numeric(bo_cot["Tỉ lệ an toàn"], errors='coerce')
    if y == "Chi tiết":
        bo_cot = pd.DataFrame(bo_cot).sort_values(["Timestamp","Tên quy trình"])
        bo_cot['Tỉ lệ an toàn'] = bo_cot['Tỉ lệ an toàn'].apply(lambda x: x * 100 if pd.notna(x) else np.nan)
        bo_cot.insert(0, 'STT', range(1, len(bo_cot) + 1))
        if st.session_state.phan_quyen == "4" and st.session_state.username not in ["Trần Thị Bích Thủy (E98-020)","Nguyễn Thị Thanh Trúc (D05-118)","Phạm Hồng Khuyên (D05-066)"]:
            bo_cot = bo_cot.drop("Khoa",axis=1)
        return bo_cot
    else:
        bo_cot = bo_cot.drop(["Timestamp","Tên người đánh giá", "Tên người thực hiện"], axis=1)
        # Lọc ra 1 bảng chứa những dòng có giá trị an toàn là số
        bang_co_tlan = bo_cot.loc[pd.notna(bo_cot["Tỉ lệ an toàn"])]
        # Nhóm lại bảng đó theo khoa và tên quy trình, tạo thêm 3 cột, là tỉ lệ an toàn bàng trung bình, tỉ lệ tuân thủ bằng trung bình, và cột số lượt là bằng count số lần của tên quy trình
        ket_qua1 = bang_co_tlan.groupby(["Khoa","Tên quy trình"]).agg({
        "Tên quy trình": "count",
        "Tỉ lệ tuân thủ": "mean",
        "Tỉ lệ an toàn": "mean",
        }).rename(columns={"Tên quy trình": "Số lượt"}).reset_index()
        # Làm tương tự với bảng chứa các giá trị an toàn là NaN, tiêng cột giá trị an toàn không fungd hàm mean nữa mà mình sẽ lấy giá trị đầu tiên cũng chính là NaN
        bang_khong_tlan = bo_cot.loc[pd.isna(bo_cot["Tỉ lệ an toàn"])]
        ket_qua2 = bang_khong_tlan.groupby(["Khoa","Tên quy trình"]).agg({
        "Tên quy trình": "count",
        "Tỉ lệ tuân thủ": "mean",
        "Tỉ lệ an toàn": "first",
        }).rename(columns={"Tên quy trình": "Số lượt"}).reset_index()
        # Gép 2 bảng lại
        ket_qua = pd.concat([ket_qua1, ket_qua2], ignore_index=True)
        # Forrmat lại với điều kiện nếu giá trị trong cột an toàn không là NaN (if pd.notna(x)) thì giá trị đó được * 100 để chuyển sang dạng %, còn ngược lại (else thì sẽ giữ nguyên giá trị là NaN)
        ket_qua['Tỉ lệ an toàn'] = ket_qua['Tỉ lệ an toàn'].apply(lambda x: x * 100 if pd.notna(x) else np.nan)
        # Sort kết quả theo tên khoa
        ket_qua = pd.DataFrame(ket_qua).sort_values("Khoa")
        # Gắn thêm cột số thứ tự cho i chạy từ 1 đến số dòng của bảng mới gộp
        ket_qua.insert(0, 'STT', range(1, len(ket_qua) + 1))
        if st.session_state.phan_quyen == "4" and st.session_state.username not in ["Trần Thị Bích Thủy (E98-020)","Nguyễn Thị Thanh Trúc (D05-118)","Phạm Hồng Khuyên (D05-066)"]:
            ket_qua=ket_qua.drop("Khoa",axis=1)
        return ket_qua
##################################### Main Section ###############################################
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
        <p style="color:green">BÁO CÁO GIÁM SÁT QUY TRÌNH KỸ THUẬT</p>
        </div>
    </div>
    <div class="header-underline"></div>

 """, unsafe_allow_html=True)
html_code = f'<p class="demuc"><i>Điều dưỡng: {st.session_state.username}</i></p>'
st.html(html_code)
loai_qtkt = {  "All":"Tất cả",
              "QTCB":"Quy trình cơ bản",
              "QTCK":"Quy trình chuyên khoa",
              "CSCS":"Chỉ số chăm sóc điều dưỡng",
              "KHAC":"Khác",
              }
with st.form("Thời gian"):
    cold = st.columns([5,5])
    with cold[0]:
        sd = st.date_input(
        label="Ngày bắt đầu",
        value=datetime.date(2025, 1, 1),
        min_value=datetime.date(2025, 1, 1),
        max_value=datetime.date.today(), 
        format="DD/MM/YYYY",
        )
    with cold[1]:
        ed = st.date_input(
        label="Ngày kết thúc",
        value=datetime.date.today(),
        min_value=datetime.date(2025, 1, 1),
        max_value=datetime.date.today(), 
        format="DD/MM/YYYY",
        )
    chon_loai_qtkt = st.selectbox(label="Loại quy trình kỹ thuật",
            options=list(loai_qtkt.values()),
            index=0,             
            )
    submit_thoigian = st.form_submit_button("Xem thống kê")
if submit_thoigian:
    if ed < sd:
        st.error("Ngày kết thúc đến trước ngày bắt đầu. Vui lòng chọn lại")  
    else:
        loc_loai_qt = get_key_from_value(loai_qtkt, chon_loai_qtkt)
        data = load_data("Output-st-GSQT",sd,ed)
        if st.session_state.phan_quyen == "4":
            if st.session_state.username == "Trần Thị Bích Thủy (E98-020)":
                data = data.loc[data["Khoa"].isin([
                        "Khoa Gây mê hồi sức - Gây mê",
                        "Khoa Gây mê hồi sức - Hồi tỉnh",
                        "Khoa Gây mê hồi sức - Dụng cụ"
                    ])]
            elif st.session_state.username == "Phạm Hồng Khuyên (D05-066)":
                data = data.loc[data["Khoa"].isin([
                        "Khoa Ngoại Thần kinh",
                        "Khoa Nội Cơ Xương Khớp",
                    ])]
            elif st.session_state.username == "Nguyễn Thị Thanh Trúc (D05-118)":
                data = data.loc[data["Khoa"].isin([
                        "Khoa Lồng ngực mạch máu",
                        "Khoa Tiết niệu",
                    ])]
            else:
                data = data.loc[data["Khoa"]==st.session_state.khoa]
        if data.empty:
            st.warning("Không có dữ liệu theo yêu cầu")
        else:
            if loc_loai_qt != "All":
                data = data[(data["Mã quy trình"] == loc_loai_qt)]
            if data.empty:
                st.warning("Không có dữ liệu theo yêu cầu")
            else:
                with st.expander("Thống kê tổng quát"):
                    thongke = tao_thong_ke(data,"Tổng quát")
                    st.dataframe(thongke, 
                                hide_index=True, 
                                column_config = {
                                    "Tỉ lệ tuân thủ": st.column_config.NumberColumn(format="%.2f %%"),
                                    "Tỉ lệ an toàn": st.column_config.NumberColumn(format="%.2f %%")
                                    })
                with st.expander("Thống kê chi tiết"):
                    thongkechitiet = tao_thong_ke(data,"Chi tiết")
                    st.dataframe(thongkechitiet,
                                hide_index=True, 
                                column_config = {
                                    "Tỉ lệ tuân thủ": st.column_config.NumberColumn(format="%.2f %%"),
                                    "Tỉ lệ an toàn": st.column_config.NumberColumn(format="%.2f %%")})


    


