# Agent2Agent Communication

このディレクトリは、複数の専門エージェントを A2A（Agent-to-Agent）経由で接続し、カスタマーサポート担当がオーケストレーションするデモです。構成を見直し、各責務をモジュール分割して管理しやすくしました。

## ディレクトリ構成

```text
Agent2Agent_Communication/
├── agent.py
├── config.py
├── agents/
│   ├── __init__.py
│   ├── catalog.py
│   ├── inventory.py
│   └── shipping.py
├── servers/
│   ├── __init__.py
│   ├── catalog_server.py
│   ├── inventory_server.py
│   └── shipping_server.py
├── README.md
├── __init__.py
├── requirements.txt
└── notebooks/
```

## 各ファイルの詳細

- `agent.py`
  ルートとなるカスタマーサポートエージェントを定義し、3 つの専門エージェント（商品カタログ・在庫・配送）の uvicorn サーバーを起動します。
  `RemoteA2aAgent` を介して各エージェントと接続し、サンプル問い合わせを非同期に実行する `main()` も含まれます。
  `adk web day_5` から利用する場合にもこのファイルの `root_agent` が参照されます。

- `config.py`
  共通設定を一括管理します。Gemini モデル名、HTTP リトライポリシー、各エージェントのポート番号、表示用ラベル、uvicorn が読み込むモジュールパス、`RemoteA2aAgent` で使う名称などをまとめています。ファイル間でのハードコーディングを避けるための基盤です。

- `agents/__init__.py`
  個別エージェントのファクトリ関数（`create_product_catalog_agent` など）を公開します。これにより他モジュールからシンプルにインポートできます。

- `agents/catalog.py`
  商品カタログ担当の LLM エージェントを定義します。`get_product_info` ツールで価格や仕様を返し、
  `create_product_catalog_agent()` が `LlmAgent` を生成します。

- `agents/inventory.py`
  倉庫在庫を扱うエージェントです。`get_inventory_status` ツールで在庫数と次回入荷予定を回答し、`create_inventory_agent()` が A2A 向けエージェントを返します。

- `agents/shipping.py`
  配送見積もりとトラッキングを担当するエージェントです。
  `get_shipping_info` ツールで都市別の配送日数や注文 ID の追跡情報を提供し、`create_shipping_agent()` でエージェントを組み立てます。

- `servers/catalog_server.py` / `servers/inventory_server.py` / `servers/shipping_server.py`
  それぞれ `to_a2a()` を用いて ASGI アプリを生成し、uvicorn から呼び出せる `app` を公開します。
  `agent.py` はこれらのモジュールを指定してサーバーを自動起動し、`.well-known/agent-card.json` を通じてメタデータを取得します。

- `servers/__init__.py`
  上記サーバーモジュールをまとめて公開します。静的インポートでテストする際に利用できます。

- `requirements.txt`
  ノートブックやスクリプトで必要となる依存パッケージを定義します。

- `notebooks/`
  セッション中に使用する補助ノートブック群を格納しています（今回のリファクタリングでは変更していません）。

## 実行方法

1. `GOOGLE_API_KEY` を環境変数に設定します。
2. 専門エージェントのサーバー起動と動作確認をまとめて行う場合は、リポジトリのルートから次を実行してください。

```bash
python day_5/Agent2Agent_Communication/agent.py
```

スクリプトが 3 つの uvicorn プロセスを起動し、シナリオごとの応答を表示した後、自動でサーバーを終了します。

3. Web UI から試す場合は `adk web day_5` を実行すると、このフォルダの `root_agent` が読み込まれ、バックグラウンドで起動した各 A2A エージェント経由で問い合わせを処理します。
