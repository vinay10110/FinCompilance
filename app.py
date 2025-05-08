from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Test route
@app.route('/api/test', methods=['GET'])
def test_route():
    return jsonify({"message": "Backend is working!"})

# Upload document route
@app.route('/api/upload', methods=['POST'])
def upload_document():
    # Mock response for now
    return jsonify({
        "status": "success",
        "message": "Document received successfully",
        "documentId": "123"
    })

# Verify compliance route
@app.route('/api/verify-compliance', methods=['POST'])
def verify_compliance():
    # Mock response for now
    return jsonify({
        "status": "success",
        "results": [
            {
                "requirement": "Data Privacy",
                "status": "Compliant",
                "details": "All necessary privacy measures are in place"
            },
            {
                "requirement": "Security Standards",
                "status": "Needs Review",
                "details": "Additional security measures may be required"
            }
        ]
    })

# Get implementation plan route
@app.route('/api/implementation-plan', methods=['GET'])
def get_implementation_plan():
    # Mock response for now
    return jsonify({
        "status": "success",
        "plan": [
            {
                "step": 1,
                "title": "Initial Assessment",
                "description": "Review current compliance status",
                "timeframe": "1-2 weeks"
            },
            {
                "step": 2,
                "title": "Gap Analysis",
                "description": "Identify areas needing improvement",
                "timeframe": "2-3 weeks"
            }
        ]
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
