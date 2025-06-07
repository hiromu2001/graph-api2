from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import matplotlib.font_manager as fm
import os
from io import StringIO

# 非GUI環境でも描画可能にする
matplotlib.use("Agg")

# 日本語フォント設定（プロジェクト内のフォントを使用）
font_path = "./fonts/NotoSansJP-Regular.otf"
if os.path.exists(font_path):
    font_prop = fm.FontProperties(fname=font_path)
    plt.rcParams["font.family"] = font_prop.get_name()
else:
    print("⚠️ フォントファイルが見つかりません。fonts/NotoSansJP-Regular.otf を配置してください")

app = FastAPI()

@app.post("/generate-graphs")
async def generate_graphs(file: UploadFile = File(...)):
    contents = await file.read()
    try:
        df = pd.read_csv(StringIO(contents.decode("utf-8")))
    except Exception as e:
        return JSONResponse(content={"error": f"CSV読み込み失敗: {str(e)}"}, status_code=400)

    # 必要なカラム確認
    required_cols = ["販売数量", "単価", "サブカテゴリ", "曜日", "最高気温", "値引き率", "廃棄率", "商品名"]
    for col in required_cols:
        if col not in df.columns:
            return JSONResponse(content={"error": f"CSVに『{col}』の列が必要です"}, status_code=400)

    # 金額計算
    df["金額"] = df["単価"] * df["販売数量"]

    # 出力フォルダ作成
    os.makedirs("output", exist_ok=True)

    image_urls = []

    # グラフ保存関数
    def save_plot(fig, name):
        fig.tight_layout()
        path = f"output/{name}.png"
        fig.savefig(path)
        plt.close(fig)
        image_urls.append(f"https://graph-api2.onrender.com/images/{name}.png")

    weekdays = ["月", "火", "水", "木", "金", "土", "日"]

    # 各グラフを作成して保存
    save_plot(df.groupby("サブカテゴリ")["金額"].sum().sort_values().plot.barh(title="サブカテゴリ別売上").get_figure(), "subcat_sales")
    save_plot(df.groupby("曜日")["金額"].sum().reindex(weekdays).plot.bar(title="曜日別売上").get_figure(), "weekday_sales")
    save_plot(df.groupby("値引き率")["金額"].mean().plot.bar(title="値引き率ごとの平均売上").get_figure(), "discount_avg_sales")
    save_plot(df.groupby("廃棄率")["金額"].mean().plot.bar(title="廃棄率ごとの平均売上").get_figure(), "waste_avg_sales")

    # 気温と売上散布図
    fig5 = plt.figure()
    plt.scatter(df["最高気温"], df["金額"])
    plt.xlabel("最高気温")
    plt.ylabel("売上金額")
    plt.title("気温と売上の関係")
    save_plot(fig5, "temp_vs_sales")

    # トップ10商品
    save_plot(df.groupby("商品名")["金額"].sum().sort_values(ascending=False).head(10).plot.bar(title="売上金額トップ10商品").get_figure(), "top10_sales")
    save_plot(df.groupby("商品名")["値引き率"].mean().sort_values(ascending=False).head(10).plot.bar(title="値引き率トップ10商品").get_figure(), "top10_discount")
    save_plot(df.groupby("商品名")["廃棄率"].mean().sort_values(ascending=False).head(10).plot.bar(title="廃棄率トップ10商品").get_figure(), "top10_waste")

    # 気温×サブカテゴリ
    fig9 = plt.figure()
    sub_temp = df.groupby("サブカテゴリ")[["最高気温", "金額"]].mean()
    plt.scatter(sub_temp["最高気温"], sub_temp["金額"])
    plt.xlabel("最高気温（平均）")
    plt.ylabel("売上金額（平均）")
    plt.title("気温とサブカテゴリ別売上")
    save_plot(fig9, "temp_vs_subcat_sales")

    # 曜日×サブカテゴリ
    fig10 = plt.figure()
    weekday_sub = df.groupby(["曜日", "サブカテゴリ"])["金額"].mean().unstack()
    weekday_sub.plot(marker="o", title="曜日とサブカテゴリの売上傾向")
    plt.ylabel("平均売上")
    save_plot(fig10, "weekday_vs_subcat")

    # 円グラフ
    fig11 = plt.figure()
    df.groupby("サブカテゴリ")["金額"].sum().plot.pie(autopct="%1.1f%%", startangle=90)
    plt.title("サブカテゴリ別売上構成")
    plt.ylabel("")
    save_plot(fig11, "subcat_pie")

    fig12 = plt.figure()
    weekday_sum = df.groupby("曜日")["金額"].sum().reindex(weekdays)
    weekday_sum.dropna(inplace=True)
    weekday_sum.plot.pie(autopct="%1.1f%%", startangle=90)
    plt.title("曜日別売上構成")
    plt.ylabel("")
    save_plot(fig12, "weekday_pie")

    return {"message": "グラフを生成しました", "image_urls": image_urls}
