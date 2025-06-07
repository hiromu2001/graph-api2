from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import os
from io import StringIO

# レンダリング環境ではGUIがないのでこの設定
matplotlib.use("Agg")

# 日本語フォント設定 (.ttf に修正)
font_path = "fonts/NotoSansJP-Regular.ttf"
if os.path.exists(font_path):
    matplotlib.rcParams["font.family"] = "Noto Sans JP"
    from matplotlib import font_manager as fm
    fm.fontManager.addfont(font_path)
else:
    print("⚠️ フォントファイルが見つかりません。fonts/NotoSansJP-Regular.ttf を配置してください")

# FastAPI アプリ
app = FastAPI()

# images フォルダを静的公開
app.mount("/images", StaticFiles(directory="images"), name="images")

@app.post("/generate-graphs")
async def generate_graphs(file: UploadFile = File(...)):
    contents = await file.read()
    try:
        df = pd.read_csv(StringIO(contents.decode("utf-8")))
    except Exception as e:
        return JSONResponse(content={"error": f"CSV読み込み失敗: {str(e)}"}, status_code=400)

    # 必要なカラムの確認
    required_cols = ["販売数量", "単価", "サブカテゴリ", "曜日", "最高気温", "値引き率", "廃棄率", "商品名"]
    for col in required_cols:
        if col not in df.columns:
            return JSONResponse(content={"error": f"CSVに『{col}』の列が必要です"}, status_code=400)

    # 金額列を作成
    df["金額"] = df["単価"] * df["販売数量"]

    # 出力先ディレクトリ
    os.makedirs("images", exist_ok=True)

    # 保存用関数
    def save_plot(fig, name):
        path = f"images/{name}.png"
        fig.tight_layout()
        fig.savefig(path)
        plt.close(fig)
        return f"https://graph-api2.onrender.com/images/{name}.png"

    image_urls = {}

    # グラフ① サブカテゴリ別売上
    fig1 = plt.figure()
    df.groupby("サブカテゴリ")["金額"].sum().sort_values().plot.barh(title="サブカテゴリ別売上")
    image_urls["subcat_sales"] = save_plot(fig1, "subcat_sales")

    # グラフ② 曜日別売上
    fig2 = plt.figure()
    weekdays = ["月", "火", "水", "木", "金", "土", "日"]
    df.groupby("曜日")["金額"].sum().reindex(weekdays).plot.bar(title="曜日別売上")
    image_urls["weekday_sales"] = save_plot(fig2, "weekday_sales")

    # グラフ③ 気温と売上の散布図
    fig3 = plt.figure()
    plt.scatter(df["最高気温"], df["金額"])
    plt.title("気温と売上の関係")
    plt.xlabel("最高気温")
    plt.ylabel("売上金額")
    image_urls["temp_vs_sales"] = save_plot(fig3, "temp_vs_sales")

    # グラフ④ サブカテゴリ円グラフ
    fig4 = plt.figure()
    df.groupby("サブカテゴリ")["金額"].sum().plot.pie(autopct="%1.1f%%", startangle=90)
    plt.title("サブカテゴリ別売上構成")
    plt.ylabel("")
    image_urls["subcat_pie"] = save_plot(fig4, "subcat_pie")

    # グラフ⑤ 曜日円グラフ
    fig5 = plt.figure()
    weekday_sum = df.groupby("曜日")["金額"].sum().reindex(weekdays)
    weekday_sum.dropna(inplace=True)
    weekday_sum.plot.pie(autopct="%1.1f%%", startangle=90)
    plt.title("曜日別売上構成")
    plt.ylabel("")
    image_urls["weekday_pie"] = save_plot(fig5, "weekday_pie")

    return {"message": "グラフを生成しました", "images": image_urls}
