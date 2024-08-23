import os
import json
import streamlit as st
from phi.tools.tavily import TavilyTools
from assistant import get_research_assistant  # type: ignore
from dotenv import load_dotenv
import requests

# Load environment variables from .env for local development
load_dotenv()

# Check if running in Streamlit Cloud or locally
if "GROQ_API_KEY" in st.secrets:
    groq_api_key = st.secrets["GROQ_API_KEY"]
    openai_api_key = st.secrets["OPENAI_API_KEY"]
    tavily_api_key = st.secrets["TAVILY_API_KEY"]
    langchain_api_key = st.secrets["LANGCHAIN_API_KEY"]
    diffbot_api_key = st.secrets["DIFFBOT_API_KEY"]
    scraper_api_key = st.secrets["SCRAPER_API_KEY"]
else:
    groq_api_key = os.getenv("GROQ_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    langchain_api_key = os.getenv("LANGCHAIN_API_KEY")
    diffbot_api_key = os.getenv("DIFFBOT_API_KEY")
    scraper_api_key = os.getenv("SCRAPER_API_KEY")

# Validate that API keys are available
if not all([groq_api_key, openai_api_key, tavily_api_key, langchain_api_key, diffbot_api_key, scraper_api_key]):
    st.error("Missing one or more API keys. Please check your environment.")
    st.stop()

st.set_page_config(page_title="Research Assistant", page_icon=":orange_heart:")
st.title("Research Assistant for Consultants")

# Define individual agents
class TavilyAgent:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def search(self, topic: str) -> str:
        return TavilyTools(api_key=self.api_key).web_search_using_tavily(topic)

class DiffbotAgent:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def search(self, topic: str) -> str:
        # Placeholder for Diffbot API search logic
        return f"Simulated Diffbot search results for topic: {topic}"

class ScraperAPIAgent:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def search(self, topic: str) -> str:
        response = requests.get(f"https://api.scraperapi.com?api_key={self.api_key}&url=https://www.google.com/search?q={topic}")
        if response.status_code == 200:
            return response.text
        return "Failed to retrieve results from ScraperAPI"

class JobsAndOrgsAgent:
    def search(self, topic: str) -> str:
        # Placeholder for job and organization crawler logic
        return f"Simulated job and organization info for topic: {topic}"

class ReportGeneratorAgent:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.assistant = get_research_assistant(model=model_name)

    def generate_report(self, search_results: str) -> str:
        final_report = ""
        try:
            for delta in self.assistant.run(search_results):
                final_report += delta
        except Exception as e:
            st.error(f"Error generating draft with {self.model_name}: {e}")
        return final_report

# Manager or orchestrator agent
class ResearchManager:
    def __init__(self, tavily_agent, diffbot_agent, scraperapi_agent, jobs_and_orgs_agent):
        self.agents = {
            "Tavily": tavily_agent,
            "Diffbot": diffbot_agent,
            "ScraperAPI": scraperapi_agent,
            "Jobs & Organizations": jobs_and_orgs_agent
        }

    def conduct_research(self, search_agent: str, topic: str) -> str:
        agent = self.agents.get(search_agent)
        if agent:
            return agent.search(topic)
        return "No valid search agent selected."

# Initialize agents
tavily_agent = TavilyAgent(api_key=tavily_api_key)
diffbot_agent = DiffbotAgent(api_key=diffbot_api_key)
scraperapi_agent = ScraperAPIAgent(api_key=scraper_api_key)
jobs_and_orgs_agent = JobsAndOrgsAgent()

# Initialize manager
research_manager = ResearchManager(tavily_agent, diffbot_agent, scraperapi_agent, jobs_and_orgs_agent)

# Streamlit UI
def main() -> None:
    llm_model = st.sidebar.selectbox("Select Model", ["llama3-70b-8192", "llama3-8b-8192", "mixtral-8x7b-32768"])
    search_agent = st.sidebar.selectbox("Select Search Agent", ["Tavily", "Diffbot", "ScraperAPI", "Jobs & Organizations"])

    if "llm_model" not in st.session_state:
        st.session_state["llm_model"] = llm_model
    elif st.session_state["llm_model"] != llm_model:
        st.session_state["llm_model"] = llm_model
        st.rerun()

    if "search_agent" not in st.session_state:
        st.session_state["search_agent"] = search_agent
    elif st.session_state["search_agent"] != search_agent:
        st.session_state["search_agent"] = search_agent
        st.rerun()

    input_topic = st.text_input("",value="please enter a topic")
    generate_report = st.button("Generate Report")

    if generate_report:
        search_results = research_manager.conduct_research(search_agent, input_topic)
        if search_results:
            st.markdown("## Search Results")
            st.write(search_results)

            report_generator = ReportGeneratorAgent(model_name=llm_model)
            final_report = report_generator.generate_report(search_results)
            st.markdown("## Final Report")
            st.text_area("Draft", value=final_report, height=400)

            with open("report.json", "w") as f:
                json.dump({"topic": input_topic, "report": final_report}, f, indent=4)

            with open("report.json", "r") as f:
                st.download_button(label="Download Report", data=f, file_name="report.json", mime="application/json")
        else:
            st.write("Sorry, report generation failed. Please try again.")

    st.sidebar.markdown("---")
    if st.sidebar.button("Restart"):
        st.rerun()

main()