# Git 基本ワークフロー

このドキュメントは、今後の開発で毎回使う基本的な Git の流れをまとめたものです。

## 1. 毎回使う基本コマンド

### 変更状況を確認する
```bash
cd /Users/takahiroazuma/Desktop/kabu/claude
git status
```

### 変更を保存する
```bash
git add .
git commit -m "変更内容"
```

### GitHub に送る
```bash
git push
```

### もし GitHub 側の内容を取り込む場合
```bash
git pull
```

---

## 2. VS Code での操作方法

### ターミナルを開く
- VS Code の上部メニューで「Terminal」→「New Terminal」を選ぶ

### そのターミナルでコマンドを実行する
- 例:
```bash
cd /Users/takahiroazuma/Desktop/kabu/claude
git status
```

### 変更内容を確認する
- VS Code のソース管理（Source Control）ペインを見る
- 変更されたファイルが一覧表示される

### コミットする
- 変更ファイルをステージング
- 「Commit」ボタンを押す
- メッセージを入力する

### push する
- 画面上部またはコマンドパレットから Git の操作を実行する
- もしくはターミナルで `git push` を実行する

---

## 3. どんなときに push すればよいか

### push すべきケース
- 変更がまとまったとき
- 1日の作業が終わったとき
- バックアップを取りたいとき
- GitHub 上で共有したいとき
- 他の人と作業内容を同期したいとき

### push しなくてよいケース
- まだ作業途中で内容が固まっていないとき
- まだ試行錯誤中のとき
- いったんローカルで保存したいだけのとき

---

## 4. おすすめの基本サイクル

1. 変更をする
2. `git status` で確認する
3. `git add .`
4. `git commit -m "..."`
5. `git push`

---

## 5. ひとことでいうと

- ローカルで普段使いする
- 変更がまとまったら commit
- 必要なときだけ push
- GitHub は共有・バックアップ用
