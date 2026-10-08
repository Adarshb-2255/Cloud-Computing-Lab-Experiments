import requests
import time
import csv
import subprocess
from concurrent.futures import ThreadPoolExecutor

URL = "http://localhost:5001/order"

WORKLOADS = [1, 2, 4, 8, 16]
REQUESTS_PER_WORKLOAD = 50
MONITOR_INTERVAL = 0.1


def send_request():
    start = time.perf_counter()

    try:
        response = requests.get(URL, timeout=10)
        elapsed = time.perf_counter() - start

        return response.status_code == 200, elapsed

    except Exception:
        elapsed = time.perf_counter() - start
        return False, elapsed


def get_docker_stats():
    command = [
        "docker", "stats", "--no-stream",
        "--format",
        "{{.Name}},{{.CPUPerc}},{{.MemUsage}}"
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True
    )

    stats = {}

    for line in result.stdout.strip().splitlines():

        parts = line.split(",")

        if len(parts) != 3:
            continue

        name = parts[0]
        cpu = parts[1].replace("%", "").strip()

        memory = parts[2].split("/")[0].strip()

        # Convert MiB/GiB to MiB
        if "GiB" in memory:
            memory_value = float(memory.replace("GiB", "")) * 1024
        elif "MiB" in memory:
            memory_value = float(memory.replace("MiB", ""))
        elif "KiB" in memory:
            memory_value = float(memory.replace("KiB", "")) / 1024
        else:
            memory_value = 0

        stats[name] = {
            "cpu": float(cpu),
            "memory": memory_value
        }

    return stats


results = []

print("\n==============================================")
print(" MICROservice WORKLOAD + RESOURCE TEST")
print("==============================================")

for concurrency in WORKLOADS:

    print("\n" + "=" * 55)
    print(f"W{WORKLOADS.index(concurrency) + 1} - "
          f"{concurrency} concurrent requests")
    print("=" * 55)

    resource_samples = []

    start_test = time.perf_counter()

    with ThreadPoolExecutor(max_workers=concurrency) as executor:

        futures = [
            executor.submit(send_request)
            for _ in range(REQUESTS_PER_WORKLOAD)
        ]

        while True:

            finished = sum(
                future.done() for future in futures
            )

            resource_samples.append(
                get_docker_stats()
            )

            if finished == REQUESTS_PER_WORKLOAD:
                break

            time.sleep(MONITOR_INTERVAL)

        request_results = [
            future.result()
            for future in futures
        ]

    total_time = time.perf_counter() - start_test

    successful = sum(
        success for success, _ in request_results
    )

    failed = REQUESTS_PER_WORKLOAD - successful

    response_times = [
        elapsed for _, elapsed in request_results
    ]

    average_response = (
        sum(response_times) /
        len(response_times)
    )

    throughput = successful / total_time

    # Calculate maximum CPU and memory observed
    service_data = {
        "order-service": {"cpu": 0, "memory": 0},
        "product-service": {"cpu": 0, "memory": 0},
        "user-service": {"cpu": 0, "memory": 0}
    }

    for sample in resource_samples:

        for service in service_data:

            if service in sample:

                service_data[service]["cpu"] = max(
                    service_data[service]["cpu"],
                    sample[service]["cpu"]
                )

                service_data[service]["memory"] = max(
                    service_data[service]["memory"],
                    sample[service]["memory"]
                )

    print(f"Requests              : {REQUESTS_PER_WORKLOAD}")
    print(f"Successful            : {successful}")
    print(f"Failed                : {failed}")
    print(f"Average Response Time : {average_response:.4f} seconds")
    print(f"Throughput            : {throughput:.2f} requests/sec")

    for service in service_data:

        print(
            f"{service:18} CPU: "
            f"{service_data[service]['cpu']:.2f}% | "
            f"Memory: "
            f"{service_data[service]['memory']:.2f} MiB"
        )

    results.append({
        "workload": f"W{WORKLOADS.index(concurrency) + 1}",
        "concurrency": concurrency,
        "response_time": round(average_response, 4),
        "throughput": round(throughput, 2),
        "successful": successful,
        "failed": failed,
        "order_cpu": round(
            service_data["order-service"]["cpu"], 2
        ),
        "order_memory": round(
            service_data["order-service"]["memory"], 2
        ),
        "product_cpu": round(
            service_data["product-service"]["cpu"], 2
        ),
        "product_memory": round(
            service_data["product-service"]["memory"], 2
        ),
        "user_cpu": round(
            service_data["user-service"]["cpu"], 2
        ),
        "user_memory": round(
            service_data["user-service"]["memory"], 2
        )
    })


# Save CSV
with open("final_results.csv", "w", newline="") as file:

    writer = csv.DictWriter(
        file,
        fieldnames=results[0].keys()
    )

    writer.writeheader()
    writer.writerows(results)


# Generate graphs
import matplotlib.pyplot as plt

concurrency = [
    row["concurrency"]
    for row in results
]

response_time = [
    row["response_time"]
    for row in results
]

throughput = [
    row["throughput"]
    for row in results
]

order_cpu = [
    row["order_cpu"]
    for row in results
]

product_cpu = [
    row["product_cpu"]
    for row in results
]

user_cpu = [
    row["user_cpu"]
    for row in results
]

order_memory = [
    row["order_memory"]
    for row in results
]

product_memory = [
    row["product_memory"]
    for row in results
]

user_memory = [
    row["user_memory"]
    for row in results
]


# Response time graph
plt.figure()
plt.plot(concurrency, response_time, marker="o")
plt.xlabel("Concurrent Requests")
plt.ylabel("Average Response Time (seconds)")
plt.title("Concurrent Requests vs Average Response Time")
plt.grid(True)
plt.savefig("response_time.png", dpi=300)
plt.close()


# Throughput graph
plt.figure()
plt.plot(concurrency, throughput, marker="o")
plt.xlabel("Concurrent Requests")
plt.ylabel("Throughput (requests/sec)")
plt.title("Concurrent Requests vs Throughput")
plt.grid(True)
plt.savefig("throughput.png", dpi=300)
plt.close()


# CPU graph
plt.figure()
plt.plot(concurrency, order_cpu, marker="o", label="Order Service")
plt.plot(concurrency, product_cpu, marker="o", label="Product Service")
plt.plot(concurrency, user_cpu, marker="o", label="User Service")
plt.xlabel("Concurrent Requests")
plt.ylabel("CPU Usage (%)")
plt.title("Concurrent Requests vs CPU Usage")
plt.legend()
plt.grid(True)
plt.savefig("cpu_usage.png", dpi=300)
plt.close()


# Memory graph
plt.figure()
plt.plot(concurrency, order_memory, marker="o", label="Order Service")
plt.plot(concurrency, product_memory, marker="o", label="Product Service")
plt.plot(concurrency, user_memory, marker="o", label="User Service")
plt.xlabel("Concurrent Requests")
plt.ylabel("Memory Usage (MiB)")
plt.title("Concurrent Requests vs Memory Usage")
plt.legend()
plt.grid(True)
plt.savefig("memory_usage.png", dpi=300)
plt.close()


# Final table
print("\n\n==============================================")
print(" FINAL OBSERVATION TABLE")
print("==============================================")

print(
    f"{'Workload':<10}"
    f"{'Conc.':<8}"
    f"{'Response':<12}"
    f"{'Throughput':<14}"
    f"{'Failed':<8}"
)

for row in results:

    print(
        f"{row['workload']:<10}"
        f"{row['concurrency']:<8}"
        f"{row['response_time']:<12}"
        f"{row['throughput']:<14}"
        f"{row['failed']:<8}"
    )


print("\nFiles generated:")
print("1. final_results.csv")
print("2. response_time.png")
print("3. throughput.png")
print("4. cpu_usage.png")
print("5. memory_usage.png")