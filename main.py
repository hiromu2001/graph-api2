from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import os
from io import StringIO
from matplotlib import font_manager as fm

matplotlib.use("Agg")

# 日本語フォント設定
FONT_PATH = "fonts/NotoSansJP-Regular.ttf"
if os.path.exists(FONT_PATH):
    fm.fontManager.addfont(FONT_PATH)
    plt.rcParams["font.family"] = "Noto Sans JP"
else:
    print("⚠️ フォントファイルが見つかりません。fonts/NotoSansJP-Regular.ttf を配置してください")

# imagesディレクトリがなければ作成
os.makedirs("images", exist_ok=True)

app = FastAPI()
app.mount("/images", StaticFiles(directory="images"), name="images")

@app.post("/generate-graphs")
async def generate_graphs(file: UploadFile = File(...)):
    contents = await file.read()
    try:
        df = pd.read_csv(StringIO(contents.decode("utf-8")))
    except Exception:
        return JSONResponse(content={"error": "CSV読み込み失敗"}, status_code=400)

    required_cols = ["販売数量", "単価", "サブカテゴリ", "曜日", "最高気温", "値引き率", "廃棄率"]
    for col in required_cols:
        if col not in df.columns:
            return JSONResponse(content={"error": f"CSVに『{col}』の列が必要です"}, status_code=400)

    df["金額"] = df["販売数量"] * df["単価"]

    # デバッグ用出力：曜日の出現回数と金額合計
    print("=== 曜日ごとの出現回数 ===")
    print(df["曜日"].value_counts())
    print("=== 曜日ごとの売上合計 ===")
    print(df.groupby("曜日")["金額"].sum())

    # グラフ保存関数
    def save_plot(fig, name):
        fig.tight_layout()
        fig.savefig(f"images/{name}.png")
        plt.close(fig)

    # サブカテゴリ別売上
    fig1 = plt.figure()
    df.groupby("サブカテゴリ")["金額"].sum().sort_values().plot.barh(title="サブカテゴリ別売上")
    save_plot(fig1, "subcat_sales")

    # 曜日別売上
    fig2 = plt.figure()
    weekdays = ["月", "火", "水", "木", "金", "土", "日"]
    df.groupby("曜日")["金額"].sum().reindex(weekdays).plot.bar(title="曜日別売上")
    save_plot(fig2, "weekday_sales")

    # 値引き率ごとの平均売上
    fig3 = plt.figure()
    df.groupby("値引き率")["金額"].mean().plot.bar(title="値引き率ごとの平均売上")
    save_plot(fig3, "discount_avg_sales")

    # 廃棄率ごとの平均売上
    fig4 = plt.figure()
    df.groupby("廃棄率")["金額"].mean().plot.bar(title="廃棄率ごとの平均売上")
    save_plot(fig4, "waste_avg_sales")

    # 気温と売上の散布図
    fig5 = plt.figure()
    plt.scatter(df["最高気温"], df["金額"])
    plt.xlabel("最高気温")
    plt.ylabel("売上金額")
    plt.title("気温と売上の関係")
    save_plot(fig5, "temp_vs_sales")

    # サブカテゴリごとの平均気温と平均売上の散布図
    fig6 = plt.figure()
    temp_grp = df.groupby("サブカテゴリ")[["最高気温", "金額"]].mean()
    plt.scatter(temp_grp["最高気温"], temp_grp["金額"])
    plt.xlabel("平均気温")
    plt.ylabel("平均売上金額")
    plt.title("気温とサブカテゴリ別平均売上")
    save_plot(fig6, "temp_vs_subcat_sales")

    # 曜日×サブカテゴリの売上傾向
    fig7 = plt.figure()
    weekday_subcat = df.groupby(["曜日", "サブカテゴリ"])["金額"].mean().unstack()
    weekday_subcat.plot(marker="o", title="曜日とサブカテゴリの売上傾向")
    plt.ylabel("平均売上")
    save_plot(fig7, "weekday_vs_subcat")

    # サブカテゴリ売上構成（円グラフ）
    fig8 = plt.figure()
    df.groupby("サブカテゴリ")["金額"].sum().plot.pie(autopct="%1.1f%%", startangle=90)
    plt.title("サブカテゴリ別売上構成")
    plt.ylabel("")
    save_plot(fig8, "subcat_pie")

    # 曜日売上構成（円グラフ）
    fig9 = plt.figure()
    weekday_sum = df.groupby("曜日")["金額"].sum().reindex(weekdays)
    weekday_sum.dropna(inplace=True)
    weekday_sum.plot.pie(autopct="%1.1f%%", startangle=90)
    plt.title("曜日別売上構成")
    plt.ylabel("")
    save_plot(fig9, "weekday_pie")

    return {
        "message": "グラフを生成しました",
        "image_urls": [f"https://graph-api2.onrender.com/images/{name}.png" for name in [
            "subcat_sales", "weekday_sales", "discount_avg_sales", "waste_avg_sales",
            "temp_vs_sales", "temp_vs_subcat_sales", "weekday_vs_subcat",
            "subcat_pie", "weekday_pie"
        ]]
    }
