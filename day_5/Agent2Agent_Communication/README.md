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
  ルートとなるカスタマーサポートエージェントを定義します。`root_agent` はモジュール読み込み時に `_initialize_root_agent()` を介して構築され、デフォルトではインポート時（`__name__ != "__main__"` の場合）に不足している A2A サーバーを自動起動します。
  スクリプトとして直接実行する場合や `A2A_AUTO_START_SERVERS=0` を設定した場合は自動起動を抑止し、`get_root_agent(auto_start=True)` や `initialize_agents()` を呼んだときだけサーバーを立てます。`cleanup_root_agent()` で自動起動したサーバーを安全に停止できます。
  `initialize_agents()` / `main()` を呼び出すと明示的に 3 つの uvicorn サーバーを開始し、終了時にクリーンアップします。
  `subprocess.PIPE` を使わず `/dev/null` へ出力を捨てることで大量ログによるデッドロックを防ぎます。

- `config.py`
  共通設定を一括管理します。Gemini モデル名、HTTP リトライポリシー、各エージェントのポート番号、表示用ラベル、uvicorn が読み込むモジュールパス、`RemoteA2aAgent` で使う名称などをまとめています。
  リトライの指数バックオフは `exp_base=2` に見直しており、最長でも数十秒で応答が返る現実的な設定です。

- `agents/__init__.py`
  個別エージェントのファクトリ関数（`create_product_catalog_agent` など）を公開します。これにより他モジュールからシンプルにインポートできます。

- `agents/catalog.py`
  商品カタログ担当の LLM エージェントを定義します。`get_product_info` ツールで価格や仕様を返し、
  `create_product_catalog_agent()` が `LlmAgent` を生成します。

- `agents/inventory.py`
  倉庫在庫を扱うエージェントです。`get_inventory_status` ツールはユーザー入力を正規化した上で表示に用いるため、前後の余白が含まれても自然な文面になります。

- `agents/shipping.py`
  配送見積もりとトラッキングを担当するエージェントです。
  `get_shipping_info` ツールで都市別の配送日数や注文 ID の追跡情報を提供し、`create_shipping_agent()` でエージェントを組み立てます。

- `servers/catalog_server.py` / `servers/inventory_server.py` / `servers/shipping_server.py`
  それぞれ `to_a2a()` を用いて ASGI アプリを生成し、uvicorn から呼び出せる `app` を公開します。
  `agent.py` から `initialize_agents()` や `get_root_agent(auto_start=True)` を呼び出すと、これらモジュールが順番に起動され `.well-known/agent-card.json` への到達性をチェックします。

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

3. Web UI から試す場合は `adk web day_5` を実行すると、このフォルダの `root_agent` が読み込まれます。
   既定ではインポート時に不足している A2A サーバーを自動起動します（`A2A_AUTO_START_SERVERS=0` を設定すると抑止可能、`1` で強制オン）。
   明示的に常駐させたい場合は、別ターミナルで `python day_5/Agent2Agent_Communication/agent.py` を実行するか、`get_root_agent(auto_start=True)` を呼んで事前にサーバーを立ててください。
   `.well-known/agent-card.json` の応答を待つ時間を短縮したいときは `A2A_WAIT_FOR_AGENT_CARD=0` を指定すると待機をスキップできます（代わりに、ポートが閉じたままでも即座に検知できない点に注意）。
