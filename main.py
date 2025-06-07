from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse, JSONResponse
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from matplotlib.font_manager import FontProperties

app = FastAPI()

# フォント設定（プロジェクト内）
font_path = os.path.join(os.path.dirname(__file__), "fonts", "NotoSansJP-Regular.ttf")
if os.path.exists(font_path):
    font_prop = FontProperties(fname=font_path)
    plt.rcParams["font.family"] = font_prop.get_name()

# 出力フォルダ
output_dir = "output"
os.makedirs(output_dir, exist_ok=True)

@app.post("/generate-graphs")
async def generate_graphs(file: UploadFile = File(...)):
    contents = await file.read()
    try:
        df = pd.read_csv(pd.compat.StringIO(contents.decode("utf-8")))
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": f"CSV読み込み失敗: {str(e)}"})

    # 列名の正規化（全角→半角、空白除去など）
    df.columns = df.columns.str.strip()

    # 必須列のチェック
    required_columns = ["サブカテゴリ", "曜日", "単価", "売上数量"]
    for col in required_columns:
        if col not in df.columns:
            return JSONResponse(status_code=400, content={"error": f"CSVに『{col}』の列が必要です"})

    # 金額列を計算
    df["金額"] = df["単価"] * df["売上数量"]

    # グラフ生成処理一覧
    filenames = []

    def save_plot(fig, filename):
        path = os.path.join(output_dir, filename)
        fig.savefig(path, bbox_inches='tight')
        plt.close(fig)
        filenames.append(filename)

    # サブカテゴリ別売上
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(x="金額", y="サブカテゴリ", data=df.groupby("サブカテゴリ", as_index=False)["金額"].sum().sort_values(by="金額", ascending=False), ax=ax)
    ax.set_title("サブカテゴリ別売上")
    save_plot(fig, "subcat_sales.png")

    # 曜日別売上
    fig, ax = plt.subplots(figsize=(8, 5))
    order = ["月", "火", "水", "木", "金", "土", "日"]
    weekday_sum = df.groupby("曜日")["金額"].sum().reindex(order)
    sns.barplot(x=weekday_sum.index, y=weekday_sum.values, ax=ax)
    ax.set_title("曜日別売上")
    save_plot(fig, "weekday_sales.png")

    # 値引き率別平均売上
    if "値引き率" in df.columns:
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(x="値引き率", y="金額", data=df, estimator="mean", ax=ax)
        ax.set_title("値引き率別平均売上")
        save_plot(fig, "discount_rate_avg_sales.png")

    # 廃棄率別平均売上
    if "廃棄率" in df.columns:
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(x="廃棄率", y="金額", data=df, estimator="mean", ax=ax)
        ax.set_title("廃棄率別平均売上")
        save_plot(fig, "waste_rate_avg_sales.png")

    # 売上金額トップ10商品
    if "商品名" in df.columns:
        top10 = df.groupby("商品名")["金額"].sum().sort_values(ascending=False).head(10)
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(x=top10.values, y=top10.index, ax=ax)
        ax.set_title("売上金額トップ10商品")
        save_plot(fig, "top10_sales.png")

    # 値引き率トップ10商品
    if "商品名" in df.columns and "値引き率" in df.columns:
        disc_top10 = df.groupby("商品名")["値引き率"].mean().sort_values(ascending=False).head(10)
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(x=disc_top10.values, y=disc_top10.index, ax=ax)
        ax.set_title("値引き率トップ10商品")
        save_plot(fig, "top10_discount.png")

    # 廃棄率トップ10商品
    if "商品名" in df.columns and "廃棄率" in df.columns:
        waste_top10 = df.groupby("商品名")["廃棄率"].mean().sort_values(ascending=False).head(10)
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(x=waste_top10.values, y=waste_top10.index, ax=ax)
        ax.set_title("廃棄率トップ10商品")
        save_plot(fig, "top10_waste.png")

    # 気温と売上の散布図
    if "気温" in df.columns:
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.scatterplot(x="気温", y="金額", data=df, ax=ax)
        ax.set_title("気温と売上の散布図")
        save_plot(fig, "temp_vs_sales.png")

    # 気温とサブカテゴリの散布図
    if "気温" in df.columns:
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.scatterplot(x="気温", y="金額", hue="サブカテゴリ", data=df, ax=ax)
        ax.set_title("気温とサブカテゴリ売上の関係")
        save_plot(fig, "temp_vs_subcat.png")

    # 曜日別売上構成円グラフ
    fig, ax = plt.subplots(figsize=(6, 6))
    weekday_pie = df.groupby("曜日")["金額"].sum().reindex(order)
    ax.pie(weekday_pie, labels=weekday_pie.index, autopct="%1.1f%%", startangle=90)
    ax.set_title("曜日別売上構成比")
    save_plot(fig, "weekday_pie.png")

    # サブカテゴリ別構成円グラフ
    fig, ax = plt.subplots(figsize=(6, 6))
    subcat_pie = df.groupby("サブカテゴリ")["金額"].sum().sort_values(ascending=False)
    ax.pie(subcat_pie, labels=subcat_pie.index, autopct="%1.1f%%", startangle=90)
    ax.set_title("サブカテゴリ別売上構成比")
    save_plot(fig, "subcat_pie.png")

    return {"message": "グラフを生成しました", "files": filenames}

@app.get("/get-graph")
def get_graph(name: str):
    file_path = os.path.join(output_dir, name)
    if not os.path.exists(file_path):
        return JSONResponse(status_code=404, content={"error": "ファイルが存在しません"})
    return FileResponse(file_path, media_type="image/png")
