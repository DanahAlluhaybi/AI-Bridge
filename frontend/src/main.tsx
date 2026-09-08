import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import "./index.css";

// BrowserRouter is what makes react-router-dom aware of the actual
// browser URL (and lets it change the URL without a full page reload
// when you click a <Link>). Everything inside it can use routing
// features like <Routes>, <Link>, and useParams().
ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>,
);
