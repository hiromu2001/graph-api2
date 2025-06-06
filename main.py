from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import uuid

app = FastAPI()

@app.post("/generate-graphs")
async def generate_graphs(file: UploadFile = File(...)):
    contents = await file.read()
    df = pd.read_csv(pd.compat.StringIO(contents.decode("utf-8")))

    output_dir = "generated_graphs"
    os.makedirs(output_dir, exist_ok=True)

    if not all(col in df.columns for col in ["単価", "販売数量", "売上金額", "商品名", "サブカテゴリ", "値引き率", "廃棄率", "曜日", "最高気温"]):
        return {"error": "必要なカラムが含まれていません"}

    df["金額"] = df["単価"] * df["販売数量"]

    def save_plot(fig, name):
        path = os.path.join(output_dir, f"{name}.png")
        fig.savefig(path)
        plt.close(fig)

    # 1. サブカテゴリ別売上
    fig, ax = plt.subplots(figsize=(10, 6))
    subcat_sales = df.groupby("サブカテゴリ")["金額"].sum().sort_values()
    sns.barplot(x=subcat_sales.values, y=subcat_sales.index, ax=ax)
    ax.set_title("サブカテゴリ別売上")
    save_plot(fig, "subcat_sales")

    # 2. 曜日別売上
    fig, ax = plt.subplots(figsize=(10, 6))
    weekday_sales = df.groupby("曜日")["金額"].sum()
    sns.barplot(x=weekday_sales.index, y=weekday_sales.values, ax=ax)
    ax.set_title("曜日別売上")
    save_plot(fig, "weekday_sales")

    # 3. 値引き率ごとの平均売上
    fig, ax = plt.subplots(figsize=(10, 6))
    discount_sales = df.groupby("値引き率")["金額"].mean()
    sns.barplot(x=discount_sales.index, y=discount_sales.values, ax=ax)
    ax.set_title("値引き率ごとの平均売上")
    save_plot(fig, "discount_avg_sales")

    # 4. 廃棄率ごとの平均売上
    fig, ax = plt.subplots(figsize=(10, 6))
    waste_sales = df.groupby("廃棄率")["金額"].mean()
    sns.barplot(x=waste_sales.index, y=waste_sales.values, ax=ax)
    ax.set_title("廃棄率ごとの平均売上")
    save_plot(fig, "waste_avg_sales")

    # 5. 気温と売上の散布図
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.scatterplot(x="最高気温", y="金額", data=df, ax=ax)
    ax.set_title("気温と売上の散布図")
    save_plot(fig, "temp_vs_sales")

    # 6. 売上金額トップ10商品
    fig, ax = plt.subplots(figsize=(10, 6))
    top10_sales = df.groupby("商品名")["金額"].sum().sort_values(ascending=False).head(10)
    sns.barplot(x=top10_sales.values, y=top10_sales.index, ax=ax)
    ax.set_title("売上金額トップ10商品")
    save_plot(fig, "top10_sales")

    # 7. 値引き率トップ10商品
    fig, ax = plt.subplots(figsize=(10, 6))
    top10_discount = df.groupby("商品名")["値引き率"].mean().sort_values(ascending=False).head(10)
    sns.barplot(x=top10_discount.values, y=top10_discount.index, ax=ax)
    ax.set_title("値引き率トップ10商品")
    save_plot(fig, "top10_discount")

    # 8. 廃棄率トップ10商品
    fig, ax = plt.subplots(figsize=(10, 6))
    top10_waste = df.groupby("商品名")["廃棄率"].mean().sort_values(ascending=False).head(10)
    sns.barplot(x=top10_waste.values, y=top10_waste.index, ax=ax)
    ax.set_title("廃棄率トップ10商品")
    save_plot(fig, "top10_waste")

    # 9. 気温とサブカテゴリの散布図
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.scatterplot(x="最高気温", y="金額", hue="サブカテゴリ", data=df, ax=ax)
    ax.set_title("気温とサブカテゴリ別売上")
    save_plot(fig, "temp_vs_subcat")

    # 10. 曜日とサブカテゴリの散布図
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.stripplot(x="曜日", y="金額", hue="サブカテゴリ", data=df, dodge=True, ax=ax)
    ax.set_title("曜日とサブカテゴリ別売上")
    save_plot(fig, "weekday_vs_subcat")

    # 11. サブカテゴリ別売上構成比（円グラフ）
    fig, ax = plt.subplots(figsize=(8, 8))
    subcat_pie = df.groupby("サブカテゴリ")["金額"].sum()
    ax.pie(subcat_pie.values, labels=subcat_pie.index, autopct="%1.1f%%", startangle=140)
    ax.set_title("サブカテゴリ別 売上構成比")
    save_plot(fig, "subcat_pie")

    # 12. 曜日別売上構成比（円グラフ）
    fig, ax = plt.subplots(figsize=(8, 8))
    weekday_pie = df.groupby("曜日")["金額"].sum()
    ax.pie(weekday_pie.values, labels=weekday_pie.index, autopct="%1.1f%%", startangle=140)
    ax.set_title("曜日別 売上構成比")
    save_plot(fig, "weekday_pie")

    return {"message": "グラフの生成が完了しました", "files": os.listdir(output_dir)}
