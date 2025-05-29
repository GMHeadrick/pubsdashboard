# First install required packages:
# pip install streamlit pandas plotly requests

import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# Step 1: Retrieve SUNY Downstate publications
def get_downstate_publications():
    OPENALEX_API = "https://api.openalex.org/works"
    DOWNSTATE_ID = "i181697535"  # Verify institution ID via OpenAlex
    
    params = {
        "filter": f"institutions.id:{DOWNSTATE_ID}",
        "per-page": 200  # Max per page (paginate for more results)
    }
    
    response = requests.get(OPENALEX_API, params=params)
    return response.json()["results"]

# Step 2: Process data into DataFrame
def process_data(publications):
    data = []
    for work in publications:
        entry = {
            "Title": work["title"],
            "Year": work["publication_year"],
            "Citations": work["cited_by_count"],
            "OA": work["open_access"]["is_oa"],
            "Type": work["type"],
            "Authors": ", ".join([a["author"]["display_name"] for a in work["authorships"]]),
            "DOI": work["doi"],
            "Topics": ", ".join([c["display_name"] for c in work["concepts"]])
        }
        data.append(entry)
    return pd.DataFrame(data)

# Step 3: Create Streamlit dashboard
def main():
    st.title("SUNY Downstate Publications Dashboard")
    st.caption("Data from OpenAlex API")
    
    # Load data
    publications = get_downstate_publications()
    df = process_data(publications)
    
    # Filters sidebar
    st.sidebar.header("Filters")
    min_year, max_year = st.sidebar.slider(
        "Publication Year", 
        min_value=int(df["Year"].min()), 
        max_value=int(df["Year"].max()),
        value=(2010, 2025)
    )
    
    # Filtered data
    filtered_df = df[(df["Year"] >= min_year) & (df["Year"] <= max_year)]
    
    # Key metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Publications", len(filtered_df))
    with col2:
        st.metric("Open Access Rate", f"{filtered_df['OA'].mean()*100:.1f}%")
    with col3:
        st.metric("Avg Citations", filtered_df["Citations"].mean().round(1))
    
    # Visualization tabs
    tab1, tab2, tab3 = st.tabs(["Trends", "Topics", "Authors"])
    
    with tab1:
        fig = px.line(filtered_df.groupby("Year").size().reset_index(name="Count"), 
                     x="Year", y="Count", title="Publication Trends")
        st.plotly_chart(fig)
    
    with tab2:
        topics = filtered_df["Topics"].str.split(", ").explode()
        fig = px.bar(topics.value_counts().head(10), 
                    title="Top Research Topics")
        st.plotly_chart(fig)
    
    with tab3:
        authors = filtered_df["Authors"].str.split(", ").explode()
        fig = px.bar(authors.value_counts().head(10), 
                    title="Most Prolific Authors")
        st.plotly_chart(fig)
    
    # Data table
    st.subheader("Publication Details")
    st.dataframe(filtered_df, use_container_width=True)

if __name__ == "__main__":
    main()
