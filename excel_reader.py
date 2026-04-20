import os
import pandas as pd

def read_sheet(file_path: str):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".csv":
        return pd.read_csv(file_path)
    else:
        return pd.read_excel(file_path)
