# 🚕 NYC Taxi Rides Analysis — PySpark Batch Processing

A big data analysis project using **Apache Spark** to analyze New York City taxi ride data, computing key utilization statistics across NYC boroughs.

---

## 📋 Table of Contents

- [Project Overview](#project-overview)
- [Dataset](#dataset)
- [Queries](#queries)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Pipeline Overview](#pipeline-overview)
- [Key Implementation Notes](#Key-Implementation-Notes)
- [Results](#results)

---

## 📌 Project Overview

**Utilization** is the fraction of time a cab is on the road and occupied by one or more passengers. One factor that impacts utilization is the passenger's destination:

- A cab dropping off near **Union Square at midday** is likely to find its next fare in just a minute or two.
- A cab dropping someone off at **2AM on Staten Island** may have to drive all the way back to Manhattan before finding its next fare.

This project computes utilization-related statistics by analyzing taxi trips per NYC borough.

---

## 📂 Dataset

### Taxi Rides Dataset

Each row represents a single taxi ride in CSV format with the following fields:

| Column | Description |
|---|---|
| `medallion` | Hashed unique ID for the cab |
| `hack_license` | Hashed driver license ID |
| `pickup_datetime` | Trip start timestamp |
| `dropoff_datetime` | Trip end timestamp |
| `pickup_longitude` | Pickup location longitude |
| `pickup_latitude` | Pickup location latitude |
| `dropoff_longitude` | Dropoff location longitude |
| `dropoff_latitude` | Dropoff location latitude |
| `passenger_count` | Number of passengers |
| `trip_distance` | Distance of the trip |

### Borough Boundaries Dataset
A **GeoJSON** file specifying the boundaries of each NYC borough:
- Manhattan
- Brooklyn
- Queens
- Bronx
- Staten Island

---

## 🎯 Queries

### Query 1 — Average Idle Time per Destination Borough
> How long does a taxi wait for its next fare after dropping off a passenger, grouped by destination borough?

### Query 2 — Intra-Borough Trips
> How many trips started and ended within the same borough?

### Query 3 — Inter-Borough Trips
> How many trips started in one borough and ended in another?

---


## 🛠 Tech Stack

| Tool | Version | Purpose |
|---|---|---|
| Python | 3.9 | Programming language |
| Apache Spark (PySpark) | 3.3.0 | Distributed data processing |
| Java (OpenJDK Temurin) | 11 | Spark runtime |
| Shapely | latest | Geospatial point-in-polygon |
| Jupyter Notebook | latest | Development environment |

---

## 📁 Project Structure

```
nyc-taxi-analysis/
│
├── data/
│   ├── taxi_rides.csv          # Raw taxi rides dataset (sample)
│   └── nyc-boroughs.geojson    # NYC borough boundaries
│
├── notebooks/
│   └── nyc_taxi_analysis.ipynb # Main analysis notebook
│
│
└── README.md
```


## 🔄 Pipeline Overview

```
Raw CSV                        GeoJSON
(taxi rides)                (borough boundaries)
     │                              │
     ▼                              ▼
Read with Spark            Load with json module
     │                              │
     │                     Build Shapely polygons
     │                              │
     │                     Sort by borough code + area
     │                              │
     │                     Broadcast to workers
     │                              │
     ▼                              ▼
Map lat/lon ──────────────► get_borough UDF
     │                     (point-in-polygon check)
     ▼
Add pickup_borough + dropoff_borough columns
     │
     ▼
Drop Unknown boroughs
     │
     ▼
Compute Duration = dropoff_ts - pickup_ts
     │
     ▼
Clean dirty data:
  - duration <= 0     → drop
  - duration > 4 hrs  → drop
     │
     ▼
Window per taxi (medallion):
  - partitionBy(medallion) → shuffle
  - orderBy(pickup_datetime) → sort
  - lag(dropoff_datetime) → prev trip dropoff
     │
     ▼
Compute idle_time = pickup[n] - dropoff[n-1]
     │
     ▼
Filter valid idle times:
  - idle > 0
  - idle <= 4 hours (same session)
     │
     ├──────────────────────────────────────────┐
     ▼                                          ▼
Query 1:                                   Query 2 & 3:
groupBy(medallion, dropoff_borough)        filter pickup == dropoff borough
→ sum(idle_time)                           → count  (Query 2)
→ groupBy(dropoff_borough)                 filter pickup != dropoff borough
→ avg(idle_time)                           → count  (Query 3)
```

---

## 📝 Key Implementation Notes

- **GeoJSON broadcast**: Borough boundary data is small so it is broadcast to all Spark workers to avoid shuffling
- **Shapely UDF**: Custom UDF uses point-in-polygon check to map coordinates to borough names
- **Window operator**: Used to compare consecutive trips per driver to compute idle time
- **4-hour threshold**: Gaps larger than 4 hours between trips are treated as new work sessions, not idle time
- **Data cleaning**: Records with negative duration or duration over 4 hours are dropped as outliers

---


## 📊 Results

### Query 1 — Average Idle Time per Destination Borough

```
+--------------------+---------------+------------------+
|           medallion|dropoff_borough|     avg_idle_mins|
+--------------------+---------------+------------------+
|000318C2E3E638158...|      Manhattan|20.636363636363637|
|002B4CFC5B8920A87...|      Manhattan| 34.46153846153846|
|002B4CFC5B8920A87...|         Queens|              10.0|
|002E3B405B6ABEA23...|      Manhattan|            42.375|
|002E3B405B6ABEA23...|         Queens|              91.0|
|0030AD2648D81EE87...|       Brooklyn|              21.0|
|0035520A854E4F276...|       Brooklyn|             100.0|
|0035520A854E4F276...|      Manhattan|25.363636363636363|
|0036961468659D0BF...|      Manhattan|29.764705882352942|
|003889E315BFDD985...|      Manhattan|             28.75|
|0038EF45118925A51...|      Manhattan|              22.0|
|003D87DB553C6F00F...|      Manhattan|16.541666666666668|
|003EEA559FA618008...|      Manhattan|             42.55|
|003EEA559FA618008...|         Queens|              14.0|
|0053334C798EC6C8E...|      Manhattan|            61.125|
|0053334C798EC6C8E...|         Queens|              12.0|
|005DED7D6E6C45441...|      Manhattan|              30.5|
|005DED7D6E6C45441...|         Queens|              20.5|
|005F00B38F46E2100...|      Manhattan|41.083333333333336|
|005F00B38F46E2100...|         Queens|              13.0|
+--------------------+---------------+------------------+
only showing 20 rows
```

### Query 2 — Intra-Borough Trips

```
+--------------+---------+
|pickup_borough|num_trips|
+--------------+---------+
|     Manhattan|    83464|
|        Queens|     1369|
|      Brooklyn|     1062|
|         Bronx|       49|
| Staten Island|        1|
+--------------+---------+
```

### Query 3 — Inter-Borough Trips

```
+--------------+---------+
|pickup_borough|num_trips|
+--------------+---------+
|     Manhattan|     6119|
|        Queens|     4396|
|      Brooklyn|      888|
|         Bronx|       27|
| Staten Island|        1|
+--------------+---------+
```
