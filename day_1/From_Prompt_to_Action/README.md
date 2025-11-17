# 🎯 このコードの主な目的

このコードの最大の目的は、「**`google-adk`という特定のライブラリ（エージェント開発キット）がインストールされていなくても、コード全体がクラッシュせずに動作する**」ことです。

これは「**グレースフル・フォールバック（Graceful Fallback）**」と呼ばれる設計パターンの一例です。

* **本番環境（`google-adk`あり）:** `google-adk`の強力な`Agent`クラスを使い、AIモデル（Gemini）と`get_weather`などの「ツール」を連携させる、本格的なAIエージェントとして機能します。
* **開発・テスト環境（`google-adk`なし）:** `google-adk`が`ImportError`を起こしても、ダミーの`FallbackAgent`クラスが代わりに使用されます。これにより、`google-adk`がインストールされていない開発者のPCや、軽量なテスト環境でも、モジュールのインポートやツールの単体テストが問題なく実行できます。

この設計により、**コードのポータビリティ（可搬性）とテスト容易性**が劇的に向上しています。

---

## ⚙️ 主要コンポーネントの詳細解説

コードを論理的なブロックに分けて解説します。

### 1. エージェントの動的読み込み（最重要部分）

このコードの心臓部です。

* `tool_types.py` の `ToolResponse` / `Tool`:
    `ToolSuccessResponse` と `ToolErrorResponse` という TypedDict でツールの戻り値を定義し、`status` が `"success"` か `"error"` のどちらかであることを静的に保証しています。`Tool` は「任意の引数を受け取り `ToolResponse` を返す関数」です。`get_weather` や `get_current_time` がこの型に該当します。

* `class BaseAgent(Protocol):`:
    `Protocol`（プロトコル）を使い、「エージェント」が持つべき**インターフェース（設計図）**を定義しています。`__init__`メソッドが特定の引数（`name`, `model`, `tools`など）を持つこと、`tools`というリストのプロパティを持つことを「要求」します。

* `class FallbackAgent:`:
    `google-adk`がない場合に備えた、**ダミー（フォールバック）**のエージェントクラスです。`BaseAgent`プロトコルで定義された`__init__`シグネチャ（引数の仕様）を実装しており、`agents/fallback.py` に切り出されています。中身はAIとして動作するロジックを持たず、設定値をプロパティとして保持するだけです。

* `def _load_agent_class() -> Type[BaseAgent]:`:
**動的インポート**を行う関数です。
    1. `importlib.import_module("google.adk.agents")` で `google-adk` のインポートを**試みます**。
    2. **成功すれば**（＝ `google-adk`がインストールされている）、本物の `Agent` クラスを返します。
    3. **失敗すれば**（＝ `ImportError`など）、ダミーの `FallbackAgent` クラスを返します。

* `Agent: Type[BaseAgent] = _load_agent_class()`:
    上記の関数を実行し、その結果（本物の`Agent`かダミーの`FallbackAgent`）を `Agent` という名前の変数に格納します。
    このコード以降、`Agent(...)` と書くだけで、実行環境に応じて適切なクラスが自動的に使われることになります。

### 2. ツール（Tools）の定義

エージェントが利用できる具体的な機能（関数）です。

* `_WEATHER_REPORTS`, `_CITY_TIMEZONES`:
    ツールのための**モックデータ（模擬データ）**です。本来は外部の天気APIや時刻APIを呼び出すところですが、サンプルコードとして簡潔にするため、辞書に固定値を定義しています。`tools/weather.py` と `tools/time.py` にそれぞれ分割されています。

* `def get_weather(city: str) -> ToolResponse` (`tools/weather.py`):
    `Tool`型に準拠した関数です。引数 `city` を小文字（`.lower()`）に変換し、OpenWeatherMap API（利用可能な場合）またはローカルモックデータを参照します。戻り値は `ToolSuccessResponse` か `ToolErrorResponse` のどちらかで、`status` や `report` / `error_message` フィールドが保証されます。

* `def get_current_time(city: str) -> ToolResponse` (`tools/time.py`):
    こちらも`Tool`型に準拠した関数です。`zoneinfo.ZoneInfo` を使ってPythonの標準機能で**実際の現在時刻**を取得し、`ToolResponse` の形式で戻します。`try...except`ブロックで、`ZoneInfo`が見つからない場合やその他の例外を適切に処理し、`get_weather`と同様の形式でエラーを返します。

### 3. エージェントのインスタンス化

最後に、これらをすべて組み合わせてエージェントを作成します。

* `root_agent: BaseAgent = Agent(...)`:
    `Agent` クラス（本物またはダミー）を使って、`root_agent` という名前のインスタンスを生成します。
* `name`, `model`, `description`, `instruction` は、エージェントの基本設定です。LLM（この場合は `gemini-2.0-flash`）に、「あなたは誰で、どう振る舞うべきか」を指示します。
* `tools=[get_weather, get_current_time]`：
        ここで、先ほど定義した2つの関数をエージェントに「道具」として渡しています。

---

## 🌟 優れた設計プラクティス

このコードが「世界トップクラス」と評される理由は、以下の設計プラクティスを採用している点にあります。

1. **疎結合（Loose Coupling）:**
    `get_weather` などのツール関数は、`google-adk` や `Agent` クラスについて一切関知しません。それらは独立した純粋なPython関数であり、単体でテスト可能です。
2. **依存関係の分離（Dependency Isolation）:**
    `google-adk` という「重い」または「オプションの」依存関係のインポート処理を `_load_agent_class` という一点に集約し、失敗してもアプリケーション全体が停止しないようにしています。
3. **インターフェース（契約）によるプログラミング:**
    `Protocol` (`BaseAgent`) を使うことで、本物の`Agent`と`FallbackAgent`が同じ「契約」を満たしていることを型システムレベルで保証しています。これにより、`Agent` 変数の中身がどちらであっても、コードの他の部分（この例では `root_agent` の初期化）は同じように扱えます。

---

## 🤖 実行時の動作まとめ

* **`google-adk` がインストールされている場合:**
    `Agent` は `google.adk.agents.Agent` になります。`root_agent` は、`gemini-2.0-flash` モデルと通信し、ユーザーの質問（例：「東京の天気は？」）を解釈し、必要に応じて `get_weather("tokyo")` を自動的に呼び出してその結果を返す、**高機能なAIエージェント**として動作します。

* **`google-adk` がインストールされていない場合:**
    `Agent` は `FallbackAgent` クラスになります。`root_agent` は、`description` や `tools` などの設定情報を保持するだけの**軽量なオブジェクト**になります。AIとしての機能は持ちませんが、コードがエラーで停止しないため、他の開発やテスト（例：`get_weather`関数の単体テスト）の妨げになりません。

このコードは、堅牢でモジュール性が高く、テストしやすいAIアプリケーションを構築するための見本となるものです。

---

### 🏛️ Protocol vs. ABC (抽象基底クラス)

この2つは、どちらもPythonにおける「インターフェース（設計図）」の役割を果たしますが、そのアプローチと哲学が根本的に異なります。

これは、**「名目的な型付け」**（Nominal Subtyping）と\*\*「構造的な型付け」\*\*（Structural Subtyping）の違いとして理解するのが最も明確です。

#### 1\. ABC (Abstract Base Classes) - "名目的な" インターフェース

`abc` モジュールを使う `ABC` は、伝統的で厳格なインターフェース定義です。

* **哲学:** 「私のファミリー（基底クラス）の一員であると**明示的に宣言**し、必要なメソッドを実装しなければならない」

* **使い方:**

    1. `abc.ABC` を継承した「抽象基底クラス」を定義します。
    2. 実装を強制したいメソッドに `@abc.abstractmethod` デコレータを付けます。
    3. 利用するクラスは、その `ABC` を**明示的に継承**します。

* **コード例:**

    ```python
    import abc

    class Vehicle(abc.ABC):
        """乗り物の「名目的な」インターフェース"""
        
        @abc.abstractmethod
        def start_engine(self):
            """エンジンをかけることを強制する"""
            pass

    # 明示的に継承する
    class Car(Vehicle):
        def start_engine(self):
            print("エンジンがかかりました (Car)")

    # エラーになる例:
    # class Bicycle(Vehicle):
    #     pass  # start_engineを実装しないと、インスタンス化の瞬間にエラー

    # c = Car()
    # b = Bicycle() # TypeError: Can't instantiate abstract class ...
    ```

* **特徴:**

  * **実行時チェック:** `ABC` を継承したクラスが抽象メソッドを実装していない場合、インスタンス化しようとすると**実行時に `TypeError` が発生します**。
  * **強い束縛:** `Car` は `Vehicle` である、という強い継承関係（IS-A関係）をコード上で明示します。
  * **`isinstance()` との相性:** `isinstance(Car(), Vehicle)` は `True` となります。

#### 2\. Protocol - "構造的な" インターフェース

`typing` モジュールの `Protocol` は、より柔軟な「ダックタイピング」を静的型チェックの世界に持ち込んだものです。

* **哲学:** 「アヒルのように歩き、アヒルのように鳴くなら、それはアヒル（として扱ってよい）。**継承しているかは問わない**」

* **使い方:**

    1. `typing.Protocol` を継承した「プロトコル」を定義します。
    2. 必要なメソッドや属性のシグネチャ（型定義）を記述します。
    3. 利用するクラスは、**`Protocol` を継承する必要は全くありません**。

* **コード例:**

    ```python
    from typing import Protocol

    class Startable(Protocol):
        """エンジンをかけられるものの「構造的な」インターフェース"""
        
        def start_engine(self) -> None:
            ... # 実装は書かない

    # Protocolを継承しない
    class Car:
        def start_engine(self) -> None:
            print("エンジンがかかりました (Car)")

    class Lawnmower: # 芝刈り機
        def start_engine(self) -> None:
            print("ブオオン！ (Lawnmower)")

    class Bicycle:
        def pedal(self) -> None:
            print("ペダルを漕ぐ")

    # 型チェッカー(Mypy)がどう判断するか
    def run_vehicle(v: Startable):
        v.start_engine()

    run_vehicle(Car())       # OK: start_engine() がある
    run_vehicle(Lawnmower()) # OK: start_engine() がある
    # run_vehicle(Bicycle())   # 型エラー: Bicycleに start_engine がない
    ```

* **特徴:**

  * **静的型チェック:** `Protocol` のチェックは、主に **Mypy などの型チェッカー**によって実行されます。（実行時ではなく）
  * **疎結合:** `Car` や `Lawnmower` は `Startable` プロトコルの存在を一切知る必要がありません。
  * **既存コードへの適用:** サードパーティのライブラリなど、**自分が変更できないコード**に対してもインターフェースを定義し、型チェックの恩恵を受けられます。

#### ⚖️ まとめ: 使い分け

| 比較項目 | ABC (Abstract Base Classes) | Protocol |
| :--- | :--- | :--- |
| **主な目的** | 実装の共通化と**実行時**の強制 | 型の一貫性チェック（**静的**） |
| **継承** | **必須**（名目的な型付け） | **不要**（構造的な型付け） |
| **チェック** | `isinstance()` / 実行時エラー | Mypy / 静的型チェッカー |
| **適した場面** | フレームワーク開発\<br>（「我々の枠組みに従え」） | 既存コードへの型付け\<br>（「同じ形ならOK」） |

前回の `BaseAgent` の例で `Protocol` が使われたのは、`google-adk` の本物の `Agent` と、ダミーの `FallbackAgent` という、**互いに継承関係のないクラス**を「エージェント」という**共通の型（構造）**で扱いたかったためであり、`Protocol` の理想的な使用例です。

---

### 📦 `importlib` のその他の使い方

`importlib` は、Pythonの `import` システム自体をPythonコードから操作するための強力なライブラリです。

#### 1\. モジュールの再読み込み: `importlib.reload()`

すでにインポート済みのモジュールを、強制的に再読み込み（再実行）します。

* **ユースケース:**

  * 開発中にWebサーバーなどの長時間動くプロセスを**再起動せず**に、設定ファイルや一部のモジュールの変更を反映させたい時。
  * Jupyter Notebookなどで、別ファイルにしたヘルパー関数を修正した後に、セルを再実行するだけで変更を反映させたい時。

* **コード例:**

    ```python
    # config.py (初回: DEBUG = True)

    # main.py
    import config
    import importlib

    print(config.DEBUG) # True と表示される

    # ...ここで config.py を開いて DEBUG = False に手動で修正...

    print(config.DEBUG) # True と表示される (importはキャッシュされるため)

    # 強制的に再読み込み
    importlib.reload(config)

    print(config.DEBUG) # False と表示される！
    ```

**注意:** `reload` は、既存のオブジェクトとの不整合を引き起こす可能性があり、デバッグが難しくなるため、本番コードでの使用は推奨されず、主に開発・デバッグ用途で使われます。

#### 2\. ファイルパスからの動的インポート: `importlib.util`

文字列のモジュール名ではなく、「特定のファイルパスにある `.py` ファイル」をモジュールとして読み込みます。

* **ユースケース:**

  * **プラグインシステムの構築**。`plugins/` ディレクトリ配下にある全ての `.py` ファイルを検出し、それぞれをプラグインとして動的に読み込む、といった処理に最適です。

* **コード例:**

    ```python
    import importlib.util
    import sys

    plugin_path = "/path/to/my_plugin.py"
    plugin_name = "my_plugin"

    # 1. スペック（仕様）の取得
    spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)

    if spec and spec.loader:
        # 2. スペックからモジュールを作成
        plugin_module = importlib.util.module_from_spec(spec)
        
        # 3. モジュールを sys.modules に登録 (重要)
        sys.modules[plugin_name] = plugin_module
        
        # 4. モジュールを実行（インポート処理の実行）
        spec.loader.exec_module(plugin_module)
        
        # これで plugin_module が使えるようになる
        plugin_module.run_my_plugin_function()
    ```

#### 3\. パッケージメタ情報の取得: `importlib.metadata` (Python 3.8+)

インストールされているPythonパッケージの\*\*メタ情報（バージョン、依存関係、エントリーポイントなど）\*\*にアクセスします。

* **ユースケース:**

* インストールされているライブラリの**バージョン番号**を取得する。
* アプリケーションが依存しているライブラリの一覧を動的にチェックする。

* **コード例:**

    ```python
    from importlib import metadata

    # NumPy のバージョンを取得する
    try:
        numpy_version = metadata.version("numpy")
        print(f"NumPy version: {numpy_version}")
    except metadata.PackageNotFoundError:
        print("NumPy is not installed.")

    # あるパッケージが依存しているライブラリ一覧
    # requires = metadata.requires("requests")
    # print(requires)
    ```

`importlib` は、Pythonの柔軟性と動的性を支える非常に強力なツールです。

---
