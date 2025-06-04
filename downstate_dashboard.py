import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime

# Limit API to first 200 works only
@st.cache_data(show_spinner=False)
def get_downstate_publications_limited():
    OPENALEX_API = "https://api.openalex.org/works"
    DOWNSTATE_ID = "I97018004"

    current_year = datetime.now().year
    start_year = current_year - 1  # last 2 years

    params = {
        "filter": f"institutions.id:{DOWNSTATE_ID},from_publication_date:{start_year}-01-01",
        "per-page": 200,
        "mailto": "gregg.headrick@downstate.edu"
    }

    response = requests.get(OPENALEX_API, params=params)
    if response.status_code != 200:
        st.error("Failed to fetch data from OpenAlex.")
        return []
    return response.json().get("results", [])

# Process data into DataFrame
def process_data(publications):
    data = []
    for work in publications:
        try:
            year = work.get("publication_year")
            if not isinstance(year, int):
                continue

            entry = {
                "Title": work.get("title", "No title"),
                "Year": year,
                "Citations": work.get("cited_by_count", 0),
                "OA": work.get("open_access", {}).get("is_oa", False),
                "Type": work.get("type", "unknown"),
                "Authors": ", ".join([a["author"]["display_name"] for a in work.get("authorships", [])][:5]) +
                           ("..." if len(work.get("authorships", [])) > 5 else ""),
                "DOI": work.get("doi", "No DOI"),
                "Topics": ", ".join([c["display_name"] for c in work.get("concepts", [])]) or "No topics"
            }
            data.append(entry)
        except Exception as e:
            st.warning(f"Skipping a record due to error: {e}")
    return pd.DataFrame(data)

# Main app logic
def main():
    st.title("SUNY Downstate Publications Dashboard (200 Most Recent)")
    st.caption("Data from OpenAlex API (limited to 200 works)")

    # Load and process
    with st.spinner("Loading up to 200 recent publications..."):
        publications = get_downstate_publications_limited()
    df = process_data(publications)

    if df.empty:
        st.warning("No publication data found.")
        return

    # Sidebar year filter
    st.sidebar.header("Filters")
    min_year = int(df["Year"].min())
    max_year = int(df["Year"].max())
    year_range = st.sidebar.slider(
        "Publication Year", min_value=min_year, max_value=max_year, value=(min_year, max_year)
    )
    filtered_df = df[(df["Year"] >= year_range[0]) & (df["Year"] <= year_range[1])]

    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Publications", len(filtered_df))
    with col2:
        st.metric("Open Access Rate", f"{filtered_df['OA'].mean()*100:.1f}%")
    with col3:
        st.metric("Avg Citations", filtered_df["Citations"].mean().round(1))

    # Visual tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Trends", "Topics", "Authors", "Citations"])

    with tab1:
        trend_data = filtered_df.groupby("Year").size().reset_index(name="Count")
        fig = px.line(trend_data, x="Year", y="Count", title="Publication Trends")
        st.plotly_chart(fig)

    with tab2:
        topics = filtered_df["Topics"].str.split(", ").explode()
        top_topics = topics.value_counts().nlargest(10).reset_index()
        top_topics.columns = ["Topic", "Count"]
        fig = px.bar(top_topics, x="Topic", y="Count", title="Top Research Topics")
        st.plotly_chart(fig)

    with tab3:
        authors = filtered_df["Authors"].str.split(", ").explode()
        top_authors = authors.value_counts().nlargest(10).reset_index()
        top_authors.columns = ["Author", "Count"]
        fig = px.bar(top_authors, x="Author", y="Count", title="Most Prolific Authors")
        st.plotly_chart(fig)

    with tab4:
        fig = px.scatter(filtered_df, x="Year", y="Citations",
                         color="Citations", size="Citations",
                         title="Citation Distribution Over Time")
        st.plotly_chart(fig)

    # Data table and download
    st.subheader("Publication Details")
    st.dataframe(filtered_df, use_container_width=True)

    csv = filtered_df.to_csv(index=False)
    st.download_button("Download CSV", csv, "downstate_publications.csv", "text/csv")

if __name__ == "__main__":
    main()
