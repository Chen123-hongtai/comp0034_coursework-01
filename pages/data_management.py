"""Handle data file uploads and provide a tabular preview interface."""

from __future__ import annotations

import base64
import io

import dash
from dash import Input, Output, State, callback, dash_table, dcc, html
import dash_bootstrap_components as dbc
import pandas as pd

from services.api_client import ApiUnavailableError, create_observation


dash.register_page(__name__, name="Data Management")


layout = html.Div(
    [
        dcc.Store(id="datamanager-preview-records"),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H2("Data Management Console", className="mb-2"),
                        html.P(
                            "Upload new tourism data files (CSV or Excel) to update the database. "
                            "The system previews rows and can commit observation records to the API.",
                            className="text-muted mb-4",
                        ),
                    ]
                )
            ]
        ),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H5("Upload New Dataset", className="card-title mb-3"),
                                dcc.Upload(
                                    id="datamanager-upload-data",
                                    children=html.Div(["Drag and Drop or ", html.A("Select Files", className="text-primary font-weight-bold")]),
                                    style={
                                        "width": "100%",
                                        "height": "120px",
                                        "lineHeight": "120px",
                                        "borderWidth": "2px",
                                        "borderStyle": "dashed",
                                        "borderRadius": "10px",
                                        "textAlign": "center",
                                        "margin": "10px 0",
                                        "backgroundColor": "#f8f9fa",
                                        "cursor": "pointer",
                                    },
                                    multiple=False,
                                ),
                                html.Div(id="datamanager-upload-status", className="mt-3"),
                            ]
                        ),
                        className="shadow-sm border-0 mb-4",
                    ),
                    width=12,
                )
            ]
        ),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H5("Data Preview", className="card-title mb-3"),
                                html.Div(id="datamanager-output-data-upload"),
                                dbc.Button(
                                    "Commit to Database",
                                    id="datamanager-commit-btn",
                                    color="success",
                                    className="mt-3",
                                    n_clicks=0,
                                ),
                                html.Div(id="datamanager-commit-status", className="mt-2"),
                            ]
                        ),
                        className="shadow-sm border-0",
                    ),
                    width=12,
                )
            ]
        ),
    ]
)


def _parse_uploaded_dataframe(contents: str, filename: str) -> pd.DataFrame:
    _, content_string = contents.split(",")
    decoded = base64.b64decode(content_string)

    if "csv" in filename.lower():
        return pd.read_csv(io.StringIO(decoded.decode("utf-8")))
    if "xls" in filename.lower():
        return pd.read_excel(io.BytesIO(decoded))

    raise ValueError("Unsupported file format. Please upload a CSV or Excel file.")


def _preview_table(df: pd.DataFrame, filename: str) -> html.Div:
    return html.Div(
        [
            html.H6(f"File: {filename} (Previewing first 5 rows)"),
            dash_table.DataTable(
                data=df.head().to_dict("records"),
                columns=[{"name": i, "id": i} for i in df.columns],
                style_table={"overflowX": "auto"},
                style_cell={"textAlign": "left", "padding": "10px", "fontFamily": "sans-serif"},
                style_header={"backgroundColor": "#2C3E50", "color": "white", "fontWeight": "bold"},
            ),
        ]
    )


@callback(
    [
        Output("datamanager-output-data-upload", "children"),
        Output("datamanager-upload-status", "children"),
        Output("datamanager-preview-records", "data"),
    ],
    [Input("datamanager-upload-data", "contents")],
    [State("datamanager-upload-data", "filename")],
)
def update_output(contents, filename):
    if contents is None:
        return html.Div("No data uploaded yet. Please use the drag-and-drop box above."), "", None

    try:
        df = _parse_uploaded_dataframe(contents, filename)
        preview_table = _preview_table(df, filename)
        status_msg = dbc.Alert(f"Successfully loaded {filename} into memory.", color="success", duration=4000)
        return preview_table, status_msg, df.to_dict("records")
    except Exception as exc:
        return (
            html.Div([dbc.Alert(f"There was an error processing this file: {exc}", color="danger")]),
            dbc.Alert("Upload failed.", color="danger"),
            None,
        )


@callback(
    Output("datamanager-commit-status", "children"),
    [Input("datamanager-commit-btn", "n_clicks")],
    [State("datamanager-preview-records", "data")],
    prevent_initial_call=True,
)
def commit_data_to_backend(n_clicks: int, preview_records):
    if not preview_records:
        return dbc.Alert("No parsed data to commit.", color="warning")

    required_columns = {"series_id", "month", "date", "value"}
    if not required_columns.issubset(set(preview_records[0].keys())):
        return dbc.Alert(
            "Commit skipped: uploaded file must include columns series_id, month, date, value.",
            color="warning",
        )

    success_count = 0
    for row in preview_records:
        try:
            payload = {
                "series_id": int(row["series_id"]),
                "month": str(row["month"]),
                "date": pd.to_datetime(row["date"]).to_pydatetime().isoformat(),
                "value": float(row["value"]),
            }
            create_observation(payload)
            success_count += 1
        except (ValueError, TypeError):
            continue
        except ApiUnavailableError:
            return dbc.Alert("Backend API is not available. Start FastAPI and try again.", color="danger")

    return dbc.Alert(f"Committed {success_count} rows to the backend API.", color="success")