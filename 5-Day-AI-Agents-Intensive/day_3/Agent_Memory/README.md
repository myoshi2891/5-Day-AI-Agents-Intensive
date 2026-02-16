# Agent Memory デモ手順

このパッケージは `adk web` から直接読み込めるようにリファクタリングされ、`day_3/Agent_Memory/agent.py` が以下をすべて公開します。

1. `root_agent` — `preload_memory` / `load_memory` / `save_memory` ツールを組み込んだ `LlmAgent`
2. `runner` / `session_service` / `memory_service` — ノートブックや CLI からそのまま利用可能
3. `run_session`, `run_color_memory_demo`, `run_birthday_memory_demo` — ストリーミング出力付きのヘルパー
4. `seed_demo_memory` — ADK Web でメモリ検索を即座に再現できる決定論的なセッショントランスクリプト投入関数

## 📁 ディレクトリ構成

```text
day_3/Agent_Memory/
├── agent.py                # ADK の公開エントリーポイント（薄いラッパー）
├── demos.py                # run_session / seed / search などの共通ユーティリティ
└── core/
    ├── memory_consolidation.py  # MemoryConsolidator（LLMベースの圧縮処理）
    ├── plugins.py               # AutoMemorySaverPlugin
    └── setup.py                 # APP_NAME/runner/app などのビルダー
```

## Memory Consolidation Pipeline

このエージェントは、セッションをメモリへ保存する前に **Memory Consolidator**（LLM駆動）を必ず通過させ、会話のノイズを事実ベースのメモリへ圧縮します。

1. **Raw Session Events** – ユーザー／エージェント双方の発話ログ。
2. **LLM 分析** – Gemini により会話全体を解析。
3. **Key Facts Extraction** – 「ユーザーの好み」「誕生日」「アレルギー」などの耐久的な情報だけを抽出。
4. **Structured Memory** – `fact`, `details`, `category` を持つ JSON へ整形。
5. **Deduplication & Storage** – 既存メモリを検索し、重複する事実はスキップ。新規事実のみを保存。

### Before → After

```text
User: "My favorite color is BlueGreen. I also like purple. Actually, I prefer BlueGreen most of the time."
Agent: "Great! I'll remember that."
User: "Thanks!"
Agent: "You're welcome!"
```

**After Consolidation:** `User's favorite color: BlueGreen`

会話 4 発話 → 1 件の事実メモリに凝縮され、検索・応答速度・精度が向上します。

## 1. 事前準備（任意）

環境変数でアプリ名やユーザー ID を上書きできます。

```bash
export AGENT_MEMORY_APP_NAME=MemoryDemoApp
export AGENT_MEMORY_USER_ID=demo_user
```

## 2. メモリを手動で投入（オプション）

ADK Web だとノートブックの `await run_session(...)` が実行されないため、すぐに再現したい場合は以下を 1 回だけ実行してメモリサービスに色と誕生日の会話をシードできます。

```bash
python - <<'PY'
import asyncio
from day_3.Agent_Memory.agent import seed_demo_memory
asyncio.run(seed_demo_memory())
PY
```

`seed_demo_memory()` は内部で `Session` にユーザー/モデルの発話を埋め込み、
`InMemoryMemoryService.add_session_to_memory()` に登録します。

## 3. ADK Web で確認（`save_memory` ツールの使い方）

```bash
adk web ./day_3
```

ブラウザで以下を実行します。

1. セッション ID 例 `birthday-session-01` を選び、「My birthday is on March 15th.」と伝える。
2. 続けて「Please save this to memory for future sessions.」など、記憶させたい旨を伝える。→ エージェントが `save_memory` ツールを呼び、
会話を長期メモリへ保存します（UI のツール実行ログでも確認可能）。
3. 新しいセッション ID 例 `birthday-session-02` を作成し、「When is my birthday?」と質問。
4. コンソールに `📀 Agent is loading past memory...` が出て、モデルが「Your birthday is on March 15th」と回答。

セッション ID が異なっても、`save_memory` → `load_memory` の組み合わせで会話を共有できることが分かります。`save_memory` を使わなかった場合は長期メモリに保存されない点に注意してください。

## 4. CLI でのデモ実行

ブラウザを使わずに確認したい場合は以下を実行してください。

```bash
python -m day_3.Agent_Memory.agent --demo birthday
# または
python -m day_3.Agent_Memory.agent --demo color
# または
python -m day_3.Agent_Memory.agent --demo auto
```

いずれも `run_session()` がメモリ保存込みで呼び出されるため、会話 → メモリ保存 → 新規セッションからの検索という一連の流れを確認できます。

CLI の色デモ（`--demo color`）では最後に `search_color_preferences()` を呼び出し、`memory_service.search_memory()` の結果を以下の形式で表示します。

```text
🔍 Search Results:
  Found 1 relevant memories

  [model]: Thanks, I will remember your favorite color is blue-green....
```

CLI の `--demo auto` では `AutoMemorySaverPlugin` が有効な `Runner` を使い、以下の 2 セッションを連続実行します。
1 つ目の会話終了後にプラグインが自動でメモリへ保存し、2 つ目の会話では `preload_memory` が即座に記憶を参照するため、手動の `save_memory` 呼び出しは不要です。
ADK Web でも同じプラグインが働き、以下の確認ができます。

1. **初回セッション:** 「甥へのプレゼント」を共有すると、自動保存 ✅
2. **別セッション:** 「甥に何を贈った？」と尋ねると、`preload_memory` が記憶を取得し正しく回答 ✅

## 5. トラブルシュート

- `Session | None` 由来の型エラー: `session_service.get_session()` が `None` を返した場合に `RuntimeError` を投げ、
`add_session_to_memory` には必ず `Session` を渡すようガードしています。
- `app_name` / `user_id` が無いというエラー: `seed_demo_memory()` が生成する `Session` へ `app_name` と `user_id` を明示的に指定することで解消しています。
- 「覚えていてくれない」: `AutoMemorySaverPlugin` が各ターン終了後にセッションを自動保存し、保存前に Memory Consolidator が事実抽出と重複排除を行います。
それでも確実に残したいときは「Please remember this」などで `save_memory` ツールを呼び出してください。
