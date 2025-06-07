from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import io
from matplotlib.font_manager import FontProperties

app = FastAPI()

# フォント設定（Render環境でファイルがないときも動作）
font_path = os.path.join(os.path.dirname(__file__), "fonts", "NotoSansJP-Regular.ttf")
if os.path.exists(font_path):
    font_prop = FontProperties(fname=font_path)
    plt.rcParams["font.family"] = font_prop.get_name()

# 出力フォルダ作成
output_dir = "output"
os.makedirs(output_dir, exist_ok=True)

@app.post("/generate-graphs")
async def generate_graphs(file: UploadFile = File(...)):
    contents = await file.read()
    try:
        df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": f"CSV読み込み失敗: {str(e)}"})

    # カラム名の確認とリネーム
    col_map = {
        "売上数量": "数量",
        "サブカテゴリ": "カテゴリ"
    }
    df.rename(columns=col_map, inplace=True)

    if "単価" not in df.columns or "数量" not in df.columns:
        return JSONResponse(status_code=400, content={"error": "CSVに『単価』および『数量』の列が必要です"})

    # 売上金額算出
    df["金額"] = df["単価"] * df["数量"]

    # 値引き率・廃棄率があれば float に
    for col in ["値引き率", "廃棄率"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # ====== グラフ描画開始 ======
    sns.set(style="whitegrid")
    plt.ioff()

    def save_plot(fig, name):
        path = os.path.join(output_dir, f"{name}.png")
        fig.savefig(path)
        plt.close(fig)

    # 1. サブカテゴリ別売上
    fig1 = plt.figure(figsize=(10, 6))
    df.groupby("カテゴリ")["金額"].sum().sort_values().plot.barh()
    plt.title("サブカテゴリ別売上")
    save_plot(fig1, "subcat_sales")

    # 2. 曜日別売上
    if "曜日" in df.columns:
        fig2 = plt.figure(figsize=(10, 6))
        order = ["月", "火", "水", "木", "金", "土", "日"]
        df.groupby("曜日")["金額"].sum().reindex(order).plot.bar()
        plt.title("曜日別売上")
        save_plot(fig2, "weekday_sales")

    # 3. 値引き率ごとの平均売上
    if "値引き率" in df.columns:
        fig3 = plt.figure(figsize=(10, 6))
        df.groupby("値引き率")["金額"].mean().plot()
        plt.title("値引き率ごとの平均売上")
        save_plot(fig3, "discount_avg_sales")

    # 4. 廃棄率ごとの平均売上
    if "廃棄率" in df.columns:
        fig4 = plt.figure(figsize=(10, 6))
        df.groupby("廃棄率")["金額"].mean().plot()
        plt.title("廃棄率ごとの平均売上")
        save_plot(fig4, "waste_avg_sales")

    # 5. 気温と売上の散布図
    if "気温" in df.columns:
        fig5 = plt.figure(figsize=(10, 6))
        sns.scatterplot(x="気温", y="金額", data=df)
        plt.title("気温と売上の関係")
        save_plot(fig5, "temp_vs_sales")

    # 6. サブカテゴリ別気温との関係（散布図）
    if "気温" in df.columns:
        fig6 = plt.figure(figsize=(10, 6))
        sns.scatterplot(x="気温", y="金額", hue="カテゴリ", data=df)
        plt.title("気温とサブカテゴリ別売上")
        save_plot(fig6, "temp_vs_subcat")

    # 7. 曜日×サブカテゴリの散布図
    if "曜日" in df.columns:
        fig7 = plt.figure(figsize=(10, 6))
        sns.stripplot(x="曜日", y="金額", hue="カテゴリ", data=df, jitter=True)
        plt.title("曜日とサブカテゴリ別売上")
        save_plot(fig7, "weekday_vs_subcat")

    # 8. 売上金額トップ10商品
    if "商品名" in df.columns:
        fig8 = plt.figure(figsize=(10, 6))
        top10 = df.groupby("商品名")["金額"].sum().nlargest(10)
        top10.plot.barh()
        plt.title("売上トップ10商品")
        save_plot(fig8, "top10_sales")

    # 9. 値引き率トップ10商品
    if "値引き率" in df.columns and "商品名" in df.columns:
        fig9 = plt.figure(figsize=(10, 6))
        top10 = df.groupby("商品名")["値引き率"].mean().nlargest(10)
        top10.plot.barh()
        plt.title("値引き率トップ10商品")
        save_plot(fig9, "top10_discount")

    # 10. 廃棄率トップ10商品
    if "廃棄率" in df.columns and "商品名" in df.columns:
        fig10 = plt.figure(figsize=(10, 6))
        top10 = df.groupby("商品名")["廃棄率"].mean().nlargest(10)
        top10.plot.barh()
        plt.title("廃棄率トップ10商品")
        save_plot(fig10, "top10_waste")

    # 11. サブカテゴリ別売上構成円グラフ
    fig11 = plt.figure(figsize=(8, 8))
    df.groupby("カテゴリ")["金額"].sum().plot.pie(autopct="%1.1f%%", startangle=90)
    plt.title("サブカテゴリ別売上構成比")
    save_plot(fig11, "subcat_pie")

    # 12. 曜日別売上構成円グラフ
    if "曜日" in df.columns:
        fig12 = plt.figure(figsize=(8, 8))
        df.groupby("曜日")["金額"].sum().reindex(order).plot.pie(autopct="%1.1f%%", startangle=90)
        plt.title("曜日別売上構成比")
        save_plot(fig12, "weekday_pie")

    return {"message": "グラフを生成しました。outputフォルダを確認してください。"}
