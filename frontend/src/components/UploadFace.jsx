import React, { useState } from "react";
import axios from "axios";

export default function UploadFace() {
  const [file, setFile] = useState(null);
  const [name, setName] = useState("");
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);

  const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

  const uploadFace = async () => {
    if (!name.trim()) {
      setStatus("Please enter a person's name.");
      return;
    }

    if (!file) {
      setStatus("Please select an image.");
      return;
    }

    setLoading(true);
    setStatus("");

    const formData = new FormData();
    formData.append("file", file);
    formData.append("person_name", name);

    try {
      const response = await axios.post(`${API_BASE}/upload`, formData);

      if (response.data.status === "success") {
        setStatus(`Face of '${name}' uploaded successfully!`);
        setName("");
        setFile(null);
      } else {
        setStatus("Upload failed. Please try again.");
      }
    } catch (err) {
      console.error("Upload error:", err);
      const serverMsg = err?.response?.data?.detail || err?.response?.data || err?.message;
      setStatus(serverMsg || "Error uploading face.");
    }

    setLoading(false);
  };

  return (
    <div className="upload-face">
      <h2 className="title">Admin: Add New Face</h2>

      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "16px",
          maxWidth: "420px",
          width: "100%",
          margin: "0 auto"
        }}
      >
        {/* Person Name */}
        <input
          type="text"
          placeholder="Enter Person Name"
          aria-label="Enter the name of the person"
          className="file-input"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />

        {/* Image File */}
        <input
          type="file"
          accept="image/*"
          className="file-input"
          aria-label="Select face image to upload"
          onChange={(e) => setFile(e.target.files[0])}
        />

        {/* Button */}
        <button
          onClick={uploadFace}
          className="primary-btn"
          disabled={loading}
          aria-label="Upload new face to the database"
          style={{ width: "100%" }}
        >
          {loading ? "Uploading..." : "Upload"}
        </button>

        {/* Status Message */}
        {status && (
          <p
            className="status-text"
            style={{
              color:
                status.includes("Error") || status.includes("failed")
                  ? "#f44336"
                  : "#222"
            }}
          >
            {status}
          </p>
        )}
      </div>
    </div>
  );
}
