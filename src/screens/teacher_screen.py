import streamlit as st
from src.ui.base_layout import style_background_dashboard, style_base_layout

from src.components.header import header_dashboard
from src.components.footer import footer_dashboard
from src.components.subject_card import subject_card

from src.database.db import (
    check_teacher_exists,
    create_teacher,
    teacher_login,
    get_teacher_subjects,
)
from src.components.dialog_create_subject import create_subject_dialog


def teacher_screen():

    style_base_layout()
    style_background_dashboard()

    if "teacher_data" in st.session_state:
        teacher_dashboard()
    elif (
        "teacher_login_type" not in st.session_state
        or st.session_state.teacher_login_type == "login"
    ):
        teacher_screen_login()
    elif st.session_state.teacher_login_type == "register":
        teacher_screen_register()


def teacher_dashboard():
    teacher_data = st.session_state.teacher_data

    c1, c2 = st.columns(2, vertical_alignment="center", gap="xxlarge")
    with c1:
        header_dashboard()
    with c2:
        st.header(f"""Welcome, {teacher_data["name"]}!""")
        if st.button(
            "Logout",
            type="secondary",
            key="loginbackbtn",
            shortcut="control+backspace",
        ):
            st.session_state["is_logged_in"] = False
            del st.session_state.teacher_data
            st.rerun()

    st.space()

    if "current_teacher_tab" not in st.session_state:
        st.session_state.current_teacher_tab = "take_attendance"
    tab1, tab2, tab3 = st.columns(3)

    with tab1:
        type1 = (
            "primary"
            if st.session_state.current_teacher_tab == "take_attendance"
            else "tertiary"
        )
        if st.button(
            "Take Attendance", type=type1, width="stretch", icon=":material/ar_on_you:"
        ):
            st.session_state.current_teacher_tab = "take_attendance"
            st.rerun()

    with tab2:
        type2 = (
            "primary"
            if st.session_state.current_teacher_tab == "manage_subjects"
            else "tertiary"
        )
        if st.button(
            "Manage Subjects",
            type=type2,
            width="stretch",
            icon=":material/book_ribbon:",
        ):
            st.session_state.current_teacher_tab = "manage_subjects"
            st.rerun()

    with tab3:
        type3 = (
            "primary"
            if st.session_state.current_teacher_tab == "attendance_records"
            else "tertiary"
        )

        if st.button(
            "Attendance Records",
            type=type3,
            width="stretch",
            icon=":material/cards_stack:",
        ):
            st.session_state.current_teacher_tab = "attendance_records"
            st.rerun()

    st.divider()

    if st.session_state.current_teacher_tab == "take_attendance":
        teacher_tab_take_attendance()
    if st.session_state.current_teacher_tab == "manage_subjects":
        teacher_tab_manage_subjects()
    if st.session_state.current_teacher_tab == "attendance_records":
        teacher_tab_attendance_records()

    footer_dashboard()


def teacher_tab_take_attendance():
    st.header("Take AI Attendance")


def teacher_tab_manage_subjects():
    teacher_id = st.session_state.teacher_data["teacher_id"]
    col1, col2 = st.columns(2)
    with col1:
        st.header("Manage Subjects")
    with col2:
        if st.button("Create New Subject", width="stretch"):
            create_subject_dialog(teacher_id)

    # List all Subjects
    subjects = get_teacher_subjects(teacher_id)
    if subjects:
        for sub in subjects:
            stats = [
                ("👥", "Students", sub["total_students"]),
                ("🕰️", "Classes", sub["total_classes"]),
            ]

        def share_btn():
            if st.button(
                f"Share Code: {sub['name']}",
                key=f"share_{sub['subject_code']}",
                icon=":material/share:",
            ):
                share_subject_dialog(sub["name"], sub["subject_code"])
            st.space()

        subject_card(
            name=sub["name"],
            code=sub["subject_code"],
            section=sub["section"],
            stats=stats,
            footer_callback=share_btn,
        )
    else:
        st.info("NO SUBJECTS FOUND. CREATE ONE ABOVE")


def teacher_tab_attendance_records():
    st.header("Attendance Records")


def login_teacher(username, password):
    if not username or not password:
        return False

    teacher = teacher_login(username, password)

    if teacher:
        st.session_state.user_role = "teacher"
        st.session_state.teacher_data = teacher
        st.session_state.is_logged_in = True
        return True


def teacher_screen_login():

    c1, c2 = st.columns(2, vertical_alignment="center", gap="xxlarge")
    with c1:
        header_dashboard()
    with c2:
        if st.button(
            "Go back to Home",
            type="secondary",
            key="loginbackbtn",
            shortcut="control+backspace",
        ):
            st.session_state["login_type"] = None
            st.rerun()

    st.header("Login using password", text_alignment="center")
    st.space()
    st.space()

    username = st.text_input("Enter username", placeholder="ananyaroy")
    password = st.text_input(
        "Enter password", placeholder="Enter password", type="password"
    )

    st.divider()

    btnc1, btnc2 = st.columns(2, vertical_alignment="center", gap="xxlarge")

    with btnc1:
        if st.button(
            "Login",
            icon=":material/passkey:",
            shortcut="control+enter",
            width="stretch",
        ):
            if login_teacher(username, password):
                st.toast("welcome back!", icon="👋")
                import time

                time.sleep(1)
                st.rerun()

            else:
                st.error("Invalid username and password!")

    with btnc2:
        if st.button(
            "Register Instead",
            type="primary",
            icon=":material/passkey:",
            width="stretch",
        ):
            st.session_state.teacher_login_type = "register"
            st.rerun()

    footer_dashboard()


def register_teacher(username, teacher_name, password, confirm_password):
    if not username or not teacher_name or not password or not confirm_password:
        return False, "All fields are required!"
    if check_teacher_exists(username):
        return False, "Username already taken"
    if password != confirm_password:
        return False, "Password doesn't match"

    try:
        create_teacher(username, teacher_name, password)
        return True, "Successfully Created! Login now"
    except Exception as e:
        return False, "Unexpected Error!"


def teacher_screen_register():

    c1, c2 = st.columns(2, vertical_alignment="center", gap="xxlarge")
    with c1:
        header_dashboard()
    with c2:
        if st.button(
            "Go back to Home",
            type="secondary",
            key="loginbackbtn",
            shortcut="control+backspace",
        ):
            st.session_state["login_type"] = None
            st.rerun()

    st.header("Register your teacher profile", text_alignment="center")
    st.space()
    st.space()

    username = st.text_input("Enter username", placeholder="ananyaroy")
    teacher_name = st.text_input("Enter name", placeholder="Ananya Roy")

    password = st.text_input(
        "Enter password", placeholder="Enter password", type="password"
    )
    confirm_password = st.text_input(
        "Confirm password", placeholder="Confirm your password", type="password"
    )

    st.divider()

    btnc1, btnc2 = st.columns(2, vertical_alignment="center", gap="xxlarge")

    with btnc1:
        if st.button(
            "Register now",
            icon=":material/passkey:",
            shortcut="control+enter",
            width="stretch",
        ):
            success, message = register_teacher(
                username, teacher_name, password, confirm_password
            )
            if success:
                st.success(message)
                import time

                time.sleep(2)
                st.session_state.teacher_login_type = "login"
                st.rerun()
            else:
                st.error(message)

    with btnc2:
        if st.button(
            "Login Instead",
            type="primary",
            icon=":material/passkey:",
            width="stretch",
        ):
            st.session_state.teacher_login_type = "login"

    footer_dashboard()
