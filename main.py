from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import io
import os
from datetime import datetime

matplotlib.use("Agg")

app = FastAPI()

@app.post("/generate-graphs")
async def generate_graphs(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode("utf-8")))

        required_columns = ["日付", "商品名", "サブカテゴリ", "売上数量", "単価", "値引き額", "廃棄額", "気温"]
        for col in required_columns:
            if col not in df.columns:
                return JSONResponse(content={"error": f"CSVに『{col}』の列が必要です"}, status_code=400)

        df["金額"] = df["単価"] * df["売上数量"]
        df["値引き率"] = df["値引き額"] / (df["単価"] * df["売上数量"] + 1e-6)
        df["廃棄率"] = df["廃棄額"] / (df["単価"] * df["売上数量"] + 1e-6)
        df["曜日"] = pd.to_datetime(df["日付"]).dt.day_name().map({
            'Monday': '月', 'Tuesday': '火', 'Wednesday': '水',
            'Thursday': '木', 'Friday': '金', 'Saturday': '土', 'Sunday': '日'
        })

        os.makedirs("graphs", exist_ok=True)
        plt.rcParams["font.family"] = "IPAPGothic"

        # グラフ1: サブカテゴリ別売上
        df.groupby("サブカテゴリ")["金額"].sum().sort_values().plot.barh(title="サブカテゴリ別売上")
        plt.tight_layout()
        plt.savefig("graphs/01_サブカテゴリ別売上.png")
        plt.clf()

        # グラフ2: 曜日別売上
        df.groupby("曜日")["金額"].sum().reindex(["月", "火", "水", "木", "金", "土", "日"]).plot.bar(title="曜日別売上")
        plt.tight_layout()
        plt.savefig("graphs/02_曜日別売上.png")
        plt.clf()

        # グラフ3: 値引き率ごとの平均売上
        df.groupby(pd.cut(df["値引き率"], bins=5))["金額"].mean().plot.bar(title="値引き率ごとの平均売上")
        plt.tight_layout()
        plt.savefig("graphs/03_値引き率別平均売上.png")
        plt.clf()

        # グラフ4: 廃棄率ごとの平均売上
        df.groupby(pd.cut(df["廃棄率"], bins=5))["金額"].mean().plot.bar(title="廃棄率ごとの平均売上")
        plt.tight_layout()
        plt.savefig("graphs/04_廃棄率別平均売上.png")
        plt.clf()

        # グラフ5: 気温と売上の散布図
        plt.scatter(df["気温"], df["金額"])
        plt.title("気温と売上の関係")
        plt.xlabel("気温")
        plt.ylabel("売上金額")
        plt.tight_layout()
        plt.savefig("graphs/05_気温と売上.png")
        plt.clf()

        # グラフ6: 売上金額トップ10商品
        df.groupby("商品名")["金額"].sum().sort_values(ascending=False).head(10).plot.barh(title="売上金額トップ10商品")
        plt.tight_layout()
        plt.savefig("graphs/06_売上金額TOP10商品.png")
        plt.clf()

        # グラフ7: 値引き率トップ10商品
        df.groupby("商品名")["値引き率"].mean().sort_values(ascending=False).head(10).plot.barh(title="値引き率TOP10商品")
        plt.tight_layout()
        plt.savefig("graphs/07_値引き率TOP10商品.png")
        plt.clf()

        # グラフ8: 廃棄率トップ10商品
        df.groupby("商品名")["廃棄率"].mean().sort_values(ascending=False).head(10).plot.barh(title="廃棄率TOP10商品")
        plt.tight_layout()
        plt.savefig("graphs/08_廃棄率TOP10商品.png")
        plt.clf()

        # グラフ9: サブカテゴリ別売上構成比（円グラフ）
        df.groupby("サブカテゴリ")["金額"].sum().plot.pie(autopct="%1.1f%%", startangle=90, title="サブカテゴリ別売上構成比")
        plt.ylabel("")
        plt.tight_layout()
        plt.savefig("graphs/09_サブカテゴリ別売上構成比.png")
        plt.clf()

        # グラフ10: 曜日別売上構成比（円グラフ）
        df.groupby("曜日")["金額"].sum().reindex(["月", "火", "水", "木", "金", "土", "日"]).plot.pie(autopct="%1.1f%%", startangle=90, title="曜日別売上構成比")
        plt.ylabel("")
        plt.tight_layout()
        plt.savefig("graphs/10_曜日別売上構成比.png")
        plt.clf()

        # グラフ11: 気温×サブカテゴリの散布図
        for cat in df["サブカテゴリ"].unique():
            subset = df[df["サブカテゴリ"] == cat]
            plt.scatter(subset["気温"], subset["金額"], label=cat)
        plt.legend()
        plt.title("気温とサブカテゴリ別売上")
        plt.xlabel("気温")
        plt.ylabel("売上金額")
        plt.tight_layout()
        plt.savefig("graphs/11_気温_サブカテゴリ別散布図.png")
        plt.clf()

        # グラフ12: 曜日×サブカテゴリの散布図
        for cat in df["サブカテゴリ"].unique():
            subset = df[df["サブカテゴリ"] == cat]
            subset["曜日番号"] = subset["曜日"].map({"月":0,"火":1,"水":2,"木":3,"金":4,"土":5,"日":6})
            plt.scatter(subset["曜日番号"], subset["金額"], label=cat)
        plt.legend()
        plt.title("曜日とサブカテゴリ別売上")
        plt.xlabel("曜日（0=月〜6=日）")
        plt.ylabel("売上金額")
        plt.tight_layout()
        plt.savefig("graphs/12_曜日_サブカテゴリ別散布図.png")
        plt.clf()

        return {"message": "グラフを生成しました"}

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
