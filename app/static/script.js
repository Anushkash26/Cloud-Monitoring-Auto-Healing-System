
let usageChart = null;

let chartLabels = [];
let cpuHistory = [];
let memoryHistory = [];
let diskHistory = [];

function updateChart(data) {
    const now = new Date().toLocaleTimeString();

    chartLabels.push(now);
    cpuHistory.push(data.cpu_percent);
    memoryHistory.push(data.memory_percent);
    diskHistory.push(data.disk_percent);

    // Keep only the latest 12 readings
    if (chartLabels.length > 12) {
        chartLabels.shift();
        cpuHistory.shift();
        memoryHistory.shift();
        diskHistory.shift();
    }

    if (!usageChart) {
        const ctx = document.getElementById("usageChart");

        usageChart = new Chart(ctx, {
            type: "line",
            data: {
                labels: chartLabels,
                datasets: [
                    {
                        label: "CPU %",
                        data: cpuHistory,
                        borderColor: "#2563eb",
                        tension: 0.3
                    },
                    {
                        label: "Memory %",
                        data: memoryHistory,
                        borderColor: "#16a34a",
                        tension: 0.3
                    },
                    {
                        label: "Disk %",
                        data: diskHistory,
                        borderColor: "#f59e0b",
                        tension: 0.3
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        title: {
                            display: true,
                            text: "Usage (%)"
                        }
                    }
                }
            }
        });
    } else {
        usageChart.update();
    }
}

async function loadMetrics() {
    try {
        const response = await fetch("/api/metrics");
        const data = await response.json();

        updateChart(data);
        
        document.getElementById("cpu").textContent =
            data.cpu_percent + "%";

        document.getElementById("memory").textContent =
            data.memory_percent + "%";

        document.getElementById("disk").textContent =
            data.disk_percent + "%";

        document.getElementById("cpuBar").style.width =
            data.cpu_percent + "%";

        document.getElementById("memoryBar").style.width =
            data.memory_percent + "%";

        document.getElementById("diskBar").style.width =
            data.disk_percent + "%";

        const status = document.getElementById("systemStatus");
        status.textContent = data.status;

        status.style.color =
            data.status === "HEALTHY" ? "#16a34a" :
            data.status === "WARNING" ? "#d97706" : "#dc2626";

        document.getElementById("lastUpdated").textContent =
            "Last updated: " + new Date(data.timestamp).toLocaleString();

    } catch (error) {
        document.getElementById("systemStatus").textContent =
            "Connection Error";
        console.error("Metrics error:", error);
    }
}

async function loadAlerts() {
    try {
        const response = await fetch("/api/alerts");
        const alerts = await response.json();

        const table = document.getElementById("alertsBody");

        if (alerts.length === 0) {
            table.innerHTML =
                '<tr><td colspan="5">No alerts found</td></tr>';
            return;
        }

        table.innerHTML = alerts.map(alert => `
            <tr>
                <td>${alert.id}</td>
                <td>${alert.type}</td>
                <td>${alert.severity}</td>
                <td>${alert.detail}</td>
                <td>${alert.auto_healed ? "Yes" : "No"}</td>
            </tr>
        `).join("");

    } catch (error) {
        console.error("Alerts error:", error);
    }
}

async function runHealthCheck() {
    const button = document.getElementById("checkBtn");

    button.disabled = true;
    button.textContent = "Checking...";

    try {
        const response = await fetch("/api/check", {
            method: "POST"
        });

        if (!response.ok) {
            throw new Error("Health check failed");
        }

        await response.json();

        await loadMetrics();
        await loadAlerts();

        alert("Health check completed!");

    } catch (error) {
        alert("Unable to run health check. Please check the backend.");
        console.error(error);
    } finally {
        button.disabled = false;
        button.textContent = "Run Health Check";
    }
}

// Load dashboard data when the page opens
loadMetrics();
loadAlerts();

// Refresh metrics and alerts every 5 seconds
setInterval(() => {
    loadMetrics();
    loadAlerts();
}, 5000);
