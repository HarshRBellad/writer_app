import os
import json
import streamlit as st
from phi.tools.tavily import TavilyTools
from assistant import get_research_assistant  # type: ignore
from dotenv import load_dotenv

# Load environment variables from .env for local development
load_dotenv()

# Check if running in Streamlit Cloud or locally
if "GROQ_API_KEY" in st.secrets:
    # Running on Streamlit Cloud
    groq_api_key = st.secrets["GROQ_API_KEY"]
    openai_api_key = st.secrets["OPENAI_API_KEY"]
    tavily_api_key = st.secrets["TAVILY_API_KEY"]
    langchain_api_key = st.secrets["LANGCHAIN_API_KEY"]
else:
    # Running locally with dotenv
    groq_api_key = os.getenv("GROQ_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    langchain_api_key = os.getenv("LANGCHAIN_API_KEY")

# Validate that API keys are available
if not groq_api_key or not openai_api_key or not tavily_api_key or not langchain_api_key:
    st.error("Missing one or more API keys. Please check your environment.")
    st.stop()

st.set_page_config(
    page_title="Research Assistant",
    page_icon=":orange_heart:",
)
st.title("Research Assistant powered by Grad Hub")
st.markdown("##### :orange_heart: built using [phidata](https://github.com/phidatahq/phidata)")


def main() -> None:
    # Get model
    llm_model = st.sidebar.selectbox(
        "Select Model", options=["llama3-70b-8192", "llama3-8b-8192", "mixtral-8x7b-32768"]
    )
    # Set assistant_type in session state
    if "llm_model" not in st.session_state:
        st.session_state["llm_model"] = llm_model
    # Restart the assistant if assistant_type has changed
    elif st.session_state["llm_model"] != llm_model:
        st.session_state["llm_model"] = llm_model
        st.rerun()

    # Initialize previously searched topics
    if "previous_topics" not in st.session_state:
        st.session_state["previous_topics"] = []

    # Get topic for report
    input_topic = st.text_input(
        ":female-scientist: Enter a topic",
        value="Superfast Llama 3 inference on Groq Cloud",
    )
    # Button to generate report
    generate_report = st.button("Generate Report")
    if generate_report:
        st.session_state["topic"] = input_topic
        if input_topic not in st.session_state["previous_topics"]:
            st.session_state["previous_topics"].append(input_topic)

    st.sidebar.markdown("## Previously Searched Topics")
    for topic in st.session_state["previous_topics"]:
        if st.sidebar.button(topic):
            st.session_state["topic"] = topic

    if "topic" in st.session_state:
        report_topic = st.session_state["topic"]
        research_assistant = get_research_assistant(model=llm_model)
        tavily_search_results = None

        with st.status("Searching Web", expanded=True) as status:
            with st.container():
                tavily_container = st.empty()
                tavily_search_results = TavilyTools(api_key=tavily_api_key).web_search_using_tavily(report_topic)
                if tavily_search_results:
                    tavily_container.markdown(tavily_search_results)
            status.update(label="Web Search Complete", state="complete", expanded=False)

        if not tavily_search_results:
            st.write("Sorry, report generation failed. Please try again.")
            return

        with st.spinner("Generating Report"):
            final_report = ""
            final_report_container = st.empty()
            for delta in research_assistant.run(tavily_search_results):
                final_report += delta  # type: ignore
                final_report_container.markdown(final_report)

            # Save the generated report as a JSON file
            report_data = {"topic": report_topic, "report": final_report}
            with open("report.json", "w") as f:
                json.dump(report_data, f, indent=4)

            # Provide a download button
            with open("report.json", "r") as f:
                st.download_button(
                    label="Download Report",
                    data=f,
                    file_name="report.json",
                    mime="application/json"
                )

    st.sidebar.markdown("---")
    if st.sidebar.button("Restart"):
        st.rerun()


main()