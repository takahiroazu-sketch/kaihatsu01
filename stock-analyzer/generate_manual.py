"""
操作マニュアル生成

一括生成(generate.py)・dashboard(generate_dashboard.py)・report(generate_pdf.py)・
compare.py の使い方と出力内容をまとめたPDFマニュアルを生成する。承認済みPDFデザインスタイルを踏襲する。

使い方:
    python3 generate_manual.py

【重要】ツールに新しい機能を追加したときは、このスクリプトの該当ページも
必ず更新し、再実行して docs/manual.pdf を作り直すこと。
"""

import io
import os
from datetime import datetime

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from PIL import Image

from dashboard import pdf_report
from dashboard.pdf_report import new_page, gs_content
from dashboard.charts import BG, TEXT, TEXT2, TEAL, AMBER

POS = "#2D8A50"
PURPLE = "#8870CC"
ALTBG = "#F5F2EE"
HDRBG = "#D4D0CC"

VERSION_DATE = datetime.now().strftime("%Y年%m月%d日")
FOOTER_LABEL = f"銘柄分析ツール 操作マニュアル  {VERSION_DATE}"

OUT_PATH = os.path.join(os.path.dirname(__file__), "docs", "manual.pdf")


def code_box(fig, x, y, w, h, lines, fontsize=11):
    """コマンド例などを表示する等幅フォントの背景ボックス。"""
    ax = fig.add_axes([x, y, w, h])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.add_patch(Rectangle((0, 0), 1, 1, facecolor="#2A2A28", edgecolor="none", transform=ax.transAxes))
    n = len(lines)
    for i, line in enumerate(lines):
        ly = 1 - (i + 0.5) / n
        ax.text(0.035, ly, line, fontsize=fontsize, color="#7EE8D8",
                family="monospace", va="center", transform=ax.transAxes)


def bullet_block(fig, x, y, items, fontsize=10.5, line_gap=0.032, color=TEXT2, marker="・"):
    for i, item in enumerate(items):
        fig.text(x, y - i * line_gap, f"{marker} {item}", fontsize=fontsize, color=color, va="center")


# ══════════════════════════════════════════════════════════════
# 1. 表紙
# ══════════════════════════════════════════════════════════════
def page_cover():
    pdf_report._PAGE_NUM[0] += 1
    fig = plt.figure(figsize=(11.69, 8.27))
    fig.patch.set_facecolor(BG)

    left = fig.add_axes([0, 0.12, 0.38, 0.78])
    left.set_xlim(0, 1)
    left.set_ylim(0, 1)
    left.axis("off")
    left.add_patch(Rectangle((0, 0), 1, 1, facecolor=TEAL, edgecolor="none", transform=left.transAxes))

    fig.text(0.44, 0.80, "銘柄分析ツール", fontsize=28, fontweight="bold", color=TEXT, va="center")
    fig.text(0.44, 0.70, "操作マニュアル", fontsize=28, fontweight="bold", color=TEXT, va="center")
    fig.text(0.44, 0.60, f"バージョン: v1  ／  更新日: {VERSION_DATE}", fontsize=12, color=TEXT2, va="center")

    tools = [
        ("一括生成（おすすめ）", "generate.py", "HTML+PDF", POS),
        ("ダッシュボード", "generate_dashboard.py", "HTML", TEAL),
        ("レポート", "generate_pdf.py", "PDF", AMBER),
        ("複数銘柄比較", "compare.py", "HTML", PURPLE),
    ]
    for i, (name, cmd, fmt, clr) in enumerate(tools):
        ky = 0.48 - i * 0.085
        fig.text(0.44, ky, name, fontsize=14, fontweight="bold", color=clr, va="center")
        fig.text(0.68, ky, cmd, fontsize=11, color=TEXT, family="monospace", va="center")
        fig.text(0.90, ky, fmt, fontsize=10.5, color=TEXT2, va="center")

    div = fig.add_axes([0.44, 0.155, 0.52, 0.002])
    div.set_facecolor("#C8C4BE")
    div.axis("off")

    fig.text(0.44, 0.12,
              "本ツールはユーザーが指定した銘柄コードの分析結果を提示するものであり、\n"
              "ツール側から独自の銘柄推奨は行いません。投資判断はご自身の責任で行ってください。",
              fontsize=8.5, color=TEXT2, va="center")

    foot = fig.add_axes([0, 0, 1, 0.075])
    foot.set_xlim(0, 1)
    foot.set_ylim(0, 1)
    foot.axis("off")
    foot.add_patch(Rectangle((0, 0), 1, 1, facecolor="#1C1C1C", edgecolor="none", transform=foot.transAxes))
    foot.text(0.5, 0.45, FOOTER_LABEL, ha="center", color="#909090", fontsize=8, va="center")
    foot.text(0.96, 0.45, str(pdf_report._PAGE_NUM[0]), color="#D0D0D0", fontsize=11,
              fontweight="bold", ha="right", va="center")

    return fig


# ══════════════════════════════════════════════════════════════
# 2. 共通事項
# ══════════════════════════════════════════════════════════════
def page_common():
    fig = new_page(FOOTER_LABEL, label="共通事項",
                    title="この4つのツールに共通すること",
                    insight="証券コード1つを渡すだけで、株価・財務データの取得から分析までを自動実行する")
    gs = gs_content(fig, 1, 2, wspace=0.35, top=0.78)

    ax1 = fig.add_subplot(gs[0, 0])
    ax1.set_facecolor(BG)
    ax1.axis("off")
    ax1.set_title("対象・前提", fontsize=11.5, fontweight="bold", color=TEXT, pad=10, loc="left")
    bullet_block(fig, 0.075, 0.685, [
        "対象は日本株の証券コード（4桁、例: 7203）",
        "内部で自動的に「.T」を付与してyfinanceから取得",
        "データソースはyfinance（無料・登録不要）",
        "プロジェクトのルートフォルダ（stock-analyzer/）で",
        "  python3 コマンドを実行する",
        "財務データは直近4期分（yfinanceの取得上限）",
    ], fontsize=10.5)

    ax2 = fig.add_subplot(gs[0, 1])
    ax2.set_facecolor(BG)
    ax2.axis("off")
    ax2.set_title("3つの分析の内容", fontsize=11.5, fontweight="bold", color=TEXT, pad=10, loc="left")
    bullet_block(fig, 0.535, 0.685, [
        "① ファンダメンタルズ: 売上・利益・ROE/ROA・",
        "   CF・EPS/BPS・配当性向",
        "② バリュエーション: PER/PBR/PSR/EV-EBITDA/",
        "   配当利回り・簡易理論株価（配当割引モデル）",
        "③ テクニカル: 移動平均・RSI・MACD・",
        "   ゴールデン/デッドクロス・52週高安値",
    ], fontsize=10.5)

    fig.text(0.04, 0.30, "共通の注意事項", fontsize=11.5, fontweight="bold", color=TEXT)
    bullet_block(fig, 0.04, 0.255, [
        "本ツールは分析結果の提示のみを行い、独自の銘柄推奨は行わない",
        "理論株価・各種指標は参考値であり、投資判断はご自身の責任で行うこと",
        "存在しない証券コードを指定した場合はエラーメッセージが表示される",
        "  （generate.pyは他の正しいコードの処理を続行、compare.pyは処理を中断する）",
        "銀行株など業種によっては「営業利益」等の項目が算出できず「―」と表示される場合がある",
    ], fontsize=10.5)

    return fig


# ══════════════════════════════════════════════════════════════
# 3. 一括生成（おすすめ）
# ══════════════════════════════════════════════════════════════
def page_generate_all():
    fig = new_page(FOOTER_LABEL, label="ツール1 / 4 ー 一括生成（おすすめ）",
                    title="generate.py", insight="ダッシュボード(HTML)とレポート(PDF)を一度に自動生成する")
    gs = gs_content(fig, 1, 1, top=0.78, bottom=0.30)

    code_box(fig, 0.04, 0.66, 0.92, 0.14, [
        "$ cd stock-analyzer",
        "$ python3 generate.py 7203",
        "$ python3 generate.py 7203 6758 8306",
    ])

    fig.text(0.04, 0.585, "出力先", fontsize=11, fontweight="bold", color=TEXT)
    fig.text(0.04, 0.555,
             "output/<証券コード>_dashboard.html  と  output/<証券コード>_report.pdf  を銘柄ごとに生成",
             fontsize=10, color=TEXT2)

    fig.text(0.04, 0.50, "動作の内容", fontsize=11, fontweight="bold", color=TEXT)
    bullet_block(fig, 0.04, 0.46, [
        "証券コードを1つ以上（スペース区切りで何個でも）指定できる",
        "銘柄ごとにデータ取得・3分析（ファンダメンタルズ／バリュエーション／テクニカル）を1回だけ行い、",
        "  その結果からダッシュボードとレポートの両方を作る（取得・分析の二度手間がない）",
        "存在しない証券コードが含まれていた場合は、そのコードだけをエラーとして報告し、",
        "  残りの正しい証券コードの処理は最後まで続行する",
    ], fontsize=10.5, line_gap=0.038)

    fig.text(0.04, 0.235, "使い分け", fontsize=11, fontweight="bold", color=TEXT)
    bullet_block(fig, 0.04, 0.20, [
        "両方の形式が欲しい場合や、複数銘柄をまとめて処理したい場合はこのツールを使う",
        "片方の形式だけでよい場合は generate_dashboard.py／generate_pdf.py を個別に使ってもよい",
    ], fontsize=10.5)

    return fig


# ══════════════════════════════════════════════════════════════
# 4. ダッシュボード（単体）
# ══════════════════════════════════════════════════════════════
def page_dashboard():
    fig = new_page(FOOTER_LABEL, label="ツール2 / 4 ー ダッシュボード（単体）",
                    title="generate_dashboard.py", insight="ブラウザで見る単一HTMLダッシュボード")
    gs = gs_content(fig, 1, 1, top=0.78, bottom=0.30)

    code_box(fig, 0.04, 0.66, 0.92, 0.09, [
        "$ cd stock-analyzer",
        "$ python3 generate_dashboard.py 7203",
    ])

    fig.text(0.04, 0.615, "出力先", fontsize=11, fontweight="bold", color=TEXT)
    fig.text(0.04, 0.585, "output/<証券コード>_dashboard.html  （ブラウザで開いて閲覧する単一ファイル）",
             fontsize=10, color=TEXT2)

    fig.text(0.04, 0.53, "画面の内容", fontsize=11, fontweight="bold", color=TEXT)
    bullet_block(fig, 0.04, 0.49, [
        "ヘッダー: 会社名・セクター・終値・PER/PBR/配当利回り/ROEのKPIカード・増収増益フラグ",
        "1. ファンダメンタルズ分析: 売上高・純利益の推移チャート ＋ 期別財務指標テーブル",
        "2. バリュエーション分析: 評価指標テーブル ＋ 簡易理論株価（DDM）と前提の注記",
        "3. テクニカル分析: 株価と移動平均線チャート、RSIチャート、指標サマリー表",
        "フッター: 免責事項と生成日時",
    ], fontsize=10.5, line_gap=0.038)

    fig.text(0.04, 0.235, "特徴", fontsize=11, fontweight="bold", color=TEXT)
    bullet_block(fig, 0.04, 0.20, [
        "ブラウザのダークモード／ライトモードに自動で追従する",
        "3ツールの中で最も手軽に見た目を確認できる（ダブルクリックでブラウザが開く）",
    ], fontsize=10.5)

    return fig


# ══════════════════════════════════════════════════════════════
# 4. レポート(PDF)
# ══════════════════════════════════════════════════════════════
def page_report():
    fig = new_page(FOOTER_LABEL, label="ツール3 / 4 ー レポート（単体）",
                    title="generate_pdf.py", insight="印刷・保存・共有向けのA4横4ページPDF")
    gs = gs_content(fig, 1, 1, top=0.78, bottom=0.30)

    code_box(fig, 0.04, 0.66, 0.92, 0.09, [
        "$ cd stock-analyzer",
        "$ python3 generate_pdf.py 7203",
    ])

    fig.text(0.04, 0.615, "出力先", fontsize=11, fontweight="bold", color=TEXT)
    fig.text(0.04, 0.585, "output/<証券コード>_report.pdf  （A4横向き・4ページ）",
             fontsize=10, color=TEXT2)

    fig.text(0.04, 0.53, "各ページの内容", fontsize=11, fontweight="bold", color=TEXT)
    bullet_block(fig, 0.04, 0.49, [
        "p.1 表紙: 会社名・セクター、終値・PER/PBR/配当利回り/ROEのKPI、免責事項",
        "p.2 ファンダメンタルズ分析: 売上・純利益推移チャート ＋ 期別財務指標テーブル",
        "p.3 バリュエーション分析: 評価指標テーブル ＋ 簡易理論株価（DDM）ボックス",
        "p.4 テクニカル分析: 株価と移動平均線チャート、RSIチャート、指標サマリー表",
    ], fontsize=10.5, line_gap=0.038)

    fig.text(0.04, 0.29, "ダッシュボードとの違い", fontsize=11, fontweight="bold", color=TEXT)
    bullet_block(fig, 0.04, 0.255, [
        "同じ分析内容を、印刷・保存・メール共有しやすいPDF形式で出力する",
        "承認済みのPDFデザインスタイル（オフホワイト背景・黒フッター・ティールアクセント）を踏襲",
    ], fontsize=10.5)

    return fig


# ══════════════════════════════════════════════════════════════
# 5. 複数銘柄比較
# ══════════════════════════════════════════════════════════════
def page_compare():
    fig = new_page(FOOTER_LABEL, label="ツール4 / 4 ー 複数銘柄比較",
                    title="compare.py", insight="複数の証券コードを横並びで比較するHTMLダッシュボード")
    gs = gs_content(fig, 1, 1, top=0.78, bottom=0.30)

    code_box(fig, 0.04, 0.66, 0.92, 0.09, [
        "$ cd stock-analyzer",
        "$ python3 compare.py 7203 6758 8306",
    ])

    fig.text(0.04, 0.615, "出力先", fontsize=11, fontweight="bold", color=TEXT)
    fig.text(0.04, 0.585, "output/compare_<コード1>_<コード2>_....html", fontsize=10, color=TEXT2)

    fig.text(0.04, 0.53, "画面の内容", fontsize=11, fontweight="bold", color=TEXT)
    bullet_block(fig, 0.04, 0.49, [
        "指標一覧テーブル: 株価・PER・PBR・配当利回り・ROE・直近クロスを銘柄ごとに一覧表示",
        "比較チャート4枚: PER／PBR／ROE／配当利回りを、値の大きい順の横棒グラフで比較",
        "赤字銘柄（ROEがマイナス等）はゼロ基準線付きで正しく表示され、赤字は赤字色で強調される",
        "無配当銘柄など値が存在しない項目は「―」表示になる",
    ], fontsize=10.5, line_gap=0.038)

    fig.text(0.04, 0.27, "使い方のコツ", fontsize=11, fontweight="bold", color=TEXT)
    bullet_block(fig, 0.04, 0.235, [
        "証券コードはスペース区切りで何個でも指定できる（2〜6銘柄程度が見やすい）",
        "同業種内での比較に使うと、割安・割高やROEの差が一目でわかりやすい",
    ], fontsize=10.5)

    return fig


# ══════════════════════════════════════════════════════════════
# 6. 補足・今後の拡張予定
# ══════════════════════════════════════════════════════════════
def page_appendix():
    fig = new_page(FOOTER_LABEL, label="補足",
                    title="制約事項と今後の拡張予定",
                    insight="v1時点（2026年7月）での制約と、企画書に記載の拡張候補")
    gs = gs_content(fig, 1, 2, wspace=0.35, top=0.78)

    ax1 = fig.add_subplot(gs[0, 0])
    ax1.set_facecolor(BG)
    ax1.axis("off")
    ax1.set_title("現時点の制約", fontsize=11.5, fontweight="bold", color=TEXT, pad=10, loc="left")
    bullet_block(fig, 0.075, 0.685, [
        "同業他社比較は未実装（業界データソース未整備のため）",
        "無配当・高成長株は簡易DDMの理論株価が",
        "  構造的に低く出やすい（手法上の限界）",
        "データソースはyfinanceのみ（v1）",
        "対象は日本株のみ（米国株は未対応）",
    ], fontsize=10.5)

    ax2 = fig.add_subplot(gs[0, 1])
    ax2.set_facecolor(BG)
    ax2.axis("off")
    ax2.set_title("今後の拡張候補", fontsize=11.5, fontweight="bold", color=TEXT, pad=10, loc="left")
    bullet_block(fig, 0.535, 0.685, [
        "ウォッチリスト・定期実行",
        "米国株対応",
        "アラート通知（決算・株価急変等）",
        "J-Quants APIへの移行（データ精度向上）",
    ], fontsize=10.5)

    fig.text(0.04, 0.30, "本マニュアルの更新ルール", fontsize=11.5, fontweight="bold", color=TEXT)
    bullet_block(fig, 0.04, 0.255, [
        "stock-analyzer に新しい機能・ツールを追加した際は、必ず generate_manual.py に",
        "  該当ページを追記・修正したうえで再実行し、docs/manual.pdf を最新化すること",
        "本ページの「今後の拡張候補」は、実装済みになったものから随時この表から削除する",
    ], fontsize=10.5, line_gap=0.038)

    return fig


def build():
    pdf_report._reset_page_num()
    pages = [page_cover(), page_common(), page_generate_all(), page_dashboard(), page_report(),
             page_compare(), page_appendix()]

    a4w, a4h = int(297 * 150 / 25.4), int(210 * 150 / 25.4)
    imgs = []
    for fig in pages:
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
        buf.seek(0)
        imgs.append(Image.open(buf).convert("RGB").resize((a4w, a4h), Image.LANCZOS))
        plt.close(fig)

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    imgs[0].save(OUT_PATH, save_all=True, append_images=imgs[1:], resolution=150)
    return OUT_PATH


if __name__ == "__main__":
    path = build()
    print(f"[saved] {path}")
