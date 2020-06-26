# Imports
import os
import pandas as pd
import plotly.graph_objects as go
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import json
from dotenv import load_dotenv
from filelock import FileLock

# Load environment variables
load_dotenv()
STYLE = os.getenv('STYLE')
FOLDER = os.getenv('FOLDER')
STRATEGY = os.getenv('STRATEGY')
INFO = os.getenv('INFO')

# Dash app
app = dash.Dash(__name__)
app.layout = html.Div(
    html.Div([
        dcc.Graph(id='live-update-graph', style={"height": "98vh"}),
        dcc.Interval(
            id='interval-component',
            interval=2000,
            n_intervals=10
        )
    ], style={"height": "100%"}), style={"height": "100%"}
)


# Callback
@app.callback(Output('live-update-graph', 'figure'),
              [Input('interval-component', 'n_intervals')])
def update_graph_live(n):
    # Read data
    df = None
    lock = FileLock(os.path.join(FOLDER, STRATEGY) + '.lock')
    with lock:
        df = pd.read_csv(os.path.join(FOLDER, STRATEGY))
    # Read info
    content = ""
    with open(INFO, 'r') as f:
        content = f.read()
    info = json.loads(content)
    # Read style
    content = ""
    with open(STYLE, 'r') as f:
        content = f.read()
    style = json.loads(content)
    # Create Chart
    fig = go.Figure(layout=go.Layout(title=info.get("asset", "BTCUSDT") + " on " + info.get("interval", "5m") + " timeframe", template="plotly_dark"))
    # Candlesticks
    # Bullish
    df_bullish = df[df["Score"] > 0]
    fig.add_trace(go.Candlestick(x=df_bullish["Date"],
                                 open=df_bullish["Open"],
                                 high=df_bullish["High"],
                                 low=df_bullish["Low"],
                                 close=df_bullish["Close"],
                                 increasing_line_color=style["candlesticks"]["bullish"]["increasing_line_color"],
                                 decreasing_line_color=style["candlesticks"]["bullish"]["decreasing_line_color"],
                                 increasing_fillcolor=style["candlesticks"]["bullish"]["increasing_fillcolor"],
                                 decreasing_fillcolor=style["candlesticks"]["bullish"]["decreasing_fillcolor"],
                                 name="Bullish"))

    # Neutral
    df_neutral = df[df["Score"] == 0]
    fig.add_trace(go.Candlestick(x=df_neutral["Date"],
                                 open=df_neutral["Open"],
                                 high=df_neutral["High"],
                                 low=df_neutral["Low"],
                                 close=df_neutral["Close"],
                                 increasing_line_color=style["candlesticks"]["neutral"]["increasing_line_color"],
                                 decreasing_line_color=style["candlesticks"]["neutral"]["decreasing_line_color"],
                                 increasing_fillcolor=style["candlesticks"]["neutral"]["increasing_fillcolor"],
                                 decreasing_fillcolor=style["candlesticks"]["neutral"]["decreasing_fillcolor"],
                                 name="Neutral"))

    # Bearish
    df_bearish = df[df["Score"] < 0]
    fig.add_trace(go.Candlestick(x=df_bearish["Date"],
                                 open=df_bearish["Open"],
                                 high=df_bearish["High"],
                                 low=df_bearish["Low"],
                                 close=df_bearish["Close"],
                                 increasing_line_color=style["candlesticks"]["bearish"]["increasing_line_color"],
                                 decreasing_line_color=style["candlesticks"]["bearish"]["decreasing_line_color"],
                                 increasing_fillcolor=style["candlesticks"]["bearish"]["increasing_fillcolor"],
                                 decreasing_fillcolor=style["candlesticks"]["bearish"]["decreasing_fillcolor"],
                                 name="Bearish"))

    for trace in style['traces']:
        fig.add_trace(go.Scatter(x=df["Date"],
                                 y=df[trace['data']],
                                 line_color=trace['color'],
                                 name=trace['name'], visible='legendonly'))

    padding = 0.0025
    length = 120
    left = 5
    xrange = [df["Date"].iloc[max(-length, -len(df))], (pd.to_datetime(df["Date"].iloc[-1]) + left * (
                pd.to_datetime(df["Date"].iloc[-1]) - pd.to_datetime(df["Date"].iloc[-2])))]
    yrange = [df.tail(length)["Low"].min() * (1 - padding), df.tail(length)["High"].max() * (1 + padding)]
    fig.update_layout(
        xaxis_rangeslider_visible=False,
        xaxis=dict(range=xrange),
        yaxis=dict(range=yrange),
        uirevision='False')
    return fig


# Main
if __name__ == '__main__':
    app.run_server(debug=True)
