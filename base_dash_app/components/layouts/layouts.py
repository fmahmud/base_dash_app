from dash import html


def create_split_html_div(left_child, right_child, left_width=50):
    return [
        html.Div(
            children=left_child,
            style={
                "position": "relative", "float": "left", "width": f"calc({left_width}% - 15px)", "marginRight": "20px"
            }
        ),
        html.Div(
            children=right_child,
            style={
                "position": "relative", "float": "left", "width": f"calc({100 - left_width}% - 15px)"
            }
        ),
    ]