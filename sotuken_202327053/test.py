import matplotlib.pyplot as plt
from mplsoccer import Pitch

# サッカーピッチを描画する設定
pitch = Pitch(pitch_color='grass', line_color='white', stripe=True)
fig, ax = pitch.draw(figsize=(10, 7))

# 画面に表示
plt.show()