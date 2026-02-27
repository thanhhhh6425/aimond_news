"""
app/routes/chatbot.py - AAA (AimondAI Assistant) chatbot API
"""
from flask import Blueprint, request, jsonify
import os

chatbot_bp = Blueprint("chatbot", __name__)


def _get_full_context() -> str:
    """Load toan bo du lieu ca PL lan UCL de Gemini co the tra loi bat ki cau hoi nao."""
    from app.models import Match, Standing, Player, Club, News
    from app.extensions import db
    from sqlalchemy import func
    from datetime import datetime, timezone
    lines = []

    for league in ["PL", "UCL"]:
        league_name = "Premier League" if league == "PL" else "UEFA Champions League"
        lines.append(f"\n{'='*50}")
        lines.append(f"GIAI DAU: {league_name} ({league}) - MUA 2025/26")
        lines.append(f"{'='*50}")

        # Toan bo BXH
        try:
            standings = (Standing.query.filter_by(league=league, season="2025")
                        .order_by(Standing.position.asc()).all())
            if standings:
                lines.append(f"\nBANG XEP HANG {league} DAY DU:")
                for s in standings:
                    gd = (s.goals_for or 0) - (s.goals_against or 0)
                    lines.append(f"  {s.position:2}. {s.team_name:<25} {s.played:2} tran | "
                                f"{s.wins}T {s.draws}H {s.losses}B | "
                                f"{s.goals_for}-{s.goals_against} (HS:{gd:+d}) | "
                                f"{s.points} diem")
        except: pass

        # Tong ban thang ca giai
        try:
            total_goals = db.session.query(
                func.sum(Match.home_score + Match.away_score)
            ).filter_by(league=league, season="2025", status="FT").scalar() or 0
            total_matches = Match.query.filter_by(league=league, season="2025", status="FT").count()
            lines.append(f"\nTONG QUAN {league}:")
            lines.append(f"  - Tong so tran da choi: {total_matches}")
            lines.append(f"  - Tong ban thang ca giai: {total_goals}")
            if total_matches > 0:
                lines.append(f"  - Trung binh ban thang/tran: {total_goals/total_matches:.2f}")
        except: pass

        # Ket qua 10 tran gan nhat
        try:
            results = (Match.query.filter_by(league=league, season="2025", status="FT")
                      .order_by(Match.kickoff_at.desc()).limit(10).all())
            if results:
                lines.append(f"\nKET QUA {league} GAN NHAT (10 tran):")
                for m in results:
                    d = m.kickoff_at.strftime("%d/%m") if m.kickoff_at else ""
                    lines.append(f"  {d} {m.home_team_name} {m.home_score}-{m.away_score} {m.away_team_name}")
        except: pass

        # Lich 5 tran sap toi
        try:
            upcoming = (Match.query.filter_by(league=league, season="2025", status="SCHEDULED")
                       .filter(Match.kickoff_at >= datetime.now(timezone.utc))
                       .order_by(Match.kickoff_at.asc()).limit(5).all())
            if upcoming:
                lines.append(f"\nLICH {league} SAP TOI:")
                for m in upcoming:
                    ko = m.kickoff_at.strftime("%d/%m %H:%M") if m.kickoff_at else "TBD"
                    lines.append(f"  {ko} | {m.home_team_name} vs {m.away_team_name}")
        except: pass

        # Top 10 ghi ban
        try:
            from app.models import Statistic
            scorers = (Statistic.query.filter_by(league=league, season="2025")
                      .order_by(Statistic.goals.desc()).limit(10).all())
            if scorers:
                lines.append(f"\nTOP 10 GHI BAN {league}:")
                for i, s in enumerate(scorers, 1):
                    name = s.player.name if s.player else "?"
                    club = s.club.name if s.club else ""
                    pos = s.player.position if s.player else ""
                    lines.append(f"  {i:2}. {name:<22} ({club:<20}) - {s.goals} ban, {s.assists} kien tao, {s.appearances} tran")
        except: pass

        # Top 10 kien tao
        try:
            from app.models import Statistic
            assists = (Statistic.query.filter_by(league=league, season="2025")
                      .order_by(Statistic.assists.desc()).limit(10).all())
            if assists:
                lines.append(f"\nTOP 10 KIEN TAO {league}:")
                for i, s in enumerate(assists, 1):
                    name = s.player.name if s.player else "?"
                    club = s.club.name if s.club else ""
                    lines.append(f"  {i:2}. {name:<22} ({club:<20}) - {s.assists} kien tao, {s.goals} ban")
        except: pass

        # So luong cau thu theo CLB
        try:
            club_player_counts = (db.session.query(Player.club_name, func.count(Player.id))
                                 .filter(Player.league == league)
                                 .group_by(Player.club_name).all())
            if club_player_counts:
                lines.append(f"\nSO LUONG CAU THU THEO CLB ({league}):")
                for club_name, count in sorted(club_player_counts, key=lambda x: x[0] or ""):
                    lines.append(f"  - {club_name}: {count} cau thu")
                total_players = sum(c for _, c in club_player_counts)
                lines.append(f"  => Tong cong: {total_players} cau thu {league}")
        except: pass

        # Thong ke ban thang/thua tung CLB tu BXH
        try:
            standings_all = (Standing.query.filter_by(league=league, season="2025")
                            .order_by(Standing.position.asc()).all())
            if standings_all:
                lines.append(f"\nTHONG KE BAN THANG/THUA TUNG CLB {league}:")
                for s in standings_all:
                    gd = (s.goals_for or 0) - (s.goals_against or 0)
                    lines.append(f"  - {s.team_name}: ghi {s.goals_for} ban, thung luoi {s.goals_against} ban (hieu so {gd:+d})")
        except: pass

        # Tong ban thang cua tung CLB (join qua Club)
        try:
            from app.models import Statistic, Club
            from sqlalchemy import func as sqlfunc
            club_goals = (db.session.query(
                Club.name.label("club_name"),
                sqlfunc.sum(Statistic.goals).label("total_goals"),
                sqlfunc.sum(Statistic.assists).label("total_assists"),
            ).join(Club, Statistic.club_id == Club.id)
             .filter(Statistic.league == league, Statistic.season == "2025")
             .group_by(Club.name)
             .order_by(sqlfunc.sum(Statistic.goals).desc())
             .all())
            if club_goals:
                lines.append(f"\nTONG BAN THANG THEO CLB ({league}):")
                for row in club_goals:
                    lines.append(f"  - {row.club_name}: {row.total_goals} ban thang, {row.total_assists} kien tao")
        except Exception as e:
            lines.append(f"  [loi query club goals: {e}]")

        # Danh sach CLB
        try:
            clubs = Club.query.filter_by(league=league).all()
            if clubs:
                club_names = [c.name for c in clubs]
                lines.append(f"\nDANH SACH {len(clubs)} CLB {league}: {', '.join(club_names)}")
        except: pass

        # Tin tuc moi nhat
        try:
            news = (News.query.filter_by(league=league)
                   .order_by(News.published_at.desc()).limit(5).all())
            if news:
                lines.append(f"\nTIN TUC {league} MOI NHAT:")
                for n in news:
                    pub = n.published_at.strftime("%d/%m") if n.published_at else ""
                    lines.append(f"  [{pub}] {n.title}")
        except: pass

    # Ket qua playoff UCL va doi di tiep
    try:
        from app.models import Match
        playoffs = (Match.query.filter_by(league="UCL", season="2025", round="Playoff", status="FT")
                   .order_by(Match.kickoff_at.desc()).all())
        if playoffs:
            lines.append("\n=== UCL PLAYOFF - KET QUA VA DOI DI TIEP ===")
            # Tinh tong goc tung cap dau
            pairs = {}
            for m in playoffs:
                # Dung home/away cua leg 1 lam key
                key = tuple(sorted([m.home_team_name, m.away_team_name]))
                if key not in pairs:
                    pairs[key] = []
                pairs[key].append(m)

            for key, legs in pairs.items():
                if len(legs) == 2:
                    t1, t2 = key
                    g1 = sum((l.home_score or 0) for l in legs if l.home_team_name == t1) +                          sum((l.away_score or 0) for l in legs if l.away_team_name == t1)
                    g2 = sum((l.home_score or 0) for l in legs if l.home_team_name == t2) +                          sum((l.away_score or 0) for l in legs if l.away_team_name == t2)
                    winner = t1 if g1 > g2 else (t2 if g2 > g1 else "Chua xac dinh")
                    lines.append(f"  {t1} {g1}-{g2} {t2} => Di tiep: {winner}")
                elif len(legs) == 1:
                    m = legs[0]
                    lines.append(f"  {m.home_team_name} {m.home_score}-{m.away_score} {m.away_team_name} (con 1 luot)")
    except: pass

    # Tran dang LIVE (ca 2 giai)
    try:
        live = Match.query.filter_by(status="LIVE").all()
        if live:
            lines.append(f"\nTRAN DANG LIVE:")
            for m in live:
                lines.append(f"  {m.league} | {m.home_team_name} {m.home_score or 0}-{m.away_score or 0} {m.away_team_name}")
    except: pass

    return "\n".join(lines)


@chatbot_bp.route("/message", methods=["POST"])
def chat():
    d = request.get_json(silent=True) or {}
    msg = (d.get("message") or "").strip()
    league = (d.get("league") or "PL").upper()
    history = d.get("history") or []
    if not msg:
        return jsonify({"reply": "Bạn muốn hỏi gì về bóng đá?"})

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return jsonify({"reply": _keyword_fallback(msg.lower(), league), "league": league})

    try:
        reply = _gemini_reply(msg, api_key, history)
    except Exception as e:
        reply = _keyword_fallback(msg.lower(), league)

    return jsonify({"reply": reply, "league": league})


def _gemini_reply(msg: str, api_key: str, history: list = []) -> str:
    from google import genai
    client = genai.Client(api_key=api_key)

    db_context = _get_full_context()

    system_prompt = f"""Bạn là AAA - AimondAI Assistant, trợ lý bóng đá của AimondNews.
Bạn có đầy đủ dữ liệu về Premier League (PL) và UEFA Champions League (UCL) mùa 2025/26.

NGUYÊN TẮC:
1. Trả lời bằng tiếng Việt có dấu, ngắn gọn, đúng trọng tâm.
2. KHÔNG dùng emoji, KHÔNG dùng ký tự *, **, ---, ###.
3. Câu trả lời lý tưởng 1-3 câu, có số liệu cụ thể.
4. Nếu câu hỏi liên quan đến câu trước, dùng lịch sử hội thoại để trả lời đúng ngữ cảnh.
5. Nếu hỏi ngoài bóng đá: chỉ nói "Tôi chỉ hỗ trợ thông tin bóng đá."

DỮ LIỆU THỰC TẾ:
{db_context}"""

    # Build contents: system + history + current message
    contents = [{"role": "user", "parts": [{"text": system_prompt + "\n\nBắt đầu hội thoại."}]},
                {"role": "model", "parts": [{"text": "Xin chào! Tôi là AAA. Tôi có thể giúp gì cho bạn?"}]}]

    # Them lich su hoi thoai
    for h in history[-10:]:  # toi da 10 luot gan nhat
        role = "user" if h.get("role") == "user" else "model"
        contents.append({"role": role, "parts": [{"text": h.get("content", "")}]})

    # Them cau hoi hien tai
    contents.append({"role": "user", "parts": [{"text": msg}]})

    for model_name in ["models/gemini-2.5-flash", "models/gemini-2.0-flash-lite-001", "models/gemini-2.0-flash-001"]:
        try:
            response = client.models.generate_content(model=model_name, contents=contents)
            return response.text.strip()
        except Exception as e:
            if "404" in str(e):
                continue
            raise

    raise Exception("No model available")


def _normalize(text: str) -> str:
    import unicodedata
    nfd = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")


def _keyword_fallback(msg: str, league: str) -> str:
    """Fallback khi khong co API key hoac Gemini loi."""
    m = _normalize(msg)
    if any(k in m for k in ["bang xep hang", "bxh", "xep hang"]):
        return _get_standings_reply(league)
    if any(k in m for k in ["lich thi dau", "sap toi", "upcoming", "lich dau"]):
        return _get_upcoming_reply(league)
    if any(k in m for k in ["ket qua", "result", "hom qua"]):
        return _get_results_reply(league)
    if any(k in m for k in ["live", "truc tiep", "dang da"]):
        return _get_live_reply()
    if any(k in m for k in ["vua pha luoi", "ghi ban nhieu", "top scorer"]):
        return _get_top_scorers_reply(league)
    if any(k in m for k in ["kien tao", "assist"]):
        return _get_top_assists_reply(league)
    if any(k in m for k in ["tin tuc", "news"]):
        return _get_news_reply(league)
    return ("Toi la AAA - AimondAI Assistant.\n"
            "Toi co the tra loi ve:\n"
            "- Bang xep hang PL/UCL\n"
            "- Lich & ket qua thi dau\n"
            "- Vua pha luoi & kien tao\n"
            "- Tin tuc bong da moi nhat")


def _get_standings_reply(league):
    from app.models import Standing
    rows = Standing.query.filter_by(league=league, season="2025").order_by(Standing.position.asc()).limit(5).all()
    if not rows: return f"Chua co du lieu BXH {league}."
    lines = [f"Top 5 BXH {league}:"]
    for s in rows:
        lines.append(f"{s.position}. {s.team_name} - {s.points} diem")
    return "\n".join(lines)

def _get_upcoming_reply(league):
    from app.models import Match
    from datetime import datetime, timezone
    items = (Match.query.filter_by(league=league, season="2025", status="SCHEDULED")
             .filter(Match.kickoff_at >= datetime.now(timezone.utc))
             .order_by(Match.kickoff_at.asc()).limit(3).all())
    if not items: return f"Khong co tran {league} nao sap toi."
    lines = [f"Tran {league} sap toi:"]
    for m in items:
        ko = m.kickoff_at.strftime("%d/%m %H:%M") if m.kickoff_at else "TBD"
        lines.append(f"- {m.home_team_name} vs {m.away_team_name} | {ko}")
    return "\n".join(lines)

def _get_results_reply(league):
    from app.models import Match
    items = (Match.query.filter_by(league=league, season="2025", status="FT")
             .order_by(Match.kickoff_at.desc()).limit(5).all())
    if not items: return f"Chua co ket qua {league}."
    lines = [f"Ket qua {league} gan nhat:"]
    for m in items:
        lines.append(f"- {m.home_team_name} {m.home_score}-{m.away_score} {m.away_team_name}")
    return "\n".join(lines)

def _get_live_reply():
    from app.models import Match
    items = Match.query.filter_by(status="LIVE").all()
    if not items: return "Hien khong co tran nao dang dien ra."
    lines = ["Dang LIVE:"]
    for m in items:
        lines.append(f"- {m.home_team_name} {m.home_score or 0}-{m.away_score or 0} {m.away_team_name}")
    return "\n".join(lines)

def _get_news_reply(league):
    from app.models import News
    items = News.query.filter_by(league=league).order_by(News.published_at.desc()).limit(3).all()
    if not items: return f"Chua co tin tuc {league}."
    lines = [f"Tin {league} moi nhat:"]
    for n in items:
        lines.append(f"- {n.title}")
    return "\n".join(lines)

def _get_top_scorers_reply(league):
    from app.models import Statistic
    items = Statistic.query.filter_by(league=league, season="2025").order_by(Statistic.goals.desc()).limit(5).all()
    if not items: return f"Chua co du lieu ghi ban {league}."
    lines = [f"Vua pha luoi {league}:"]
    for i, s in enumerate(items, 1):
        name = s.player.name if s.player else "?"
        lines.append(f"{i}. {name} - {s.goals} ban")
    return "\n".join(lines)

def _get_top_assists_reply(league):
    from app.models import Statistic
    items = Statistic.query.filter_by(league=league, season="2025").order_by(Statistic.assists.desc()).limit(5).all()
    if not items: return f"Chua co du lieu kien tao {league}."
    lines = [f"Kien tao nhieu nhat {league}:"]
    for i, s in enumerate(items, 1):
        name = s.player.name if s.player else "?"
        lines.append(f"{i}. {name} - {s.assists} kien tao")
    return "\n".join(lines)