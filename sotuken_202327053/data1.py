import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor

MATCHES_FILE = "wc2022_matches.csv"
EVENTS_FILE = "wc2022_events.csv"
BASE_URL = "https://raw.githubusercontent.com/statsbomb/open-data/master/data/events/"

matches = pd.read_csv(MATCHES_FILE)
match_ids = matches['match_id'].tolist()


def fetch_match_events(m_id):
    url = f"{BASE_URL}{m_id}.json"
    res = requests.get(url)
    if res.status_code != 200:
        return []

    events_json = res.json()
    extracted = []
    for ev in events_json:
        # 必要な詳細項目をすべて抽出
        row = {
            'match_id': m_id,
            'team': ev.get('team', {}).get('name'),
            'type': ev.get('type', {}).get('name'),
            'minute': ev.get('minute'),
            'location': str(ev.get('location')) if 'location' in ev else None,
            'pass_outcome': ev.get('pass', {}).get('outcome', {}).get('name') if 'pass' in ev else None,
            'shot_statsbomb_xg': ev.get('shot', {}).get('statsbomb_xg') if 'shot' in ev else None
        }
        extracted.append(row)
    return extracted


print("StatsBombから詳細データ（xG・パス結果・座標）を取得中...（約15〜30秒かかります）")
all_rows = []
# 高速化のため並列ダウンロード
with ThreadPoolExecutor(max_workers=10) as executor:
    results = executor.map(fetch_match_events, match_ids)
    for r in results:
        all_rows.extend(r)

df_events = pd.DataFrame(all_rows)
df_events.to_csv(EVENTS_FILE, index=False)
print(f"完了！全 {len(df_events)} 件の詳細イベントデータを {EVENTS_FILE} に保存しました。")
print("保存された列:", list(df_events.columns))