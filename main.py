from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib
import os
from io import StringIO

# フォント設定
FONT_PATH = "fonts/NotoSansJP-Regular.ttf"
if os.path.exists(FONT_PATH):
    fm.fontManager.addfont(FONT_PATH)
    matplotlib.rc("font", family="Noto Sans JP")
else:
    print(f"⚠️ フォントファイルが見つかりません。{FONT_PATH} を配置してください")

# バックエンド描画エンジン設定
matplotlib.use("Agg")

# アプリ初期化
app = FastAPI()

# 画像フォルダのマウント
os.makedirs("images", exist_ok=True)
app.mount("/images", StaticFiles(directory="images"), name="images")

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
    weekdays = ["月", "火", "水", "木", "金", "土", "日"]

    def save_plot(fig, name):
        path = f"images/{name}.png"
        fig.tight_layout()
        fig.savefig(path)
        plt.close(fig)
        return f"https://graph-api2.onrender.com/images/{name}.png"

    urls = {}

    # グラフ①: サブカテゴリ別売上
    fig1 = plt.figure()
    df.groupby("サブカテゴリ")["金額"].sum().sort_values().plot.barh(title="サブカテゴリ別売上")
    urls["subcat_sales"] = save_plot(fig1, "subcat_sales")

    # グラフ②: 曜日別売上
    fig2 = plt.figure()
    df.groupby("曜日")["金額"].sum().reindex(weekdays).plot.bar(title="曜日別売上")
    urls["weekday_sales"] = save_plot(fig2, "weekday_sales")

    # グラフ③: 値引き率ごとの平均売上
    fig3 = plt.figure()
    df.groupby("値引き率")["金額"].mean().plot.bar(title="値引き率ごとの平均売上")
    urls["discount_avg_sales"] = save_plot(fig3, "discount_avg_sales")

    # グラフ④: 廃棄率ごとの平均売上
    fig4 = plt.figure()
    df.groupby("廃棄率")["金額"].mean().plot.bar(title="廃棄率ごとの平均売上")
    urls["waste_avg_sales"] = save_plot(fig4, "waste_avg_sales")

    # グラフ⑤: 気温と売上の散布図
    fig5 = plt.figure()
    plt.scatter(df["最高気温"], df["金額"])
    plt.xlabel("最高気温")
    plt.ylabel("売上金額")
    plt.title("気温と売上の関係")
    urls["temp_vs_sales"] = save_plot(fig5, "temp_vs_sales")

    # グラフ⑥: 売上トップ10商品
    fig6 = plt.figure()
    df.groupby("商品名")["金額"].sum().sort_values(ascending=False).head(10).plot.bar(title="売上金額トップ10商品")
    urls["top10_sales"] = save_plot(fig6, "top10_sales")

    # グラフ⑦: 値引き率トップ10商品
    fig7 = plt.figure()
    df.groupby("商品名")["値引き率"].mean().sort_values(ascending=False).head(10).plot.bar(title="値引き率トップ10商品")
    urls["top10_discount"] = save_plot(fig7, "top10_discount")

    # グラフ⑧: 廃棄率トップ10商品
    fig8 = plt.figure()
    df.groupby("商品名")["廃棄率"].mean().sort_values(ascending=False).head(10).plot.bar(title="廃棄率トップ10商品")
    urls["top10_waste"] = save_plot(fig8, "top10_waste")

    # グラフ⑨: 気温×サブカテゴリ 散布図
    fig9 = plt.figure()
    sub_temp = df.groupby("サブカテゴリ")[["最高気温", "金額"]].mean()
    plt.scatter(sub_temp["最高気温"], sub_temp["金額"])
    plt.xlabel("最高気温（平均）")
    plt.ylabel("売上金額（平均）")
    plt.title("気温とサブカテゴリ別売上")
    urls["temp_vs_subcat_sales"] = save_plot(fig9, "temp_vs_subcat_sales")

    # グラフ⑩: 曜日×サブカテゴリ 売上傾向
    fig10 = plt.figure()
    weekday_sub = df.groupby(["曜日", "サブカテゴリ"])["金額"].mean().unstack()
    weekday_sub.plot(marker="o", title="曜日とサブカテゴリの売上傾向")
    plt.ylabel("平均売上")
    urls["weekday_vs_subcat"] = save_plot(fig10, "weekday_vs_subcat")

    # グラフ⑪: 円グラフ（サブカテゴリ）
    fig11 = plt.figure()
    df.groupby("サブカテゴリ")["金額"].sum().plot.pie(autopct="%1.1f%%", startangle=90)
    plt.title("サブカテゴリ別売上構成")
    plt.ylabel("")
    urls["subcat_pie"] = save_plot(fig11, "subcat_pie")

    # グラフ⑫: 円グラフ（曜日）
    fig12 = plt.figure()
    weekday_sum = df.groupby("曜日")["金額"].sum().reindex(weekdays)
    weekday_sum.dropna(inplace=True)
    weekday_sum.plot.pie(autopct="%1.1f%%", startangle=90)
    plt.title("曜日別売上構成")
    plt.ylabel("")
    urls["weekday_pie"] = save_plot(fig12, "weekday_pie")

    return {
        "message": "グラフを生成しました。",
        "image_urls": urls
    }
