from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
import os
from matplotlib import rcParams

app = FastAPI()

# 日本語フォントの設定
plt.rcParams["font.family"] = "IPAexGothic"  # Noto Sans JP や IPAexGothic をインストール済み前提

@app.post("/generate-graphs")
async def generate_graphs(file: UploadFile = File(...)):
    contents = await file.read()
    df = pd.read_csv(io.StringIO(contents.decode("utf-8")))

    required_columns = ["カテゴリ", "サブカテゴリ", "売上日", "売上金額", "数量", "気温", "値引率", "廃棄率"]
    for col in required_columns:
        if col not in df.columns:
            return {"error": f"CSVに『{col}』の列が必要です"}

    df["売上日"] = pd.to_datetime(df["売上日"])
    df["曜日"] = df["売上日"].dt.day_name()
    df["金額"] = df["売上金額"]

    if not os.path.exists("graphs"):
        os.makedirs("graphs")

    graph_paths = []

    def save_plot(fig, filename):
        path = f"graphs/{filename}"
        fig.savefig(path, bbox_inches='tight')
        plt.close(fig)
        graph_paths.append(path)

    # 1. サブカテゴリ別売上
    fig1, ax1 = plt.subplots(figsize=(8, 6))
    df.groupby("サブカテゴリ")["金額"].sum().sort_values().plot(kind="barh", ax=ax1)
    ax1.set_title("サブカテゴリ別売上金額")
    save_plot(fig1, "サブカテゴリ別売上.png")

    # 2. 曜日別売上
    fig2, ax2 = plt.subplots(figsize=(8, 6))
    df.groupby("曜日")["金額"].sum().reindex([
        "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
    ]).plot(kind="bar", ax=ax2)
    ax2.set_title("曜日別売上金額")
    save_plot(fig2, "曜日別売上.png")

    # 3. 値引き率ごとの平均売上
    fig3, ax3 = plt.subplots(figsize=(8, 6))
    df.groupby("値引率")["金額"].mean().plot(kind="bar", ax=ax3)
    ax3.set_title("値引き率ごとの平均売上金額")
    save_plot(fig3, "値引率ごとの平均売上.png")

    # 4. 廃棄率ごとの平均売上
    fig4, ax4 = plt.subplots(figsize=(8, 6))
    df.groupby("廃棄率")["金額"].mean().plot(kind="bar", ax=ax4)
    ax4.set_title("廃棄率ごとの平均売上金額")
    save_plot(fig4, "廃棄率ごとの平均売上.png")

    # 5. 気温と売上の散布図
    fig5, ax5 = plt.subplots(figsize=(8, 6))
    sns.scatterplot(data=df, x="気温", y="金額", ax=ax5)
    ax5.set_title("気温と売上金額の関係")
    save_plot(fig5, "気温と売上の散布図.png")

    # 6. 売上金額トップ10商品
    fig6, ax6 = plt.subplots(figsize=(8, 6))
    df.groupby("サブカテゴリ")["金額"].sum().nlargest(10).plot(kind="bar", ax=ax6)
    ax6.set_title("売上金額トップ10商品")
    save_plot(fig6, "売上トップ10.png")

    # 7. 値引き率トップ10商品
    fig7, ax7 = plt.subplots(figsize=(8, 6))
    df.groupby("サブカテゴリ")["値引率"].mean().nlargest(10).plot(kind="bar", ax=ax7)
    ax7.set_title("値引き率トップ10商品")
    save_plot(fig7, "値引率トップ10.png")

    # 8. 廃棄率トップ10商品
    fig8, ax8 = plt.subplots(figsize=(8, 6))
    df.groupby("サブカテゴリ")["廃棄率"].mean().nlargest(10).plot(kind="bar", ax=ax8)
    ax8.set_title("廃棄率トップ10商品")
    save_plot(fig8, "廃棄率トップ10.png")

    # 9. サブカテゴリ構成比（円グラフ）
    fig9, ax9 = plt.subplots(figsize=(6, 6))
    df.groupby("サブカテゴリ")["金額"].sum().plot.pie(autopct="%1.1f%%", ax=ax9)
    ax9.set_ylabel("")
    ax9.set_title("サブカテゴリ売上構成比")
    save_plot(fig9, "サブカテゴリ構成比.png")

    # 10. 曜日構成比（円グラフ）
    fig10, ax10 = plt.subplots(figsize=(6, 6))
    df.groupby("曜日")["金額"].sum().plot.pie(autopct="%1.1f%%", ax=ax10)
    ax10.set_ylabel("")
    ax10.set_title("曜日別売上構成比")
    save_plot(fig10, "曜日構成比.png")

    return {"message": "グラフ生成成功", "files": graph_paths}
