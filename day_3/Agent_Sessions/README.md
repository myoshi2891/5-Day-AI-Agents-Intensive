# 🤖 Agent Sessions (エージェントセッション)

このパッケージは、**ステートフル**なADKエージェントのデモンストレーションであり、インメモリのチャットとデータベースに裏付けられたセッションを対比させています。

デフォルトのエクスポートでは、Geminiを搭載したチャットボットを**SQLiteデータベース**に接続し、**ADK CLIの再起動後も会話が持続する**ようにしています。
オプションのデモでは、軽量なテストのためにインメモリサービスをどのように切り替えることができるかを紹介しています。

-----

## 📂 ディレクトリ構成

* `agent.py` - ステートフルなエージェントとデモワークフローを再エクスポートする公開エントリーポイント。
* `config.py` - 共有のGeminiモデル構成とリトライポリシー。
* `apps/stateful.py` - メインのGeminiエージェント、ランナー、およびエクスポートされたヘルパー関数`run_session`を構築します。
* `workflows/compaction.py` - ADKのイベント**コンパクション**APIとヘルパーユーティリティを紹介するオプションのワークフロー。
* `storage/`
  * `database.py` - SQLiteをバックエンドとするセッションサービスを構築するためのユーティリティと、デバッガ`inspect_db_events()`。
* `demos/`
  * `inmemory.py` - `InMemorySessionService`（永続性なし）でエージェントを実行するためのオプションのスクリプト。
* `my_agent_data.db` - 永続セッションサービスによってオンデマンドで作成されるSQLiteファイル。
* `requirements.txt` - Notebook/CLIの依存関係。
* `__init__.py` - `agent.py`とストレージヘルパーを反映した公開APIエクスポート。

-----

## 🚀 使用方法

このフォルダに対してADK Webを起動します（共有場所が必要な場合はDB URIを渡します）：

```bash
adk web --session_service_uri sqlite:///day_3/Agent_Sessions/my_agent_data.db ./day_3
```

### 🧪 Session-Toolsデモを試す

`agent.py` にはユーザー名/国をスコープ付きセッションステートに保存するデモが含まれています。

#### クロスセッション共有の確認手順

1. コンソール上で最初のチャットを `"state-demo-session"`（または任意のID）で実行し、ユーザー名と国を伝えてツールに保存させます。
2. 次に別のセッションID（例：`"new-isolated-session"`）でチャットを開始し、名前を再入力せずに質問します。
3. 各セッションを `await session_service.get_session(...)` で取得するか、UIログを確認すると `user:name` と `user:country` が保持されていることが分かります。
`USER_NAME_SCOPE_LEVELS` が `user` スコープにフォールバックするため、セッションIDが異なっても同じユーザーのスコープデータが共有され、クロスセッションで情報を参照できることを示します。

* ノートブック/CLIから直接実行する場合：

  ```bash
  python -m day_3.Agent_Sessions.agent --demo session-tools
  ```

  最後に以下が自動で表示され、`new-isolated-session` のステートも `session_service` 経由で確認できます。

  ```python
  session = await session_service.get_session(
      app_name=APP_NAME,
      user_id=USER_ID,
      session_id="new-isolated-session",
  )
  print(session.state)
  ```

* ADK Web 上でこのデモを優先する場合は、環境変数でエクスポートを上書きしてください：

  ```bash
  AGENT_SESSIONS_DEMO=session-tools \
    adk web --session_service_uri sqlite:///day_3/Agent_Sessions/my_agent_data.db ./day_3
  ```

  これにより `adk web` で立ち上がるエージェント／ランナーがセッションツールデモ向けのインメモリ構成になります。

#### 複数ユーザー／ポートでの起動

* `apps/stateful.py` の `USER_ID` は `AGENT_SESSIONS_USER_ID` 環境変数で上書きできます。ユーザースコープを分離したい場合は、ADKをユーザーごとに別の値で起動します。
* 同じマシンで複数の ADK Web を動かすとポートが競合しやすいので、`--port` で明示的に割り当ててください。

例：

```bash
# ターミナル1（user_alice, ポート8081）
AGENT_SESSIONS_DEMO=session-tools \
AGENT_SESSIONS_USER_ID=user_alice \
  adk web --port 8081 --session_service_uri sqlite:///day_3/Agent_Sessions/my_agent_data.db ./day_3

# ターミナル2（user_bob, ポート8082）
AGENT_SESSIONS_DEMO=session-tools \
AGENT_SESSIONS_USER_ID=user_bob \
  adk web --port 8082 --session_service_uri sqlite:///day_3/Agent_Sessions/my_agent_data.db ./day_3
```

これで各ブラウザは異なるユーザースコープとポートを使用し、`user:` ステートが混在しません。

永続性なしで迅速なローカルテストを行うには：

```bash
python -m day_3.Agent_Sessions.demos.inmemory
```

保存されたイベントを直接確認するには：

```python
from day_3.Agent_Sessions.storage import inspect_db_events
inspect_db_events()
```
