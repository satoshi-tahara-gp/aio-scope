"""認証モジュール: Goodpatchドメイン制限 + 共通パスワード"""
import streamlit as st


def _allowed_domains():
    try:
        return list(st.secrets.get("allowed_email_domains", ["goodpatch.co.jp"]))
    except Exception:
        return ["goodpatch.co.jp"]


def _expected_password():
    try:
        return st.secrets.get("app_password", "goodpatch-aio-2026")
    except Exception:
        return "goodpatch-aio-2026"


def login_view():
    """ログイン画面を表示。成功時 session_state.authenticated = True をセット"""
    st.markdown(
        """
        <div style='text-align:center; margin-top: 3rem; margin-bottom: 2rem;'>
            <div style='font-size: 48px; font-weight: 700; color:#1E293B; letter-spacing: -0.02em;'>
                AIO-Scope
            </div>
            <div style='color:#64748B; font-size: 14px; margin-top: 0.5rem;'>
                AIO/SEO 現状診断ツール &nbsp;|&nbsp; Goodpatch Market Design Div
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container(border=True):
            st.markdown("### サインイン")
            email = st.text_input(
                "メールアドレス",
                placeholder="yourname@goodpatch.co.jp",
                key="login_email",
            )
            password = st.text_input(
                "パスワード",
                type="password",
                placeholder="共通パスワードを入力",
                key="login_password",
            )
            if st.button("ログイン", type="primary", use_container_width=True):
                domains = _allowed_domains()
                domain_ok = any(email.lower().endswith("@" + d) for d in domains)
                if not email or "@" not in email:
                    st.error("メールアドレスを入力してください")
                elif not domain_ok:
                    st.error(
                        f"許可されたドメインのメールアドレスのみログイン可能です "
                        f"({', '.join('@' + d for d in domains)})"
                    )
                elif password != _expected_password():
                    st.error("パスワードが正しくありません")
                else:
                    st.session_state.authenticated = True
                    st.session_state.user_email = email
                    st.rerun()

            st.caption(
                "パスワードが分からない場合は Market Design Div の管理者にお問い合わせください"
            )


def require_auth():
    """呼び出し時に認証を要求。未認証ならログイン画面を出して停止"""
    if not st.session_state.get("authenticated"):
        login_view()
        st.stop()


def logout():
    for key in ["authenticated", "user_email"]:
        if key in st.session_state:
            del st.session_state[key]
