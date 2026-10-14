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
