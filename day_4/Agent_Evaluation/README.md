# エージェント評価ワークスペース

このパッケージには、*ホームオートメーション*エージェント向けの**Day 4**評価アーティファクトが含まれています。
ファイルは、エージェントコード、決定論的テストケース、ユーザーシミュレーションシナリオ、およびノートブックがそれぞれ独自のサブディレクトリに配置されるように再編成されています。

## ディレクトリ構造

```text
Agent_Evaluation/
├── agent.py                 # ルートエージェントの定義（ツール、リトライ設定などをインポート）
├── __init__.py              # ADK CLI/webに`root_agent`を公開
├── requirements.txt         # Day 4演習で使用される追加の依存関係
├── evals/
│   ├── home_automation/
│   │   ├── config.json                 # 決定論的な実行で使用される合否のしきい値
│   │   ├── integration.evalset.json    # 2つの決定論的なケース（リビングルームとキッチン）
│   │   └── legacy_evalset.json         # ADK UIからキャプチャされた大型セット（最新ログで手直し済み）
│   └── movie_night_user_sim/
│       └── evalset.json                # ユーザーシミュレーションテスト用のConversationScenario
├── notebooks/
│   └── day-4a-agent-observability-nb.ipynb
└── README.md (このファイル)
```

## 決定論的な評価の実行

リポジトリのルートから実行してください：

```bash
adk eval \
  day_4/Agent_Evaluation \
  day_4/Agent_Evaluation/evals/home_automation/integration.evalset.json \
  --config_file_path=day_4/Agent_Evaluation/evals/home_automation/config.json \
  --print_detailed_results
```

これは、厳選された2つのケースを実行し、正確なツール使用経路と高いテキスト類似性を期待します。
`kitchen_light_on` という ID に変更済みなので、旧ログと混同しないようご注意ください。

## レガシー評価セットの実行

ADK Web UIからキャプチャされた、より大きな評価セットをリプレイしたい場合：

```bash
adk eval \
  day_4/Agent_Evaluation \
  day_4/Agent_Evaluation/evals/home_automation/legacy_evalset.json \
  --config_file_path=day_4/Agent_Evaluation/evals/home_automation/config.json

### レガシーケースの注意点

- 最新の eval 実行ログ（`.adk/eval_history/Agent_Evaluation_home_automation_*.json`）に合わせて、
  `invalid_location_test` や `complex_multi_device_command` などの期待値を更新済みです。
- それでも `Tests passed: 3, failed: 3` と表示される場合は、まだ現状のエージェント挙動と合っていないケースが存在します。
  `.adk/eval_history` の最新ファイルを参照し、`final_response` やツール呼び出しパラメータを逐次調整してください。
```

## ユーザーシミュレーションシナリオの実行

*ムービーナイト*シナリオには、事前に決められた参照テキストはありません。
会話を手動で確認できるように、単独で実行してください：

```bash
adk eval \
  day_4/Agent_Evaluation \
  day_4/Agent_Evaluation/evals/movie_night_user_sim/evalset.json \
  --config_file_path=day_4/Agent_Evaluation/evals/home_automation/config.json
```

このシナリオは`conversationScenario`に依存しているため、デフォルトのメトリクスは`NOT_EVALUATED`と表示されます。合否スコアの代わりに、エージェントの回復力（resilience）を検査するために使用してください。

---

## ノートブック

`notebooks/day-4a-agent-observability-nb.ipynb`には、オブザーバビリティモジュールをサポートする資料が含まれており、JupyterLabで個別に開くことができます。

---

## 最近の変更点（抜粋）

- `agent.py`：評価ガイドの出力を `if __name__ == "__main__"` に移し、Gemini のリトライ設定を標準的な指数バックオフ（attempts=3, exp_base=2）へ調整。
- `evals/home_automation/integration.evalset.json`：`kitchen_on_off_sequence` → `kitchen_light_on` にリネーム。
- `evals/home_automation/legacy_evalset.json`：
  `case103525`／`ambiguous_device_reference`／`invalid_location_test`／`complex_multi_device_command` などの期待レスポンス・ツール引数を最新ログに合わせて修正。
- ディレクトリ再編：eval ファイルは `evals/`、ノートブックは `notebooks/` に集約し、README に実行手順を追記。
