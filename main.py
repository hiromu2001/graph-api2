from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from matplotlib.font_manager import FontProperties
from io import StringIO

app = FastAPI()

# フォントをプロジェクト内のfontsフォルダから読み込む
font_path = os.path.join(os.path.dirname(__file__), "fonts", "NotoSansJP-Regular.ttf")
font_prop = FontProperties(fname=font_path)
plt.rcParams["font.family"] = font_prop.get_name()

@app.post("/generate-graphs")
async def generate_graph(file: UploadFile = File(...)):
    # アップロードされたCSVファイルの読み込み
    contents = await file.read()
    df = pd.read_csv(StringIO(contents.decode("utf-8")))

    # 列名が異なる場合に備えて変換
    if "数量" not in df.columns:
        if "販売数量" in df.columns:
            df["数量"] = df["販売数量"]
        else:
            return {"error": "CSVに『数量』または『販売数量』の列が必要です"}

    if "単価" not in df.columns or "カテゴリ" not in df.columns:
        return {"error": "CSVに『単価』および『カテゴリ』の列が必要です"}

    # 売上金額の計算
    df["金額"] = df["単価"] * df["数量"]

    # カテゴリ別売上の集計
    category_sales = df.groupby("カテゴリ")["金額"].sum().sort_values(ascending=False)

    # グラフの生成
    plt.figure(figsize=(10, 6))
    sns.barplot(x=category_sales.values, y=category_sales.index)
    plt.title("カテゴリ別売上")
    plt.xlabel("売上金額")
    plt.tight_layout()
    output_path = "category_sales.png"
    plt.savefig(output_path)
    plt.close()

    return FileResponse(output_path, media_type="image/png")
