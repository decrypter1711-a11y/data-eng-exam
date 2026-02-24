import streamlit as st
import requests
import base64
import json
import os
from datetime import datetime

# ─── PAGE CONFIG ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Exam Admin — GitHub Deployer",
    page_icon="🛡",
    layout="centered"
)

# ─── STYLES ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');

  html, body, [class*="css"] {
    font-family: 'JetBrains Mono', monospace;
    background-color: #04080f;
    color: #c0d4f0;
  }
  .stTextInput > div > input,
  .stTextArea > div > textarea,
  .stSelectbox > div > div {
    background-color: #080f1c !important;
    color: #c0d4f0 !important;
    border: 1px solid #0e2040 !important;
    font-family: 'JetBrains Mono', monospace !important;
  }
  .stButton > button {
    background-color: #00cfff;
    color: #000;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 700;
    letter-spacing: 1px;
    border: none;
    border-radius: 4px;
    padding: 10px 24px;
  }
  .stButton > button:hover {
    background-color: #00a8d0;
    color: #000;
  }
  .status-box {
    background: #080f1c;
    border: 1px solid #0e2040;
    border-radius: 6px;
    padding: 14px 18px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
    margin-top: 12px;
  }
  .success { border-left: 3px solid #00e6a0; color: #00e6a0; }
  .error   { border-left: 3px solid #ff3860; color: #ff3860; }
  .info    { border-left: 3px solid #00cfff; color: #00cfff; }
</style>
""", unsafe_allow_html=True)

# ─── HEADER ──────────────────────────────────────────────────────────────────
st.markdown("## 🛡 Exam Admin — GitHub Deployer")
st.markdown("`// Push exam files and student recordings to GitHub`")
st.divider()

# ─── GITHUB SETTINGS ─────────────────────────────────────────────────────────
st.markdown("### ⚙ GitHub Configuration")

col1, col2 = st.columns(2)
with col1:
    github_token = st.text_input(
        "GitHub Personal Access Token",
        type="password",
        placeholder="ghp_xxxxxxxxxxxx",
        help="Go to GitHub → Settings → Developer settings → Personal access tokens → Generate new token (scope: repo)"
    )
    repo_owner = st.text_input(
        "Repository Owner (username)",
        placeholder="your-github-username"
    )

with col2:
    repo_name = st.text_input(
        "Repository Name",
        placeholder="my-exam-repo"
    )
    branch = st.text_input(
        "Branch",
        value="main",
        placeholder="main"
    )

st.divider()

# ─── HELPER FUNCTIONS ────────────────────────────────────────────────────────
GITHUB_API = "https://api.github.com"

def get_headers(token):
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

def get_file_sha(token, owner, repo, path, branch):
    """Get SHA of existing file (needed to update it)."""
    url = f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}"
    r = requests.get(url, headers=get_headers(token), params={"ref": branch})
    if r.status_code == 200:
        return r.json().get("sha")
    return None

def push_file_to_github(token, owner, repo, path, content_bytes, commit_msg, branch):
    """Create or update a file in GitHub."""
    url = f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}"
    encoded = base64.b64encode(content_bytes).decode("utf-8")
    sha = get_file_sha(token, owner, repo, path, branch)

    payload = {
        "message": commit_msg,
        "content": encoded,
        "branch": branch
    }
    if sha:
        payload["sha"] = sha  # Required for update

    r = requests.put(url, headers=get_headers(token), data=json.dumps(payload))
    return r.status_code, r.json()

def verify_repo_access(token, owner, repo):
    url = f"{GITHUB_API}/repos/{owner}/{repo}"
    r = requests.get(url, headers=get_headers(token))
    return r.status_code == 200, r.json()

# ─── SECTION 1: PUSH EXAM HTML ───────────────────────────────────────────────
st.markdown("### 📄 Deploy Exam HTML Page")

exam_file_path = st.text_input(
    "Target path in repo",
    value="index.html",
    help="e.g. index.html  or  exams/data-engineering/index.html"
)

uploaded_html = st.file_uploader(
    "Upload updated exam HTML file",
    type=["html"],
    help="Upload the exam HTML file you want to push to GitHub Pages"
)

# Show current file if not uploading
use_default = st.checkbox("Use the default exam HTML (data_engineering_exam.html)", value=False)

col_a, col_b = st.columns([2,1])
with col_a:
    commit_msg_html = st.text_input(
        "Commit message",
        value=f"🚀 Update exam page [{datetime.now().strftime('%Y-%m-%d %H:%M')}]"
    )

if st.button("🚀 Push HTML to GitHub", key="push_html"):
    if not all([github_token, repo_owner, repo_name, branch]):
        st.markdown('<div class="status-box error">⚠ Please fill in all GitHub configuration fields.</div>', unsafe_allow_html=True)
    else:
        with st.spinner("Connecting to GitHub..."):
            ok, repo_info = verify_repo_access(github_token, repo_owner, repo_name)
            if not ok:
                st.markdown(f'<div class="status-box error">❌ Cannot access repo: {repo_info.get("message","Unknown error")}</div>', unsafe_allow_html=True)
            else:
                # Determine content
                html_bytes = None
                if uploaded_html is not None:
                    html_bytes = uploaded_html.read()
                elif use_default:
                    default_path = os.path.join(os.path.dirname(__file__), "data_engineering_exam.html")
                    if os.path.exists(default_path):
                        with open(default_path, "rb") as f:
                            html_bytes = f.read()
                    else:
                        st.markdown('<div class="status-box error">❌ Default exam HTML not found. Upload the file manually.</div>', unsafe_allow_html=True)

                if html_bytes:
                    with st.spinner(f"Pushing to {repo_owner}/{repo_name}/{exam_file_path}..."):
                        status, resp = push_file_to_github(
                            github_token, repo_owner, repo_name,
                            exam_file_path, html_bytes, commit_msg_html, branch
                        )
                    if status in (200, 201):
                        pages_url = f"https://{repo_owner}.github.io/{repo_name}/{exam_file_path.lstrip('/')}"
                        st.markdown(f'<div class="status-box success">✅ Successfully pushed!<br>🌐 GitHub Pages URL (if enabled):<br><a href="{pages_url}" target="_blank" style="color:#00cfff">{pages_url}</a></div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="status-box error">❌ Push failed ({status}): {resp.get("message","Unknown error")}</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="status-box error">⚠ No HTML content selected. Upload a file or check the default option.</div>', unsafe_allow_html=True)

st.divider()

# ─── SECTION 2: UPLOAD RECORDINGS ────────────────────────────────────────────
st.markdown("### 🎥 Upload Student Screen Recordings")
st.markdown("`// Recordings will be saved to: recordings/ folder in your repo`")

recordings_folder = st.text_input(
    "Recordings folder in repo",
    value="recordings",
    help="All recordings will be pushed into this folder"
)

uploaded_recordings = st.file_uploader(
    "Upload screen recording(s) (.webm / .mp4)",
    type=["webm", "mp4", "mkv"],
    accept_multiple_files=True,
    help="Upload the .webm recording files downloaded from the exam page"
)

commit_msg_rec = st.text_input(
    "Commit message for recordings",
    value=f"📹 Upload student recording [{datetime.now().strftime('%Y-%m-%d %H:%M')}]"
)

if st.button("📤 Upload Recordings to GitHub", key="push_recordings"):
    if not all([github_token, repo_owner, repo_name, branch]):
        st.markdown('<div class="status-box error">⚠ Please fill in all GitHub configuration fields.</div>', unsafe_allow_html=True)
    elif not uploaded_recordings:
        st.markdown('<div class="status-box error">⚠ No recording files selected.</div>', unsafe_allow_html=True)
    else:
        ok, _ = verify_repo_access(github_token, repo_owner, repo_name)
        if not ok:
            st.markdown('<div class="status-box error">❌ Cannot access repository. Check your token and repo name.</div>', unsafe_allow_html=True)
        else:
            results = []
            progress = st.progress(0)
            for i, rec_file in enumerate(uploaded_recordings):
                file_bytes = rec_file.read()
                target_path = f"{recordings_folder}/{rec_file.name}"
                with st.spinner(f"Uploading {rec_file.name}..."):
                    status, resp = push_file_to_github(
                        github_token, repo_owner, repo_name,
                        target_path, file_bytes, commit_msg_rec, branch
                    )
                results.append((rec_file.name, status, resp))
                progress.progress((i + 1) / len(uploaded_recordings))

            for fname, status, resp in results:
                if status in (200, 201):
                    st.markdown(f'<div class="status-box success">✅ {fname} → uploaded successfully</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="status-box error">❌ {fname} → failed ({status}): {resp.get("message","")}</div>', unsafe_allow_html=True)

st.divider()

# ─── SECTION 3: REPO STATUS ──────────────────────────────────────────────────
st.markdown("### 🔍 Verify Repository Access")

if st.button("🔍 Check Repo & List Files", key="check_repo"):
    if not all([github_token, repo_owner, repo_name]):
        st.markdown('<div class="status-box error">⚠ Enter token, owner, and repo name first.</div>', unsafe_allow_html=True)
    else:
        with st.spinner("Checking..."):
            ok, repo_info = verify_repo_access(github_token, repo_owner, repo_name)
        if ok:
            visibility = "Private" if repo_info.get("private") else "Public"
            pages_url = f"https://{repo_owner}.github.io/{repo_name}/"
            st.markdown(f"""
            <div class="status-box success">
              ✅ Connected to: <strong>{repo_info.get('full_name')}</strong><br>
              👁 Visibility: {visibility}<br>
              ⭐ Stars: {repo_info.get('stargazers_count',0)}<br>
              🌿 Default Branch: {repo_info.get('default_branch','main')}<br>
              🌐 GitHub Pages (if enabled): <a href="{pages_url}" target="_blank" style="color:#00cfff">{pages_url}</a>
            </div>
            """, unsafe_allow_html=True)

            # List recordings folder
            rec_url = f"{GITHUB_API}/repos/{repo_owner}/{repo_name}/contents/{recordings_folder}"
            r = requests.get(rec_url, headers=get_headers(github_token), params={"ref": branch})
            if r.status_code == 200:
                files = r.json()
                st.markdown(f"**📁 Files in `{recordings_folder}/`:**")
                for f in files:
                    size_kb = round(f.get('size', 0) / 1024, 1)
                    st.markdown(f"- `{f['name']}` — {size_kb} KB")
            else:
                st.markdown(f'<div class="status-box info">ℹ No recordings folder yet (will be created on first upload).</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="status-box error">❌ {repo_info.get("message","Cannot access repository")}</div>', unsafe_allow_html=True)

st.divider()
st.markdown("""
<div style="font-family:'JetBrains Mono',monospace;font-size:11px;color:#3a5070;text-align:center">
  // Exam Admin Tool · Recordings saved to recordings/ folder · HTML deployed to repo root
</div>
""", unsafe_allow_html=True)
