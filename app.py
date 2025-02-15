import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO
from flask_cors import CORS
import logging
from core.chatbot import AIChatbot
from core.membrane import DataMembrane
from core.pipeline_manager import PipelineManager
from core.cube_visualizer import generate_wireframe_cube
from core.godaddy_manager import GoDaddyManager, DNSRecord

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")
logger = logging.getLogger(__name__)

# Initialize components
chatbot = AIChatbot()
membrane = DataMembrane()
pipeline_mgr = PipelineManager()

# DNS Configuration
GODADDY_KEY = os.getenv("GODADDY_KEY")
GODADDY_SECRET = os.getenv("GODADDY_SECRET")
DOMAIN = "artificialthinker.com"
dns_manager = GoDaddyManager(GODADDY_KEY, GODADDY_SECRET)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def handle_upload():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
            
        file_path = os.path.join("data", file.filename)
        file.save(file_path)
        
        # Process data
        data = membrane.ingest_data(file_path)
        pipeline_mgr.run_full_pipeline(data)
        
        # Update DNS with new ALB endpoint
        alb_dns = "kaleidoscope.artificialthinker.com"  # Replace with actual ALB DNS
        dns_manager.update_dns(DOMAIN, [
            DNSRecord(type="A", name="@", value=alb_dns),
            DNSRecord(type="CNAME", name="www", value=DOMAIN)
        ])
        
        return jsonify({
            "message": "File processed successfully",
            "visualization": generate_wireframe_cube(pipeline_mgr.supernodes[-1].dna)
        })
        
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        return jsonify({"error": str(e)}), 500

@socketio.on("message")
def handle_message(query):
    try:
        response = chatbot.respond(query)
        socketio.emit("response", {"type": "ai", "content": response})
        
        # Update visualization
        if pipeline_mgr.supernodes:
            cube_file = generate_wireframe_cube(pipeline_mgr.supernodes[-1].dna)
            socketio.emit("visualization", {"url": f"/visualizations/{cube_file}"})
            
    except Exception as e:
        logger.error(f"Message handling error: {str(e)}")
        socketio.emit("response", {"type": "error", "content": str(e)})

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=80, debug=True)
