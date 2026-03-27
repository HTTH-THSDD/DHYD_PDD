import streamlit as st
import pandas as pd
import gspread
from datetime import datetime
from zoneinfo import ZoneInfo
import pathlib
import base64
from google.oauth2.service_account import Credentials

# ── Helpers UI ───────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def get_img_as_base64(file):
    with open(file, "rb") as f:
        return base64.b64encode(f.read()).decode()

def load_css(file_path):
    for enc in ("utf-8", "latin-1"):
        try:
            with open(file_path, "r", encoding=enc) as f:
                st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
            return
        except UnicodeDecodeError:
            continue

# ── Google Sheets ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_credentials():
    keys = ["type", "project_id", "private_key_id", "private_key", "client_email",
            "client_id", "auth_uri", "token_uri",
            "auth_provider_x509_cert_url", "client_x509_cert_url", "universe_domain"]
    creds_info = {k: st.secrets["google_service_account"][k] for k in keys}
    return Credentials.from_service_account_info(
        creds_info,
        scopes=["https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"],
    )

@st.cache_data(ttl=600)
def load_data(x):
    gc = gspread.authorize(load_credentials())
    data = gc.open(x).sheet1.get_all_values()
    return pd.DataFrame(data[1:], columns=data[0])

# ── Logic nghiệp vụ ───────────────────────────────────────────────────────────
MA_AN_THEO_NHOM = {
    "2": {"A04", "A05"},
    "3": {"A04", "A05", "A06"},
}

def kiem_tra_nhom_bao_cao(ma_thiet_bi, nhom_bao_cao):
    """True nếu thiết bị cần ẩn — chỉ áp dụng mã A, không áp dụng mã B."""
    return (
        ma_thiet_bi.startswith("A")
        and ma_thiet_bi in MA_AN_THEO_NHOM.get(str(nhom_bao_cao).strip(), set())
    )

def thong_tin_hanh_chinh():
    sheeti5 = st.secrets["sheet_name"]["input_5"]
    data_khoa = load_data(sheeti5)
    chon_khoa = st.selectbox("Khoa/Đơn vị báo cáo ",
                             options=data_khoa["Khoa"].unique(),
                             index=None, placeholder="")
    if chon_khoa:
        ckx = data_khoa.loc[data_khoa["Khoa"] == chon_khoa]
        st.session_state.khoa_VTTB    = chon_khoa
        st.session_state.thiet_bi     = ckx
        st.session_state.ten_thiet_bi = ckx["Tên thiết bị"].iloc[0]
        st.session_state.nhom_bao_cao = str(ckx["Nhóm báo cáo"].iloc[0]).strip()
    else:
        for k in ("khoa_VTTB", "nhom_bao_cao"):
            st.session_state.pop(k, None)

def kiem_tra_tong():
    thong_bao_loi = []
    nhom_bao_cao  = st.session_state.get("nhom_bao_cao", "1")
    tb = st.session_state.thiet_bi
    for i in range(len(tb)):
        ma  = tb["Mã thiết bị"].iloc[i]
        ten = tb["Tên thiết bị"].iloc[i]
        if kiem_tra_nhom_bao_cao(ma, nhom_bao_cao):
            continue
        for truong, nhan in [("dang_su_dung", "Đang dùng"),
                              ("trong", "Trống"), ("hu", "Hư")]:
            if st.session_state.get(f"{truong}_{i}") is None:
                thong_bao_loi.append(f"{ten} - số liệu {nhan} chưa được báo cáo")
    return thong_bao_loi

def kiem_tra_may_SCD():
    """Công thức: Đang dùng - Tổng mượn + Tổng cho mượn + Trống + Hư = Cơ số"""
    thong_bao_loi_SCD = []
    tb = st.session_state.thiet_bi
    for i in range(len(tb)):
        ma_thiet_bi = tb["Mã thiết bị"].iloc[i]
        if ma_thiet_bi[0] == "A":
            continue
        co_so        = st.session_state.get(f"co_so_{i}", 0)
        dang_su_dung = st.session_state.get(f"dang_su_dung_{i}", 0)
        trong        = st.session_state.get(f"trong_{i}", 0)
        hu           = st.session_state.get(f"hu_{i}", 0)
        tong_muon = sum(
            st.session_state.get(f"so_luong_muon_{idx}", 0) or 0
            for idx in st.session_state.get("them_cot_muon", [])
            if st.session_state.get(f"muon_tu_khoa_khac_{idx}") not in (None, "--Chọn khoa--")
        )
        tong_cho_muon = sum(
            st.session_state.get(f"so_luong_cho_muon_{idx}", 0) or 0
            for idx in st.session_state.get("them_cot_cho_muon", [])
            if st.session_state.get(f"cho_khoa_khac_muon{idx}") not in (None, "--Chọn khoa--")
        )
        ket_qua = dang_su_dung - tong_muon + tong_cho_muon + trong + hu
        if ket_qua != co_so:
            chenh_lech = ket_qua - co_so
            thong_bao_loi_SCD.append(
                f"Cơ số: {co_so}, Tổng tính: {ket_qua}, "
                f"Số liệu chênh lệch: {chenh_lech:+d} máy"
            )
    return thong_bao_loi_SCD

# ── Dialogs ───────────────────────────────────────────────────────────────────
@st.dialog("Thông báo")
def warning(danh_sach_loi):
    """Dùng cho lỗi nhập liệu (list) hoặc thông báo kết quả (int 1/2)."""
    if isinstance(danh_sach_loi, list):
        st.warning("Vui lòng điền đầy đủ thông tin thiết bị:\n\n"
                   + "\n".join(f"- {l}" for l in danh_sach_loi))
        st.info("💡 **Lưu ý:** Nếu số lượng là 0, vui lòng nhập số 0.")
    elif danh_sach_loi == 1:
        st.success("✅ Báo cáo đã được gửi thành công!")
    elif danh_sach_loi == 2:
        st.warning("⚠️ Bạn đã gửi kết quả này rồi!")

@st.dialog("Báo cáo máy SCD chưa chính xác")
def warning_SCD(danh_sach_loi_SCD):
    st.error("**Số liệu thiết bị SCD chưa chính xác:**\n\n"
             + "\n".join(f"- {l}" for l in danh_sach_loi_SCD))

# ── Upload ────────────────────────────────────────────────────────────────────
def check_duplicate_submission(column_ngay_bao_cao, column_khoa_bao_cao,
                                column_nguoi_bao_cao, column_tb_thong_thuong,
                                column_scd_bo_sung, column_scd_muon_tu_khoa_khac,
                                column_scd_cho_khoa_khac_muon):
    try:
        gc       = gspread.authorize(load_credentials())
        all_data = gc.open(st.secrets["sheet_name"]["output_5"]).sheet1.get_all_values()
        if len(all_data) <= 1:
            return False, None
        compare = [column_ngay_bao_cao, column_khoa_bao_cao, column_nguoi_bao_cao,
                   column_tb_thong_thuong, column_scd_bo_sung,
                   column_scd_muon_tu_khoa_khac, column_scd_cho_khoa_khac_muon]
        for row_idx, row in enumerate(all_data[1:], start=1):
            if len(row) < 9:
                continue
            if [row[j].strip() for j in range(2, 9)] == [v.strip() for v in compare]:
                return True, row_idx
        return False, None
    except Exception as e:
        st.error(f"❌ Lỗi kiểm tra trùng lặp: {e}")
        return False, None

def upload_data_VTTB():
    try:
        gc          = gspread.authorize(load_credentials())
        sheet       = gc.open(st.secrets["sheet_name"]["output_5"]).get_worksheet(0)
        all_values  = sheet.get_all_values()
        new_stt     = (int(all_values[-1][0]) + 1) if len(all_values) > 1 else 1

        now_vn               = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
        column_timestamp     = now_vn.strftime("%Y-%m-%d %H:%M:%S")
        column_ngay_bao_cao  = st.session_state.ngay_bao_cao.strftime("%Y-%m-%d")
        column_khoa_bao_cao  = str(st.session_state.khoa_VTTB)
        column_nguoi_bao_cao = str(st.session_state.username)
        nhom_bao_cao         = st.session_state.get("nhom_bao_cao", "1")
        tb                   = st.session_state.thiet_bi

        # Thiết bị thông thường
        column_tb_thong_thuong = ""
        for i in range(len(tb)):
            ten   = tb["Tên thiết bị"].iloc[i]
            ma    = tb["Mã thiết bị"].iloc[i]
            co_so = str(st.session_state.get(f"co_so_{i}", 0))
            if kiem_tra_nhom_bao_cao(ma, nhom_bao_cao):
                val = int(pd.to_numeric(tb["2025"].iloc[i], errors="coerce") or 0)
                dang_su_dung = trong = hu = str(val)
            else:
                dang_su_dung = str(st.session_state.get(f"dang_su_dung_{i}", 0))
                trong        = str(st.session_state.get(f"trong_{i}", 0))
                hu           = str(st.session_state.get(f"hu_{i}", 0))
            column_tb_thong_thuong += f"{ten}|{co_so}|{dang_su_dung}|{trong}|{hu}#"

        # SCD bổ sung
        last_i          = len(tb) - 1
        SCD_so_bn       = str(st.session_state.get(f"chua_thuc_hien_{last_i}", 0))
        SCD_nguyen_nhan = str(st.session_state.get(f"nguyen_nhan_{last_i}", ""))
        column_SCD_bo_sung = (f"{SCD_so_bn}|{SCD_nguyen_nhan}"
                              if SCD_so_bn != "0" and SCD_nguyen_nhan else "")

        # Mượn / cho mượn
        def _build_muon(lst_key, key_khoa, key_sl):
            parts = [
                f"{st.session_state[f'{key_khoa}{idx}']}:{st.session_state.get(f'{key_sl}{idx}', 0)}"
                for idx in st.session_state.get(lst_key, [])
                if st.session_state.get(f"{key_khoa}{idx}") not in (None, "--Chọn khoa--")
                and str(st.session_state.get(f"{key_sl}{idx}", 0)) != "0"
            ]
            return "+".join(parts)

        columnn_SCD_muon_khoa_khac    = _build_muon("them_cot_muon",
                                                     "muon_tu_khoa_khac_", "so_luong_muon_")
        columnn_SCD_cho_khoa_khac_muon = _build_muon("them_cot_cho_muon",
                                                      "cho_khoa_khac_muon", "so_luong_cho_muon_")

        # Kiểm tra trùng lặp
        is_duplicate, _ = check_duplicate_submission(
            column_ngay_bao_cao, column_khoa_bao_cao, column_nguoi_bao_cao,
            column_tb_thong_thuong, column_SCD_bo_sung,
            columnn_SCD_muon_khoa_khac, columnn_SCD_cho_khoa_khac_muon,
        )
        if is_duplicate:
            warning(2)
            return False

        next_row = len(all_values) + 1
        sheet.update(
            f"A{next_row}:I{next_row}",
            [[new_stt, column_timestamp, column_ngay_bao_cao, column_khoa_bao_cao,
              column_nguoi_bao_cao, column_tb_thong_thuong, column_SCD_bo_sung,
              columnn_SCD_muon_khoa_khac, columnn_SCD_cho_khoa_khac_muon]],
            value_input_option="USER_ENTERED",
        )
        st.cache_data.clear()
        return True

    except Exception as e:
        st.error(f"❌ Lỗi khi upload dữ liệu: {e}")
        import traceback; st.code(traceback.format_exc())
        return False

# ── Reset ─────────────────────────────────────────────────────────────────────
PROTECTED_KEYS = {"username", "ngay_bao_cao", "authenticated", "phan_quyen", "user_id"}

def clear_all_inputs():
    for k in [k for k in list(st.session_state.keys()) if k not in PROTECTED_KEYS]:
        st.session_state.pop(k, None)
    st.cache_data.clear()
    st.cache_resource.clear()
    st.session_state["force_refresh"] = True

def clear_session_state():
    tb = st.session_state.get("thiet_bi", pd.DataFrame())
    keys_to_clear = ["khoa_VTTB", "thiet_bi", "ten_thiet_bi", "nhom_bao_cao"]
    for i in range(len(tb)):
        keys_to_clear += [f"co_so_{i}", f"dang_su_dung_{i}", f"trong_{i}",
                          f"hu_{i}", f"chua_thuc_hien_{i}", f"nguyen_nhan_{i}"]
    for lst_key, key_khoa, key_sl in [
        ("them_cot_muon",     "muon_tu_khoa_khac_", "so_luong_muon_"),
        ("them_cot_cho_muon", "cho_khoa_khac_muon", "so_luong_cho_muon_"),
    ]:
        for idx in st.session_state.get(lst_key, []):
            keys_to_clear += [f"{key_khoa}{idx}", f"{key_sl}{idx}"]
        keys_to_clear.append(lst_key)
    for k in keys_to_clear:
        st.session_state.pop(k, None)

# ── Main Section ───────────────────────────────────────────────────────────────────
css_path = pathlib.Path("asset/style_4_VTTB.css")
load_css(css_path)
img = get_img_as_base64("pages/img/logo.png")
st.markdown(f"""
    <div class="fixed-header">
        <div class="header-content">
            <img src="data:image/png;base64,{img}" alt="logo">
            <div class="header-text">
                <h1>BỆNH VIỆN ĐẠI HỌC Y DƯỢC THÀNH PHỐ HỒ CHÍ MINH
                <span style="vertical-align:super;font-size:0.6em">&#174;</span><br>
                <span style="color:#c15088">Phòng Điều dưỡng</span></h1>
            </div>
        </div>
        <div class="header-subtext"><p>BÁO CÁO THIẾT BỊ HẰNG NGÀY</p></div>
    </div>
    <div class="header-underline"></div>
""", unsafe_allow_html=True)

st.html(f'<p class="demuc"><i>Nhân viên báo cáo: {st.session_state.username}</i></p>')

thong_tin_hanh_chinh()
sheeti5   = st.secrets["sheet_name"]["input_5"]
data_vttb = load_data(sheeti5)
now_vn    = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
st.date_input("Ngày báo cáo", value=now_vn.date(),
              format="DD/MM/YYYY", key="ngay_bao_cao", max_value=now_vn.date())

st.markdown("""
    <hr style="border:1.325px solid #195e83;margin:15px 0;">
    <p style="font-size:13.5px;color:#333"> 📌
        <i><span style="color:#f7270b;font-weight:bold">Lưu ý:</span>
        Báo cáo số máy <span style="color:#042f66;font-weight:bold">ĐANG DÙNG</span> =
        số máy <span style="color:#042f66;font-weight:bold">CỦA KHOA ĐANG DÙNG</span> +
        số máy <span style="color:#042f66;font-weight:bold">MƯỢN</span> từ khoa khác
        <span style="color:#042f66;font-weight:bold">ĐANG DÙNG</span><br>
        <span style="color:#042f66;font-weight:bold">(không tính số máy đang cho khoa khác mượn)</span>
        <br><br></i>
    </p>
""", unsafe_allow_html=True)

if "khoa_VTTB" in st.session_state and st.session_state["khoa_VTTB"] is not None:
    thiet_bi     = st.session_state.thiet_bi
    nhom_bao_cao = st.session_state.get("nhom_bao_cao", "1")
    thiet_bi["2025"] = pd.to_numeric(thiet_bi["2025"], errors="coerce")

    for i in range(len(thiet_bi)):
        ten         = thiet_bi["Tên thiết bị"].iloc[i]
        ma_thiet_bi = thiet_bi["Mã thiết bị"].iloc[i]
        Ten_thiet_bi = f"{ma_thiet_bi}: {ten}"

        if kiem_tra_nhom_bao_cao(ma_thiet_bi, nhom_bao_cao):
            continue

        st.markdown(f'<p style="font-size:15px;color:#005259;'
                    f'font-family:Source Sans Pro,sans-serif;font-weight:bold;">'
                    f'{Ten_thiet_bi}</p>', unsafe_allow_html=True)

        SL = int(thiet_bi["2025"].iloc[i]) if pd.notnull(thiet_bi["2025"].iloc[i]) else 0
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        with col1:
            st.number_input("Cơ số", value=SL, disabled=True, key=f"co_so_{i}")
        with col2:
            st.number_input("Đang dùng", step=1, key=f"dang_su_dung_{i}",
                            min_value=0, value=None)
        with col3:
            st.number_input("Trống", step=1, key=f"trong_{i}",
                            min_value=0, value=None)
        with col4:
            st.number_input("Hư", step=1, key=f"hu_{i}", min_value=0)

        if ma_thiet_bi[0] != "A":
            with st.expander(f"Thông tin bổ sung thiết bị {ten}", expanded=False):
                st.number_input("Số người bệnh có chỉ định sử dụng máy SCD nhưng chưa thực hiện",
                                min_value=0, step=1, key=f"chua_thuc_hien_{i}")
                st.selectbox("Nguyên nhân người bệnh chưa được sử dụng máy SCD",
                             options=["", "Không có máy", "Không có vớ", "Nguyên nhân khác"],
                             key=f"nguyen_nhan_{i}")

                # Dùng chung 1 vòng lặp cho 2 block mượn / cho mượn
                for label, lst_key, key_khoa, key_sl, btn_key in [
                    (f"{ten} mượn từ khoa khác",
                     "them_cot_muon", "muon_tu_khoa_khac_", "so_luong_muon_",
                     "them_lua_chon"),
                    (f"{ten} cho khoa khác mượn",
                     "them_cot_cho_muon", "cho_khoa_khac_muon", "so_luong_cho_muon_",
                     "them_lua_chon_2"),
                ]:
                    st.markdown(f'<p style="font-size:15px;color:#005259;'
                                f'font-family:Source Sans Pro,sans-serif;font-weight:bold;">'
                                f'{label}</p>', unsafe_allow_html=True)
                    if lst_key not in st.session_state:
                        st.session_state[lst_key] = [1]
                    for idx in st.session_state[lst_key]:
                        c1, c2 = st.columns([7, 3])
                        with c1:
                            st.selectbox("-",
                                options=["--Chọn khoa--"] + list(data_vttb["Khoa"].unique()),
                                key=f"{key_khoa}{idx}")
                        with c2:
                            st.number_input("-", step=1, key=f"{key_sl}{idx}")
                    ca, cr = st.columns([1, 1])
                    with ca:
                        if st.button("Thêm lựa chọn", key=f"them_{btn_key}"):
                            st.session_state[lst_key].append(
                                len(st.session_state[lst_key]) + 1)
                            st.rerun()
                    with cr:
                        if st.button("Xóa", key=f"xoa_{btn_key}"):
                            if len(st.session_state[lst_key]) > 1:
                                st.session_state[lst_key].pop()
                                st.rerun()

    submitbutton = st.button("Lưu kết quả", type="primary", key="luu")
    if submitbutton:
        loi_bat_buoc = kiem_tra_tong()
        if loi_bat_buoc:
            warning(loi_bat_buoc)
        else:
            loi_SCD = kiem_tra_may_SCD()
            if loi_SCD:
                warning_SCD(loi_SCD)
            else:
                success = upload_data_VTTB()
                if success:
                    warning(1)
                    clear_all_inputs()
                    clear_session_state()
else:
    st.warning("Vui lòng chọn khoa cần báo cáo")