import streamlit as st
import pandas as pd
import gspread
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
import pathlib
import base64
from google.oauth2.service_account import Credentials
import plotly.express as px
import numpy as np

@st.cache_data(ttl=3600)
def get_img_as_base64(file):
    with open(file, "rb") as f:
        data = f.read()
    
    return base64.b64encode(data).decode()

def load_css(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except UnicodeDecodeError:
        # Fallback to different encoding if UTF-8 fails
        with open(file_path, 'r', encoding='latin-1') as f:
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

# def tinh_phan_tram_su_dung(data, headers):
    """
    Trả về DataFrame phần trăm sử dụng theo ngày và thiết bị.
    """
    # Lấy danh sách ngày báo cáo
    data["Ngày báo cáo"] = pd.to_datetime(data["Ngày báo cáo"]).dt.strftime("%d/%m/%Y")
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
        co_so_df[header] = pd.to_numeric(co_so_df[header], errors="coerce")
        tong_su_dung[header] = pd.to_numeric(tong_su_dung[header], errors="coerce")

# Tính toán phần trăm và làm tròn
        phan_tram_df[header] = (
                tong_su_dung[header] / co_so_df[header].mask(co_so_df[header] == 0)
            ).round(2)
    # Dòng trung bình
    avg_row = pd.DataFrame(phan_tram_df[headers].mean(axis=0)).T
    avg_row.insert(0, "Ngày báo cáo", "Trung bình")
    phan_tram_df = pd.concat([phan_tram_df.iloc[:-1], avg_row], ignore_index=True)
    return phan_tram_df

def tinh_phan_tram_su_dung(data,headers):
    credentials = load_credentials()
    gc = gspread.authorize(credentials)
    sheeti5 = st.secrets["sheet_name"]["input_5"]
    sheet = gc.open(sheeti5).worksheet("Trang tính2")
    datax = sheet.get_all_values()
    header = datax[0]
    values = datax[1:]
    phan_phoi_df = pd.DataFrame(values, columns=header)
    # Chuyển đổi cột "SL điều phối được" sang kiểu số  
    phan_phoi_df["SL điều phối được"] = pd.to_numeric(phan_phoi_df["SL điều phối được"], errors='coerce')
    phan_phoi_dict = phan_phoi_df.set_index("Thiết bị")["SL điều phối được"].to_dict()
    # Chuẩn hoá cột Ngày báo cáo thành dd/mm/YYYY (hoặc giữ nguyên datetime nếu bạn muốn)
    data = data.copy()
    data["Ngày báo cáo"] = pd.to_datetime(data["Ngày báo cáo"]).dt.strftime("%d/%m/%Y")
    # Tính tổng số đang sử dụng cho mỗi ngày (hàm bạn đã có sẵn)
    tong_su_dung = tinh_tong_dang_su_dung(data, headers)
    # ----- TÍNH % SỬ DỤNG ---------------------------------------------------
    phan_tram_df = tong_su_dung.copy()

    for header in headers:
        # Đảm bảo dữ liệu là số
        tong_su_dung[header] = pd.to_numeric(tong_su_dung[header], errors='coerce')
        mau_so = pd.to_numeric(phan_phoi_dict.get(header, np.nan), errors='coerce')
        
        # Tính tỉ lệ, tránh chia cho 0
        if pd.notna(mau_so) and mau_so != 0:
            phan_tram_df[header] = (tong_su_dung[header] / mau_so).round(2)
        else:
            phan_tram_df[header] = np.nan

    ##for header in headers:
        # Lấy mẫu số cố định; nếu thiếu thì gắn NaN để dễ kiểm tra lỗi
        ##mau_so = phan_phoi_dict.get(header, np.nan)
        ##mau_so = float(mau_so)
        # Tính % (nhân 100 nếu muốn hiển thị dạng phần trăm)
        ##phan_tram_df[header] = (tong_su_dung[header] / mau_so).round(2)
        # Nếu cần nhân 100:
        # phan_tram_df[header] = (tong_su_dung[header] / mau_so * 100).round(2)

    # ----- THÊM DÒNG TRUNG BÌNH --------------------------------------------
    avg_row = pd.DataFrame(phan_tram_df[headers].mean(axis=0)).T
    avg_row.insert(0, "Ngày báo cáo", "Trung bình")
    phan_tram_df = pd.concat([phan_tram_df.iloc[:-1], avg_row], ignore_index=True)
    return phan_tram_df


#### Hàm để định dạng bảng thứ 1
def highlight_last_row_factory(data):
    def highlight(row):
        if row.name == len(data) - 1:
            return ['background-color: #ffe599; color: #cf1c00'] * len(row)
        return [''] * len(row)
    return highlight

# Hàm định dạng từng ô (cell)
def custom_format(cell, row_idx, is_last_row):
    if isinstance(cell, (int, float)):
        if is_last_row:
            return f"{cell:,.2f}"
        else:
            return f"{int(cell):,}" if isinstance(cell, int) or cell == int(cell) else f"{cell:,.0f}"
    return cell

# Xử lý toàn bộ bảng: áp dụng định dạng theo từng dòng
def format_per_row(df):
    last_idx = len(df) - 1
    formatted = df.copy()
    for r in df.index:
        for c in df.columns:
            formatted.at[r, c] = custom_format(df.at[r, c], r, r == last_idx)
    return formatted

# Xử lý cột Ngày báo cáo (nếu có)
def format_date_column(df, col_name="Ngày báo cáo"):
    if col_name in df.columns:
        df[col_name] = df[col_name].apply(
            lambda x: x.strftime("%d/%m/%Y") if isinstance(x, pd.Timestamp) else x
        )
    return df
#################################

def highlight_total_row_generic(row, total_row_idx):
    if row.name == total_row_idx:
        return ['background-color: #ffe599; color: #cf1c00'] * len(row)
    return [''] * len(row)

def extract_device_string(s, chon_thiet_bi):
    if not isinstance(s, str):
        return ""
    # Tìm vị trí bắt đầu của tên thiết bị
    start = s.find(chon_thiet_bi)
    if start == -1:
        return ""
    # Tìm dấu # gần nhất bên phải sau tên thiết bị
    end = s.find("#", start)
    if end == -1:
        return s[start:].strip()  # Nếu không có # thì lấy đến hết chuỗi
    return s[start:end].strip()

def lay_gia_tri_giua_x_y(x,y,s):
    if not isinstance(s, str):
        return "0"
    parts = s.split("|")
    if len(parts) >= y:
        return parts[x].strip()  # phần tử giữa | thứ 2 và thứ 3
    return "0"

def get_number_after_colon(col_series: pd.Series) -> pd.Series:
    return (
        col_series
        .astype(str)                           # bảo đảm kiểu chuỗi
        .str.extract(r':\s*([\d.]+)', expand=False)  # lấy phần số
        .astype(float)                         # ép kiểu số
    )



##################################### Main Section ###############################################
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
        <p style="color:green">THỐNG KÊ BÁO CÁO THIẾT BỊ HẰNG NGÀY</p>
        </div>
    </div>
    <div class="header-underline"></div>

 """, unsafe_allow_html=True)
html_code = f'<p class="demuc"><i>Nhân viên: {st.session_state.username}</i></p>'
st.html(html_code)
sheeti5 = st.secrets["sheet_name"]["input_5"]
data = load_data(sheeti5)
dict_khoa_lienhe = dict(zip(data["Khoa"], data["Liên hệ"]))
khoa = data["Khoa"].unique()
st.session_state.ds_thietbi = data["Tên thiết bị"].unique().tolist()
now_vn = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))  
md = date(2025, 1, 1)
sheeto5 = st.secrets["sheet_name"]["output_5"]
if "tab_index" not in st.session_state:
    st.session_state.tab_index = 0  # 0: tab1, 1: tab2
TABS = ["📊 Báo cáo thiết bị hằng ngày","📈 Thống kê toàn viện","🔎 Truy vấn báo cáo chi tiết"]    
if "tab_idx" not in st.session_state:
    st.session_state.tab_idx = 0  
tab_idx = st.radio(
    label="",
    options=range(len(TABS)),
    format_func=lambda i: TABS[i],
    index=st.session_state.tab_idx,
    horizontal=True,            # hiển thị ngang giống tabs
    key="tab_selector"
)
st.session_state.tab_idx = tab_idx

if tab_idx == 0:
    with st.form("Báo cáo thiết bị hằng ngày"):
        day = st.date_input(
            label="Ngày báo cáo",
            value=now_vn.date(),
            min_value=md,
            max_value=now_vn.date(), 
            format="DD/MM/YYYY",
        )
        khoa_tab1 = chon_khoa(khoa)
        chon_thiet_bi = st.selectbox(label="Chọn thiết bị",options=data["Tên thiết bị"].unique())
        submit_baocao = st.form_submit_button("OK")
        if submit_baocao:
            if not khoa_tab1:
                st.error("Vui lòng chọn ít nhất một khoa")
            else:
                sheeti5 = st.secrets["sheet_name"]["output_5"]
                data_output5 = load_data(sheeti5)
                data_output5["Ngày báo cáo"] = pd.to_datetime(data_output5["Ngày báo cáo"], errors="coerce").dt.date
                filtered = data_output5.loc[data_output5["Ngày báo cáo"] == day]
                filtered = filtered.loc[filtered.groupby(['Khoa báo cáo', 'Ngày báo cáo'])['Timestamp'].idxmax()]
                if khoa_tab1 != "Chọn tất cả khoa":
                    filtered = filtered.loc[filtered["Khoa báo cáo"].isin(khoa_tab1)]
                if data_output5.empty:
                    st.warning("Không có dữ liệu theo yêu cầu")
                else:
                    filtered["Chuỗi thiết bị"] = filtered["Thiết bị thông thường"].apply(lambda x: extract_device_string(x, chon_thiet_bi))
                    filtered["Timestamp"] = pd.to_datetime(filtered["Timestamp"], errors="coerce")
                    filtered_sorted = filtered.sort_values(["Khoa báo cáo", "Timestamp"], ascending=[True, False])
                    filtered_unique = filtered_sorted.drop_duplicates(subset=["Khoa báo cáo"], keep="first").reset_index(drop=True)
                    st.divider()
                    ds_khoa_da_bao_cao = filtered_unique["Khoa báo cáo"].tolist()
                    ds_khoa_chua_bao_cao = list(set(khoa) - set(ds_khoa_da_bao_cao))

                    # Hiển thị tổng quan
                    col1, col2 = st.columns(2)
                    col1.metric("#### Số khoa chưa báo cáo", len(ds_khoa_chua_bao_cao))
                    col2.metric("#### Số khoa đã báo cáo", len(ds_khoa_da_bao_cao))
                    st.divider()
                    # Hiển thị danh sách khoa chưa báo cáo
                    st.markdown("#### ❌ Danh sách khoa chưa báo cáo")
                    for k in sorted(ds_khoa_chua_bao_cao):
                        st.markdown(f"- {k}")
                    # Hiển thị danh sách khoa đã báo cáo
                    st.markdown("#### ✅ Danh sách khoa đã báo cáo")
                    for k in sorted(ds_khoa_da_bao_cao):
                        st.markdown(f"- {k}")
                    st.divider()
                    day1 = day.strftime("%d/%m/%Y")
                    st.markdown(f"#### Thống kê số {chon_thiet_bi} trống trong ngày {day1}")
                    filtered_unique["Số lượng trống"] = filtered_unique["Chuỗi thiết bị"].apply(lambda x: lay_gia_tri_giua_x_y(3,4,x))
                    filtered_unique = filtered_unique[filtered_unique["Số lượng trống"].astype(float) > 0]
                    if filtered_unique.empty:
                        st.warning(f"Không có khoa nào hiện có trống {chon_thiet_bi} trong ngày báo cáo này")
                    else:
                        filtered_unique = filtered_unique[["Khoa báo cáo", "Số lượng trống"]]
                        filtered_unique = filtered_unique.rename(columns={
                            "Khoa báo cáo": "Khoa",
                            "Số lượng trống": "Số lượng trống"
                                })
                        filtered_unique["Số lượng trống"] = pd.to_numeric(filtered_unique["Số lượng trống"], errors="coerce").fillna(0)
                        filtered_unique["Liên hệ"] = filtered_unique["Khoa"].map(dict_khoa_lienhe)
                        SLT = filtered_unique["Số lượng trống"].sum()
                        st.write(f"**Tổng số {chon_thiet_bi} trống:** {SLT}")
                        st.dataframe(filtered_unique, use_container_width=True, hide_index=True)
elif tab_idx == 1:
    with st.form("Thời gian"):
        cold = st.columns([5,5])
        with cold[0]:
            sd = st.date_input(
            label="Ngày bắt đầu",
            value=now_vn.date(),
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
                sheeti5 = st.secrets["sheet_name"]["input_5"]
                data_input5 = load_data(sheeti5)
                headers = data_input5["Tên thiết bị"].unique()
                data_output5 = load_data1(sheeto5, sd, ed, khoa_select)
                data_output5 = data_output5.loc[data_output5.groupby(['Khoa báo cáo', 'Ngày báo cáo'])['Timestamp'].idxmax()]
                data_output5["Thiết bị thông thường"] = data_output5["Thiết bị thông thường"].fillna("").astype(str)
                data_tong_hop = tinh_tong_dang_su_dung(data_output5, headers)
                if data_output5.empty:
                    st.warning("Không có dữ liệu theo yêu cầu")
                else:
                    st.markdown("<h5 style='text-align: center;'>Số lượng sử dụng các thiết bị toàn viện</h5>", unsafe_allow_html=True)
                    data_tong_hop["Ngày báo cáo"] = data_tong_hop["Ngày báo cáo"].apply(
                            lambda x: pd.to_datetime(x) if isinstance(x, str) and x.lower() != "trung bình" else x
                        )

                formatted_df = format_per_row(data_tong_hop.copy())
                formatted_df = format_date_column(formatted_df, "Ngày báo cáo")

                # Hiển thị bảng đã định dạng + highlight
                styled_df = (
                    formatted_df
                    .style
                    .apply(highlight_last_row_factory(data_tong_hop), axis=1)
                )

                st.dataframe(styled_df, use_container_width=True, hide_index=True)
                # Tính Hiệu suất sử dụng (%)
                st.markdown("<h5 style='text-align: center;'>Hiệu suất sử dụng các thiết bị toàn viện (%)</h5>", unsafe_allow_html=True)
                phan_tram_df = tinh_phan_tram_su_dung(data_output5, headers)
                for header in headers:
                        phan_tram_df[header] = phan_tram_df[header].apply(
                            lambda x: f"{round(float(x),2)}" if pd.notna(x) and x != "" else ""
                        )
                st.dataframe(phan_tram_df.style.apply( lambda row: highlight_total_row_generic(row, len(phan_tram_df) - 1), axis=1), use_container_width=True, hide_index=True)
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
                #Thống kê số thiết bị cho mượn và mượn của toàn viện
                st.markdown("<h5 style='text-align: center;'>Thống kê số lượng thiết bị đang sử dụng toàn viện</h5>", unsafe_allow_html=True)
                rows = []
                for big_str in data_output5["Thiết bị thông thường"]:
                    # Mỗi thiết bị ngăn cách bởi kí hiệu #
                    for device_str in filter(None, big_str.strip("#").split("#")):
                        rows.append({
                            "Thiết bị"   : device_str.split("|")[0] if "|" in device_str else "",
                            "Tổng cơ số" : lay_gia_tri_giua_x_y(1, 2, device_str),
                            "Số lượng đang sử dụng" : lay_gia_tri_giua_x_y(2, 3, device_str), 
                            "Số lượng trống" : lay_gia_tri_giua_x_y(3, 4, device_str),
                            "Số lượng hư" : lay_gia_tri_giua_x_y(4, 5, device_str)
                        })                
                ket_qua = pd.DataFrame(rows, columns=["Thiết bị", "Tổng cơ số", "Số lượng đang sử dụng", "Số lượng trống", "Số lượng hư"])
                cols_num = ["Tổng cơ số", "Số lượng đang sử dụng", "Số lượng trống","Số lượng hư"]
                ket_qua[cols_num] = ket_qua[cols_num].apply(
                    pd.to_numeric, errors="coerce"
                ).fillna(0)
                ket_qua_grouped = (
                    ket_qua
                    .groupby("Thiết bị", as_index=False,sort=False)[cols_num]
                    .sum()
                )
                tong_values = ket_qua_grouped[cols_num].sum()
                row_total = pd.DataFrame({
                    "Thiết bị": ["Tổng"],         
                    **tong_values.to_dict()     
                })
                ket_qua_grouped = pd.concat(
                    [ket_qua_grouped, row_total],
                    ignore_index=True
                )
                st.dataframe(ket_qua_grouped.style.apply(
                    lambda row: highlight_total_row_generic(row, len(ket_qua_grouped) - 1), axis=1
                    ), use_container_width=True, hide_index=True,height=422)
                # 12 dòng x 35px (chiều cao 1 dòng) + 2px (chiều cao lề bảng) = 422px là ra chiều cao của bảng#
else:  # Tab 3
    with st.form("Thời gian"):
        cold = st.columns([5,5])
        with cold[0]:
            sd = st.date_input(
                label="Ngày bắt đầu",
                value=now_vn.date(),
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
        
        # Lấy danh sách thiết bị từ sheeti5
        sheeti5 = st.secrets["sheet_name"]["input_5"]
        data_input5 = load_data(sheeti5)
        list_thiet_bi = data_input5["Tên thiết bị"].unique()
        
        # Trường chọn thiết bị
        chon_thiet_bi = st.selectbox(
            label="Chọn thiết bị",
            options=list_thiet_bi
        )
        
        submit_thoigian = st.form_submit_button("OK")
        
        if submit_thoigian:
            if ed < sd:
                st.error("Lỗi ngày kết thúc đến trước ngày bắt đầu. Vui lòng chọn lại")  
            else:      
                # Tải dữ liệu từ sheeto5
                data_output5 = load_data1(sheeto5, sd, ed, khoa_select)
                
                if data_output5.empty:
                    st.warning("Không có dữ liệu theo yêu cầu")
                else:
                    # Lọc để chỉ lấy báo cáo cuối cùng của mỗi khoa trong từng ngày
                    data_output5['Timestamp'] = pd.to_datetime(data_output5['Timestamp'])
                    data_output5['Ngày báo cáo'] = data_output5['Timestamp'].dt.date
                    
                    # Lấy chỉ số của timestamp cuối cùng cho mỗi khoa trong mỗi ngày
                    data_filtered = data_output5.loc[
                        data_output5.groupby(['Khoa báo cáo', 'Ngày báo cáo'])['Timestamp'].idxmax()
                    ].reset_index(drop=True)
                    
                    # Tạo danh sách để chứa các dòng dữ liệu
                    rows_list = []
                    
                    # Duyệt qua từng dòng trong data_filtered
                    for index, row in data_filtered.iterrows():
                        # Lấy thông tin cơ bản
                        timestamp = row['Timestamp']
                        khoa_bao_cao = row['Khoa báo cáo']
                        nguoi_bao_cao = row['Người báo cáo']
                        thiet_bi_thong_thuong = row['Thiết bị thông thường']
                        
                        # Xử lý cột "Thiết bị thông thường" để lấy thông tin thiết bị đã chọn
                        co_so = ""
                        dang_dung = ""
                        trong = ""
                        hu = ""
                        
                        if pd.notna(thiet_bi_thong_thuong) and isinstance(thiet_bi_thong_thuong, str):
                            # Tìm vị trí của thiết bị đã chọn trong chuỗi
                            device_start = thiet_bi_thong_thuong.find(chon_thiet_bi)
                            if device_start != -1:
                                # Lấy từ tên thiết bị đến cuối chuỗi hoặc dấu # tiếp theo
                                device_part = thiet_bi_thong_thuong[device_start:]
                                
                                # Tìm dấu # để kết thúc phần thiết bị (nếu có thiết bị khác phía sau)
                                hash_pos = device_part.find("#")
                                if hash_pos != -1:
                                    device_part = device_part[:hash_pos]
                                
                                # Tách theo dấu "|"
                                device_components = device_part.split("|")
                                if len(device_components) >= 5:
                                    co_so = device_components[1].strip()         # Cơ số
                                    dang_dung = device_components[2].strip()     # Đang dùng
                                    trong = device_components[3].strip()         # Trống
                                    hu = device_components[4].strip()            # Hư
                                elif len(device_components) >= 2:
                                    # Nếu không đủ thông tin, lấy những gì có thể
                                    if len(device_components) > 1:
                                        co_so = device_components[1].strip()
                                    if len(device_components) > 2:
                                        dang_dung = device_components[2].strip()
                                    if len(device_components) > 3:
                                        trong = device_components[3].strip()
                                    if len(device_components) > 4:
                                        hu = device_components[4].strip()
                        
                        # Tạo dictionary cơ bản cho dòng dữ liệu
                        row_data = {
                            'Timestamp': timestamp,
                            'Khoa báo cáo': khoa_bao_cao,
                            'Người báo cáo': nguoi_bao_cao,
                            'Cơ số': co_so,
                            'Đang dùng': dang_dung,
                            'Trống': trong,
                            'Hư': hu
                        }
                        
                        # Nếu là Máy SCD, thêm 2 cột đặc biệt với format xuống dòng
                        if chon_thiet_bi == "Máy SCD":
                            scd_muon_tu_khoa_khac = row['SCD mượn từ khoa khác']
                            scd_cho_khoa_khac_muon = row['SCD cho khoa khác mượn']
                            
                            # Format xuống dòng cho SCD mượn từ khoa khác
                            if pd.notna(scd_muon_tu_khoa_khac) and scd_muon_tu_khoa_khac:
                                scd_muon_formatted = scd_muon_tu_khoa_khac.replace('+', '\n')
                            else:
                                scd_muon_formatted = ""
                            
                            # Format xuống dòng cho SCD cho khoa khác mượn  
                            if pd.notna(scd_cho_khoa_khac_muon) and scd_cho_khoa_khac_muon:
                                scd_cho_formatted = scd_cho_khoa_khac_muon.replace('+', '\n')
                            else:
                                scd_cho_formatted = ""
                                
                            row_data['SCD mượn từ khoa khác'] = scd_muon_formatted
                            row_data['SCD cho khoa khác mượn'] = scd_cho_formatted
                        
                        # Chỉ thêm dòng nếu có thông tin thiết bị (có ít nhất 1 trong 4 giá trị số)
                        if any([co_so, dang_dung, trong, hu]):
                            rows_list.append(row_data)
                    
                    # Tạo DataFrame từ danh sách
                    result_df = pd.DataFrame(rows_list)
                    
                    if result_df.empty:
                        st.warning(f"Không có dữ liệu về {chon_thiet_bi} trong khoảng thời gian đã chọn")
                    else:
                        # Chuyển đổi các cột số về kiểu số để tính tổng
                        numeric_cols = ['Cơ số', 'Đang dùng', 'Trống', 'Hư']
                        for col in numeric_cols:
                            result_df[col] = pd.to_numeric(result_df[col], errors='coerce').fillna(0)
                        
                        # Tạo dictionary cho dòng tổng
                        total_row = {
                            'Timestamp': 'Tổng',
                            'Khoa báo cáo': '',
                            'Người báo cáo': '',
                            'Cơ số': result_df['Cơ số'].sum(),
                            'Đang dùng': result_df['Đang dùng'].sum(),
                            'Trống': result_df['Trống'].sum(),
                            'Hư': result_df['Hư'].sum()
                        }
                        
                        # Nếu là Máy SCD, thêm cột trống cho dòng tổng
                        if chon_thiet_bi == "Máy SCD":
                            total_row['SCD mượn từ khoa khác'] = ''
                            total_row['SCD cho khoa khác mượn'] = ''
                        
                        # Thêm dòng tổng vào DataFrame
                        result_df = pd.concat([result_df, pd.DataFrame([total_row])], ignore_index=True)
                        
                        # Định dạng lại cột Timestamp (trừ dòng tổng)
                        for i in range(len(result_df) - 1):  # Bỏ qua dòng cuối (dòng tổng)
                            if pd.notna(result_df.iloc[i]['Timestamp']) and result_df.iloc[i]['Timestamp'] != 'Tổng':
                                result_df.iloc[i, result_df.columns.get_loc('Timestamp')] = pd.to_datetime(result_df.iloc[i]['Timestamp']).strftime('%d/%m/%Y %H:%M:%S')
                        
                        # Hiển thị tiêu đề động theo thiết bị đã chọn
                        st.markdown(f"<h5 style='text-align: center;'>Truy vấn báo cáo <span style='color: brown;'>{chon_thiet_bi}</h5>", unsafe_allow_html=True)
                        
                        # Hiển thị thông tin tổng quan
                        col1, col2, col3, col4, col5 = st.columns(5)
                        
                        # Lấy dữ liệu từ dòng tổng (dòng cuối)
                        total_data = result_df.iloc[-1]
                        data_without_total = result_df[result_df['Timestamp'] != 'Tổng']
                        
                        with col1:
                            unique_khoa = data_without_total['Khoa báo cáo'].nunique()
                            st.metric("Số khoa báo cáo", unique_khoa)
                        with col2:
                            st.metric("Tổng cơ số", int(total_data['Cơ số']))
                        with col3:
                            st.metric("Tổng đang dùng", int(total_data['Đang dùng']))
                        with col4:
                            st.metric("Tổng máy trống", int(total_data['Trống']))
                        with col5:
                            st.metric("Tổng máy hư", int(total_data['Hư']))
                        
                        st.divider()
                        
                        # Hiển thị bảng kết quả với highlight dòng tổng
                        def highlight_total_row(row):
                            if row['Timestamp'] == 'Tổng':
                                return ['background-color: #ffe599; color: #cf1c00; font-weight: bold'] * len(row)
                            return [''] * len(row)
                        
                        styled_df = result_df.style.apply(highlight_total_row, axis=1)
                        
                        # Tạo column_config động
                        column_config = {
                            'Timestamp': st.column_config.TextColumn('Thời gian báo cáo'),
                            'Khoa báo cáo': st.column_config.TextColumn('Khoa báo cáo'),
                            'Người báo cáo': st.column_config.TextColumn('Người báo cáo'),
                            'Cơ số': st.column_config.NumberColumn('Cơ số', format="%.0f"),
                            'Đang dùng': st.column_config.NumberColumn('Đang dùng', format="%.0f"),
                            'Trống': st.column_config.NumberColumn('Trống', format="%.0f"),
                            'Hư': st.column_config.NumberColumn('Hư', format="%.0f")
                        }
                        
                        # Nếu là Máy SCD, thêm config cho 2 cột đặc biệt
                        if chon_thiet_bi == "Máy SCD":
                            column_config['SCD mượn từ khoa khác'] = st.column_config.TextColumn('SCD mượn từ khoa khác')
                            column_config['SCD cho khoa khác mượn'] = st.column_config.TextColumn('SCD cho khoa khác mượn')
                        
                        st.dataframe(
                            styled_df,
                            use_container_width=True,
                            hide_index=True,
                            column_config=column_config
                        )