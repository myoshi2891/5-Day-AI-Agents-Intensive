# Day 2 – Agent Tools (エージェントツール)

このパッケージは、`google-adk` が利用可能かどうかにかかわらず、Google ADK (Agent Development Kit) ワークフローを完全に動作させ続ける方法を実証します。**本番環境（Production）パス**では、Gemini に裏打ちされた実際の `google.adk.agents.Agent` を使用します。一方、**開発（Development）パス**では、`agent.py` で公開されている**厳密なコンストラクタ契約**（contract）を遵守する、軽量な `FallbackAgent` に切り替わります。このフォールバック機構により、構造化された引数を渡すことで、`payment` や `rate` ツールを**直接呼び出し**たり、完全な**通貨変換フローを実行**（orchestrate）したりすることが引き続き可能です。

-----

## 🎯 このモジュールが保証すること

* **グレースフル・フォールバック:** `agent.py` は ADK のインポートを試みます。成功した場合、命令の実行、ツールの実行、さらには `InMemoryRunner` を介した試行も可能な、完全な `LlmAgent` を取得します。インポートが失敗した場合、`_load_agent_class()` は `FallbackAgent` を返し、これにより（ツールのユニットテストを含む）残りのコードがエラーなしでインポートできるようになります。
* **共通の契約（Contract）:** `BaseAgent` プロトコルは `.tools` 属性を持つことだけを要求し、google-adk の実エージェント／フォールバックの両方を同じ「形」として扱えるようにしています。
* **徹底した型付け:** `tool_types.py` は `ToolResponse`、`ToolSuccessResponse`、`ToolErrorResponse` を定義します。`get_fee_for_payment_method()`（支払いツール）と `get_exchange_rate()`（レートツール）は、どちらもこれらの型を返すようになりました。これにより、Pylance / MyPy は各ツールが何を生成するかを正確に理解できます。

-----

## 📁 ディレクトリ構造

```text
day_2/Agent_Tools/
├── README.md
├── requirements.txt
├── __init__.py                 # パッケージの公開 API
├── agent.py                    # `app.agent` への互換レイヤー
├── app/
│   ├── __init__.py
│   └── agent.py                # ルートエージェントを公開するエントリーポイント
├── core/
│   ├── __init__.py             # コア部品の再エクスポート
│   ├── config.py               # モデル名とリトライ設定
│   ├── compat.py               # `BaseAgent` プロトコルと ADK ローダー
│   ├── builders.py             # Enhanced agent / runner のファクトリ
│   ├── debug_utils.py          # デバッグ出力ヘルパー
│   ├── tool_types.py           # 共通の TypedDict/TypeAlias 定義
│   ├── agents/
│   │   └── fallback.py         # google-adk が利用不可の場合のドロップイン置換
│   └── tools/
│       ├── payment.py          # get_fee_for_payment_method の実装
│       └── rate.py             # get_exchange_rate の実装
└── day-2a-agent-tools.ipynb 他  # 演習ノートブック
```

-----

## 🔑 ファイルごとのハイライト

### **`app/agent.py`**

* `compat.load_agent_class()` を用いて ADK の `Agent` を動的にロードし、利用不可の場合はフォールバックへ切り替えます。
* `get_root_agent()` はデフォルトで Google ADK の `LlmAgent` を返し、本番同等の挙動を再現します。環境変数 `AGENT_TOOLS_USE_ENHANCED=0` あるいは `AGENT_TOOLS_FORCE_FALLBACK=1` をセットすると、決定論的な `FallbackAgent` に切り替えられます。
* `run_sample_conversion()` は Enhanced エージェントの `InMemoryRunner` を再利用し、コード生成のデバッグトレースを `debug_utils.show_python_code_and_result()` で表示します。

### **`core/builders.py`**

* `build_enhanced_currency_agent()` が料金・レートの2つのツールを束ねた `LlmAgent` を構築します。
* `build_enhanced_runner()` が `InMemoryRunner` を生成し、ノートブックや CLI からそのままデバッグできるようにします。

### **`core/compat.py`**

* `BaseAgent` プロトコルと `load_agent_class()` を切り離し、別モジュールからも再利用できるようにしました。
* google-adk が存在しない場合は `FallbackAgent` を返すため、`agent.py` 以外でも条件分岐なく扱えます。

### **`core/config.py`**

* コード実行が可能な Gemini モデル（デフォルトは `gemini-1.5-flash`）名と `types.HttpRetryOptions` を一元管理し、`AGENT_TOOLS_MODEL_NAME` でモデルを上書きできます。`AGENT_TOOLS_USE_ENHANCED`/`AGENT_TOOLS_FORCE_FALLBACK` でリモート ADK ルートを切り替えられるようにしています。

### **`core/debug_utils.py`**

* `show_python_code_and_result()` がコード実行パートのレスポンスを判定し、生成された Python コード／結果を整形して標準出力へ表示します。

### **`core/agents/fallback.py`**

* `agent.py` のコンストラクタシグネチャ（`name`, `model`, `instruction`, `tools`, `**kwargs`）をミラーリングし、**透過的にインスタンス化**できるようにします。
* 2つの動作を公開します。
        1. **ツールの直接呼び出し:** `run(..., tool_name="get_exchange_rate", base_currency="USD", target_currency="EUR")` を介して行います。推論されたツールに必要な kwargs のみが転送され、意図しない `TypeError` を防ぎます。
        2. **通貨変換フロー:** `amount`, `base_currency`, `target_currency`, `method` が供給されると、フォールバックは `get_fee_for_payment_method` と `get_exchange_rate` を**順次呼び出し**ます。その後、LLM が文章で記述する内容を模倣した、**統合された `ToolSuccessResponse`** を返します。
* 迅速な手動テストのためのキーワードトリガーモードも保持していますが、各ツールを呼び出す前に、必要なパラメータがすべて存在するかを**検証**するようになりました。

### **`tool_types.py`**

* `ToolSuccessResponse`/`ToolErrorResponse` は `status` を `Required[...]` としてマークし、`rate` や `fee_percentage` などのオプションのペイロードキーを許可します。`Tool` は単純に `Callable[..., ToolResponse]` です。

### **`core/tools/payment.py` (`get_fee_for_payment_method`)**

* 手数料の割合、またはメソッドが不明な場合のエラーのいずれかを記述する `ToolResponse` を返します。
* ネットワーク呼び出しなしで、内部の手数料テーブルをシミュレートするのに最適です。

### **`core/tools/rate.py` (`get_exchange_rate`)**

* モックのレートテーブル（USD→EUR/JPY/INR）を使用し、`ToolResponse` を発行します。
* ユニットテストが本番のFX APIを必要としないよう、**決定論的**（deterministic）に動作するよう設計されています。

-----

## 🧪 フォールバックの実行方法

```python
from day_2.Agent_Tools.agent import root_agent

# 1) 完全な通貨変換フローをリクエスト（LLM不使用、純粋に決定論的）
response = root_agent.run(
    "Convert 500 USD to EUR via my platinum credit card.",
    amount=500,
    base_currency="USD",
    target_currency="EUR",
    method="platinum credit card",
)
print(response["report"])

# 2) または、個別のツールを直接呼び出す
rate_only = root_agent.run(
    "Need an FX rate",
    tool_name="get_exchange_rate",
    base_currency="USD",
    target_currency="EUR",
)
```

* `tool_name` が指定された場合、そのツールに必要な引数だけが転送されます。余分な kwargs が呼び出しに紛れ込むことはありません。
* 4つの通貨関連引数が利用可能な場合、フォールバックは `agent.py` で記述された通りのワークフロー（手数料％の取得、FXレートの取得、正味金額の計算、および推論パスの報告）を実行します。
* 実際の Google ADK / Gemini エージェントはデフォルトで有効になっています。トークン節約やモデルを切り替えたい場合は、`AGENT_TOOLS_MODEL_NAME`、`AGENT_TOOLS_USE_ENHANCED`、`AGENT_TOOLS_FORCE_FALLBACK` を適宜設定してからスクリプトを実行してください。

-----

## ✅ 要点

1. **本番環境との同等性 (Production parity):** Google ADK がインストールされている場合、`agent.py` は実際の `LlmAgent` をインスタンス化し、ADK のすべての機能（`InMemoryRunner`、コード実行、Google 検索など）を提供します。
2. **開発時の安全性:** Google ADK がない場合、フォールバックは同じコンストラクタシグネチャを使用し、`.tools` 属性を公開し、マルチツールのロジックを再現します。これにより、支払い/レートの統合を引き続き検証できます。
3. **型による保証:** このディレクトリ内のすべてのツールは `ToolResponse` に準拠しているため、静的解析（Pylance, Pyright, MyPy）は環境に関係なく同じ契約（contract）を認識します。

CI、ローカルのノートブック、または教育環境のような軽量な環境でも実行する必要がある ADK ベースのエージェントを出荷（ship）する際は、いつでもこのモジュールをテンプレートとして使用してください。
