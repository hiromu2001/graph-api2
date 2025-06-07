from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import os
from io import StringIO
import matplotlib.font_manager as fm

matplotlib.use("Agg")

app = FastAPI()

# 日本語フォントの設定
FONT_PATH = "fonts/NotoSansJP-Regular.ttf"
if os.path.exists(FONT_PATH):
    fm.fontManager.addfont(FONT_PATH)
    plt.rcParams['font.family'] = 'Noto Sans JP'
else:
    print("⚠️ フォントファイルが見つかりません。fonts/NotoSansJP-Regular.ttf を配置してください")

# 画像フォルダを公開
os.makedirs("images", exist_ok=True)
app.mount("/images", StaticFiles(directory="images"), name="images")

@app.post("/generate-graphs")
async def generate_graphs(file: UploadFile = File(...)):
    contents = await file.read()
    try:
        df = pd.read_csv(StringIO(contents.decode("utf-8")))
    except Exception as e:
        return JSONResponse(content={"error": f"CSV読み込み失敗: {e}"}, status_code=400)

    # 必須カラム確認
    required_cols = ["販売数量", "単価", "サブカテゴリ", "曜日", "最高気温", "値引き率", "廃棄率", "商品名"]
    for col in required_cols:
        if col not in df.columns:
            return JSONResponse(content={"error": f"CSVに『{col}』の列が必要です"}, status_code=400)

    # 金額列追加
    df["金額"] = df["販売数量"] * df["単価"]

    # 曜日変換（例: "月" → "月曜日"）
    weekday_map = {
        "月": "月曜日", "火": "火曜日", "水": "水曜日", "木": "木曜日",
        "金": "金曜日", "土": "土曜日", "日": "日曜日"
    }
    df["曜日"] = df["曜日"].map(weekday_map).fillna(df["曜日"])
    weekdays = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"]

    def save_fig(fig, name):
        fig.tight_layout()
        fig.savefig(f"images/{name}.png")
        plt.close(fig)

    # グラフ生成関数群
    fig1 = plt.figure()
    df.groupby("サブカテゴリ")["金額"].sum().sort_values().plot.barh(title="サブカテゴリ別売上")
    save_fig(fig1, "subcat_sales")

    fig2 = plt.figure()
    df.groupby("曜日")["金額"].sum().reindex(weekdays).plot.bar()
    plt.title("曜日別売上")
    plt.xlabel("曜日")
    save_fig(fig2, "weekday_sales")

    fig3 = plt.figure()
    df.groupby("値引き率")["金額"].mean().plot.bar(title="値引き率ごとの平均売上")
    save_fig(fig3, "discount_avg_sales")

    fig4 = plt.figure()
    df.groupby("廃棄率")["金額"].mean().plot.bar(title="廃棄率ごとの平均売上")
    save_fig(fig4, "waste_avg_sales")

    fig5 = plt.figure()
    plt.scatter(df["最高気温"], df["金額"])
    plt.xlabel("最高気温")
    plt.ylabel("売上金額")
    plt.title("気温と売上の関係")
    save_fig(fig5, "temp_vs_sales")

    fig6 = plt.figure()
    df.groupby("商品名")["金額"].sum().sort_values(ascending=False).head(10).plot.bar(title="売上金額トップ10商品")
    save_fig(fig6, "top10_sales")

    fig7 = plt.figure()
    df.groupby("商品名")["値引き率"].mean().sort_values(ascending=False).head(10).plot.bar(title="値引き率トップ10商品")
    save_fig(fig7, "top10_discount")

    fig8 = plt.figure()
    df.groupby("商品名")["廃棄率"].mean().sort_values(ascending=False).head(10).plot.bar(title="廃棄率トップ10商品")
    save_fig(fig8, "top10_waste")

    fig9 = plt.figure()
    temp_group = df.groupby("サブカテゴリ")[["最高気温", "金額"]].mean()
    plt.scatter(temp_group["最高気温"], temp_group["金額"])
    plt.xlabel("最高気温（平均）")
    plt.ylabel("売上金額（平均）")
    plt.title("気温とサブカテゴリ別売上")
    save_fig(fig9, "temp_vs_subcat_sales")

    fig10 = plt.figure()
    weekday_sub = df.groupby(["曜日", "サブカテゴリ"])["金額"].mean().unstack()
    weekday_sub = weekday_sub.reindex(weekdays)
    weekday_sub.plot(marker="o", title="曜日とサブカテゴリの売上傾向")
    plt.ylabel("平均売上")
    save_fig(fig10, "weekday_vs_subcat")

    fig11 = plt.figure()
    df.groupby("サブカテゴリ")["金額"].sum().plot.pie(autopct="%1.1f%%", startangle=90)
    plt.title("サブカテゴリ別売上構成")
    plt.ylabel("")
    save_fig(fig11, "subcat_pie")

    fig12 = plt.figure()
    weekday_sum = df.groupby("曜日")["金額"].sum().reindex(weekdays).dropna()
    weekday_sum.plot.pie(autopct="%1.1f%%", startangle=90)
    plt.title("曜日別売上構成")
    plt.ylabel("")
    save_fig(fig12, "weekday_pie")

    # レスポンス整形
    image_info = [
        {"title": "サブカテゴリ別売上", "url": "https://graph-api2.onrender.com/images/subcat_sales.png"},
        {"title": "曜日別売上", "url": "https://graph-api2.onrender.com/images/weekday_sales.png"},
        {"title": "値引き率ごとの平均売上", "url": "https://graph-api2.onrender.com/images/discount_avg_sales.png"},
        {"title": "廃棄率ごとの平均売上", "url": "https://graph-api2.onrender.com/images/waste_avg_sales.png"},
        {"title": "気温と売上の関係", "url": "https://graph-api2.onrender.com/images/temp_vs_sales.png"},
        {"title": "売上金額トップ10商品", "url": "https://graph-api2.onrender.com/images/top10_sales.png"},
        {"title": "値引き率トップ10商品", "url": "https://graph-api2.onrender.com/images/top10_discount.png"},
        {"title": "廃棄率トップ10商品", "url": "https://graph-api2.onrender.com/images/top10_waste.png"},
        {"title": "気温とサブカテゴリ別売上", "url": "https://graph-api2.onrender.com/images/temp_vs_subcat_sales.png"},
        {"title": "曜日とサブカテゴリの売上傾向", "url": "https://graph-api2.onrender.com/images/weekday_vs_subcat.png"},
        {"title": "サブカテゴリ別売上構成", "url": "https://graph-api2.onrender.com/images/subcat_pie.png"},
        {"title": "曜日別売上構成", "url": "https://graph-api2.onrender.com/images/weekday_pie.png"},
    ]

    return JSONResponse(content={"message": "グラフを生成しました", "images": image_info})
