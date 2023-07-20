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

categoryDataFrame = spark.read \
    .format("jdbc") \
    .option("driver", "com.mysql.cj.jdbc.Driver") \
    .option("url", f"jdbc:mysql://{DATABASE_IP}:3306/store") \
    .option("dbtable", "store.category") \
    .option("user", "root") \
    .option("password", "root") \
    .load()

productCategoryDataFrame = spark.read \
    .format("jdbc") \
    .option("driver", "com.mysql.cj.jdbc.Driver") \
    .option("url", f"jdbc:mysql://{DATABASE_IP}:3306/store") \
    .option("dbtable", "store.productcategory") \
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

deliveryDataFrame = spark.read \
    .format("jdbc") \
    .option("driver", "com.mysql.cj.jdbc.Driver") \
    .option("url", f"jdbc:mysql://{DATABASE_IP}:3306/store") \
    .option("dbtable", "store.delivery") \
    .option("user", "root") \
    .option("password", "root") \
    .load()

joinedDataFrame = productCategoryDataFrame.join(
    productDataFrame,
    productDataFrame["id"] == productCategoryDataFrame["productId"],
    "left"
).join(
    categoryDataFrame,
    categoryDataFrame["id"] == productCategoryDataFrame["categoryId"],
    "left"
).join(
    deliveryProductDataFrame,
    deliveryProductDataFrame["productId"] == productDataFrame["id"],
    "left"
).join(
    deliveryDataFrame,
    deliveryDataFrame["id"] == deliveryProductDataFrame["deliveryId"],
    "left"
)

result = joinedDataFrame.groupBy(categoryDataFrame["name"]) \
    .agg(F.sum(F.when(deliveryDataFrame["status"] == "COMPLETE", deliveryProductDataFrame["quantity"]).otherwise(0)).alias("delivered_copies")) \
    .orderBy(F.desc("delivered_copies"), F.asc(categoryDataFrame["name"])) \
    .collect()

statistics = [row["name"] for row in result]

with open("/app/results.json", "w") as file:
    for row in statistics:
        file.write(row + '\n')

spark.stop()