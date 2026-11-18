import requests
import pandas as pd
import time

BASE_URL = "https://raw.githubusercontent.com/statsbomb/open-data/master/data"

# 対象大会：FIFA World Cup (competition_id = 43)
# season_id: 3 (2018 Russia), 106 (2022 Qatar)
SEASONS = {
    3: "2018",
    106: "2022"
}

all_matches_list = []
all_events_list = []

print("🚀 2018年＆2022年 ワールドカップデータの取得を開始します...")

for season_id, year_label in SEASONS.items():
    matches_url = f"{BASE_URL}/matches/43/{season_id}.json"
    print(f"\n📥 {year_label}年大会の試合一覧を取得中...")
    res = requests.get(matches_url)
    if res.status_code != 200:
        print(f"⚠️ {year_label}年大会の試合一覧の取得に失敗しました。")
        continue

    matches_data = res.json()
    print(f"✅ {year_label}年大会: {len(matches_data)} 試合を検出")

    for idx, m in enumerate(matches_data, 1):
        match_id = m['match_id']
        home_team = m['home_team']['home_team_name']
        away_team = m['away_team']['away_team_name']

        all_matches_list.append({
            'season': year_label,
            'match_id': match_id,
            'match_date': m['match_date'],
            'home_team': home_team,
            'away_team': away_team,
            'home_score': m['home_score'],
            'away_score': m['away_score'],
            'stage': m.get('competition_stage', {}).get('name', '')
        })

        # イベントデータの取得
        events_url = f"{BASE_URL}/events/{match_id}.json"
        ev_res = requests.get(events_url)
        if ev_res.status_code == 200:
            events_data = ev_res.json()
            for ev in events_data:
                ev_type = ev.get('type', {}).get('name')
                # 分析に必要な主要イベントのみ抽出（ファイルサイズ軽量化のため）
                if ev_type in ['Shot', 'Pass', 'Interception', 'Duel', 'Block', 'Clearance']:
                    all_events_list.append({
                        'match_id': match_id,
                        'minute': ev.get('minute'),
                        'team': ev.get('team', {}).get('name'),
                        'type': ev_type,
                        'location': str(ev.get('location')) if ev.get('location') else None,
                        'pass_outcome': ev.get('pass', {}).get('outcome', {}).get('name') if ev_type == 'Pass' else None,
                        'shot_statsbomb_xg': ev.get('shot', {}).get('statsbomb_xg') if ev_type == 'Shot' else None
                    })

        if idx % 10 == 0 or idx == len(matches_data):
            print(f"   [{year_label}年] {idx}/{len(matches_data)} 試合完了...")
        time.sleep(0.05)

# CSV保存
df_matches = pd.DataFrame(all_matches_list)
df_events = pd.DataFrame(all_events_list)

df_matches.to_csv("wc_all_matches.csv", index=False, encoding="utf-8-sig")
df_events.to_csv("wc_all_events.csv", index=False, encoding="utf-8-sig")

print("\n🎉 すべてのデータ取得とCSV保存が完了しました！")
print(f"   - 試合データ: wc_all_matches.csv ({len(df_matches)} 試合)")
print(f"   - イベントデータ: wc_all_events.csv ({len(df_events)} 件)")