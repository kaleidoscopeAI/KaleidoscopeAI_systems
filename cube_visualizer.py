import plotly.graph_objects as go
import pandas as pd
import os

def generate_enhanced_cube(supernode_data: pd.DataFrame) -> str:
    """
    Generates an enhanced 3D visualization with node-link relationships.
    Nodes are color-coded by average correlation, and sample links are drawn.
    
    Args:
        supernode_data (pd.DataFrame): DataFrame with columns 'node_index' and 'avg_corr'
    
    Returns:
        str: Filename of the generated HTML visualization.
    """
    if supernode_data.empty:
        return ""
    
    supernode_data["X"] = supernode_data.index
    supernode_data["Y"] = supernode_data["avg_corr"]
    supernode_data["Z"] = supernode_data["avg_corr"] * 0.5

    # Create node trace
    node_trace = go.Scatter3d(
        x=supernode_data["X"],
        y=supernode_data["Y"],
        z=supernode_data["Z"],
        mode='markers',
        marker=dict(
            size=8,
            color=supernode_data["avg_corr"],
            colorscale='Viridis',
            opacity=0.8
        ),
        text=supernode_data["node_index"].astype(str),
        name='SuperNodes'
    )

    # Create a sample link trace (for demonstration)
    link_trace = go.Scatter3d(
        x=[supernode_data["X"].iloc[0], supernode_data["X"].iloc[-1]],
        y=[supernode_data["Y"].iloc[0], supernode_data["Y"].iloc[-1]],
        z=[supernode_data["Z"].iloc[0], supernode_data["Z"].iloc[-1]],
        mode='lines',
        line=dict(color='gray', width=2),
        name='Relationships'
    )

    fig = go.Figure(data=[node_trace, link_trace])
    fig.update_layout(
        title='Enhanced 3D Cube with Node-Link Relationships',
        scene=dict(
            xaxis_title='Node Index',
            yaxis_title='Average Correlation',
            zaxis_title='Scaled Correlation'
        )
    )
    
    filename = f"enhanced_cube_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.html"
    vis_dir = os.environ.get("VISUALIZATION_DIR")
    filepath = os.path.join(vis_dir, filename)
    fig.write_html(filepath)
    return filename

# Optional: S3 upload function for visualizations
import boto3
def upload_to_s3(filename):
    s3 = boto3.client("s3")
    bucket = "kaleidoscope-visuals"
    filepath = os.path.join(os.environ.get("VISUALIZATION_DIR"), filename)
    s3.upload_file(filepath, bucket, filename)
    url = s3.generate_presigned_url("get_object", Params={"Bucket": bucket, "Key": filename}, ExpiresIn=3600)
    return url

