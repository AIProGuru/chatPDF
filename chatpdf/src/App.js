import { Training } from "pages/dashboard/training/Training";
import "./App.css";
import Chatbot from "./components/chatbot/Chatbot";

import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
import Home from "pages/dashboard/home/Home";

function App() {
  return (
    <div className="App">
      <Router>
        <Routes>
          <Route path="/chatbot" element={<Chatbot />} />
          <Route path="/dashboard/training" element={<Training />} />
          <Route path="/dashboard/" element={<Home />} />
        </Routes>
      </Router>
    </div>
  );
}

export default App;
