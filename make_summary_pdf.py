# -*- coding: utf-8 -*-
"""프로젝트 요약 + Evaluation Guidance 대응표 PDF 생성 스크립트."""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

# --- 한글 폰트 등록 (Noto Sans CJK KR) ---
FONT_R = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
FONT_B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
try:
    pdfmetrics.registerFont(TTFont("KR", FONT_R, subfontIndex=2))   # KR subfont
    pdfmetrics.registerFont(TTFont("KR-B", FONT_B, subfontIndex=2))
    BASE, BOLD = "KR", "KR-B"
except Exception:
    pdfmetrics.registerFont(UnicodeCIDFont("HYSMyeongJo-Medium"))
    BASE = BOLD = "HYSMyeongJo-Medium"

NAVY = colors.HexColor("#1f2a5e")
GOLD = colors.HexColor("#e8a838")
LIGHT = colors.HexColor("#e8ecf7")
GREY = colors.HexColor("#555555")

styles = getSampleStyleSheet()
def st(name, **kw):
    base = dict(fontName=BASE, fontSize=9.5, leading=14, textColor=colors.black, alignment=TA_LEFT)
    base.update(kw)
    return ParagraphStyle(name, **base)

H1 = st("H1", fontName=BOLD, fontSize=20, leading=24, textColor=NAVY, spaceAfter=4)
SUB = st("SUB", fontSize=10, leading=14, textColor=GREY, spaceAfter=8)
H2 = st("H2", fontName=BOLD, fontSize=13, leading=17, textColor=NAVY, spaceBefore=10, spaceAfter=4)
BODY = st("BODY", fontSize=9.5, leading=14)
CELL = st("CELL", fontSize=8.3, leading=11)
CELLB = st("CELLB", fontName=BOLD, fontSize=8.3, leading=11, textColor=NAVY)
CELLW = st("CELLW", fontName=BOLD, fontSize=9, leading=12, textColor=colors.white)

# 일부 글리프(가운뎃점/화살표 등)가 KR subfont에 없어 깨지므로 ASCII로 치환
def clean(s):
    return (s.replace("·", " / ").replace("→", " -> ")
             .replace("↔", " <-> ").replace("×", " x ").replace("↑", " 증가")
             .replace("−", " - ").replace("∞", "무한"))

# Paragraph 생성을 가로채 자동 치환
_Para = Paragraph
def Paragraph(text, style):  # noqa: F811
    return _Para(clean(text), style)

doc = SimpleDocTemplate(
    "Project_Summary.pdf", pagesize=A4,
    leftMargin=16 * mm, rightMargin=16 * mm, topMargin=15 * mm, bottomMargin=14 * mm,
)
E = []

# ---- 제목 ----
E.append(Paragraph("Dungeon Crawler RPG — 프로젝트 요약", H1))
E.append(Paragraph("GIST AI2000 자료구조및알고리즘 · 팀 프로젝트 / Evaluation Guidance(200점) 대응 요약", SUB))
E.append(HRFlowable(width="100%", thickness=1.5, color=GOLD, spaceAfter=8))

# ---- 1. 개요 ----
E.append(Paragraph("1. 게임 개요", H2))
E.append(Paragraph(
    "Python + pygame로 구현한 절차적 던전 크롤러 RPG. 플레이어는 절차 생성된 던전을 탐험하며 "
    "적과 턴 기반 전투를 하고, 아이템을 모으고, 층을 내려가 5층 보스를 처치한다. 게임 종료 시 점수가 "
    "리더보드에 기록된다. 게임 루프·렌더링·입력은 <b>main.py</b>가, 상태는 매 턴 하나의 "
    "<b>Frame</b>(player·map·enemies·items 묶음) 스택으로 관리한다.", BODY))

# ---- 2. 6대 핵심 기능 대응표 ----
E.append(Paragraph("2. 6대 핵심 기능 ↔ 자료구조/알고리즘 (Guidance 요구 형식)", H2))
E.append(Paragraph(
    "Guidance는 기능마다 <b>① 사용한 DS/알고리즘 ② 선택 이유 ③ 대안 비교 ④ 복잡도 ⑤ 코드 위치</b>를 "
    "답하도록 요구한다 (6 features × 15점 + 인터뷰 25%).", BODY))
E.append(Spacer(1, 4))

header = [Paragraph(t, CELLW) for t in ["기능", "DS / 알고리즘", "선택 이유 · 대안 비교", "복잡도", "코드 위치"]]
rows = [
    ("1. Dungeon Map",
     "2D 그리드 + 절차 생성 (방 배치 + L자 복도)",
     "그리드는 좌표→타일 O(1) 접근. 방 겹침은 AABB로 검사. 그래프(인접리스트) 대비 격자 이동·렌더에 단순·직관적.",
     "접근 O(1)\n생성 O(W·H)",
     "map.py\nMap, Room\n_generate / _connect_rooms"),
    ("2. Undo System",
     "Stack (LIFO) — 프레임 히스토리",
     "되돌리기는 LIFO이므로 Stack이 정확히 맞음. Queue(FIFO)면 순서가 거꾸로 됨. 전체 상태 deepcopy 저장(델타 아님) — 단순하지만 메모리↑.",
     "push/pop O(1)\n최대 30프레임",
     "frame.py\nFrame (list 기반)\nmain.py:63 deepcopy"),
    ("3. Turn Management",
     "순차 턴 루프 (입력→플레이어→적→픽업)",
     "현재 모든 캐릭터 동일 속도라 단순 순회로 충분. 속도가 다르면 Priority Queue(Heap)로 행동 순서 정렬이 더 적합.",
     "턴당 O(적 수)",
     "main.py:52\nturn_update()"),
    ("4. Item Inventory",
     "List (고정 10칸) + 아이템 클래스 계층",
     "슬롯 수가 작고 1~0키로 인덱스 접근하므로 List가 단순·충분. 이름 검색이 잦으면 Dict, 정렬·범위검색이 필요하면 Tree가 유리.",
     "추가/접근 O(1)\n검색 O(n)",
     "player.py inventory\nuse_item()\nitem.py Item/Weapon/Potion"),
    ("5. Enemy AI",
     "BFS 추적 + Bresenham 시야 + 도주",
     "격자가 무가중치라 BFS가 최단경로를 보장하며 구현이 단순. A*는 휴리스틱으로 더 빠르나 가중치/큰 맵에서 이점 — 현 규모엔 과함.",
     "BFS O(V+E)\n시야 O(거리)",
     "enemy.py\n_bfs_next_step()\ncan_see (Bresenham)"),
    ("6. Leaderboard",
     "Dict 저장 + sorted() 내림차순 정렬",
     "이름→최고점 매핑은 Dict가 적합. 전체 정렬은 O(n log n). top-k만 필요하면 Heap이 O(n log k)로 유리.",
     "정렬 O(n log n)\n조회 O(1)",
     "leaderboard.py\nadd_score / get_leaderboard\nrender.py _compute_score"),
]
data = [header]
for f, ds, why, cx, loc in rows:
    data.append([
        Paragraph(f, CELLB), Paragraph(ds, CELL),
        Paragraph(why, CELL), Paragraph(cx.replace("\n", "<br/>"), CELL),
        Paragraph(loc.replace("\n", "<br/>"), CELL),
    ])

tbl = Table(data, colWidths=[24 * mm, 30 * mm, 56 * mm, 20 * mm, 28 * mm])
tbl.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), NAVY),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#c2cbe6")),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
]))
E.append(tbl)

# ---- 3. 점수 공식 ----
E.append(Paragraph("3. 인게임 점수 공식", H2))
E.append(Paragraph(
    "점수 = 킬XP×10 + 골드(아이템)×500 + Undo 잔여×90 + max(0, 3000 − 경과초)×10 "
    "(render.py 의 _compute_score 함수)", BODY))

# ---- 4. 제출/평가 체크리스트 ----
E.append(Paragraph("4. 제출 · 평가 대비 체크리스트 (Guidance 기준)", H2))
checks = [
    ("PPT & 알고리즘 설명 제출 (30%)", "전체 구조 + 6기능 + DS/알고리즘 + 선택이유 + 대안비교 + 코드위치 포함"),
    ("6대 핵심 기능 구현 (15%)", "위 2번 표의 6기능 모두 코드에 실재 — 대부분 구현 완료"),
    ("알고리즘 비교·설명 (10%)", "각 기능마다 대안 1개 이상과 복잡도 비교 (표 참고)"),
    ("인터뷰 (25%)", "5단계 답변(DS→이유→코드위치→대안→복잡도) 팀원별 연습"),
    ("라이브 데모 (20%)", "AI+X Studio PC에서 시작→플레이→게임오버까지 무crash 실행"),
]
cdata = [[Paragraph("항목 (배점)", CELLW), Paragraph("준비 내용", CELLW)]]
for a, b in checks:
    cdata.append([Paragraph(a, CELLB), Paragraph(b, CELL)])
ctbl = Table(cdata, colWidths=[55 * mm, 103 * mm])
ctbl.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), NAVY),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#c2cbe6")),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ("LEFTPADDING", (0, 0), (-1, -1), 5),
]))
E.append(ctbl)

# ---- 5. 남은 작업 ----
E.append(Paragraph("5. 데모 전 남은 작업", H2))
for t in [
    "게임오버 / 클리어 화면 — player.die()가 빈 함수, 보스 처치 후 종료 처리 필요",
    "리더보드 게임오버 화면 연결 — 저장/로드(leaderboard.py)는 있으나 게임오버에서 호출 경로 미연결",
    "코드 정리 — enemy_boss.py(중복) 제거, [DEBUG] 키(K_b/K_t/floor=5 시작) 제거",
    "PPT가 실제 코드와 일치하는지 최종 점검",
]:
    E.append(Paragraph("• " + t, BODY))

E.append(Spacer(1, 8))
E.append(HRFlowable(width="100%", thickness=1, color=GOLD, spaceAfter=4))
E.append(Paragraph(
    "<i>핵심 메시지: Run it · Defend it · Compare it — \"돌아간다\"가 아니라 \"왜 이 자료구조를 골랐는가\"를 말할 수 있어야 한다.</i>",
    st("foot", fontSize=8.5, textColor=GREY)))

doc.build(E)
print("OK: Project_Summary.pdf")
