import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import "./App.css";
import { AppLayout } from "./layouts/AppLayout";
import { MethodologyPage } from "./pages/MethodologyPage";
import { WorkspacePage } from "./pages/WorkspacePage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route index element={<WorkspacePage />} />
          <Route path="methodology" element={<MethodologyPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
