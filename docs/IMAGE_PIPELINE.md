# 人物画像の作成手順(別のセッションでもすぐ再現するための手引き)

このリポジトリで、架空の大人の女性キャラクターの縦長画像(512×768)を作った手順と、そのとき分かったことをまとめたものです。
キャラクター設定は `characters/characters.json`(読みやすい版は `characters/CHARACTERS.md`)。

## 0. 先に守るルール(ユーザーとの約束)
1. 日本語で話す。専門用語は使ったあとに(  )で補足する。初心者向けに。
2. 答えが複数あるときは、おすすめを先に出す。情報が足りないときは推測せず質問する。
3. 時刻は必ず日本時間(JST)で言う。生成中かどうかは、実際にプロセスを確認してから報告する。
4. **部分的な修正(一部だけ描き直す・画素を直接いじって継ぎ目を直す)は禁止。** ユーザーが「いい」と言うまで使わない。直したいときは画像全体を新しく生成し直す。
5. 勝手に有料の道具(vidIQ など)を使わない。使う前に必ず聞く。
6. 出てくる人物はすべて架空の大人の女性。実在の人物の名前を指示文に入れない。実在の人物そっくりにも作らない。
7. 画像は、必ず目で確認してから見せる。露出が多すぎるもの・透ける服・肩ひもだけの服は不採用にして削除する(法律ではなく、投稿の表示が減るのを避けるための基準)。
   - 採用してよい: 丸首、浅いV字、肩が少し出る服。
   - 採用しない: 胸の谷間がはっきり見える、透ける、肩ひもだけ、太ももや下半身が出る。
8. 腕を交差した構図はうまく作れないので、指示文で「腕は体の横・画面の外」にする。

## 1. 許可(ネットワーク)
- モデルの最初のダウンロードのときだけ、環境の「ネットワーク許可」に次のドメインを追加する(ユーザーが設定画面で行う)。
  - `huggingface.co`
  - `us.aws.cdn.hf.co`
  - `cas-bridge.xethub.hf.co`
  - `cas-server.xethub.hf.co`
- ダウンロードが終わったら、許可はすべて外してよい(以後は `HF_HUB_OFFLINE=1` でオフライン動作)。
- **クラウド環境が回収されるとモデルも消える。** その場合は同じ手順でもう一度取得する。画像は消える前にローカルへダウンロードしておく。
- 許可の追加方法が分からないときは、Claude が `read_documentation`(topic: `environment.network`)を読んで案内する。
- コマンドの実行許可(Bash の毎回確認)を減らしたいときは `.claude/settings.json` の allow 一覧を使う。これはリポジトリに入れてある。

## 2. 環境の準備
```
bash scripts/setup_env.sh            # ライブラリを入れ、モデルの有無を確認
bash scripts/setup_env.sh --models   # モデルを取得(上のネット許可が必要・初回だけ・容量が大きい)
```
- Python 3.13、torch(CPU のみ)、diffusers、transformers、accelerate、peft。GPU は無いので1枚あたり約 60〜130 秒。
- 使うモデル
  - `stablediffusionapi/chilloutmix`(.bin 形式): 柔らかいアイドル風の顔。ただし服の指定を守らず、露出が多くなりやすい。安全モード(weights_only)で読み込まれる。
  - `SG161222/Realistic_Vision_V5.1_noVAE`(safetensors): 服は安全に作れるが、顔が写真っぽく、アイドル風にならない。
  - `latent-consistency/lcm-lora-sdv1-5`: 高速化の部品(LCM-LoRA)。両方に組み合わせる。steps 8、guidance 1.5。

## 3. 画像を作る(ふだんの使い方)
```
python scripts/generate_persona.py --list
python scripts/generate_persona.py 07 --seeds 701 702 703 704 705 706     # 6パターン作って選ぶ
python scripts/generate_persona.py 02 06 --seeds 1 2 3 4 --out-prefix v31
python scripts/contact_sheet.py output/sheet.jpg output/a.png output/b.png ... --cols 3
```
- 1人あたり4〜6パターン作って、使えるものを選ぶのが基本(ChilloutMix は当たり外れが大きい)。
- 同じ指示文・同じ seed(乱数の種)なら、ほぼ同じ画像が再現できる(02・08 番は完全一致を確認済み)。
- 指示文の骨組みは `scripts/generate_persona.py`(PROMPT_HEAD と NEG_BASE)。
  - 童顔寄り: `youthful soft face, gentle round eyes, soft rounded cheeks`(年齢は20代半ば。子どもっぽく見える語は避け、negative に child 系を必ず入れる)。
  - 服: `loose oversized knit sweater` + 首元の指定(strict なら丸首で肩を覆う、relaxed なら浅いVや肩出しまで可)。
  - 胸の大きさ: `slim petite build, small bust` と negative の `large breasts, busty`。
  - 色の傾き・髪色のずれは、negative に `green hair, purple hair, colored hair` を入れて避ける。
- 生成は `HF_HUB_OFFLINE=1` で背景実行(nohup)し、できた画像を1枚ずつ見る。進み具合は Monitor で追う(複数の監視を重ねると通知が二重になる)。

### 採用画像の厳密な再現
- `characters/exact_recipes.json` に、採用した02・06・07・08の指示文・出さないもの・seed・モデルをそのまま記録してある。
- `python scripts/reproduce_adopted.py 08` で、同じ画像を作り直し、元画像との差を表示する(0なら完全一致)。
- 03・04・09 は、Realistic Vision の画像に首から下の描き直しと補修を重ねたもので、レシピ1つでは再現できない。作り直すなら `generate_persona.py` で新規生成する。
- 01・05 は最初の画像(ChilloutMix、`output/before/`)をそのまま採用。

## 4. 確認チェックリスト(見せる前に必ず)
- [ ] 顔が崩れていない(左右の目の大きさ、顔の斑点がない)
- [ ] 日本人の顔立ちに見える。大人に見える(童顔でも子どもっぽくしない)
- [ ] 首・肩・服のつなぎ目が自然(角ばった膨らみ、切れ目がない)
- [ ] 腕・手が不自然でない(交差・折れ曲がり・指の増減がない)
- [ ] 露出が基準内(上のルール7)
- [ ] 髪色が自然(緑・紫に傾いていない)
- 不採用の画像は削除する。リポジトリには採用したものだけをコミットする。

## 5. これまでに分かったこと(失敗の記録)
- ChilloutMix で「丸首」「肩を覆う」と書いても無視されることが多い。タートルネックなら確実に覆えるが、全員同じ服になってしまう。→ 人ごとに服を変え、浅いV・肩出しは許可しつつ、胸元が見えるものは選ばない。
- 首から下だけを描き直す(インペイント)方法は、継ぎ目・首の盛り上がり・腕の崩れが出やすい。画素を直接いじって直す方法も、何度やってもぼこぼこが残った。→ **全体の再生成が確実。**
- img2img(元画像を土台に弱く描き直す)で顔だけ童顔化しようとしても、肌がざらつき、かえって大人っぽくなった。
- Realistic Vision の顔は、アイドル風の柔らかい雰囲気にならない。
- 実在人物名を指示文に入れず、系統の特徴(髪型・雰囲気・服)だけを言葉にする。

## 6. 過去の部分修正スクリプト(参考。ユーザーが許可したときだけ使う)
`fix_seam_pixel.py`、`fix_hair06b.py`、`fix_neck_shift.py` など、リポジトリ直下の `fix_*.py` と `gen_inpaint*.py`、`gen_img2img.py`。

## 7. 参考: 画像ファイルの場所
- 第1パターン(最初の9枚): `output/before/`
- 第2パターン(採用の9枚): `output/sheet_adopted9c.jpg` と、`output/final_*.png`、`output/v7_03_bright_fixed.png`、`output/v6_04_cute_fixed.png`、`output/v8_09_glam_fixed.png`、`output/before/01_soothing.png`、`output/before/05_calm.png`
