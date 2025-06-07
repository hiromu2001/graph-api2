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

    # 「単価」「販売数量」の列が存在するかチェック
    required_cols = ["単価", "販売数量"]
    for col in required_cols:
        if col not in df.columns:
            return {"error": f"CSVに『{col}』の列が必要です"}

    # カテゴリ列の判定
    if "カテゴリ" in df.columns:
        category_col = "カテゴリ"
    elif "サブカテゴリ" in df.columns:
        category_col = "サブカテゴリ"
    else:
        return {"error": "CSVに『カテゴリ』または『サブカテゴリ』の列が必要です"}

    if "曜日" not in df.columns:
        return {"error": "CSVに『曜日』の列が必要です"}

    # 売上金額を追加
    df["金額"] = df["単価"] * df["販売数量"]

    # グラフ出力用フォルダ
    output_dir = f"output_{uuid.uuid4().hex}"
    os.makedirs(output_dir, exist_ok=True)

    # グラフ1: サブカテゴリ別売上
    df.groupby(category_col)["金額"].sum().sort_values().plot(kind="barh", title="サブカテゴリ別売上")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "サブカテゴリ別売上.png"))
    plt.close()

    # グラフ2: 曜日別売上
    df.groupby("曜日")["金額"].sum().reindex(["月", "火", "水", "木", "金", "土", "日"]).plot(kind="bar", title="曜日別売上")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "曜日別売上.png"))
    plt.close()

    # グラフ3: 値引き率ごとの平均売上
    if "値引き率" in df.columns:
        df.groupby("値引き率")["金額"].mean().plot(kind="line", marker="o", title="値引き率ごとの平均売上")
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "値引き率ごとの平均売上.png"))
        plt.close()

        # グラフ: 値引き率トップ10商品
        df["商品別金額"] = df["金額"]
        top_discounted = df.sort_values("値引き率", ascending=False).head(10)
        top_discounted[["商品名", "値引き率"]].set_index("商品名").plot(kind="bar", title="値引き率トップ10商品")
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "値引き率トップ10商品.png"))
        plt.close()

    # グラフ4: 廃棄率ごとの平均売上
    if "廃棄率" in df.columns:
        df.groupby("廃棄率")["金額"].mean().plot(kind="line", marker="x", title="廃棄率ごとの平均売上")
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "廃棄率ごとの平均売上.png"))
        plt.close()

        # グラフ: 廃棄率トップ10商品
        top_disposal = df.sort_values("廃棄率", ascending=False).head(10)
        top_disposal[["商品名", "廃棄率"]].set_index("商品名").plot(kind="bar", title="廃棄率トップ10商品")
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "廃棄率トップ10商品.png"))
        plt.close()

    # グラフ5: 気温と売上の散布図
    if "気温" in df.columns:
        df.plot.scatter(x="気温", y="金額", title="気温と売上の散布図")
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "気温と売上の散布図.png"))
        plt.close()

        # グラフ: 気温×サブカテゴリ
        df.groupby(["気温", category_col])["金額"].sum().unstack().plot(title="気温とサブカテゴリ別売上")
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "気温とサブカテゴリ別売上.png"))
        plt.close()

    # グラフ6: 曜日×サブカテゴリ別散布図
    weekday_map = {"月":0, "火":1, "水":2, "木":3, "金":4, "土":5, "日":6}
    if df["曜日"].isin(weekday_map.keys()).all():
        df["曜日番号"] = df["曜日"].map(weekday_map)
        df.plot.scatter(x="曜日番号", y="金額", c="black", alpha=0.3, title="曜日と売上の散布図")
        plt.xticks(ticks=range(7), labels=["月", "火", "水", "木", "金", "土", "日"])
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "曜日と売上の散布図.png"))
        plt.close()

    # グラフ7: 売上金額トップ10商品
    top_sales = df.groupby("商品名")["金額"].sum().sort_values(ascending=False).head(10)
    top_sales.plot(kind="bar", title="売上金額トップ10商品")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "売上金額トップ10商品.png"))
    plt.close()

    # グラフ8: カテゴリ別売上構成（円グラフ）
    category_sales = df.groupby(category_col)["金額"].sum()
    category_sales.plot.pie(autopct="%1.1f%%", startangle=90, title="カテゴリ別売上構成比")
    plt.ylabel("")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "カテゴリ別売上構成比.png"))
    plt.close()

    # グラフ9: 曜日別売上構成（円グラフ）
    weekday_sales = df.groupby("曜日")["金額"].sum().reindex(["月", "火", "水", "木", "金", "土", "日"])
    weekday_sales.plot.pie(autopct="%1.1f%%", startangle=90, title="曜日別売上構成比")
    plt.ylabel("")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "曜日別売上構成比.png"))
    plt.close()

    # グラフ画像のパス一覧を返す（Dify等のツールと接続しやすく）
    result = {"graphs": []}
    for filename in os.listdir(output_dir):
        result["graphs"].append(f"/{output_dir}/{filename}")

    return result
