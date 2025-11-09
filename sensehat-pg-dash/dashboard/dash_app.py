import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd, psycopg2, plotly.express as px

app = dash.Dash(__name__)

def get_data():
    conn= psycopg2.connect(host="10.234.143.103",   # Pi’s IP
        database="iiot_lab",
        user="group2",
        password="mfg598")

    df = pd.read_sql("SELECT * FROM sensor_data ORDER BY timestamp DESC LIMIT 300", conn)
    conn.close()
    return df

app.layout = html.Div([
    html.H3("IIoT Sensor Dashboard"),
    dcc.Interval(id='tick', interval=5000, n_intervals=0),
    dcc.Graph(id='temp'), dcc.Graph(id='hum'), dcc.Graph(id='press'), dcc.Graph(id='pitch'), dcc.Graph(id='roll'), dcc.Graph(id='yaw')
])

@app.callback(
    [Output('temp','figure'), Output('hum','figure'), Output('press','figure'), Output('pitch','figure'), Output('roll','figure'), Output('yaw','figure')],
    Input('tick','n_intervals')
)
def update(_):
    df = get_data()
    f1 = px.line(df, x='timestamp', y='temperature', title='Temperature')
    f2 = px.line(df, x='timestamp', y='humidity',    title='Humidity')
    f3 = px.line(df, x='timestamp', y='pressure',    title='Pressure')
    f4 = px.line(df, x='timestamp', y='pitch',    title='Pitch')
    f5 = px.line(df, x='timestamp', y='roll',    title='Roll')
    f6 = px.line(df, x='timestamp', y='yaw',    title='Yaw')
    return f1, f2, f3, f4, f5, f6

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050)
