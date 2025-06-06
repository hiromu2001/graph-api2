from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from matplotlib.font_manager import FontProperties

app = FastAPI()

# フォントをプロジェクト内のfontsフォルダから読み込む
font_path = os.path.join(os.path.dirname(__file__), "fonts", "NotoSansJP-Regular.ttf")
font_prop = FontProperties(fname=font_path)
plt.rcParams["font.family"] = font_prop.get_name()

@app.post("/generate-graphs")
async def generate_graph(file: UploadFile = File(...)):
    # CSVファイル読み込み
    contents = await file.read()
    df = pd.read_csv(pd.compat.StringIO(contents.decode("utf-8")))

    # 売上合計
    df["金額"] = df["単価"] * df["数量"]

    # カテゴリ別売上
    category_sales = df.groupby("カテゴリ")["金額"].sum().sort_values(ascending=False)

    # グラフ出力
    plt.figure(figsize=(10, 6))
    sns.barplot(x=category_sales.values, y=category_sales.index)
    plt.title("カテゴリ別売上")
    plt.xlabel("売上金額")
    plt.tight_layout()
    output_path = "category_sales.png"
    plt.savefig(output_path)
    plt.close()

    return FileResponse(output_path, media_type="image/png")
