import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import Overview from "./pages/Overview";
import PromptHistory from "./pages/PromptHistory";
import EvalRunDetail from "./pages/EvalRunDetail";
import CIHistory from "./pages/CIHistory";

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Overview />} />
        <Route path="/prompts/:id" element={<PromptHistory />} />
        <Route path="/eval/:id" element={<EvalRunDetail />} />
        <Route path="/ci" element={<CIHistory />} />
      </Routes>
    </Layout>
  );
}
