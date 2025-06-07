import os
import uuid
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from starlette.staticfiles import StaticFiles
import matplotlib.font_manager as fm

app = FastAPI()

# フォント設定（日本語対応）
font_path = "./fonts/NotoSansJP-Regular.ttf"
if os.path.exists(font_path):
    font_prop = fm.FontProperties(fname=font_path)
    plt.rcParams["font.family"] = font_prop.get_name()

UPLOAD_DIR = "uploads"
IMAGE_DIR = "images"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(IMAGE_DIR, exist_ok=True)

app.mount("/images", StaticFiles(directory=IMAGE_DIR), name="images")

df_cache = None

@app.post("/upload-and-generate")
def upload_and_generate(file: UploadFile = File(...)):
    global df_cache
    try:
        # ファイル保存
        csv_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(csv_path, "wb") as buffer:
            buffer.write(file.file.read())

        # CSV読み込み
        df = pd.read_csv(csv_path)
        df_cache = df

        # 必須カラムチェック
        required_columns = ['サブカテゴリ', '曜日', '値引き率', '廃棄率', '最高気温', '商品名', '売上金額']
        for col in required_columns:
            if col not in df.columns:
                return JSONResponse(content={"error": f"CSVに'{col}'列が存在しません。"}, status_code=400)

        # グラフ保存関数
        def save_plot(fig, title):
            filename = f"{uuid.uuid4().hex}.png"
            path = os.path.join(IMAGE_DIR, filename)
            fig.savefig(path, bbox_inches='tight')
            plt.close(fig)
            return {
                "title": title,
                "url": f"https://graph-api2.onrender.com/images/{filename}"
            }

        response = []

        try:
            fig = plt.figure()
            sns.barplot(data=df, x="サブカテゴリ", y="売上金額", estimator=sum)
            plt.xticks(rotation=45)
            response.append(save_plot(fig, "サブカテゴリ別売上"))
        except Exception as e:
            print("Error in サブカテゴリ別売上:", e)

        try:
            fig = plt.figure()
            sns.barplot(data=df, x="曜日", y="売上金額", estimator=sum)
            response.append(save_plot(fig, "曜日別売上"))
        except Exception as e:
            print("Error in 曜日別売上:", e)

        try:
            fig = plt.figure()
            sns.barplot(data=df, x="値引き率", y="売上金額")
            response.append(save_plot(fig, "値引き率ごとの平均売上"))
        except Exception as e:
            print("Error in 値引き率ごとの平均売上:", e)

        try:
            fig = plt.figure()
            sns.barplot(data=df, x="廃棄率", y="売上金額")
            response.append(save_plot(fig, "廃棄率ごとの平均売上"))
        except Exception as e:
            print("Error in 廃棄率ごとの平均売上:", e)

        try:
            fig = plt.figure()
            sns.scatterplot(data=df, x="最高気温", y="売上金額")
            response.append(save_plot(fig, "気温と売上の関係"))
        except Exception as e:
            print("Error in 気温と売上の関係:", e)

        try:
            fig = plt.figure()
            top10 = df.groupby("商品名")["売上金額"].sum().sort_values(ascending=False).head(10)
            sns.barplot(x=top10.values, y=top10.index)
            response.append(save_plot(fig, "売上金額トップ10商品"))
        except Exception as e:
            print("Error in 売上金額トップ10商品:", e)

        try:
            fig = plt.figure()
            sns.scatterplot(data=df, x="最高気温", y="売上金額", hue="サブカテゴリ")
            response.append(save_plot(fig, "気温とサブカテゴリ別売上"))
        except Exception as e:
            print("Error in 気温とサブカテゴリ別売上:", e)

        try:
            fig = plt.figure()
            sns.boxplot(data=df, x="曜日", y="売上金額", hue="サブカテゴリ")
            response.append(save_plot(fig, "曜日とサブカテゴリの売上傾向"))
        except Exception as e:
            print("Error in 曜日とサブカテゴリの売上傾向:", e)

        try:
            fig = plt.figure()
            pie_data = df.groupby("サブカテゴリ")["売上金額"].sum()
            plt.pie(pie_data.values, labels=pie_data.index, autopct='%1.1f%%')
            plt.axis("equal")
            response.append(save_plot(fig, "サブカテゴリ別売上構成"))
        except Exception as e:
            print("Error in サブカテゴリ別売上構成:", e)

        try:
            fig = plt.figure()
            pie_data = df.groupby("曜日")["売上金額"].sum()
            plt.pie(pie_data.values, labels=pie_data.index, autopct='%1.1f%%')
            plt.axis("equal")
            response.append(save_plot(fig, "曜日別売上構成"))
        except Exception as e:
            print("Error in 曜日別売上構成:", e)

        return response

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
        
