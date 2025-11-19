# 🛠️ Agent Tools Best Practices

このパッケージには、Google ADK の長時間実行ワークフロー（`adk_request_confirmation` を使った承認フロー）を体験できる Shipping Agent が含まれています。`agent.py` は `workflows/shipping.py` の実装を呼び出し、ADK (`root_agent`) からも直接利用できます。

-----

## 📂 ファイル構成

| パス | 説明 |
| :--- | :--- |
| `agent.py` | メインのエントリーポイント。Shipping Agent ワークフローを呼び出します。 |
| `agents/` | `google.adk`が利用できない場合に使用される軽量なフォールバックエージェント。 |
| `workflows/` | `image.py`（MCPイメージ生成デモ）と `shipping.py`（承認付きワークフローデモ）を収録。 |
| `tools/` | 既存コードとの互換レイヤー。内部的には `workflows/` を再エクスポートしています。 |
| `tool_types.py` | ツール応答のための共有`TypedDict`エイリアス。 |
| `config.py` | Geminiモデル/リトライ設定を一元管理するヘルパー。 |

-----

## ▶️ ローカルでの実行

```bash
cd day_2/Agent_Tools_Best_Practices
python agent.py
```

起動すると `run_shipping_workflow_sync()` が呼び出され、コンテナ数に応じて承認が必要になるデモが自動で実行されます。`auto_approve` などの挙動は `workflows/shipping.py` 内で調整できます。

インポートされた場合（例: `adk serve`によるインポート）、`root_agent` として Shipping Agent が公開されるだけで、デモワークフローは起動しません（アプリ側で任意の制御を実装できます）。

-----

## 🧭 ワークフローの全体像

`run_shipping_workflow("Ship 10 containers to Rotterdam", auto_approve=True)` を実行すると、以下のタイムラインで処理が進みます。ポイントは **TIME 6** でツールが `pending` を返し、**TIME 8** でワークフローが確認イベントを検出、**TIME 10** で同じ `invocation_id` を使って再開する点です。

| 時刻 | イベント概要 |
| :--- | :--- |
| TIME 1 | ユーザーが「Ship 10 containers to Rotterdam」を送信 |
| TIME 2 | ワークフローが `shipping_runner.run_async(...)` を呼び出し、ADK が一意の `invocation_id="abc123"` を割り当て |
| TIME 3 | エージェントがユーザー入力を受け取り、`place_shipping_order` ツールを選択 |
| TIME 4 | ADK がツール `place_shipping_order(10, "Rotterdam", tool_context)` を実行 |
| TIME 5 | ツールが 10 > 5 を検知し `tool_context.request_confirmation(...)` を呼び出す |
| TIME 6 | ツールが `{"status": "pending", ...}` を返却 |
| TIME 7 | ADK が `adk_request_confirmation` イベントを生成し、`invocation_id="abc123"` と紐付け |
| TIME 8 | ワークフローが `check_for_approval()` でイベントを検出し、`approval_id` と `invocation_id` を保存 |
| TIME 9 | 人による意思決定（この例では APPROVE ✅）を取得 |
| TIME 10 | `shipping_runner.run_async(..., invocation_id="abc123")` を再度呼び出し、人間の決定（FunctionResponse）を渡す |
| TIME 11 | ADK が同じ `invocation_id` を検知し、停止した実行を RESUME |
| TIME 12 | ADK が再度 `place_shipping_order` を呼び出すが、今度は `tool_context.tool_confirmation.confirmed=True` |
| TIME 13 | ツールが `{"status": "approved", "order_id": "ORD-10-HUMAN", ...}` を返却 |
| TIME 14 | エージェントがユーザーへ最終レスポンスを返信 |

この流れにより、ADK は単一の `invocation_id` をキーにワークフローを停止・再開できます。
