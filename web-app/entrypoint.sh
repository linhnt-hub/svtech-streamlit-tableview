#! bin/bash
mkdir -p $DB_DIR
streamlit run streamlit_mainpage.py --server.port=8501 --server.address=0.0.0.0