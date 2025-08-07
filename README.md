# just-mp3-tagger

just-mp3-tagger 是一款可以編輯`mp3`檔案內的標籤(tag)，包含曲目名稱、歌手、曲目編號、曲目風格、專輯封面，還包含字幕以及簡易的`lrc`編輯器

## 安裝說明
1. 安裝所需模組
```bash
pip3 install pygame
pip3 install mutagen
pip3 install pillow
```

2. 下載程式
```bash
git clone "https://www.github.com/d1fficult222/just-mp3-tagger"
```

3. 將 `no_cover.png` 與 `just-mp3-tagger.py` 放於同個資料夾內，並與此路徑執行python檔案，會跳出檔案選擇框，選擇你的`mp3`檔案，即可編輯



## Changelog
- 1.2
  - 新增：鍵盤快捷鍵 (Ctrl+S, Ctrl+O)
  - 新增：複製歌詞
  - 新增：移除時間戳記、移除所有字幕
- 1.1
  - 更改：以ID3v2.3儲存
  - 更改：所有圖片以jpg格式儲存
  - 修復：評論可以正常讀取
  - 修復：新檔案會套用上一個檔案的cover
  - 修復：字幕結尾空換行現在會移除
- 1.0
  - Initial Commit