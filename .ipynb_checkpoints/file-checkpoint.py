import subprocess

# Check Java version
result = subprocess.run(['java', '-version'], capture_output=True, text=True)
print(result.stderr)

# Check PySpark version
import pyspark
print("PySpark version:", pyspark.__version__)
