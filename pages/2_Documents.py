# pages/2_Documents.py

"""
This page allows users to upload, view, and manage their health documents.
Files are securely stored in an AWS S3 bucket, and metadata is saved in the database.
"""

# ==============================================================================
# 1. IMPORTS
# ==============================================================================
import streamlit as st
import boto3
import os
import time
from botocore.exceptions import ClientError

# Import utility functions and database models
from modules.utils import page_setup, check_login, get_db_session, get_user_id
from modules.database import Document

# ==============================================================================
# 2. PAGE SETUP AND AUTHENTICATION CHECK
# ==============================================================================
page_setup()
check_login()

# ==============================================================================
# 3. S3 AND DATABASE SETUP
# ==============================================================================

# Fetch S3 configuration from environment variables
S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME")

# Initialize S3 client
# Boto3 will automatically use the credentials from environment variables
try:
    s3_client = boto3.client('s3')
except Exception as e:
    st.error(f"Failed to initialize S3 client. Please check your AWS credentials and region setup. Error: {e}")
    st.stop()
    
# Check if bucket name is configured
if not S3_BUCKET_NAME:
    st.error("S3_BUCKET_NAME environment variable is not set. File uploads will be disabled.")
    st.stop()

# Get the current user's database ID
user_id = st.session_state.get("user_db_id")
if not user_id:
    st.error("User not properly logged in. Cannot load documents.")
    st.stop()

# ==============================================================================
# 4. UPLOAD FUNCTIONALITY
# ==============================================================================

st.title("📄 My Documents")
st.write("Securely upload, view, and manage your prescriptions, lab reports, and other health documents.")

with st.form("document_upload_form", clear_on_submit=True):
    uploaded_files = st.file_uploader(
        "Upload new documents",
        type=['pdf', 'png', 'jpg', 'jpeg'],
        accept_multiple_files=True
    )
    description = st.text_input("Add a description for the document(s)")
    submitted = st.form_submit_button("Upload and Save")

    if submitted and uploaded_files:
        with st.spinner("Uploading files..."):
            for file in uploaded_files:
                # Generate a unique, secure key for the S3 object
                # Format: username/timestamp-filename
                username = st.session_state.get("username", "unknown_user")
                storage_key = f"{username}/{int(time.time())}-{file.name}"

                try:
                    # Upload file to S3
                    s3_client.upload_fileobj(file, S3_BUCKET_NAME, storage_key)

                    # Save metadata to the database
                    with get_db_session() as db:
                        new_doc = Document(
                            original_filename=file.name,
                            storage_key=storage_key,
                            description=description,
                            owner_id=user_id
                        )
                        db.add(new_doc)
                        db.commit()

                except ClientError as e:
                    st.error(f"Failed to upload {file.name} to S3. Error: {e}")
                except Exception as e:
                    st.error(f"An error occurred while saving {file.name}. Error: {e}")
            
        st.success("All files uploaded successfully!")
        st.rerun() # Rerun the script to show the new documents in the list below

# ==============================================================================
# 5. DOCUMENT LISTING, DOWNLOADING, AND DELETION
# ==============================================================================
st.divider()
st.subheader("Your Uploaded Documents")

with get_db_session() as db:
    user_docs = db.query(Document).filter(Document.owner_id == user_id).order_by(Document.upload_date.desc()).all()

if not user_docs:
    st.info("You have not uploaded any documents yet. Use the form above to get started.")
else:
    for doc in user_docs:
        with st.container(border=True):
            col1, col2, col3 = st.columns([4, 1, 1])
            with col1:
                st.markdown(f"**{doc.original_filename}**")
                st.caption(f"Description: {doc.description}" if doc.description else "No description")
                st.caption(f"Uploaded on: {doc.upload_date.strftime('%Y-%m-%d %H:%M')}")

            with col2:
                # --- Download Button ---
                try:
                    # Generate a pre-signed URL that is valid for 1 minute
                    download_url = s3_client.generate_presigned_url(
                        'get_object',
                        Params={'Bucket': S3_BUCKET_NAME, 'Key': doc.storage_key},
                        ExpiresIn=300  # URL expires in 300 seconds (5 minutes)
                    )
                    st.link_button("⬇️ Download", url=download_url)
                except Exception as e:
                    st.error("Could not generate download link.")
            
            with col3:
                # --- Delete Button ---
                if st.button("🗑️ Delete", key=f"delete_{doc.id}", type="primary"):
                    try:
                        # 1. Delete from S3
                        s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=doc.storage_key)
                        
                        # 2. Delete from Database
                        with get_db_session() as db_session:
                            doc_to_delete = db_session.query(Document).filter(Document.id == doc.id).first()
                            db_session.delete(doc_to_delete)
                            db_session.commit()
                        
                        st.success(f"Deleted '{doc.original_filename}' successfully.")
                        st.rerun() # Refresh the page to update the list
                    except Exception as e:
                        st.error(f"Failed to delete file. Error: {e}")