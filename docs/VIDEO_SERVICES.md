# 毎日20秒の動画: 安くて高品質なAI動画サービスの調査(2026-10-14)

注意: 出典の多くは、販売会社や、まとめサイトの記事です。料金・無料枠・順位は、記事によってばらつきます。使う前に、必ず各社の公式の料金ページで、最新の内容を確認してください。

## 必要な量
- 毎日20秒 = 5秒のクリップを4本(または10秒を2本)つなぐ。声・字幕・BGMは、こちら(`scripts/compose_video.py`)で重ねるので、AI側は「映像だけ」でよい。
- 月に換算すると、約600秒。

## 無料枠(検索で出た内容。未確認)
| サービス | 無料枠(目安) | 注意 |
|---|---|---|
| Kling | 1日あたり約66クレジット(標準の5秒の動画で約6本) | 透かし・利用制限あり。記事によっては「更新される枠が不明」 |
| Dreamina(CapCut) | 1日120クレジット | |
| PixVerse | 1日60クレジット | 無料の書き出しは透かし付き |
| Hailuo(MiniMax) | 1日3本程度(6秒・720p) | |
| Pika | 月80クレジット・480pまで | |
| Runway | 最初の125クレジットだけ(更新なし) | |
| Luma | 個人向けの継続的な無料プランなし | |
| Viggle | 無料枠あり(1日5本程度、透かし・720p、という記事あり) | 動きの見本(テンプレート)を人物の絵に当てる。歩く動きに向く可能性 |

→ 1日合計で20秒を、複数サービスの無料枠を組み合わせて作れる可能性がある。商用利用が許されるか、透かしを消せるかは、各サービスの利用規約を確認すること。

## 有料(1秒あたりの目安。まとめサイトの数字)
| サービス | 1秒あたり | 20秒/日 | 30日 |
|---|---|---|---|
| Vidu(360p・540p) | 約$0.035 | 約$0.7 | 約$21 |
| PixVerse(720p) | 約$0.04 | 約$0.8 | 約$24 |
| Veo 3.1 Lite(720p) | $0.05 | $1.0 | $30 |
| Hailuo(720p) | 約$0.07〜0.08 | 約$1.4〜1.6 | 約$42〜48 |
| Wan 2.6 | 約$0.07 | 約$1.4 | 約$42 |
| Seedance 2.0(480p) | 約$0.07 | 約$1.4 | 約$42 |
| Kling(公式API・音なし) | 約$0.084 | 約$1.7 | 約$50 |
- 画質の順位(1つのまとめサイトの順位): Seedance 2.0 Pro が2位、Kling 3.0 Pro が3位、Veo 3.1 Fast が9位。1つのサイトだけの順位なので、参考程度。
- 為替は変わるので、円には換算していない。

## アニメの人物・歩く動きの評価(販売会社の記事が中心。独立した比較は見つからなかった)
- 人物の一貫性: Vidu(参照画像で顔・服が保てる、という評価)、Kling 3.0、Seedance 2.5、Hailuo(頭を回しても特徴が保てる、という評価)。
- 歩く動き: 動きが大きいと、人物が参照画像から崩れやすい。ゆっくりした動きのほうが安定する。「ループする歩き、カメラは動かさない」を指示すると良い、という助言あり。
- Viggle: 動きの見本を、1枚の人物の絵に当てる方式。歩く動きの見本がある。

## 試す手順(無料)
1. 画像: `output/walk_final/walk_03_B.png`、`walk_07_B.png`(全身)。背景が単色に近い画像のほうが安定する。
2. 指示文(英語): `The anime girl walks forward confidently toward the camera, arms swinging naturally, hair and skirt flowing, smooth loopable walking motion, static camera, anime style`
3. 同じ画像・同じ指示文を、2〜3のサービス(Kling、Dreamina、Hailuo、Viggle)で試す。
4. 比べる観点: ①歩いているか ②顔・服が崩れないか ③手足の数・形 ④透かし ⑤1日に作れる量。
5. 良かったものの mp4 を、チャットにアップロード → 声・字幕・BGMを重ねて仕上げる(`compose_video.py`)。

## 20秒の組み立て案(5秒×4本)
1. 歩いてくる(全身) → 2. 立ち止まって手を振る(半身) → 3. 笑顔のアップ → 4. 振り向いて歩き去る。各クリップは、同じ人物の画像から作る。

## 出典
- [8 Best AI Video Generation APIs in 2026](https://apiframe.ai/blog/best-ai-video-generation-apis)
- [Cheapest AI Video Generation APIs in 2026 - Atlas Cloud](https://www.atlascloud.ai/blog/tips/cheapest-ai-video-generation-api-2026)
- [The cheapest AI video generation APIs in 2026 - Infer](https://tryinfer.com/pricing/cheapest-ai-video-api)
- [AI Video Generation Cost: Real Per-Second Rates](https://morphed.app/blog/ai-video-generation-cost)
- [Best AI Video Models Sept 2026: Ranked by Price per Second](https://www.teamday.ai/blog/best-ai-video-models-2026)
- [Best Free AI Photo-to-Video Tools 2026](https://dreamina.capcut.com/ai-video/best-free-ai-photo-to-video-tools)
- [Best free AI video generators in 2026 - Krea](https://www.krea.ai/blog/best-free-ai-video-generators-in-2026)
- [The Best AI Anime Video Generators of 2026 - PixVerse](https://pixverse.ai/en/blog/best-ai-anime-video-generators-2026)
- [Best AI video generator for consistent characters](https://blog.neural4d.com/comparisons/best-ai-video-generator-for-consistent-characters/)
- [Viggle 2.0 - aixploria](https://www.aixploria.com/en/viggle-2-0-ai/)

## 追記(2026-10-15): Gemini(Veo)と、全自動化の計画
### Gemini(Veo 3.1)の評価
- 公式の料金(Gemini API・1秒あたり・音声つき): Lite $0.05(720p)/$0.08(1080p)、Fast $0.10(720p)/$0.12(1080p)、Standard $0.40(720p・1080p)/$0.60(4K)。無料枠: **API には無い**(公式の料金ページに「Free Tier: Not available」)。
- 1本は約8秒(第三者の計算)。20秒/日 = 3本(24秒)として: Lite 720p ≒ $1.2/日 ≒ $36/月、Fast 720p ≒ $2.4/日 ≒ $72/月、Standard ≒ $9.6/日。
- 強み: 動きや物理の表現が強いとされる。**音声(セリフ・効果音)も同時に作れる**。公式APIで安定している。全自動に向く。
- 不明: アニメ絵の人物の一貫性、参照画像の仕様と料金(確認できず)。→ 実際に試して確認する。
- Gemini アプリ(画面)で作る場合は、Google AI の有料プランが必要で、自動化できない(検索結果より)。
- 出典: [Gemini Developer API pricing](https://ai.google.dev/gemini-api/docs/pricing)、[Veo 3.1 pricing (2026) - Magic Hour](https://magichour.ai/blog/veo-3-pricing)

### 全自動(Claude が作る)に必要なもの
1. APIキー(読み取り・生成用)を、環境の「Network secrets / 環境変数」に入れる。**キーをチャットに貼らない**。
2. 環境のネットワーク許可に、APIのドメインを足す(例: `generativelanguage.googleapis.com`、fal.ai を使うなら `fal.run` など)。
3. サービス側で、月の上限金額(予算の上限)を設定する。
4. スクリプト(これから作る): 画像+指示文 → 動画クリップ(複数) → `compose_video.py` で声・字幕・BGM → 20秒の縦動画。

### 激しい動きに強い候補(私が選ぶ3つ)
| 候補 | 理由 | 目安の費用 |
|---|---|---|
| Veo 3.1 Fast(Gemini API) | 動き・物理が強い。音声も作れる。公式API | $0.10/秒 |
| Seedance 2.0 | 画質の順位が高い(1つの比較サイト)。人物の一貫性の評価も高い | 約$0.07/秒(480p)〜 |
| Hailuo(02/2.3) | 動きの激しさに強い、とされる。いちばん安い部類 | 約$0.07〜0.08/秒 |
- 3つとも、同じ画像・同じ指示文・同じ長さ(5〜8秒)で比べる。費用は3本で約$2〜3。
- fal.ai などの窓口(1つのキーで複数のモデルが使える)を使うと、設定が1回で済む。料金は窓口ごとに違う(Kling は fal 経由が公式の約2.7倍、という記事あり)ので、公式と比べて選ぶ。
