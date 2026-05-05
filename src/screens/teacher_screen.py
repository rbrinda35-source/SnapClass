import streamlit as st
from src.ui.base_layout import style_background_dashboard, style_base_layout

from src.components.header import header_dashboard
from src.components.footer import footer_dashboard
from src.components.subject_card import subject_card
from src.components.dialog_share_subject import share_subject_dialog
from src.components.dialog_add_photo import add_photos_dialog
from src.components.dialog_attendance_results import attendance_result_dialog
from src.components.dialog_attendance_voice import voice_attendance_dialog

from src.pipelines.face_pipeline import predict_attendance

from src.database.config import supabase

import numpy as np
import pandas as pd
from datetime import datetime

from src.database.db import (
    check_teacher_exists,
    create_teacher,
    teacher_login,
    get_teacher_subjects,
    get_attendance_for_teacher
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
    teacher_id = st.session_state.teacher_data["teacher_id"]
    st.header("Take AI Attendance")
    
    if 'attendance_images' not in st.session_state:
        st.session_state.attendance_images = []
        
    subjects = get_teacher_subjects(teacher_id)
    
    if not subjects:
        st.warning("You have not created any subjects yet. Please create one to begin!")
        return
    
    subject_options = {f"{sub['name']} - {sub['subject_code']}" : sub['subject_id'] for sub in subjects}
    
    col1, col2 = st.columns([3, 1], vertical_alignment="bottom")
    with col1:
        selected_subject_label = st.selectbox("Select Subject", options=list(subject_options.keys()), key="attendance_subject")
        
    with col2:
        if st.button("Add Photos", type="primary", icon=":material/photo_prints:", width="stretch"):
            add_photos_dialog()
            
    selected_subject_id = subject_options[selected_subject_label]
    
    st.divider()
    
    if st.session_state.attendance_images:
        st.header("Added Photos")
        gallery_cols = st.columns(4)
        
        for idx, img in enumerate(st.session_state.attendance_images):
            with gallery_cols[idx % 4]:
                st.image(img, width='stretch', caption=f"Photo {idx+1}")
        
        has_photos = bool(st.session_state.attendance_images)
        
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("Clear all photos", type="tertiary", width="stretch", icon=":material/delete:", disabled=not has_photos):
                st.session_state.attendance_images = []
                st.rerun()
        
        with c2:
            if st.button("Run face analysis", type="secondary", width="stretch", icon=":material/analytics:", disabled=not has_photos):
                with st.spinner("Analyzing photos for attendance..."):
                    all_detected_ids = {}
                    
                    for idx, img in enumerate(st.session_state.attendance_images):
                        img_np = np.array(img.convert("RGB"))
                        detected, _, _ = predict_attendance(img_np)
                        
                        if detected:
                            for student_id in detected:
                                sid = int(student_id)
                                all_detected_ids.setdefault(sid, []).append(f"Photo {idx+1}")
                    
                    enrolled_res = supabase.table("subject_students").select("student_id, students(*)").eq("subject_id", selected_subject_id).execute()
                    enrolled_students = enrolled_res.data
                    
                    results, attendance_logs = [], []

                    if not enrolled_students:
                        st.warning("No students are enrolled in this subject yet.")
                    else:
                        results, attendance_logs = [], []
                        current_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                        
                        for node in enrolled_students:
                            student = node["students"]
                            sources = all_detected_ids.get(int(student["student_id"]), [])
                            is_present = len(sources) > 0
                            
                            results.append({
                                "Name": student['name'],
                                "ID": student['student_id'],
                                "Sources": ", ".join(sources) if is_present else "-",
                                "Status": "✅ Present" if is_present else "❌ Absent"
                            })
                            
                            attendance_logs.append({
                                "student_id": student['student_id'],
                                "subject_id": selected_subject_id,
                                "timestamp": current_time,
                                "is_present": bool(is_present)
                            })
                    
                        attendance_result_dialog(pd.DataFrame(results), attendance_logs)
             
        with c3:
            if st.button("Use voice attendance", type="primary", width="stretch", icon=":material/mic:"):
                voice_attendance_dialog(selected_subject_id)
               
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
    
    teacher_id = st.session_state.teacher_data["teacher_id"]
    
    records = get_attendance_for_teacher(teacher_id)
    
    if not records:
        return
    
    data = []
    for rec in records:
        ts = rec.get("timestamp")
        
        data.append({
            "ts_group": ts.split("T")[0] if ts else None,
            "Time": datetime.fromisoformat(ts).strftime("%Y-%m-%d %I:%M %p") if ts else "N/A",
            "Subject": rec.get("subjects", {}).get("name", "Unknown"),
            "Subject Code": rec.get("subjects", {}).get("subject_code", "Unknown"),
            "is_present": bool(rec.get("is_present", False))
        })
        
    df = pd.DataFrame(data)
    
    summary = (
        df.groupby(["ts_group", "Time", "Subject", "Subject Code"])
        .agg(Total_Students = ("is_present", "count"), Present_Count = ("is_present", "sum"))
    ).reset_index()
    
    summary["Attendance Stats"] = (
        "✅" + summary["Present_Count"].astype(str) + " / " 
        + summary["Total_Students"].astype(str) + ' Students Present'
    )

    display_df = ( summary.sort_values(by = "ts_group", ascending=False)
                  [["Time", "Subject", "Subject Code", "Attendance Stats"]]
                )
    
    st.dataframe(display_df, hide_index=True, width='stretch')
    
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
