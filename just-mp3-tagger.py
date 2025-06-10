from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, TCON, TRCK, COMM, USLT, APIC, ID3NoHeaderError
from mutagen.mp3 import MP3
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
from pygame import mixer
import shutil, os, re





file_modified = False
removed_album_cover = False
cover_changed = False
ALBUM_SIZE = 200
lyrics = []





def save_file(audio, hint):
    global cover_changed, file_modified
    audio['TIT2'] = TIT2(encoding=3, text=title_entry.get())
    audio['TPE1'] = TPE1(encoding=3, text=artist_entry.get())
    audio['TALB'] = TALB(encoding=3, text=album_entry.get())
    audio['TDRC'] = TDRC(encoding=3, text=date_entry.get())
    audio['TCON'] = TCON(encoding=3, text=str(genre_entry.get()))
    audio['TRCK'] = TRCK(encoding=3, text=track_entry.get())
    audio.delall("COMM")  # Clear existing comments
    audio.add(COMM(encoding=3, lang='eng', desc='', text=comment_entry.get()))
    # album art
    if removed_album_cover:
        audio.delall("APIC")
    elif cover_changed:
        with open("cover.jpg", 'rb') as img:
            audio.add(
                APIC(
                    encoding=3,        # UTF-8
                    mime='image/jpeg',
                    type=3,            # 3 = front cover
                    desc='Cover',
                    data=img.read()
                )
            )
        cover_changed = False
    # lyrics
    audio.setall("USLT", [USLT(encoding=3, text=lyrics_entry.get('1.0','end'))])
    # save
    audio.save(file_path, v2_version=3)  # Use ID3v2.3 so that Windows Explorer can show the cover art
    if os.path.exists("cover.jpg"):
        os.remove("cover.jpg")
    clear_modified()
    if hint:
        messagebox.showinfo(title=file_path, message="已儲存變更")

def load_data(audio):
    global cover_changed
    cover_changed = False
    # Clear old cover.jpg
    if os.path.exists("cover.jpg"):
        os.remove("cover.jpg")

    # Title bar
    clear_modified()
    
    # Text Data
    title_entry.delete(first=0, last="end")
    artist_entry.delete(first=0, last="end")
    album_entry.delete(first=0, last="end")
    date_entry.delete(first=0, last="end")
    genre_entry.delete(first=0, last="end")
    track_entry.delete(first=0, last="end")
    comment_entry.delete(first=0, last="end")
    lyrics_entry.delete("1.0", "end")
    try: title_entry.insert(0, audio['TIT2'][0])
    except: pass
    try: artist_entry.insert(0, audio['TPE1'][0])
    except: pass
    try: album_entry.insert(0, audio['TALB'][0])
    except: pass
    try: date_entry.insert(0, audio['TDRC'][0])
    except: pass
    try: genre_entry.insert(0, audio['TCON'][0])
    except: pass
    try: track_entry.insert(0, audio['TRCK'][0])
    except: pass
    try:
        for c in audio.getall("COMM"):
            comment_entry.insert(0, f"{c.text[0]}")
    except: pass
    try:
        for uslt in audio.getall("USLT"):
            lrc = uslt.text.rstrip('\n')
        lyrics_entry.insert("1.0", lrc)
    except: pass

    # Album Cover
    found_cover = False
    for i in audio.values():
        if isinstance(i, APIC):
            with open("cover.jpg", "wb") as img:
                img.write(i.data)
            show_album_art("cover.jpg")
            found_cover = True
            break
    if not found_cover:
        if os.path.exists("cover.jpg"):
            os.remove("cover.jpg")
        show_album_art("no_cover.jpg")
        resolution_label.config(text="沒有專輯圖片")


def show_album_art(file):
    cover = Image.open(file)
    resolution = cover.size
    resolution_label.config(text=f"解析度：{resolution[0]}x{resolution[1]}")
    cover = cover.resize((ALBUM_SIZE, ALBUM_SIZE))
    photo = ImageTk.PhotoImage(cover)
    image_label.config(image=photo)
    image_label.image = photo

def remove_album_art():
    global removed_album_cover, cover_changed
    removed_album_cover = True
    cover_changed = False
    mark_modified()
    if os.path.exists("cover.jpg"):
        os.remove("cover.jpg")
    show_album_art("no_cover.jpg")
    resolution_label.config(text="沒有專輯圖片")

def change_album_art():
    file = filedialog.askopenfilename(title="請選擇專輯圖片", filetypes=[("Image files", "*.png"), ("Image files", "*.jpg")])
    if file:
        global removed_album_cover, cover_changed
        removed_album_cover = False
        cover_changed = True
        mark_modified()
        img = Image.open(file)
        img = img.convert("RGB")
        img.save("cover.jpg", "JPEG")
        show_album_art("cover.jpg")

def export_album_art():
    file = filedialog.asksaveasfilename(initialfile=f"{audio['TIT2']}.png", defaultextension=".png", filetypes=[("Image Files", "*.png"), ("Image Files", "*.jpg")])
    if file:
        try:
            shutil.copy("cover.jpg", file)
        except Exception as e:
            messagebox.showerror(title="發生錯誤", message=f'無法儲存檔案: "{file}"，錯誤: "{e}"')


def upload_lyrics():
    if messagebox.askokcancel(title="確認變更", message="這將會覆蓋目前的字幕，確定要繼續嗎?"):
        file = filedialog.askopenfilename(title="請選擇檔案", filetypes=[("Lyrics files", "*.lrc"), ("Lyrics files", "*.srt"), ("Text files", "*.txt")])
        if file:
            with open(file, 'r') as f:
                lyrics_entry.delete('1.0', 'end')
                lyrics_entry.insert('1.0', ''.join(f.readlines()))

def export_lyrics(file_format):
    file = filedialog.asksaveasfilename(initialfile=f"{audio['TIT2']}.{file_format}", defaultextension=f".{file_format}", filetypes=[("Lyrics Files", f"*.{file_format}")])
    if file:
        # try:
        lrc = lyrics_entry.get('1.0','end')
        if file_format == "lrc":
            with open(file, 'w', encoding="utf-8") as f:
                f.write(lrc)
        elif file_format == "txt":
            txt = lrc_to_txt(lrc)
            with open(file, 'w', encoding="utf-8") as f:
                f.write(txt)
        elif file_format == "srt":
            txt = lrc_to_srt(lrc)
            with open(file, 'w', encoding="utf-8") as f:
                f.write(txt)
        # except Exception as e:
            # messagebox.showerror(title="發生錯誤", message=f'無法儲存檔案: "{file}"，錯誤: "{e}"')


def mills_to_lrc_time(ms):
    cs = ms % 1000 // 10
    m = ms // 1000 // 60
    s = ms // 1000 % 60
    return f"{m:02d}:{s:02d}.{cs:02d}"

def lrc_listed_to_lrc_list(lrc: list) -> list:
    converted = []
    pattern = re.compile(r'\[(\d+):(\d+)(?:\.(\d+))?\]')
    for i in lrc:
        with_time = False  
        if i == "": continue
        time = pattern.findall(i)
        text = pattern.sub('', i).strip()
        for m, s, cs in time:
            ms = int(m) * 60 * 1000 + int(s) * 1000
            if cs:
                if len(cs) == 2: ms += int(cs) * 10
                elif len(cs) == 3: ms += int(cs)
            converted.append([ms,text])
            with_time = True
        if not with_time:
            converted.append([-1,text])
    return converted

def lrc_list_to_lrc_listed(lrc_list: list) -> list:
    converted = []
    for i in lrc_list:
        if i[0] != -1:
            converted.append(f"[{mills_to_lrc_time(i[0])}]{i[1]}")
        else:
            converted.append(i[1])
    return converted


def lrc_to_txt(lrc: str) -> str:
    lrc_lines = lrc.split("\n")
    txt_lines = []
    for i in lrc_lines:
        txt_lines.append(i[10:])
    return "\n".join(txt_lines)

def lrc_to_srt(lrc: str) -> str:
    lrc_lines = lrc_listed_to_lrc_list(lrc.split('\n'))
    srt_lines = []

    def ms_to_srt_time(ms):
        if ms == -1:
            return "00:00:00,000"

        h = ms // 3600000
        m = (ms % 3600000) // 60000
        s = (ms % 60000) // 1000
        ms = ms % 1000

        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    for i in range(len(lrc_lines)):
        srt_lines.append(f"{i+1}")
        if i+1 <= len(lrc_lines) - 1:
            srt_lines.append(f"{ms_to_srt_time(lrc_lines[i][0])} --> {ms_to_srt_time(lrc_lines[i+1][0])}")
        else:
            srt_lines.append(f"{ms_to_srt_time(lrc_lines[i][0])} --> {ms_to_srt_time(lrc_lines[i][0])}")
        srt_lines.append(lrc_lines[i][1])
        srt_lines.append('')

    return '\n'.join(srt_lines)


def open_file():
    file = filedialog.askopenfilename(title="請選擇 mp3 檔案", filetypes=[("Audio files", "*.mp3")])
    if file:
        return file
    else:
        raise FileNotFoundError
    
def initialize():
    global file_path, audio
    try:
        file_path = open_file()
        try:
            audio = ID3(file_path)
        except ID3NoHeaderError:
            audio = ID3()
            audio.save(file_path)
        load_data(audio)
    except FileNotFoundError:
        raise FileNotFoundError
    

def mark_modified(*args):
    global file_modified
    if not file_modified:
        root.title(f'*"{file_path}" - just mp3 tagger')
        file_modified = True

def clear_modified():
    global file_modified
    file_modified = False
    root.title(f'"{file_path}" - just mp3 tagger')


def on_exit():
    if file_modified:
        answer = messagebox.askyesnocancel(title="有未儲存的變更", message=f'是否儲存對 "{file_path}" 的變更?')
        if answer is None:
            return
        elif answer:
            save_file(audio=audio, hint=False)
    try:
        os.remove("cover.jpg")
    except FileNotFoundError:
        pass
    root.destroy()





# Load the MP3 file
try:
    file_path = open_file()
except FileNotFoundError:
    exit()

# Load ID3 tags
try:
    audio = ID3(file_path)
except ID3NoHeaderError:
    audio = ID3()
    audio.save(file_path)





# Window
root = tk.Tk()
root.title("just mp3 tagger")
root.geometry("900x500")





# Synchorinized Lyrics Window
def lyrics_window():
    window = tk.Toplevel(root)
    window.title("編輯同步歌詞 (lrc)")

    audio_info = MP3(file_path)
    length = int(audio_info.info.length) * 1000
    length_in_lrc_time = mills_to_lrc_time(length)
    lrc = lrc_listed_to_lrc_list(lyrics_entry.get('1.0', 'end').split('\n'))
    mixer.init()
    mixer.music.load(file_path)
    mixer.music.play()
    mixer.music.pause()
    is_playing = False
    current_line = -2
    # pygame.mixer.music.get_pos() only returns time since music played so we need an offset if we forward
    offset_mills = 0

    def play_pause():
        nonlocal is_playing
        if is_playing:
            mixer.music.pause()
            is_playing = False
        else:
            mixer.music.unpause()
            is_playing = True
        update_time()

    def update_time():
        try:
            pos = mixer.music.get_pos() + offset_mills
            time_label.config(text=f"{mills_to_lrc_time(pos)} / {length_in_lrc_time}")
            progress_bar.config(value=pos)
        except:
            pass
        finally:
            if is_playing:
                window.after(10, update_time)
    
    def forward(sec: int):
        nonlocal offset_mills
        offset_mills = ((mixer.music.get_pos() + offset_mills) // 1000 + sec) * 1000
        pos = offset_mills // 1000
        mixer.music.stop()
        mixer.music.play(start=pos)
        update_time() # update progress bar
        if not is_playing: mixer.music.pause()

    def sync_current():
        nonlocal lrc
        lrc[current_line+1][0] = mixer.music.get_pos() + offset_mills
        next_lyric()

    def next_lyric():
        nonlocal current_line
        if current_line+1 <= len(lrc)-1:
            current_line += 1
            try:
                if current_line == -1: raise IndexError()
                current_label.config(text=f"{mills_to_lrc_time(lrc[current_line][0]) if lrc[current_line][0] != -1 else ''} {lrc[current_line][1]}")
            except IndexError:
                current_label.config(text="")


            next_line = current_line + 1
            try:
                next_label.config(text=f"{mills_to_lrc_time(lrc[next_line][0]) if lrc[next_line][0] != -1 else ''} {lrc[next_line][1]}")
            except IndexError:
                next_label.config(text="")
            
            next_line += 1
            try:
                next2_label.config(text=f"{mills_to_lrc_time(lrc[next_line][0]) if lrc[next_line][0] != -1 else ''} {lrc[next_line][1]}")
            except IndexError:
                next2_label.config(text="")
    
    def last_lyric():
        nonlocal current_line
        if current_line-1 >= -1:
            current_line -= 1
            try:
                if current_line == -1: raise IndexError()
                current_label.config(text=f"{mills_to_lrc_time(lrc[current_line][0]) if lrc[current_line][0] != -1 else ''} {lrc[current_line][1]}")
            except:
                current_label.config(text="")
            
            next_line = current_line + 1
            try:
                next_label.config(text=f"{mills_to_lrc_time(lrc[next_line][0]) if lrc[next_line][0] != -1 else ''} {lrc[next_line][1]}")
            except IndexError:
                next_label.config(text="")
            
            next_line += 1
            try:
                next2_label.config(text=f"{mills_to_lrc_time(lrc[next_line][0]) if lrc[next_line][0] != -1 else ''} {lrc[next_line][1]}")
            except IndexError:
                next2_label.config(text="")

    def on_exit():
        mixer.music.stop()
        lyrics_new = lrc_list_to_lrc_listed(lrc)
        lyrics_entry.delete('1.0', 'end')
        lyrics_entry.insert("1.0", '\n'.join(lyrics_new).rstrip('\n'))
        mixer.quit()
        window.destroy()

    current_label = ttk.Label(window)
    current_label.pack(anchor='w')
    ttk.Label(window, text="接下來的歌詞:").pack(anchor='w')
    next_label = ttk.Label(window, font=("Arial", 14))
    next_label.pack(anchor='w')
    next2_label = ttk.Label(window)
    next2_label.pack(anchor='w')

    progress_bar = ttk.Progressbar(window)
    progress_bar.config(maximum=length, length=720)
    progress_bar.pack()

    time_label = ttk.Label(window, text=f"00:00.00 / {length_in_lrc_time}")
    time_label.pack()

    control_area = tk.Frame(window)
    control_area.pack()
    b5_button = ttk.Button(window, text="倒退5秒", command=lambda: forward(-5))
    b5_button.pack(side='left')
    play_button = ttk.Button(window, text="播放/暫停", command=play_pause)
    play_button.pack(side='left')
    n5_button = ttk.Button(window, text="前進5秒", command=lambda: forward(5))
    n5_button.pack(side='left')

    next_lrc_button = ttk.Button(window, text="前往下一歌詞", command=next_lyric)
    next_lrc_button.pack(side='right')
    time_code_button = ttk.Button(window, text="綁定粗體歌詞至目前時間", command=sync_current)
    time_code_button.pack(side='right')
    last_lrc_button = ttk.Button(window, text="前往上一歌詞", command=last_lyric)
    last_lrc_button.pack(side='right')
    
    next_lyric()
    update_time()
    window.protocol("WM_DELETE_WINDOW", on_exit)





# Left: Cover
left_frame = tk.Frame(root)
left_frame.pack(side="left", padx=10, pady=10, anchor="n")

image_label = ttk.Label(left_frame, text="專輯圖片")
image_label.pack()
resolution_label = ttk.Label(left_frame, text="解析度：")
resolution_label.pack()

ttk.Button(left_frame, text="移除圖片", command=remove_album_art).pack(pady=5)
ttk.Button(left_frame, text="更換圖片", command=change_album_art).pack(pady=5)
ttk.Button(left_frame, text="匯出圖片", command=export_album_art).pack(pady=5)


# Right: Controls
right_frame = tk.Frame(root)
right_frame.pack(side="left", anchor="n", padx=10, pady=10)

ttk.Label(right_frame, text="標題").pack(anchor="w", pady=5)
title_entry = ttk.Entry(right_frame)
title_entry.bind("<KeyRelease>", mark_modified)
title_entry.pack(pady=5)

ttk.Label(right_frame, text="作者 (使用 '/' 分隔)").pack(anchor="w", pady=5)
artist_entry = ttk.Entry(right_frame)
artist_entry.bind("<KeyRelease>", mark_modified)
artist_entry.pack(pady=5)

ttk.Label(right_frame, text="專輯").pack(anchor="w", pady=5)
album_entry = ttk.Entry(right_frame)
album_entry.bind("<KeyRelease>", mark_modified)
album_entry.pack(pady=5)

ttk.Label(right_frame, text="年份").pack(anchor="w", pady=5)
date_entry = ttk.Entry(right_frame)
date_entry.bind("<KeyRelease>", mark_modified)
date_entry.pack(pady=5)

ttk.Label(right_frame, text="類別").pack(anchor="w", pady=5)
genre_entry = ttk.Entry(right_frame)
genre_entry.bind("<KeyRelease>", mark_modified)
genre_entry.pack(pady=5)

ttk.Label(right_frame, text="#").pack(anchor="w", pady=5)
track_entry = ttk.Entry(right_frame)
track_entry.bind("<KeyRelease>", mark_modified)
track_entry.pack(pady=5)

ttk.Label(right_frame, text="評論").pack(anchor="w", pady=5)
comment_entry = ttk.Entry(right_frame)
comment_entry.bind("<KeyRelease>", mark_modified)
comment_entry.pack(pady=5)

ttk.Button(right_frame, text="儲存", command=lambda: save_file(audio=audio, hint=True)).pack(pady=5)


# Lyrics frame
lyrics_frame = tk.Frame(root)
lyrics_frame.pack(side="left", anchor="n", padx=10, pady=10)

ttk.Label(lyrics_frame, text="歌詞 (lrc)").pack(anchor="w", pady=5)
lyrics_entry = tk.Text(lyrics_frame, font=("Arial", 14), wrap="none")
lyrics_entry.bind("<KeyRelease>", mark_modified)
lyrics_entry.pack(pady=5)


# Menu bar
menubar = tk.Menu(root)

file_menu = tk.Menu(menubar, tearoff=0)
file_menu.add_command(label="開啟檔案", command=initialize)
file_menu.add_command(label="儲存檔案", command=lambda: save_file(audio=audio, hint=True))
file_menu.add_command(label="另存新檔")
file_menu.add_separator()
file_menu.add_command(label="離開",command=on_exit)
menubar.add_cascade(label="檔案",menu=file_menu)

edit_menu = tk.Menu(menubar, tearoff=0)
edit_menu.add_command(label="撤銷所有變更", command=lambda: load_data(audio))
edit_menu.add_separator()
edit_menu.add_command(label="移除專輯圖片", command=remove_album_art)
edit_menu.add_command(label="變更專輯圖片", command=change_album_art)
edit_menu.add_command(label="匯出專輯圖片", command=export_album_art)
edit_menu.add_separator()
lyrics_menu = tk.Menu(edit_menu, tearoff=0)
lyrics_menu.add_command(label=".srt 檔案", command=lambda: export_lyrics("srt"))
lyrics_menu.add_command(label=".lrc 檔案", command=lambda: export_lyrics("lrc"))
lyrics_menu.add_command(label=".txt 檔案 (不含時間戳記)", command=lambda: export_lyrics("txt"))
edit_menu.add_command(label="上傳字幕檔案", command=upload_lyrics)
edit_menu.add_cascade(label="匯出字幕檔案", menu=lyrics_menu)
edit_menu.add_command(label="編輯同步歌詞", command=lyrics_window)
menubar.add_cascade(label="編輯",menu=edit_menu)

help_menu = tk.Menu(menubar, tearoff=0)
help_menu.add_command(label="關於 just-mp3-tagger", command=lambda: messagebox.showinfo(title="關於", message="just-mp3-tagger v1.1\n2025.05.29"))
menubar.add_cascade(label="說明",menu=help_menu)

root.config(menu=menubar)





# Start GUI
load_data(audio)
root.protocol("WM_DELETE_WINDOW", on_exit)
root.mainloop()