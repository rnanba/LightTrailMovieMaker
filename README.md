# LightTrailMovieMaker v0.1

## 概要

流星等を撮影した動画を「ライブコンポジット」的に時間経過に沿って比較明合成していく動画に変換するツールです。

出現した流星の光跡が後までずっと残るので通常の動画では見逃してしまう流星を見つけることができます。また、全フレームを比較明合成した画像と比べて、どの流星がいつ流れたのかを特定できるメリットがあります。

SharpCap で記録した SER ファイルまたは PNG ファイル用として作成しましたが、ffmpeg で読み込める動画形式、Pillow で読み込める画像形式なら同様に扱えるはずです。

## 出力サンプル

<video src="https://www.flickr.com/photos/rnanba/53928500895/play/1080p/882c15b91b"></video>

## 動作環境

以下の環境で動作を確認しています。

- python 3.10.12
  - av 12.3.0
  - numpy 2.0.1
  - opencv-python 4.10.0.84
  - pillow 10.4.0

venv 環境で `pip install -r requirments.txt` でモジュールをインストールして動作確認しています。

OS は Ubuntu 22.04 と Windows 11 で動作を確認ています。macOS でも動くように作ってありますが確認はしていません。以下の使用例では Linux の bash でのコマンドラインを例示しています。

## 使用方法

```
usage: ltmm.py [-h] [--out-dir OUT_DIR] [--out-ext OUT_EXT]
               [--start-frame START_FRAME] [--end-frame END_FRAME]
               [--frame-rate FRAME_RATE] [--font FONT] [--font-size FONT_SIZE]
               [--font-color FONT_COLOR] [--text-position TEXT_POSITION]
               [--video-codec VIDEO_CODEC] [--video-bit-rate VIDEO_BIT_RATE]
               [--debayer-image DEBAYER_IMAGE] [--no-frame-count]
               input_files_or_dirs [input_files_or_dirs ...]
```

### 出力ファイル名

出力ファイル名は入力ファイル名の末尾に `-max` を付けたものになります。拡張子はデフォルトでは `.mp4` です。`--start-frame START_FRAME` または `--end-frame END_FRAME` でフレーム範囲を指定した場合はファイル名末尾が `-max-`*{開始フレーム番号}*_*{終了フレーム番号}* になります。

### 引数

| 引数                  | 説明 |
|-----------------------|------|
| `input_files_or_dirs` | 入力する動画ファイルまたは連番ファイル名の画像ファイルが保存されたディレクトリを指定します。複数指定するとそれぞれについて一つの動画を生成します。ワイルドカードを使用したファイル名指定も可能です。 |

### オプション

| オプション                        | 説明                                                                                                                                        | デフォルト値 |
|-----------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------|--------------|
| `--out-dir OUTDIR`                | 出力動画の保存祭ディレクトリを指定します。                                                                                                  | `.`          |
| `--out-ext OUT_EXT`               | 出力動画のフォーマットを拡張子で指定します。                                                                                                | `.mp4`       |
| `--start-frame START_FRAME`       | 入力動画の読込開始フレームを指定します。                                                                                                    | `0`          |
| `--end-frame END_FRAME`           | 入力動画の読込終了レームを指定します。指定がなければ最後まで読み込みます。                                                                  |              |
| `--frame-rate FRAME_RATE`         | 出力動画のフレームレートを指定します。指定がなければ入力動画のメタデータにある平均ビットレートを使用します(後述)。                          |              |
| `--font FONT`                     | フレームカウント表示のフォントを指定します。指定がなければ環境から推定した Courier New フォントを使用します(後述)。                         | `24`         |
| `--font-size FONT_SIZE`           | フレームカウント表示のフォントサイズを指定します(単位はピクセル)。                                                                          |              |
| `--font-color FONT_COLOR`         | フレームカウント表示の文字色を指定します。HTML/CSSのカラーコードが使えます。                                                                | `#FF8888`    |
| `--text-position TEXT_POSITION`   | フレームカウントの表示位置を `top-left`, `top-middle`, `top-right`, `bottom-left`, `bottom-middle`, `bottom-right` のいずれかで指定します。 | `top-left`   |
| `--video-codec VIDEO_CODEC`       | 出力動画のコーデックを ffmpeg のコーデック名で指定します。                                                                                  | `libx264`    |
| `--video-bit-rate VIDEO_BIT_RATE` | 出力動画のビットレート(単位はbps)を指定します。                                                                                             | `12M`        |
| `--debayer-image DEBAYER_IMAGE`   | 入力動画フレームのデベイヤーが必要な場合にベイヤーパターンを `RGGB`, `GRBG`, `GBRG`, `BGGR` のいずれかで指定します(後述)。                  |              |
| `--no-frame-count`                | フレームカウント表示を無効にする場合に指定します。                                                                                          |              |

### フレームレートについて

デフォルトでは入力動画のメタデータから平均フレームレートを取得してそれを出力動画のフレームレートにします。メタデータから平均フレームレートが取得できない場合は明示的に `--frame-rate FRAME_RATE` オプションを指定しないとエラーになります。SER ファイルの場合メタデータに平均ビットレートが含まれないためこのオプションの指定が必須になります。

### フォントについて

デフォルトでは Windows, Linux(Ubuntu 等のディストリビューション), macOS がシステムに標準で持つ Courier New フォントを使用します。他の OS では明示的に `--font FONT` オプションを指定しないとエラーになります。`FONT` に指定するのは TrueType フォントのフォントファイル名です。詳細は[Pillow の ImageFont の説明](https://pillow.readthedocs.io/en/stable/reference/ImageFont.html)を参照してください。

### デベイヤーについて

このツールは ffmpeg 経由で動画を読み込むためカラーカメラで RAW 記録した SER ファイルでも自動的にデベイヤー処理した形でフレームを読み込みます。しかし SharpCap で RAW 記録された PNG 画像等を読み込む場合は `--debayer-image DEBAYER_IMAGE` オプションでベイヤーパターンを指定しないとモノクロのまま出力されます。

### 使用例

SER 動画ファイル `input.ser` を変換してフレームレート 15.9 fps の動画として出力するには以下のようにします。出力ファイル名は `input-max.mp4` になります。

```
./ltmm.py --frame-rate 15.9 input.ser
```

## ライセンス

MITライセンスです。
