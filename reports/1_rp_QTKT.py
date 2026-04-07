import streamlit as st
import pandas as pd
import gspread
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
import pathlib
import base64
from google.oauth2.service_account import Credentials
import numpy as np

# ======================== UTILS ========================

@st.cache_data(ttl=3600)
def get_img_as_base64(file):
    with open(file, "rb") as f:
        return base64.b64encode(f.read()).decode()

def load_css(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
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

def _doc_sheet(ten_sheet):
    """Đọc raw DataFrame từ Google Sheet — dùng nội bộ bởi load_data1 và load_data."""
    gc = gspread.authorize(load_credentials())
    raw = gc.open(ten_sheet).sheet1.get_all_values()
    return pd.DataFrame(raw[1:], columns=raw[0])

@st.cache_data(ttl=10)
def get_key_from_value(dictionary, value):
    return next((k for k, v in dictionary.items() if v == value), None)

@st.cache_data(ttl=10)
def load_data1(x):
    return _doc_sheet(x)

@st.cache_data(ttl=10)
def load_data(x, sd, ed, khoa_select):
    data = _doc_sheet(x)

    # Xác định danh sách khoa cần lọc
    u = st.secrets["user_special"]
    special_map = {
        u["u1"]: [u["u1_khoa1"], u["u1_khoa2"], u["u1_khoa3"]],
        u["u2"]: [u["u2_khoa1"], u["u2_khoa2"]],
        u["u3"]: [u["u3_khoa1"], u["u3_khoa2"]],
    }
    username = st.session_state.username
    if khoa_select == "Chọn tất cả khoa":
        if username in special_map:
            khoa_select = special_map[username]
        elif st.session_state.phan_quyen in ["1", "2", "3"]:
            khoa_select = data["Khoa"]

    data = data.loc[data["Khoa"].isin(khoa_select)]
    data["Timestamp"] = pd.to_datetime(data["Timestamp"], errors="coerce")
    data_final = data[
        (data["Timestamp"] >= pd.Timestamp(sd)) &
        (data["Timestamp"] < pd.Timestamp(ed + timedelta(days=1)))
    ]
    return data_final

# ======================== THỐNG KÊ ========================

def _to_numeric_col(df, col):
    """Chuyển cột sang numeric, xử lý dấu phẩy thập phân."""
    return pd.to_numeric(df[col].astype(str).str.replace(",", "."), errors="coerce")

def tao_thong_ke(x, y):
    df = pd.DataFrame(x)
    bo_cot = df[["STT", "Timestamp", "Khoa", "Tên quy trình",
                 "Tỉ lệ tuân thủ", "Tỉ lệ an toàn", "Tỉ lệ nhận dạng NB",
                 "Tên người đánh giá", "Tên người thực hiện",
                 "Ghi chú 1", "Ghi chú 2"]].copy()

    for col in ["Tỉ lệ tuân thủ", "Tỉ lệ an toàn", "Tỉ lệ nhận dạng NB"]:
        bo_cot[col] = _to_numeric_col(bo_cot, col)

    bo_cot["Tỉ lệ tuân thủ"] = (bo_cot["Tỉ lệ tuân thủ"] * 100).round(1)
    bo_cot["Tỉ lệ an toàn"] = bo_cot["Tỉ lệ an toàn"].round(4)
    bo_cot["Tỉ lệ nhận dạng NB"] = bo_cot["Tỉ lệ nhận dạng NB"].round(4)

    if y == "Chi tiết":
        for col in ["Tỉ lệ an toàn", "Tỉ lệ nhận dạng NB"]:
            bo_cot[col] = bo_cot[col].apply(lambda v: v * 100 if pd.notna(v) else np.nan)
        return bo_cot

    # ── Tổng quát ──────────────────────────────────────────────────────────────
    bo_cot = bo_cot.drop(
        ["Timestamp", "Tên người đánh giá", "Tên người thực hiện",
         "Ghi chú 1", "Ghi chú 2"], axis=1
    )

    # Tạo mask theo trạng thái NaN của 2 cột tỉ lệ
    has_at  = bo_cot["Tỉ lệ an toàn"].notna()
    has_nd  = bo_cot["Tỉ lệ nhận dạng NB"].notna()

    # Với mỗi nhóm (AT có số / không, ND có số / không) → dùng agg tương ứng
    def _group(mask, agg_at, agg_nd):
        subset = bo_cot.loc[mask]
        if subset.empty:
            return pd.DataFrame()
        return (subset.groupby(["Khoa", "Tên quy trình"])
                      .agg({"Tên quy trình": "count",
                            "Tỉ lệ tuân thủ": "mean",
                            "Tỉ lệ an toàn": agg_at,
                            "Tỉ lệ nhận dạng NB": agg_nd})
                      .rename(columns={"Tên quy trình": "Số lượt"})
                      .reset_index())

    ket_qua1 = _group( has_at &  has_nd, "mean",  "mean")
    ket_qua2 = _group(~has_at & ~has_nd, "first", "first")
    ket_qua3 = _group( has_at & ~has_nd, "mean",  "first")
    ket_qua4 = _group(~has_at &  has_nd, "first", "mean")

    # Tính tổng trước khi gộp (dùng cho dòng summary)
    def _sum_count(mask, col):
        s = bo_cot.loc[mask, col]
        return s.sum(), s.count()

    sum_at1, cnt_at1 = _sum_count( has_at &  has_nd, "Tỉ lệ an toàn")
    sum_at2, cnt_at2 = _sum_count( has_at & ~has_nd, "Tỉ lệ an toàn")
    sum_nd1, cnt_nd1 = _sum_count( has_at &  has_nd, "Tỉ lệ nhận dạng NB")
    sum_nd2, cnt_nd2 = _sum_count(~has_at &  has_nd, "Tỉ lệ nhận dạng NB")

    ket_qua = (pd.concat([ket_qua1, ket_qua2, ket_qua3, ket_qua4], ignore_index=True)
                 .sort_values(["Khoa", "Tên quy trình"]))

    for col in ["Tỉ lệ an toàn", "Tỉ lệ nhận dạng NB"]:
        ket_qua[col] = ket_qua[col].apply(lambda v: v * 100 if pd.notna(v) else np.nan)

    ket_qua.insert(0, "STT", range(1, len(ket_qua) + 1))

    # Dòng tổng kết
    cnt_at = cnt_at1 + cnt_at2
    cnt_nd = cnt_nd1 + cnt_nd2
    row_mean = pd.DataFrame({
        "STT": [""],
        "Khoa": ["Tổng"],
        "Tên quy trình": [f"{ket_qua['Tên quy trình'].nunique()} quy trình"],
        "Số lượt": [ket_qua["Số lượt"].sum()],
        "Tỉ lệ tuân thủ": [ket_qua["Tỉ lệ tuân thủ"].mean()],
        "Tỉ lệ an toàn": [(sum_at1 + sum_at2) / cnt_at * 100 if cnt_at > 0 else np.nan],
        "Tỉ lệ nhận dạng NB": [(sum_nd1 + sum_nd2) / cnt_nd * 100 if cnt_nd > 0 else np.nan],
    })
    ket_qua = pd.concat([ket_qua, row_mean[[c for c in ket_qua.columns if c in row_mean.columns]]],
                        ignore_index=True)
    return ket_qua

def highlight_total_row(row):
    if any(isinstance(v, str) and v == "Tổng" for v in row):
        return ["background-color: #ffe599; color: #cf1c00; font-weight: bold"] * len(row)
    return [""] * len(row)

# Ánh xạ kết quả sang số
_KET_QUA_MAP = {
    "Thực hiện đúng, đủ":                          3,
    "Thực hiện đúng nhưng chưa đủ":                2,
    "Thực hiện chưa đúng, KHÔNG thực hiện":        1,
    "KHÔNG ÁP DỤNG":                               0,
}

def mau_sac_diem_cac_buoc(val):
    """Tô màu giá trị kết quả: 1,2 = đỏ; 0 = xanh dương; 3 = bình thường"""
    if val == 0:
        return 'color: #0066cc; background-color: #e3f7fc'  # Xanh dương
    elif val in (1, 2):
        return 'color: #cc0000; background-color: #f7ded7'  # Đỏ
    return ''

def tach_chuoi_data(data_str):
    """
    Tách chuỗi Data thành:
      - dict {buoc: so} (B01→3/2/1/0)
      - dict {buoc: ton_dong} chỉ những bước có tồn đọng
    Cấu trúc: B01|kết quả|tồn đọng#B02|...
    """
    scores, ton_dong_dict = {}, {}
    if not isinstance(data_str, str) or not data_str.strip():
        return scores, ton_dong_dict
    for segment in data_str.split("#"):
        parts = segment.split("|")
        if len(parts) < 2:
            continue
        buoc   = parts[0].strip()           # "B01"
        ketqua = parts[1].strip()           # tên kết quả
        tondong = parts[2].strip() if len(parts) > 2 else ""
        scores[buoc] = _KET_QUA_MAP.get(ketqua, None)
        if tondong:
            ton_dong_dict[buoc] = tondong
    return scores, ton_dong_dict

def tao_thong_ke_chitiet2(data):
    """
    Trả về DataFrame với các cột:
      STT | Timestamp | Khoa | Tên người thực hiện | Tên người đánh giá |
      B01 | B02 | ... | Tồn đọng
    Giá trị cột Bxx là số nguyên (0-3), None nếu bước không tồn tại trong lượt đó.
    """
    rows = []
    all_buoc = []   # thu thập tất cả mã bước để tạo cột động

    parsed_cache = []
    for _, row in data.iterrows():
        scores, ton_dong = tach_chuoi_data(row.get("Data", ""))
        parsed_cache.append((row, scores, ton_dong))
        for b in scores:
            if b not in all_buoc:
                all_buoc.append(b)

    # Sắp xếp bước theo thứ tự số: B01 < B02 < ... < B10 < B11
    all_buoc.sort(key=lambda b: int(b[1:]) if b[1:].isdigit() else 999)

    for idx, (row, scores, ton_dong) in enumerate(parsed_cache, start=1):
        record = {
            "STT":                   idx,
            "Timestamp":             row.get("Timestamp", ""),
            "Khoa":                  row.get("Khoa", ""),
            "Tên người thực hiện":   row.get("Tên người thực hiện", ""),
            "Tên người đánh giá":    row.get("Tên người đánh giá", ""),
            "Tên quy trình":    row.get("Tên quy trình", ""),
        }
        for b in all_buoc:
            record[b] = scores.get(b, None)
        # Cột Tồn đọng: "B01: nội dung; B03: nội dung"
        record["Tồn đọng"] = "; ".join(f"{b}: {v}" for b, v in ton_dong.items()) if ton_dong else ""
        rows.append(record)

    return pd.DataFrame(rows), all_buoc


# ======================== UI HELPERS ========================

def chon_khoa(khoa):
    placeholder1 = st.empty()
    if st.session_state.phan_quyen in ["1","2","3"]:
        if st.checkbox("Chọn tất cả khoa"):
            placeholder1.empty()
            khoa_select = "Chọn tất cả khoa"
        else:
            with placeholder1:
                khoa_select = st.multiselect(label="Chọn khoa",
                                                  options= khoa.unique())
        return khoa_select
    else:
        if st.session_state.username == st.secrets["user_special"]["u1"]:
            if st.checkbox("Cả 3 khoa"):
                placeholder1.empty()
                khoa_select = "Chọn tất cả khoa"
            else:
                with placeholder1:
                    khoa_select = st.multiselect(label="Chọn khoa",
                                         options= [
                            st.secrets["user_special"]["u1_khoa1"],
                            st.secrets["user_special"]["u1_khoa2"],
                            st.secrets["user_special"]["u1_khoa3"],])
            return khoa_select
        elif st.session_state.username == st.secrets["user_special"]["u2"]:
            if st.checkbox("Cả 2 khoa"):
                placeholder1.empty()
                khoa_select = "Chọn tất cả khoa"
            else:
                with placeholder1:
                    khoa_select = st.multiselect(label="Chọn khoa",
                                         options= [
                            st.secrets["user_special"]["u2_khoa1"],
                            st.secrets["user_special"]["u2_khoa2"],])
            return khoa_select
        elif st.session_state.username == st.secrets["user_special"]["u3"]:
            if st.checkbox("Cả 2 khoa"):
                placeholder1.empty()
                khoa_select = "Chọn tất cả khoa"
            else:
                with placeholder1:
                    khoa_select = st.multiselect(label="Chọn khoa",
                                         options= [
                            st.secrets["user_special"]["u3_khoa1"],
                            st.secrets["user_special"]["u3_khoa2"]])
            return khoa_select
        else:
            khoa_select = st.session_state.khoa
            khoa_select = [khoa_select]
            return khoa_select
    return st.multiselect(label="Chọn khoa", options=options, default=None)

def tinh_metrics(data):
    data_temp = data.copy()
    for col in ["Tỉ lệ tuân thủ", "Tỉ lệ an toàn", "Tỉ lệ nhận dạng NB"]:
        data_temp[col] = _to_numeric_col(data_temp, col)

    grouped_tuan_thu = data_temp.groupby(["Khoa", "Tên quy trình"])["Tỉ lệ tuân thủ"].mean()
    tl_tuan_thu = (grouped_tuan_thu.mean() * 100).round(2)

    def _mean_pct(col):
        vals = data_temp[col].dropna()
        return (vals.sum() / len(vals) * 100).round(2) if len(vals) > 0 else None

    dieu_duong_set = set()
    for col in ["Tên người thực hiện", "Ghi chú 1", "Ghi chú 2"]:
        if col in data.columns:
            valid = data[col].dropna()
            valid = valid[valid.astype(str).str.strip() != ""]
            dieu_duong_set.update(valid.unique())
    dieu_duong_set.discard("")
    dieu_duong_set.discard(None)

    return {
        "luot_giam_sat": len(data),
        "so_khoa":        data["Khoa"].nunique(),
        "so_dieu_duong":  len(dieu_duong_set),
        "so_qtkt":        data["Tên quy trình"].nunique(),
        "tl_tuan_thu":    tl_tuan_thu,
        "tl_an_toan":     _mean_pct("Tỉ lệ an toàn"),
        "tl_nhan_dang":   _mean_pct("Tỉ lệ nhận dạng NB"),
    }

def _hien_thi_metric(label, value):
    """Hiển thị st.metric cho tỉ lệ phần trăm, tự chọn format *.0f hay *.2f."""
    if value is None:
        st.metric(f"**:red[{label}]**", "-", border=True)
    elif value == 100:
        st.metric(f"**:red[{label}]**", f"{value:.0f}%", border=True)
    else:
        st.metric(f"**:red[{label}]**", f"{value:.2f}%", border=True)

# ======================== MAIN ========================

css_path = pathlib.Path("asset/style.css")
load_css(css_path)
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
        <div class="header-subtext">
            <p style="color:green">THỐNG KÊ GIÁM SÁT QUY TRÌNH</p>
        </div>
    </div>
    <div class="header-underline"></div>
""", unsafe_allow_html=True)

st.html(f'<p class="demuc"><i>Nhân viên: {st.session_state.username}</i></p>')

data = load_data1(st.secrets["sheet_name"]["input_1"])
khoa = data["Khoa"]

loai_qtkt = {
    "All":  "Tất cả",
    "QTCB": "Quy trình kỹ thuật cơ bản",
    "QTCK": "Quy trình kỹ thuật chuyên khoa",
    "QTHC": "Quy trình hành chính chuyên môn",
}

now_vn = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
md = date(2025, 1, 1)

with st.form("Thời gian"):
    cold = st.columns([5, 5])
    with cold[0]:
        sd = st.date_input("Ngày bắt đầu", value=now_vn.date(),
                           min_value=md, max_value=now_vn.date(), format="DD/MM/YYYY")
    with cold[1]:
        ed = st.date_input("Ngày kết thúc", value=now_vn.date(),
                           min_value=md, max_value=now_vn.date(), format="DD/MM/YYYY")
    chon_loai_qtkt = st.radio(label="Loại quy trình",
                              options=list(loai_qtkt.values()), index=0)
    khoa_select = chon_khoa(khoa)
    submit_thoigian = st.form_submit_button("OK")

if submit_thoigian:
    if ed < sd:
        st.error("Lỗi ngày kết thúc đến trước ngày bắt đầu. Vui lòng chọn lại")
    else:
        loc_loai_qt = get_key_from_value(loai_qtkt, chon_loai_qtkt)
        data = load_data(st.secrets["sheet_name"]["output_1"], sd, ed, khoa_select)

        if data.empty:
            st.toast("Không có dữ liệu theo yêu cầu")
        else:
            if loc_loai_qt != "All":
                data = data[data["Mã quy trình"] == loc_loai_qt]

            if data.empty:
                st.warning("Không có dữ liệu theo yêu cầu")
            else:
                metrics = tinh_metrics(data)

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("**:red[Lượt giám sát]**", f"{metrics['luot_giam_sat']:,}", border=True)
                with col2:
                    st.metric("**:red[Số khoa]**", metrics["so_khoa"], border=True)
                with col3:
                    st.metric("**:red[Số điều dưỡng]**", metrics["so_dieu_duong"], border=True)
                with col4:
                    st.metric("**:red[Số quy trình]**", metrics["so_qtkt"], border=True)

                col5, col6, col7, _ = st.columns(4)
                with col5:
                    _hien_thi_metric("Tỉ lệ tuân thủ QT" if metrics["tl_tuan_thu"] != 100
                                     else "Tỉ lệ tuân thủ QTKT", metrics["tl_tuan_thu"])
                with col6:
                    _hien_thi_metric("Tỉ lệ tuân thủ CSAT", metrics["tl_an_toan"])
                with col7:
                    _hien_thi_metric("Tỉ lệ tuân thủ NDNB", metrics["tl_nhan_dang"])

                col_cfg = {
                    "Số QTKT":              st.column_config.NumberColumn(format="%d"),
                    "Số lượt":              st.column_config.NumberColumn(format="%d"),
                    "Tỉ lệ tuân thủ":       st.column_config.NumberColumn(format="%.2f"),
                    "Tỉ lệ an toàn":        st.column_config.NumberColumn(format="%.2f"),
                    "Tỉ lệ nhận dạng NB":   st.column_config.NumberColumn(format="%.2f"),
                }

                with st.expander("**:blue[Thống kê cấp khoa/đơn vị]**"):
                    thongke = tao_thong_ke(data, "Tổng quát")
                    st.dataframe(
                        thongke.style.apply(highlight_total_row, axis=1),
                        hide_index=True,
                        use_container_width=True,
                        column_config=col_cfg,
                        column_order=list(thongke.columns),
                    )

                with st.expander("**:blue[Thống kê cấp cá nhân]**"):
                    thongkechitiet = tao_thong_ke(data, "Chi tiết")
                    st.dataframe(
                        thongkechitiet,
                        hide_index=True,
                        column_config={
                            "Tỉ lệ tuân thủ":     st.column_config.NumberColumn(format="%.2f %%"),
                            "Tỉ lệ an toàn":      st.column_config.NumberColumn(format="%.2f %%"),
                            "Tỉ lệ nhận dạng NB": st.column_config.NumberColumn(format="%.2f %%"),
                        },
                    )

                with st.expander("**:blue[Thống kê cấp bước quy trình]**"):
                    st.markdown("""
                        <p style="font-size:15px;text-align:left">
                            <b>Chú thích điểm quy đổi:</b><br>
                                <span style="margin-left:30px; color:#080707">Thực hiện đúng, đủ: 3 </span><br>
                                <span style="margin-left:30px;color:#cf0808">Thực hiện đúng nhưng chưa đủ: 2</span><br>
                                <span style="margin-left:30px; color:#cf0808">Thực hiện chưa đúng, KHÔNG thực hiện: 1</span><br>
                                <span style="margin-left:30px; color:#082dcf">KHÔNG ÁP DỤNG: 0</span>
                        </p>
                    """, unsafe_allow_html=True)

                    dataframe_chitiet2, all_buoc = tao_thong_ke_chitiet2(data)
                    dinh_dang_diem_ket_qua = {b: st.column_config.NumberColumn(format="%d") for b in all_buoc}
                    st.dataframe(
                        dataframe_chitiet2.style.map(mau_sac_diem_cac_buoc, subset=all_buoc),
                        hide_index=True,
                        column_config=dinh_dang_diem_ket_qua,
                    )

powerbi_url = (
    "https://app.powerbi.com/groups/fbea42ac-f40a-4ada-bdbe-95cd1dc34b62"
    "/reports/e4d93ac2-150f-4e45-9932-e93fc32666e8/ReportSection?experience=power-bi"
)
st.markdown(f"[📊 Xem báo cáo chi tiết tại Power BI]({powerbi_url})", unsafe_allow_html=True)