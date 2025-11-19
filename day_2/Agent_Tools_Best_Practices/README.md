# 🛠️ Agent Tools Best Practices

このパッケージには、Model Context Protocol (MCP) の「everything」サーバーをGoogle ADKツールレイヤー経由で呼び出す`agent.py`のイメージアシスタントが含まれています。このモジュールは、ADK (`root_agent`) によってインポートすることも、迅速なデバッグのために直接実行することも可能です（その場合、`InMemoryRunner`を起動し、`run_debug`を呼び出し、インラインツール出力を永続化して表示します）。

-----

## 📂 ファイル構成

| パス | 説明 |
| :--- | :--- |
| `agent.py` | メインのエントリーポイント。MCPツールセットをGoogle ADKエージェントに組み込みます。 |
| `agents/` | `google.adk`が利用できない場合に使用される軽量なフォールバックエージェント。 |
| `tools/` | イメージアシスタントの構築・デバッグユーティリティ (`image_agent.py`)。 |
| `tool_types.py` | ツール応答のための共有`TypedDict`エイリアス。 |
| `config.py` | Geminiモデル/リトライ設定を一元管理するヘルパー。 |

-----

## ▶️ ローカルでの実行

```bash
cd day_2/Agent_Tools_Best_Practices
python agent.py
```

Google ADKが実際のエージェントを使用できる場合、スクリプトは以下の処理を行います。

1. MCP対応エージェントで\*\*`InMemoryRunner`\*\*を起動します。
2. \*\*`run_debug("Provide a sample tiny image")`\*\*を実行します。
3. インラインのMCPペイロードを`debug_outputs/event_<n>_<m>.png`に保存し、IPythonが利用可能な場合は**インラインで表示**を試みます。

IPythonがない場合は、保存されたファイルを**手動で**開くことができます。

インポートされた場合（例: `adk serve`によるインポート）、\*\*`root_agent`\*\*のみが公開され、デバッグ実行はトリガーされません。
