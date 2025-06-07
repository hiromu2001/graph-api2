from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

app = FastAPI()

# 静的ファイル（imagesディレクトリ）を公開
if not os.path.exists("images"):
    os.makedirs("images")
app.mount("/images", StaticFiles(directory="images"), name="images")

# CSVを保存するファイル名（固定）
csv_path = "売上データ_1週間_単価追加_utf8.csv"

def save_uploaded_file(file: UploadFile):
    with open(csv_path, "wb") as buffer:
        buffer.write(file.file.read())

def generate_all_graphs():
    df = pd.read_csv(csv_path)

    image_info = []

    # 1. サブカテゴリ別売上
    try:
        df.groupby("サブカテゴリ")["金額"].sum().sort_values().plot.barh()
        plt.title("サブカテゴリ別売上")
        path = "images/subcat_sales.png"
        plt.tight_layout()
        plt.savefig(path)
        plt.clf()
        image_info.append({"title": "サブカテゴリ別売上", "url": f"/images/{os.path.basename(path)}"})
    except Exception as e:
        print("Error in サブカテゴリ別売上:", e)

    # 2. 曜日別売上
    try:
        weekday_order = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"]
        weekday_sales = df.groupby("曜日")["金額"].sum().reindex(weekday_order)
        weekday_sales.plot(kind="bar", title="曜日別売上")
        path = "images/weekday_sales.png"
        plt.tight_layout()
        plt.savefig(path)
        plt.clf()
        image_info.append({"title": "曜日別売上", "url": f"/images/{os.path.basename(path)}"})
    except Exception as e:
        print("Error in 曜日別売上:", e)

    # 3. 値引き率ごとの平均売上
    try:
        df.groupby("値引き率")["金額"].mean().plot.bar(title="値引き率ごとの平均売上")
        path = "images/discount_avg_sales.png"
        plt.tight_layout()
        plt.savefig(path)
        plt.clf()
        image_info.append({"title": "値引き率ごとの平均売上", "url": f"/images/{os.path.basename(path)}"})
    except Exception as e:
        print("Error in 値引き率ごとの平均売上:", e)

    # 4. 廃棄率ごとの平均売上
    try:
        df.groupby("廃棄率")["金額"].mean().plot.bar(title="廃棄率ごとの平均売上")
        path = "images/waste_avg_sales.png"
        plt.tight_layout()
        plt.savefig(path)
        plt.clf()
        image_info.append({"title": "廃棄率ごとの平均売上", "url": f"/images/{os.path.basename(path)}"})
    except Exception as e:
        print("Error in 廃棄率ごとの平均売上:", e)

    # 5. 気温と売上の関係
    try:
        sns.scatterplot(data=df, x="気温", y="金額")
        plt.title("気温と売上の関係")
        path = "images/temp_vs_sales.png"
        plt.tight_layout()
        plt.savefig(path)
        plt.clf()
        image_info.append({"title": "気温と売上の関係", "url": f"/images/{os.path.basename(path)}"})
    except Exception as e:
        print("Error in 気温と売上の関係:", e)

    # 6. 売上金額トップ10商品
    try:
        df.groupby("商品名")["金額"].sum().sort_values(ascending=False).head(10).plot.bar()
        plt.title("売上金額トップ10商品")
        path = "images/top10_sales.png"
        plt.tight_layout()
        plt.savefig(path)
        plt.clf()
        image_info.append({"title": "売上金額トップ10商品", "url": f"/images/{os.path.basename(path)}"})
    except Exception as e:
        print("Error in 売上金額トップ10商品:", e)

    # 7. 値引き率トップ10商品
    try:
        df.groupby("商品名")["値引き率"].mean().sort_values(ascending=False).head(10).plot.bar()
        plt.title("値引き率トップ10商品")
        path = "images/top10_discount.png"
        plt.tight_layout()
        plt.savefig(path)
        plt.clf()
        image_info.append({"title": "値引き率トップ10商品", "url": f"/images/{os.path.basename(path)}"})
    except Exception as e:
        print("Error in 値引き率トップ10商品:", e)

    # 8. 廃棄率トップ10商品
    try:
        df.groupby("商品名")["廃棄率"].mean().sort_values(ascending=False).head(10).plot.bar()
        plt.title("廃棄率トップ10商品")
        path = "images/top10_waste.png"
        plt.tight_layout()
        plt.savefig(path)
        plt.clf()
        image_info.append({"title": "廃棄率トップ10商品", "url": f"/images/{os.path.basename(path)}"})
    except Exception as e:
        print("Error in 廃棄率トップ10商品:", e)

    # 9. 気温とサブカテゴリ別売上
    try:
        sns.scatterplot(data=df, x="気温", y="金額", hue="サブカテゴリ")
        plt.title("気温とサブカテゴリ別売上")
        path = "images/temp_vs_subcat_sales.png"
        plt.tight_layout()
        plt.savefig(path)
        plt.clf()
        image_info.append({"title": "気温とサブカテゴリ別売上", "url": f"/images/{os.path.basename(path)}"})
    except Exception as e:
        print("Error in 気温とサブカテゴリ別売上:", e)

    # 10. 曜日とサブカテゴリの売上傾向
    try:
        pivot = df.pivot_table(index="曜日", columns="サブカテゴリ", values="金額", aggfunc="sum")
        pivot = pivot.fillna(0)
        pivot.plot(kind="bar", stacked=True)
        plt.title("曜日とサブカテゴリの売上傾向")
        path = "images/weekday_vs_subcat.png"
        plt.tight_layout()
        plt.savefig(path)
        plt.clf()
        image_info.append({"title": "曜日とサブカテゴリの売上傾向", "url": f"/images/{os.path.basename(path)}"})
    except Exception as e:
        print("Error in 曜日とサブカテゴリの売上傾向:", e)

    # 11. サブカテゴリ別売上構成（円グラフ）
    try:
        df.groupby("サブカテゴリ")["金額"].sum().plot.pie(autopct="%1.1f%%")
        plt.title("サブカテゴリ別売上構成")
        path = "images/subcat_pie.png"
        plt.tight_layout()
        plt.savefig(path)
        plt.clf()
        image_info.append({"title": "サブカテゴリ別売上構成", "url": f"/images/{os.path.basename(path)}"})
    except Exception as e:
        print("Error in サブカテゴリ別売上構成:", e)

    # 12. 曜日別売上構成（円グラフ）
    try:
        df.groupby("曜日")["金額"].sum().reindex(weekday_order).plot.pie(autopct="%1.1f%%")
        plt.title("曜日別売上構成")
        path = "images/weekday_pie.png"
        plt.tight_layout()
        plt.savefig(path)
        plt.clf()
        image_info.append({"title": "曜日別売上構成", "url": f"/images/{os.path.basename(path)}"})
    except Exception as e:
        print("Error in 曜日別売上構成:", e)

    return image_info

@app.post("/upload-and-generate")
async def upload_and_generate(file: UploadFile = File(...)):
    try:
        save_uploaded_file(file)
        images = generate_all_graphs()
        return JSONResponse(content=images)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
