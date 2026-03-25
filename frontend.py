#Step3: Build Streamlit frontend
import streamlit as st
from main import get_data_from_database
st.set_page_config(
    page_title="AI Data Analyst",
    page_icon="🤖",
    layout="centered"
)

st.title("🤖 AI Data Analyst")
st.markdown("Ask questions about your data in natural language.")

user_query = st.text_area("💬 Enter your question:", placeholder="e.g., Total products sold in 2025")

if st.button("Analyze"):
    if user_query.strip() == "":
        st.warning("Please enter a question.")
    else:
        with st.spinner("Analyzing your query..."):
            natural_answer, raw_results = get_data_from_database(user_query)

        st.success("Analysis complete!")
        st.markdown(f"### 💡 {natural_answer}")
        
        # Show raw results in an expander for transparency
        with st.expander("🔍 See raw database results"):
            st.write(raw_results)

st.markdown("""
    <style>
    textarea {
        font-size: 16px !important;
    }
    </style>
""", unsafe_allow_html=True)