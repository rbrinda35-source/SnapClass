import streamlit as st
from src.database.db import enroll_student_to_subject
from src.database.config import supabase
from PIL import Image
import time

@st.dialog("Capture or upload photos")
def add_photos_dialog():
    st.write("Add classroom photos to scan for attendance")
    
    if 'photo_tab' not in st.session_state:
        st.session_state['photo_tab'] = 'capture'
        
    t1, t2 = st.columns(2)
    with t1:
        type_camera = "primary" if st.session_state.photo_tab == 'camera' else "tertiary"
        if st.button("Camera", type = type_camera, width="stretch"):
            st.session_state.photo_tab = 'camera'
    
    with t2:
        type_upload = "primary" if st.session_state.photo_tab == 'upload' else "tertiary"
        if st.button("Upload", type = type_upload, width="stretch"):
            st.session_state.photo_tab = 'upload'
            
    if st.session_state.photo_tab == 'camera':
        cam_photos = st.camera_input("Take Snapshot", key="dialog_cam")
        if cam_photos:
            st.session_state.attendance_images.append(Image.open(cam_photos))
            st.toast("Photo captured!")    
            st.rerun()
    
    if st.session_state.photo_tab == 'upload':
        uploaded_photos = st.file_uploader("Upload Photos", accept_multiple_files=True, type=["jpg", "jpeg", "png"], key="dialog_upload")
        if uploaded_photos:
            for photo in uploaded_photos:
                st.session_state.attendance_images.append(Image.open(photo))
            st.toast(f"{len(uploaded_photos)} photo(s) uploaded!")
            st.rerun()
    
    st.divider()
    if st.button("Done", type="primary", width="stretch"):
        st.session_state.pop('photo_tab')
        st.rerun()