import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import AgentControlCenter from "./pages/AgentControlCenter";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/tasks" replace />} />
        <Route path="/tasks" element={<AgentControlCenter />} />
        <Route path="/tasks/:taskId" element={<AgentControlCenter />} />
      </Routes>
    </BrowserRouter>
  );
}
