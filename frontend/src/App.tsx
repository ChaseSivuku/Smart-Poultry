import React, { useState } from "react";
import { Droplets, Gauge } from "lucide-react";
import Dashboard from "./Dashboard/Dashboard";

function App() {
  const [soilMoisture] = useState(42);
  const [tankLevel] = useState(23);
  const [rainfall] = useState(0);

  return (
    
    <div className="App">
        <Dashboard />

        

    </div>
  );
}

export default App;
