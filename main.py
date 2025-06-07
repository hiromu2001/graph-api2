from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import uuid
from matplotlib import font_manager

app = FastAPI()

# 画像保存ディレクトリ
IMAGE_DIR = "images"
os.makedirs(IMAGE_DIR, exist_ok=True)

# 日本語フォント設定（IPAexゴシック）
font_path = "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"
if os.path.exists(font_path):
    plt.rcParams["font.family"] = font_manager.FontProperties(fname=font_path).get_name()

# Static files serve
app.mount("/images", StaticFiles(directory=IMAGE_DIR), name="images")

@app.post("/upload-and-generate")
async def upload_and_generate(file: UploadFile = File(...)):
    try:
        df = pd.read_csv(file.file)

        # カラム名の正規化
        df.columns = df.columns.str.strip()

        # 必須カラムがなければエラー
        required_columns = ["サブカテゴリ", "曜日", "売上金額", "値引き率", "廃棄率", "気温", "商品名"]
        for col in required_columns:
            if col not in df.columns:
                return JSONResponse(status_code=400, content={"error": f"CSVに'{col}'列が存在しません。"})

        image_urls = []

        def save_and_record(fig, title):
            filename = f"{uuid.uuid4().hex}.png"
            path = os.path.join(IMAGE_DIR, filename)
            fig.savefig(path)
            plt.close(fig)
            image_urls.append({
                "title": title,
                "url": f"https://graph-api2.onrender.com/images/{filename}"
            })

        # 1. サブカテゴリ別売上
        fig, ax = plt.subplots()
        df.groupby("サブカテゴリ")["売上金額"].sum().plot.bar(ax=ax)
        ax.set_title("サブカテゴリ別売上")
        save_and_record(fig, "サブカテゴリ別売上")

        # 2. 曜日別売上
        fig, ax = plt.subplots()
        weekday_order = ["月", "火", "水", "木", "金", "土", "日"]
        df["曜日"] = pd.Categorical(df["曜日"], categories=weekday_order, ordered=True)
        df.groupby("曜日")["売上金額"].sum().reindex(weekday_order).plot.bar(ax=ax)
        ax.set_title("曜日別売上")
        save_and_record(fig, "曜日別売上")

        # 3. 値引き率ごとの平均売上
        fig, ax = plt.subplots()
        df.groupby("値引き率")["売上金額"].mean().plot.bar(ax=ax)
        ax.set_title("値引き率ごとの平均売上")
        save_and_record(fig, "値引き率ごとの平均売上")

        # 4. 廃棄率ごとの平均売上
        fig, ax = plt.subplots()
        df.groupby("廃棄率")["売上金額"].mean().plot.bar(ax=ax)
        ax.set_title("廃棄率ごとの平均売上")
        save_and_record(fig, "廃棄率ごとの平均売上")

        # 5. 気温と売上の関係
        fig, ax = plt.subplots()
        sns.scatterplot(data=df, x="気温", y="売上金額", ax=ax)
        ax.set_title("気温と売上の関係")
        save_and_record(fig, "気温と売上の関係")

        # 6. 売上金額トップ10商品
        fig, ax = plt.subplots()
        df.groupby("商品名")["売上金額"].sum().sort_values(ascending=False).head(10).plot.bar(ax=ax)
        ax.set_title("売上金額トップ10商品")
        save_and_record(fig, "売上金額トップ10商品")

        # 7. 気温とサブカテゴリ別売上
        fig, ax = plt.subplots()
        sns.lineplot(data=df, x="気温", y="売上金額", hue="サブカテゴリ", ax=ax)
        ax.set_title("気温とサブカテゴリ別売上")
        save_and_record(fig, "気温とサブカテゴリ別売上")

        # 8. 曜日とサブカテゴリの売上傾向
        fig, ax = plt.subplots()
        sns.barplot(data=df, x="曜日", y="売上金額", hue="サブカテゴリ", ax=ax, estimator=sum, ci=None)
        ax.set_title("曜日とサブカテゴリの売上傾向")
        save_and_record(fig, "曜日とサブカテゴリの売上傾向")

        # 9. サブカテゴリ別売上構成
        fig, ax = plt.subplots()
        df.groupby("サブカテゴリ")["売上金額"].sum().plot.pie(ax=ax, autopct="%1.1f%%", startangle=90)
        ax.set_ylabel("")
        ax.set_title("サブカテゴリ別売上構成")
        save_and_record(fig, "サブカテゴリ別売上構成")

        # 10. 曜日別売上構成
        fig, ax = plt.subplots()
        df.groupby("曜日")["売上金額"].sum().reindex(weekday_order).plot.pie(ax=ax, autopct="%1.1f%%", startangle=90)
        ax.set_ylabel("")
        ax.set_title("曜日別売上構成")
        save_and_record(fig, "曜日別売上構成")

        return JSONResponse(content=image_urls)

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
