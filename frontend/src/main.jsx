import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import { AuthProvider } from "./context/AuthContext";
import ScrollToTop from "./components/ScrollToTop";
import { seedDemoAccountsOnce } from "./lib/mockAuth";
import "./styles/globals.css";

// Manager/Admin accounts can't be created from the Register page
//  so seed a couple of demo logins the first time
// the app runs, purely so those dashboards are reachable for testing.
seedDemoAccountsOnce();

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <ScrollToTop />
      <AuthProvider>
        <App />
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>
);
