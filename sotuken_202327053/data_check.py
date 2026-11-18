from statsbombpy import sb

# 2018年ワールドカップ（コンペティションID: 43, シーズンID: 3）の全試合データを取得
matches = sb.matches(competition_id=43, season_id=3)

# データの最初の5試合分を画面に表示
print(matches[['match_date', 'home_team', 'away_team', 'home_score', 'away_score']].head())