import pyspark.sql.functions as F
from pyspark.sql import SparkSession
import os

PRODUCTION = True if "PRODUCTION" in os.environ else False
DATABASE_IP = os.environ["DATABASE_URL"] if "DATABASE_URL" in os.environ else "localhost"

builder = SparkSession.builder.appName("PySpark Database example")

if not PRODUCTION:
    builder = builder.master("local[*]") \
        .config(
            "spark.driver.extraClassPath",
            "mysql-connector-j-8.0.33.jar"
        )

spark = builder.getOrCreate()

productDataFrame = spark.read \
    .format("jdbc") \
    .option("driver", "com.mysql.cj.jdbc.Driver") \
    .option("url", f"jdbc:mysql://{DATABASE_IP}:3306/store") \
    .option("dbtable", "store.product") \
    .option("user", "root") \
    .option("password", "root") \
    .load()

deliveryDataFrame = spark.read \
    .format("jdbc") \
    .option("driver", "com.mysql.cj.jdbc.Driver") \
    .option("url", f"jdbc:mysql://{DATABASE_IP}:3306/store") \
    .option("dbtable", "store.delivery") \
    .option("user", "root") \
    .option("password", "root") \
    .load()

deliveryProductDataFrame = spark.read \
    .format("jdbc") \
    .option("driver", "com.mysql.cj.jdbc.Driver") \
    .option("url", f"jdbc:mysql://{DATABASE_IP}:3306/store") \
    .option("dbtable", "store.deliveryproduct") \
    .option("user", "root") \
    .option("password", "root") \
    .load()

joinedDataFrame = productDataFrame.join(
    deliveryProductDataFrame,
    productDataFrame["id"] == deliveryProductDataFrame["productId"],
    "inner"
).join(
    deliveryDataFrame,
    deliveryDataFrame["id"] == deliveryProductDataFrame["deliveryId"],
    "inner"
)

result = joinedDataFrame.groupBy(productDataFrame["name"]) \
    .agg(
        F.sum(F.when(deliveryDataFrame["status"] == "COMPLETE", deliveryProductDataFrame["quantity"]).otherwise(0)).alias("sold"),
        F.sum(F.when(deliveryDataFrame["status"] != "COMPLETE", deliveryProductDataFrame["quantity"]).otherwise(0)).alias("waiting")
    ).toJSON().collect()

# statistics = []
# for row in result:
#     name = row["name"]
#     sold = row["sold"]
#     waiting = row["waiting"]
#     statistics.append({"name": name, "sold": sold, "waiting": waiting})


with open("/app/results.json", "w") as file:
    for row in result:
        file.write(row + '\n')

spark.stop()