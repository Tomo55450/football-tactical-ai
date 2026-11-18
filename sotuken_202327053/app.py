import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import ast
import os

# ページの設定
st.set_page_config(
    page_title="Football Tactical AI Analyzer",
    page_icon="⚽",
    layout="wide"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MATCHES_FILE = os.path.join(BASE_DIR, "wc2022_matches.csv")
EVENTS_FILE = os.path.join(BASE_DIR, "wc2022_events.csv")

# 2022年W杯 全32カ国の日本語 ⇔ 英語 辞書
JP_TO_EN = {
    '日本': 'Japan', 'スペイン': 'Spain', 'ドイツ': 'Germany',
    'コスタリカ': 'Costa Rica', 'クロアチア': 'Croatia', 'アルゼンチン': 'Argentina',
    'フランス': 'France', 'モロッコ': 'Morocco', 'ブラジル': 'Brazil',
    'イングランド': 'England', 'ポルトガル': 'Portugal', 'オランダ': 'Netherlands',
    'カタール': 'Qatar', 'エクアドル': 'Ecuador', 'セネガル': 'Senegal',
    'イラン': 'Iran', 'アメリカ': 'United States', 'ウェールズ': 'Wales',
    'サウジアラビア': 'Saudi Arabia', 'メキシコ': 'Mexico', 'ポーランド': 'Poland',
    'オーストラリア': 'Australia', 'デンマーク': 'Denmark', 'チュニジア': 'Tunisia',
    'ベルギー': 'Belgium', 'カナダ': 'Canada', 'セルビア': 'Serbia',
    'スイス': 'Switzerland', 'カメルーン': 'Cameroon', 'ウルグアイ': 'Uruguay',
    '韓国': 'South Korea', 'ガーナ': 'Ghana'
}
EN_TO_JP = {v: k for k, v in JP_TO_EN.items()}


def to_jp(en_name):
    return EN_TO_JP.get(en_name, en_name)


@st.cache_data
def load_data():
    if os.path.exists(MATCHES_FILE) and os.path.exists(EVENTS_FILE):
        matches = pd.read_csv(MATCHES_FILE)
        events = pd.read_csv(EVENTS_FILE, low_memory=False)
        return matches, events
    return None, None


def extract_xy(loc_str):
    if pd.isna(loc_str):
        return (-1.0, -1.0)
    try:
        coords = ast.literal_eval(str(loc_str))
        if isinstance(coords, list) and len(coords) >= 2:
            return (float(coords[0]), float(coords[1]))
    except Exception:
        pass
    return (-1.0, -1.0)


# --- ユーザーの質問意図を解析する関数 ---
def detect_user_intent(text):
    if any(k in text for k in ['傾向', 'まとめ', '総括', '平均', '全体', '通算']):
        return 'summary'
    elif any(k in text for k in ['勝因', '理由', 'なぜ', 'どうして', '勝てた', '負けた']):
        return 'win_reason'
    elif any(k in text for k in ['シュート', 'ゴール', '得点', '攻撃', 'xG', '期待値', 'マップ']):
        return 'offense'
    elif any(k in text for k in ['守備', 'ディフェンス', 'パス', 'ポゼッション', '支配']):
        return 'tactics_def'
    return 'full'


# --- 戦術スタイルの自動分類（アーキタイプ判定） ---
def classify_tactical_style(team_stats, opp_stats):
    pass_ratio = team_stats['passes'] / max(opp_stats['passes'], 1)
    if pass_ratio >= 1.3 and team_stats['pass_acc'] >= 82.0:
        return "支配型ポゼッション（ボール保持・遅攻主体）"
    elif pass_ratio <= 0.77 and team_stats['def'] >= opp_stats['def']:
        return "堅守速攻・カウンター型（ブロック守備＋縦への速攻）"
    elif team_stats['def'] >= 95 and team_stats['final_third'] >= opp_stats['final_third']:
        return "ハイプレス・インテンシティ型（前線からの激しい奪取）"
    else:
        return "バランス・状況適応型（攻守の切り替え重視）"


# 1. スタッツ比較チャート
def create_stats_chart(t1, t2):
    fig, ax = plt.subplots(figsize=(8, 3.8))
    fig.patch.set_facecolor('#0E1117')
    ax.set_facecolor('#0E1117')

    metrics = ['Defensive Actions', 'Final Third Entries', 'Pass Accuracy (%)', 'xG (x10)', 'Shots']
    t1_vals = [t1['def'], t1['final_third'], t1['pass_acc'], t1['xg'] * 10, t1['shots']]
    t2_vals = [t2['def'], t2['final_third'], t2['pass_acc'], t2['xg'] * 10, t2['shots']]

    y = range(len(metrics))
    height = 0.35

    bars1 = ax.barh([i + height / 2 for i in y], t1_vals, height, label=t1['en_team'], color='#00D4FF')
    bars2 = ax.barh([i - height / 2 for i in y], t2_vals, height, label=t2['en_team'], color='#FF4B4B')

    ax.set_yticks(list(y))
    ax.set_yticklabels(metrics, color='white', fontsize=10, fontweight='bold')
    ax.tick_params(axis='x', colors='gray')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('gray')
    ax.spines['bottom'].set_color('gray')
    ax.grid(axis='x', linestyle='--', alpha=0.2, color='white')

    for bar, orig_val in zip(bars1,
                             [t1['def'], t1['final_third'], f"{t1['pass_acc']:.1f}%", f"{t1['xg']:.2f}", t1['shots']]):
        ax.text(bar.get_width() + 1.5, bar.get_y() + bar.get_height() / 2, str(orig_val),
                va='center', ha='left', color='#00D4FF', fontsize=9, fontweight='bold')
    for bar, orig_val in zip(bars2,
                             [t2['def'], t2['final_third'], f"{t2['pass_acc']:.1f}%", f"{t2['xg']:.2f}", t2['shots']]):
        ax.text(bar.get_width() + 1.5, bar.get_y() + bar.get_height() / 2, str(orig_val),
                va='center', ha='left', color='#FF4B4B', fontsize=9, fontweight='bold')

    ax.set_xlim(0, max(max(t1_vals), max(t2_vals)) * 1.18 + 5)
    ax.set_title(f"Tactical Stats Comparison: {t1['en_team']} vs {t2['en_team']}", color='white', fontsize=12,
                 fontweight='bold', pad=12)
    legend = ax.legend(loc='lower right', facecolor='#1E222B', edgecolor='gray')
    for text in legend.get_texts():
        text.set_color('white')

    plt.tight_layout()
    return fig


# 2. シュート位置＆xGピッチマップ
def create_shot_map(match_events, t1_en, t2_en):
    fig, ax = plt.subplots(figsize=(9, 5.8))
    fig.patch.set_facecolor('#0E1117')
    ax.set_facecolor('#1B4D3E')

    line_color = 'white'
    lw = 1.5
    ax.plot([0, 120, 120, 0, 0], [0, 0, 80, 80, 0], color=line_color, lw=lw)
    ax.plot([60, 60], [0, 80], color=line_color, lw=lw)
    center_circle = patches.Circle((60, 40), 10, fill=False, color=line_color, lw=lw)
    ax.add_patch(center_circle)
    ax.plot([0, 18, 18, 0], [18, 18, 62, 62], color=line_color, lw=lw)
    ax.plot([0, 6, 6, 0], [30, 30, 50, 50], color=line_color, lw=lw)
    ax.plot([120, 102, 102, 120], [18, 18, 62, 62], color=line_color, lw=lw)
    ax.plot([120, 114, 114, 120], [30, 30, 50, 50], color=line_color, lw=lw)

    shots = match_events[match_events['type'] == 'Shot'].copy()

    t1_shots = shots[shots['team'] == t1_en]
    for _, row in t1_shots.iterrows():
        x, y = row['x_coord'], row['y_coord']
        xg = row['shot_statsbomb_xg'] if pd.notna(row['shot_statsbomb_xg']) else 0.05
        if x >= 0 and y >= 0:
            ax.scatter(x, y, s=xg * 900 + 80, color='#00D4FF', edgecolors='white', linewidth=1.5, alpha=0.85, zorder=4)

    t2_shots = shots[shots['team'] == t2_en]
    for _, row in t2_shots.iterrows():
        x, y = row['x_coord'], row['y_coord']
        xg = row['shot_statsbomb_xg'] if pd.notna(row['shot_statsbomb_xg']) else 0.05
        if x >= 0 and y >= 0:
            ax.scatter(120 - x, 80 - y, s=xg * 900 + 80, color='#FF4B4B', edgecolors='white', linewidth=1.5, alpha=0.85,
                       zorder=4)

    ax.scatter([], [], s=150, color='#00D4FF', edgecolors='white', label=f"{t1_en} (Attack ->)")
    ax.scatter([], [], s=150, color='#FF4B4B', edgecolors='white', label=f"{t2_en} (<- Attack)")

    ax.set_xlim(-3, 123)
    ax.set_ylim(83, -3)
    ax.axis('off')
    ax.set_title("Shot Map & xG Size (Circle Size = Goal Probability)", color='white', fontsize=12, fontweight='bold',
                 pad=10)

    legend = ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.02), ncol=2, facecolor='#1E222B', edgecolor='gray')
    for text in legend.get_texts():
        text.set_color('white')

    plt.tight_layout()
    return fig


# --- 1試合分の詳細解析関数（質問意図に応じてレポート構成を最適化） ---
def analyze_single_match(match, all_events, intent='full'):
    m_id = int(match['match_id'])
    match_events = all_events[all_events['match_id'] == m_id].copy()

    if 'location' in match_events.columns:
        coords = match_events['location'].apply(extract_xy)
        match_events['x_coord'] = [c[0] for c in coords]
        match_events['y_coord'] = [c[1] for c in coords]
    else:
        match_events['x_coord'] = -1.0
        match_events['y_coord'] = -1.0

    has_minute = 'minute' in match_events.columns

    stats_summary = []
    for en_team in [match['home_team'], match['away_team']]:
        team_events = match_events[match_events['team'] == en_team]

        shot_events = team_events[team_events['type'] == 'Shot']
        shots = len(shot_events)
        total_xg = shot_events['shot_statsbomb_xg'].fillna(
            0).sum() if 'shot_statsbomb_xg' in shot_events.columns else 0.0

        all_passes = team_events[team_events['type'] == 'Pass']
        total_passes = len(all_passes)
        if 'pass_outcome' in all_passes.columns and total_passes > 0:
            completed_passes = all_passes['pass_outcome'].isna().sum()
            pass_acc = (completed_passes / total_passes) * 100
        else:
            pass_acc = 0.0

        final_third = len(team_events[team_events['x_coord'] >= 80.0])
        defensive_actions = len(team_events[team_events['type'].isin(['Interception', 'Duel', 'Block', 'Clearance'])])
        score = match['home_score'] if en_team == match['home_team'] else match['away_score']

        # 前半(0-45分) vs 後半(45分以降)のファイナルサード進入数
        if has_minute:
            ft_1st = len(team_events[(team_events['x_coord'] >= 80.0) & (team_events['minute'] <= 45)])
            ft_2nd = len(team_events[(team_events['x_coord'] >= 80.0) & (team_events['minute'] > 45)])
        else:
            ft_1st, ft_2nd = 0, 0

        stats_summary.append({
            'en_team': en_team,
            'team': to_jp(en_team),
            'score': int(score),
            'shots': shots,
            'xg': total_xg,
            'passes': total_passes,
            'pass_acc': pass_acc,
            'final_third': final_third,
            'def': defensive_actions,
            'ft_1st': ft_1st,
            'ft_2nd': ft_2nd
        })

    t1, t2 = stats_summary[0], stats_summary[1]
    t1['style'] = classify_tactical_style(t1, t2)
    t2['style'] = classify_tactical_style(t2, t1)

    header_title = f"📅 {match['match_date']} ｜ 🏆 {t1['team']} {t1['score']} - {t2['score']} {t2['team']}"

    # 意図に応じたフォーカス見出し
    intent_badge = {
        'win_reason': "🎯 **【フォーカス：勝因・決定力特化レポート】**",
        'offense': "⚡ **【フォーカス：攻撃・シュート・xG特化レポート】**",
        'tactics_def': "🛡️ **【フォーカス：戦術構造・ポゼッション・守備特化レポート】**",
        'full': "📊 **【総合戦術＆勝因分析レポート】**"
    }.get(intent, "📊 **【総合戦術＆勝因分析レポート】**")

    match_text = f"### 🏆 {t1['team']} {t1['score']} - {t2['score']} {t2['team']} （試合日: {match['match_date']}）\n"
    match_text += f"{intent_badge}\n\n"

    # チーム基本スタッツ＆戦術スタイル判定
    for s in [t1, t2]:
        match_text += f"#### 🟢 **{s['team']}** ｜ 🏷️ 判定戦術: `{s['style']}`\n"
        match_text += f"- 🎯 **シュート数**: {s['shots']} 本 （**xG合計: {s['xg']:.2f}**）\n"
        match_text += f"- 🔄 **パス試行数**: {s['passes']} 本 （**成功率: {s['pass_acc']:.1f}%**）\n"
        match_text += f"- ⚡ **敵陣深く（ファイナルサード）でのプレイ**: {s['final_third']} 回"
        if has_minute:
            match_text += f" （前半: {s['ft_1st']}回 → 後半: {s['ft_2nd']}回）\n"
        else:
            match_text += "\n"
        match_text += f"- 🛡️ **守備アクション数**: {s['def']} 回\n\n"

    match_text += "---\n"

    # セクション生成
    sec_win = ""
    t1_diff = t1['score'] - t1['xg']
    t2_diff = t2['score'] - t2['xg']
    sec_win += "#### 🏆 勝因分析とxG（ゴール期待値）効率\n"
    sec_win += f"- **期待値との差分（実得点 - xG）**: {t1['team']} `{t1_diff:+.2f}` ｜ {t2['team']} `{t2_diff:+.2f}`\n"
    if t1['score'] > t2['score']:
        winner, loser, w_diff = t1, t2, t1_diff
    elif t2['score'] > t1['score']:
        winner, loser, w_diff = t2, t1, t2_diff
    else:
        winner = None

    if winner:
        if winner['xg'] < loser['xg']:
            sec_win += f"- **【効率的勝利・ジャイアントキリング】** チャンスの総量（xG）では敗れた **{loser['team']}**（xG: {loser['xg']:.2f}）が上回っていましたが、勝った **{winner['team']}**（xG: {winner['xg']:.2f}）が限られた好機を期待値以上に決めきった（差分 `{w_diff:+.2f}`）ことが最大の勝因です。\n\n"
        else:
            sec_win += f"- **【順当な攻撃力の勝利】** 勝った **{winner['team']}** は質の高い決定機を多く創出し（xG: {winner['xg']:.2f}）、内容・結果ともに相手を上回りました。\n\n"
    else:
        sec_win += "- 両チームの決定機創出とゴール期待値のバランスが釣り合った、妥当な引き分けと言えます。\n\n"

    sec_tactics = "#### 🧠 戦術構造・ポゼッションと守備強度\n"
    if t1['passes'] > t2['passes'] * 1.3:
        sec_tactics += f"- **{t1['team']}** がパス数（{t1['passes']}本・成功率{t1['pass_acc']:.1f}%）で圧倒し、ボールを保持して試合を支配。対する **{t2['team']}** は自陣ブロックからのカウンター戦術を選択しています。\n"
    elif t2['passes'] > t1['passes'] * 1.3:
        sec_tactics += f"- **{t2['team']}** がパス数（{t2['passes']}本・成功率{t2['pass_acc']:.1f}%）で主導権を掌握。**{t1['team']}** はポゼッションを譲り、スペースを消す守備と速攻に徹しました。\n"
    else:
        sec_tactics += f"- 両チームともパス精度が拮抗（{t1['team']}: {t1['pass_acc']:.1f}% vs {t2['team']}: {t2['pass_acc']:.1f}%）し、中盤の主導権を激しく奪い合う展開でした。\n"

    if t1['def'] > t2['def'] * 1.2:
        sec_tactics += f"- 守備面では **{t1['team']}** が{t1['def']}回の守備アクションを記録し、高い守備強度で相手の攻撃を跳ね返しました。\n\n"
    elif t2['def'] > t1['def'] * 1.2:
        sec_tactics += f"- 守備面では **{t2['team']}** が{t2['def']}回の守備アクションを記録し、激しいプレスとブロックで自由を奪いました。\n\n"
    else:
        sec_tactics += "- 守備アクション数は両チームとも高水準で均衡しており、集中力の高いディフェンスが光りました。\n\n"

    sec_momentum = ""
    if has_minute:
        sec_momentum += "#### ⏱️ 時間帯別（前半 vs 後半）の試合展開モメンタム\n"
        sec_momentum += f"- **{t1['team']}** の敵陣進入数: 前半 `{t1['ft_1st']}回` → 後半 `{t1['ft_2nd']}回`\n"
        sec_momentum += f"- **{t2['team']}** の敵陣進入数: 前半 `{t2['ft_1st']}回` → 後半 `{t2['ft_2nd']}回`\n"
        if t1['ft_2nd'] > t1['ft_1st'] * 1.3 and t1['ft_2nd'] > t2['ft_2nd']:
            sec_momentum += f"- 後半に入り **{t1['team']}** が敵陣への押し込みを大幅に増やし、攻撃のギアを上げて試合の流れを引き寄せました。\n\n"
        elif t2['ft_2nd'] > t2['ft_1st'] * 1.3 and t2['ft_2nd'] > t1['ft_2nd']:
            sec_momentum += f"- 後半に入り **{t2['team']}** が敵陣でのプレイ数を急増させ、戦術修正や選手交代によって攻勢を強めました。\n\n"
        else:
            sec_momentum += "- 前半・後半を通じて両チームの陣地バランスに大きな崩れはなく、一貫したゲームプランが維持されました。\n\n"

    # 質問意図に応じて並び順・表示を最適化
    if intent == 'win_reason':
        match_text += sec_win + sec_momentum + sec_tactics
    elif intent == 'offense':
        match_text += sec_momentum + sec_win
    elif intent == 'tactics_def':
        match_text += sec_tactics + sec_momentum
    else:
        match_text += sec_tactics + sec_win + sec_momentum

    fig_bar = create_stats_chart(t1, t2)
    fig_pitch = create_shot_map(match_events, t1['en_team'], t2['en_team'])

    return {
        "title": header_title,
        "text": match_text,
        "figs": [fig_bar, fig_pitch],
        "t1": t1,
        "t2": t2
    }


# --- 複数試合の傾向総括レポートを生成する関数 ---
def generate_team_summary(en_team, results, all_events):
    jp_team = to_jp(en_team)
    total_matches = len(results)
    wins, draws, losses = 0, 0, 0
    sum_goals, sum_conceded, sum_xg, sum_shots, sum_passes, sum_acc, sum_ft, sum_def = 0, 0, 0.0, 0, 0, 0.0, 0, 0

    for _, match in results.iterrows():
        m_id = int(match['match_id'])
        m_ev = all_events[all_events['match_id'] == m_id].copy()
        if 'location' in m_ev.columns:
            m_ev['x_coord'] = m_ev['location'].apply(lambda s: extract_xy(s)[0])
        else:
            m_ev['x_coord'] = -1.0

        is_home = (match['home_team'] == en_team)
        gf = int(match['home_score'] if is_home else match['away_score'])
        ga = int(match['away_score'] if is_home else match['home_score'])
        sum_goals += gf
        sum_conceded += ga
        if gf > ga:
            wins += 1
        elif gf == ga:
            draws += 1
        else:
            losses += 1

        t_ev = m_ev[m_ev['team'] == en_team]
        shots = t_ev[t_ev['type'] == 'Shot']
        sum_shots += len(shots)
        sum_xg += shots['shot_statsbomb_xg'].fillna(0).sum() if 'shot_statsbomb_xg' in shots.columns else 0.0

        passes = t_ev[t_ev['type'] == 'Pass']
        sum_passes += len(passes)
        if 'pass_outcome' in passes.columns and len(passes) > 0:
            sum_acc += (passes['pass_outcome'].isna().sum() / len(passes)) * 100

        sum_ft += len(t_ev[t_ev['x_coord'] >= 80.0])
        sum_def += len(t_ev[t_ev['type'].isin(['Interception', 'Duel', 'Block', 'Clearance'])])

    avg_xg = sum_xg / total_matches
    avg_shots = sum_shots / total_matches
    avg_passes = sum_passes / total_matches
    avg_acc = sum_acc / total_matches
    avg_ft = sum_ft / total_matches
    avg_def = sum_def / total_matches

    summary_md = f"### 📈 【大会総括レポート】{jp_team} の全{total_matches}試合 戦術傾向分析\n\n"
    summary_md += f"- **通算成績**: `{wins}勝 {draws}分 {losses}敗` （総得点: {sum_goals} / 総失点: {sum_conceded}）\n"
    summary_md += f"- **1試合平均シュート / xG**: `{avg_shots:.1f} 本` / `xG {avg_xg:.2f}` （決定力差分: `{sum_goals - sum_xg:+.2f}`）\n"
    summary_md += f"- **1試合平均パス数 / 成功率**: `{avg_passes:.0f} 本` / `{avg_acc:.1f}%`\n"
    summary_md += f"- **1試合平均敵陣進入 / 守備アクション**: `{avg_ft:.1f} 回` / `{avg_def:.1f} 回`\n\n"
    summary_md += "#### 💡 大会を通じた戦術的特徴\n"
    if avg_passes < 420 and avg_def > 95:
        summary_md += f"- **{jp_team}** は大会を通じてボール保持に固執せず、組織的なブロック守備（平均{avg_def:.0f}回の守備アクション）から鋭いカウンターを仕掛ける**堅守速攻型**の戦術を一貫して遂行しました。\n"
    elif avg_passes >= 550 and avg_acc >= 85:
        summary_md += f"- **{jp_team}** は1試合平均{avg_passes:.0f}本・成功率{avg_acc:.1f}%という極めて高いパスワークを武器に、主導権を握り続ける**ポゼッション支配型**のスタイルを展開しました。\n"
    else:
        summary_md += f"- **{jp_team}** は対戦相手に応じてボール保持と守備ブロックを使い分ける**柔軟なバランス型**の戦術で大会を戦いました。\n"

    return summary_md


all_matches, all_events = load_data()

if all_matches is None:
    st.error("データファイルが見つかりません。")
    st.stop()

# --- サイドバー ---
with st.sidebar:
    st.title("⚽ Tactical AI v6.0")
    st.caption("対話意図理解＆高度戦術解析システム")
    st.markdown("---")

    st.subheader("💬 対話質問の例")
    st.write("国名だけでなく、知りたい観点を自由に質問できます。")
    st.code("日本対スペインの勝因は？")
    st.code("日本対ドイツのシュートデータ")
    st.code("日本の全試合の傾向をまとめて")
    st.markdown("---")

    st.subheader("💡 搭載アルゴリズム")
    st.write("- **対話意図解析**: 質問文から勝因・攻撃・守備・総括を自動判定")
    st.write("- **戦術スタイル分類**: スタッツ比率から4つの戦術タイプへ自動分類")
    st.write("- **モメンタム分析**: 前半・後半の敵陣押し込み推移を計測")
    st.write("- **空間・期待値解析**: xG差分とシュート座標マップ描画")

# --- メイン画面 ---
st.title("🤖 Football Tactical AI Assistant")
st.write("試合統計データの可視化と、ルールベース解析アルゴリズムによる**戦術・勝因レポート生成を行う対話型AI**です。")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant",
         "content": "こんにちは！対戦カードや質問を入力してください（例：「日本対スペインの勝因は？」「日本の全試合の傾向をまとめて」「アルゼンチン対フランス」）。質問内容に合わせて戦術レポートとチャートを生成します！"}
    ]

# 過去のメッセージ表示
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if "content" in msg and msg["content"]:
            st.markdown(msg["content"])
        if "matches_data" in msg:
            auto_expand = (len(msg["matches_data"]) == 1)
            for m_data in msg["matches_data"]:
                with st.expander(m_data["title"], expanded=auto_expand):
                    st.markdown(m_data["text"])
                    col1, col2 = st.columns(2)
                    with col1:
                        st.pyplot(m_data["figs"][0])
                    with col2:
                        st.pyplot(m_data["figs"][1])

if user_input := st.chat_input("例: 日本対スペインの勝因は？ / 日本の傾向をまとめて..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    intent = detect_user_intent(user_input)
    detected_teams = []
    for jp_name, en_name in JP_TO_EN.items():
        if jp_name in user_input:
            detected_teams.append(en_name)

    if len(detected_teams) == 1:
        team = detected_teams[0]
        results = all_matches[(all_matches['home_team'] == team) | (all_matches['away_team'] == team)].sort_values(
            'match_date')
    elif len(detected_teams) >= 2:
        t1, t2 = detected_teams[0], detected_teams[1]
        results = all_matches[
            ((all_matches['home_team'] == t1) & (all_matches['away_team'] == t2)) |
            ((all_matches['home_team'] == t2) & (all_matches['away_team'] == t1))
            ].sort_values('match_date')
    else:
        results = pd.DataFrame()

    if results.empty:
        err_msg = "⚠️ 指定された国名、または対戦カードが見つかりませんでした。（2022年W杯出場32カ国の日本語名に対応しています）"
        st.session_state.messages.append({"role": "assistant", "content": err_msg})
        with st.chat_message("assistant"):
            st.markdown(err_msg)
    else:
        matches_data_list = []
        summary_report = ""

        with st.spinner("質問意図を解析し、戦術レポートとチャートを生成しています..."):
            # 1カ国指定かつ「傾向・まとめ」意図の場合は大会総括レポートを作成
            if len(detected_teams) == 1 and intent == 'summary':
                summary_report = generate_team_summary(detected_teams[0], results, all_events) + "\n---\n"

            for _, match in results.iterrows():
                m_data = analyze_single_match(match, all_events, intent=intent)
                matches_data_list.append(m_data)

        if len(matches_data_list) > 1:
            intro_text = summary_report + f"🔍 **{len(matches_data_list)}試合** のデータが見つかりました。各試合をクリックすると詳細レポートとグラフが開きます。"
        else:
            intro_text = summary_report

        st.session_state.messages.append({
            "role": "assistant",
            "content": intro_text,
            "matches_data": matches_data_list
        })

        with st.chat_message("assistant"):
            if intro_text:
                st.markdown(intro_text)
            auto_expand = (len(matches_data_list) == 1)
            for m_data in matches_data_list:
                with st.expander(m_data["title"], expanded=auto_expand):
                    st.markdown(m_data["text"])
                    col1, col2 = st.columns(2)
                    with col1:
                        st.pyplot(m_data["figs"][0])
                    with col2:
                        st.pyplot(m_data["figs"][1])
