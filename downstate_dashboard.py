import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# Helper function to get all SUNY Downstate publications using cursor paging
def get_all_downstate_publications():
    OPENALEX_API = "https://api.openalex.org/works"
    DOWNSTATE_ID = "I97018004"  # Verify institution ID via OpenAlex
    all_results = []

    params = {
        "filter": f"institutions.id:{DOWNSTATE_ID}",
        "per-page": 200,
        "cursor": "*",
        "mailto": "your.email@example.com"  # Replace with your email!
    }

    while True:
        response = requests.get(OPENALEX_API, params=params)
        if response.status_code != 200:
            st.error("Failed to fetch data from OpenAlex")
            break
        data = response.json()
        all_results.extend(data["results"])
        next_cursor = data["meta"].get("next_cursor")
        if not next_cursor:
            break
        params["cursor"] = next_cursor

    return all_results

# Process data into DataFrame
def process_data(publications):
    data = []
    for work in publications:
        try:
            entry = {
                "Title": work.get("title", "No title"),
                "Year": work.get("publication_year"),
                "Citations": work.get("cited_by_count", 0),
                "OA": work.get("open_access", {}).get("is_oa", False),
                "Type": work.get("type", "unknown"),
                "Authors": ", ".join([a["author"]["display_name"] for a in work["authorships"]]) if work.get("authorships") else "Unknown",
                "DOI": work.get("doi", "No DOI"),
                "Topics": ", ".join([c["display_name"] for c in work["concepts"]]) if work.get("concepts") else "No topics",
                # "Institutions": ", ".join([i["institution"]["display_name"] for i in work["authorships"] if "institution" in i]) if work.get("authorships") else "Unknown",
                # "Country": "US"  # Placeholder: You would need to extract real country data from OpenAlex if available
            }
            data.append(entry)
        except Exception as e:
            st.warning(f"Skipping a record due to error: {e}")
    return pd.DataFrame(data)

# Main dashboard function
def main():
    st.title("SUNY Downstate Publications Dashboard")
    st.caption("Data from OpenAlex API")

    # Load data
    publications = get_all_downstate_publications()
    df = process_data(publications)

    # Filters sidebar
    st.sidebar.header("Filters")
    min_year = int(df["Year"].min()) if not df.empty else 2000
    max_year = int(df["Year"].max()) if not df.empty else 2025
    year_range = st.sidebar.slider(
        "Publication Year",
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year)
    )
    filtered_df = df[(df["Year"] >= year_range[0]) & (df["Year"] <= year_range[1])]

    # Key metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Publications", len(filtered_df))
    with col2:
        st.metric("Open Access Rate", f"{filtered_df['OA'].mean()*100:.1f}%")
    with col3:
        st.metric("Avg Citations", filtered_df["Citations"].mean().round(1))

    # Visualization tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Trends", "Topics", "Authors", "Citations"])

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

    with tab4:
        fig = px.scatter(filtered_df, x="Year", y="Citations",
                        color="Citations", size="Citations",
                        title="Citation Distribution Over Time")
        st.plotly_chart(fig)

    # Advanced: Collaboration country map (commented out—requires real country data)
    # if "Country" in filtered_df.columns:
    #     st.subheader("Collaboration Countries")
    #     country_counts = filtered_df["Country"].value_counts().reset_index()
    #     country_counts.columns = ["Country", "Count"]
    #     fig = px.choropleth(country_counts,
    #                        locations="Country",
    #                        locationmode="country names",
    #                        color="Count",
    #                        title="Collaboration Countries")
    #     st.plotly_chart(fig)
    # else:
    #     st.info("No country data available for collaboration mapping.")

    # Data table
    st.subheader("Publication Details")
    st.dataframe(filtered_df, use_container_width=True)

if __name__ == "__main__":
    main()
