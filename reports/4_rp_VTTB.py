import streamlit as st
import pandas as pd
import gspread
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
import pathlib
import base64
from google.oauth2.service_account import Credentials
import plotly.express as px

@st.cache_data(ttl=3600)
def get_img_as_base64(file):
    with open(file, "rb") as f:
        data = f.read()
    
    return base64.b64encode(data).decode()

def load_css(file_path):
    with open(file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


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
def load_data(x):
    credentials = load_credentials()
    gc = gspread.authorize(credentials)
    sheet = gc.open(x).sheet1
    data = sheet.get_all_values()
    header = data[0]
    values = data[1:]
    data = pd.DataFrame(values, columns=header)
    return data

@st.cache_data(ttl=10)
def load_data1(sheeto5,sd,ed,khoa_select):
    credentials = load_credentials()
    gc = gspread.authorize(credentials)
    sheet = gc.open(sheeto5).sheet1
    data = sheet.get_all_values()
    header = data[0]
    values = data[1:]
    data = pd.DataFrame(values, columns=header)
    if khoa_select != "Chọn tất cả khoa":
        data = data.loc[data["Khoa báo cáo"].isin(khoa_select)]
    data['Timestamp'] = pd.to_datetime(data['Timestamp'], errors='coerce')
    start_date = sd
    end_date = ed + timedelta(days=1)
    data_final = data[(data['Timestamp'] >= pd.Timestamp(start_date)) & (data['Timestamp'] < pd.Timestamp(end_date))]
    return data_final

def chon_khoa(khoa):
    if st.checkbox("Chọn tất cả khoa"):
        khoa_select = "Chọn tất cả khoa"
    else:
        khoa_select = st.multiselect(label="Chọn khoa",
                                                options= khoa)
    return khoa_select

def khoa_chua_bao_cao(khoa,sd,ed):
    credentials = load_credentials()
    gc = gspread.authorize(credentials)
    sheeto5 = st.secrets["sheet_name"]["output_5"]
    sheet = gc.open(sheeto5).sheet1
    data = sheet.get_all_values()
    header = data[0]
    values = data[1:]
    datax = pd.DataFrame(values, columns=header)
    start_date = sd
    end_date = ed + timedelta(days=1)
    datax["Ngày báo cáo"] = pd.to_datetime(datax["Ngày báo cáo"]).dt.date
    datax = datax[(datax["Ngày báo cáo"] >= start_date) & (datax["Ngày báo cáo"] <= end_date)]
    data = datax.groupby("Ngày báo cáo").agg(
    Cac_khoa_da_bao_cao=("Khoa báo cáo", lambda x: ",".join(sorted(set(x)))),
    So_khoa_bao_cao=("Khoa báo cáo", lambda x: len(set(x)))  
    ).reset_index()
    data = data.rename(columns={
    "Cac_khoa_da_bao_cao": "Các khoa đã báo cáo",
    "So_khoa_bao_cao": "Số khoa đã báo cáo"
    })
    tat_ca_khoa = set(khoa)
    data["Các khoa chưa báo cáo"] = data["Các khoa đã báo cáo"].apply(
    lambda x: ", ".join(sorted(tat_ca_khoa - set(map(str.strip, x.split(",")))))
    )
    data["Số khoa chưa báo cáo"] = data["Các khoa chưa báo cáo"].apply(
    lambda x: 0 if not x else len(x.split(", "))
    )
    data["Các khoa đã báo cáo"] = data["Các khoa đã báo cáo"].str.replace(",", "\n")
    data["Các khoa chưa báo cáo"] = data["Các khoa chưa báo cáo"].str.replace(", ", "\n")
    return data


# Hàm hỗ trợ để tách giá trị từ cột "Thiết bị thông thường"
def tach_cot_lay_dang_su_dung(column_data, header):
    """
    Tách giá trị từ cột "Thiết bị thông thường" dựa trên header.
    """
    if pd.isna(column_data):
        return None
    for item in column_data.split("#"):  # Giả sử các cụm thiết bị được phân tách bằng dấu "#"
        parts = item.split("|")
        if len(parts) >= 3 and parts[0].strip() == header:  # Kiểm tra header
            try:
                return int(parts[2].strip())  # Lấy giá trị nằm giữa dấu "|" thứ 2 và thứ 3
            except ValueError:
                return None
    return None

def tinh_tong_dang_su_dung(data, header):
    result = pd.DataFrame()
    result["Ngày báo cáo"] = data["Ngày báo cáo"].unique()
    # Tính tổng cho từng thiết bị theo ngày báo cáo
    for header in headers:
        result[header] = result["Ngày báo cáo"].apply(
            lambda date: data[data["Ngày báo cáo"] == date]["Thiết bị thông thường"].apply(
                lambda x: tach_cot_lay_dang_su_dung(x, header)
            ).sum()
        )
    avg_row = pd.DataFrame(result[headers].mean(axis=0)).T
    avg_row.insert(0, "Ngày báo cáo", "Trung bình")
    result = pd.concat([result, avg_row], ignore_index=True)
    return result

def tach_gia_tri_co_so(column_data, header):
    """
    Lấy giá trị cơ số từ cột "Thiết bị thông thường" dựa trên header.
    (Giá trị nằm giữa dấu | thứ 1 và thứ 2)
    """
    if pd.isna(column_data):
        return 0
    for item in column_data.split("#"):
        parts = item.split("|")
        if len(parts) >= 3 and parts[0].strip() == header:
            try:
                return int(parts[1].strip())
            except ValueError:
                return 0
    return 0

def tinh_phan_tram_su_dung(data, headers):
    """
    Trả về DataFrame phần trăm sử dụng theo ngày và thiết bị.
    """
    # Lấy danh sách ngày báo cáo
    ngay_bao_cao = data["Ngày báo cáo"].unique()
    # Tạo bảng tổng số lượng đang sử dụng
    tong_su_dung = tinh_tong_dang_su_dung(data, headers)
    # Tạo bảng tổng cơ số
    co_so_dict = {}
    for header in headers:
        co_so_dict[header] = []
        for ngay in ngay_bao_cao:
            mask = data["Ngày báo cáo"] == ngay
            co_so = data.loc[mask, "Thiết bị thông thường"].apply(lambda x: tach_gia_tri_co_so(x, header)).sum()
            co_so_dict[header].append(co_so)
    # Tạo DataFrame cơ số
    co_so_df = pd.DataFrame(co_so_dict)
    co_so_df.insert(0, "Ngày báo cáo", ngay_bao_cao)
    # Tính phần trăm
    phan_tram_df = tong_su_dung.copy()
    for header in headers:
        phan_tram_df[header] = (tong_su_dung[header] / co_so_df[header].replace(0, pd.NA) * 100).round(2)
    # Dòng trung bình
    avg_row = pd.DataFrame(phan_tram_df[headers].mean(axis=0)).T
    avg_row.insert(0, "Ngày báo cáo", "Trung bình")
    phan_tram_df = pd.concat([phan_tram_df.iloc[:-1], avg_row], ignore_index=True)
    return phan_tram_df

def highlight_total_row_generic(row, total_row_idx):
    if row.name == total_row_idx:
        return ['background-color: #ffe599; color: #cf1c00'] * len(row)
    return [''] * len(row)

##################################### Main Section ###############################################
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
        <p style="color:green">THỐNG KÊ BÁO CÁO THIẾT BỊ HẰNG NGÀY</p>
        </div>
    </div>
    <div class="header-underline"></div>

 """, unsafe_allow_html=True)
html_code = f'<p class="demuc"><i>Nhân viên: {st.session_state.username}</i></p>'
st.html(html_code)
sheeti5 = st.secrets["sheet_name"]["input_5"]
data = load_data(sheeti5)
khoa = data["Khoa"].unique()
now_vn = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))  
md = date(2025, 1, 1)
with st.form("Thời gian"):
    cold = st.columns([5,5])
    with cold[0]:
        sd = st.date_input(
        label="Ngày bắt đầu",
        value=md,
        min_value=md,
        max_value=now_vn.date(), 
        format="DD/MM/YYYY",
        )
    with cold[1]:
        ed = st.date_input(
        label="Ngày kết thúc",
        value=now_vn.date(),
        min_value=md,
        max_value=now_vn.date(), 
        format="DD/MM/YYYY",
        )
    khoa_select = chon_khoa(khoa)
    submit_thoigian = st.form_submit_button("OK")
if submit_thoigian:
    if ed < sd:
        st.error("Lỗi ngày kết thúc đến trước ngày bắt đầu. Vui lòng chọn lại")  
    else:           
        sheeto5 = st.secrets["sheet_name"]["output_5"]
        tab1, tab2, tab3 = st.tabs(["Báo cáo thiết bị hằng ngày", "Thống kê toàn viện","Thống kê theo khoa"])
        with tab1:
            data1 = khoa_chua_bao_cao(khoa,sd,ed)
            st.write(f"Thống kê báo cáo theo ngày")
            st.dataframe(data1, use_container_width=True, hide_index=True)
        with tab2:
            sheeti5 = st.secrets["sheet_name"]["input_5"]
            data_input5 = load_data(sheeti5)
            headers = data_input5["Tên thiết bị"].unique()
            data_output5 = load_data1(sheeto5, sd, ed, khoa_select)
            data_output5["Thiết bị thông thường"] = data_output5["Thiết bị thông thường"].fillna("").astype(str)
            data_tong_hop = tinh_tong_dang_su_dung(data_output5, headers)
            if data_output5.empty:
                st.warning("Không có dữ liệu theo yêu cầu")
            else:
                st.markdown("<h5 style='text-align: center;'>Số lượng sử dụng các thiết bị toàn viện</h5>", unsafe_allow_html=True)
                st.dataframe(data_tong_hop,use_container_width=True, hide_index=True)
            
            # Tính Hiệu suất sử dụng (%)
            st.markdown("<h5 style='text-align: center;'>Hiệu suất sử dụng các thiết bị toàn viện (%)</h5>", unsafe_allow_html=True)
            phan_tram_df = tinh_phan_tram_su_dung(data_output5, headers)
            for header in headers:
                    phan_tram_df[header] = phan_tram_df[header].apply(
                        lambda x: f"{round(float(x),2)}" if pd.notna(x) and x != "" else ""
                    )
            st.dataframe(phan_tram_df.style.apply( lambda row: highlight_total_row_generic(row, len(phan_tram_df) - 1), axis=1), use_container_width=True, hide_index=True)
                        # Sau khi đã có phan_tram_df và headers
            # Lấy dòng trung bình (dòng cuối cùng)
            avg_row = phan_tram_df.iloc[-1]
            # Loại bỏ cột "Ngày báo cáo"
            avg_row = avg_row.drop("Ngày báo cáo")
            # Chuyển giá trị về float (nếu đang là string có ký tự %)
            avg_row_float = avg_row.apply(lambda x: float(str(x).replace("%", "")) if x != "" else 0)
            fig = px.bar(
                x=headers,
                y=[avg_row_float[header] for header in headers],
                labels={'x': '', 'y': 'Hiệu suất sử dụng (%)'},
                text=[avg_row_float[header] for header in headers],
                color_discrete_sequence=["#1f77b4"],
            )
            fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
            fig.update_layout(yaxis_tickformat='.2f')
            st.markdown("<h5 style='text-align: center;'>Biểu đồ hiệu suất sử dụng các thiết bị toàn viện</h5>", unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True)
        with tab3:                            
            sheeti5 = st.secrets["sheet_name"]["input_5"]
            data_input5 = load_data(sheeti5)
            headers = data_input5["Tên thiết bị"].unique()
            data_output5 = load_data1(sheeto5, sd, ed, khoa_select)
            if data_output5.empty:
                st.warning("Không có dữ liệu theo yêu cầu")
            else:
                data_expanded = data_output5[["Timestamp", "Ngày báo cáo", "Khoa báo cáo", "Người báo cáo"]].copy()
                for header in headers:
                    data_expanded[header] = data_output5["Thiết bị thông thường"].apply(
                        lambda x: tach_cot_lay_dang_su_dung(x, header)
                    )
                sum_row = {col: "" for col in data_expanded.columns}
                for header in headers:
                    sum_row[header] = data_expanded[header].sum()
                sum_row["Người báo cáo"] = "Tổng"
                data_expanded = pd.concat([data_expanded, pd.DataFrame([sum_row])], ignore_index=True)
                st.markdown("<h5 style='text-align: center;'>Số lượng sử dụng các thiết bị</h5>", unsafe_allow_html=True)
                st.dataframe(
                    data_expanded.style.apply(lambda row: highlight_total_row_generic(row, len(data_expanded) - 1), axis=1),
                    use_container_width=True,
                    hide_index=True
                )
            st.markdown("<h5 style='text-align: center;'>Hiệu suất sử dụng các thiết bị toàn viện (%)</h5>", unsafe_allow_html=True)
            phan_tram_df = tinh_phan_tram_su_dung(data_output5, headers)
            for header in headers:
                    phan_tram_df[header] = phan_tram_df[header].apply(
                        lambda x: f"{round(float(x),2)}" if pd.notna(x) and x != "" else ""
                    )
            st.dataframe(phan_tram_df.style.apply( lambda row: highlight_total_row_generic(row, len(phan_tram_df) - 1), axis=1), use_container_width=True, hide_index=True)
                        # Sau khi đã có phan_tram_df và headers
            # Lấy dòng trung bình (dòng cuối cùng)
            avg_row = phan_tram_df.iloc[-1]
            # Loại bỏ cột "Ngày báo cáo"
            avg_row = avg_row.drop("Ngày báo cáo")
            # Chuyển giá trị về float (nếu đang là string có ký tự %)
            avg_row_float = avg_row.apply(lambda x: float(str(x).replace("%", "")) if x != "" else 0)
            fig = px.bar(
                x=headers,
                y=[avg_row_float[header] for header in headers],
                labels={'x': '', 'y': 'Hiệu suất sử dụng (%)'},
                text=[avg_row_float[header] for header in headers],
                color_discrete_sequence=["#1f77b4"],
            )
            fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
            fig.update_layout(yaxis_tickformat='.2f')

                