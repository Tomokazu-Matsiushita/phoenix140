# Project Phoenix 140 v3

CSV管理をやめ、SQLite DB・不動産入力フォーム・金融API連携の拡張口を持たせた版です。

## 起動方法（Mac M2）

```bash
cd ~/Downloads/Project_Phoenix_140_v3
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

初回起動時に `phoenix140.db` が自動作成され、サンプルデータが入ります。

## 主な機能

- Home：総資産・年間CF・FIRE進捗
- Financial：金融資産一覧、Moneytree連携の受け皿
- Real Estate：不動産情報を画面から追加・編集
- Units：部屋別の入居状況入力
- Monthly CF：月次収支入力
- AI CFO：月次レビュー風コメント
- Phoenix 140：健康データ連携の将来枠

## Version 4への拡張余地

- Moneytree公式API接続
- SBI証券または証券CSVインポート
- Oura / Garmin / Apple Health連携
- AI CFOのOpenAI API接続
- PostgreSQL移行
- Streamlit Cloud / Docker / iPhoneホーム画面対応

## 注意

本アプリは投資判断・税務判断の補助ツールです。最終判断は専門家にも確認してください。
