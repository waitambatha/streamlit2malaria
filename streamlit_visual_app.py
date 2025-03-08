import os
from dotenv import load_dotenv
from pyodk import Client
import streamlit as st
import pandas as pd
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt

# Load environment variables from .env file
load_dotenv()

# Retrieve the ODK Central URL and API token from environment variables
central_url = os.getenv("ODK_CENTRAL_URL", "https://your-odk-central-instance-url")
api_token = os.getenv("ODK_API_TOKEN", "your-api-token")

# Initialize the pyodk client
client = Client(base_url=central_url, token=api_token)

st.title("ODK Central Data Dashboard")

# Fetch the list of forms available on the ODK Central server
forms = client.get_forms()
if not forms:
    st.error("No forms found on the ODK Central server. Please check your connection and credentials.")
    st.stop()

# Create a dictionary for easy lookup; assuming each form has an 'xmlFormId'
form_options = {form['xmlFormId']: form for form in forms}
selected_form = st.selectbox("Select a Form", list(form_options.keys()))

if selected_form:
    form = form_options[selected_form]
    st.write(f"### Selected Form: {form.get('name', selected_form)}")

    # Retrieve submissions for the selected form using its xmlFormId
    submissions = client.get_submissions(form_id=selected_form)

    # Convert the submissions list (assumed to be a list of dicts) to a DataFrame
    df = pd.DataFrame(submissions)

    if df.empty:
        st.warning("No submissions available for this form.")
    else:
        # Data Preview & Sidebar Filters
        st.write("### Data Preview")
        st.dataframe(df.head())
        selected_columns = st.sidebar.multiselect("Select Columns to Display", df.columns.tolist(),
                                                  default=df.columns.tolist()[:5])
        st.write("### Dataset Preview")
        st.dataframe(df[selected_columns])

        # Display Summary Statistics
        st.write("### Data Summary Statistics")
        st.dataframe(df.describe().transpose())

        # Interactive Visualizations
        st.write("### Data Visualizations")

        # Bar Chart
        st.write("#### Bar Chart")
        x_axis_bar = st.selectbox("Select X-axis for Bar Chart", df.columns, key="bar_x")
        y_axis_bar = st.selectbox("Select Y-axis for Bar Chart", df.columns, key="bar_y")
        fig_bar = px.bar(df, x=x_axis_bar, y=y_axis_bar, title=f"Bar Chart: {x_axis_bar} vs {y_axis_bar}")
        st.plotly_chart(fig_bar)

        # Line Chart
        st.write("#### Line Chart")
        x_axis_line = st.selectbox("Select X-axis for Line Chart", df.columns, key="line_x")
        y_axis_line = st.selectbox("Select Y-axis for Line Chart", df.columns, key="line_y")
        fig_line = px.line(df, x=x_axis_line, y=y_axis_line, title=f"Line Chart: {x_axis_line} vs {y_axis_line}")
        st.plotly_chart(fig_line)

        # Donut Chart
        st.write("#### Donut Chart")
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        numerical_cols = df.select_dtypes(include=['number']).columns.tolist()
        if categorical_cols and numerical_cols:
            x_axis_donut = st.selectbox("Select Category for Donut Chart", categorical_cols, key="donut_x")
            y_axis_donut = st.selectbox("Select Values for Donut Chart", numerical_cols, key="donut_y")
            donut_data = df[[x_axis_donut, y_axis_donut]].copy()
            donut_data[y_axis_donut] = pd.to_numeric(donut_data[y_axis_donut], errors='coerce').fillna(0)
            fig_donut = px.pie(donut_data, names=x_axis_donut, values=y_axis_donut, hole=0.4,
                               title=f"Donut Chart: {x_axis_donut}")
            st.plotly_chart(fig_donut)
        else:
            st.warning("Insufficient categorical or numerical columns available for a donut chart.")

        # Heatmap of correlations
        st.write("#### Heatmap")
        selected_heatmap_cols = st.multiselect("Select Columns for Heatmap", numerical_cols, default=numerical_cols[:5])
        if len(selected_heatmap_cols) > 1:
            fig_heatmap = plt.figure(figsize=(10, 6))
            sns.heatmap(df[selected_heatmap_cols].corr(), annot=True, cmap="coolwarm", fmt=".2f")
            st.pyplot(fig_heatmap)
        else:
            st.warning("Select at least two numerical columns for the heatmap.")

        # Option to Download Data
        st.write("### Download Data")
        st.download_button("Download CSV", df.to_csv(index=False), "odk_data.csv", "text/csv")
