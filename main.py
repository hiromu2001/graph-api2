from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import os
from io import StringIO
import matplotlib.font_manager as fm

# 使用フォントを指定（.otf）
FONT_PATH = "fonts/NotoSansJP-Regular.otf"
if os.path.exists(FONT_PATH):
    fm.fontManager.addfont(FONT_PATH)
    matplotlib.rcParams["font.family"] = "Noto Sans JP"
else:
    print("⚠️ フォントファイルが見つかりません。fonts/NotoSansJP-Regular.otf を配置してください")

matplotlib.use("Agg")

# フォルダを事前に作成（存在しなければ作る）
os.makedirs("images", exist_ok=True)
os.makedirs("output", exist_ok=True)

app = FastAPI()

# 静的ファイルとして画像フォルダを公開（URLでアクセス可能に）
app.mount("/images", StaticFiles(directory="images"), name="images")

@app.post("/generate-graphs")
async def generate_graphs(file: UploadFile = File(...)):
    contents = await file.read()
    try:
        df = pd.read_csv(StringIO(contents.decode("utf-8")))
    except UnicodeDecodeError:
        return JSONResponse(content={"error": "文字コードの読み込みに失敗しました。UTF-8形式で保存してください。"}, status_code=400)
    except Exception as e:
        return JSONResponse(content={"error": f"CSV読み込み失敗: {str(e)}"}, status_code=400)

    # 必須カラムの確認
    required_cols = ["販売数量", "単価", "サブカテゴリ", "曜日", "最高気温", "値引き率", "廃棄率", "商品名"]
    for col in required_cols:
        if col not in df.columns:
            return JSONResponse(content={"error": f"CSVに『{col}』の列が必要です"}, status_code=400)

    # 金額を計算
    df["金額"] = df["単価"] * df["販売数量"]

    # 曜日順序定義
    weekdays = ["月", "火", "水", "木", "金", "土", "日"]

    # グラフ保存関数
    def save_plot(fig, name):
        path = f"images/{name}.png"
        fig.tight_layout()
        fig.savefig(path)
        plt.close(fig)
        return f"https://graph-api2.onrender.com/images/{name}.png"

    graph_urls = []

    # サブカテゴリ別売上
    fig = plt.figure()
    df.groupby("サブカテゴリ")["金額"].sum().sort_values().plot.barh(title="サブカテゴリ別売上")
    graph_urls.append(save_plot(fig, "subcat_sales"))

    # 曜日別売上
    fig = plt.figure()
    df.groupby("曜日")["金額"].sum().reindex(weekdays).plot.bar(title="曜日別売上")
    graph_urls.append(save_plot(fig, "weekday_sales"))

    # 値引き率ごとの平均売上
    fig = plt.figure()
    df.groupby("値引き率")["金額"].mean().plot.bar(title="値引き率ごとの平均売上")
    graph_urls.append(save_plot(fig, "discount_avg_sales"))

    # 廃棄率ごとの平均売上
    fig = plt.figure()
    df.groupby("廃棄率")["金額"].mean().plot.bar(title="廃棄率ごとの平均売上")
    graph_urls.append(save_plot(fig, "waste_avg_sales"))

    # 気温と売上の散布図
    fig = plt.figure()
    plt.scatter(df["最高気温"], df["金額"])
    plt.xlabel("最高気温")
    plt.ylabel("売上金額")
    plt.title("気温と売上の関係")
    graph_urls.append(save_plot(fig, "temp_vs_sales"))

    # 売上トップ10商品
    fig = plt.figure()
    df.groupby("商品名")["金額"].sum().sort_values(ascending=False).head(10).plot.bar(title="売上金額トップ10商品")
    graph_urls.append(save_plot(fig, "top10_sales"))

    # 値引き率トップ10商品
    fig = plt.figure()
    df.groupby("商品名")["値引き率"].mean().sort_values(ascending=False).head(10).plot.bar(title="値引き率トップ10商品")
    graph_urls.append(save_plot(fig, "top10_discount"))

    # 廃棄率トップ10商品
    fig = plt.figure()
    df.groupby("商品名")["廃棄率"].mean().sort_values(ascending=False).head(10).plot.bar(title="廃棄率トップ10商品")
    graph_urls.append(save_plot(fig, "top10_waste"))

    # 気温×サブカテゴリ
    fig = plt.figure()
    sub_temp = df.groupby("サブカテゴリ")[["最高気温", "金額"]].mean()
    plt.scatter(sub_temp["最高気温"], sub_temp["金額"])
    plt.xlabel("最高気温（平均）")
    plt.ylabel("売上金額（平均）")
    plt.title("気温とサブカテゴリ別売上")
    graph_urls.append(save_plot(fig, "temp_vs_subcat_sales"))

    # 曜日×サブカテゴリ
    fig = plt.figure()
    weekday_sub = df.groupby(["曜日", "サブカテゴリ"])["金額"].mean().unstack()
    weekday_sub.plot(marker="o", title="曜日とサブカテゴリの売上傾向")
    plt.ylabel("平均売上")
    graph_urls.append(save_plot(fig, "weekday_vs_subcat"))

    # サブカテゴリ別売上構成（円グラフ）
    fig = plt.figure()
    df.groupby("サブカテゴリ")["金額"].sum().plot.pie(autopct="%1.1f%%", startangle=90)
    plt.title("サブカテゴリ別売上構成")
    plt.ylabel("")
    graph_urls.append(save_plot(fig, "subcat_pie"))

    # 曜日別売上構成（円グラフ）
    fig = plt.figure()
    weekday_sum = df.groupby("曜日")["金額"].sum().reindex(weekdays)
    weekday_sum.dropna(inplace=True)
    weekday_sum.plot.pie(autopct="%1.1f%%", startangle=90)
    plt.title("曜日別売上構成")
    plt.ylabel("")
    graph_urls.append(save_plot(fig, "weekday_pie"))

    return {"message": "グラフを生成しました", "image_urls": graph_urls}
