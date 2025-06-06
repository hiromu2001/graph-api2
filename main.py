from fastapi import FastAPI, File, UploadFile  # FastAPI関連のライブラリ
from fastapi.responses import FileResponse  # 画像ファイルを返すために使用
import pandas as pd  # データ処理用
import matplotlib.pyplot as plt  # グラフ描画用
import seaborn as sns  # グラフスタイル調整用
import os  # フォントのパス操作
from matplotlib.font_manager import FontProperties  # 日本語フォント指定用
import io  # StringIO用

app = FastAPI()

# フォントをプロジェクト内のfontsフォルダから読み込む
font_path = os.path.join(os.path.dirname(__file__), "fonts", "NotoSansJP-Regular.ttf")
font_prop = FontProperties(fname=font_path)
plt.rcParams["font.family"] = font_prop.get_name()  # 日本語フォントを設定

@app.post("/generate-graphs")
async def generate_graph(file: UploadFile = File(...)):
    # CSVファイル読み込み
    contents = await file.read()
    df = pd.read_csv(io.StringIO(contents.decode("utf-8")))  # ← 修正点！

    # 売上金額列の作成
    df["金額"] = df["単価"] * df["数量"]

    # カテゴリ別売上の合計
    category_sales = df.groupby("カテゴリ")["金額"].sum().sort_values(ascending=False)

    # グラフ描画
    plt.figure(figsize=(10, 6))
    sns.barplot(x=category_sales.values, y=category_sales.index)
    plt.title("カテゴリ別売上", fontproperties=font_prop)
    plt.xlabel("売上金額", fontproperties=font_prop)
    plt.ylabel("カテゴリ", fontproperties=font_prop)
    plt.tight_layout()

    # 画像として保存
    output_path = "category_sales.png"
    plt.savefig(output_path)
    plt.close()

    # 保存した画像ファイルを返す
    return FileResponse(output_path, media_type="image/png")
