import React, { useState } from "react";
import UploadForm from "./components/UploadForm";
import UploadFace from "./components/UploadFace";
import "./style.css";

export default function App() {
  const [page, setPage] = useState("search");

  return (
    <div className="app-container">
      
      {/* Header */}
      <header
        style={{
          padding: "26px 12px 16px",
          textAlign: "center",
          background: "#fff",
          borderBottomLeftRadius: "18px",
          borderBottomRightRadius: "18px",
          boxShadow: "0 6px 28px rgba(33,150,243,0.08)",
          position: "sticky",
          top: 0,
          zIndex: 10,
        }}
      >
        <h1
          style={{
            fontSize: "clamp(1.6rem, 3vw, 2.8rem)",
            margin: 0,
            fontWeight: 700,
            color: "#2196f3",
          }}
        >
          Face Recognition System
        </h1>

        {/* Navigation buttons */}
        <nav
          style={{
            marginTop: "20px",
            display: "flex",
            flexWrap: "wrap",
            justifyContent: "center",
            gap: "14px",
          }}
        >
          <button
            onClick={() => setPage("search")}
            className={page === "search" ? "nav-btn active" : "nav-btn"}
            aria-label="Switch to Search Page"
          >
            Search Faces
          </button>

          <button
            onClick={() => setPage("upload")}
            className={page === "upload" ? "nav-btn active" : "nav-btn"}
            aria-label="Switch to Admin Upload Page"
          >
            Add New Person (Admin)
          </button>
        </nav>
      </header>

      {/* Main Content */}
      <main style={{ paddingTop: "20px" }}>
        <div className="container">
          {page === "search" && <UploadForm />}
          {page === "upload" && <UploadFace />}
        </div>
      </main>
    </div>
  );
}
