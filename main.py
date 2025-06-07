from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import pandas as pd
import matplotlib.pyplot as plt
import os
from io import StringIO

app = FastAPI()

@app.post("/generate-graphs")
async def generate_graphs(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        df = pd.read_csv(StringIO(contents.decode("utf-8")))

        # 必須カラムチェック
        required_columns = ["日付", "商品名", "サブカテゴリ", "曜日", "売上数量", "単価", "気温", "値引き率", "廃棄率"]
        for col in required_columns:
            if col not in df.columns:
                return JSONResponse(status_code=400, content={"error": f"CSVに『{col}』の列が必要です"})

        # 金額列を追加
        df["金額"] = df["売上数量"] * df["単価"]

        # グラフ出力ディレクトリ作成
        os.makedirs("static", exist_ok=True)

        # サブカテゴリ別売上
        df.groupby("サブカテゴリ")["金額"].sum().sort_values().plot.barh(title="サブカテゴリ別売上")
        plt.tight_layout()
        plt.savefig("static/subcategory_sales.png")
        plt.clf()

        # 曜日別売上
        df.groupby("曜日")["金額"].sum().reindex(["月", "火", "水", "木", "金", "土", "日"]).dropna().plot.bar(title="曜日別売上")
        plt.tight_layout()
        plt.savefig("static/weekday_sales.png")
        plt.clf()

        # 値引き率ごとの平均売上
        df.groupby("値引き率")["金額"].mean().plot.bar(title="値引き率ごとの平均売上")
        plt.tight_layout()
        plt.savefig("static/avg_sales_by_discount.png")
        plt.clf()

        # 廃棄率ごとの平均売上
        df.groupby("廃棄率")["金額"].mean().plot.bar(title="廃棄率ごとの平均売上")
        plt.tight_layout()
        plt.savefig("static/avg_sales_by_disposal.png")
        plt.clf()

        # 気温と売上の散布図
        plt.scatter(df["気温"], df["金額"])
        plt.xlabel("気温")
        plt.ylabel("売上金額")
        plt.title("気温と売上の散布図")
        plt.tight_layout()
        plt.savefig("static/temp_vs_sales.png")
        plt.clf()

        # 売上金額トップ10商品
        df.groupby("商品名")["金額"].sum().sort_values(ascending=False).head(10).plot.bar(title="売上金額トップ10商品")
        plt.tight_layout()
        plt.savefig("static/top10_sales.png")
        plt.clf()

        # 値引き率トップ10商品
        df.groupby("商品名")["値引き率"].mean().sort_values(ascending=False).head(10).plot.bar(title="値引き率トップ10商品")
        plt.tight_layout()
        plt.savefig("static/top10_discount.png")
        plt.clf()

        # 廃棄率トップ10商品
        df.groupby("商品名")["廃棄率"].mean().sort_values(ascending=False).head(10).plot.bar(title="廃棄率トップ10商品")
        plt.tight_layout()
        plt.savefig("static/top10_disposal.png")
        plt.clf()

        # サブカテゴリ別売上構成比（円グラフ）
        df.groupby("サブカテゴリ")["金額"].sum().dropna().plot.pie(autopct="%1.1f%%", startangle=90, title="サブカテゴリ別売上構成比")
        plt.ylabel("")
        plt.tight_layout()
        plt.savefig("static/subcategory_sales_pie.png")
        plt.clf()

        # 曜日別売上構成比（円グラフ）
        df.groupby("曜日")["金額"].sum().reindex(["月", "火", "水", "木", "金", "土", "日"]).dropna().plot.pie(autopct="%1.1f%%", startangle=90, title="曜日別売上構成比")
        plt.ylabel("")
        plt.tight_layout()
        plt.savefig("static/weekday_sales_pie.png")
        plt.clf()

        # 気温とサブカテゴリの散布図（例：カテゴリ別に色分けはここでは省略）
        for cat in df["サブカテゴリ"].unique():
            subset = df[df["サブカテゴリ"] == cat]
            plt.scatter(subset["気温"], subset["金額"], label=cat)
        plt.xlabel("気温")
        plt.ylabel("売上")
        plt.title("気温とサブカテゴリ別売上の散布図")
        plt.legend()
        plt.tight_layout()
        plt.savefig("static/temp_vs_subcategory.png")
        plt.clf()

        # 曜日とサブカテゴリの散布図（例：曜日別の位置で色分け）
        for cat in df["サブカテゴリ"].unique():
            subset = df[df["サブカテゴリ"] == cat]
            subset["曜日_index"] = subset["曜日"].map({"月":0, "火":1, "水":2, "木":3, "金":4, "土":5, "日":6})
            plt.scatter(subset["曜日_index"], subset["金額"], label=cat)
        plt.xlabel("曜日（0=月, ..., 6=日）")
        plt.ylabel("売上")
        plt.title("曜日とサブカテゴリ別売上の散布図")
        plt.legend()
        plt.tight_layout()
        plt.savefig("static/weekday_vs_subcategory.png")
        plt.clf()

        return {"message": "グラフを生成しました", "files": os.listdir("static")}

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

