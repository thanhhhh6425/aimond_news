"""
app/routes/auth.py - API Authentication
"""
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db
from app.models import User

auth_bp = Blueprint("auth", __name__)

def _err(msg, code=400): return jsonify({"success": False, "error": msg}), code
def _ok(data=None, msg="OK"): return jsonify({"success": True, "message": msg, **(data or {})})

@auth_bp.route("/register", methods=["POST"])
def register():
    d = request.get_json(silent=True) or {}
    username = (d.get("username") or "").strip().lower()
    email = (d.get("email") or "").strip().lower()
    password = d.get("password") or ""
    if not username or not email or not password:
        return _err("username, email và password là bắt buộc")
    if len(password) < 6:
        return _err("Mật khẩu phải từ 6 ký tự trở lên")
    if User.query.filter_by(username=username).first():
        return _err("Username đã tồn tại")
    if User.query.filter_by(email=email).first():
        return _err("Email đã được đăng ký")
    user = User(username=username, email=email,
                full_name=d.get("full_name","").strip(),
                preferred_league=d.get("preferred_league","PL"))
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    login_user(user, remember=True)
    return _ok({"user": user.to_dict()}, "Đăng ký thành công"), 201

@auth_bp.route("/login", methods=["POST"])
def login():
    d = request.get_json(silent=True) or {}
    ident = (d.get("username") or d.get("email") or "").strip().lower()
    pw = d.get("password") or ""
    if not ident or not pw:
        return _err("Vui lòng nhập username/email và mật khẩu")
    user = (User.query.filter_by(username=ident).first()
            or User.query.filter_by(email=ident).first())
    if not user or not user.check_password(pw):
        return _err("Thông tin đăng nhập không chính xác", 401)
    if not user.is_active:
        return _err("Tài khoản đã bị khóa", 403)
    user.last_login = datetime.now(timezone.utc)
    db.session.commit()
    login_user(user, remember=d.get("remember", True))
    return _ok({"user": user.to_dict()}, "Đăng nhập thành công")

@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return _ok(msg="Đăng xuất thành công")

@auth_bp.route("/me", methods=["GET"])
def me():
    if not current_user.is_authenticated:
        return _err("Chưa đăng nhập", 401)
    return _ok({"user": current_user.to_dict()})

@auth_bp.route("/me", methods=["PATCH"])
@login_required
def update_profile():
    d = request.get_json(silent=True) or {}
    user = current_user
    if "full_name" in d: user.full_name = d["full_name"].strip()
    if "preferred_league" in d and d["preferred_league"] in ("PL","UCL"):
        user.preferred_league = d["preferred_league"]
    if "avatar_url" in d: user.avatar_url = d["avatar_url"]
    if d.get("new_password"):
        if not d.get("current_password"): return _err("Cần nhập mật khẩu hiện tại")
        if not user.check_password(d["current_password"]): return _err("Mật khẩu hiện tại không đúng")
        if len(d["new_password"]) < 6: return _err("Mật khẩu mới phải từ 6 ký tự")
        user.set_password(d["new_password"])
    db.session.commit()
    return _ok({"user": user.to_dict()}, "Cập nhật thành công")
