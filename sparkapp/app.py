import json
import os
import subprocess
import xmlrpc.server


class SparkApp:
    def products(self):

        os.environ["SPARK_APPLICATION_PYTHON_LOCATION"] = "/app/products.py"
        os.environ["SPARK_SUBMIT_ARGS"] = "--driver-class-path /app/mysql-connector-j-8.0.33.jar --jars /app/mysql-connector-j-8.0.33.jar"

        subprocess.run(["/template.sh"])

        with open("/app/results.json", "r") as file:
            results = [
                json.loads(row)
                for row in file
            ]

        os.remove("/app/results.json")
        return {"statistics": results}

    def categories(self):

        os.environ["SPARK_APPLICATION_PYTHON_LOCATION"] = "/app/categories.py"
        os.environ["SPARK_SUBMIT_ARGS"] = "--driver-class-path /app/mysql-connector-j-8.0.33.jar --jars /app/mysql-connector-j-8.0.33.jar"

        subprocess.run(["/template.sh"])

        with open("/app/results.json", "r") as file:
            results = [row.strip() for row in file]

        os.remove("/app/results.json")
        return {"statistics": results}


server = xmlrpc.server.SimpleXMLRPCServer(("0.0.0.0", 8000))
server.register_instance(SparkApp())
server.serve_forever()