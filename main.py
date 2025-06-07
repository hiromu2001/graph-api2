from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
from io import StringIO

# アプリ初期化
app = FastAPI()

# 画像フォルダのマウント
if not os.path.exists("images"):
    os.makedirs("images")
app.mount("/images", StaticFiles(directory="images"), name="images")

# 日本語フォント設定（.ttf 使用）
FONT_PATH = "fonts/NotoSansJP-Regular.ttf"
if os.path.exists(FONT_PATH):
    fm.fontManager.addfont(FONT_PATH)
    plt.rcParams["font.family"] = "Noto Sans JP"
else:
    print("⚠️ フォントファイルが見つかりません。fonts/NotoSansJP-Regular.ttf を配置してください")

@app.post("/generate-graphs")
async def generate_graphs(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        df = pd.read_csv(StringIO(contents.decode("utf-8")))
    except Exception as e:
        return JSONResponse(content={"error": f"CSV読み込み失敗: {e}"}, status_code=400)

    # 必須カラムの確認
    required_cols = ["販売数量", "単価", "サブカテゴリ", "曜日", "最高気温", "値引き率", "廃棄率", "商品名"]
    for col in required_cols:
        if col not in df.columns:
            return JSONResponse(content={"error": f"CSVに『{col}』の列が必要です"}, status_code=400)

    df["金額"] = df["単価"] * df["販売数量"]

    image_urls = []

    def save_plot(fig, filename, title=None):
        if title:
            plt.title(title)
        filepath = f"images/{filename}.png"
        fig.tight_layout()
        fig.savefig(filepath)
        plt.close(fig)
        image_urls.append({
            "title": title or filename,
            "url": f"https://graph-api2.onrender.com/images/{filename}.png"
        })

    weekdays = ["月", "火", "水", "木", "金", "土", "日"]
    df["曜日"] = pd.Categorical(df["曜日"], categories=weekdays, ordered=True)

    # サブカテゴリ別売上
    fig1 = plt.figure()
    df.groupby("サブカテゴリ")["金額"].sum().sort_values().plot.barh()
    save_plot(fig1, "subcat_sales", "サブカテゴリ別売上")

    # 曜日別売上
    fig2 = plt.figure()
    df.groupby("曜日")["金額"].sum().reindex(weekdays).plot.bar()
    save_plot(fig2, "weekday_sales", "曜日別売上")

    # 値引き率ごとの平均売上
    fig3 = plt.figure()
    df.groupby("値引き率")["金額"].mean().plot.bar()
    save_plot(fig3, "discount_avg_sales", "値引き率ごとの平均売上")

    # 廃棄率ごとの平均売上
    fig4 = plt.figure()
    df.groupby("廃棄率")["金額"].mean().plot.bar()
    save_plot(fig4, "waste_avg_sales", "廃棄率ごとの平均売上")

    # 気温と売上の散布図
    fig5 = plt.figure()
    plt.scatter(df["最高気温"], df["金額"])
    plt.xlabel("最高気温")
    plt.ylabel("売上金額")
    save_plot(fig5, "temp_vs_sales", "気温と売上の関係")

    # 売上トップ10商品
    fig6 = plt.figure()
    df.groupby("商品名")["金額"].sum().sort_values(ascending=False).head(10).plot.bar()
    save_plot(fig6, "top10_sales", "売上金額トップ10商品")

    # 値引き率トップ10商品
    fig7 = plt.figure()
    df.groupby("商品名")["値引き率"].mean().sort_values(ascending=False).head(10).plot.bar()
    save_plot(fig7, "top10_discount", "値引き率トップ10商品")

    # 廃棄率トップ10商品
    fig8 = plt.figure()
    df.groupby("商品名")["廃棄率"].mean().sort_values(ascending=False).head(10).plot.bar()
    save_plot(fig8, "top10_waste", "廃棄率トップ10商品")

    # 気温×サブカテゴリ 散布図（平均）
    fig9 = plt.figure()
    sub_temp = df.groupby("サブカテゴリ")[["最高気温", "金額"]].mean()
    plt.scatter(sub_temp["最高気温"], sub_temp["金額"])
    plt.xlabel("最高気温（平均）")
    plt.ylabel("売上金額（平均）")
    save_plot(fig9, "temp_vs_subcat_sales", "気温とサブカテゴリ別売上")

    # 曜日×サブカテゴリ 売上傾向（折れ線）
    fig10 = plt.figure()
    weekday_sub = df.groupby(["曜日", "サブカテゴリ"])["金額"].mean().unstack()
    weekday_sub.plot(marker="o")
    plt.ylabel("平均売上")
    save_plot(fig10, "weekday_vs_subcat", "曜日とサブカテゴリの売上傾向")

    # サブカテゴリ円グラフ
    fig11 = plt.figure()
    df.groupby("サブカテゴリ")["金額"].sum().plot.pie(autopct="%1.1f%%", startangle=90)
    plt.ylabel("")
    save_plot(fig11, "subcat_pie", "サブカテゴリ別売上構成")

    # 曜日円グラフ
    fig12 = plt.figure()
    weekday_sum = df.groupby("曜日")["金額"].sum().reindex(weekdays)
    weekday_sum.dropna().plot.pie(autopct="%1.1f%%", startangle=90)
    plt.ylabel("")
    save_plot(fig12, "weekday_pie", "曜日別売上構成")

    return JSONResponse(content=image_urls)
