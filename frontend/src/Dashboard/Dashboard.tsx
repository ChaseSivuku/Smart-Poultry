import { JSX, useState, useEffect } from "react";
import {
  Droplets,
  CloudRain,
  Gauge,
  Activity,
  Sun,
  Fan,
  Zap,
  Lightbulb,
  Bell,
  Bot,
} from "lucide-react";
import { Card, CardContent } from "./ui/card";
import { io } from "socket.io-client";
import React from "react";
import Assistant from "./Assistant";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Legend,
} from "recharts";

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [feed, setFeed] = useState(0);
  const [tankLevel, setTankLevel] = useState(0);
  const [temperature, setTemperature] = useState(0);
  const [light, setLight] = useState(0);
  const [humidity, setHumidity] = useState(0);

  // Alert thresholds for each metric
  const alertThresholds = {
    temperature: { min: 18, max: 30 }, // Optimal range: 18-30°C
    tankLevel: { min: 20 }, // Alert if below 20%
    feed: { min: 15 }, // Alert if below 15kg
    light: { min: 200 }, // Alert if below 200 lux
    humidity: { min: 40, max: 80 }, // Optimal range: 40-80%
  };

  const [fanOn, setFanOn] = useState(false);
  const [pumpOn, setPumpOn] = useState(false);
  const [lightOn, setLightOn] = useState(false);

  const [lineData, setLineData] = useState<{ time: string; temp: number }[]>([]);
  const [barData, setBarData] = useState<{ name: string; amount: number }[]>([]);
  const [pieData, setPieData] = useState<{ name: string; value: number }[]>([]);

  const COLORS = ["#0a5526", "#5cb85c", "#a3d9a5", "#e2f3e2"];

  // Helper function to check if a metric is in alert state
  const isMetricInAlert = (metric: string, value: number): boolean => {
    const threshold = alertThresholds[metric as keyof typeof alertThresholds];
    if (!threshold) return false;
    
    if (threshold.min !== undefined && value < threshold.min) return true;
    if ('max' in threshold && threshold.max !== undefined && value > threshold.max) return true;
    
    return false;
  };

  // --- Fetch IoT data periodically ---
  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch("http://127.0.0.1:5000/api/sensor-data");
        const data = await res.json();

        setTemperature(data.temperature);
        setHumidity(data.humidity);
        setTankLevel(data.tankLevel);
        setFeed(data.feed);
        setLight(data.light);

        const currentTime = new Date().toLocaleTimeString("en-US", {
          hour: "2-digit",
          minute: "2-digit",
        });
        setLineData((prev) => {
          const updated = [...prev, { time: currentTime, temp: data.temperature }];
          return updated.slice(-20);
        });

        setBarData([
          { name: "Feed A", amount: data.feed },
          { name: "Starter", amount: Math.max(0, data.feed - 10) },
          { name: "Grower", amount: Math.max(0, data.feed - 20) },
          { name: "Finisher", amount: Math.max(0, data.feed - 30) },
        ]);

        setPieData([
          { name: "Water", value: data.tankLevel },
          { name: "Feed", value: data.feed },
          { name: "Electricity", value: Math.round(data.light / 10) },
          { name: "Maintenance", value: 10 },
        ]);
      } catch (err) {
        console.error("Failed to fetch sensor data:", err);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 1000);
    return () => clearInterval(interval);
  }, []);

// --- WebSocket for device + system state updates ---
useEffect(() => {
  const socket = io("http://127.0.0.1:5000");

  socket.on("connect", () => console.log("✅ Connected to WebSocket"));

  // 🎯 Activity-based events (e.g. "Fan Activated" / "Fan Deactivated")
  socket.on("activity_event", (data) => {
    console.log("📢 Activity Event:", data);

    const title = data.title?.toLowerCase() || "";
    const detail = data.detail?.toLowerCase() || "";

    if(title === "fan" && detail==="activated"){
      setFanOn(true);

    }

    if(title === "fan" && detail==="deactivated"){
      setFanOn(false);
    }

    if(title === "pump" && detail==="activated"){
      setPumpOn(true);

    }

    if(title === "pump" && detail==="deactivated"){
      setPumpOn(false);
    }

       if(title === "light" && detail==="activated"){
      setLightOn(true);

    }

    if(title === "light" && detail==="deactivated"){
      setLightOn(false);
    }


  });

  // ⚙️ Real-time system state updates from automation agent
  socket.on("system_state", (data) => {
    console.log("⚙️ System State Update:", data);

    if (data.fan !== undefined) setFanOn(data.fan);
    if (data.pump !== undefined) setPumpOn(data.pump);
    if (data.light_on !== undefined) setLightOn(data.light_on);
  });

  return () => {
    socket.disconnect();
  };
}, []);

  return (
    <div className="flex min-h-screen bg-[#f9f7f3] text-[#2b2b2b]">

      
      {/* Sidebar */}
      <aside className="w-64 bg-[#0a5526] text-white flex flex-col justify-between">
        <div>
          <div className="px-6 py-6 text-2xl font-bold">Smart Poultry</div>
          <nav className="space-y-2 px-4">
            {[
              { name: "Dashboard", icon: <Activity size={20} /> },
              { name: "Assistant", icon: <Bot size={20} /> }
            ].map((item) => (
              <button
                key={item.name}
                onClick={() => setActiveTab(item.name.toLowerCase())}
                className={`w-full text-left px-4 py-2 rounded-lg flex items-center gap-3 ${
                  activeTab === item.name.toLowerCase()
                    ? "bg-white text-[#0a5526] font-semibold"
                    : "hover:bg-[#1b6a38]"
                }`}
              >
                {item.icon}
                {item.name}
              </button>
            ))}
          </nav>
        </div>

        <div className="p-4 flex items-center space-x-3 border-t border-green-800">
          <div className="w-10 h-10 bg-[#cfe8d9] text-[#0a5526] flex items-center justify-center rounded-full font-semibold">
            JD
          </div>
          <div>
            <p className="font-medium">John Doe</p>
            <p className="text-sm text-green-100">Farmer</p>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 p-8 overflow-y-auto">
        {activeTab === "dashboard" ? (
          <div className="space-y-8">
            {/* Top Stats */}
            <div className="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-5 gap-6">
              <StatCard 
                title="Temperature" 
                icon={<Droplets size={30} />} 
                value={`${temperature} °C`} 
                subtitle="Current Temperature" 
                isAlert={isMetricInAlert('temperature', temperature)}
              />
              <StatCard 
                title="Water Tank Level" 
                icon={<Gauge size={30} />} 
                value={`${tankLevel}%`} 
                subtitle="Main Storage Tank" 
                isAlert={isMetricInAlert('tankLevel', tankLevel)}
              />
              <StatCard 
                title="Feed Amount" 
                icon={<CloudRain size={30} />} 
                value={`${feed} kg`} 
                subtitle="Available Feed" 
                isAlert={isMetricInAlert('feed', feed)}
              />
              <StatCard 
                title="Light Intensity" 
                icon={<Activity size={30} />} 
                value={`${light} cd`} 
                subtitle="Current Brightness" 
                isAlert={isMetricInAlert('light', light)}
              />
              <StatCard 
                title="Humidity" 
                icon={<CloudRain size={30} />} 
                value={`${humidity} %`} 
                subtitle="Air Moisture" 
                isAlert={isMetricInAlert('humidity', humidity)}
              />
            </div>

            {/* Charts Section */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              <ChartCard title="Temperature Trend">
                <ResponsiveContainer width="100%" height={250}>
                  <LineChart data={lineData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey="temp" stroke="#0a5526" strokeWidth={3} dot={{ r: 4 }} />
                  </LineChart>
                </ResponsiveContainer>
              </ChartCard>

              <ChartCard title="Feed Distribution">
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={barData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="amount" fill="#0a5526" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </ChartCard>

              <ChartCard title="Resource Usage">
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie data={pieData} dataKey="value" nameKey="name" outerRadius={80} label>
                      {pieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </ChartCard>
            </div>

            {/* Device Status Section */}
            <Card className="bg-white shadow-md rounded-2xl border border-gray-100 mt-8">
              <CardContent className="p-6">
                <h2 className="text-lg font-semibold mb-6 text-gray-700 flex items-center gap-2">
                  <Zap className="text-[#0a5526]" size={20} /> Device Status
                </h2>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 text-center">
                  <DeviceStatus icon={<Fan size={40} />} label="Fan" active={fanOn} />
                  <DeviceStatus icon={<Droplets size={40} />} label="Pump" active={pumpOn} />
                  <DeviceStatus icon={<Lightbulb size={40} />} label="Light" active={lightOn} />
                </div>
              </CardContent>
            </Card>
          </div>
        ) : (
          <Assistant />
        )}
      </main>
    </div>
  );
}

/* ====== Components ====== */
function StatCard({
  title,
  icon,
  value,
  subtitle,
  isAlert = false,
}: {
  title: string;
  icon: JSX.Element;
  value: string;
  subtitle: string;
  isAlert?: boolean;
}) {
  return (
    <Card className={`shadow-sm rounded-2xl hover:shadow-md transition ${
      isAlert 
        ? "border-red-500 bg-red-50" 
        : "border-gray-200 bg-white"
    }`}>
      <CardContent className="p-5 space-y-3">
        <div className={`flex items-center justify-between font-medium ${
          isAlert ? "text-red-700" : "text-gray-700"
        }`}>
          <span>{title}</span>
          <span className={isAlert ? "text-red-600" : ""}>{icon}</span>
        </div>
        <div className={`text-3xl font-bold ${isAlert ? "text-red-600" : ""}`}>
          {value}
        </div>
        <div className={`text-sm ${isAlert ? "text-red-600" : "text-gray-500"}`}>
          {subtitle}
        </div>
        {isAlert && (
          <div className="flex items-center gap-2 mt-2">
            <div className="w-2 h-2 bg-red-500 rounded-full"></div>
            <span className="text-xs font-semibold text-red-600">ALERT</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function ChartCard({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <Card className="bg-white shadow-md rounded-2xl border border-gray-100">
      <CardContent className="p-6">
        <h2 className="text-lg font-semibold mb-4 text-gray-700">{title}</h2>
        {children}
      </CardContent>
    </Card>
  );
}

function DeviceStatus({
  icon,
  label,
  active,
}: {
  icon: JSX.Element;
  label: string;
  active: boolean;
}) {
  return (
    <div
      className={`p-6 rounded-2xl border-2 transition-all ${
        active
          ? "border-green-500 bg-green-50 text-green-700 shadow-lg shadow-green-100"
          : "border-gray-300 bg-gray-50 text-gray-500"
      }`}
    >
      <div className={`flex justify-center mb-3 ${active ? "text-green-600" : ""}`}>
        {icon}
      </div>
      <h3 className="text-lg font-semibold">{label}</h3>
      <p className="mt-1 text-sm font-medium">{active ? "ON" : "OFF"}</p>
      {active && (
        <div className="flex items-center justify-center gap-2 mt-2">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          <span className="text-xs font-semibold text-green-600">ACTIVE</span>
        </div>
      )}
    </div>
  );
}
