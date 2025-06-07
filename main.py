from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import uuid

app = FastAPI()
app.mount("/images", StaticFiles(directory="images"), name="images")

CSV_PATH = "uploaded.csv"


def save_uploaded_file(uploaded_file: UploadFile):
    with open(CSV_PATH, "wb") as buffer:
        buffer.write(uploaded_file.file.read())


def save_plot(fig, title):
    if not os.path.exists("images"):
        os.makedirs("images")
    filename = f"{uuid.uuid4().hex}.png"
    path = os.path.join("images", filename)
    fig.savefig(path)
    plt.close(fig)
    return f"https://graph-api2.onrender.com/images/{filename}"


def generate_all_graphs(df):
    results = []
    try:
        fig, ax = plt.subplots()
        df.groupby("サブカテゴリ")["売上金額"].sum().plot(kind="bar", ax=ax)
        ax.set_title("サブカテゴリ別売上")
        results.append({"title": "サブカテゴリ別売上", "url": save_plot(fig, "subcat_sales")})
    except Exception as e:
        print(f"Error in サブカテゴリ別売上: {e}")

    try:
        fig, ax = plt.subplots()
        df.groupby("曜日")["売上金額"].sum().plot(kind="bar", ax=ax)
        ax.set_title("曜日別売上")
        results.append({"title": "曜日別売上", "url": save_plot(fig, "weekday_sales")})
    except Exception as e:
        print(f"Error in 曜日別売上: {e}")

    try:
        fig, ax = plt.subplots()
        df.groupby("値引き率")["売上金額"].mean().plot(kind="bar", ax=ax)
        ax.set_title("値引き率ごとの平均売上")
        results.append({"title": "値引き率ごとの平均売上", "url": save_plot(fig, "discount_avg_sales")})
    except Exception as e:
        print(f"Error in 値引き率ごとの平均売上: {e}")

    try:
        fig, ax = plt.subplots()
        df.groupby("廃棄率")["売上金額"].mean().plot(kind="bar", ax=ax)
        ax.set_title("廃棄率ごとの平均売上")
        results.append({"title": "廃棄率ごとの平均売上", "url": save_plot(fig, "waste_avg_sales")})
    except Exception as e:
        print(f"Error in 廃棄率ごとの平均売上: {e}")

    try:
        fig = sns.lmplot(x="最高気温", y="売上金額", data=df)
        plt.title("気温と売上の関係")
        results.append({"title": "気温と売上の関係", "url": save_plot(plt.gcf(), "temp_vs_sales")})
    except Exception as e:
        print(f"Error in 気温と売上の関係: {e}")

    try:
        fig, ax = plt.subplots()
        df.groupby("商品名")["売上金額"].sum().sort_values(ascending=False).head(10).plot(kind="bar", ax=ax)
        ax.set_title("売上金額トップ10商品")
        results.append({"title": "売上金額トップ10商品", "url": save_plot(fig, "top10_sales")})
    except Exception as e:
        print(f"Error in 売上金額トップ10商品: {e}")

    try:
        fig = sns.lmplot(x="最高気温", y="売上金額", hue="サブカテゴリ", data=df)
        plt.title("気温とサブカテゴリ別売上")
        results.append({"title": "気温とサブカテゴリ別売上", "url": save_plot(plt.gcf(), "temp_vs_subcat_sales")})
    except Exception as e:
        print(f"Error in 気温とサブカテゴリ別売上: {e}")

    try:
        fig = plt.figure()
        sns.boxplot(x="曜日", y="売上金額", hue="サブカテゴリ", data=df)
        plt.title("曜日とサブカテゴリの売上傾向")
        results.append({"title": "曜日とサブカテゴリの売上傾向", "url": save_plot(plt.gcf(), "weekday_vs_subcat")})
    except Exception as e:
        print(f"Error in 曜日とサブカテゴリの売上傾向: {e}")

    try:
        fig, ax = plt.subplots()
        df.groupby("サブカテゴリ")["売上金額"].sum().plot(kind="pie", ax=ax, autopct="%1.1f%%")
        ax.set_ylabel("")
        ax.set_title("サブカテゴリ別売上構成")
        results.append({"title": "サブカテゴリ別売上構成", "url": save_plot(fig, "subcat_pie")})
    except Exception as e:
        print(f"Error in サブカテゴリ別売上構成: {e}")

    try:
        fig, ax = plt.subplots()
        df.groupby("曜日")["売上金額"].sum().plot(kind="pie", ax=ax, autopct="%1.1f%%")
        ax.set_ylabel("")
        ax.set_title("曜日別売上構成")
        results.append({"title": "曜日別売上構成", "url": save_plot(fig, "weekday_pie")})
    except Exception as e:
        print(f"Error in 曜日別売上構成: {e}")

    return results


@app.post("/upload-and-generate")
async def upload_and_generate(file: UploadFile = File(...)):
    save_uploaded_file(file)
    df = pd.read_csv(CSV_PATH)
    df.columns = df.columns.str.strip()
    if "売上金額" not in df.columns:
        return JSONResponse(content={"error": "CSVに'売上金額'列が存在しません。"}, status_code=400)
    results = generate_all_graphs(df)
    return results
