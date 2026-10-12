---
name: persona-images
description: 架空の大人の女性キャラクター(1〜9番)の画像・声・設定を、このリポジトリの手順で新規生成するときに使う。人物画像を作る、作り直す、キャラの性格や声を使う、といった依頼で読む。
---

# 人物画像の作成(persona-images)

1. まず `docs/IMAGE_PIPELINE.md` を最後まで読む(約束事・許可・失敗の記録がある)。
2. 設定は `characters/characters.json`。名前・性格・しゃべり方・声(高さ half_tone と速さ speed)・セリフ例・指示文の骨組みが入っている。
3. 環境の確認: `bash scripts/setup_env.sh`。モデルが「なし」なら、ユーザーにネット許可(huggingface 関連4ドメイン)の追加をお願いしてから `bash scripts/setup_env.sh --models`。終わったら許可を外すよう伝える。
4. 生成: `python scripts/generate_persona.py <番号> --seeds ...`(背景実行・Monitor で進み具合を見る)。1人 4〜6 パターン。
5. 見せる前に、チェックリスト(docs の4章)で1枚ずつ確認。不採用は削除。採用した画像だけコミット&プッシュ。
6. 声の見本: `python scripts/persona_voice.py <番号>`。
7. 禁止: 部分的な修正(許可があるまで)、実在人物名の使用、勝手な有料ツールの使用。

## アニメ画像のとき(実写風との違い)
- モデルは `Meina/MeinaMix_V11`(別に取得が必要。ネット許可は実写風と同じ4ドメイン)。DreamShaper は写真風になるので使わない。
- 生成は `python scripts/generate_anime.py`(A=実物風アニメ、B=完全アニメ。各3候補)。最初に1人だけ試作して、画風をユーザーに確認してから全員を作る。
- 全員20代半ばの大人として指定し、制服・子ども系の語は negative に入れる。指示文は77トークンを超えると末尾が切れる。
- 声はアニメ版だけ高く明るく: `python scripts/persona_voice.py <番号> --style A|B`(設定は characters.json の voice_anime)。
- 詳しくは `docs/IMAGE_PIPELINE.md` の8章。

