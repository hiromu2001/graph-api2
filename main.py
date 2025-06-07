from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import matplotlib.font_manager as fm
import os
from io import StringIO

# 日本語フォント設定
FONT_PATH = "fonts/NotoSansJP-Regular.ttf"
if os.path.exists(FONT_PATH):
    fm.fontManager.addfont(FONT_PATH)
    plt.rcParams["font.family"] = "Noto Sans JP"
else:
    print("⚠️ フォントファイルが見つかりません。fonts/NotoSansJP-Regular.ttf を配置してください")

matplotlib.use("Agg")

app = FastAPI()
app.mount("/images", StaticFiles(directory="images"), name="images")

@app.post("/generate-graphs")
async def generate_graphs(file: UploadFile = File(...)):
    contents = await file.read()
    try:
        df = pd.read_csv(StringIO(contents.decode("utf-8")))
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": f"CSV読み込み失敗: {str(e)}"})

    required_cols = ["販売数量", "単価", "商品名", "サブカテゴリ", "曜日", "最高気温", "値引き率", "廃棄率"]
    for col in required_cols:
        if col not in df.columns:
            return JSONResponse(status_code=400, content={"error": f"CSVに『{col}』の列が必要です"})

    df["曜日"] = df["曜日"].str.replace("曜日", "", regex=False)
    df["金額"] = df["単価"] * df["販売数量"]
    os.makedirs("images", exist_ok=True)

    def save_plot(fig, name):
        fig.tight_layout()
        fig.savefig(f"images/{name}.png")
        plt.close(fig)

    image_urls = []
    weekdays = ["月", "火", "水", "木", "金", "土", "日"]

    # サブカテゴリ別売上
    fig = plt.figure()
    df.groupby("サブカテゴリ")["金額"].sum().sort_values().plot.barh(title="サブカテゴリ別売上")
    save_plot(fig, "subcat_sales")
    image_urls.append("https://graph-api2.onrender.com/images/subcat_sales.png")

    # 曜日別売上
    fig = plt.figure()
    df_by_weekday = df.groupby("曜日")["金額"].sum().reindex(weekdays)
    df_by_weekday.dropna(inplace=True)
    df_by_weekday.plot.bar(title="曜日別売上")
    save_plot(fig, "weekday_sales")
    image_urls.append("https://graph-api2.onrender.com/images/weekday_sales.png")

    # 値引き率ごとの平均売上
    fig = plt.figure()
    df.groupby("値引き率")["金額"].mean().plot.bar(title="値引き率ごとの平均売上")
    save_plot(fig, "discount_avg_sales")
    image_urls.append("https://graph-api2.onrender.com/images/discount_avg_sales.png")

    # 廃棄率ごとの平均売上
    fig = plt.figure()
    df.groupby("廃棄率")["金額"].mean().plot.bar(title="廃棄率ごとの平均売上")
    save_plot(fig, "waste_avg_sales")
    image_urls.append("https://graph-api2.onrender.com/images/waste_avg_sales.png")

    # 気温と売上の散布図（サブカテゴリ別平均）
    fig = plt.figure()
    temp_sales = df.groupby("サブカテゴリ")[["最高気温", "金額"]].mean()
    plt.scatter(temp_sales["最高気温"], temp_sales["金額"])
    plt.xlabel("最高気温（平均）")
    plt.ylabel("売上金額（平均）")
    plt.title("気温と売上の関係（サブカテゴリ別）")
    save_plot(fig, "temp_vs_sales")
    image_urls.append("https://graph-api2.onrender.com/images/temp_vs_sales.png")

    # 売上トップ10商品
    fig = plt.figure()
    df.groupby("商品名")["金額"].sum().sort_values(ascending=False).head(10).plot.bar(title="売上金額トップ10商品")
    save_plot(fig, "top10_sales")
    image_urls.append("https://graph-api2.onrender.com/images/top10_sales.png")

    # 値引き率トップ10商品
    fig = plt.figure()
    df.groupby("商品名")["値引き率"].mean().sort_values(ascending=False).head(10).plot.bar(title="値引き率トップ10商品")
    save_plot(fig, "top10_discount")
    image_urls.append("https://graph-api2.onrender.com/images/top10_discount.png")

    # 廃棄率トップ10商品
    fig = plt.figure()
    df.groupby("商品名")["廃棄率"].mean().sort_values(ascending=False).head(10).plot.bar(title="廃棄率トップ10商品")
    save_plot(fig, "top10_waste")
    image_urls.append("https://graph-api2.onrender.com/images/top10_waste.png")

    # 気温×サブカテゴリ（平均）散布図
    fig = plt.figure()
    plt.scatter(temp_sales["最高気温"], temp_sales["金額"])
    plt.xlabel("最高気温（平均）")
    plt.ylabel("平均売上")
    plt.title("サブカテゴリ別：気温と平均売上")
    save_plot(fig, "temp_vs_subcat_sales")
    image_urls.append("https://graph-api2.onrender.com/images/temp_vs_subcat_sales.png")

    # 曜日×サブカテゴリ 売上散布図（平均）
    fig = plt.figure()
    weekday_sub = df.groupby(["曜日", "サブカテゴリ"])["金額"].mean().unstack().reindex(weekdays)
    weekday_sub.plot(marker="o", title="曜日とサブカテゴリの売上傾向")
    plt.ylabel("平均売上")
    save_plot(fig, "weekday_vs_subcat")
    image_urls.append("https://graph-api2.onrender.com/images/weekday_vs_subcat.png")

    # 円グラフ: サブカテゴリ別売上構成
    fig = plt.figure()
    df.groupby("サブカテゴリ")["金額"].sum().plot.pie(autopct="%1.1f%%", startangle=90)
    plt.title("サブカテゴリ別売上構成")
    plt.ylabel("")
    save_plot(fig, "subcat_pie")
    image_urls.append("https://graph-api2.onrender.com/images/subcat_pie.png")

    # 円グラフ: 曜日売上構成
    fig = plt.figure()
    df_by_weekday.plot.pie(autopct="%1.1f%%", startangle=90)
    plt.title("曜日別売上構成")
    plt.ylabel("")
    save_plot(fig, "weekday_pie")
    image_urls.append("https://graph-api2.onrender.com/images/weekday_pie.png")

    return {"message": "グラフを生成しました", "image_urls": image_urls}
