from dashboard.app import app
from dashboard.app import result


if __name__ == '__main__':
    print(result.columns)
    app.run_server(debug=True)
