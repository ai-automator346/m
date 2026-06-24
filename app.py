import streamlit as st
import google.generativeai as genai
import requests
from PIL import Image
import io
import urllib.parse

st.set_page_config(
    page_title="フリマ価格チェッカー",
    page_icon="💰",
    layout="centered"
)

st.title("💰 フリマ価格チェッカー")
st.caption("写真を撮るだけで相場がわかる")

api_key = st.secrets.get("GEMINI_API_KEY", "")
if not api_key:
    st.error("APIキーが設定されていません。Streamlit Cloud の Secrets に GEMINI_API_KEY を追加してください。")
    st.stop()

genai.configure(api_key=api_key)


def identify_product(image: Image.Image) -> dict:
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = """この商品の写真を見て、以下を日本語で答えてください。

1. 商品名（ブランド・メーカーと製品名）
2. 型番やモデル名（わかれば）
3. 推定コンディション（未使用/美品/良品/傷あり/ジャンク のどれか）
4. メルカリで検索するのに最適なキーワード（シンプルに）

回答は以下の形式で：
商品名: 〇〇
型番: 〇〇（不明な場合は「不明」）
コンディション: 〇〇
検索キーワード: 〇〇"""

    response = model.generate_content([prompt, image])
    text = response.text

    result = {"商品名": "", "型番": "", "コンディション": "", "検索キーワード": "", "raw": text}
    for line in text.split("\n"):
        for key in ["商品名", "型番", "コンディション", "検索キーワード"]:
            if line.startswith(f"{key}:"):
                result[key] = line.split(":", 1)[1].strip()
    return result


def build_search_links(keyword: str) -> dict:
    encoded = urllib.parse.quote(keyword)
    return {
        "メルカリ（売り切れ）": f"https://mercari.com/search/?keyword={encoded}&status=sold_out",
        "メルカリ（出品中）": f"https://mercari.com/search/?keyword={encoded}",
        "ヤフオク（落札済み）": f"https://auctions.yahoo.co.jp/search/search?p={encoded}&b=1&n=50&s1=bids&o1=d&closed=1",
        "ラクマ": f"https://fril.jp/search?query={encoded}&sold=1",
    }


# --- UI ---
tab1, tab2 = st.tabs(["📷 写真で調べる", "⌨️ 文字で調べる"])

with tab1:
    st.markdown("スマホなら「カメラ」で直接撮影できます")
    uploaded = st.camera_input("カメラで撮影") or st.file_uploader(
        "または写真ファイルをアップロード", type=["jpg", "jpeg", "png", "webp"]
    )

    if uploaded:
        image = Image.open(uploaded)
        st.image(image, caption="アップロードされた画像", use_column_width=True)

        with st.spinner("商品を識別中..."):
            result = identify_product(image)

        st.success("識別完了！")

        with st.expander("識別結果", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**商品名**  \n{result['商品名']}")
                st.markdown(f"**型番**  \n{result['型番']}")
            with col2:
                st.markdown(f"**コンディション**  \n{result['コンディション']}")
                keyword = st.text_input("検索キーワード（修正可）", value=result["検索キーワード"])

        if keyword:
            st.markdown("---")
            st.markdown("### 🔍 相場を調べる")
            links = build_search_links(keyword)
            for name, url in links.items():
                st.link_button(name, url, use_container_width=True)

            st.info("💡 「売り切れ」「落札済み」のリンクを見ると実際に売れた価格がわかります")

with tab2:
    keyword_text = st.text_input("商品名を入力", placeholder="例: AirPods Pro 第2世代")
    if keyword_text:
        st.markdown("### 🔍 相場を調べる")
        links = build_search_links(keyword_text)
        for name, url in links.items():
            st.link_button(name, url, use_container_width=True)
        st.info("💡 「売り切れ」「落札済み」のリンクを見ると実際に売れた価格がわかります")

st.markdown("---")
st.caption("データはフリマサイトのリンクから確認できます。価格は市場の変動により異なります。")
