import csv
import time
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

# 武蔵野大学のトップページURL
START_URL = "https://www.musashino-u.ac.jp/"
BASE_DOMAIN = urlparse(START_URL).netloc

# URLとタイトルを格納する辞書型変数
sitemap_dict = {}

# 訪問済みURLと探索用リスト
visited_urls = set()
urls_to_visit = [START_URL]

print("スクレイピングを開始します...")
print("※途中で Ctrl+C を押して停止させても、それまでに取得したデータがCSVに保存されます。\n")

try:
    while urls_to_visit:
        current_url = urls_to_visit.pop(0)

        if current_url in visited_urls:
            continue

        visited_urls.add(current_url)

        try:
            time.sleep(1)  # サーバ負荷軽減

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = requests.get(current_url, headers=headers, timeout=10)

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
            print(f"取得 [{len(sitemap_dict)}]: {current_url} -> {page_title}")

            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                full_url = urljoin(current_url, href)
                parsed_full = urlparse(full_url)

                clean_url = f"{parsed_full.scheme}://{parsed_full.netloc}{parsed_full.path}"

                if (
                    parsed_full.netloc == BASE_DOMAIN
                    and parsed_full.scheme in ["http", "https"]
                ):
                    if (
                        clean_url not in visited_urls
                        and clean_url not in urls_to_visit
                    ):
                        urls_to_visit.append(clean_url)

        except Exception as e:
            print(f"アクセスエラー ({current_url}): {e}")

except KeyboardInterrupt:
    print("\n[中断] 処理を停止しました。取得済みのデータをCSVに出力します...")

finally:
    # 正常終了時も途中停止時（Ctrl+C）でも必ず実行されるCSV書き出し処理
    csv_filename = "sitemap.csv"
    with open(csv_filename, mode="w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["URL", "Title"])  # ヘッダー
        for url, title in sitemap_dict.items():
            writer.writerow([url, title])

    print(f"\n完了: 取得した {len(sitemap_dict)} 件のデータを {csv_filename} に保存しました！")