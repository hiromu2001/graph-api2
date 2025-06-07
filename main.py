from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import uuid

app = FastAPI()

# ディレクトリ作成
IMAGE_DIR = "images"
os.makedirs(IMAGE_DIR, exist_ok=True)

# matplotlibの日本語表示対策
plt.rcParams["font.family"] = "IPAPGothic"

# アップロード＆グラフ生成統合エンドポイント
@app.post("/upload-and-generate")
def upload_and_generate(file: UploadFile = File(...)):
    try:
        df = pd.read_csv(file.file)
    except Exception as e:
        return JSONResponse(content={"error": f"CSV読み込みエラー: {str(e)}"}, status_code=400)

    if "金額" not in df.columns:
        return JSONResponse(content={"error": "CSVに'金額'列が存在しません。"}, status_code=400)

    image_urls = []

    def save_plot(title):
        filename = f"{uuid.uuid4()}.png"
        path = os.path.join(IMAGE_DIR, filename)
        plt.savefig(path)
        plt.close()
        image_urls.append({"title": title, "url": f"https://graph-api2.onrender.com/images/{filename}"})

    try:
        # サブカテゴリ別売上
        df.groupby("サブカテゴリ")['金額'].sum().plot.bar(title="サブカテゴリ別売上")
        save_plot("サブカテゴリ別売上")
    except Exception as e:
        print("Error in サブカテゴリ別売上:", e)

    try:
        # 曜日別売上
        weekday_order = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"]
        df.groupby("曜日")["金額"].sum().reindex(weekday_order).plot.bar(title="曜日別売上")
        save_plot("曜日別売上")
    except Exception as e:
        print("Error in 曜日別売上:", e)

    try:
        # 値引き率ごとの平均売上
        df.groupby("値引き率")["金額"].mean().plot.bar(title="値引き率ごとの平均売上")
        save_plot("値引き率ごとの平均売上")
    except Exception as e:
        print("Error in 値引き率ごとの平均売上:", e)

    try:
        # 廃棄率ごとの平均売上
        df.groupby("廃棄率")["金額"].mean().plot.bar(title="廃棄率ごとの平均売上")
        save_plot("廃棄率ごとの平均売上")
    except Exception as e:
        print("Error in 廃棄率ごとの平均売上:", e)

    try:
        # 気温と売上の関係
        sns.scatterplot(data=df, x="気温", y="金額").set(title="気温と売上の関係")
        save_plot("気温と売上の関係")
    except Exception as e:
        print("Error in 気温と売上の関係:", e)

    try:
        # 売上金額トップ10商品
        df.groupby("商品名")["金額"].sum().sort_values(ascending=False).head(10).plot.bar(title="売上金額トップ10商品")
        save_plot("売上金額トップ10商品")
    except Exception as e:
        print("Error in 売上金額トップ10商品:", e)

    try:
        # 気温とサブカテゴリ別売上
        sns.scatterplot(data=df, x="気温", y="金額", hue="サブカテゴリ").set(title="気温とサブカテゴリ別売上")
        save_plot("気温とサブカテゴリ別売上")
    except Exception as e:
        print("Error in 気温とサブカテゴリ別売上:", e)

    try:
        # 曜日とサブカテゴリの売上傾向
        sns.barplot(data=df, x="曜日", y="金額", hue="サブカテゴリ", estimator=sum).set(title="曜日とサブカテゴリの売上傾向")
        save_plot("曜日とサブカテゴリの売上傾向")
    except Exception as e:
        print("Error in 曜日とサブカテゴリの売上傾向:", e)

    try:
        # サブカテゴリ別売上構成
        df.groupby("サブカテゴリ")["金額"].sum().plot.pie(title="サブカテゴリ別売上構成", autopct='%1.1f%%')
        save_plot("サブカテゴリ別売上構成")
    except Exception as e:
        print("Error in サブカテゴリ別売上構成:", e)

    try:
        # 曜日別売上構成
        df.groupby("曜日")["金額"].sum().reindex(weekday_order).plot.pie(title="曜日別売上構成", autopct='%1.1f%%')
        save_plot("曜日別売上構成")
    except Exception as e:
        print("Error in 曜日別売上構成:", e)

    # 以下追加分グラフ
    try:
        # 平均気温と平均廃棄率の関係
        temp_dispose = df.groupby("気温")["廃棄率"].mean()
        temp_dispose.plot(title="平均気温と平均廃棄率の関係")
        save_plot("平均気温と平均廃棄率の関係")
    except Exception as e:
        print("Error in 平均気温と平均廃棄率の関係:", e)

    try:
        # 単価と値引き率の関係
        sns.scatterplot(data=df, x="単価", y="値引き率").set(title="単価と値引き率の関係")
        save_plot("単価と値引き率の関係")
    except Exception as e:
        print("Error in 単価と値引き率の関係:", e)

    try:
        # 廃棄率ごとの販売点数平均
        df.groupby("廃棄率")["販売点数"].mean().plot.bar(title="廃棄率ごとの販売点数平均")
        save_plot("廃棄率ごとの販売点数平均")
    except Exception as e:
        print("Error in 廃棄率ごとの販売点数平均:", e)

    try:
        # 商品別平均単価
        df.groupby("商品名")["単価"].mean().sort_values(ascending=False).head(10).plot.bar(title="商品別平均単価")
        save_plot("商品別平均単価")
    except Exception as e:
        print("Error in 商品別平均単価:", e)

    return JSONResponse(content=image_urls)
