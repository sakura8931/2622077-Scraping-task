import csv
import time
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

# 武蔵野大学のトップページURL
START_URL = "https://www.musashino-u.ac.jp/"
BASE_DOMAIN = urlparse(START_URL).netloc

# スキップ対象の拡張子（PDFや画像・動画などをアクセス前に除外）
IGNORE_EXTENSIONS = (
    ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg",
    ".zip", ".tar", ".gz", ".mp3", ".mp4", ".doc", ".docx",
    ".xls", ".xlsx", ".ppt", ".pptx", ".css", ".js", ".ico"
)

# URLとタイトルを格納する辞書型変数
sitemap_dict = {}

# 訪問済みURLと探索用リスト
visited_urls = set()
urls_to_visit = [START_URL]

print("スクレイピングを開始します...")
print("※途中で Ctrl+C を押しても、それまでに取得したデータがCSVに保存されます。\n")

# ブラウザを装うヘッダー情報
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ja,en-US;q=0.7,en;q=0.3"
}

try:
    while urls_to_visit:
        current_url = urls_to_visit.pop(0)

        if current_url in visited_urls:
            continue

        visited_urls.add(current_url)

        # PDFや画像などの拡張子はアクセスせずに即スキップ
        parsed_current = urlparse(current_url)
        if parsed_current.path.lower().endswith(IGNORE_EXTENSIONS):
            continue

        try:
            time.sleep(1)  # サーバ負荷軽減

            response = requests.get(current_url, headers=headers, timeout=10)

            # エラーレスポンスの場合はスキップ
            if response.status_code != 200:
                continue

            content_type = response.headers.get("Content-Type", "")
            if "text/html" not in content_type:
                continue

            # 文字化け防止のために response.content を渡す
            soup = BeautifulSoup(response.content, "html.parser")

            page_title = (
                soup.title.string.strip()
                if soup.title and soup.title.string
                else "タイトルなし"
            )

            sitemap_dict[current_url] = page_title
            print(f"取得 [{len(sitemap_dict)}件] (探索待ち: {len(urls_to_visit)}件): {current_url} -> {page_title}")

            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                full_url = urljoin(current_url, href)
                parsed_full = urlparse(full_url)

                clean_url = f"{parsed_full.scheme}://{parsed_full.netloc}{parsed_full.path}"

                # PDFなどのURLは最初から探索リストに追加しない
                if clean_url.lower().endswith(IGNORE_EXTENSIONS):
                    continue

                # 同一ドメインかつ未訪問のURLのみ追加
                if parsed_full.netloc == BASE_DOMAIN and parsed_full.scheme in ["http", "https"]:
                    if clean_url not in visited_urls and clean_url not in urls_to_visit:
                        urls_to_visit.append(clean_url)

        except Exception as e:
            print(f"アクセスエラー ({current_url}): {e}")

except KeyboardInterrupt:
    print("\n[中断] 処理を停止しました。取得済みのデータをCSVに出力します...")

finally:
    csv_filename = "sitemap.csv"
    with open(csv_filename, mode="w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["URL", "Title"])  # ヘッダー
        for url, title in sitemap_dict.items():
            writer.writerow([url, title])

    print(f"\n完了: 取得した {len(sitemap_dict)} 件のデータを {csv_filename} に保存しました！")