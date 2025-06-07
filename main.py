from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import uuid

app = FastAPI()

UPLOAD_DIR = "images"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# データを保存し読み込む関数
def load_and_save_csv(uploaded_file: UploadFile) -> pd.DataFrame:
    csv_path = os.path.join(UPLOAD_DIR, "uploaded_data.csv")
    with open(csv_path, "wb") as buffer:
        buffer.write(uploaded_file.file.read())
    df = pd.read_csv(csv_path)
    return df


# グラフを保存し、URL形式で返す
def save_plot(fig, title: str):
    filename = f"{uuid.uuid4().hex}.png"
    path = os.path.join(UPLOAD_DIR, filename)
    fig.savefig(path)
    plt.close(fig)
    return {"title": title, "url": f"/{UPLOAD_DIR}/{filename}"}


@app.post("/upload-and-generate")
async def upload_and_generate(file: UploadFile = File(...)):
    try:
        df = load_and_save_csv(file)
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": f"CSV読み込みエラー: {str(e)}"})

    required_cols = ['売上金額', '曜日', 'サブカテゴリ', '値引き率', '廃棄率', '最高気温', '商品名']
    for col in required_cols:
        if col not in df.columns:
            return JSONResponse(status_code=400, content={"error": f"CSVに'{col}'列が存在しません。"})

    graph_urls = []

    # 1. サブカテゴリ別売上
    try:
        fig, ax = plt.subplots()
        df.groupby("サブカテゴリ")["売上金額"].sum().plot.bar(ax=ax, title="サブカテゴリ別売上")
        graph_urls.append(save_plot(fig, "サブカテゴリ別売上"))
    except Exception as e:
        print("Error in サブカテゴリ別売上:", e)

    # 2. 曜日別売上
    try:
        weekday_order = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"]
        fig, ax = plt.subplots()
        df.groupby("曜日")["売上金額"].sum().reindex(weekday_order).plot.bar(ax=ax, title="曜日別売上")
        graph_urls.append(save_plot(fig, "曜日別売上"))
    except Exception as e:
        print("Error in 曜日別売上:", e)

    # 3. 値引き率ごとの平均売上
    try:
        fig, ax = plt.subplots()
        df.groupby("値引き率")["売上金額"].mean().plot.bar(ax=ax, title="値引き率ごとの平均売上")
        graph_urls.append(save_plot(fig, "値引き率ごとの平均売上"))
    except Exception as e:
        print("Error in 値引き率ごとの平均売上:", e)

    # 4. 廃棄率ごとの平均売上
    try:
        fig, ax = plt.subplots()
        df.groupby("廃棄率")["売上金額"].mean().plot.bar(ax=ax, title="廃棄率ごとの平均売上")
        graph_urls.append(save_plot(fig, "廃棄率ごとの平均売上"))
    except Exception as e:
        print("Error in 廃棄率ごとの平均売上:", e)

    # 5. 気温と売上の関係
    try:
        fig, ax = plt.subplots()
        sns.scatterplot(data=df, x="最高気温", y="売上金額", ax=ax).set(title="気温と売上の関係")
        graph_urls.append(save_plot(fig, "気温と売上の関係"))
    except Exception as e:
        print("Error in 気温と売上の関係:", e)

    # 6. 売上トップ10商品
    try:
        fig, ax = plt.subplots()
        df.groupby("商品名")["売上金額"].sum().nlargest(10).plot.bar(ax=ax, title="売上金額トップ10商品")
        graph_urls.append(save_plot(fig, "売上金額トップ10商品"))
    except Exception as e:
        print("Error in 売上金額トップ10商品:", e)

    # 7. 気温とサブカテゴリ別売上の関係
    try:
        fig, ax = plt.subplots()
        sns.scatterplot(data=df, x="最高気温", y="売上金額", hue="サブカテゴリ", ax=ax).set(title="気温とサブカテゴリ別売上")
        graph_urls.append(save_plot(fig, "気温とサブカテゴリ別売上"))
    except Exception as e:
        print("Error in 気温とサブカテゴリ別売上:", e)

    # 8. 曜日とサブカテゴリの売上傾向
    try:
        fig, ax = plt.subplots()
        sns.barplot(data=df, x="曜日", y="売上金額", hue="サブカテゴリ", ax=ax).set(title="曜日とサブカテゴリの売上傾向")
        graph_urls.append(save_plot(fig, "曜日とサブカテゴリの売上傾向"))
    except Exception as e:
        print("Error in 曜日とサブカテゴリの売上傾向:", e)

    # 9. サブカテゴリ別売上構成
    try:
        fig, ax = plt.subplots()
        df.groupby("サブカテゴリ")["売上金額"].sum().plot.pie(ax=ax, autopct="%1.1f%%")
        ax.set_title("サブカテゴリ別売上構成")
        ax.set_ylabel("")
        graph_urls.append(save_plot(fig, "サブカテゴリ別売上構成"))
    except Exception as e:
        print("Error in サブカテゴリ別売上構成:", e)

    # 10. 曜日別売上構成
    try:
        fig, ax = plt.subplots()
        df.groupby("曜日")["売上金額"].sum().reindex(weekday_order).plot.pie(ax=ax, autopct="%1.1f%%")
        ax.set_title("曜日別売上構成")
        ax.set_ylabel("")
        graph_urls.append(save_plot(fig, "曜日別売上構成"))
    except Exception as e:
        print("Error in 曜日別売上構成:", e)

    return graph_urls
