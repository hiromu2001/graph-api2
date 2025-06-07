from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd
import matplotlib.pyplot as plt
import os

# アプリと画像ディレクトリの設定
app = FastAPI()

if not os.path.exists("images"):
    os.makedirs("images")

app.mount("/images", StaticFiles(directory="images"), name="images")

# 読み込みと前処理
def load_data():
    csv_path = "売上データ_1週間_単価追加_utf8.csv"
    df = pd.read_csv(csv_path)
    print("=== CSV 読み込み成功 ===")
    print(df.head())
    
    # 必要な列を確認
    print("=== カラム一覧 ===")
    print(df.columns)

    # 必要な前処理
    df["金額"] = df["金額"].fillna(0)
    df["曜日"] = df["曜日"].fillna("不明")
    df["サブカテゴリ"] = df["サブカテゴリ"].fillna("不明")
    return df

@app.post("/generate-graphs")
def generate_graphs():
    df = load_data()
    image_infos = []

    weekdays = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"]

    # サブカテゴリ別売上
    subcat_group = df.groupby("サブカテゴリ")["金額"].sum()
    if not subcat_group.empty:
        subcat_group.sort_values().plot.barh(title="サブカテゴリ別売上")
        plt.tight_layout()
        path = "images/subcat_sales.png"
        plt.savefig(path)
        plt.close()
        image_infos.append({"title": "サブカテゴリ別売上", "url": f"/images/subcat_sales.png"})

    # 曜日別売上
    weekday_sales = df.groupby("曜日")["金額"].sum().reindex(weekdays)
    print("=== 曜日ごとの売上合計 ===")
    print(weekday_sales)
    if weekday_sales.sum() > 0:
        weekday_sales.plot.bar(title="曜日別売上")
        plt.tight_layout()
        path = "images/weekday_sales.png"
        plt.savefig(path)
        plt.close()
        image_infos.append({"title": "曜日別売上", "url": f"/images/weekday_sales.png"})

    # 値引き率ごとの平均売上
    if "値引き率" in df.columns:
        discount_group = df.groupby("値引き率")["金額"].mean()
        if not discount_group.empty:
            discount_group.plot.bar(title="値引き率ごとの平均売上")
            plt.tight_layout()
            path = "images/discount_avg_sales.png"
            plt.savefig(path)
            plt.close()
            image_infos.append({"title": "値引き率ごとの平均売上", "url": f"/images/discount_avg_sales.png"})

    # 廃棄率ごとの平均売上
    if "廃棄率" in df.columns:
        waste_group = df.groupby("廃棄率")["金額"].mean()
        if not waste_group.empty:
            waste_group.plot.bar(title="廃棄率ごとの平均売上")
            plt.tight_layout()
            path = "images/waste_avg_sales.png"
            plt.savefig(path)
            plt.close()
            image_infos.append({"title": "廃棄率ごとの平均売上", "url": f"/images/waste_avg_sales.png"})

    # 気温と売上の関係
    if "気温" in df.columns:
        temp_sales = df[["気温", "金額"]].dropna()
        if not temp_sales.empty:
            temp_sales.plot.scatter(x="気温", y="金額", title="気温と売上の関係")
            plt.tight_layout()
            path = "images/temp_vs_sales.png"
            plt.savefig(path)
            plt.close()
            image_infos.append({"title": "気温と売上の関係", "url": f"/images/temp_vs_sales.png"})

    # 売上金額トップ10商品
    if "商品名" in df.columns:
        top10 = df.groupby("商品名")["金額"].sum().sort_values(ascending=False).head(10)
        if not top10.empty:
            top10.plot.barh(title="売上金額トップ10商品")
            plt.tight_layout()
            path = "images/top10_sales.png"
            plt.savefig(path)
            plt.close()
            image_infos.append({"title": "売上金額トップ10商品", "url": f"/images/top10_sales.png"})

    # 値引き率トップ10商品
    if "値引き率" in df.columns and "商品名" in df.columns:
        discount_top10 = df.groupby("商品名")["値引き率"].mean().sort_values(ascending=False).head(10)
        if not discount_top10.empty:
            discount_top10.plot.barh(title="値引き率トップ10商品")
            plt.tight_layout()
            path = "images/top10_discount.png"
            plt.savefig(path)
            plt.close()
            image_infos.append({"title": "値引き率トップ10商品", "url": f"/images/top10_discount.png"})

    # 廃棄率トップ10商品
    if "廃棄率" in df.columns and "商品名" in df.columns:
        waste_top10 = df.groupby("商品名")["廃棄率"].mean().sort_values(ascending=False).head(10)
        if not waste_top10.empty:
            waste_top10.plot.barh(title="廃棄率トップ10商品")
            plt.tight_layout()
            path = "images/top10_waste.png"
            plt.savefig(path)
            plt.close()
            image_infos.append({"title": "廃棄率トップ10商品", "url": f"/images/top10_waste.png"})

    # 気温とサブカテゴリ別売上
    if "気温" in df.columns:
        temp_cat = df.groupby(["気温", "サブカテゴリ"])["金額"].mean().unstack().dropna(how='all')
        if not temp_cat.empty:
            temp_cat.plot(title="気温とサブカテゴリ別売上")
            plt.tight_layout()
            path = "images/temp_vs_subcat_sales.png"
            plt.savefig(path)
            plt.close()
            image_infos.append({"title": "気温とサブカテゴリ別売上", "url": f"/images/temp_vs_subcat_sales.png"})

    # 曜日とサブカテゴリの売上傾向
    weekday_cat = df.groupby(["曜日", "サブカテゴリ"])["金額"].mean().unstack().reindex(weekdays)
    if not weekday_cat.empty:
        weekday_cat.plot(title="曜日とサブカテゴリの売上傾向")
        plt.tight_layout()
        path = "images/weekday_vs_subcat.png"
        plt.savefig(path)
        plt.close()
        image_infos.append({"title": "曜日とサブカテゴリの売上傾向", "url": f"/images/weekday_vs_subcat.png"})

    # サブカテゴリ別売上構成（円グラフ）
    subcat_sum = df.groupby("サブカテゴリ")["金額"].sum()
    if not subcat_sum.empty:
        subcat_sum.plot.pie(autopct="%1.1f%%", startangle=90)
        plt.title("サブカテゴリ別売上構成")
        plt.ylabel("")
        plt.tight_layout()
        path = "images/subcat_pie.png"
        plt.savefig(path)
        plt.close()
        image_infos.append({"title": "サブカテゴリ別売上構成", "url": f"/images/subcat_pie.png"})

    # 曜日別売上構成（円グラフ）
    weekday_sum = df.groupby("曜日")["金額"].sum().reindex(weekdays)
    if weekday_sum.sum() > 0:
        weekday_sum.plot.pie(autopct="%1.1f%%", startangle=90)
        plt.title("曜日別売上構成")
        plt.ylabel("")
        plt.tight_layout()
        path = "images/weekday_pie.png"
        plt.savefig(path)
        plt.close()
        image_infos.append({"title": "曜日別売上構成", "url": f"/images/weekday_pie.png"})

    # 完了
    for info in image_infos:
        info["url"] = f"https://graph-api2.onrender.com{info['url']}"
    return JSONResponse(content=image_infos)
