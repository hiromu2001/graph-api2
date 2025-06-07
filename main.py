from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
import pandas as pd
import matplotlib.pyplot as plt
import os
import uuid
import shutil
from io import StringIO

app = FastAPI()

@app.post("/generate-graphs")
async def generate_graphs(file: UploadFile = File(...)):
    contents = await file.read()
    try:
        df = pd.read_csv(StringIO(contents.decode("utf-8")))
    except UnicodeDecodeError:
        return {"error": "CSVファイルの文字コードがUTF-8ではありません"}

    # 必須カラムの存在確認
    if "単価" not in df.columns or "販売数量" not in df.columns or "曜日" not in df.columns:
        return {"error": "CSVに『単価』『販売数量』『曜日』の列が必要です"}

    # 「カテゴリ」がなければ「サブカテゴリ」を使う
    if "カテゴリ" in df.columns:
        category_col = "カテゴリ"
    elif "サブカテゴリ" in df.columns:
        category_col = "サブカテゴリ"
    else:
        return {"error": "CSVに『カテゴリ』または『サブカテゴリ』の列が必要です"}

    df["金額"] = df["単価"] * df["販売数量"]

    output_dir = f"output_{uuid.uuid4().hex}"
    os.makedirs(output_dir, exist_ok=True)

    def save_plot(name):
        plt.tight_layout()
        path = os.path.join(output_dir, f"{name}.png")
        plt.savefig(path)
        plt.close()
        return f"/{output_dir}/{name}.png"

    urls = []

    # グラフ: サブカテゴリ別売上
    df.groupby(category_col)["金額"].sum().sort_values().plot(kind="barh", title="サブカテゴリ別売上")
    urls.append(save_plot("サブカテゴリ別売上"))

    # グラフ: 曜日別売上
    df.groupby("曜日")["金額"].sum().reindex(["月", "火", "水", "木", "金", "土", "日"]).plot(kind="bar", title="曜日別売上")
    urls.append(save_plot("曜日別売上"))

    # グラフ: 値引き率ごとの平均売上
    if "値引き率" in df.columns:
        df.groupby("値引き率")["金額"].mean().plot(marker="o", title="値引き率ごとの平均売上")
        urls.append(save_plot("値引き率ごとの平均売上"))

        top = df.sort_values("値引き率", ascending=False).head(10)
        top[["商品名", "値引き率"]].set_index("商品名").plot(kind="bar", title="値引き率トップ10商品")
        urls.append(save_plot("値引き率トップ10商品"))

    # グラフ: 廃棄率ごとの平均売上
    if "廃棄率" in df.columns:
        df.groupby("廃棄率")["金額"].mean().plot(marker="x", title="廃棄率ごとの平均売上")
        urls.append(save_plot("廃棄率ごとの平均売上"))

        top = df.sort_values("廃棄率", ascending=False).head(10)
        top[["商品名", "廃棄率"]].set_index("商品名").plot(kind="bar", title="廃棄率トップ10商品")
        urls.append(save_plot("廃棄率トップ10商品"))

    # グラフ: 気温と売上の散布図
    if "気温" in df.columns:
        df.plot.scatter(x="気温", y="金額", title="気温と売上の散布図")
        urls.append(save_plot("気温と売上の散布図"))

        df.groupby(["気温", category_col])["金額"].sum().unstack().plot(title="気温とサブカテゴリ別売上")
        urls.append(save_plot("気温とサブカテゴリ別売上"))

    # グラフ: 曜日×サブカテゴリの散布図
    weekday_map = {"月":0, "火":1, "水":2, "木":3, "金":4, "土":5, "日":6}
    if df["曜日"].isin(weekday_map.keys()).all():
        df["曜日番号"] = df["曜日"].map(weekday_map)
        df.plot.scatter(x="曜日番号", y="金額", c="black", alpha=0.3, title="曜日と売上の散布図")
        plt.xticks(ticks=range(7), labels=["月", "火", "水", "木", "金", "土", "日"])
        urls.append(save_plot("曜日と売上の散布図"))

    # グラフ: 売上金額トップ10商品
    df.groupby("商品名")["金額"].sum().sort_values(ascending=False).head(10).plot(kind="bar", title="売上金額トップ10商品")
    urls.append(save_plot("売上金額トップ10商品"))

    # 円グラフ: カテゴリ別構成
    df.groupby(category_col)["金額"].sum().plot.pie(autopct="%1.1f%%", startangle=90, title="カテゴリ別売上構成比")
    plt.ylabel("")
    urls.append(save_plot("カテゴリ別売上構成比"))

    # 円グラフ: 曜日別構成
    df.groupby("曜日")["金額"].sum().reindex(["月", "火", "水", "木", "金", "土", "日"]).plot.pie(autopct="%1.1f%%", startangle=90, title="曜日別売上構成比")
    plt.ylabel("")
    urls.append(save_plot("曜日別売上構成比"))

    return {"graphs": urls}
