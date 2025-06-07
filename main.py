from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import os
from io import StringIO

matplotlib.use("Agg")

app = FastAPI()
app.mount("/images", StaticFiles(directory="images"), name="images")

# フォント設定（必要に応じて）
from matplotlib import font_manager as fm
FONT_PATH = "fonts/NotoSansJP-Regular.ttf"
if os.path.exists(FONT_PATH):
    fm.fontManager.addfont(FONT_PATH)
    plt.rcParams['font.family'] = 'Noto Sans JP'
else:
    print(f"⚠️ フォントファイルが見つかりません。{FONT_PATH} を配置してください")

@app.post("/generate-graphs")
async def generate_graphs(file: UploadFile = File(...)):
    contents = await file.read()
    try:
        df = pd.read_csv(StringIO(contents.decode("utf-8")))
    except Exception as e:
        return JSONResponse(content={"error": f"CSV読み込み失敗: {str(e)}"}, status_code=400)

    required_cols = ["販売数量", "単価", "サブカテゴリ", "曜日", "最高気温", "値引き率", "廃棄率", "商品名"]
    for col in required_cols:
        if col not in df.columns:
            return JSONResponse(content={"error": f"CSVに『{col}』の列が必要です"}, status_code=400)

    df["金額"] = df["販売数量"] * df["単価"]

    os.makedirs("images", exist_ok=True)

    def save_plot(fig, name):
        fig.tight_layout()
        fig.savefig(f"images/{name}.png")
        plt.close(fig)

    image_info = []
    
    # サブカテゴリ別売上
    fig1 = plt.figure()
    df.groupby("サブカテゴリ")["金額"].sum().sort_values().plot.barh(title="サブカテゴリ別売上")
    save_plot(fig1, "subcat_sales")
    image_info.append({"title": "サブカテゴリ別売上", "url": "https://graph-api2.onrender.com/images/subcat_sales.png"})

    # 曜日別売上
    fig2 = plt.figure()
    weekday_map = {"月": "月曜日", "火": "火曜日", "水": "水曜日", "木": "木曜日", "金": "金曜日", "土": "土曜日", "日": "日曜日"}
    df["曜日"] = df["曜日"].map(weekday_map)
    df = df[df["曜日"].notna()]
    weekday_order = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"]
    df["曜日"] = pd.Categorical(df["曜日"], categories=weekday_order, ordered=True)
    weekday_sales = df.groupby("曜日")["金額"].sum().reindex(weekday_order)
    print("=== 曜日ごとの売上合計 ===")
    print(weekday_sales)
    weekday_sales.plot.bar()
    plt.title("曜日別売上")
    plt.xlabel("曜日")
    save_plot(fig2, "weekday_sales")
    image_info.append({"title": "曜日別売上", "url": "https://graph-api2.onrender.com/images/weekday_sales.png"})

    # 値引き率ごとの平均売上
    fig3 = plt.figure()
    df.groupby("値引き率")["金額"].mean().plot.bar(title="値引き率ごとの平均売上")
    save_plot(fig3, "discount_avg_sales")
    image_info.append({"title": "値引き率ごとの平均売上", "url": "https://graph-api2.onrender.com/images/discount_avg_sales.png"})

    # 廃棄率ごとの平均売上
    fig4 = plt.figure()
    df.groupby("廃棄率")["金額"].mean().plot.bar(title="廃棄率ごとの平均売上")
    save_plot(fig4, "waste_avg_sales")
    image_info.append({"title": "廃棄率ごとの平均売上", "url": "https://graph-api2.onrender.com/images/waste_avg_sales.png"})

    # 気温と売上の関係
    fig5 = plt.figure()
    plt.scatter(df["最高気温"], df["金額"])
    plt.title("気温と売上の関係")
    plt.xlabel("最高気温")
    plt.ylabel("金額")
    save_plot(fig5, "temp_vs_sales")
    image_info.append({"title": "気温と売上の関係", "url": "https://graph-api2.onrender.com/images/temp_vs_sales.png"})

    # 売上トップ10商品
    fig6 = plt.figure()
    df.groupby("商品名")["金額"].sum().sort_values(ascending=False).head(10).plot.bar(title="売上金額トップ10商品")
    save_plot(fig6, "top10_sales")
    image_info.append({"title": "売上金額トップ10商品", "url": "https://graph-api2.onrender.com/images/top10_sales.png"})

    # 値引き率トップ10商品
    fig7 = plt.figure()
    df.groupby("商品名")["値引き率"].mean().sort_values(ascending=False).head(10).plot.bar(title="値引き率トップ10商品")
    save_plot(fig7, "top10_discount")
    image_info.append({"title": "値引き率トップ10商品", "url": "https://graph-api2.onrender.com/images/top10_discount.png"})

    # 廃棄率トップ10商品
    fig8 = plt.figure()
    df.groupby("商品名")["廃棄率"].mean().sort_values(ascending=False).head(10).plot.bar(title="廃棄率トップ10商品")
    save_plot(fig8, "top10_waste")
    image_info.append({"title": "廃棄率トップ10商品", "url": "https://graph-api2.onrender.com/images/top10_waste.png"})

    # 気温とサブカテゴリ別売上
    fig9 = plt.figure()
    sub_temp = df.groupby("サブカテゴリ")[["最高気温", "金額"]].mean()
    plt.scatter(sub_temp["最高気温"], sub_temp["金額"])
    plt.xlabel("最高気温（平均）")
    plt.ylabel("売上金額（平均）")
    plt.title("気温とサブカテゴリ別売上")
    save_plot(fig9, "temp_vs_subcat_sales")
    image_info.append({"title": "気温とサブカテゴリ別売上", "url": "https://graph-api2.onrender.com/images/temp_vs_subcat_sales.png"})

    # 曜日とサブカテゴリの売上傾向
    fig10 = plt.figure(figsize=(10, 6))
    weekday_sub = df.groupby(["曜日", "サブカテゴリ"])["金額"].mean().unstack()
    print("=== 曜日とサブカテゴリの平均売上 ===")
    print(weekday_sub.head())
    weekday_sub.plot(marker="o", ax=plt.gca())
    plt.title("曜日とサブカテゴリの売上傾向")
    plt.ylabel("平均売上")
    plt.xlabel("曜日")
    plt.xticks(rotation=45)
    save_plot(fig10, "weekday_vs_subcat")
    image_info.append({"title": "曜日とサブカテゴリの売上傾向", "url": "https://graph-api2.onrender.com/images/weekday_vs_subcat.png"})

    # サブカテゴリ別売上構成
    fig11 = plt.figure()
    df.groupby("サブカテゴリ")["金額"].sum().plot.pie(autopct="%1.1f%%", startangle=90)
    plt.title("サブカテゴリ別売上構成")
    plt.ylabel("")
    save_plot(fig11, "subcat_pie")
    image_info.append({"title": "サブカテゴリ別売上構成", "url": "https://graph-api2.onrender.com/images/subcat_pie.png"})

    # 曜日別売上構成
    fig12 = plt.figure()
    weekday_sum = df.groupby("曜日")["金額"].sum().reindex(weekday_order)
    weekday_sum.plot.pie(autopct="%1.1f%%", startangle=90)
    plt.title("曜日別売上構成")
    plt.ylabel("")
    save_plot(fig12, "weekday_pie")
    image_info.append({"title": "曜日別売上構成", "url": "https://graph-api2.onrender.com/images/weekday_pie.png"})

    return {"message": "グラフを生成しました", "image_urls": image_info}
