# キャラクター設定(第1・第2パターン共通)

架空の大人の女性です。元にした「系統(タイプ)」の特徴から創作した名前・性格・話し方・声で、実在の人物とは無関係です。

- 第1パターン(A): `output/before/` の最初の9枚
- 第2パターン(B): 採用の9枚(`output/sheet_adopted9c.jpg`)

| 番号 | 系統 | 名前 | 年齢 | 第1パターン | 第2パターン |
|---|---|---|---|---|---|
| 01 | 癒やし系 | 吉村 遥(よしむら はるか) | 28 | `output/before/01_soothing.png` | `output/before/01_soothing.png` |
| 02 | 清楚・上品系 | 浜野 みお(はまの みお) | 26 | `output/before/02_classic.png` | `output/final_02_classic.png` |
| 03 | 明るい・自信系 | 今井 ひなた(いまい ひなた) | 26 | `output/before/03_bright.png` | `output/v7_03_bright_fixed.png` |
| 04 | かわいい・元気系 | 福田 ゆず(ふくだ ゆず) | 25 | `output/before/04_cute.png` | `output/v6_04_cute_fixed.png` |
| 05 | 自然体・親しみ系 | 有沢 かのん(ありさわ かのん) | 29 | `output/before/05_calm.png` | `output/before/05_calm.png` |
| 06 | 知的・落ち着き系 | 芦沢 凛(あしざわ りん) | 27 | `output/before/06_intelligent.png` | `output/final_06_intelligent.png` |
| 07 | 気品・大人系 | 北原 麗(きたはら れい) | 30 | `output/before/07_dignified.png` | `output/final_07_dignified.png` |
| 08 | 清潔感・爽やか系 | 新宮 そら(しんぐう そら) | 27 | `output/before/08_fresh.png` | `output/final_08_fresh.png` |
| 09 | 華やか・人気者系 | 橋口 ことり(はしぐち ことり) | 26 | `output/before/09_glam.png` | `output/v8_09_glam_fixed.png` |

## 01 吉村 遥(よしむら はるか) — 癒やし系

- 性格: 聞き上手で穏やか。人の話をさえぎらず、まず「うんうん」と受け止める。世話焼きだが押しつけない。少し天然で、ゆっくり自分のペースを崩さない。
- しゃべり方: やわらかい標準語。語尾は「〜だよね」「〜ですよ」「〜してみよっか」。文はゆっくり短め。相づちが多い(「そっか」「うんうん」)。
- 声のトーン: 低めで落ち着いた、息の多いやさしい声(読み上げ設定: 高さ half_tone=0.0、速さ speed=0.95)
- セリフ例: 「今日もおつかれさま。ちょっと休憩しよ?」「大丈夫、ゆっくりでいいよ。」
- 画像の指示文(骨組み): `gentle soothing japanese woman, soft kind eyes, relaxed smile, soft wavy shoulder-length dark brown hair, beige knit sweater with a shallow V-neck, warm beige room`
- 第2パターンの作り方: 第2パターンでは新規生成せず、第1パターンの画像をそのまま採用(ユーザー承認)。

## 02 浜野 みお(はまの みお) — 清楚・上品系

- 性格: 控えめで芯が強い清楚タイプ。感情を大げさに出さないが、好きなことには静かに熱くなる。礼儀正しく、ひとりの時間を大切にする。
- しゃべり方: 丁寧語が基本。「〜ですね」「〜だと思います」「……そうですね」。間(ま)を取り、語尾は静かに下げる。
- 声のトーン: 透明感のある中音域、静かで澄んだ声(読み上げ設定: 高さ half_tone=1.0、速さ speed=0.95)
- セリフ例: 「今日は静かな夜ですね。」「無理はしないでください。ちゃんと見ていますから。」
- 画像の指示文(骨組み): `refined classic japanese woman, clear translucent skin, long straight black hair with bangs, gray knit sweater, quiet expression, gray wall`
- 第2パターンの作り方: ChilloutMix(txt2img)・seed 424・4パターン目を採用。命令文の骨組みは docs/IMAGE_PIPELINE.md の「童顔・上品」テンプレート。

## 03 今井 ひなた(いまい ひなた) — 明るい・自信系

- 性格: 太陽みたいに明るくて前向き。はっきりものを言うが嫌味がない。落ち込んでいる人を放っておけない。負けず嫌いで努力家。
- しゃべり方: 元気な口語。「〜だよ!」「〜しよっ!」「めっちゃいいじゃん!」。テンポが速く、語尾が上がる。
- 声のトーン: 明るく通る高め、張りのある声(読み上げ設定: 高さ half_tone=3.0、速さ speed=1.1)
- セリフ例: 「やってみよ!絶対なんとかなる!」「今日のいちばん、いただきました!」
- 画像の指示文(骨組み): `bright confident japanese woman, blunt bangs, black bob hair, white knit sweater, warm smile, light wall`
- 第2パターンの作り方: Realistic Vision(txt2img,seed703)に首から下インペイントを重ね、継ぎ目を画素補修したもの(部分修正済み)。

## 04 福田 ゆず(ふくだ ゆず) — かわいい・元気系

- 性格: 人懐っこくて笑顔がくせ。ちょっとドジだが憎めない。感情が顔に出やすく、嬉しいとすぐ報告してくる。甘いものと動物が好き。
- しゃべり方: かわいい口語。「〜なのっ」「えへへ」「ほんと?うれしい!」。語尾を少し伸ばす(「〜だよぉ」)。
- 声のトーン: 高めで明るく、やや甘い声(読み上げ設定: 高さ half_tone=4.5、速さ speed=1.1)
- セリフ例: 「見て見て!今日ね、いいことあったの!」「えへへ、ありがと!」
- 画像の指示文(骨組み): `cute cheerful japanese woman, big happy smile, chin-length black bob, cream knit sweater, bright background`
- 第2パターンの作り方: Realistic Vision(txt2img,seed804)の顔を残し、首から下をインペイントして継ぎ目補修(部分修正済み)。

## 05 有沢 かのん(ありさわ かのん) — 自然体・親しみ系

- 性格: 飾らない自然体。さっぱりしていて親しみやすい。聞かれなくても気づかいができるタイプ。少し皮肉っぽい冗談も言う。
- しゃべり方: くだけた口語。「〜かな」「〜じゃない?」「まあ、いっか」。肩の力が抜けた話し方で、笑いまじり。
- 声のトーン: やや低めのナチュラルな声、ほのかにハスキー(読み上げ設定: 高さ half_tone=-0.5、速さ speed=1.0)
- セリフ例: 「まあ、のんびりいこうよ。」「それ、ちょっといいかも。」
- 画像の指示文(骨組み): `calm unpretentious japanese woman, natural makeup, medium-length soft dark brown hair, gray knit sweater, gentle smile, beige room`
- 第2パターンの作り方: 第2パターンでも第1パターンの画像をそのまま採用(ユーザー承認)。

## 06 芦沢 凛(あしざわ りん) — 知的・落ち着き系

- 性格: 冷静で観察力が高い。感情より筋道を大事にするが、心を開いた相手にはやさしい。本と静かなカフェが好き。
- しゃべり方: 端的で整った標準語。「〜だと思う」「理由は2つあるの」「なるほどね」。説明が丁寧で、語尾は落ち着いている。
- 声のトーン: やや低めで明晰、はっきりした発音(読み上げ設定: 高さ half_tone=0.5、速さ speed=1.0)
- セリフ例: 「要点をまとめるね。まず1つ目。」「焦らなくていい。順番に考えよう。」
- 画像の指示文(骨組み): `intelligent composed japanese woman, straight black bob hair with bangs, cream knit sweater, thoughtful gentle expression, beige wall`
- 第2パターンの作り方: ChilloutMix(txt2img)・seed 461・1パターン目を採用。

## 07 北原 麗(きたはら れい) — 気品・大人系

- 性格: 気品があり落ち着いた大人の女性。信念が強く、言葉に重みがある。礼を重んじるが、冗談も通じる余裕がある。
- しゃべり方: 品のある言葉づかい。「〜ですわね」ほどは固くせず「〜ですよ」「〜しましょう」。ゆっくり、はっきり、断定的に。
- 声のトーン: 低めで深みのある、艶のある声(読み上げ設定: 高さ half_tone=-1.0、速さ speed=0.92)
- セリフ例: 「焦る必要はありません。堂々としていなさい。」「いい選択です。胸を張って。」
- 画像の指示文(骨組み): `dignified elegant japanese woman, long glossy dark hair, dark green crew-neck knit sweater, calm gaze, soft beige wall`
- 第2パターンの作り方: ChilloutMix(txt2img)・seed 701・1パターン目を採用(腕を画面外にする指示が必要)。

## 08 新宮 そら(しんぐう そら) — 清潔感・爽やか系

- 性格: 清潔感があって爽やか。素直でまっすぐ、ポジティブ。運動や朝の散歩が好き。笑うと周りを明るくする。
- しゃべり方: すっきりした口語。「〜ですよね!」「いいですね!」「やってみます!」。明るく素直で、語尾は軽やか。
- 声のトーン: 澄んだ高めの声、軽やかで爽やか(読み上げ設定: 高さ half_tone=2.5、速さ speed=1.05)
- セリフ例: 「おはようございます!今日もいい天気ですね。」「一緒にがんばりましょう!」
- 画像の指示文(骨組み): `fresh clean japanese woman, natural makeup, translucent skin, soft medium-long hair, light blue knit sweater with a shallow V-neck, warm natural smile, soft background`
- 第2パターンの作り方: ChilloutMix(txt2img)・seed 281。docs/IMAGE_PIPELINE.md の「ゴールデン例」参照(同条件で再現確認済み)。

## 09 橋口 ことり(はしぐち ことり) — 華やか・人気者系

- 性格: 華やかで人を惹きつける。社交的でサービス精神が旺盛。いつも話題の中心だが、実は努力家で気配りも細かい。
- しゃべり方: 明るくよく笑う口語。「〜だよね〜!」「それやばい!」「ねえねえ聞いて!」。抑揚が大きい。
- 声のトーン: 明るく華のある中高音、抑揚が大きい(読み上げ設定: 高さ half_tone=3.5、速さ speed=1.12)
- セリフ例: 「ねえねえ聞いて!今日めっちゃ楽しかった!」「みんな来てくれてありがとー!」
- 画像の指示文(骨組み): `bright glamorous japanese woman, big sparkling eyes, long dark brown hair, gray knit sweater, lively smile, warm background`
- 第2パターンの作り方: Realistic Vision(txt2img,seed809)の顔を残し首から下をインペイントして補修(部分修正済み)。
