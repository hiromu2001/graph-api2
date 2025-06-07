from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

app = FastAPI()

# images フォルダが存在しない場合は作成
if not os.path.exists("images"):
    os.makedirs("images")

# static files 用の設定
app.mount("/images", StaticFiles(directory="images"), name="images")

CSV_PATH = "uploaded_data.csv"

@app.post("/upload-csv")
def upload_csv(file: UploadFile = File(...)):
    try:
        df = pd.read_csv(file.file)
        df.to_csv(CSV_PATH, index=False)
        return {"message": "CSV uploaded and saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading CSV: {e}")

@app.post("/generate-graphs")
def generate_graphs():
    try:
        df = pd.read_csv(CSV_PATH)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="CSV file not found. Please upload first.")

    # デバッグ用: 曜日別の売上合計を表示
    if "曜日" not in df.columns or "金額" not in df.columns:
        raise HTTPException(status_code=400, detail="曜日または金額列が存在しません")

    print("=== 曜日ごとの売上合計 ===")
    weekday_order = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"]
    weekday_sales = df.groupby("曜日")["金額"].sum().reindex(weekday_order)
    print(weekday_sales)

    graph_info = []

    def save_plot(fig, filename, title):
        filepath = f"images/{filename}"
        fig.savefig(filepath)
        plt.close(fig)
        graph_info.append({"title": title, "url": f"https://graph-api2.onrender.com/images/{filename}"})

    # グラフ1: サブカテゴリ別売上
    if "サブカテゴリ" in df.columns:
        fig1 = plt.figure()
        df.groupby("サブカテゴリ")["金額"].sum().plot.bar(title="サブカテゴリ別売上")
        save_plot(fig1, "subcat_sales.png", "サブカテゴリ別売上")

    # グラフ2: 曜日別売上
    fig2 = plt.figure()
    weekday_sales.plot.bar(title="曜日別売上")
    save_plot(fig2, "weekday_sales.png", "曜日別売上")

    # グラフ3: 値引き率ごとの平均売上
    if "値引き率" in df.columns:
        discount_group = df.groupby("値引き率")["金額"].mean()
        if not discount_group.empty:
            fig3 = plt.figure()
            discount_group.plot.bar(title="値引き率ごとの平均売上")
            save_plot(fig3, "discount_avg_sales.png", "値引き率ごとの平均売上")

    # グラフ4: 廃棄率ごとの平均売上
    if "廃棄率" in df.columns:
        waste_group = df.groupby("廃棄率")["金額"].mean()
        if not waste_group.empty:
            fig4 = plt.figure()
            waste_group.plot.bar(title="廃棄率ごとの平均売上")
            save_plot(fig4, "waste_avg_sales.png", "廃棄率ごとの平均売上")

    # グラフ5: 気温と売上の関係
    if "気温" in df.columns:
        fig5 = plt.figure()
        plt.scatter(df["気温"], df["金額"])
        plt.title("気温と売上の関係")
        save_plot(fig5, "temp_vs_sales.png", "気温と売上の関係")

    # グラフ6: 売上金額トップ10商品
    if "商品名" in df.columns:
        fig6 = plt.figure()
        df.groupby("商品名")["金額"].sum().nlargest(10).plot.bar(title="売上金額トップ10商品")
        save_plot(fig6, "top10_sales.png", "売上金額トップ10商品")

    # グラフ7: 値引き率トップ10商品
    if "商品名" in df.columns and "値引き率" in df.columns:
        fig7 = plt.figure()
        df.groupby("商品名")["値引き率"].mean().nlargest(10).plot.bar(title="値引き率トップ10商品")
        save_plot(fig7, "top10_discount.png", "値引き率トップ10商品")

    # グラフ8: 廃棄率トップ10商品
    if "商品名" in df.columns and "廃棄率" in df.columns:
        fig8 = plt.figure()
        df.groupby("商品名")["廃棄率"].mean().nlargest(10).plot.bar(title="廃棄率トップ10商品")
        save_plot(fig8, "top10_waste.png", "廃棄率トップ10商品")

    # グラフ9: 気温とサブカテゴリ別売上
    if "気温" in df.columns and "サブカテゴリ" in df.columns:
        fig9 = plt.figure()
        sns.scatterplot(data=df, x="気温", y="金額", hue="サブカテゴリ")
        plt.title("気温とサブカテゴリ別売上")
        save_plot(fig9, "temp_vs_subcat_sales.png", "気温とサブカテゴリ別売上")

    # グラフ10: 曜日とサブカテゴリの売上傾向
    if "曜日" in df.columns and "サブカテゴリ" in df.columns:
        fig10 = plt.figure()
        pivot = df.pivot_table(index="曜日", columns="サブカテゴリ", values="金額", aggfunc="sum")
        if not pivot.empty:
            pivot = pivot.reindex(weekday_order)  # 曜日順に並べる
            pivot.plot(kind="bar", stacked=True, title="曜日とサブカテゴリの売上傾向")
            save_plot(fig10, "weekday_vs_subcat.png", "曜日とサブカテゴリの売上傾向")

    # グラフ11: サブカテゴリ別売上構成（円グラフ）
    if "サブカテゴリ" in df.columns:
        fig11 = plt.figure()
        df.groupby("サブカテゴリ")["金額"].sum().plot.pie(title="サブカテゴリ別売上構成", autopct='%1.1f%%')
        save_plot(fig11, "subcat_pie.png", "サブカテゴリ別売上構成")

    # グラフ12: 曜日別売上構成（円グラフ）
    fig12 = plt.figure()
    weekday_sales.plot.pie(title="曜日別売上構成", autopct='%1.1f%%')
    save_plot(fig12, "weekday_pie.png", "曜日別売上構成")

    return JSONResponse(content=graph_info)
