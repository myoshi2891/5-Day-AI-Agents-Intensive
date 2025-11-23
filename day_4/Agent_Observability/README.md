# Agent Observability（エージェントの可観測性）

このリファクタリングされたプロジェクトは、モジュール化されたレイアウトで Google ADK エージェントを監視する方法を示しています。各レイヤー（ロギング、ツール、エージェント、プラグイン、ランナー、エントリーポイント）は分離されているため、スタックの残りの部分を書き直すことなく、コンポーネントを再利用または交換できます。

-----

## 📂 ディレクトリ構成

```text
Agent_Observability/
├── agent.py                     # エントリーポイント + root_agentの遅延エクスポート
├── agent_observability/
│   ├── __init__.py              # 利便性のためのエクスポート
│   ├── agents.py                # エージェントファクトリのヘルパー
│   ├── config.py                # 定数とリトライ設定
│   ├── logging_utils.py         # ログのクリーンアップ + 設定
│   ├── plugins.py               # カスタムのロギング + カウンタープラグイン
│   ├── runner.py                # ランナー + 実行ヘルパー
│   └── tools.py                 # ドメイン固有のツール
└── requirements.txt
```

-----

## 🛠️ 実行フロー

1. **ロギングのセットアップ (`logging_utils.configure_logging`)**

      * 古い `logger.log`、`web.log`、`tunnel.log` の削除を試み、ファイルが削除できない場合は分かりやすい警告を表示します（クリーンアップ中のクラッシュを防ぎます）。
      * 構造化ロギング（ファイル名/行/レベル/メッセージ）を設定し、デバッグログを `logger.log` にルーティングします。

2. **設定 (`config.py`)**

      * Gemini モデル名、リトライポリシー、デフォルトの自然言語クエリなどの共有定数を一元管理します。
      * `RETRY_CONFIG` を公開し、API ポリシーが変更されたときに検索エージェントとリサーチエージェントの両方が同期を保てるようにします。

3. **ドメインツール (`tools.count_papers`)**

      * 実際の文字列のシーケンスのみを受け入れます（文字列のみでは拒否される）。これにより、カウントが文字数ではなく論文の数と一致することを保証します。
      * ビジネスロジック（返された論文のカウント）をオーケストレーションから分離します。

4. **エージェントファクトリ (`agents.py`)**

      * `create_google_search_agent` は、Google Search を生の検索スニペットを返す ADK エージェントに接続します。
      * `create_research_agent` は、`AgentTool` 経由でその検索エージェントを受け取り、候補となる論文を検索するためにそれを呼び出し、
      `count_papers` を呼び出し、最終的な応答で各論文を箇条書きでリストアップし、その後に **`Total papers found: X`** を含めることを強制します。

5. **プラグイン (`plugins.CountInvocationPlugin`, `ConversationTracePlugin`)**

      * `CountInvocationPlugin` は、非同期ロックを使用してエージェント/モデルの呼び出し回数を追跡し、並行するコールバックでも正確さを保ちます。
      * `ConversationTracePlugin` は `runner.run_debug()` の出力（セッションバナー + `User > …` + エージェントの応答）をミラーリングするため、
      ADK Web のログが CLI と一致し、デフォルトのデバッグセッションでの重複を自動的に抑制します。

6. **ランナー (`runner.build_runner` および `run_observability_demo`)**

      * エージェントとプラグインを `InMemoryRunner` に組み立て、すべての実行に `ConversationTracePlugin`、標準の `LoggingPlugin`、
      および `CountInvocationPlugin` が含まれるようにします。
      * `run_observability_demo` は短いステータスバナーを出力し、`runner.run_debug` を実行し、トランスクリプトと ADK インストゥルメンテーションを並行してストリームします。

7. **エントリーポイント (`agent.py`)**

      * `configure_logging` を呼び出し、クエリを解決し（CLI 引数または `AGENT_QUERY` 環境変数を優先し、
      `DEFAULT_QUERY` にフォールバックします）、`run_observability_demo` を待ちます。
      * `get_root_agent()` と `__getattr__` を介して遅延 `root_agent` を公開し、ADK Web（`adk web day_4`）がインポート時間を低く保ちながらモジュールをロードできるようにします。

-----

## ▶️ デモの実行

リポジトリのルートから実行します。

```bash
python day_4/Agent_Observability/agent.py
```

オプションとして、デフォルトのリサーチテーマを上書きできます。

```bash
AGENT_QUERY="Find papers on constitutional AI" python day_4/Agent_Observability/agent.py
```

このコマンドは、構造化されたトレースを `logger.log` に記録しながら、トランスクリプト形式の行と `[logging_plugin]` の診断情報の両方をターミナルに出力します。

-----

## 🌐 ADK Web での使用

```bash
adk web day_4
```

UI で **`Agent_Observability`** を選択し、「Find recent papers on quantum computing.（量子コンピューティングに関する最近の論文を探して。）」のようなプロンプトを発行します。
遅延 `root_agent` のエクスポートにより、ADK Web はエージェントパッケージを安全にロードし、同じロギング設定を再利用し、トランスクリプトと詳細なプラグイン出力をサーバーログに表示できます。

-----
