# iPhone から日報を作成する

GitHub Actions の `Create Daily Report` workflow を起動すると、iPhone から Git を触らずに日報を作成できます。

## いちばん簡単な使い方

1. iPhone の GitHub アプリ、または Safari でこのリポジトリを開く
2. `Actions` を開く
3. `Create Daily Report` を選ぶ
4. `Run workflow` から以下を入力する
   - `report_date`: 空欄なら日本時間の今日。指定する場合は `YYYY-MM-DD`
   - `topics`: 学習内容。複数行にすると複数の箇条書き
   - `today_hours`: 今日の学習時間。例: `1.5`
   - `memo`: 学習メモ。空欄なら `特になし`
5. 実行すると `YYYY/MM/DD.md` が作成され、`YYYYMMDDの日報作成` でコミットされます

## ショートカットアプリから起動する場合

ショートカットから GitHub API の `workflow_dispatch` を呼ぶと、入力ダイアログだけで日報を送れます。

事前に GitHub の Fine-grained personal access token を作成してください。対象リポジトリはこのリポジトリだけに限定し、権限は `Actions: Read and write` を付与します。期限は短めに設定し、トークンはショートカット内だけに保存してください。

ショートカットの流れ:

1. `入力を要求`: 学習内容
2. `入力を要求`: 学習時間
3. `URL の内容を取得`
   - URL: `https://api.github.com/repos/so-engineer/daily_report/actions/workflows/create-daily-report.yml/dispatches`
   - メソッド: `POST`
   - ヘッダー:
     - `Accept`: `application/vnd.github+json`
     - `Authorization`: `Bearer YOUR_GITHUB_TOKEN`
     - `X-GitHub-Api-Version`: `2022-11-28`
   - JSON:

```json
{
  "ref": "main",
  "inputs": {
    "report_date": "",
    "topics": "ショートカットの学習内容入力",
    "today_hours": "1.5",
    "memo": ""
  }
}
```

`topics` と `today_hours` には、ショートカットで受け取った入力値を差し込んでください。`memo` は空欄なら `特になし` になります。
