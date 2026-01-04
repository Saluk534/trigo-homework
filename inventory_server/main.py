from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/inventory', methods=['GET'])
def json_example():
    sensors = [f"sensor_{i}" for i in range(100)]
    return jsonify(sensors)  

if __name__ == '__main__':
    app.run(debug=True, port=1337, host="0.0.0.0")
