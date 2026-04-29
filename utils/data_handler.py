import pandas as pd
import numpy as np

def to_numeric_safe(value):
    """
    Chuyển đổi một giá trị sang kiểu số một cách an toàn.
    Xử lý: khoảng trắng, dấu phẩy, dấu trừ Unicode, chuỗi rỗng.
    
    Parameters:
        value: Giá trị cần chuyển đổi
    
    Returns:
        Giá trị số hoặc NaN nếu không thể chuyển đổi
    """
    if pd.isna(value):
        return np.nan
    
    # Chuyển sang string và xử lý
    str_val = str(value).strip()
    
    if not str_val or str_val.lower() in ['nan', 'none', '']:
        return np.nan
    
    # Thay dấu phẩy bằng dấu chấm
    str_val = str_val.replace(',', '.')
    # Xử lý dấu trừ Unicode
    str_val = str_val.replace('−', '-')
    
    try:
        return float(str_val)
    except (ValueError, TypeError):
        return np.nan

def convert_numeric_columns(data, columns, strip_whitespace=True):
    """
    Chuyển đổi nhiều cột sang kiểu số một cách an toàn.
    
    Parameters:
        data: DataFrame
        columns: Danh sách các chỉ số cột hoặc tên cột cần chuyển đổi
        strip_whitespace: Có loại bỏ khoảng trắng không
    
    Returns:
        DataFrame đã được chuyển đổi
    """
    data = data.copy()
    
    for col in columns:
        if isinstance(col, int):
            # Chuyển đổi theo chỉ số cột
            data.iloc[:, col] = (data.iloc[:, col]
                                .astype(str)
                                .str.strip() if strip_whitespace else data.iloc[:, col].astype(str))
            data.iloc[:, col] = data.iloc[:, col].str.replace(',', '.', regex=False)
            data.iloc[:, col] = data.iloc[:, col].str.replace('−', '-', regex=False)
            data.iloc[:, col] = data.iloc[:, col].replace('', np.nan)
            data.iloc[:, col] = data.iloc[:, col].replace('nan', np.nan)
            data.iloc[:, col] = pd.to_numeric(data.iloc[:, col], errors='coerce')
        else:
            # Chuyển đổi theo tên cột
            data[col] = (data[col]
                        .astype(str)
                        .str.strip() if strip_whitespace else data[col].astype(str))
            data[col] = data[col].str.replace(',', '.', regex=False)
            data[col] = data[col].str.replace('−', '-', regex=False)
            data[col] = data[col].replace('', np.nan)
            data[col] = data[col].replace('nan', np.nan)
            data[col] = pd.to_numeric(data[col], errors='coerce')
    
    return data

def convert_numeric_by_range(data, start_col, end_col=None):
    """
    Chuyển đổi một phạm vi cột từ vị trí bắt đầu đến cột cuối cùng.
    
    Parameters:
        data: DataFrame
        start_col: Chỉ số cột bắt đầu
        end_col: Chỉ số cột kết thúc (nếu None, chuyển đến cột cuối cùng)
    
    Returns:
        DataFrame đã được chuyển đổi
    """
    if end_col is None:
        end_col = len(data.columns)
    
    return convert_numeric_columns(data, range(start_col, end_col))
