from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import os
from io import StringIO

matplotlib.use("Agg")

app = FastAPI()


@app.post("/generate-graphs")
async def generate_graphs(file: UploadFile = File(...)):
    contents = await file.read()
    try:
        df = pd.read_csv(StringIO(contents.decode("utf-8")))
    except UnicodeDecodeError:
        return JSONResponse(content={"error": "文字コードの読み込みに失敗しました。UTF-8形式で保存してください。"}, status_code=400)

    # カラム名の確認と前処理
    required_cols = ["販売数量", "単価", "サブカテゴリ", "曜日", "最高気温", "値引き率", "廃棄率"]
    for col in required_cols:
        if col not in df.columns:
            return JSONResponse(content={"error": f"CSVに『{col}』の列が必要です"}, status_code=400)

    df["金額"] = df["単価"] * df["販売数量"]

    os.makedirs("output", exist_ok=True)

    # 各種グラフの作成
    def save_plot(fig, name):
        fig.tight_layout()
        fig.savefig(f"output/{name}.png")
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

    # 売上トップ10商品
    fig6 = plt.figure()
    df.groupby("商品名")["金額"].sum().sort_values(ascending=False).head(10).plot.bar(title="売上金額トップ10商品")
    save_plot(fig6, "top10_sales")

    # 値引き率トップ10商品
    fig7 = plt.figure()
    df.groupby("商品名")["値引き率"].mean().sort_values(ascending=False).head(10).plot.bar(title="値引き率トップ10商品")
    save_plot(fig7, "top10_discount")

    # 廃棄率トップ10商品
    fig8 = plt.figure()
    df.groupby("商品名")["廃棄率"].mean().sort_values(ascending=False).head(10).plot.bar(title="廃棄率トップ10商品")
    save_plot(fig8, "top10_waste")

    # 気温×サブカテゴリ 散布図（平均）
    fig9 = plt.figure()
    sub_temp = df.groupby("サブカテゴリ")[["最高気温", "金額"]].mean()
    plt.scatter(sub_temp["最高気温"], sub_temp["金額"])
    plt.xlabel("最高気温（平均）")
    plt.ylabel("売上金額（平均）")
    plt.title("気温とサブカテゴリ別売上")
    save_plot(fig9, "temp_vs_subcat_sales")

    # 曜日×サブカテゴリ 売上散布図（平均）
    fig10 = plt.figure()
    weekday_sub = df.groupby(["曜日", "サブカテゴリ"])["金額"].mean().unstack()
    weekday_sub.plot(marker="o", title="曜日とサブカテゴリの売上傾向")
    plt.ylabel("平均売上")
    save_plot(fig10, "weekday_vs_subcat")

    # 円グラフ: サブカテゴリ売上構成
    fig11 = plt.figure()
    df.groupby("サブカテゴリ")["金額"].sum().plot.pie(autopct="%1.1f%%", startangle=90)
    plt.title("サブカテゴリ別売上構成")
    plt.ylabel("")
    save_plot(fig11, "subcat_pie")

    # 円グラフ: 曜日売上構成
    fig12 = plt.figure()
    weekday_sum = df.groupby("曜日")["金額"].sum().reindex(weekdays)
    weekday_sum.dropna(inplace=True)
    weekday_sum.plot.pie(autopct="%1.1f%%", startangle=90)
    plt.title("曜日別売上構成")
    plt.ylabel("")
    save_plot(fig12, "weekday_pie")

    return {"message": "グラフを生成しました。outputフォルダを確認してください。"}
