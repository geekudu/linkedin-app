import streamlit as st
from openai import OpenAI
from bs4 import BeautifulSoup
from scrapfly import ScrapflyClient, ScrapeConfig
from pydantic import BaseModel
import os

# Initialize Scrapfly API client
scrapfly_api_key =  os.getenv('SCRAPFLY')
scrapfly_client = ScrapflyClient(key=scrapfly_api_key)

# Initialize OpenAI API
api_key = os.getenv('OPENAI')
openai_client = OpenAI(
    api_key=api_key,
)

# Model to hold LinkedIn info
class LinkedinInfo(BaseModel):
    name: str
    position: str
    company: str
    linkedin_url: str

# Function to perform Google search
def google_search(query):
    search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}&hl=en"
    response = scrapfly_client.scrape(ScrapeConfig(
        url=search_url,
        render_js=True,  # Set to True to render JavaScript
    ))
    return response.content

# Function to process scraped data and extract LinkedIn info using OpenAI
def get_most_accurate_linkedin_url(content, search):
    prompt = (f"From the following Google search results, find the most accurate LinkedIn profile URL matching the search term '{search}'. "
              "Also, extract the name, position, and company name if available. Format the output as JSON with fields 'name', 'position', 'company', and 'linkedin_url'. "
              f"Search Results: '{content}")
    
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",  # Use the appropriate model
        messages=[
            {"role": "system", "content": "You are a helpful assistant that extracts LinkedIn profile information."},
            {"role": "user", "content": prompt}
        ],
        response_format={ "type": "json_object" },
    )

    # Extract and format the response
    return response.choices[0].message.content

# Parse HTML content to get the text from the body
def parse_html(content):
    soup = BeautifulSoup(content, 'html.parser')
    body = soup.find('body')
    text_content = body.get_text() if body else ''
    return text_content

# Streamlit App
st.title("LinkedIn Profile Extractor")
st.write("Find the most accurate LinkedIn profile for the specified position and company.")

# User input for position and company
position = st.text_input("Enter Position", placeholder="e.g., CEO, Director")
company = st.text_input("Enter Company", placeholder="e.g., Google, Amazon")

# When the user clicks the 'Search' button
if st.button("Search LinkedIn Profile"):
    if position and company:
        query = f"{position} of {company} LinkedIn"

        # Step 1: Use Scrapfly to scrape Google search results
        st.write("Searching Google for relevant LinkedIn profiles...")
        search_results = google_search(query)
        
        # Step 2: Parse HTML content from the search results
        st.write("Parsing search results...")
        parsed_content = parse_html(search_results)

        # Step 3: Use OpenAI to extract the most accurate LinkedIn profile URL
        st.write("Extracting LinkedIn profile information...")
        linkedin_info = get_most_accurate_linkedin_url(parsed_content, query)
        
        # Display the result in a visually appealing manner
        st.subheader("Most Accurate LinkedIn Profile Found")
        if linkedin_info:
            linkedin_data = eval(linkedin_info)
            st.write(f"**Name:** {linkedin_data['name']}")
            st.write(f"**Position:** {linkedin_data['position']}")
            st.write(f"**Company:** {linkedin_data['company']}")
            st.write(f"**LinkedIn URL:** [Visit Profile]({linkedin_data['linkedin_url']})")
        else:
            st.error("No LinkedIn profile found. Try refining your search.")
    else:
        st.warning("Please enter both position and company.")

# Add some styling to make it visually pleasing
st.markdown(
    """
    <style>
    div.stButton > button {
        background-color: #4CAF50;
        color: white;
        border-radius: 8px;
    }

    h1, h2, h3, h4, h5, h6 {
        color: #0A74DA;
    }

    .stTextInput, .stTextArea {
        border-radius: 10px;
        background-color: #F5F5F5;
        border: 1px solid #CCCCCC;
    }

    .stMarkdown {
        font-size: 1.1em;
        line-height: 1.6;
    }
    </style>
    """,
    unsafe_allow_html=True
)
